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
from rich.prompt import Confirm, Prompt

#local imp
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
@click.option('--no-confirm', is_flag=True, help='Skip Confirmation') #mot recommended
@click.version_option(version='0.1.0')
def main(query, model, dry_run, verbose, no_confirm):
    #logger
    logger = setup_logging(verbose)

    #start session
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
            generated_command =llm_handler.generate_command(query)

        except Exception as e:
            console.print(f"Error generating command: {e}", style="red")
            logger.error(f"LLM generation failed: {e}")
            sys.exit(1)

        #generated comm
        command_panel = Panel(
            f"[bold green]{generated_command}[/bold green]",
            title="📝 Generated Command",
            border_style="green"
        )
            
        console.print(command_panel)

        safety_result = safety_checker.check_command(generated_command)

        if not safety_result.is_safe:
            console.print(Panel(
                f"[bold red] SAFETY WARNING[/bold red]\n"
                f"reason: {safety_result.reason}\n"
                f"risk level: {safety_result.risk_level}",
                title="Safety check FAILED",
                border_style="red"
            ))

            if safety_result.risk_level == "high":
                console.print("Command blocked for safety reasons", style="red")
                log_session(session_id, query, generated_command, "BLOCKED", safety_result.reason)
                sys.exit(1)
        
        if dry_run: 
            console.print("Dry run mode - command not executed", style="yellow")
            log_session(session_id, query, generated_command, "DRY_RUN", "")
            sys.exit(0)

        if not no_confirm:
            console.print("\n")
            #options
            console.print("Options:", style="bold")
            console.print(" [bold green]y[/bold green] - Execute command")
            console.print(" [bold red]n[/bold red] - Cancel")
            console.print(" [bold yellow]e[/bold yellow] - Edit command")
            console.print(" [bold blue]i[/bold blue] - Show more info")

            while True:
                choice = Prompt.ask(
                    "\n[bold]Proceed?[/bold]",
                    choices=["y", "n", "e", "i"],
                    default="n"
                )

                if choice == "n":
                    console.print("Command cancelled by user.", style="red")
                    log_session(session_id, query, generated_command, "CANCELLED", "User cancelled")
                    sys.exit(0)

                elif choice == "e":
                    edited_command = Prompt.ask(
                        "[bold]Edit command[/bold]",
                        default=generated_command
                    )
                    
                    safety_result = safety_checker.check_command(edited_command)
                    if not safety_result.is_safe and safety_result.risk_level == "HIGH":
                        console.print(f"Edited command blocked: {safety_result.reason}", style="red")
                        continue
                    
                    generated_command = edited_command
                    console.print(f"Command updated to: [bold green]{generated_command}[/bold green]")
                    continue

                elif choice == "i":
                    info_panel = Panel(
                        f"[bold]Original Query:[/bold] {query}\n"
                        f"[bold]Generated Command:[/bold] {generated_command}\n"
                        f"[bold]Model Used:[/bold] {model}\n"
                        f"[bold]Safety Status:[/bold] {'Safe' if safety_result.is_safe else safety_result.reason}\n"
                        f"[bold]Session ID:[/bold] {session_id}",
                        title="Command Details",
                        border_style="blue"
                    )
                    console.print(info_panel)
                    continue
                
                elif choice == "y":
                    break

            #start executing
            console.print("Executing command...", style="green")

            try:
                result = command_runner.execute(generated_command)

                #results
                if result.success:
                    console.print(Panel(
                        f"[bold green]Command executed successfully[/bold green]\n"
                        f"Exit code: {result.exit_code}\n"
                        f"Execution time: {result.execution_time:.2f}s",
                        title="Execution Status",
                        border_style="green"
                     ))
                    
                    if result.stdout:
                        console.print("\n[bold]Output:[/bold]")
                        console.print(Panel(result.stdout, border_style="blue"))
                    
                    if result.stderr and verbose:
                        console.print("\n[bold]Stderr:[/bold]")
                        console.print(Panel(result.stderr, border_style="yellow"))

                    #log
                    log_session(session_id, query, generated_command, "SUCCESS", result.stdout[:500])

                else:
                    console.print(Panel(
                        f"[bold red]Command failed[/bold red]\n"
                        f"Exit code: {result.exit_code}\n"
                        f"Error: {result.stderr}",
                        title="Execution Failed",
                        border_style="red"
                    ))
                    
                    #log-failed ones
                    log_session(session_id, query, generated_command, "FAILED", result.stderr)
                    sys.exit(result.exit_code)
            
            except Exception as e:
                console.print(f"Execution error: {e}", style="red")
                logger.error(f"Command execution failed: {e}")
                log_session(session_id, query, generated_command, "ERROR", str(e))
                sys.exit(1)
    
    except KeyboardInterrupt:
        console.print("\nInterrupted by user", style="red")
        sys.exit(130)
    
    except Exception as e:
        console.print(f"Unexpected error: {e}", style="red")
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


@click.group()
def cli():
    pass

@cli.command()
def logs():
    from logs import view_logs
    view_logs()

@cli.command()
@click.option('--count', '-c', default=10, help='Number of entries to show')
def history(count):
    from logs import show_history
    show_history(count)

@cli.command()
def models():
    #list of available models
    try:
        from commands.llm_handler import LLMHandler
        llm = LLMHandler()
        available_models = llm.list_models()
        
        console.print("[bold]Available Ollama Models:[/bold]")
        for model in available_models:
            console.print(f"  • {model}")
    
    except Exception as e:
        console.print(f"Error listing models: {e}", style="red")


if __name__ == "__main__":
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        main()
    else:
        cli()   