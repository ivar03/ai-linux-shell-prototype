#!/usr/bin/env python3
"""
AI Shell CLI - Comprehensive System Evaluation (Orchestrator)
============================================================
Orchestrates all module-specific test suites.
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Import module test suites
try:
    from test_rollback import evaluate_rollback_system
    from test_compliance import evaluate_compliance_system
    from test_context_awareness import evaluate_context_awareness
    from test_logging import evaluate_logging_system
    from test_safety import evaluate_safety_system
except ImportError as e:
    console.print(f"[red]Error importing test modules: {e}[/red]")
    console.print("[yellow]Make sure all test files are in the same directory[/yellow]")
    sys.exit(1)


def main():
    """Main orchestrator for all tests"""
    console.print("\n[bold green]" + "="*80 + "[/bold green]")
    console.print("[bold green]" + " "*20 + "AI SHELL CLI - COMPREHENSIVE SYSTEM EVALUATION" + " "*14 + "[/bold green]")
    console.print("[bold green]" + "="*80 + "[/bold green]\n")
    
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "modules": {}
    }
    
    # Run Rollback Tests
    console.print("\n[bold cyan]>>> MODULE 1/5: Rollback System[/bold cyan]")
    try:
        rollback_results = evaluate_rollback_system()
        all_results["modules"]["rollback"] = rollback_results
    except Exception as e:
        console.print(f"[red]Rollback tests failed: {e}[/red]")
        all_results["modules"]["rollback"] = {"error": str(e)}
    
    # Run Compliance Tests
    console.print("\n[bold cyan]>>> MODULE 2/5: Compliance Checking[/bold cyan]")
    try:
        compliance_results = evaluate_compliance_system()
        all_results["modules"]["compliance"] = compliance_results
    except Exception as e:
        console.print(f"[red]Compliance tests failed: {e}[/red]")
        all_results["modules"]["compliance"] = {"error": str(e)}
    
    # Run Context Awareness Tests
    console.print("\n[bold cyan]>>> MODULE 3/5: Context Awareness[/bold cyan]")
    try:
        context_results = evaluate_context_awareness()
        all_results["modules"]["context_awareness"] = context_results
    except Exception as e:
        console.print(f"[red]Context awareness tests failed: {e}[/red]")
        all_results["modules"]["context_awareness"] = {"error": str(e)}
    
    # Run Logging Tests
    console.print("\n[bold cyan]>>> MODULE 4/5: Logging System[/bold cyan]")
    try:
        logging_results = evaluate_logging_system()
        all_results["modules"]["logging"] = logging_results
    except Exception as e:
        console.print(f"[red]Logging tests failed: {e}[/red]")
        all_results["modules"]["logging"] = {"error": str(e)}
    
    # Run Safety Tests
    console.print("\n[bold cyan]>>> MODULE 5/5: Safety Validation[/bold cyan]")
    try:
        safety_results = evaluate_safety_system()
        all_results["modules"]["safety"] = safety_results
    except Exception as e:
        console.print(f"[red]Safety tests failed: {e}[/red]")
        all_results["modules"]["safety"] = {"error": str(e)}
    
    # Generate comprehensive summary
    console.print("\n[bold green]" + "="*80 + "[/bold green]")
    console.print("[bold green]" + " "*30 + "FINAL EVALUATION SUMMARY" + " "*26 + "[/bold green]")
    console.print("[bold green]" + "="*80 + "[/bold green]\n")
    
    # Calculate overall metrics
    total_tests = sum(m.get("total_tests", 0) for m in all_results["modules"].values())
    total_passed = sum(m.get("tests_passed", 0) for m in all_results["modules"].values())
    total_failed = total_tests - total_passed
    overall_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    # Create summary table
    summary_table = Table(title="Module-wise Results")
    summary_table.add_column("Module", style="cyan", width=25)
    summary_table.add_column("Tests", style="white", width=10)
    summary_table.add_column("Passed", style="green", width=10)
    summary_table.add_column("Failed", style="red", width=10)
    summary_table.add_column("Success Rate", style="yellow", width=15)
    summary_table.add_column("Status", style="white", width=10)
    
    for module_name, results in all_results["modules"].items():
        if "error" in results:
            summary_table.add_row(
                module_name.replace("_", " ").title(),
                "-", "-", "-", "-", "[red]ERROR[/red]"
            )
        else:
            passed = results['tests_passed']
            failed = results['tests_failed']
            total = results['total_tests']
            rate = results['success_rate']
            
            status = "✓" if rate >= 90 else "⚠" if rate >= 70 else "✗"
            color = "green" if rate >= 90 else "yellow" if rate >= 70 else "red"
            
            summary_table.add_row(
                module_name.replace("_", " ").title(),
                str(total),
                str(passed),
                str(failed),
                f"{rate:.1f}%",
                f"[{color}]{status}[/{color}]"
            )
    
    console.print(summary_table)
    
    # Overall summary panel
    summary_text = f"""[bold]Total Tests Run:[/bold] {total_tests}
[bold]Tests Passed:[/bold] [green]{total_passed}[/green]
[bold]Tests Failed:[/bold] [red]{total_failed}[/red]
[bold]Overall Success Rate:[/bold] [{'green' if overall_rate >= 90 else 'yellow' if overall_rate >= 70 else 'red'}]{overall_rate:.1f}%[/]

[bold]Timestamp:[/bold] {all_results['timestamp']}

[bold]Report Status:[/bold] {'[green]EXCELLENT[/green]' if overall_rate >= 95 else '[green]GOOD[/green]' if overall_rate >= 90 else '[yellow]ACCEPTABLE[/yellow]' if overall_rate >= 70 else '[red]NEEDS IMPROVEMENT[/red]'}"""
    
    console.print("\n")
    console.print(Panel(summary_text, title="📊 Overall Evaluation Summary", border_style="green" if overall_rate >= 90 else "yellow"))
    
    # Detailed recommendations
    if overall_rate < 90:
        console.print("\n[bold yellow]═══ RECOMMENDATIONS ═══[/bold yellow]\n")
        
        for module_name, results in all_results["modules"].items():
            if "error" not in results and results['success_rate'] < 90:
                console.print(f"[yellow]• {module_name.replace('_', ' ').title()}: "
                            f"{results['success_rate']:.1f}% - Review failed test cases[/yellow]")
    
    # Save comprehensive report
    with open("comprehensive_evaluation.json", 'w') as f:
        json.dump(all_results, f, indent=2)
    
    console.print("\n[green]✓ Comprehensive report saved to comprehensive_evaluation.json[/green]")
    
    # Generate issues summary
    issues = []
    if overall_rate < 90:
        issues.append(f"Overall success rate below 90% (current: {overall_rate:.1f}%)")
    
    for module_name, results in all_results["modules"].items():
        if "error" in results:
            issues.append(f"{module_name} module encountered errors")
        elif results.get('success_rate', 0) < 90:
            issues.append(f"{module_name} success rate: {results['success_rate']:.1f}%")
    
    if issues:
        console.print(f"\n[yellow]⚠ Found {len(issues)} issues requiring attention[/yellow]")
        return 1
    else:
        console.print("\n[green]✓ All modules passed with excellent results![/green]")
        return 0


if __name__ == "__main__":
    sys.exit(main())