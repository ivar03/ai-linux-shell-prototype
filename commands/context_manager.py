import json
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

