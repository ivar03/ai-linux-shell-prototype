import re
from datetime import datetime

# ==========================
# Compliance Rule Definitions
# ==========================

COMPLIANCE_RULES = [
    # -------------------
    # General Security
    # -------------------
    {
        "name": "No PII Exposure",
        "pattern": r"(cat|less|more)\s+.*(passwd|shadow|creditcard|ssn|patient)",
        "description": "Command may expose sensitive PII/PHI data."
    },
    {
        "name": "No Unencrypted Data Transfer",
        "pattern": r"\bftp\b|\btelnet\b",
        "description": "Insecure protocols used for data transfer (unencrypted)."
    },
    {
        "name": "No Passwords in Commands",
        "pattern": r"(--password|--pass|--pwd)\s+\S+",
        "description": "Password detected directly in command arguments."
    },
    {
        "name": "No Mass Deletion",
        "pattern": r"rm\s+-rf\s+/",
        "description": "Potential system-wide deletion detected."
    },
    # -------------------
    # SOX Compliance
    # -------------------
    {
        "name": "SOX: Logging Required",
        "pattern": r"(useradd|userdel|usermod|groupadd|groupdel|passwd)\b",
        "description": "User and group management must be logged under SOX compliance."
    },
    {
        "name": "SOX: File Permission Change",
        "pattern": r"chmod\s+[0-7]{3}\s+",
        "description": "File permission changes must be logged and reviewed under SOX."
    },
    # -------------------
    # HIPAA Compliance
    # -------------------
    {
        "name": "HIPAA: No PHI Exposure",
        "pattern": r"(cat|less|more)\s+.*(patient|medical|health|record)",
        "description": "Potential PHI exposure without proper audit logging."
    },
    {
        "name": "HIPAA: Encrypted Transfers",
        "pattern": r"\bftp\b|\btelnet\b",
        "description": "HIPAA requires secure, encrypted transfers for ePHI."
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
