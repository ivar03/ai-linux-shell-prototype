from logs import LogManager
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import List

console = Console()

def suggest_frequent_commands(limit: int = 5):
    log_manager = LogManager()
    commands = log_manager.get_frequent_commands(limit=limit)
    if not commands:
        console.print("[yellow]No frequent commands found yet.[/yellow]")
        return

    table = Table(title="💡 Frequently Used Commands")
    table.add_column("No.", style="cyan", width=5)
    table.add_column("Command", style="green")

    for idx, cmd in enumerate(commands, start=1):
        table.add_row(str(idx), cmd)

    console.print(table)

def suggest_safe_automations(limit: int = 5):
    log_manager = LogManager()
    commands = log_manager.get_frequent_commands(limit=limit)
    if not commands:
        console.print("[yellow]No commands available for automation suggestions.[/yellow]")
        return

    read_only_commands = [
        "ls", "cat", "less", "more", "head", "tail", "grep", "find",
        "ps", "top", "df", "du", "free", "uptime", "whoami", "id",
        "pwd", "echo", "date", "cal", "history", "which", "whereis",
        "file", "stat", "wc", "diff", "sort", "uniq", "cut"
    ]

    suggested = []
    for cmd in commands:
        if any(cmd.strip().startswith(ro) for ro in read_only_commands):
            suggested.append(cmd)

    if not suggested:
        console.print("[yellow]No safe automation suggestions at this time.[/yellow]")
        return

    table = Table(title="⚡ Safe Automation Suggestions")
    table.add_column("No.", style="cyan", width=5)
    table.add_column("Command", style="green")

    for idx, cmd in enumerate(suggested, start=1):
        table.add_row(str(idx), cmd)

    console.print(table)

def suggest_all():
    console.print(Panel("[bold blue]Contextual Suggestions[/bold blue]", border_style="blue"))
    suggest_frequent_commands()
    suggest_safe_automations()
