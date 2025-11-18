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