import platform
import os
import shutil
from typing import Dict, List, Optional, Tuple
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
    #context aware promptsss
    def __init__(self):
        self.system_context = self._gather_system_context()
        self.command_categories = self._load_command_categories()
    
    def _gather_system_context(self) -> SystemContext:
         try:
            #detect OS and distribution
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
            
            #get shell
            shell = os.environ.get('SHELL', '/bin/bash').split('/')[-1]
            
            #check available tools
            common_tools = ['find', 'grep', 'awk', 'sed', 'sort', 'uniq', 'cut', 'tar', 'gzip', 'curl', 'wget']
            available_tools = [tool for tool in common_tools if shutil.which(tool)]
            
            #get current directory and user
            current_dir = str(Path.cwd())
            user = os.environ.get('USER', 'unknown')
            
            #permissions (simplified)
            permissions = "user"
            if os.getuid() == 0:
                permissions = "root"
            
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
        #for speciallized prompts
        return {
            "file_operations": [
                "find", "locate", "ls", "du", "df", "stat", "file", "tree"
            ],
            "process_management": [
                "ps", "top", "htop", "kill", "killall", "pkill", "pgrep", "jobs"
            ],
            "network": [
                "ping", "curl", "wget", "netstat", "ss", "lsof", "nmap", "dig"
            ],
            "system_info": [
                "uname", "uptime", "free", "vmstat", "iostat", "lscpu", "lsblk"
            ],
            "text_processing": [
                "grep", "sed", "awk", "sort", "uniq", "cut", "tr", "wc", "head", "tail"
            ],
            "archive": [
                "tar", "gzip", "gunzip", "zip", "unzip", "7z"
            ],
            "permissions": [
                "chmod", "chown", "chgrp", "ls", "stat", "getfacl", "setfacl"
            ]
        }
    
    def generate_system_prompt(self, category: Optional[str] = None) -> str:
        base_prompt = f"""You are a Linux command generator for {self.system_context.distribution} running {self.system_context.shell}.

                            SYSTEM CONTEXT:
                            - OS: {self.system_context.os_name} ({self.system_context.distribution})
                            - Shell: {self.system_context.shell}
                            - User: {self.system_context.user} ({self.system_context.permissions} permissions)
                            - Current directory: {self.system_context.current_dir}
                            - Available tools: {', '.join(self.system_context.available_tools[:10])}

                            RULES:
                            1. Output ONLY the command, no explanations or markdown
                            2. Use tools available on this system
                            3. Consider current directory context
                            4. Respect user permissions (avoid sudo unless requested)
                            5. Use appropriate flags for human-readable output
                            6. Prefer safe, commonly used commands
                            7. If multiple commands needed, use && or ; or |
                            8. Use proper quoting and escaping"""
        
        if category and category in self.command_categories:
            tools = self.command_categories[category]
            available_tools = [t for t in tools if t in self.system_context.available_tools]
            
            category_prompt = f"""
                                9. PREFERRED TOOLS for {category}: {', '.join(available_tools)}
                                10. Focus on {category.replace('_', ' ')} operations"""
            
            base_prompt += category_prompt
        
        return base_prompt
    
    def generate_user_prompt(self, query: str, context: Optional[Dict] = None) -> str:
        prompt = f'Convert this natural language query to a Linux command:\n\nQuery: "{query}"'
        
        if context:
            context_parts = []
            
            if context.get('files'):
                context_parts.append(f"Files in current directory: {', '.join(context['files'][:5])}")
            
            if context.get('previous_command'):
                context_parts.append(f"Previous command: {context['previous_command']}")
            
            if context.get('working_dir'):
                context_parts.append(f"Working directory: {context['working_dir']}")
            
            if context.get('target_files'):
                context_parts.append(f"Target files: {', '.join(context['target_files'])}")
            
            if context_parts:
                prompt += f"\n\nCONTEXT:\n- " + "\n- ".join(context_parts)
        
        prompt += "\n\nCommand:"
        return prompt
    
    def detect_query_category(self, query: str) -> str:
        #for speciallized prompts/query finding the category of query
        query_lower = query.lower()
        
        category_keywords = {
            "file_operations": [
                "file", "files", "directory", "folder", "find", "search", "list", "size", "large", "small",
                "extension", "modified", "created", "disk", "space", "tree", "locate"
            ],
            "process_management": [
                "process", "processes", "kill", "stop", "running", "cpu", "memory", "ram", "pid",
                "service", "daemon", "background", "foreground", "job", "jobs"
            ],
            "network": [
                "network", "ping", "download", "upload", "curl", "wget", "http", "https", "ftp",
                "port", "connection", "socket", "dns", "ip", "address"
            ],
            "system_info": [
                "system", "info", "information", "hardware", "cpu", "memory", "disk", "uptime",
                "version", "kernel", "distribution", "stats", "usage"
            ],
            "text_processing": [
                "text", "content", "grep", "search", "replace", "pattern", "word", "line", "lines",
                "count", "sort", "unique", "filter", "extract", "parse"
            ],
            "archive": [
                "archive", "compress", "decompress", "zip", "unzip", "tar", "extract", "backup",
                "compress", "gzip", "gunzip"
            ],
            "permissions": [
                "permission", "permissions", "chmod", "chown", "owner", "group", "access", "rights",
                "readable", "writable", "executable"
            ]
        }
        
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return "general"
    
    def generate_example_prompt(self, category: str) -> str:
        examples = {
            "file_operations": [
                ('Show files larger than 1GB', 'find . -type f -size +1G -exec ls -lh {} \\;'),
                ('List Python files modified today', 'find . -name "*.py" -type f -newermt "today" -ls'),
                ('Show disk usage by folder', 'du -sh */ | sort -hr')
            ],
            "process_management": [
                ('Kill all Python processes', 'pkill python'),
                ('Show processes using most CPU', 'ps aux --sort=-%cpu | head -10'),
                ('Find process by name', 'pgrep -f "process_name"')
            ],
            "network": [
                ('Download file from URL', 'curl -O "https://example.com/file.txt"'),
                ('Check if port 80 is open', 'nc -zv localhost 80'),
                ('Show network connections', 'netstat -tuln')
            ],
            "text_processing": [
                ('Count lines in file', 'wc -l filename.txt'),
                ('Find unique words', 'tr " " "\\n" < file.txt | sort | uniq'),
                ('Replace text in file', 'sed -i "s/old/new/g" file.txt')
            ]
        }
        
        if category not in examples:
            return ""
        
        example_text = f"\n\nEXAMPLES for {category.replace('_', ' ')}:\n"
        for query, command in examples[category]:
            example_text += f'Query: "{query}" → Command: {command}\n'
        
        return example_text
    
    def generate_contextual_prompt(self, query: str, previous_commands: List[str] = None) -> Tuple[str, str]:
        category = self.detect_query_category(query)
        
        system_prompt = self.generate_system_prompt(category)
        
        #add examples if it's a specific category for better and accurate response
        if category != "general":
            system_prompt += self.generate_example_prompt(category)
        
        context = {}
        
        if previous_commands:
            context['previous_command'] = previous_commands[-1]
        
        try:
            current_files = [f.name for f in Path('.').iterdir() if f.is_file()][:5]
            if current_files:
                context['files'] = current_files
        except:
            pass
        
        context['working_dir'] = self.system_context.current_dir
        
        user_prompt = self.generate_user_prompt(query, context)
        
        return system_prompt, user_prompt
    
    def generate_safety_aware_prompt(self, query: str, risk_level: str = "medium") -> str:
        safety_rules = {
            "low": "Prefer safe commands with minimal system impact.",
            "medium": "Include safety checks and confirmations for potentially destructive operations.",
            "high": "Avoid destructive commands. If unavoidable, include --dry-run or similar safety flags."
        }
        
        safety_prompt = f"""
                            SAFETY LEVEL: {risk_level.upper()}
                            SAFETY RULE: {safety_rules.get(risk_level, safety_rules['medium'])}

                            Additional safety considerations:
                            - Always use relative paths unless absolute paths are explicitly requested
                            - Include appropriate flags to make commands reversible where possible
                            - For file operations, consider suggesting backup creation first
                            - For system changes, prefer user-level over system-level modifications"""
        
        return safety_prompt
    
    def get_command_suggestions(self, partial_query: str) -> List[str]:
        suggestions = []
        query_lower = partial_query.lower()
        
        patterns = {
            "find": ["find files by name", "find files by size", "find files by date"],
            "kill": ["kill process by name", "kill all processes", "kill process by PID"],
            "show": ["show disk usage", "show running processes", "show system info"],
            "list": ["list files", "list directories", "list processes"],
            "search": ["search in files", "search for files", "search text pattern"],
            "copy": ["copy files", "copy directory", "copy with permissions"],
            "move": ["move files", "move directory", "rename files"],
            "compress": ["compress files", "create archive", "backup directory"],
            "download": ["download file", "download from URL", "sync files"]
        }
        
        for pattern, suggestions_list in patterns.items():
            if pattern in query_lower:
                suggestions.extend(suggestions_list)
        
        return suggestions[:5] 