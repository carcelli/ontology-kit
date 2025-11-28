#!/usr/bin/env python3
"""
Comprehensive CLI for Ontology-Kit: Orchestration, ML Workflows, and Agent Management.

From first principles: CLI as thin adapter layer that delegates to core domain
logic (factories, orchestrators, ontology loaders). Uses Click for declarative
command structure with Rich for beautiful output.

Architecture:
- Orchestration: Domain-driven agent coordination
- Ontology: SPARQL queries, entity exploration, semantic routing
- ML Workflows: Training, leverage analysis, semantic graphs
- Agent Management: Create, list, run individual agents
- Tool Discovery: Ontology-driven tool finding and execution
- Interactive Mode: REPL for complex multi-step workflows

References:
- Click docs: https://click.palletsprojects.com/
- Rich docs: https://rich.readthedocs.io/
- CLI design: 12 Factor App (CLI as process)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import click
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.tree import Tree

from agent_kit.agents.base import AgentTask
from agent_kit.data_collection import AgentDataCollector, MonitoringConfig, PerformanceAnalytics
from agent_kit.domains.registry import get_global_registry
from agent_kit.factories.agent_factory import AgentFactory
from agent_kit.interactive_dashboard import InteractiveDashboard
from agent_kit.monitoring.circuit_breaker import _circuit_breakers
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.ontology_ml_workflow import OntologyMLWorkflowAnalyzer
from agent_kit.orchestrator.ontology_orchestrator import OntologyOrchestrator

console = Console()


class AppContext:
    """Application context for CLI commands."""

    def __init__(self):
        self.factory = AgentFactory()
        self.registry = get_global_registry()
        self.collector = AgentDataCollector()
        self.workflow_analyzer = OntologyMLWorkflowAnalyzer()


@click.group()
@click.version_option(version="0.1.0", prog_name="ontology-kit")
@click.pass_context
def cli(ctx):
    """
    🧠 Ontology-Kit: Production-grade distributed agent system.

    Unified orchestration across domains with ontology-driven routing,
    policy enforcement, and structured outputs. Enables ML workflows
    through semantic understanding and agent coordination.
    """
    ctx.ensure_object(dict)
    ctx.obj['app'] = AppContext()


# ============================================================================
# ORCHESTRATION COMMANDS
# ============================================================================

@cli.group(name="orchestrate")
def orchestrate_group():
    """Orchestrate agents across domains."""
    pass


@orchestrate_group.command(name="run")
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
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Interactive mode: confirm before each step",
)
@click.option(
    "--track",
    "-t",
    is_flag=True,
    help="Enable performance tracking",
)
@click.option(
    "--workflow-id",
    type=str,
    help="Custom workflow ID (auto-generated if not provided)",
)
@click.pass_context
def orchestrate_run(ctx, domain: str, goal: str, output: str | None, verbose: bool,
                    interactive: bool, track: bool, workflow_id: str | None):
    """
    Run orchestration for a domain.

    Example:
        ontology-kit orchestrate run --domain business --goal "Forecast revenue for next 30 days"
    """
    console.print(f"\n[bold cyan]🚀 Ontology-Kit Orchestration[/bold cyan]")
    console.print(f"[dim]Domain:[/dim] {domain}")
    console.print(f"[dim]Goal:[/dim] {goal}\n")

    app = ctx.obj['app']

    # Generate workflow ID if not provided
    if not workflow_id:
        workflow_id = f"{domain}_{int(time.time())}"

    try:
        # Create orchestrator
        with console.status("[bold green]Initializing orchestrator..."):
            orchestrator = app.factory.create_orchestrator(domain)

        if interactive:
            console.print(
                "\n[bold yellow]Orchestrator Configuration:[/bold yellow]")
            _display_orchestrator_config(orchestrator, verbose)
            if not Confirm.ask("\n[bold]Proceed with execution?[/bold]"):
                console.print("[yellow]Cancelled.[/yellow]")
                return

        # Start tracking if enabled
        if track:
            workflow = app.workflow_analyzer.start_workflow_tracking(
                workflow_id, goal)
            collector = app.collector
        else:
            collector = None
            workflow = None

        # Execute with tracking
        if track and collector:
            with collector.track_execution("orchestrator", domain, goal, session_id=workflow_id):
                with console.status("[bold green]Executing..."):
                    task = AgentTask(prompt=goal)
                    result = orchestrator.run(task)

                # Record workflow completion
                if workflow:
                    app.workflow_analyzer.complete_workflow(
                        workflow_id,
                        "success" if hasattr(
                            result, "result") else "completed",
                        metrics={"duration": collector._record_var.get(
                        ).execution.duration_seconds or 0.0}
                    )
        else:
            # Execute without tracking
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
        # Record failure if tracking
        if track and workflow:
            app.workflow_analyzer.complete_workflow(
                workflow_id,
                "failed",
                metrics={"error": str(e)}
            )

        console.print(f"\n[bold red]✗ Error:[/bold red] {e}", style="red")
        if verbose:
            import traceback
            console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        raise click.ClickException(str(e))


@orchestrate_group.command(name="workflow")
@click.option(
    "--workflow-file",
    "-f",
    type=click.Path(exists=True),
    help="JSON workflow file defining multi-step operations",
)
@click.option(
    "--save",
    "-s",
    type=click.Path(),
    help="Save workflow template to file",
)
@click.option(
    "--track",
    "-t",
    is_flag=True,
    help="Enable performance tracking for workflow",
)
@click.pass_context
def orchestrate_workflow(ctx, workflow_file: str | None, save: str | None, track: bool):
    """
    Execute or create multi-step workflows.

    Workflow JSON format:
    {
        "steps": [
            {"domain": "business", "goal": "Forecast revenue"},
            {"domain": "business", "goal": "Find leverage points"}
        ],
        "output": "results.json"
    }
    """
    if save:
        # Create workflow template
        template = {
            "name": "Example Workflow",
            "steps": [
                {"domain": "business", "goal": "Forecast revenue for next 30 days"},
                {"domain": "business", "goal": "Find top 3 leverage points"},
            ],
            "output": "workflow_results.json"
        }
        with open(save, "w") as f:
            json.dump(template, f, indent=2)
        console.print(f"[green]✓ Workflow template saved to {save}[/green]")
        return

    if not workflow_file:
        console.print(
            "[red]Error: Must provide --workflow-file or --save[/red]")
        sys.exit(1)

    # Load and execute workflow
    with open(workflow_file, "r") as f:
        workflow_config = json.load(f)

    console.print(
        f"\n[bold cyan]Executing Workflow: {workflow_config.get('name', 'Unnamed')}[/bold cyan]\n")

    app = ctx.obj['app']
    collector = app.collector if track else None

    # Start workflow tracking
    workflow_id = workflow_config.get(
        "workflow_id", f"workflow_{int(time.time())}")
    if track:
        workflow = app.workflow_analyzer.start_workflow_tracking(
            workflow_id,
            workflow_config.get('name', 'Unnamed workflow')
        )

    results = []

    for i, step in enumerate(workflow_config.get("steps", []), 1):
        domain = step.get("domain")
        goal = step.get("goal")

        console.print(
            f"[bold]Step {i}/{len(workflow_config['steps'])}:[/bold] {goal}")

        try:
            orchestrator = app.factory.create_orchestrator(domain)
            task = AgentTask(prompt=goal)

            if track and collector:
                with collector.track_execution(f"workflow_step_{i}", domain, goal, session_id=workflow_id):
                    result = orchestrator.run(task)
            else:
                result = orchestrator.run(task)

            results.append({
                "step": i,
                "domain": domain,
                "goal": goal,
                "result": result.result if hasattr(result, "result") else result
            })
            console.print(f"[green]✓ Step {i} complete[/green]\n")
        except Exception as e:
            console.print(f"[red]✗ Step {i} failed: {e}[/red]")
            results.append({
                "step": i,
                "domain": domain,
                "goal": goal,
                "error": str(e)
            })

    # Complete workflow tracking
    if track:
        app.workflow_analyzer.complete_workflow(
            workflow_id,
            "success" if all(
                "error" not in r for r in results) else "partial_failure",
            metrics={"steps_completed": len(
                [r for r in results if "error" not in r])}
        )

    # Save results
    output_file = workflow_config.get("output", "workflow_results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    console.print(
        f"[green]✓ Workflow complete. Results saved to {output_file}[/green]")


# ============================================================================
# ONTOLOGY COMMANDS
# ============================================================================

@cli.group(name="ontology")
def ontology_group():
    """Query and explore ontologies."""
    pass


@ontology_group.command(name="query")
@click.option(
    "--sparql",
    "-q",
    required=True,
    help="SPARQL query string",
)
@click.option(
    "--ontology",
    "-o",
    default="core",
    help="Ontology file name (without .ttl extension)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "raw"]),
    default="table",
    help="Output format",
)
def ontology_query(sparql: str, ontology: str, format: str):
    """
    Execute SPARQL query against ontology.

    Example:
        ontology-kit ontology query --sparql "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"
    """
    try:
        ontology_path = f"assets/ontologies/{ontology}.ttl"
        loader = OntologyLoader(ontology_path)
        graph = loader.load()

        results = list(graph.query(sparql))

        if format == "json":
            # Convert to JSON-serializable format
            output = []
            for row in results:
                row_dict = {}
                for key in row.keys():
                    row_dict[key] = str(row[key])
                output.append(row_dict)
            console.print(json.dumps(output, indent=2))
        elif format == "table":
            if results:
                table = Table(show_header=True, header_style="bold magenta")
                # Get column names from first result
                columns = list(results[0].keys())
                for col in columns:
                    table.add_column(col, style="cyan")
                # Add rows
                for row in results:
                    table.add_row(*[str(row[col]) for col in columns])
                console.print(table)
            else:
                console.print("[yellow]No results found.[/yellow]")
        else:  # raw
            for row in results:
                console.print(row)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@ontology_group.command(name="explore")
@click.option(
    "--ontology",
    "-o",
    default="core",
    help="Ontology file name (without .ttl extension)",
)
@click.option(
    "--entity",
    "-e",
    help="Entity IRI or label to explore",
)
def ontology_explore(ontology: str, entity: str | None):
    """
    Explore ontology structure and entities.

    Example:
        ontology-kit ontology explore --ontology business
        ontology-kit ontology explore --ontology business --entity "Business"
    """
    try:
        ontology_path = f"assets/ontologies/{ontology}.ttl"
        loader = OntologyLoader(ontology_path)
        graph = loader.load()

        if entity:
            # Explore specific entity
            console.print(
                f"\n[bold cyan]Exploring Entity: {entity}[/bold cyan]\n")

            # Query for entity properties
            query = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT ?property ?value
            WHERE {{
                ?entity ?property ?value .
                FILTER (
                    STR(?entity) = "{entity}" ||
                    STR(?entity) LIKE "%{entity}%" ||
                    ?value = "{entity}"
                )
            }}
            LIMIT 50
            """
            results = list(graph.query(query))

            if results:
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")
                for row in results:
                    table.add_row(str(row.property), str(row.value))
                console.print(table)
            else:
                console.print(
                    f"[yellow]No properties found for entity: {entity}[/yellow]")
        else:
            # Show ontology overview
            console.print(
                f"\n[bold cyan]Ontology Overview: {ontology}[/bold cyan]\n")

            # Count classes
            classes_query = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT (COUNT(DISTINCT ?class) as ?count)
            WHERE {
                ?class a owl:Class .
            }
            """
            class_count = list(graph.query(classes_query))[0][0]

            # Count properties
            props_query = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT (COUNT(DISTINCT ?prop) as ?count)
            WHERE {
                ?prop a owl:ObjectProperty .
            }
            """
            prop_count = list(graph.query(props_query))[0][0]

            # List classes
            list_classes_query = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT DISTINCT ?class ?label
            WHERE {
                ?class a owl:Class .
                OPTIONAL { ?class rdfs:label ?label . }
            }
            ORDER BY ?class
            LIMIT 20
            """
            classes = list(graph.query(list_classes_query))

            console.print(f"[bold]Classes:[/bold] {class_count}")
            console.print(f"[bold]Properties:[/bold] {prop_count}\n")

            if classes:
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Class IRI", style="cyan")
                table.add_column("Label", style="green")
                for row in classes:
                    # Use bracket notation because 'class' is a reserved keyword in Python
                    # rdflib ResultRow supports bracket access
                    class_iri = row['class']
                    # Handle optional label field (OPTIONAL fields return None when not bound)
                    # Check if 'label' exists in row keys and is not None
                    label = row['label'] if 'label' in row.keys(
                    ) and row['label'] is not None else None
                    table.add_row(str(class_iri), str(label) if label else "")
                console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# ============================================================================
# ML WORKFLOW COMMANDS
# ============================================================================

@cli.group(name="ml")
def ml_group():
    """Machine learning workflows and leverage analysis."""
    pass


@ml_group.command(name="leverage")
@click.option(
    "--terms",
    "-t",
    required=True,
    multiple=True,
    help="Business terms to analyze (can specify multiple)",
)
@click.option(
    "--kpi",
    "-k",
    required=True,
    help="Target KPI (e.g., Revenue, Satisfaction)",
)
@click.option(
    "--actionable",
    "-a",
    multiple=True,
    help="Actionable terms (can specify multiple)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for results",
)
def ml_leverage(terms: tuple[str, ...], kpi: str, actionable: tuple[str, ...], output: str | None):
    """
    Analyze leverage points for business optimization.

    Example:
        ontology-kit ml leverage -t Revenue -t Budget -t Marketing -k Revenue -a Budget -a Marketing
    """
    console.print("\n[bold cyan]🔍 Leverage Analysis[/bold cyan]\n")

    try:
        from agent_kit.tools.ml_training import analyze_leverage

        result = analyze_leverage({
            "terms": list(terms),
            "kpi_term": kpi,
            "actionable_terms": list(actionable) if actionable else list(terms)
        })

        # Display results
        console.print(f"[bold]Top Leverage Points:[/bold]\n")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Term", style="cyan")
        table.add_column("Leverage Score", style="green")
        table.add_column("Actionable", style="yellow")

        for lever in result.get("top_levers", [])[:10]:
            table.add_row(
                lever.get("term", ""),
                f"{lever.get('leverage', 0):.3f}",
                "✓" if lever.get("term") in actionable else ""
            )
        console.print(table)

        if output:
            with open(output, "w") as f:
                json.dump(result, f, indent=2, default=str)
            console.print(f"\n[dim]Results saved to {output}[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@ml_group.command(name="graph")
@click.option(
    "--terms",
    "-t",
    required=True,
    multiple=True,
    help="Terms to build graph from",
)
@click.option(
    "--threshold",
    default=0.7,
    type=float,
    help="Similarity threshold (0.0-1.0)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="outputs/semantic_graph.json",
    help="Output file for graph JSON",
)
def ml_graph(terms: tuple[str, ...], threshold: float, output: str):
    """
    Build semantic graph from business entities.

    Example:
        ontology-kit ml graph -t Revenue -t Budget -t Marketing -t Sales --threshold 0.7
    """
    console.print("\n[bold cyan]📊 Building Semantic Graph[/bold cyan]\n")

    try:
        from agent_kit.tools.semantic_graph import build_semantic_graph

        result = build_semantic_graph({
            "terms": list(terms),
            "similarity_threshold": threshold,
            "output_path": output
        })

        graph_data = result.get("graph", {})
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        console.print(f"[green]✓ Graph built successfully[/green]")
        console.print(f"  Nodes: {len(nodes)}")
        console.print(f"  Edges: {len(edges)}")
        console.print(f"  Saved to: {output}\n")

        # Show top nodes by centrality
        if "centrality" in graph_data:
            console.print("[bold]Top Nodes by Centrality:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Node", style="cyan")
            table.add_column("Betweenness", style="green")
            table.add_column("Closeness", style="yellow")

            centrality = graph_data["centrality"]
            sorted_nodes = sorted(
                centrality.items(),
                key=lambda x: x[1].get("betweenness", 0),
                reverse=True
            )[:10]

            for node_id, metrics in sorted_nodes:
                node_name = next(
                    (n["id"] for n in nodes if n["id"] == node_id), node_id)
                table.add_row(
                    node_name,
                    f"{metrics.get('betweenness', 0):.3f}",
                    f"{metrics.get('closeness', 0):.3f}"
                )
            console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@ml_group.command(name="target-leverage")
@click.option(
    "--graph",
    "-g",
    required=True,
    type=click.Path(exists=True),
    help="Path to semantic graph JSON",
)
@click.option(
    "--target",
    "-t",
    required=True,
    help="Target KPI (e.g., Revenue)",
)
@click.option(
    "--top-k",
    default=5,
    type=int,
    help="Number of top levers to return",
)
def ml_target_leverage(graph: str, target: str, top_k: int):
    """
    Compute targeted leverage scores for specific KPI.

    Example:
        ontology-kit ml target-leverage --graph outputs/semantic_graph.json --target Revenue --top-k 5
    """
    console.print("\n[bold cyan]🎯 Targeted Leverage Analysis[/bold cyan]\n")

    try:
        from agent_kit.tools.semantic_graph import compute_target_leverage

        result = compute_target_leverage({
            "graph_path": graph,
            "target": target,
            "top_k": top_k
        })

        levers = result.get("levers", [])

        if levers:
            console.print(
                f"[bold]Top {len(levers)} Leverage Points for {target}:[/bold]\n")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Lever", style="cyan")
            table.add_column("Score", style="green")
            table.add_column("Betweenness", style="yellow")
            table.add_column("Path Strength", style="blue")

            for lever in levers:
                table.add_row(
                    lever.get("lever", ""),
                    f"{lever.get('leverage_score', 0):.3f}",
                    f"{lever.get('betweenness', 0):.3f}",
                    f"{lever.get('path_strength', 0):.3f}"
                )
            console.print(table)

            # Show strongest paths
            if "strongest_paths" in result:
                console.print("\n[bold]Strongest Paths:[/bold]")
                for i, path in enumerate(result["strongest_paths"][:3], 1):
                    path_str = " → ".join(path.get("nodes", []))
                    console.print(
                        f"  {i}. {path_str} (strength: {path.get('strength', 0):.3f})")

        else:
            console.print("[yellow]No leverage points found.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@ml_group.command(name="interventions")
@click.option(
    "--graph",
    "-g",
    required=True,
    type=click.Path(exists=True),
    help="Path to semantic graph JSON",
)
@click.option(
    "--node",
    "-n",
    required=True,
    help="Lever node to generate interventions for",
)
@click.option(
    "--target",
    "-t",
    required=True,
    help="Target KPI",
)
def ml_interventions(graph: str, node: str, target: str):
    """
    Generate intervention recommendations for high-leverage nodes.

    Example:
        ontology-kit ml interventions --graph outputs/semantic_graph.json --node Marketing --target Revenue
    """
    console.print("\n[bold cyan]💡 Intervention Recommendations[/bold cyan]\n")

    try:
        from agent_kit.tools.semantic_graph import recommend_interventions

        result = recommend_interventions({
            "graph_path": graph,
            "node": node,
            "target": target
        })

        experiments = result.get("experiments", [])

        if experiments:
            for i, exp in enumerate(experiments, 1):
                console.print(
                    f"[bold]Experiment {i}:[/bold] {exp.get('name', 'Unnamed')}")
                console.print(f"  Action: {exp.get('action', 'N/A')}")
                console.print(
                    f"  Expected Lift: {exp.get('expected_lift', 0):.1f}%")
                console.print(
                    f"  Sample Size: {exp.get('sample_size', {}).get('per_group', 'N/A')}/group")
                console.print(
                    f"  Duration: {exp.get('duration_weeks', 'N/A')} weeks")
                console.print()
        else:
            console.print("[yellow]No experiments generated.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# ============================================================================
# AGENT COMMANDS
# ============================================================================

@cli.group(name="agent")
def agent_group():
    """Manage and run individual agents."""
    pass


@agent_group.command(name="list")
def agent_list():
    """List all available agents."""
    console.print("\n[bold cyan]Available Agents[/bold cyan]\n")

    factory = AgentFactory()
    agents = factory.AGENT_REGISTRY

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Agent Name", style="cyan")
    table.add_column("Class", style="green")

    for name, agent_class in agents.items():
        table.add_row(name, agent_class.__name__)

    console.print(table)
    console.print()


@agent_group.command(name="run")
@click.option(
    "--name",
    "-n",
    required=True,
    help="Agent name (e.g., ForecastAgent)",
)
@click.option(
    "--domain",
    "-d",
    help="Domain context (optional)",
)
@click.option(
    "--goal",
    "-g",
    required=True,
    help="Task goal",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file",
)
def agent_run(name: str, domain: str | None, goal: str, output: str | None):
    """
    Run an individual agent.

    Example:
        ontology-kit agent run --name ForecastAgent --domain business --goal "Forecast next 30 days"
    """
    console.print(f"\n[bold cyan]Running Agent: {name}[/bold cyan]\n")

    try:
        factory = AgentFactory()
        agent = factory.create_agent(name, domain=domain)

        task = AgentTask(prompt=goal)
        result = agent.run(task)

        console.print(f"[bold]Result:[/bold] {result.result}\n")

        if output:
            with open(output, "w") as f:
                json.dump({"result": result.result}, f, indent=2, default=str)
            console.print(f"[dim]Saved to {output}[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# ============================================================================
# TOOL COMMANDS
# ============================================================================

@cli.group(name="tool")
def tool_group():
    """Discover and execute tools via ontology."""
    pass


@tool_group.command(name="discover")
@click.option(
    "--ontology",
    "-o",
    default="ml_tools",
    help="Ontology file name",
)
@click.option(
    "--algorithm",
    "-a",
    help="Filter by algorithm (e.g., t-SNE)",
)
def tool_discover(ontology: str, algorithm: str | None):
    """
    Discover tools via ontology queries.

    Example:
        ontology-kit tool discover --ontology ml_tools
        ontology-kit tool discover --ontology ml_tools --algorithm t-SNE
    """
    console.print("\n[bold cyan]🔧 Tool Discovery[/bold cyan]\n")

    try:
        ontology_path = f"assets/ontologies/{ontology}.ttl"
        loader = OntologyLoader(ontology_path)
        graph = loader.load()

        from agent_kit.tools.ml_training import ML_TOOL_REGISTRY
        orchestrator = OntologyOrchestrator(loader, ML_TOOL_REGISTRY)

        if algorithm:
            tools = orchestrator.discover_tools_by_algorithm(algorithm)
            console.print(f"[bold]Tools implementing '{algorithm}':[/bold]\n")
        else:
            # List all tools
            query = """
            PREFIX ml: <http://agent-kit.com/ontology/ml#>
            SELECT ?tool ?py ?label
            WHERE {
                ?tool ml:hasPythonIdentifier ?py .
                OPTIONAL { ?tool rdfs:label ?label . }
            }
            """
            results = list(graph.query(query))
            tools = []
            for row in results:
                py_id = str(row.py)
                if py_id in ML_TOOL_REGISTRY:
                    tools.append(ML_TOOL_REGISTRY[py_id])

        if tools:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Python ID", style="cyan")
            table.add_column("Description", style="green")

            for tool in tools[:20]:  # Limit to 20
                desc = tool.get("description", "No description")
                table.add_row(tool.get("python_id", "N/A"), desc[:80])
            console.print(table)
        else:
            console.print("[yellow]No tools found.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# ============================================================================
# DOMAIN COMMANDS (Existing)
# ============================================================================

@cli.command(name="list-domains")
@click.pass_context
def list_domains(ctx):
    """
    List all available domains and their configurations.

    Example:
        ontology-kit list-domains
    """
    console.print("\n[bold cyan]Available Domains[/bold cyan]\n")

    app = ctx.obj['app']
    domains = app.registry.list_domains()

    if not domains:
        console.print(
            "[yellow]No domains found. Create YAML configs in src/agent_kit/domains/[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Domain", style="cyan")
    table.add_column("Description")
    table.add_column("Agents", style="green")
    table.add_column("Tools", style="blue")

    for domain_id in domains:
        cfg = app.registry.get(domain_id)
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
@click.pass_context
def validate_config(ctx, domain: str | None):
    """
    Validate domain configurations.

    Example:
        ontology-kit validate-config --domain business
    """
    console.print("\n[bold cyan]Validating Domain Configs[/bold cyan]\n")

    app = ctx.obj['app']
    domains = [domain] if domain else app.registry.list_domains()

    all_valid = True

    for domain_id in domains:
        try:
            cfg = app.registry.get(domain_id)

            # Check required fields (DomainConfig is dict subclass, so .get() works)
            required = ["id", "description", "default_agents", "allowed_tools"]
            missing = [field for field in required if field not in cfg or not cfg.get(field)]

            if missing:
                console.print(
                    f"[red]✗ {domain_id}: Missing fields {missing}[/red]")
                all_valid = False
            else:
                console.print(f"[green]✓ {domain_id}: Valid[/green]")

                # Check agents exist in registry
                for agent_name in cfg.default_agents:
                    if agent_name not in app.factory.AGENT_REGISTRY:
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
# INTERACTIVE MODE
# ============================================================================

@cli.group(name="dashboard")
def dashboard_group():
    """Generate and view dashboards."""
    pass


@dashboard_group.command(name="full")
@click.option(
    "--days",
    default=7,
    type=int,
    help="Number of days to include in analysis",
)
@click.option(
    "--open",
    is_flag=True,
    help="Open dashboard in browser after generation",
)
def dashboard_full(days: int, open: bool):
    """Generate full interactive dashboard."""
    console.print("\n[bold cyan]📊 Generating Full Dashboard[/bold cyan]\n")

    try:
        dashboard = InteractiveDashboard()
        path = dashboard.generate_full_dashboard(days=days)

        console.print(f"[green]✓ Dashboard generated:[/green] {path}")

        if open:
            import webbrowser
            webbrowser.open(f"file://{Path(path).absolute()}")
            console.print("[dim]Opened in browser[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.ClickException(str(e))


@dashboard_group.command(name="performance")
@click.option(
    "--agent",
    "-a",
    help="Specific agent to focus on",
)
@click.option(
    "--open",
    is_flag=True,
    help="Open dashboard in browser after generation",
)
def dashboard_performance(agent: str | None, open: bool):
    """Generate performance-focused dashboard."""
    console.print(
        "\n[bold cyan]📈 Generating Performance Dashboard[/bold cyan]\n")

    try:
        dashboard = InteractiveDashboard()
        path = dashboard.generate_performance_focused_dashboard(
            agent_name=agent)

        console.print(f"[green]✓ Dashboard generated:[/green] {path}")

        if open:
            import webbrowser
            webbrowser.open(f"file://{Path(path).absolute()}")
            console.print("[dim]Opened in browser[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.ClickException(str(e))


@cli.command(name="interactive")
@click.pass_context
def interactive(ctx):
    """
    Launch interactive REPL mode for complex workflows.

    Example:
        ontology-kit interactive
    """
    console.print("\n[bold cyan]🧠 Ontology-Kit Interactive Mode[/bold cyan]")
    console.print("[dim]Type 'help' for commands, 'exit' to quit[/dim]\n")

    app = ctx.obj['app']

    while True:
        try:
            command = Prompt.ask(
                "[bold cyan]ontology-kit>[/bold cyan]").strip()

            if not command:
                continue

            if command == "exit" or command == "quit":
                console.print("[yellow]Goodbye![/yellow]")
                break

            if command == "help":
                _show_interactive_help()
                continue

            # Parse command
            parts = command.split()
            cmd = parts[0]

            if cmd == "domains":
                domains = app.registry.list_domains()
                console.print(
                    f"\n[bold]Available domains:[/bold] {', '.join(domains)}\n")

            elif cmd == "agents":
                agents = list(app.factory.AGENT_REGISTRY.keys())
                console.print(
                    f"\n[bold]Available agents:[/bold] {', '.join(agents)}\n")

            elif cmd == "run":
                if len(parts) < 3:
                    console.print("[red]Usage: run <domain> <goal>[/red]")
                    continue
                domain = parts[1]
                goal = " ".join(parts[2:])
                orchestrator = app.factory.create_orchestrator(domain)
                task = AgentTask(prompt=goal)
                result = orchestrator.run(task)
                console.print(f"\n[bold]Result:[/bold] {result.result}\n")

            elif cmd == "dashboard":
                dashboard = InteractiveDashboard()
                path = dashboard.generate_full_dashboard(days=7)
                console.print(
                    f"\n[green]Dashboard generated:[/green] {path}\n")

            else:
                console.print(
                    f"[yellow]Unknown command: {cmd}. Type 'help' for available commands.[/yellow]")

        except KeyboardInterrupt:
            console.print(
                "\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def _show_interactive_help():
    """Show help for interactive mode."""
    help_text = """
[bold]Available Commands:[/bold]

  domains              List all available domains
  agents               List all available agents
  run <domain> <goal>  Run orchestration for a domain
  dashboard            Generate full dashboard
  help                 Show this help message
  exit / quit          Exit interactive mode

[bold]Examples:[/bold]

  ontology-kit> domains
  ontology-kit> run business "Forecast revenue for next 30 days"
  ontology-kit> agents
  ontology-kit> dashboard
"""
    console.print(help_text)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _display_orchestrator_config(orchestrator, verbose: bool):
    """Display orchestrator configuration."""
    console.print(f"  Domain: {orchestrator.domain}")
    console.print(f"  Specialists: {len(orchestrator.specialists)}")
    if verbose:
        for spec in orchestrator.specialists:
            console.print(f"    - {spec.__class__.__name__}")
    console.print(f"  Tools: {len(orchestrator.tools)}")
    console.print(f"  Policies: {len(orchestrator.risk_policies)}")


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
        console.print(
            f"[bold]Signals:[/bold] {len(result['signals'])} generated\n")

    if "edges" in result and result["edges"]:
        console.print(
            f"[bold]Betting Edges:[/bold] {len(result['edges'])} detected\n")

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
            console.print(
                f"  • {spec_result.get('specialist')}: {spec_result.get('result')}")
        console.print()


if __name__ == "__main__":
    cli()
