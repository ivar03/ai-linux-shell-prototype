import json
import sys
from pathlib import Path
import click
from rich import print
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

def load_denylist(denylist_path):
    if denylist_path.exists():
        with open(denylist_path, "r") as f:
            return json.load(f)
    else:
        return {"critical": [], "high": [], "medium": [], "low": []}

def save_denylist(denylist_path, denylist):
    with open(denylist_path, "w") as f:
        json.dump(denylist, f, indent=4)

@click.group()
def cli():
    pass

@cli.command()
@click.argument("level", type=click.Choice(["critical", "high", "medium", "low"]))
@click.argument("pattern")
def add(level, pattern):
    """Add a pattern to denylist.json at LEVEL."""
    denylist_path = Path(__file__).parent / "denylist.json"
    denylist = load_denylist(denylist_path)

    if pattern in denylist[level]:
        print(f":warning: [yellow]Pattern already exists in {level}[/yellow]")
        sys.exit(0)

    denylist[level].append(pattern)
    save_denylist(denylist_path, denylist)
    print(f":white_check_mark: [green]Added '{pattern}' to {level}[/green]")

@cli.command()
def view():
    """View current denylist.json contents."""
    denylist_path = Path(__file__).parent / "denylist.json"
    denylist = load_denylist(denylist_path)
    print(Panel(str(json.dumps(denylist, indent=4)), title="Current Denylist"))

@cli.command()
def validate():
    """Validate denylist.json structure."""
    denylist_path = Path(__file__).parent / "denylist.json"
    denylist = load_denylist(denylist_path)
    required_levels = ["critical", "high", "medium", "low"]
    
    errors = []
    for level in required_levels:
        if level not in denylist:
            errors.append(f"Missing level: {level}")
        elif not isinstance(denylist[level], list):
            errors.append(f"Level {level} is not a list")

    if errors:
        print(Panel("\n".join(errors), title="[red]Validation Failed[/red]", border_style="red"))
        sys.exit(1)
    else:
        print(Panel(":white_check_mark: [green]Denylist validation passed[/green]", title="Validation Passed", border_style="green"))

if __name__ == "__main__":
    cli()