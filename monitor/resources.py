import psutil
import shutil
import os
from typing import Dict, Any, List

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
