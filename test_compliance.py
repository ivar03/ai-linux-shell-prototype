#!/usr/bin/env python3
"""
Comprehensive Compliance Checking Testing
==========================================
Tests SOX, HIPAA, and general security compliance rules.
"""

import sys
from typing import Dict, List
from dataclasses import dataclass

from rich.console import Console
from rich.progress import Progress
from rich.table import Table

console = Console()

@dataclass
class ComplianceTestResult:
    test_name: str
    passed: bool
    details: str


class ComplianceTester:
    """Comprehensive compliance testing"""
    
    def __init__(self):
        self.results: List[ComplianceTestResult] = []
    
    def run_test(self, test_name: str, command: str, should_be_compliant: bool, expected_violation: str = None):
        """Run a single compliance test"""
        try:
            from compliance.checker import check_compliance, is_compliant
            
            compliant = is_compliant(command)
            failures = check_compliance(command)
            
            if compliant == should_be_compliant:
                self.results.append(ComplianceTestResult(test_name, True, "✓"))
                return True
            else:
                expected = "compliant" if should_be_compliant else "non-compliant"
                actual = "compliant" if compliant else "non-compliant"
                details = f"Expected {expected}, got {actual}"
                if failures and expected_violation:
                    details += f" | Violations: {', '.join(f['rule'] for f in failures)}"
                self.results.append(ComplianceTestResult(test_name, False, details))
                return False
        except Exception as e:
            self.results.append(ComplianceTestResult(test_name, False, f"Exception: {e}"))
            return False
    
    def run_all_tests(self) -> Dict:
        """Run all compliance tests"""
        console.print("\n[bold cyan]═══ Running Comprehensive Compliance Tests ═══[/bold cyan]\n")
        
        test_cases = [
            # Safe/Compliant Commands
            ("Safe: List files", "ls -la", True),
            ("Safe: Print working directory", "pwd", True),
            ("Safe: Echo text", "echo 'hello world'", True),
            ("Safe: Cat file", "cat myfile.txt", True),
            ("Safe: Grep search", "grep 'pattern' file.txt", True),
            ("Safe: Find command", "find . -name '*.txt'", True),
            ("Safe: Process list", "ps aux", True),
            ("Safe: Disk usage", "df -h", True),
            ("Safe: Memory info", "free -h", True),
            ("Safe: Show date", "date", True),
            
            # PII/PHI Exposure
            ("PII: Password file", "cat /etc/passwd", False),
            ("PII: Shadow file", "cat /etc/shadow", False),
            ("PII: Credit card log", "less /var/log/creditcard.log", False),
            ("PII: SSN database", "cat ssn_database.csv", False),
            ("HIPAA: Patient records", "cat patient_records.txt", False),
            ("HIPAA: Medical data", "less medical_records.txt", False),
            ("HIPAA: Health info", "more health_info.log", False),
            
            # Unencrypted Transfer
            ("Security: FTP transfer", "ftp server.com", False),
            ("Security: Telnet connection", "telnet remote.server", False),
            ("Security: FTP uppercase", "FTP upload.server.com", False),
            ("Safe: SSH connection", "ssh user@server", True),
            ("Safe: SCP transfer", "scp file.txt user@server:/path/", True),
            ("Safe: SFTP transfer", "sftp user@server", True),
            ("Safe: Rsync transfer", "rsync -av source/ destination/", True),
            
            # Password in Commands
            ("Security: MySQL password", "mysql --password=secret123 -u user", False),
            ("Security: Generic password", "connect --password=mypassword", False),
            ("Security: PWD flag", "auth --pwd=admin123", False),
            ("Safe: Password prompt", "mysql -u user -p", True),
            
            # Mass Deletion
            ("Critical: Delete root", "rm -rf /", False),
            ("Critical: Delete var", "rm -rf /var", False),
            ("Critical: Delete home", "rm -rf /home", False),
            ("Safe: Delete specific file", "rm myfile.txt", True),
            ("Safe: Delete temp folder", "rm -rf /tmp/my_temp_folder", True),
            
            # SOX Compliance
            ("SOX: Add user", "useradd newuser", False),
            ("SOX: Delete user", "userdel olduser", False),
            ("SOX: Modify user", "usermod -g group user", False),
            ("SOX: Add group", "groupadd developers", False),
            ("SOX: Delete group", "groupdel admins", False),
            ("SOX: Change password", "passwd username", False),
            ("SOX: File permission change", "chmod 777 important_file.txt", False),
            ("SOX: Safe permission", "chmod 644 myfile.txt", True),
            
            # HIPAA with transfers
            ("HIPAA: FTP medical data", "ftp medical.server.com", False),
            ("HIPAA: Telnet health DB", "telnet health.database.com", False),
            
            # Edge Cases
            ("Edge: Empty command", "", True),
            ("Edge: Whitespace only", "   ", True),
            ("Edge: Complex safe command", "find /var/log -name '*.log' -mtime +30 -exec gzip {} \\;", True),
            ("Edge: Pipe commands", "ps aux | grep python | wc -l", True),
            ("Edge: Multiple commands", "cd /tmp && ls -la", True),
        ]
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Running compliance tests...", total=len(test_cases))
            
            for test_name, command, should_be_compliant in test_cases:
                self.run_test(test_name, command, should_be_compliant)
                progress.advance(task)
        
        # Calculate metrics
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            "total_tests": total,
            "tests_passed": passed,
            "tests_failed": failed,
            "success_rate": success_rate,
            "test_details": [(r.test_name, "PASS" if r.passed else "FAIL", r.details) 
                           for r in self.results]
        }
    
    def display_results(self, results: Dict):
        """Display test results"""
        table = Table(title="Compliance Checking Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="white")
        
        for test_name, status, details in results["test_details"]:
            color = "green" if status == "PASS" else "red"
            table.add_row(test_name, f"[{color}]{status}[/{color}]", details)
        
        table.add_row(
            "[bold]Overall Success Rate[/bold]",
            f"[bold]{results['success_rate']:.1f}%[/bold]",
            f"{results['tests_passed']}/{results['total_tests']} passed"
        )
        
        console.print(table)


def evaluate_compliance_system() -> Dict:
    """Main entry point for compliance evaluation"""
    tester = ComplianceTester()
    results = tester.run_all_tests()
    tester.display_results(results)
    return results


if __name__ == "__main__":
    evaluate_compliance_system()