import platform
import os
import shutil
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path

@dataclass
class SystemContext:
    os_name: str
    distribution: str
    shell: str
    available_tools: List[str]
    current_dir: str
    user: str
    permissions: str

class PromptGenerator:
    def __init__(self):
        self.system_context = self._gather_system_context()
        self.command_categories = self._load_command_categories()

    def _gather_system_context(self) -> SystemContext:
        try:
            os_name = platform.system()
            distribution = "Unknown"
            if os_name == "Linux":
                try:
                    with open('/etc/os-release', 'r') as f:
                        for line in f:
                            if line.startswith('NAME='):
                                distribution = line.split('=')[1].strip().strip('"')
                                break
                except:
                    distribution = "Linux"
            shell = os.environ.get('SHELL', '/bin/bash').split('/')[-1]
            common_tools = ['find', 'grep', 'awk', 'sed', 'sort', 'uniq', 'cut', 'tar', 'gzip', 'curl', 'wget']
            available_tools = [tool for tool in common_tools if shutil.which(tool)]
            current_dir = str(Path.cwd())
            user = os.environ.get('USER', 'unknown')
            permissions = "root" if os.getuid() == 0 else "user"

            return SystemContext(
                os_name=os_name,
                distribution=distribution,
                shell=shell,
                available_tools=available_tools,
                current_dir=current_dir,
                user=user,
                permissions=permissions
            )
        except Exception:
            return SystemContext(
                os_name="Linux",
                distribution="Unknown",
                shell="bash",
                available_tools=['find', 'grep', 'ls', 'cat'],
                current_dir="/",
                user="user",
                permissions="user"
            )

    def _load_command_categories(self) -> Dict[str, List[str]]:
        return {
            "file_operations": ["find", "locate", "ls", "du", "df"],
            "process_management": ["ps", "top", "kill", "pkill"],
            "network": ["ping", "curl", "wget"],
            "system_info": ["uname", "uptime", "free"],
            "text_processing": ["grep", "sed", "awk"],
            "archive": ["tar", "gzip", "zip"],
            "permissions": ["chmod", "chown"]
        }

    def generate_system_prompt(self, category: Optional[str] = None, mode: str = "default") -> str:
        base_prompt = (
            f"You are a Linux CLI command generator for {self.system_context.distribution} using {self.system_context.shell}.\n\n"
            f"SYSTEM CONTEXT:\n"
            f"- OS: {self.system_context.os_name} ({self.system_context.distribution})\n"
            f"- Shell: {self.system_context.shell}\n"
            f"- User: {self.system_context.user} ({self.system_context.permissions})\n"
            f"- Current directory: {self.system_context.current_dir}\n"
            f"- Available tools: {', '.join(self.system_context.available_tools[:10])}\n\n"
            f"RULES:\n"
            f"1. Output ONLY the command, no explanations, markdown, or extra text.\n"
            f"2. If multiple commands are needed, combine using '&&', ';', or '|'.\n"
            f"3. Use appropriate, safe, and efficient flags.\n"
            f"4. Use relative paths unless absolute paths are explicitly needed.\n"
            f"5. Use available tools only.\n"
        )

        if mode == "advanced":
            base_prompt += (
                f"6. Handle conditions (e.g., if disk > 80%), iterations (e.g., for each file), and filters (e.g., files > 1GB).\n"
                f"7. Ensure commands are safe, preferring --dry-run where applicable.\n"
            )

        if category and category in self.command_categories:
            available = [t for t in self.command_categories[category] if t in self.system_context.available_tools]
            base_prompt += f"\nPREFERRED TOOLS for {category}: {', '.join(available)}\n"

        return base_prompt

    def generate_user_prompt(self, query: str) -> str:
        return (
            f"Convert the following natural language query into a valid Linux shell command:\n"
            f"Query: \"{query}\"\n\n"
            f"Command:"
        )

    def generate_contextual_prompt(
        self,
        query: str,
        previous_commands: Optional[List[str]] = None,
        mode: str = "default",
        context: Optional[Union[SystemContext, Dict]] = None
    ) -> Tuple[str, str]:
        # If external context provided, override
        if context:
            if isinstance(context, SystemContext):
                self.system_context = context
            elif isinstance(context, dict):
                # Build SystemContext safely from partial dict
                self.system_context = SystemContext(
                    os_name=context.get("os_name", self.system_context.os_name),
                    distribution=context.get("distribution", self.system_context.distribution),
                    shell=context.get("shell", self.system_context.shell),
                    available_tools=context.get("available_tools", self.system_context.available_tools),
                    current_dir=context.get("current_dir", self.system_context.current_dir),
                    user=context.get("user", self.system_context.user),
                    permissions=context.get("permissions", self.system_context.permissions)
                )
            else:
                raise ValueError("Context must be a SystemContext or a Dict with valid keys.")

        category = self.detect_query_category(query)
        system_prompt = self.generate_system_prompt(category, mode=mode)
        user_prompt = self.generate_user_prompt(query)
        return system_prompt, user_prompt

    def detect_query_category(self, query: str) -> str:
        query_lower = query.lower()
        category_keywords = {
            "file_operations": ["file", "folder", "disk", "directory", "size", "list", "find"],
            "process_management": ["process", "cpu", "kill", "memory"],
            "network": ["ping", "download", "upload", "port", "curl"],
            "system_info": ["system", "info", "version", "uptime"],
            "text_processing": ["grep", "find", "replace", "search"],
            "archive": ["compress", "zip", "tar"],
            "permissions": ["chmod", "chown", "permissions"]
        }
        for category, keywords in category_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return category
        return "general"
