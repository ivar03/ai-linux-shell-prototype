import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import shlex
import json
from pathlib import Path

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
        self.denylist = self._load_denylist()
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

    def _load_denylist(self) -> Dict[str, List[str]]:
        default_path = Path(__file__).parent / "denylist.json"
        if default_path.exists():
            with open(default_path, "r") as f:
                return json.load(f)
        else:
            # fallback hardcoded denylist
            return {
                "high": ["rm -rf /", ":(){:|:&};:", "mkfs", "dd of=/dev/sd"],
                "medium": ["shutdown", "reboot", "poweroff"],
                "low": ["pkill", "killall"]
            }

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

        syntax_ok, syntax_msg = self.validate_command_syntax(command)
        if not syntax_ok:
            return SafetyResult(
                is_safe=False,
                risk_level=RiskLevel.MEDIUM.value,
                reason=f"Invalid syntax: {syntax_msg}"
            )

        if len(command) > self.config["max_command_length"]:
            return SafetyResult(
                is_safe=False,
                risk_level=RiskLevel.MEDIUM.value,
                reason=f"Command too long ({len(command)} chars)"
            )

        # Denylist check (from JSON)
        denylist_check = self._check_against_denylist(command)
        if not denylist_check.is_safe:
            return denylist_check

        dangerous_check = self._check_dangerous_patterns(command)
        if not dangerous_check.is_safe:
            return dangerous_check

        privilege_check = self._check_privilege_commands(command)
        if not privilege_check.is_safe:
            return privilege_check

        destructive_check = self._check_destructive_commands(command)
        if not destructive_check.is_safe:
            return destructive_check

        network_check = self._check_network_commands(command)
        if not network_check.is_safe:
            return network_check

        path_check = self._check_file_paths(command)
        if not path_check.is_safe:
            return path_check

        wildcard_check = self._check_wildcards(command)
        if not wildcard_check.is_safe:
            return wildcard_check

        return SafetyResult(
            is_safe=True,
            risk_level=RiskLevel.LOW.value,
            reason="Command passed all safety checks"
        )

    def _check_against_denylist(self, command: str) -> SafetyResult:
        matched = []
        for level, patterns in self.denylist.items():
            for pattern in patterns:
                if re.search(re.escape(pattern), command, re.IGNORECASE):
                    matched.append(pattern)
                    risk = RiskLevel[level.upper()].value
                    return SafetyResult(
                        is_safe=False,
                        risk_level=risk,
                        reason=f"Command matches denylist ({level}): {pattern}",
                        blocked_patterns=matched
                    )
        return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")

    def _check_dangerous_patterns(self, command: str) -> SafetyResult:
        matched = []
        for pattern in [
            r":\(\)\{.*\}",
            r"while\s+true.*do.*done",
            r"yes\s+.*\|\s*.*"
        ]:
            if re.search(pattern, command, re.IGNORECASE):
                matched.append(pattern)
        if matched:
            return SafetyResult(
                is_safe=False,
                risk_level=RiskLevel.CRITICAL.value,
                reason="Matches dangerous known pattern",
                blocked_patterns=matched
            )
        return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")

    def _check_privilege_commands(self, command: str) -> SafetyResult:
        words = shlex.split(command.lower())
        if not words:
            return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")

        first = words[0]
        if first == "sudo" and not self.config["allow_sudo"]:
            return SafetyResult(
                is_safe=False,
                risk_level=RiskLevel.HIGH.value,
                reason="sudo is blocked",
                suggestions=["Run without sudo"]
            )
        if first in self.privilege_commands:
            return SafetyResult(
                is_safe=False,
                risk_level=RiskLevel.HIGH.value,
                reason=f"Privileged command blocked: {first}",
                suggestions=["Reconsider needing privileges"]
            )
        return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")

    def _check_destructive_commands(self, command: str) -> SafetyResult:
        words = shlex.split(command.lower())
        if not words:
            return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")
        first = words[0]
        if first in self.destructive_commands and not self.config["allow_destructive"]:
            return SafetyResult(
                is_safe=False,
                risk_level=RiskLevel.HIGH.value,
                reason=f"Destructive command not allowed: {first}"
            )
        return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")

    def _check_network_commands(self, command: str) -> SafetyResult:
        words = shlex.split(command.lower())
        if not words:
            return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")
        first = words[0]
        if first in self.network_commands and not self.config["allow_network"]:
            return SafetyResult(
                is_safe=False,
                risk_level=RiskLevel.MEDIUM.value,
                reason=f"Network command blocked: {first}"
            )
        if "|" in command and any(shell in command for shell in ["sh", "bash"]):
            return SafetyResult(
                is_safe=False,
                risk_level=RiskLevel.CRITICAL.value,
                reason="Network command piped to shell detected"
            )
        return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")

    def _check_file_paths(self, command: str) -> SafetyResult:
        critical = ["/etc/", "/boot/", "/usr/", "/lib/", "/lib64/", "/bin/", "/sbin/"]
        for path in critical:
            if path in command:
                return SafetyResult(
                    is_safe=False,
                    risk_level=RiskLevel.HIGH.value,
                    reason=f"Operation on critical path: {path}"
                )
        return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")

    def _check_wildcards(self, command: str) -> SafetyResult:
        if not self.config["warn_on_wildcards"]:
            return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")
        for pattern in [r"rm\s+.*\*", r"chmod\s+.*\*", r"chown\s+.*\*"]:
            if re.search(pattern, command, re.IGNORECASE):
                return SafetyResult(
                    is_safe=True,
                    risk_level=RiskLevel.MEDIUM.value,
                    reason="Wildcard used; caution advised",
                    suggestions=["Double-check wildcard scope"]
                )
        return SafetyResult(is_safe=True, risk_level=RiskLevel.LOW.value, reason="")

    def validate_command_syntax(self, command: str) -> Tuple[bool, str]:
        try:
            shlex.split(command)
            return True, "Syntax OK"
        except ValueError as e:
            return False, str(e)
