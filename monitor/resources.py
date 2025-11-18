import psutil
import shutil
import os
import socket
from typing import Dict, Any, List
from datetime import datetime

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
    status = {
        "ok": cpu_percent < threshold,
        "cpu_percent": cpu_percent,
        "message": f"CPU usage: {cpu_percent:.2f}%"
    }
    if cpu_percent >= threshold:
        status["warning"] = f"High CPU usage: {cpu_percent:.2f}%."
    return status

def check_memory_usage(threshold: float = 85.0) -> Dict[str, Any]:
    """Check memory usage and return status if above threshold (%)"""
    mem = psutil.virtual_memory()
    used_percent = mem.percent
    status = {
        "ok": used_percent < threshold,
        "used_percent": used_percent,
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2),
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

def detect_project_context() -> Dict[str, Any]:
    """Detect if inside a Git repo, Docker project, Node.js project"""
    cwd = os.getcwd()
    context = {
        "git_repo": os.path.isdir(os.path.join(cwd, ".git")),
        "docker_project": os.path.isfile(os.path.join(cwd, "docker-compose.yml")),
        "node_project": os.path.isfile(os.path.join(cwd, "package.json")),
    }
    detected = []
    if context["git_repo"]:
        detected.append("Git repository")
    if context["docker_project"]:
        detected.append("Docker project")
    if context["node_project"]:
        detected.append("Node.js project")
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

def get_disk_io_stats() -> Dict:
    """Get disk I/O statistics"""
    try:
        io = psutil.disk_io_counters()
        return {
            'read_bytes': io.read_bytes,
            'write_bytes': io.write_bytes,
            'read_count': io.read_count,
            'write_count': io.write_count
        }
    except:
        return {}

def get_network_io_stats() -> Dict:
    """Get network I/O statistics"""
    try:
        io = psutil.net_io_counters()
        return {
            'bytes_sent': io.bytes_sent,
            'bytes_recv': io.bytes_recv,
            'packets_sent': io.packets_sent,
            'packets_recv': io.packets_recv
        }
    except:
        return {}

def get_boot_time() -> str:
    """Get system boot time"""
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        return boot_time.isoformat()
    except:
        return ""

def get_load_average() -> List[float]:
    """Get system load average"""
    try:
        return list(psutil.getloadavg())
    except:
        return [0.0, 0.0, 0.0]

def get_user_sessions() -> List[Dict]:
    """Get active user sessions"""
    try:
        users = psutil.users()
        return [{'name': u.name, 'terminal': u.terminal, 'host': u.host, 'started': u.started} for u in users]
    except:
        return []

def check_cpu_usage(threshold=80):
    """Enhanced CPU usage check"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        return {
            'percent': cpu_percent,
            'warning': cpu_percent > threshold,
            'core_count': cpu_count
        }
    except:
        return {'percent': 0, 'warning': False, 'core_count': 0}

def check_memory_usage(threshold=80):
    """Enhanced memory usage check"""
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            'percent': mem.percent,
            'warning': mem.percent > threshold,
            'swap_percent': swap.percent,
            'swap_used': swap.used,
            'swap_total': swap.total
        }
    except:
        return {'percent': 0, 'warning': False}

def check_running_process_summary(user_filter=None, name_filter=None):
    """Enhanced process summary with filters"""
    try:
        processes = []
        for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent', 'username']):
            try:
                pinfo = proc.info
                if user_filter and pinfo['username'] != user_filter:
                    continue
                if name_filter and name_filter not in pinfo['name']:
                    continue
                processes.append(pinfo)
            except:
                pass
        
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        return processes[:10]
    except:
        return []

def check_network_connections(protocol=None, state=None):
    """Enhanced network connections with filters"""
    try:
        connections = psutil.net_connections()
        filtered = []
        for conn in connections:
            if protocol and conn.type.name != protocol:
                continue
            if state and conn.status != state:
                continue
            filtered.append({
                'type': conn.type.name if hasattr(conn.type, 'name') else str(conn.type),
                'status': conn.status,
                'laddr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                'raddr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None
            })
        return filtered[:10]
    except:
        return []
