import re
from datetime import datetime

# ==========================
# Compliance Rule Definitions
# ==========================

COMPLIANCE_RULES = [
    # -------------------
    # PII Protection
    # -------------------
    {
        "name": "No PII Exposure - Sensitive Files",
        "pattern": r"(cat|less|more|grep|awk|sed|tail|head)\s+.*(passwd|shadow|creditcard|ssn|patient)",
        "description": "Command may expose sensitive PII/PHI data."
    },
    {
        "name": "No PII - Social Security",
        "pattern": r"(cat|grep|echo|print).*\b(social.?security|ssn)\b",
        "description": "Potential social security number exposure."
    },
    {
        "name": "No PII - Personal Info",
        "pattern": r"(cat|grep|less|more).*\b(personal.?info|personal.?data)\b",
        "description": "Potential personal information exposure."
    },
    {
        "name": "No PII - Customer Data",
        "pattern": r"(cat|grep|less|more).*\b(customer.?data|customer.?info)\b",
        "description": "Potential customer data exposure."
    },
    {
        "name": "No PII - User Credentials",
        "pattern": r"(cat|grep|less|more).*\b(credentials|user.?pass)\b",
        "description": "Potential user credentials exposure."
    },
    {
        "name": "No PII - Email Addresses",
        "pattern": r"(cat|grep|less|more).*\b(email.?address|emails)\b",
        "description": "Potential email address exposure."
    },
    {
        "name": "No PII - Phone Numbers",
        "pattern": r"(cat|grep|less|more).*\b(phone.?number|phone.?data)\b",
        "description": "Potential phone number exposure."
    },

    # -------------------
    # HIPAA Compliance
    # -------------------
    {
        "name": "HIPAA: No PHI Exposure",
        "pattern": r"(cat|less|more|grep)\s+.*(patient|medical|health|record)",
        "description": "Potential PHI exposure without proper audit logging."
    },
    {
        "name": "HIPAA: PHI Database",
        "pattern": r"(mysql|psql|sqlite3).*\b(phi|patient_data)\b",
        "description": "Direct access to PHI database detected."
    },
    {
        "name": "HIPAA: Diagnosis Data",
        "pattern": r"(cat|grep|less).*\b(diagnosis|diagnostic)\b",
        "description": "Access to diagnosis codes/data."
    },
    {
        "name": "HIPAA: Treatment Plans",
        "pattern": r"(cat|grep|less).*\b(treatment|therapy)\b",
        "description": "Access to treatment plan data."
    },
    {
        "name": "HIPAA: Lab Results",
        "pattern": r"(cat|grep|less).*\b(lab.?result|laboratory)\b",
        "description": "Access to lab results."
    },
    {
        "name": "HIPAA: Prescription Data",
        "pattern": r"(cat|grep|less).*\b(prescription|medication|pharma)\b",
        "description": "Access to prescription data."
    },
    {
        "name": "HIPAA: Insurance Info",
        "pattern": r"(cat|grep|less).*\b(insurance|coverage)\b",
        "description": "Access to insurance information."
    },
    {
        "name": "HIPAA: Encrypted Transfers",
        "pattern": r"\b(ftp|telnet)\b(?!s)",
        "description": "HIPAA requires secure, encrypted transfers for ePHI."
    },

    # -------------------
    # GDPR Compliance
    # -------------------
    {
        "name": "GDPR: Personal Data",
        "pattern": r"(export|dump|backup).*\b(personal.?data|gdpr)\b",
        "description": "GDPR personal data export requires documentation."
    },
    {
        "name": "GDPR: EU Citizen Data",
        "pattern": r"(select|export).*\b(eu.?users|eu.?citizens)\b",
        "description": "EU citizen data access requires consent tracking."
    },
    {
        "name": "GDPR: Consent Records",
        "pattern": r"(delete|drop|truncate).*\b(consent|privacy.?settings)\b",
        "description": "Deleting consent records violates GDPR retention."
    },
    {
        "name": "GDPR: Data Subject Info",
        "pattern": r"(cat|grep|export).*\b(data.?subject|user.?profile)\b",
        "description": "Data subject information access must be logged."
    },

    # -------------------
    # PCI-DSS Compliance
    # -------------------
    {
        "name": "PCI: Card Numbers",
        "pattern": r"(cat|grep|echo).*\b(card.?number|credit.?card)\b",
        "description": "Credit card number exposure violates PCI-DSS."
    },
    {
        "name": "PCI: CVV Codes",
        "pattern": r"(cat|grep|echo).*\b(cvv|cvc|security.?code)\b",
        "description": "CVV code storage/exposure violates PCI-DSS."
    },
    {
        "name": "PCI: Payment Data",
        "pattern": r"(cat|grep|dump).*\b(payment.?data|transaction)\b",
        "description": "Payment data access requires encryption."
    },
    {
        "name": "PCI: Cardholder Data",
        "pattern": r"(export|backup|dump).*\b(cardholder|card.?data)\b",
        "description": "Cardholder data must be encrypted at rest."
    },
    {
        "name": "PCI: Transaction Log",
        "pattern": r"(cat|grep|less).*\b(transaction.?log|payment.?log)\b",
        "description": "Transaction log access must be audited."
    },

    # -------------------
    # Password Security
    # -------------------
    {
        "name": "No Passwords in Commands",
        "pattern": r"(-p\s+\S+|--password\s+\S+|--pass\s+\S+|--pwd\s+\S+|password=\S+)",
        "description": "Password detected directly in command arguments."
    },
    {
        "name": "MySQL Password in Command",
        "pattern": r"mysql.*-p\S+",
        "description": "MySQL password in command line."
    },
    {
        "name": "PostgreSQL Password",
        "pattern": r"(psql|pg_dump).*password",
        "description": "PostgreSQL password in command."
    },
    {
        "name": "Redis Password",
        "pattern": r"redis-cli.*-a\s+\S+",
        "description": "Redis password in command line."
    },
    {
        "name": "MongoDB Password",
        "pattern": r"mongo.*--password\s+\S+",
        "description": "MongoDB password in command line."
    },
    {
        "name": "Ansible Vault Password",
        "pattern": r"ansible.*--vault-password\s+\S+",
        "description": "Ansible vault password in command."
    },
    {
        "name": "Docker Login Password",
        "pattern": r"docker\s+login.*-p\s+\S+",
        "description": "Docker password in command line."
    },
    {
        "name": "Git Credential Password",
        "pattern": r"git.*://.*:.*@",
        "description": "Git credential with password in URL."
    },
    {
        "name": "Curl Authentication",
        "pattern": r"curl.*-u\s+\S+:\S+",
        "description": "Curl authentication with password."
    },
    {
        "name": "Wget Authentication",
        "pattern": r"wget.*--password\s+\S+",
        "description": "Wget password in command."
    },
    {
        "name": "API Key Inline",
        "pattern": r"(api.?key|apikey|auth.?token)=\S+",
        "description": "API key or auth token in command."
    },
    {
        "name": "AWS Credentials",
        "pattern": r"(AWS_ACCESS_KEY|AWS_SECRET)",
        "description": "AWS credentials in command."
    },

    # -------------------
    # Encryption Requirements
    # -------------------
    {
        "name": "No Unencrypted FTP",
        "pattern": r"\bftp\s+",
        "description": "Unencrypted FTP protocol detected."
    },
    {
        "name": "No Unencrypted Telnet",
        "pattern": r"\btelnet\s+",
        "description": "Unencrypted Telnet protocol detected."
    },
    {
        "name": "No HTTP Transfer",
        "pattern": r"(curl|wget).*http://(?!localhost|127\.0\.0\.1)",
        "description": "Unencrypted HTTP transfer detected."
    },
    {
        "name": "No Plain SMTP",
        "pattern": r"(sendmail|smtp).*port\s+25\b",
        "description": "Unencrypted SMTP detected."
    },
    {
        "name": "No TFTP",
        "pattern": r"\btftp\s+",
        "description": "Unencrypted TFTP protocol."
    },
    {
        "name": "No Rlogin",
        "pattern": r"\brlogin\s+",
        "description": "Insecure rlogin protocol."
    },
    {
        "name": "No Rsh",
        "pattern": r"\brsh\s+",
        "description": "Insecure rsh protocol."
    },
    {
        "name": "No Rexec",
        "pattern": r"\brexec\s+",
        "description": "Insecure rexec protocol."
    },

    # -------------------
    # Dangerous Deletions
    # -------------------
    {
        "name": "No Mass Deletion",
        "pattern": r"rm\s+-rf\s+/\s*$",
        "description": "Potential system-wide deletion detected."
    },
    {
        "name": "Delete All Files",
        "pattern": r"rm\s+-rf?\s+/\*",
        "description": "Attempting to delete all files."
    },

    # -------------------
    # SOX Compliance
    # -------------------
    {
        "name": "SOX: User Management",
        "pattern": r"(useradd|userdel|usermod|groupadd|groupdel|passwd)\b",
        "description": "User and group management must be logged under SOX."
    },
    {
        "name": "SOX: Permission Changes",
        "pattern": r"chmod\s+(777|666)\b",
        "description": "Overly permissive file permissions."
    },
    {
        "name": "SOX: Chown to Root",
        "pattern": r"chown.*root:",
        "description": "Changing ownership to root requires approval."
    },
    {
        "name": "SOX: Sudoers Edit",
        "pattern": r"(vi|vim|nano|edit).*sudoers",
        "description": "Sudoers file modification must be logged."
    },
    {
        "name": "SOX: Crontab Modification",
        "pattern": r"crontab\s+-e",
        "description": "Crontab modification must be audited."
    },
    {
        "name": "SOX: Add Cron Job",
        "pattern": r"(crontab|at\s+)",
        "description": "Scheduled task creation requires approval."
    },
    {
        "name": "SOX: ACL Modification",
        "pattern": r"(setfacl|getfacl)",
        "description": "ACL changes must be logged."
    },
    {
        "name": "SOX: File Ownership Change",
        "pattern": r"chown\s+",
        "description": "File ownership changes must be logged."
    },
    {
        "name": "SOX: Recursive Chmod",
        "pattern": r"chmod\s+-R",
        "description": "Recursive permission changes require review."
    },
    {
        "name": "SOX: Recursive Chown",
        "pattern": r"chown\s+-R",
        "description": "Recursive ownership changes require review."
    },
    {
        "name": "SOX: System Config Edit",
        "pattern": r"(vi|vim|nano|edit).*/etc/(sysconfig|default)",
        "description": "System configuration changes must be logged."
    },
    {
        "name": "SOX: Firewall Change",
        "pattern": r"(ufw|firewalld|firewall-cmd)\s+",
        "description": "Firewall changes must be approved."
    },
    {
        "name": "SOX: IPTables Rule",
        "pattern": r"iptables\s+",
        "description": "Firewall rule changes must be audited."
    },
    {
        "name": "SOX: SELinux Change",
        "pattern": r"(setenforce|setsebool)",
        "description": "SELinux changes must be documented."
    },
    {
        "name": "SOX: AppArmor Disable",
        "pattern": r"(aa-disable|apparmor)",
        "description": "Security policy changes require approval."
    },
    {
        "name": "SOX: Service Start",
        "pattern": r"(systemctl\s+start|service\s+\S+\s+start)",
        "description": "Service state changes must be logged."
    },
    {
        "name": "SOX: Service Stop",
        "pattern": r"(systemctl\s+stop|service\s+\S+\s+stop)",
        "description": "Service state changes must be logged."
    },
    {
        "name": "SOX: Service Enable",
        "pattern": r"systemctl\s+enable",
        "description": "Service autostart changes must be approved."
    },
    {
        "name": "SOX: Mount Filesystem",
        "pattern": r"mount\s+",
        "description": "Filesystem mount operations must be logged."
    },
    {
        "name": "SOX: Unmount Filesystem",
        "pattern": r"umount\s+",
        "description": "Filesystem unmount operations must be logged."
    },

    # -------------------
    # Audit Trail Protection
    # -------------------
    {
        "name": "Audit: Clear History",
        "pattern": r"(history\s+-c|>\s*~?/.bash_history)",
        "description": "Clearing command history violates audit requirements."
    },
    {
        "name": "Audit: Delete History",
        "pattern": r"rm.*\.bash_history",
        "description": "Deleting command history violates audit requirements."
    },
    {
        "name": "Audit: Clear Auth Log",
        "pattern": r"(>|truncate).*/(var/)?log/auth",
        "description": "Clearing authentication logs violates audit requirements."
    },
    {
        "name": "Audit: Clear Syslog",
        "pattern": r"(>|truncate).*/(var/)?log/syslog",
        "description": "Clearing system logs violates audit requirements."
    },
    {
        "name": "Audit: Delete Logs",
        "pattern": r"rm.*/(var/)?log/",
        "description": "Deleting log files violates audit requirements."
    },
    {
        "name": "Audit: Shred Log",
        "pattern": r"shred.*/(var/)?log/",
        "description": "Destroying log files violates audit requirements."
    },
    {
        "name": "Audit: Disable Logging",
        "pattern": r"(systemctl\s+stop|service\s+\S+\s+stop).*(syslog|rsyslog|journal)",
        "description": "Disabling logging violates audit requirements."
    },
    {
        "name": "Audit: Clear Lastlog",
        "pattern": r"(>|truncate).*lastlog",
        "description": "Clearing lastlog violates audit requirements."
    },
    {
        "name": "Audit: Clear Wtmp",
        "pattern": r"(>|truncate).*wtmp",
        "description": "Clearing wtmp violates audit requirements."
    },
    {
        "name": "Audit: Clear Btmp",
        "pattern": r"(>|truncate).*btmp",
        "description": "Clearing btmp violates audit requirements."
    },
    {
        "name": "Audit: Modify Audit Rules",
        "pattern": r"(auditctl|aureport)",
        "description": "Audit rule modification must be logged."
    },
    {
        "name": "Audit: Disable Auditd",
        "pattern": r"(systemctl\s+stop|service\s+\S+\s+stop).*audit",
        "description": "Disabling audit daemon violates compliance."
    },

    # -------------------
    # Network Security
    # -------------------
    {
        "name": "Network: Open Firewall",
        "pattern": r"(iptables\s+-F|ufw\s+allow)",
        "description": "Opening firewall requires security review."
    },
    {
        "name": "Network: Allow All Traffic",
        "pattern": r"iptables.*ACCEPT.*0\.0\.0\.0",
        "description": "Allowing all traffic is a security risk."
    },
    {
        "name": "Network: Disable Firewall",
        "pattern": r"(ufw\s+disable|systemctl\s+stop.*firewall)",
        "description": "Disabling firewall violates security policy."
    },
    {
        "name": "Network: Port Forwarding",
        "pattern": r"(iptables.*PREROUTING|socat.*TCP-LISTEN)",
        "description": "Port forwarding requires security approval."
    },
    {
        "name": "Network: Packet Sniffing",
        "pattern": r"(tcpdump|wireshark|tshark)",
        "description": "Network sniffing must be authorized."
    },
    {
        "name": "Network: Network Scan",
        "pattern": r"(nmap|masscan|zmap)",
        "description": "Network scanning must be authorized."
    },
    {
        "name": "Network: ARP Spoofing",
        "pattern": r"(arpspoof|ettercap)",
        "description": "ARP spoofing is prohibited."
    },
    {
        "name": "Network: DNS Spoofing",
        "pattern": r"(dnsspoof|dnschef)",
        "description": "DNS spoofing is prohibited."
    },
    {
        "name": "Network: Port Scan",
        "pattern": r"nmap.*-p",
        "description": "Port scanning requires authorization."
    },
    {
        "name": "Network: Banner Grabbing",
        "pattern": r"(nc|netcat|telnet).*\d+$",
        "description": "Banner grabbing must be authorized."
    },

    # -------------------
    # Database Security
    # -------------------
    {
        "name": "Database: Drop Database",
        "pattern": r"(DROP\s+DATABASE|DROP\s+SCHEMA)",
        "description": "Dropping database requires approval."
    },
    {
        "name": "Database: Delete All Records",
        "pattern": r"DELETE\s+FROM\s+\S+\s*(;|$)",
        "description": "Deleting all records requires approval."
    },
    {
        "name": "Database: Truncate Table",
        "pattern": r"TRUNCATE\s+TABLE",
        "description": "Truncating table requires approval."
    },
    {
        "name": "Database: Grant All Privileges",
        "pattern": r"GRANT\s+ALL",
        "description": "Granting all privileges violates least privilege."
    },
    {
        "name": "Database: Create Superuser",
        "pattern": r"CREATE\s+USER.*SUPERUSER",
        "description": "Creating superuser requires approval."
    },
    {
        "name": "Database: Disable Backup",
        "pattern": r"(ALTER|SET).*archive_mode\s*=\s*off",
        "description": "Disabling backups violates data protection."
    },
    {
        "name": "Database: Export PHI",
        "pattern": r"(mysqldump|pg_dump).*patient",
        "description": "Exporting PHI requires encryption."
    },
    {
        "name": "Database: Export PII",
        "pattern": r"(mysqldump|pg_dump).*(user|customer|personal)",
        "description": "Exporting PII requires approval and encryption."
    },
]

# ==========================
# Core Functions
# ==========================

def check_compliance(command: str):
    """
    Check a command against compliance rules.

    Returns:
        List of failed compliance checks.
    """
    failures = []
    for rule in COMPLIANCE_RULES:
        if re.search(rule["pattern"], command, re.IGNORECASE):
            failures.append({
                "rule": rule["name"],
                "description": rule["description"],
                "pattern": rule["pattern"],
                "command": command
            })
    return failures

def is_compliant(command: str):
    """
    Returns True if the command passes all compliance checks.
    """
    return len(check_compliance(command)) == 0

def generate_compliance_report(command: str, user: str = "unknown_user"):
    """
    Generate a structured compliance report for a command.
    """
    failures = check_compliance(command)
    passed = len(failures) == 0
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "user": user,
        "command": command,
        "compliant": passed,
        "failures": failures
    }
    return report

def print_compliance_report(report: dict):
    """
    Print the compliance report in a human-readable format.
    """
    from rich import print
    from rich.panel import Panel

    if report["compliant"]:
        print(Panel(
            f"Command is compliant.\n"
            f"Command: {report['command']}\n"
            f"Checked at: {report['timestamp']} by {report['user']}",
            title="Compliance Check Passed",
            border_style="green"
        ))
    else:
        failure_list = "\n".join(
            [f"- {f['rule']}: {f['description']}" for f in report["failures"]]
        )
        print(Panel(
            f"Command is NOT compliant.\n"
            f"Command: {report['command']}\n"
            f"Failures:\n{failure_list}\n"
            f"Checked at: {report['timestamp']} by {report['user']}",
            title="Compliance Check Failed",
            border_style="red"
        ))
