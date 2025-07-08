### main entry point 
### -----------------------------!!

import click
import sys
import json
import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt

# Local imports
from commands.llm_handler import LLMHandler
from executor.safety_checker import SafetyChecker
from executor.command_runner import CommandRunner
from logs import setup_logging, log_session

console = Console()

@click.command()
@click.argument('query', required=True)
@click.option('--model', '-m', default='llama3.2:3b', help='Ollama model to use')
@click.option('--dry-run', '-d', is_flag=True, help='Show command without executing')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--no-confirm', is_flag=True, help='Skip Confirmation')
@click.option('--advanced', '-a', is_flag=True, help='Use advanced prompt engineering')
@click.option('--split-multi', '-s', is_flag=True, help='Enable splitting of multi-command outputs')
@click.version_option(version='0.1.0')
def main(query, model, dry_run, verbose, no_confirm, advanced, split_multi):
    logger = setup_logging(verbose)
    session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        llm_handler = LLMHandler(model=model)
        safety_checker = SafetyChecker()
        command_runner = CommandRunner()

        console.print(Panel(
            f"[bold cyan]Natural Language Query:[/bold cyan]\n{query}",
            title="🤖 AI Shell",
            border_style="cyan"
        ))

        console.print("Generating command...", style="yellow")
        try:
            mode = "advanced" if advanced else "default"
            generated_commands = llm_handler.generate_command(query, mode=mode)
        except Exception as e:
            console.print(f"[red]Error generating command:[/red] {e}")
            logger.error(f"LLM generation failed: {e}")
            sys.exit(1)

        all_commands = []
        if split_multi:
            for cmd_str in generated_commands:
                fragments = safety_checker.split_commands(cmd_str)
                all_commands.extend(fragments)
        else:
            all_commands = generated_commands

        for idx, generated_command in enumerate(all_commands, start=1):
            console.print(Panel(
                f"[bold green]{generated_command}[/bold green]",
                title=f"📝 Generated Command [{idx}/{len(generated_commands)}]",
                border_style="green"
            ))

            while True:
                safety_result = safety_checker.check_command(generated_command)

                if not safety_result.is_safe:
                    blocked_info = f"\n[bold red]Blocked Patterns:[/bold red] {safety_result.blocked_patterns}" if safety_result.blocked_patterns else ""
                    console.print(Panel(
                        f"[bold red]SAFETY WARNING[/bold red]\n"
                        f"Reason: {safety_result.reason}\n"
                        f"Risk Level: {safety_result.risk_level}{blocked_info}",
                        title="Safety Check Failed",
                        border_style="red"
                    ))

                    if safety_result.risk_level in ["critical", "high"]:
                        console.print("[red]Command blocked due to critical/high risk.[/red]")
                        log_session(session_id, query, generated_command, "BLOCKED", safety_result.reason)
                        break
                    else:
                        console.print("[yellow]Warning: Proceed with caution.[/yellow]")

                if dry_run:
                    console.print("[yellow]Dry run mode - command not executed.[/yellow]")
                    log_session(session_id, query, generated_command, "DRY_RUN", safety_result.reason)
                    break

                execute = False  
                
                if no_confirm:
                    execute = True
                else:
                    console.print("\nOptions:")
                    console.print("[bold green]y[/bold green] - Execute")
                    console.print("[bold red]n[/bold red] - Skip")
                    console.print("[bold yellow]e[/bold yellow] - Edit")
                    console.print("[bold blue]i[/bold blue] - Info")

                    choice = Prompt.ask("\n[bold]Proceed?[/bold]", choices=["y", "n", "e", "i"], default="n")

                    if choice == "n":
                        console.print("[red]Command skipped by user.[/red]")
                        log_session(session_id, query, generated_command, "SKIPPED", "User skipped")
                        break

                    elif choice == "e":
                        generated_command = Prompt.ask(
                            "[bold]Edit command[/bold]",
                            default=generated_command
                        )
                        continue

                    elif choice == "i":
                        console.print(Panel(
                            f"Original Query: {query}\n"
                            f"Generated Command: {generated_command}\n"
                            f"Model: {model}\n"
                            f"Safety: {'Safe' if safety_result.is_safe else safety_result.reason}\n"
                            f"Risk Level: {safety_result.risk_level}\n"
                            f"Session ID: {session_id}",
                            title="Command Info",
                            border_style="blue"
                        ))
                        continue

                    elif choice == "y":
                        execute = True

                if execute:
                    console.print("[green]Executing command...[/green]")
                    try:
                        result = command_runner.execute(generated_command)

                        if result.success:
                            console.print(Panel(
                                f"[bold green]Command executed successfully[/bold green]\n"
                                f"Exit code: {result.exit_code}\n"
                                f"Execution time: {result.execution_time:.2f}s",
                                title="Execution Success",
                                border_style="green"
                            ))
                            if result.stdout:
                                console.print(Panel(result.stdout, title="Output", border_style="blue"))
                            if result.stderr and verbose:
                                console.print(Panel(result.stderr, title="Stderr", border_style="yellow"))
                            log_session(session_id, query, generated_command, "SUCCESS", result.stdout[:500])
                        else:
                            console.print(Panel(
                                f"[bold red]Command failed[/bold red]\n"
                                f"Exit code: {result.exit_code}\n"
                                f"Error: {result.stderr}",
                                title="Execution Failed",
                                border_style="red"
                            ))
                            log_session(session_id, query, generated_command, "FAILED", result.stderr)
                        break

                    except Exception as e:
                        console.print(f"[red]Execution error:[/red] {e}")
                        logger.error(f"Execution failed: {e}")
                        log_session(session_id, query, generated_command, "ERROR", str(e))
                        break

    except KeyboardInterrupt:
        console.print("\n[red]Interrupted by user[/red]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

@click.group()
def cli():
    pass

cli.add_command(main, name="run")

@cli.group()
def denylist():
    """Manage the denylist dynamically."""
    pass

@denylist.command()
@click.argument("level", type=click.Choice(["critical", "high", "medium", "low"]))
@click.argument("pattern")
def add(level, pattern):
    """Add a pattern to the denylist."""
    from executor import denylist_utils
    denylist_utils.add.callback(level, pattern)

@denylist.command()
def view():
    """View current denylist."""
    from executor import denylist_utils
    denylist_utils.view.callback()

@denylist.command()
def validate():
    """Validate denylist structure."""
    from executor import denylist_utils
    denylist_utils.validate.callback()

@cli.command()
@click.option('--count', '-c', default=10, help='Show last N logs')
def history(count):
    from logs import show_history
    show_history(count)

@cli.command()
def models():
    try:
        llm = LLMHandler()
        available_models = llm.list_models()
        console.print("[bold]Available Models:[/bold]")
        for m in available_models:
            console.print(f" • {m}")
    except Exception as e:
        console.print(f"[red]Error listing models:[/red] {e}")

if __name__ == "__main__":
    cli()