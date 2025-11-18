import psutil
import shutil
import os
import socket
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

def check_disk_usage(threshold: float = 10.0) -> Dict[str, Any]:
    """Check disk usage and return status if below threshold (%)"""
    usage = shutil.disk_usage("/")
    percent_free = (usage.free / usage.total) * 100
    status = {
        "ok": percent_free > threshold,
        "percent_free": percent_free,
        "total_gb": round(usage.total / (1024 ** 3), 2),
        "free_gb": round(usage.free / (1024 ** 3), 2),
        "message": f"Disk free: {percent_free:.2f}%"
    }
    if percent_free <= threshold:
        status["warning"] = f"Low disk space: only {percent_free:.2f}% free."
    return status

def check_cpu_usage(threshold: float = 85.0) -> Dict[str, Any]:
    """Check CPU usage and return status if above threshold (%)"""
    cpu_percent = psutil.cpu_percent(interval=1)
    core_count = psutil.cpu_count()
    status = {
        "ok": cpu_percent < threshold,
        "cpu_percent": cpu_percent,
        "core_count": core_count,
        "message": f"CPU usage: {cpu_percent:.2f}%"
    }
    if cpu_percent >= threshold:
        status["warning"] = f"High CPU usage: {cpu_percent:.2f}%."
    return status

def check_memory_usage(threshold: float = 85.0) -> Dict[str, Any]:
    """Check memory usage and return status if above threshold (%)"""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    used_percent = mem.percent
    status = {
        "ok": used_percent < threshold,
        "used_percent": used_percent,
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2),
        "swap_used_percent": swap.percent,
        "swap_total_gb": round(swap.total / (1024 ** 3), 2),
        "message": f"Memory usage: {used_percent:.2f}%"
    }
    if used_percent >= threshold:
        status["warning"] = f"High memory usage: {used_percent:.2f}%."
    return status

def check_zombie_processes() -> Dict[str, Any]:
    """Check for zombie processes"""
    zombies = []
    for proc in psutil.process_iter(attrs=['pid', 'name', 'status']):
        try:
            if proc.info['status'] == psutil.STATUS_ZOMBIE:
                zombies.append({"pid": proc.info['pid'], "name": proc.info['name']})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    status = {
        "ok": len(zombies) == 0,
        "zombie_count": len(zombies),
        "message": f"Zombie processes: {len(zombies)}"
    }
    if zombies:
        status["warning"] = f"Detected {len(zombies)} zombie processes."
        status["zombies"] = zombies
    return status

def check_running_process_summary(limit: int = 5) -> Dict[str, Any]:
    """Return a summary of top running processes by CPU usage"""
    procs = []
    for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent']):
        try:
            procs.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs = sorted(procs, key=lambda x: x['cpu_percent'], reverse=True)[:limit]
    return {
        "ok": True,
        "top_processes": procs,
        "message": f"Top {limit} processes by CPU usage collected."
    }

def check_network_connections(limit: int = 5) -> Dict[str, Any]:
    """Check for active network connections"""
    try:
        connections = psutil.net_connections(kind='inet')
        conns_summary = []
        for conn in connections[:limit]:
            conns_summary.append({
                "fd": conn.fd,
                "family": str(conn.family),
                "type": str(conn.type),
                "laddr": conn.laddr.ip if conn.laddr else None,
                "raddr": conn.raddr.ip if conn.raddr else None,
                "status": conn.status
            })
        return {
            "ok": True,
            "connections_summary": conns_summary,
            "message": f"Collected {min(limit, len(connections))} active network connections."
        }
    except Exception as e:
        return {
            "ok": False,
            "message": f"Failed to collect network connections: {e}"
        }

def get_disk_io_stats() -> Dict[str, Any]:
    """Get disk I/O statistics"""
    try:
        io_counters = psutil.disk_io_counters()
        return {
            "read_bytes": io_counters.read_bytes,
            "write_bytes": io_counters.write_bytes,
            "read_count": io_counters.read_count,
            "write_count": io_counters.write_count
        }
    except Exception:
        return {}

def get_network_io_stats() -> Dict[str, Any]:
    """Get network I/O statistics"""
    try:
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
    except Exception:
        return {}

def get_boot_time() -> float:
    """Get system boot time"""
    try:
        return psutil.boot_time()
    except Exception:
        return 0.0

def get_load_average() -> tuple:
    """Get system load average"""
    try:
        return os.getloadavg() if hasattr(os, 'getloadavg') else (0.0, 0.0, 0.0)
    except Exception:
        return (0.0, 0.0, 0.0)

def get_temperature_info() -> Dict[str, Any]:
    """Get temperature information if available"""
    try:
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            return {"available": len(temps) > 0, "data": dict(temps) if temps else {}}
    except Exception:
        pass
    return {"available": False, "data": {}}

def get_battery_status() -> Dict[str, Any]:
    """Get battery status if available"""
    try:
        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "available": True,
                    "percent": battery.percent,
                    "plugged": battery.power_plugged,
                    "time_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
                }
    except Exception:
        pass
    return {"available": False}

def get_user_sessions() -> List[Dict[str, Any]]:
    """Get active user sessions"""
    try:
        users = psutil.users()
        return [{"name": u.name, "terminal": u.terminal, "host": u.host, "started": u.started} for u in users]
    except Exception:
        return []

def detect_project_context() -> Dict[str, Any]:
    """Detect project type and characteristics"""
    cwd = os.getcwd()
    context = {
        "git_repo": os.path.isdir(os.path.join(cwd, ".git")),
        "docker_project": os.path.isfile(os.path.join(cwd, "docker-compose.yml")),
        "node_project": os.path.isfile(os.path.join(cwd, "package.json")),
        "python_project": any([
            os.path.isfile(os.path.join(cwd, "requirements.txt")),
            os.path.isfile(os.path.join(cwd, "setup.py")),
            os.path.isfile(os.path.join(cwd, "pyproject.toml"))
        ]),
        "java_project": any([
            os.path.isfile(os.path.join(cwd, "pom.xml")),
            os.path.isfile(os.path.join(cwd, "build.gradle"))
        ]),
        "rust_project": os.path.isfile(os.path.join(cwd, "Cargo.toml")),
        "go_project": os.path.isfile(os.path.join(cwd, "go.mod")),
        "ruby_project": os.path.isfile(os.path.join(cwd, "Gemfile")),
        "has_venv": any([
            os.path.isdir(os.path.join(cwd, "venv")),
            os.path.isdir(os.path.join(cwd, ".venv")),
            os.environ.get("VIRTUAL_ENV") is not None
        ]),
        "has_dockerfile": os.path.isfile(os.path.join(cwd, "Dockerfile")),
        "has_kubernetes": os.path.isdir(os.path.join(cwd, "k8s")),
        "has_makefile": os.path.isfile(os.path.join(cwd, "Makefile")),
        "has_cicd": any([
            os.path.isdir(os.path.join(cwd, ".github/workflows")),
            os.path.isfile(os.path.join(cwd, ".gitlab-ci.yml")),
            os.path.isfile(os.path.join(cwd, ".travis.yml"))
        ]),
        "has_readme": any([
            os.path.isfile(os.path.join(cwd, "README.md")),
            os.path.isfile(os.path.join(cwd, "README.rst")),
            os.path.isfile(os.path.join(cwd, "README"))
        ]),
        "has_license": any([
            os.path.isfile(os.path.join(cwd, "LICENSE")),
            os.path.isfile(os.path.join(cwd, "LICENSE.txt")),
            os.path.isfile(os.path.join(cwd, "LICENSE.md"))
        ]),
        "has_gitignore": os.path.isfile(os.path.join(cwd, ".gitignore"))
    }

    detected = []
    if context["git_repo"]:
        detected.append("Git repository")
    if context["docker_project"]:
        detected.append("Docker project")
    if context["node_project"]:
        detected.append("Node.js project")
    if context["python_project"]:
        detected.append("Python project")
    if context["java_project"]:
        detected.append("Java project")
    if context["rust_project"]:
        detected.append("Rust project")
    if context["go_project"]:
        detected.append("Go project")
    if context["ruby_project"]:
        detected.append("Ruby project")

    return {
        "ok": any(context.values()),
        "context": context,
        "message": f"Detected: {', '.join(detected) if detected else 'No project context'}"
    }

def detect_environment() -> Dict[str, Any]:
    """Detect if running in dev vs prod environment"""
    env = os.environ.get("ENV", "development").lower()
    hostname = socket.gethostname()
    detected_env = "production" if env == "production" else "development"
    return {
        "ok": True,
        "environment": detected_env,
        "hostname": hostname,
        "message": f"Environment detected: {detected_env}, Host: {hostname}"
    }

def collect_full_context() -> Dict[str, Any]:
    """Collect all system and project context"""
    context = {
        "timestamp": datetime.now().isoformat(),
        "disk_status": check_disk_usage(),
        "cpu_status": check_cpu_usage(),
        "memory_status": check_memory_usage(),
        "zombie_status": check_zombie_processes(),
        "processes": check_running_process_summary(),
        "network": check_network_connections(),
        "project": detect_project_context(),
        "environment": detect_environment()
    }
    return context

def filter_context(context: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """Filter context to specific keys"""
    return {k: v for k, v in context.items() if k in keys}

def merge_contexts(contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple context dictionaries"""
    merged = {}
    for ctx in contexts:
        merged.update(ctx)
    return merged

def diff_contexts(ctx1: Dict[str, Any], ctx2: Dict[str, Any]) -> Dict[str, Any]:
    """Find differences between two contexts"""
    diff = {}
    all_keys = set(ctx1.keys()) | set(ctx2.keys())
    for key in all_keys:
        if key not in ctx1:
            diff[key] = {"added": ctx2[key]}
        elif key not in ctx2:
            diff[key] = {"removed": ctx1[key]}
        elif ctx1[key] != ctx2[key]:
            diff[key] = {"old": ctx1[key], "new": ctx2[key]}
    return diff

def get_context_summary() -> str:
    """Get a formatted summary of current context"""
    ctx = collect_full_context()
    lines = []

    if "disk_status" in ctx:
        disk = ctx["disk_status"]
        lines.append(f"Disk: {disk.get('percent_free', 0):.1f}% free")

    if "cpu_status" in ctx:
        cpu = ctx["cpu_status"]
        lines.append(f"CPU: {cpu.get('cpu_percent', 0):.1f}%")

    if "memory_status" in ctx:
        mem = ctx["memory_status"]
        lines.append(f"Memory: {mem.get('used_percent', 0):.1f}%")

    if "project" in ctx and ctx["project"].get("context"):
        proj_types = [k for k, v in ctx["project"]["context"].items() if v]
        if proj_types:
            lines.append(f"Project: {', '.join(proj_types)}")

    return " | ".join(lines)

def get_context_warnings() -> List[str]:
    """Get list of warning messages from context"""
    ctx = collect_full_context()
    warnings = []

    for key, value in ctx.items():
        if isinstance(value, dict) and "warning" in value:
            warnings.append(value["warning"])

    return warnings

def calculate_health_score() -> Dict[str, Any]:
    """Calculate overall system health score (0-100)"""
    ctx = collect_full_context()
    score = 100
    issues = []

    # Disk health
    if "disk_status" in ctx and not ctx["disk_status"].get("ok", True):
        score -= 20
        issues.append("Low disk space")

    # CPU health
    if "cpu_status" in ctx and not ctx["cpu_status"].get("ok", True):
        score -= 15
        issues.append("High CPU usage")

    # Memory health
    if "memory_status" in ctx and not ctx["memory_status"].get("ok", True):
        score -= 15
        issues.append("High memory usage")

    # Zombie processes
    if "zombie_status" in ctx and ctx["zombie_status"].get("zombie_count", 0) > 0:
        score -= 10
        issues.append(f"{ctx['zombie_status']['zombie_count']} zombie processes")

    return {
        "score": max(0, score),
        "rating": "Good" if score >= 80 else "Fair" if score >= 60 else "Poor",
        "issues": issues
    }

def get_recommendations() -> List[str]:
    """Get recommendations based on current system state"""
    ctx = collect_full_context()
    recommendations = []

    if "disk_status" in ctx and ctx["disk_status"].get("percent_free", 100) < 10:
        recommendations.append("Clean up disk space - less than 10% free")

    if "cpu_status" in ctx and ctx["cpu_status"].get("cpu_percent", 0) > 85:
        recommendations.append("Investigate high CPU usage - consider killing resource-intensive processes")

    if "memory_status" in ctx and ctx["memory_status"].get("used_percent", 0) > 85:
        recommendations.append("High memory usage - consider restarting services or clearing cache")

    if "zombie_status" in ctx and ctx["zombie_status"].get("zombie_count", 0) > 5:
        recommendations.append("Multiple zombie processes detected - investigate parent processes")

    return recommendations

def export_context(format: str = "json") -> str:
    """Export context in specified format"""
    ctx = collect_full_context()

    if format == "json":
        return json.dumps(ctx, indent=2)
    elif format == "text":
        lines = []
        for key, value in ctx.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
    else:
        return str(ctx)
