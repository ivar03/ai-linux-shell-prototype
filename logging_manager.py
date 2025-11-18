import os
import psutil
from datetime import datetime
import json
from typing import Dict, List, Optional, Any
from rich.panel import Panel
from rich.console import Console
from monitor import resources

console = Console()

def collect_full_context() -> dict:
    """Collects full system, project, and environment context."""
    project_context = resources.detect_project_context()
    environment_status = resources.detect_environment()
    running_procs = resources.check_running_process_summary()
    network_conns = resources.check_network_connections()
    disk_status = resources.check_disk_usage()
    cpu_status = resources.check_cpu_usage()
    mem_status = resources.check_memory_usage()
    zombie_status = resources.check_zombie_processes()

    context = {
        "project_context": project_context,
        "environment_status": environment_status,
        "running_procs": running_procs,
        "network_conns": network_conns,
        "disk_status": disk_status,
        "cpu_status": cpu_status,
        "mem_status": mem_status,
        "zombie_status": zombie_status,
    }
    return context

def display_context_summary(context: dict):
    """Nicely formats and displays context summary in the CLI."""
    lines = [
        f"📦 [bold]Project Context:[/bold] {context['project_context']['message']}",
        f"🌎 [bold]Environment:[/bold] {context['environment_status']['message']}",
        f"⚙️ [bold]Processes:[/bold] {context['running_procs']['message']}",
        f"🔗 [bold]Network:[/bold] {context['network_conns']['message']}",
        f"💾 [bold]Disk:[/bold] {context['disk_status']['message']}",
        f"🖥️ [bold]CPU:[/bold] {context['cpu_status']['message']}",
        f"🧠 [bold]Memory:[/bold] {context['mem_status']['message']}",
        f"👻 [bold]Zombies:[/bold] {context['zombie_status']['message']}",
    ]
    panel = Panel("\n".join(lines), title="🧠 Context Awareness", border_style="cyan")
    console.print(panel)

def context_to_json(context: dict) -> str:
    """Converts context dictionary to JSON string for logging."""
    try:
        return json.dumps(context, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to convert context to JSON: {e}"})

def get_context():
    """Collect full system context with timestamp"""
    context = {
        'timestamp': datetime.now().isoformat(),
        'project': detect_project_type(),
        'environment': resources.detect_environment(),
        'hostname': resources.get_hostname(),
        'disk': resources.check_disk_usage(),
        'cpu': resources.check_cpu_usage(),
        'memory': resources.check_memory_usage(),
        'zombies': resources.check_zombie_processes(),
        'processes': resources.check_running_process_summary(),
        'network': resources.check_network_connections()
    }
    return context

def detect_project_type():
    """Enhanced project detection"""
    cwd = os.getcwd()
    project_indicators = {
        'python_project': ['setup.py', 'requirements.txt', 'pyproject.toml', 'Pipfile'],
        'java_project': ['pom.xml', 'build.gradle', 'build.xml'],
        'rust_project': ['Cargo.toml'],
        'go_project': ['go.mod', 'go.sum'],
        'ruby_project': ['Gemfile', 'Rakefile'],
        'node_project': ['package.json', 'node_modules'],
        'docker_project': ['Dockerfile', 'docker-compose.yml'],
        'git_repo': ['.git'],
        'has_dockerfile': ['Dockerfile'],
        'has_makefile': ['Makefile'],
        'has_readme': ['README.md', 'README.rst', 'README.txt', 'README'],
        'has_license': ['LICENSE', 'LICENSE.txt', 'LICENSE.md'],
        'has_gitignore': ['.gitignore'],
        'has_ci_cd': ['.github/workflows', '.gitlab-ci.yml', '.travis.yml', 'Jenkinsfile']
    }
    
    detected = {}
    for key, indicators in project_indicators.items():
        for indicator in indicators:
            path = os.path.join(cwd, indicator)
            if os.path.exists(path):
                detected[key] = True
                break
    
    # Check for virtual environment
    detected['virtual_env'] = 'VIRTUAL_ENV' in os.environ or os.path.exists('venv') or os.path.exists('.venv')
    
    # Check for Kubernetes
    detected['has_kubernetes'] = os.path.exists('k8s') or os.path.exists('kubernetes')
    
    return detected

def filter_context(context: Dict, keys: List[str]) -> Dict:
    """Filter context to specific keys"""
    return {k: context.get(k) for k in keys if k in context}

def merge_contexts(*contexts: Dict) -> Dict:
    """Merge multiple contexts"""
    merged = {}
    for ctx in contexts:
        merged.update(ctx)
    return merged

def diff_contexts(ctx1: Dict, ctx2: Dict) -> Dict:
    """Detect differences between contexts"""
    diff = {}
    all_keys = set(ctx1.keys()) | set(ctx2.keys())
    for key in all_keys:
        if ctx1.get(key) != ctx2.get(key):
            diff[key] = {'old': ctx1.get(key), 'new': ctx2.get(key)}
    return diff

def get_context_summary(context: Dict) -> str:
    """Get formatted context summary"""
    summary = []
    summary.append(f"Timestamp: {context.get('timestamp', 'N/A')}")
    summary.append(f"Environment: {context.get('environment', 'N/A')}")
    summary.append(f"Disk: {context.get('disk', {}).get('percent', 'N/A')}%")
    summary.append(f"CPU: {context.get('cpu', {}).get('percent', 'N/A')}%")
    summary.append(f"Memory: {context.get('memory', {}).get('percent', 'N/A')}%")
    return "\n".join(summary)

def get_context_warnings(context: Dict) -> List[str]:
    """Get warnings from context"""
    warnings = []
    disk = context.get('disk', {})
    if disk.get('percent', 0) > 90:
        warnings.append("Low disk space")
    
    cpu = context.get('cpu', {})
    if cpu.get('percent', 0) > 80:
        warnings.append("High CPU usage")
    
    memory = context.get('memory', {})
    if memory.get('percent', 0) > 80:
        warnings.append("High memory usage")
    
    return warnings

def calculate_health_score(context: Dict) -> float:
    """Calculate system health score (0-100)"""
    score = 100.0
    
    # Deduct for high resource usage
    disk = context.get('disk', {}).get('percent', 0)
    score -= max(0, (disk - 80) * 2)
    
    cpu = context.get('cpu', {}).get('percent', 0)
    score -= max(0, (cpu - 70) * 1.5)
    
    memory = context.get('memory', {}).get('percent', 0)
    score -= max(0, (memory - 70) * 1.5)
    
    return max(0, min(100, score))

def get_recommendations(context: Dict) -> List[str]:
    """Generate recommendations from context"""
    recommendations = []
    warnings = get_context_warnings(context)
    
    for warning in warnings:
        if "disk" in warning.lower():
            recommendations.append("Consider cleaning up old files or expanding storage")
        elif "cpu" in warning.lower():
            recommendations.append("Review running processes and consider optimization")
        elif "memory" in warning.lower():
            recommendations.append("Close unused applications or increase RAM")
    
    return recommendations

def export_context(context: Dict, format: str = 'json', filepath: Optional[str] = None) -> str:
    """Export context in multiple formats"""
    if format == 'json':
        output = json.dumps(context, indent=2)
    elif format == 'yaml':
        import yaml
        output = yaml.dump(context)
    else:
        output = str(context)
    
    if filepath:
        with open(filepath, 'w') as f:
            f.write(output)
    
    return output

class LogManager:
    def __init__(self, backend="json"):
        self.backend = backend
        if backend == "json":
            self.json_log_path = "logs.json"
        else:
            self.db_path = "logs.db"
        self.init_logs()

    def init_logs(self):
        """Initialize logs storage"""
        if self.backend == "json":
            if not os.path.exists(self.json_log_path):
                with open(self.json_log_path, 'w') as f:
                    json.dump([], f)
        else:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TEXT,
                            query TEXT,
                            command TEXT,
                            status TEXT,
                            execution_time REAL
                        )''')
            conn.commit()
            conn.close()

    def log_interaction(self, query: str, command: str, status: str, execution_time: float):
        """Log an interaction"""
        if self.backend == "json":
            with open(self.json_log_path, 'r+') as f:
                data = json.load(f)
                data.append({
                    "timestamp": datetime.now().isoformat(),
                    "query": query,
                    "command": command,
                    "status": status,
                    "execution_time": execution_time
                })
                f.seek(0)
                json.dump(data, f, indent=2)
        else:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''INSERT INTO logs (timestamp, query, command, status, execution_time)
                          VALUES (?, ?, ?, ?, ?)''', 
                          (datetime.now().isoformat(), query, command, status, execution_time))
            conn.commit()
            conn.close()

    def get_history(self) -> List[LogEntry]:
        """Get command history"""
        if self.backend == "json":
            with open(self.json_log_path, 'r') as f:
                data = json.load(f)
                return [LogEntry(**item) for item in data]
        else:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT * FROM logs")
            rows = c.fetchall()
            conn.close()
            return [LogEntry(*row) for row in rows]

    def filter_by_status(self, status: str) -> List[LogEntry]:
        """Filter logs by status"""
        return [entry for entry in self.get_history() if entry.status == status]
    
    def filter_by_date_range(self, start_date: str, end_date: str) -> List[LogEntry]:
        """Filter logs by date range"""
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        return [entry for entry in self.get_history() 
                if start <= datetime.fromisoformat(entry.timestamp) <= end]
    
    def filter_by_model(self, model: str) -> List[LogEntry]:
        """Filter logs by AI model"""
        return [entry for entry in self.get_history() if entry.ai_model == model]
    
    def search_queries(self, search_text: str) -> List[LogEntry]:
        """Search in query text"""
        return [entry for entry in self.get_history() 
                if search_text.lower() in entry.query.lower()]
    
    def search_commands(self, search_text: str) -> List[LogEntry]:
        """Search in command text"""
        return [entry for entry in self.get_history() 
                if search_text.lower() in entry.command.lower()]
    
    def filter_by_execution_time(self, min_time: float, max_time: float) -> List[LogEntry]:
        """Filter logs by execution time"""
        return [entry for entry in self.get_history() 
                if min_time <= entry.execution_time <= max_time]
    
    def export_to_csv(self, filepath: str):
        """Export logs to CSV"""
        import csv
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'query', 'command', 'status', 'execution_time'])
            for entry in self.get_history():
                writer.writerow([entry.timestamp, entry.query, entry.command, 
                               entry.status, entry.execution_time])
    
    def export_to_json(self, filepath: str):
        """Export logs to JSON"""
        with open(filepath, 'w') as f:
            json.dump([entry.__dict__ for entry in self.get_history()], f, indent=2)
    
    def import_from_json(self, filepath: str):
        """Import logs from JSON"""
        with open(filepath, 'r') as f:
            data = json.load(f)
            for item in data:
                self.log_interaction(**item)
    
    def import_from_csv(self, filepath: str):
        """Import logs from CSV"""
        import csv
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.log_interaction(**row)
    
    def backup_logs(self, backup_path: str):
        """Backup logs to specified path"""
        import shutil
        if self.backend == "json":
            shutil.copy2(self.json_log_path, backup_path)
        else:
            shutil.copy2(self.db_path, backup_path)
    
    def merge_logs(self, *log_files: str):
        """Merge multiple log files"""
        for log_file in log_files:
            if log_file.endswith('.json'):
                self.import_from_json(log_file)