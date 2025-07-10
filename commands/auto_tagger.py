from typing import List

# Optional: Extend or externalize into a JSON config later
SAFE_COMMANDS = [
    "ls", "cat", "df", "du", "free", "ps", "top", "uptime", "pwd", "whoami",
    "id", "date", "cal", "echo"
]

CLEANUP_KEYWORDS = [
    "rm", "clean", "delete", "purge", "prune", "wipe", "rmdir", "trash", "autoremove"
]

MONITORING_KEYWORDS = [
    "htop", "top", "watch", "vmstat", "iostat", "dstat", "glances"
]

NETWORK_KEYWORDS = [
    "ping", "curl", "wget", "ssh", "scp", "ftp", "sftp", "nc", "nmap", "telnet"
]

INSTALL_KEYWORDS = [
    "install", "update", "upgrade", "apt", "yum", "dnf", "pacman", "brew", "pip", "npm"
]

BACKUP_KEYWORDS = [
    "backup", "copy", "cp", "rsync", "tar", "zip", "gzip", "bzip2"
]

READ_ONLY_COMMANDS = SAFE_COMMANDS + [
    "find", "grep", "less", "more", "head", "tail", "wc", "sort", "uniq"
]


def auto_tag(query: str, command: str) -> List[str]:
    tags = []
    cmd_lower = command.lower()
    query_lower = query.lower()
    combined_text = f"{query_lower} {cmd_lower}"

    # Safety tags
    if any(cmd_lower.startswith(cmd) for cmd in SAFE_COMMANDS + READ_ONLY_COMMANDS):
        tags.append("safe")

    # Cleanup
    if any(kw in combined_text for kw in CLEANUP_KEYWORDS):
        tags.append("cleanup")

    # Monitoring
    if any(kw in combined_text for kw in MONITORING_KEYWORDS):
        tags.append("monitoring")

    # Network
    if any(kw in combined_text for kw in NETWORK_KEYWORDS):
        tags.append("network")

    # Install / Update
    if any(kw in combined_text for kw in INSTALL_KEYWORDS):
        tags.append("install")

    # Backup / Copy
    if any(kw in combined_text for kw in BACKUP_KEYWORDS):
        tags.append("backup")

    # Resource-intensive commands (example: compile/build)
    if any(kw in combined_text for kw in ["make", "build", "compile", "gcc", "mvn"]):
        tags.append("resource-intensive")

    # Add unique tags only
    return list(set(tags))