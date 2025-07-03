from .safety_checker import SafetyChecker, SafetyResult, RiskLevel
from .command_runner import CommandRunner, ExecutionResult, ExecutionStatus

__all__ = [
    'SafetyChecker', 
    'SafetyResult', 
    'RiskLevel',
    'CommandRunner', 
    'ExecutionResult', 
    'ExecutionStatus'
]

# Package version
__version__ = "0.1.0"

# Default safety configuration
DEFAULT_SAFETY_CONFIG = {
    "enable_safety_checks": True,
    "block_high_risk": True,
    "warn_medium_risk": True,
    "log_all_commands": True,
    "dry_run_destructive": False,
    "timeout_seconds": 300,  # 5 minutes default timeout
    "max_output_lines": 1000,
    "allow_sudo": False,
    "allow_network": True,
    "allow_file_operations": True,
}

# Command execution limits
EXECUTION_LIMITS = {
    "max_runtime_seconds": 300,
    "max_memory_mb": 1024,
    "max_output_size_mb": 10,
    "max_processes": 10,
    "max_open_files": 100,
}

# Safety risk levels
RISK_LEVELS = {
    "LOW": "Commands with minimal system impact",
    "MEDIUM": "Commands that modify files or system state",
    "HIGH": "Potentially destructive or dangerous commands",
    "CRITICAL": "Commands that could cause system damage"
}

# Common dangerous command patterns
DANGEROUS_PATTERNS = [
    # File system destruction
    r"rm\s+.*-rf\s*/",
    r"rm\s+.*-rf\s*\$",
    r"rm\s+.*-rf\s*~",
    r"rm\s+.*-rf\s*\.",
    r"dd\s+.*of=/dev/",
    r"mkfs\.",
    r"format\s+",
    
    # System modification
    r"sudo\s+rm",
    r"sudo\s+dd",
    r"sudo\s+mkfs",
    r"sudo\s+fdisk",
    r"sudo\s+parted",
    r"chmod\s+.*777",
    r"chown\s+.*root",
    
    # Network/Security
    r"curl\s+.*\|\s*sh",
    r"wget\s+.*\|\s*sh",
    r"nc\s+.*-l.*-e",
    r"socat\s+.*EXEC",
    
    # Process manipulation
    r"kill\s+-9\s+1",
    r"killall\s+-9\s+init",
    r"pkill\s+-9\s+.*",
    
    # System shutdown
    r"shutdown\s+",
    r"reboot\s*",
    r"halt\s*",
    r"poweroff\s*",
]

# Commands that require elevated privileges
PRIVILEGE_COMMANDS = [
    "sudo", "su", "mount", "umount", "fdisk", "parted", "mkfs", 
    "fsck", "iptables", "systemctl", "service", "chkconfig",
    "useradd", "userdel", "usermod", "groupadd", "groupdel",
    "crontab", "at", "batch"
]

# Commands that can modify system files
SYSTEM_MODIFYING_COMMANDS = [
    "rm", "mv", "cp", "dd", "shred", "truncate", "tee",
    "chmod", "chown", "chgrp", "setfacl", "ln", "unlink",
    "mkdir", "rmdir", "touch", "install"
]

# Network commands that might pose security risks
NETWORK_COMMANDS = [
    "curl", "wget", "nc", "netcat", "socat", "ssh", "scp", "rsync",
    "ftp", "sftp", "telnet", "nmap", "tcpdump", "wireshark"
]

# File extensions that might contain executables
EXECUTABLE_EXTENSIONS = [
    ".sh", ".bash", ".py", ".pl", ".rb", ".php", ".js", ".exe", 
    ".bin", ".run", ".deb", ".rpm", ".msi", ".dmg", ".pkg"
]

# Default allowed commands (whitelist for high-security environments)
SAFE_COMMANDS = [
    # File listing and information
    "ls", "ll", "la", "dir", "tree", "file", "stat", "du", "df",
    "pwd", "basename", "dirname", "realpath", "readlink",
    
    # Text processing
    "cat", "less", "more", "head", "tail", "grep", "egrep", "fgrep",
    "sed", "awk", "cut", "sort", "uniq", "tr", "wc", "diff", "comm",
    
    # System information
    "ps", "top", "htop", "free", "uptime", "uname", "whoami", "id",
    "groups", "finger", "w", "who", "last", "history", "env", "printenv",
    
    # Process information (read-only)
    "pgrep", "pstree", "jobs", "lsof", "netstat", "ss",
    
    # Archive operations (read-only)
    "tar", "gzip", "gunzip", "zip", "unzip", "7z", "compress", "uncompress",
    
    # Network information (read-only)
    "ping", "dig", "nslookup", "host", "traceroute", "curl", "wget",
]

# Commands that are generally safe but should be monitored
MONITORED_COMMANDS = [
    "find", "locate", "which", "whereis", "type", "command",
    "echo", "printf", "date", "cal", "bc", "expr", "test",
    "sleep", "timeout", "time", "watch", "yes", "seq", "shuf",
    "base64", "md5sum", "sha1sum", "sha256sum", "cksum",
]

# Default timeout values for different command types
COMMAND_TIMEOUTS = {
    "network": 30,      # Network operations
    "file": 60,         # File operations
    "process": 10,      # Process operations
    "system": 120,      # System information
    "default": 30,      # Default timeout
}

# Resource limits for command execution
RESOURCE_LIMITS = {
    "max_cpu_percent": 80,
    "max_memory_mb": 512,
    "max_disk_io_mb": 100,
    "max_network_kb": 1024,
}

def get_safety_config() -> dict:
    return DEFAULT_SAFETY_CONFIG.copy()

def get_execution_limits() -> dict:
    return EXECUTION_LIMITS.copy()

def is_dangerous_pattern(command: str) -> bool:
    import re
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

def requires_privileges(command: str) -> bool:
    words = command.split()
    if not words:
        return False
    
    first_word = words[0]
    return first_word in PRIVILEGE_COMMANDS

def get_command_category(command: str) -> str:
    if not command:
        return "unknown"
    
    first_word = command.split()[0]
    
    if first_word in NETWORK_COMMANDS:
        return "network"
    elif first_word in SYSTEM_MODIFYING_COMMANDS:
        return "file_system"
    elif first_word in PRIVILEGE_COMMANDS:
        return "privileged"
    elif first_word in SAFE_COMMANDS:
        return "safe"
    elif first_word in MONITORED_COMMANDS:
        return "monitored"
    else:
        return "unknown"

def get_recommended_timeout(command: str) -> int:
    category = get_command_category(command)
    return COMMAND_TIMEOUTS.get(category, COMMAND_TIMEOUTS["default"])