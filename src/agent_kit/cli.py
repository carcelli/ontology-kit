#!/usr/bin/env python3
"""
CLI entrypoint for ontology-kit orchestration.

From first principles: CLI as thin adapter layer that delegates to core domain
logic (factories, orchestrators). Uses Click for declarative command structure.

Commands:
- run: Execute orchestration for a domain
- list-domains: Show available domains
- status: Show circuit breaker status
- validate-config: Check domain configs

References:
- Click docs: https://click.palletsprojects.com/
- CLI design: 12 Factor App (CLI as process)
"""

from __future__ import annotations

import json
import sys
from typing import Any

import click
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from agent_kit.agents.base import AgentTask
from agent_kit.domains.registry import get_global_registry
from agent_kit.factories.agent_factory import AgentFactory
from agent_kit.monitoring.circuit_breaker import _circuit_breakers

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="ontology-kit")
def cli():
    """
    Ontology-Kit: Production-grade distributed agent system.

    Unified orchestration across business, betting, and trading domains
    with ontology-driven routing, policy enforcement, and structured outputs.
    """
    pass


@cli.command()
@click.option(
    "--domain",
    "-d",
    required=True,
    help="Domain to run (business, betting, trading)",
)
@click.option(
    "--goal",
    "-g",
    required=True,
    help="Goal/query to execute (e.g., 'Forecast next 30 days')",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for results (JSON)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output (show specialist results)",
)
def run(domain: str, goal: str, output: str | None, verbose: bool):
    """
    Run orchestration for a domain.

    Example:
        ontology-kit run --domain business --goal "Forecast revenue for next 30 days"
    """
    console.print(f"\n[bold cyan]🚀 Ontology-Kit Orchestration[/bold cyan]")
    console.print(f"[dim]Domain:[/dim] {domain}")
    console.print(f"[dim]Goal:[/dim] {goal}\n")

    try:
        # Create orchestrator
        with console.status("[bold green]Initializing orchestrator..."):
            factory = AgentFactory()
            orchestrator = factory.create_orchestrator(domain)

        # Execute
        with console.status("[bold green]Executing..."):
            task = AgentTask(prompt=goal)
            result = orchestrator.run(task)

        # Display results
        console.print("\n[bold green]✓ Execution complete![/bold green]\n")

        # Parse result (may be dict or string)
        result_data = result.result if hasattr(result, "result") else result

        if isinstance(result_data, dict):
            # Pretty print structured result
            _display_structured_result(result_data, verbose)

            # Save to file if requested
            if output:
                try:
                    with open(output, "w", encoding="utf-8") as f:
                        json.dump(result_data, f, indent=2, default=str)
                    console.print(f"\n[dim]Results saved to {output}[/dim]")
                except (IOError, OSError) as e:
                    console.print(f"\n[bold red]✗ Failed to save results:[/bold red] {e}", style="red")
                    sys.exit(1)
        else:
            # Plain text result
            console.print(f"[bold]Result:[/bold] {result_data}")

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}", style="red")
        if verbose:
            import traceback
            console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@cli.command(name="list-domains")
def list_domains():
    """
    List all available domains and their configurations.

    Example:
        ontology-kit list-domains
    """
    console.print("\n[bold cyan]Available Domains[/bold cyan]\n")

    registry = get_global_registry()
    domains = registry.list_domains()

    if not domains:
        console.print("[yellow]No domains found. Create YAML configs in src/agent_kit/domains/[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Domain", style="cyan")
    table.add_column("Description")
    table.add_column("Agents", style="green")
    table.add_column("Tools", style="blue")

    for domain_id in domains:
        cfg = registry.get(domain_id)
        table.add_row(
            domain_id,
            cfg.description,
            ", ".join(cfg.default_agents),
            f"{len(cfg.allowed_tools)} tools",
        )

    console.print(table)
    console.print()


@cli.command()
@click.option(
    "--domain",
    "-d",
    help="Domain to validate (validates all if not specified)",
)
def validate_config(domain: str | None):
    """
    Validate domain configurations.

    Example:
        ontology-kit validate-config --domain business
    """
    console.print("\n[bold cyan]Validating Domain Configs[/bold cyan]\n")

    registry = get_global_registry()
    domains = [domain] if domain else registry.list_domains()

    all_valid = True

    for domain_id in domains:
        try:
            cfg = registry.get(domain_id)

            # Check required fields (DomainConfig is dict subclass, so .get() works)
            required = ["id", "description", "default_agents", "allowed_tools"]
            missing = [field for field in required if field not in cfg or not cfg.get(field)]

            if missing:
                console.print(f"[red]✗ {domain_id}: Missing fields {missing}[/red]")
                all_valid = False
            else:
                console.print(f"[green]✓ {domain_id}: Valid[/green]")

                # Check agents exist in registry
                from agent_kit.factories.agent_factory import AgentFactory
                factory = AgentFactory()
                for agent_name in cfg.default_agents:
                    if agent_name not in factory.AGENT_REGISTRY:
                        console.print(
                            f"  [yellow]⚠ Agent '{agent_name}' not in registry[/yellow]"
                        )

        except Exception as e:
            console.print(f"[red]✗ {domain_id}: {e}[/red]")
            all_valid = False

    console.print()
    if all_valid:
        console.print("[bold green]All configs valid![/bold green]\n")
    else:
        console.print("[bold red]Some configs have issues.[/bold red]\n")
        sys.exit(1)


@cli.command()
def status():
    """
    Show circuit breaker status for all tools/agents.

    Example:
        ontology-kit status
    """
    console.print("\n[bold cyan]Circuit Breaker Status[/bold cyan]\n")

    if not _circuit_breakers:
        console.print("[yellow]No circuit breakers active.[/yellow]\n")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Agent/Tool", style="cyan")
    table.add_column("State", style="bold")
    table.add_column("Recent Errors", style="red")
    table.add_column("Last Event")

    for name, breaker in _circuit_breakers.items():
        status_data = breaker.get_status()

        state = status_data["state"]
        state_color = "green" if state == "CLOSED" else "red"

        recent_events = status_data.get("recent_events", [])
        last_event = recent_events[-1]["reason"] if recent_events else "N/A"

        table.add_row(
            name,
            f"[{state_color}]{state}[/{state_color}]",
            str(status_data["recent_errors"]),
            last_event,
        )

    console.print(table)
    console.print()


# ============================================================================
# Helper Functions
# ============================================================================


def _display_structured_result(result: dict[str, Any], verbose: bool = False):
    """Display structured result with rich formatting."""

    # Display summary
    if "summary" in result:
        console.print(f"[bold]Summary:[/bold] {result['summary']}\n")

    # Display forecast if present
    if "forecast" in result and isinstance(result["forecast"], dict):
        forecast_data = result["forecast"]
        console.print("[bold]Forecast:[/bold]")
        console.print(f"  Horizon: {forecast_data.get('horizon_days')} days")
        console.print(f"  Model: {forecast_data.get('model_name')}")
        if "cv_metrics" in forecast_data:
            metrics = forecast_data["cv_metrics"]
            console.print(f"  Metrics: {json.dumps(metrics, indent=4)}")
        console.print()

    # Display interventions if present
    if "interventions" in result and result["interventions"]:
        console.print("[bold]Top Interventions:[/bold]")
        for i, intervention in enumerate(result["interventions"][:5], 1):
            if isinstance(intervention, dict):
                console.print(
                    f"  {i}. {intervention.get('action')} "
                    f"(impact: {intervention.get('expected_impact', 0):.1f}%)"
                )
        console.print()

    # Display signals/edges if present
    if "signals" in result and result["signals"]:
        console.print(f"[bold]Signals:[/bold] {len(result['signals'])} generated\n")

    if "edges" in result and result["edges"]:
        console.print(f"[bold]Betting Edges:[/bold] {len(result['edges'])} detected\n")

    # Display risk checks
    if "passed_risk_checks" in result:
        passed = result["passed_risk_checks"]
        if passed:
            console.print("[green]✓ All risk checks passed[/green]\n")
        else:
            console.print("[red]✗ Risk violations:[/red]")
            for violation in result.get("risk_violations", []):
                console.print(f"  - {violation}")
            console.print()

    # Verbose: show specialist results
    if verbose and "specialist_results" in result:
        console.print("[bold]Specialist Results:[/bold]")
        for spec_result in result["specialist_results"]:
            console.print(f"  • {spec_result.get('specialist')}: {spec_result.get('result')}")
        console.print()


if __name__ == "__main__":
    cli()

