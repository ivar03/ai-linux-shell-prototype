#!/usr/bin/env python3
"""
Comprehensive Compliance Checking Testing - 200+ Test Cases
============================================================
Tests SOX, HIPAA, GDPR, PCI-DSS, and general security compliance rules.
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
    category: str = "General"


class ComplianceTester:
    """Comprehensive compliance testing"""
    
    def __init__(self):
        self.results: List[ComplianceTestResult] = []
    
    def run_test(self, test_name: str, command: str, should_be_compliant: bool, 
                 category: str = "General", expected_violation: str = None):
        """Run a single compliance test"""
        try:
            from compliance.checker import check_compliance, is_compliant
            
            compliant = is_compliant(command)
            failures = check_compliance(command)
            
            if compliant == should_be_compliant:
                self.results.append(ComplianceTestResult(test_name, True, "✓", category))
                return True
            else:
                expected = "compliant" if should_be_compliant else "non-compliant"
                actual = "compliant" if compliant else "non-compliant"
                details = f"Expected {expected}, got {actual}"
                if failures and expected_violation:
                    details += f" | Violations: {', '.join(f['rule'] for f in failures)}"
                self.results.append(ComplianceTestResult(test_name, False, details, category))
                return False
        except Exception as e:
            self.results.append(ComplianceTestResult(test_name, False, f"Exception: {e}", category))
            return False
    
    def run_all_tests(self) -> Dict:
        """Run all compliance tests"""
        console.print("\n[bold cyan]═══ Running Comprehensive Compliance Tests (200+ cases) ═══[/bold cyan]\n")
        
        test_cases = [
            # ========== SECTION 1: Safe Commands (20 tests) ==========
            ("Safe: List files", "ls -la", True, "Safe"),
            ("Safe: Print working directory", "pwd", True, "Safe"),
            ("Safe: Echo text", "echo 'hello world'", True, "Safe"),
            ("Safe: Cat file", "cat myfile.txt", True, "Safe"),
            ("Safe: Grep search", "grep 'pattern' file.txt", True, "Safe"),
            ("Safe: Find command", "find . -name '*.txt'", True, "Safe"),
            ("Safe: Process list", "ps aux", True, "Safe"),
            ("Safe: Disk usage", "df -h", True, "Safe"),
            ("Safe: Memory info", "free -h", True, "Safe"),
            ("Safe: Show date", "date", True, "Safe"),
            ("Safe: Show uptime", "uptime", True, "Safe"),
            ("Safe: Show hostname", "hostname", True, "Safe"),
            ("Safe: Show whoami", "whoami", True, "Safe"),
            ("Safe: Show environment", "env", True, "Safe"),
            ("Safe: Tail log", "tail -f /var/log/app.log", True, "Safe"),
            ("Safe: Head file", "head -n 20 file.txt", True, "Safe"),
            ("Safe: Count lines", "wc -l file.txt", True, "Safe"),
            ("Safe: Sort file", "sort file.txt", True, "Safe"),
            ("Safe: Unique values", "uniq file.txt", True, "Safe"),
            ("Safe: Compare files", "diff file1.txt file2.txt", True, "Safe"),
            
            # ========== SECTION 2: PII/PHI Exposure (30 tests) ==========
            ("PII: Password file", "cat /etc/passwd", False, "PII"),
            ("PII: Shadow file", "cat /etc/shadow", False, "PII"),
            ("PII: Credit card log", "less /var/log/creditcard.log", False, "PII"),
            ("PII: SSN database", "cat ssn_database.csv", False, "PII"),
            ("PII: Social security", "grep ssn users.txt", False, "PII"),
            ("PII: Personal info", "cat personal_info.json", False, "PII"),
            ("PII: Customer data", "less customer_data.csv", False, "PII"),
            ("PII: User credentials", "cat credentials.txt", False, "PII"),
            ("PII: Email addresses", "grep email user_emails.txt", False, "PII"),
            ("PII: Phone numbers", "cat phone_numbers.txt", False, "PII"),
            ("HIPAA: Patient records", "cat patient_records.txt", False, "HIPAA"),
            ("HIPAA: Medical data", "less medical_records.txt", False, "HIPAA"),
            ("HIPAA: Health info", "more health_info.log", False, "HIPAA"),
            ("HIPAA: PHI database", "cat phi_database.csv", False, "HIPAA"),
            ("HIPAA: Diagnosis codes", "grep diagnosis medical.txt", False, "HIPAA"),
            ("HIPAA: Treatment plans", "cat treatment_plans.txt", False, "HIPAA"),
            ("HIPAA: Lab results", "less lab_results.txt", False, "HIPAA"),
            ("HIPAA: Prescription data", "cat prescriptions.csv", False, "HIPAA"),
            ("HIPAA: Insurance info", "grep insurance patient_data.txt", False, "HIPAA"),
            ("HIPAA: Medical history", "cat medical_history.json", False, "HIPAA"),
            ("GDPR: Personal data", "cat gdpr_personal_data.txt", False, "GDPR"),
            ("GDPR: EU citizen data", "less eu_users.csv", False, "GDPR"),
            ("GDPR: Privacy data", "cat privacy_records.txt", False, "GDPR"),
            ("GDPR: Consent records", "grep consent user_prefs.txt", False, "GDPR"),
            ("GDPR: Data subject info", "cat data_subjects.json", False, "GDPR"),
            ("PCI: Card numbers", "cat card_numbers.txt", False, "PCI-DSS"),
            ("PCI: CVV codes", "grep cvv transactions.log", False, "PCI-DSS"),
            ("PCI: Payment data", "less payment_data.csv", False, "PCI-DSS"),
            ("PCI: Cardholder data", "cat cardholder_data.txt", False, "PCI-DSS"),
            ("PCI: Transaction log", "tail credit_card_transactions.log", False, "PCI-DSS"),
            
            # ========== SECTION 3: Unencrypted Transfer (25 tests) ==========
            ("Security: FTP transfer", "ftp server.com", False, "Encryption"),
            ("Security: Telnet connection", "telnet remote.server", False, "Encryption"),
            ("Security: FTP uppercase", "FTP upload.server.com", False, "Encryption"),
            ("Security: HTTP transfer", "curl http://api.example.com/data", False, "Encryption"),
            ("Security: Plain SMTP", "sendmail -t < mail.txt", False, "Encryption"),
            ("Security: FTP upload", "ftp -n ftp.server.com", False, "Encryption"),
            ("Security: Telnet port 23", "telnet 192.168.1.1 23", False, "Encryption"),
            ("Security: TFTP transfer", "tftp server.com", False, "Encryption"),
            ("Security: Rlogin", "rlogin remote.host", False, "Encryption"),
            ("Security: Rsh", "rsh remote.host ls", False, "Encryption"),
            ("Security: Rexec", "rexec remote.host command", False, "Encryption"),
            ("Safe: SSH connection", "ssh user@server", True, "Encryption"),
            ("Safe: SCP transfer", "scp file.txt user@server:/path/", True, "Encryption"),
            ("Safe: SFTP transfer", "sftp user@server", True, "Encryption"),
            ("Safe: Rsync over SSH", "rsync -av -e ssh source/ user@server:/dest/", True, "Encryption"),
            ("Safe: HTTPS request", "curl https://api.example.com/data", True, "Encryption"),
            ("Safe: FTPS transfer", "curl ftps://server.com/file", True, "Encryption"),
            ("Safe: SCP with key", "scp -i key.pem file.txt user@server:/path/", True, "Encryption"),
            ("Safe: SSH tunnel", "ssh -L 8080:localhost:80 user@server", True, "Encryption"),
            ("Safe: Git over SSH", "git clone git@github.com:user/repo.git", True, "Encryption"),
            ("Safe: SMTPS", "openssl s_client -connect smtp.gmail.com:465", True, "Encryption"),
            ("Safe: Secure wget", "wget https://example.com/file.tar.gz", True, "Encryption"),
            ("Safe: Secure curl", "curl -k https://secure.api.com/endpoint", True, "Encryption"),
            ("Safe: SSH key copy", "ssh-copy-id user@server", True, "Encryption"),
            ("Safe: Rsync SSH tunnel", "rsync -avz -e 'ssh -p 2222' src/ dest/", True, "Encryption"),
            
            # ========== SECTION 4: Password in Commands (20 tests) ==========
            ("Security: MySQL password", "mysql --password=secret123 -u user", False, "Passwords"),
            ("Security: Generic password", "connect --password=mypassword", False, "Passwords"),
            ("Security: PWD flag", "auth --pwd=admin123", False, "Passwords"),
            ("Security: Pass flag", "login --pass=password123", False, "Passwords"),
            ("Security: PostgreSQL password", "psql -U user -W password123", False, "Passwords"),
            ("Security: Redis password", "redis-cli -a mypassword", False, "Passwords"),
            ("Security: MongoDB password", "mongo -u admin -p admin123", False, "Passwords"),
            ("Security: Ansible vault", "ansible-playbook --vault-password=secret play.yml", False, "Passwords"),
            ("Security: Docker login", "docker login -u user -p password123", False, "Passwords"),
            ("Security: Git credential", "git clone https://user:password@github.com/repo.git", False, "Passwords"),
            ("Security: Curl auth", "curl -u user:password123 http://api.com", False, "Passwords"),
            ("Security: Wget auth", "wget --user=admin --password=secret http://site.com", False, "Passwords"),
            ("Security: API key inline", "curl -H 'Authorization: Bearer secret_key_123' api.com", False, "Passwords"),
            ("Security: AWS credentials", "aws configure set aws_secret_access_key AKIAI...", False, "Passwords"),
            ("Safe: Password prompt", "mysql -u user -p", True, "Passwords"),
            ("Safe: SSH key auth", "ssh -i ~/.ssh/id_rsa user@server", True, "Passwords"),
            ("Safe: Keyring usage", "secret-tool lookup user password", True, "Passwords"),
            ("Safe: Environment var", "mysql -u $DB_USER -p", True, "Passwords"),
            ("Safe: Config file", "mysql --defaults-file=~/.my.cnf", True, "Passwords"),
            ("Safe: Vault file", "ansible-playbook --vault-password-file vault.txt play.yml", True, "Passwords"),
            
            # ========== SECTION 5: Mass Deletion (20 tests) ==========
            ("Critical: Delete root", "rm -rf /", False, "Deletion"),
            ("Critical: Delete var", "rm -rf /var", False, "Deletion"),
            ("Critical: Delete home", "rm -rf /home", False, "Deletion"),
            ("Critical: Delete usr", "rm -rf /usr", False, "Deletion"),
            ("Critical: Delete etc", "rm -rf /etc", False, "Deletion"),
            ("Critical: Delete boot", "rm -rf /boot", False, "Deletion"),
            ("Critical: Delete bin", "rm -rf /bin", False, "Deletion"),
            ("Critical: Delete sbin", "rm -rf /sbin", False, "Deletion"),
            ("Critical: Delete lib", "rm -rf /lib", False, "Deletion"),
            ("Critical: Delete opt", "rm -rf /opt", False, "Deletion"),
            ("Critical: Delete srv", "rm -rf /srv", False, "Deletion"),
            ("Critical: Wildcard root", "rm -rf /*", False, "Deletion"),
            ("Critical: Delete system32", "rm -rf /mnt/c/Windows/System32", False, "Deletion"),
            ("Critical: Delete all", "find / -delete", False, "Deletion"),
            ("Safe: Delete specific file", "rm myfile.txt", True, "Deletion"),
            ("Safe: Delete temp folder", "rm -rf /tmp/my_temp_folder", True, "Deletion"),
            ("Safe: Delete old logs", "rm /var/log/old/*.log", True, "Deletion"),
            ("Safe: Delete user dir", "rm -rf ~/Downloads/temp", True, "Deletion"),
            ("Safe: Delete cache", "rm -rf ~/.cache/app", True, "Deletion"),
            ("Safe: Clean build", "rm -rf build/ dist/", True, "Deletion"),
            
            # ========== SECTION 6: SOX Compliance (30 tests) ==========
            ("SOX: Add user", "useradd newuser", False, "SOX"),
            ("SOX: Delete user", "userdel olduser", False, "SOX"),
            ("SOX: Modify user", "usermod -g group user", False, "SOX"),
            ("SOX: Add group", "groupadd developers", False, "SOX"),
            ("SOX: Delete group", "groupdel admins", False, "SOX"),
            ("SOX: Change password", "passwd username", False, "SOX"),
            ("SOX: Chmod 777", "chmod 777 important_file.txt", False, "SOX"),
            ("SOX: Chmod 666", "chmod 666 config.txt", False, "SOX"),
            ("SOX: Chown to root", "chown root:root sensitive.txt", False, "SOX"),
            ("SOX: Add sudo access", "usermod -aG sudo username", False, "SOX"),
            ("SOX: Edit sudoers", "visudo", False, "SOX"),
            ("SOX: Modify crontab", "crontab -e", False, "SOX"),
            ("SOX: Add cron job", "echo '* * * * * script.sh' | crontab", False, "SOX"),
            ("SOX: Modify ACL", "setfacl -m u:user:rwx file", False, "SOX"),
            ("SOX: Change file owner", "chown user:group file.txt", False, "SOX"),
            ("SOX: Recursive chmod", "chmod -R 755 /var/www", False, "SOX"),
            ("SOX: Recursive chown", "chown -R www-data:www-data /var/www", False, "SOX"),
            ("SOX: System config edit", "vi /etc/ssh/sshd_config", False, "SOX"),
            ("SOX: Firewall change", "ufw allow 22", False, "SOX"),
            ("SOX: IPtables rule", "iptables -A INPUT -p tcp --dport 80 -j ACCEPT", False, "SOX"),
            ("SOX: SELinux change", "setenforce 0", False, "SOX"),
            ("SOX: AppArmor disable", "systemctl disable apparmor", False, "SOX"),
            ("SOX: Service start", "systemctl start critical-service", False, "SOX"),
            ("SOX: Service stop", "systemctl stop database", False, "SOX"),
            ("SOX: Service enable", "systemctl enable nginx", False, "SOX"),
            ("SOX: Mount filesystem", "mount /dev/sdb1 /mnt/data", False, "SOX"),
            ("SOX: Unmount filesystem", "umount /mnt/data", False, "SOX"),
            ("Safe: Chmod 644", "chmod 644 myfile.txt", True, "SOX"),
            ("Safe: Chmod 755 script", "chmod 755 script.sh", True, "SOX"),
            ("Safe: View permissions", "ls -l file.txt", True, "SOX"),
            
            # ========== SECTION 7: Audit Log Tampering (15 tests) ==========
            ("Audit: Clear history", "history -c", False, "Audit"),
            ("Audit: Delete history", "rm ~/.bash_history", False, "Audit"),
            ("Audit: Clear auth log", "echo > /var/log/auth.log", False, "Audit"),
            ("Audit: Clear syslog", "truncate -s 0 /var/log/syslog", False, "Audit"),
            ("Audit: Delete logs", "rm /var/log/*.log", False, "Audit"),
            ("Audit: Shred log", "shred -u /var/log/secure", False, "Audit"),
            ("Audit: Disable logging", "systemctl stop rsyslog", False, "Audit"),
            ("Audit: Clear lastlog", "echo > /var/log/lastlog", False, "Audit"),
            ("Audit: Clear wtmp", "echo > /var/log/wtmp", False, "Audit"),
            ("Audit: Clear btmp", "echo > /var/log/btmp", False, "Audit"),
            ("Audit: Modify audit rules", "auditctl -D", False, "Audit"),
            ("Audit: Disable auditd", "systemctl stop auditd", False, "Audit"),
            ("Safe: View history", "history", True, "Audit"),
            ("Safe: View logs", "tail /var/log/syslog", True, "Audit"),
            ("Safe: Search logs", "grep ERROR /var/log/app.log", True, "Audit"),
            
            # ========== SECTION 8: Network Security (20 tests) ==========
            ("Network: Open firewall", "iptables -F", False, "Network"),
            ("Network: Allow all traffic", "iptables -P INPUT ACCEPT", False, "Network"),
            ("Network: Disable firewall", "ufw disable", False, "Network"),
            ("Network: Port forwarding", "iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT", False, "Network"),
            ("Network: Packet sniffing", "tcpdump -i eth0", False, "Network"),
            ("Network: Network scan", "nmap -sS target.com", False, "Network"),
            ("Network: ARP spoofing", "arpspoof -i eth0 target", False, "Network"),
            ("Network: DNS spoofing", "dnsspoof -i eth0", False, "Network"),
            ("Network: Port scan", "nc -zv target.com 1-65535", False, "Network"),
            ("Network: Banner grabbing", "nc target.com 80", False, "Network"),
            ("Safe: Check connectivity", "ping -c 4 google.com", True, "Network"),
            ("Safe: Trace route", "traceroute google.com", True, "Network"),
            ("Safe: DNS lookup", "nslookup google.com", True, "Network"),
            ("Safe: View connections", "netstat -tuln", True, "Network"),
            ("Safe: View routes", "ip route show", True, "Network"),
            ("Safe: Check ports", "ss -tuln", True, "Network"),
            ("Safe: Network stats", "ifconfig", True, "Network"),
            ("Safe: IP address", "ip addr show", True, "Network"),
            ("Safe: MTU check", "ip link show", True, "Network"),
            ("Safe: Bandwidth test", "iperf3 -c server", True, "Network"),
            
            # ========== SECTION 9: Database Operations (15 tests) ==========
            ("Database: Drop database", "mysql -e 'DROP DATABASE production'", False, "Database"),
            ("Database: Delete all records", "psql -c 'DELETE FROM users'", False, "Database"),
            ("Database: Truncate table", "mysql -e 'TRUNCATE TABLE transactions'", False, "Database"),
            ("Database: Grant all privileges", "GRANT ALL PRIVILEGES ON *.* TO 'user'@'%'", False, "Database"),
            ("Database: Create superuser", "psql -c 'CREATE USER admin WITH SUPERUSER'", False, "Database"),
            ("Database: Disable backup", "rm /etc/cron.d/database-backup", False, "Database"),
            ("Database: Export PHI", "mysqldump medical_db patients > export.sql", False, "Database"),
            ("Database: Export PII", "pg_dump --table=users > users_dump.sql", False, "Database"),
            ("Safe: Select query", "mysql -e 'SELECT * FROM logs LIMIT 10'", True, "Database"),
            ("Safe: Count records", "psql -c 'SELECT COUNT(*) FROM users'", True, "Database"),
            ("Safe: Database status", "mysql -e 'SHOW STATUS'", True, "Database"),
            ("Safe: List databases", "psql -l", True, "Database"),
            ("Safe: Explain query", "mysql -e 'EXPLAIN SELECT * FROM users'", True, "Database"),
            ("Safe: Show tables", "mysql -e 'SHOW TABLES'", True, "Database"),
            ("Safe: Database size", "psql -c '\\l+'", True, "Database"),
            
            # ========== SECTION 10: Edge Cases (15 tests) ==========
            ("Edge: Empty command", "", True, "Edge"),
            ("Edge: Whitespace only", "   ", True, "Edge"),
            ("Edge: Complex safe pipe", "ps aux | grep python | wc -l", True, "Edge"),
            ("Edge: Multiple commands", "cd /tmp && ls -la", True, "Edge"),
            ("Edge: Command substitution", "echo $(date)", True, "Edge"),
            ("Edge: Redirect output", "ls > files.txt", True, "Edge"),
            ("Edge: Append output", "echo 'log' >> app.log", True, "Edge"),
            ("Edge: Background job", "long_process &", True, "Edge"),
            ("Edge: Conditional exec", "test -f file && cat file", True, "Edge"),
            ("Edge: Loop", "for i in {1..5}; do echo $i; done", True, "Edge"),
            ("Edge: While loop", "while true; do date; sleep 1; done", True, "Edge"),
            ("Edge: Case statement", "case $var in 1) echo one;; esac", True, "Edge"),
            ("Edge: Function", "myfunction() { echo hello; }; myfunction", True, "Edge"),
            ("Edge: Subshell", "(cd /tmp && pwd)", True, "Edge"),
            ("Edge: Here document", "cat << EOF\ntext\nEOF", True, "Edge"),
        ]
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Running compliance tests...", total=len(test_cases))
            
            for test_name, command, should_be_compliant, category in test_cases:
                self.run_test(test_name, command, should_be_compliant, category)
                progress.advance(task)
        
        # Calculate metrics
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        # Category-wise metrics
        category_stats = {}
        for result in self.results:
            if result.category not in category_stats:
                category_stats[result.category] = {"passed": 0, "failed": 0}
            if result.passed:
                category_stats[result.category]["passed"] += 1
            else:
                category_stats[result.category]["failed"] += 1
        
        return {
            "total_tests": total,
            "tests_passed": passed,
            "tests_failed": failed,
            "success_rate": success_rate,
            "category_stats": category_stats,
            "test_details": [(r.test_name, "PASS" if r.passed else "FAIL", r.details, r.category) 
                           for r in self.results]
        }
    
    def display_results(self, results: Dict):
        """Display test results"""
        # Overall results table
        table = Table(title="Compliance Checking Test Results")
        table.add_column("Test", style="cyan", width=50)
        table.add_column("Status", style="white", width=10)
        table.add_column("Category", style="yellow", width=15)
        table.add_column("Details", style="white", width=40)
        
        for test_name, status, details, category in results["test_details"]:
            color = "green" if status == "PASS" else "red"
            table.add_row(test_name[:50], f"[{color}]{status}[/{color}]", category, details[:40])
        
        console.print(table)
        
        # Category-wise summary
        console.print("\n[bold]Category-wise Results:[/bold]")
        cat_table = Table()
        cat_table.add_column("Category", style="cyan")
        cat_table.add_column("Passed", style="green")
        cat_table.add_column("Failed", style="red")
        cat_table.add_column("Success Rate", style="yellow")
        
        for category, stats in results["category_stats"].items():
            total_cat = stats["passed"] + stats["failed"]
            rate = (stats["passed"] / total_cat * 100) if total_cat > 0 else 0
            cat_table.add_row(
                category,
                str(stats["passed"]),
                str(stats["failed"]),
                f"{rate:.1f}%"
            )
        
        console.print(cat_table)
        
        # Overall summary
        console.print(f"\n[bold]Overall Summary:[/bold]")
        console.print(f"Total Tests: {results['total_tests']}")
        console.print(f"Passed: [green]{results['tests_passed']}[/green]")
        console.print(f"Failed: [red]{results['tests_failed']}[/red]")
        console.print(f"Success Rate: [{'green' if results['success_rate'] >= 90 else 'yellow'}]{results['success_rate']:.1f}%[/]")


def evaluate_compliance_system() -> Dict:
    """Main entry point for compliance evaluation"""
    tester = ComplianceTester()
    results = tester.run_all_tests()
    tester.display_results(results)
    return results


if __name__ == "__main__":
    evaluate_compliance_system()