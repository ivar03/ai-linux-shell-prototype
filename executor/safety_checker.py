import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import shlex

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SafetyResult:
    is_safe: bool
    risk_level: str
    reason: str
    suggestions: List[str] = None
    blocked_patterns: List[str] = None

class SafetyChecker:
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()
        self.dangerous_patterns = self._load_dangerous_patterns()
        self.privilege_commands = self._load_privilege_commands()
        self.destructive_commands = self._load_destructive_commands()
        self.network_commands = self._load_network_commands()
        
    def _get_default_config(self) -> Dict:
        return {
            "block_high_risk": True,
            "block_critical": True,
            "allow_sudo": False,
            "allow_destructive": False,
            "allow_network": True,
            "max_command_length": 1000,
            "check_file_paths": True,
            "warn_on_wildcards": True
        }
    
    def _load_dangerous_patterns(self) -> List[str]:
        return [
            # File system destruction
            r"rm\s+.*-rf\s*/\s*$",
            r"rm\s+.*-rf\s*/.*",
            r"rm\s+.*-rf\s*\$HOME",
            r"rm\s+.*-rf\s*~",
            r"rm\s+.*-rf\s*\.",
            r"dd\s+.*of=/dev/sd[a-z]",
            r"dd\s+.*of=/dev/hd[a-z]",
            r"dd\s+.*of=/dev/nvme",
            r"mkfs\.",
            r"format\s+/dev/",
            r"fdisk\s+/dev/",
            r"parted\s+/dev/",
            
            # System critical files
            r"rm\s+.*(/etc/passwd|/etc/shadow|/etc/group)",
            r"rm\s+.*/boot/",
            r"rm\s+.*/usr/",
            r"rm\s+.*/var/",
            r"rm\s+.*/lib/",
            r"rm\s+.*/lib64/",
            
            # Network security risks
            r"curl\s+.*\|\s*sh",
            r"wget\s+.*\|\s*sh",
            r"curl\s+.*\|\s*bash",
            r"wget\s+.*\|\s*bash",
            r"nc\s+.*-l.*-e",
            r"socat\s+.*EXEC",
            r"bash\s+<\s*\(",
            
            # System shutdown/reboot
            r"shutdown\s+.*now",
            r"reboot\s*$",
            r"halt\s*$",
            r"poweroff\s*$",
            r"init\s+0",
            r"init\s+6",
            
            # Process manipulation
            r"kill\s+-9\s+1\s*$",
            r"killall\s+-9\s+init",
            r"killall\s+-9\s+systemd",
            r"pkill\s+-9\s+init",
            
            # Privilege escalation
            r"chmod\s+.*777\s+/",
            r"chmod\s+.*4755",
            r"chmod\s+.*6755",
            r"chown\s+.*root:root\s+/",
            
            # Fork bombs and resource exhaustion
            r":\(\)\{.*\}",
            r"while\s+true.*do.*done",
            r"yes\s+.*\|\s*.*",
            
            # Overwriting important files
            r">\s*/etc/passwd",
            r">\s*/etc/shadow",
            r">\s*/etc/group",
            r">\s*/boot/",
        ]
    
    def _load_privilege_commands(self) -> List[str]:
        return [
            "sudo", "su", "mount", "umount", "fdisk", "parted", "mkfs", 
            "fsck", "iptables", "systemctl", "service", "chkconfig",
            "useradd", "userdel", "usermod", "groupadd", "groupdel",
            "passwd", "chpasswd", "visudo", "crontab", "at", "batch"
        ]
    
    def _load_destructive_commands(self) -> List[str]:
        return [
            "rm", "rmdir", "mv", "dd", "shred", "truncate", "wipe",
            "chmod", "chown", "chgrp", "unlink", "mkfs", "format",
            "fdisk", "parted", "gparted", "wipefs"
        ]
    
    def _load_network_commands(self) -> List[str]:
        return [
            "curl", "wget", "nc", "netcat", "socat", "ssh", "scp", "rsync",
            "ftp", "sftp", "telnet", "nmap", "masscan", "tcpdump", "wireshark"
        ]
    
    def check_command(self, command: str) -> SafetyResult:
        if not command or not command.strip():
            return SafetyResult(
                is_safe=False,
                risk_level=RiskLevel.MEDIUM.value,
                reason="Empty command provided"
            )
        
        command = command.strip()
        
        # Check command length
        if len(command) > self.config["max_command_length"]:
            return SafetyResult(
                is_safe=False,
                risk_level=RiskLevel.MEDIUM.value,
                reason=f"Command too long ({len(command)} chars)"
            )
        
        # Check for dangerous patterns
        dangerous_check = self._check_dangerous_patterns(command)
        if not dangerous_check.is_safe:
            return dangerous_check
        
        # Check for privilege escalation
        privilege_check = self._check_privilege_commands(command)
        if not privilege_check.is_safe:
            return privilege_check
        
        # Check for destructive operations
        destructive_check = self._check_destructive_commands(command)
        if not destructive_check.is_safe:
            return destructive_check
        
        # Check for network operations
        network_check = self._check_network_commands(command)
        if not network_check.is_safe:
            return network_check
        
        # Check for suspicious file paths
        path_check = self._check_file_paths(command)
        if not path_check.is_safe:
            return path_check
        
        # Check for wildcards and globbing
        wildcard_check = self._check_wildcards(command)
        if not wildcard_check.is_safe:
            return wildcard_check
        
        # If all checks pass, command is considered safe
        return SafetyResult(
            is_safe=True,
            risk_level=RiskLevel.LOW.value,
            reason="Command passed all safety checks"
        )
    
    def _check_dangerous_patterns(self, command: str) -> SafetyResult:
        matched_patterns = []
        
        for pattern in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                matched_patterns.append(pattern)
        
        if matched_patterns:
            return SafetyResult(
                is_safe=False,
                risk_level=RiskLevel.CRITICAL.value,
                reason="Command matches dangerous patterns",
                blocked_patterns=matched_patterns
            )
        
        return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="No dangerous patterns found")
    
    def _check_privilege_commands(self, command: str) -> SafetyResult:
        words = shlex.split(command.lower())
        if not words:
            return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")
        
        first_word = words[0]
        
        # Check for sudo
        if first_word == "sudo":
            if not self.config["allow_sudo"]:
                return SafetyResult(
                    is_safe=False,
                    risk_level=RiskLevel.HIGH.value,
                    reason="sudo commands not allowed",
                    suggestions=["Remove sudo and run command as regular user"]
                )
            else:
                return SafetyResult(
                    is_safe=True,
                    risk_level=RiskLevel.MEDIUM.value,
                    reason="sudo command allowed by configuration"
                )
        
        # Check for other privilege commands
        if first_word in self.privilege_commands:
            return SafetyResult(
                is_safe=False,
                risk_level=RiskLevel.HIGH.value,
                reason=f"Command '{first_word}' requires elevated privileges",
                suggestions=["Consider running without special privileges"]
            )
        
        return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")
    
    def _check_destructive_commands(self, command: str) -> SafetyResult:
        words = shlex.split(command.lower())
        if not words:
            return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")
        
        first_word = words[0]
        
        if first_word in self.destructive_commands:
            if not self.config["allow_destructive"]:
                # Special handling for rm command
                if first_word == "rm":
                    # Check for dangerous rm patterns
                    if "-rf" in command or "-fr" in command:
                        if any(path in command for path in ["/", "~", "$HOME", "*"]):
                            return SafetyResult(
                                is_safe=False,
                                risk_level=RiskLevel.CRITICAL.value,
                                reason="Potentially destructive rm command with dangerous paths",
                                suggestions=["Be more specific with file paths", "Use trash command instead"]
                            )
                    
                    return SafetyResult(
                        is_safe=True,
                        risk_level=RiskLevel.MEDIUM.value,
                        reason="rm command detected but appears safe"
                    )
                
                return SafetyResult(
                    is_safe=False,
                    risk_level=RiskLevel.HIGH.value,
                    reason=f"Destructive command '{first_word}' not allowed",
                    suggestions=["Consider using safer alternatives"]
                )
        
        return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")
    
    def _check_network_commands(self, command: str) -> SafetyResult:
        words = shlex.split(command.lower())
        if not words:
            return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")
        
        first_word = words[0]
        
        if first_word in self.network_commands:
            if not self.config["allow_network"]:
                return SafetyResult(
                    is_safe=False,
                    risk_level=RiskLevel.MEDIUM.value,
                    reason=f"Network command '{first_word}' not allowed",
                    suggestions=["Network operations are disabled"]
                )
            
            # Check for pipe to shell execution
            if "|" in command and any(shell in command for shell in ["sh", "bash", "zsh"]):
                return SafetyResult(
                    is_safe=False,
                    risk_level=RiskLevel.CRITICAL.value,
                    reason="Network command piped to shell - potential security risk",
                    suggestions=["Download to file first, then inspect before executing"]
                )
        
        return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")
    
    def _check_file_paths(self, command: str) -> SafetyResult:
        if not self.config["check_file_paths"]:
            return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")
        
        # Critical system directories
        critical_paths = [
            "/etc/", "/boot/", "/usr/", "/lib/", "/lib64/", "/bin/", "/sbin/",
            "/dev/", "/proc/", "/sys/", "/var/log/", "/var/lib/"
        ]
        
        for path in critical_paths:
            if path in command:
                # Check if it's a read operation or write operation
                if any(op in command for op in ["rm", "mv", "cp", "dd", ">"]):
                    return SafetyResult(
                        is_safe=False,
                        risk_level=RiskLevel.HIGH.value,
                        reason=f"Operation on critical system path: {path}",
                        suggestions=["Avoid modifying system directories"]
                    )
        
        return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")
    
    def _check_wildcards(self, command: str) -> SafetyResult:
        if not self.config["warn_on_wildcards"]:
            return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")
        
        # Check for dangerous wildcard patterns
        dangerous_wildcards = [
            r"rm\s+.*\*",
            r"rm\s+.*\?",
            r"chmod\s+.*\*",
            r"chown\s+.*\*",
            r"mv\s+.*\*.*/"
        ]
        
        for pattern in dangerous_wildcards:
            if re.search(pattern, command, re.IGNORECASE):
                return SafetyResult(
                    is_safe=True,  # Warning, not blocking
                    risk_level=RiskLevel.MEDIUM.value,
                    reason="Command uses wildcards - be careful",
                    suggestions=["Double-check which files will be affected"]
                )
        
        return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")
    
    def suggest_safer_alternative(self, command: str) -> Optional[str]:
        suggestions = {
            r"rm\s+-rf\s+\*": "Use 'find . -name \"pattern\" -delete' for specific files",
            r"rm\s+-rf\s+/": "NEVER delete root directory!",
            r"curl\s+.*\|\s*sh": "Download first: curl URL > file.sh && chmod +x file.sh && ./file.sh",
            r"chmod\s+777": "Use more restrictive permissions like 755 or 644",
            r"sudo\s+rm": "Be very careful with sudo rm - consider using trash instead"
        }
        
        for pattern, suggestion in suggestions.items():
            if re.search(pattern, command, re.IGNORECASE):
                return suggestion
        
        return None
    
    def get_risk_explanation(self, risk_level: str) -> str:
        explanations = {
            RiskLevel.LOW.value: "Low risk - command appears safe",
            RiskLevel.MEDIUM.value: "Medium risk - command may modify files or system state",
            RiskLevel.HIGH.value: "High risk - potentially destructive or dangerous command",
            RiskLevel.CRITICAL.value: "Critical risk - command could cause system damage"
        }
        
        return explanations.get(risk_level, "Unknown risk level")
    
    def validate_command_syntax(self, command: str) -> Tuple[bool, str]:
        try:
            # Try to parse the command
            shlex.split(command)
            return True, "Syntax appears valid"
        except ValueError as e:
            return False, f"Syntax error: {e}"
    
    def is_read_only_command(self, command: str) -> bool:
        read_only_commands = [
            "ls", "cat", "less", "more", "head", "tail", "grep", "find",
            "ps", "top", "df", "du", "free", "uptime", "whoami", "id",
            "pwd", "echo", "date", "cal", "history", "which", "whereis",
            "file", "stat", "wc", "diff", "sort", "uniq", "cut"
        ]
        
        words = shlex.split(command.lower())
        if not words:
            return False
        
        first_word = words[0]
        return first_word in read_only_commands
    
    def update_config(self, new_config: Dict):
        self.config.update(new_config)
        logger.info(f"Safety configuration updated: {new_config}")