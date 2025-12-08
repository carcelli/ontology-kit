"""
Interactive Ontology Exploration Dashboard

This module provides an interactive dashboard for exploring ontologies and
agent performance data. Features include:

1. Ontology Graph Visualization: Interactive 3D graph of ontology relationships
2. Agent Performance Dashboard: Real-time metrics and trends
3. Workflow Explorer: Step-by-step workflow breakdown with metrics
4. Decision Analysis: Confidence scores and decision patterns
5. Tool Usage Analytics: Which tools work best for which tasks
6. Learning Progress: Performance improvement over time

The dashboard combines static visualizations (saved as HTML) with
interactive exploration capabilities.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from agent_kit.data_collection import PerformanceAnalytics
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.ontology_ml_workflow import OntologyMLWorkflowAnalyzer


class InteractiveDashboard:
    """
    Interactive dashboard for ontology and agent performance exploration.

    Generates HTML dashboards that can be opened in browsers for interactive
    exploration of ontology structures and agent performance patterns.
    """

    def __init__(
        self,
        ontology_path: str = "assets/ontologies/core.ttl",
        data_dir: str = "outputs/agent_data",
        workflow_data_dir: str = "outputs/workflow_data",
        output_dir: str = "outputs/dashboards",
    ):
        self.ontology_path = ontology_path
        self.data_dir = Path(data_dir)
        self.workflow_data_dir = Path(workflow_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Load ontology
        self.ontology = OntologyLoader(ontology_path).load()
        self.analytics = PerformanceAnalytics(str(self.data_dir))
        self.workflow_analyzer = OntologyMLWorkflowAnalyzer(ontology_path)

    def generate_full_dashboard(self, days: int = 7) -> str:
        """
        Generate complete interactive dashboard.

        Args:
            days: Number of recent days to include in analysis

        Returns:
            Path to generated HTML dashboard
        """
        # Load performance data
        performance_data = self.analytics.get_agent_performance_summary(days=days)

        # Create dashboard components
        ontology_viz = self._create_ontology_graph()
        performance_charts = self._create_performance_dashboard(performance_data)
        workflow_explorer = self._create_workflow_explorer()
        decision_analysis = self._create_decision_analysis()

        # Combine into single HTML page
        dashboard_html = self._create_dashboard_html(
            ontology_viz, performance_charts, workflow_explorer, decision_analysis
        )

        # Save dashboard
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dashboard_path = self.output_dir / f"ontology_dashboard_{timestamp}.html"

        with open(dashboard_path, "w", encoding="utf-8") as f:
            f.write(dashboard_html)

        return str(dashboard_path)

    def generate_performance_focused_dashboard(
        self, agent_name: str | None = None
    ) -> str:
        """
        Generate dashboard focused on agent performance metrics.

        Args:
            agent_name: Specific agent to focus on (None for all)

        Returns:
            Path to generated HTML dashboard
        """
        performance_data = self.analytics.get_agent_performance_summary(
            agent_name=agent_name
        )

        # Create performance-focused visualizations
        timeline_chart = self._create_performance_timeline(performance_data)
        confidence_distribution = self._create_confidence_distribution(performance_data)
        bottleneck_analysis = self._create_bottleneck_visualization()

        # Create HTML
        dashboard_html = self._create_performance_dashboard_html(
            timeline_chart, confidence_distribution, bottleneck_analysis, agent_name
        )

        # Save dashboard
        agent_suffix = f"_{agent_name}" if agent_name else "_all_agents"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dashboard_path = (
            self.output_dir / f"performance_dashboard{agent_suffix}_{timestamp}.html"
        )

        with open(dashboard_path, "w", encoding="utf-8") as f:
            f.write(dashboard_html)

        return str(dashboard_path)

    def _create_ontology_graph(self) -> str:
        """Create interactive 3D ontology graph visualization."""
        # Extract nodes and edges from ontology
        node_types = {}

        # Query for all triples
        query = """
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject ?predicate ?object .
        }
        """

        results = self.ontology.query(query)

        # Build graph
        G = nx.DiGraph()

        for row in results:
            subj = str(row.subject)
            pred = str(row.predicate)
            obj = str(row.object)

            # Add nodes
            G.add_node(subj)
            G.add_node(obj)

            # Add edge with predicate as label
            G.add_edge(subj, obj, label=pred.split("#")[-1] if "#" in pred else pred)

            # Categorize nodes by type
            if "Agent" in subj or "Agent" in obj:
                node_types[subj] = "Agent"
                node_types[obj] = "Agent"
            elif "Task" in subj or "Task" in obj:
                node_types[subj] = "Task"
                node_types[obj] = "Task"
            elif "Tool" in subj or "Tool" in obj:
                node_types[subj] = "Tool"
                node_types[obj] = "Tool"
            else:
                node_types.setdefault(subj, "Concept")
                node_types.setdefault(obj, "Concept")

        # Scale graph if too large (limit to top 500 nodes by degree)
        if len(G) > 500:
            nodes_sorted = sorted(G.degree, key=lambda x: x[1], reverse=True)[:500]
            G = G.subgraph([n for n, _ in nodes_sorted]).copy()

        # Calculate positions using spring layout
        pos = nx.spring_layout(G, dim=3, seed=42)

        # Create 3D scatter plot
        node_x = [pos[node][0] for node in G.nodes()]
        node_y = [pos[node][1] for node in G.nodes()]
        node_z = [pos[node][2] for node in G.nodes()]

        node_labels = [
            node.split("#")[-1] if "#" in node else node for node in G.nodes()
        ]
        node_colors = [
            self._get_node_color(node_types.get(node, "Concept")) for node in G.nodes()
        ]

        # Create edges
        edge_x, edge_y, edge_z = [], [], []
        edge_text = []

        for edge in G.edges(data=True):
            x0, y0, z0 = pos[edge[0]]
            x1, y1, z1 = pos[edge[1]]

            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_z.extend([z0, z1, None])

            edge_text.append(edge[2]["label"])

        # Create edge trace
        edge_trace = go.Scatter3d(
            x=edge_x,
            y=edge_y,
            z=edge_z,
            mode="lines",
            line={"width": 2, "color": "#888"},
            hoverinfo="text",
            text=edge_text * 3,  # Repeat for each segment
            showlegend=False,
        )

        # Create node trace
        node_trace = go.Scatter3d(
            x=node_x,
            y=node_y,
            z=node_z,
            mode="markers+text",
            marker={
                "size": 8,
                "color": node_colors,
                "colorscale": "Viridis",
                "showscale": True,
                "colorbar": {"title": "Node Type"},
            },
            text=node_labels,
            hovertext=[
                f"{label}<br>Type: {node_types.get(node, 'Concept')}"
                for node, label in zip(G.nodes(), node_labels, strict=False)
            ],
            textposition="top center",
            showlegend=False,
        )

        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace])

        fig.update_layout(
            title="Ontology Relationship Graph (3D)",
            scene={
                "xaxis": {"showbackground": False},
                "yaxis": {"showbackground": False},
                "zaxis": {"showbackground": False},
            },
            margin={"l": 0, "r": 0, "b": 0, "t": 40},
            height=600,
        )

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    def _create_performance_dashboard(self, performance_data: dict[str, Any]) -> str:
        """Create performance metrics dashboard."""
        if "error" in performance_data:
            return f"<div class='alert alert-warning'>No performance data available: {performance_data['error']}</div>"

        # Create subplots
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Agent Success Rates",
                "Average Execution Times",
                "Confidence Score Distribution",
                "Task Distribution",
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "histogram"}, {"type": "pie"}],
            ],
        )

        agent_performance = performance_data.get("agent_performance", {})

        if agent_performance:
            # Success rates
            agents = list(agent_performance.keys())
            success_rates = [
                stats["success_rate"] for stats in agent_performance.values()
            ]

            fig.add_trace(
                go.Bar(
                    x=agents,
                    y=success_rates,
                    name="Success Rate",
                    marker_color="lightgreen",
                ),
                row=1,
                col=1,
            )

            # Execution times
            avg_durations = [
                stats["avg_duration"] for stats in agent_performance.values()
            ]

            fig.add_trace(
                go.Bar(
                    x=agents,
                    y=avg_durations,
                    name="Avg Duration (s)",
                    marker_color="lightblue",
                ),
                row=1,
                col=2,
            )

            # Confidence distribution (simplified - would need more data)
            # For now, show average confidence per agent
            avg_confidences = [
                stats["avg_confidence"] for stats in agent_performance.values()
            ]

            fig.add_trace(
                go.Histogram(
                    x=avg_confidences, name="Confidence Scores", marker_color="orange"
                ),
                row=2,
                col=1,
            )

        # Task distribution
        task_dist = performance_data.get("task_distribution", {})
        if task_dist:
            fig.add_trace(
                go.Pie(
                    labels=list(task_dist.keys()),
                    values=list(task_dist.values()),
                    name="Task Types",
                ),
                row=2,
                col=2,
            )

        fig.update_layout(height=800, title_text="Agent Performance Dashboard")
        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    def _create_workflow_explorer(self) -> str:
        """Create workflow step explorer from real workflow data."""
        # Load workflow data from JSON files
        workflow_files = list(self.workflow_data_dir.glob("workflow_*.json"))

        if not workflow_files:
            # No workflow data available
            fig = go.Figure()
            fig.add_annotation(
                text="No workflow data available. Run workflows to see analysis.",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            fig.update_layout(title="Workflow Stage Analysis", height=400)
            return fig.to_html(full_html=False, include_plotlyjs="cdn")

        # Aggregate stage metrics from all workflows
        stages = self.workflow_analyzer.define_workflow_stages()
        stage_names = [stage.name for stage in stages]
        stage_durations = {name: [] for name in stage_names}
        stage_successes = {name: [] for name in stage_names}

        for workflow_file in workflow_files[:50]:  # Limit to recent 50
            try:
                with open(workflow_file) as f:
                    workflow_data = json.load(f)

                # Extract stage completion data
                # Note: This is simplified - real implementation would track per-stage timing
                if workflow_data.get("duration_seconds"):
                    avg_duration = workflow_data["duration_seconds"] / len(stage_names)
                    for stage_name in stage_names:
                        stage_durations[stage_name].append(avg_duration)
                        stage_successes[stage_name].append(
                            1.0
                            if workflow_data.get("final_outcome") == "success"
                            else 0.0
                        )
            except (json.JSONDecodeError, KeyError):
                continue

        # Calculate averages
        avg_durations = [
            (
                sum(stage_durations[name]) / len(stage_durations[name])
                if stage_durations[name]
                else stage.duration_estimate
            )
            for name, stage in zip(stage_names, stages, strict=False)
        ]
        avg_success_rates = [
            (
                sum(stage_successes[name]) / len(stage_successes[name])
                if stage_successes[name]
                else 0.0
            )
            for name in stage_names
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=stage_names,
                y=avg_durations,
                name="Duration (seconds)",
                marker_color="lightblue",
                yaxis="y",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=stage_names,
                y=avg_success_rates,
                name="Success Rate",
                mode="lines+markers",
                marker_color="red",
                yaxis="y2",
            )
        )

        fig.update_layout(
            title="Workflow Stage Analysis",
            xaxis={"title": "Workflow Stage"},
            yaxis={"title": "Duration (seconds)", "side": "left"},
            yaxis2={"title": "Success Rate", "side": "right", "overlaying": "y"},
            height=400,
        )

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    def _create_decision_analysis(self) -> str:
        """Create decision confidence analysis from real decision data."""
        # Load decision data from JSONL files
        decision_files = list(self.workflow_data_dir.glob("decisions_*.jsonl"))

        decisions = []
        confidence_scores = []
        success_outcomes = []

        for decision_file in decision_files[-7:]:  # Last 7 days
            try:
                with open(decision_file) as f:
                    for line in f:
                        if line.strip():
                            decision_data = json.loads(line)
                            decisions.append(
                                decision_data.get("decision_made", "Unknown")
                            )
                            confidence_scores.append(
                                decision_data.get("confidence_score", 0.0)
                            )
                            success_outcomes.append(
                                decision_data.get("outcome") == "success"
                                if decision_data.get("outcome")
                                else None
                            )
            except (json.JSONDecodeError, FileNotFoundError):
                continue

        if not decisions:
            # No decision data available
            fig = go.Figure()
            fig.add_annotation(
                text="No decision data available. Run workflows to see analysis.",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            fig.update_layout(title="Decision Confidence vs Success", height=400)
            return fig.to_html(full_html=False, include_plotlyjs="cdn")

        # Aggregate by decision type (top 10 most common)
        from collections import Counter

        decision_counts = Counter(decisions)
        top_decisions = [d for d, _ in decision_counts.most_common(10)]

        # Calculate average confidence and success rate per decision type
        decision_stats = {}
        for decision, conf, success in zip(
            decisions, confidence_scores, success_outcomes, strict=False
        ):
            if decision not in decision_stats:
                decision_stats[decision] = {"confidences": [], "successes": []}
            decision_stats[decision]["confidences"].append(conf)
            if success is not None:
                decision_stats[decision]["successes"].append(success)

        top_decision_names = [d for d in top_decisions if d in decision_stats]
        avg_confidences = [
            sum(decision_stats[d]["confidences"])
            / len(decision_stats[d]["confidences"])
            for d in top_decision_names
        ]
        success_rates = [
            (
                sum(decision_stats[d]["successes"])
                / len(decision_stats[d]["successes"])
                if decision_stats[d]["successes"]
                else 0.0
            )
            for d in top_decision_names
        ]

        colors = [
            "green" if rate > 0.7 else "orange" if rate > 0.5 else "red"
            for rate in success_rates
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=top_decision_names,
                y=avg_confidences,
                marker_color=colors,
                name="Decision Confidence",
                text=[f"{rate:.1%}" for rate in success_rates],
                textposition="outside",
            )
        )

        fig.update_layout(
            title="Decision Confidence vs Success (Top 10 Decisions)",
            xaxis_title="Decision",
            yaxis_title="Average Confidence Score",
            height=400,
        )

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    def _create_performance_timeline(self, performance_data: dict[str, Any]) -> str:
        """Create performance timeline visualization from real data."""
        # Load daily summaries
        summary_files = sorted(
            self.data_dir.glob("daily_summary_*.json"), reverse=True
        )[:7]

        dates = []
        success_rates = []

        for summary_file in summary_files:
            try:
                with open(summary_file) as f:
                    summary = json.load(f)
                    date_str = summary.get(
                        "date", summary_file.stem.replace("daily_summary_", "")
                    )
                    dates.append(datetime.strptime(date_str, "%Y-%m-%d"))

                    # Calculate overall success rate
                    agent_perf = summary.get("agent_performance", {})
                    if agent_perf:
                        total_sessions = sum(
                            stats.get("session_count", 0)
                            for stats in agent_perf.values()
                        )
                        total_successes = sum(
                            stats.get("total_successes", 0)
                            for stats in agent_perf.values()
                        )
                        success_rate = (
                            total_successes / total_sessions
                            if total_sessions > 0
                            else 0.0
                        )
                        success_rates.append(success_rate)
                    else:
                        success_rates.append(0.0)
            except (json.JSONDecodeError, ValueError, FileNotFoundError):
                continue

        if not dates:
            # No data available
            fig = go.Figure()
            fig.add_annotation(
                text="No performance data available. Run agents to see timeline.",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            fig.update_layout(title="Performance Timeline", height=400)
            return fig.to_html(full_html=False, include_plotlyjs="cdn")

        # Sort by date
        sorted_data = sorted(zip(dates, success_rates, strict=False))
        dates, success_rates = (
            zip(*sorted_data, strict=False) if sorted_data else ([], [])
        )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=list(dates),
                y=list(success_rates),
                mode="lines+markers",
                name="Success Rate",
                line={"color": "green", "width": 3},
            )
        )

        fig.update_layout(
            title="Performance Timeline (Last 7 Days)",
            xaxis_title="Date",
            yaxis_title="Success Rate",
            height=400,
        )

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    def _create_confidence_distribution(self, performance_data: dict[str, Any]) -> str:
        """Create confidence score distribution from real decision data."""
        # Load decision data from JSONL files
        decision_files = list(self.workflow_data_dir.glob("decisions_*.jsonl"))

        confidence_scores = []

        for decision_file in decision_files[-7:]:  # Last 7 days
            try:
                with open(decision_file) as f:
                    for line in f:
                        if line.strip():
                            decision_data = json.loads(line)
                            conf = decision_data.get("confidence_score")
                            if conf is not None:
                                confidence_scores.append(conf)
            except (json.JSONDecodeError, FileNotFoundError):
                continue

        # Also try loading from agent performance records
        if not confidence_scores:
            record_files = list(self.data_dir.glob("*/*.json"))[
                :100
            ]  # Limit to 100 records
            for record_file in record_files:
                try:
                    with open(record_file) as f:
                        record_data = json.load(f)
                        for decision in record_data.get("decisions", []):
                            conf = decision.get("confidence_score")
                            if conf is not None:
                                confidence_scores.append(conf)
                except (json.JSONDecodeError, FileNotFoundError):
                    continue

        if not confidence_scores:
            # No confidence data available
            fig = go.Figure()
            fig.add_annotation(
                text="No confidence data available. Run agents to see distribution.",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            fig.update_layout(title="Decision Confidence Distribution", height=400)
            return fig.to_html(full_html=False, include_plotlyjs="cdn")

        fig = go.Figure()

        fig.add_trace(
            go.Histogram(
                x=confidence_scores,
                nbinsx=10,
                marker_color="orange",
                name="Confidence Scores",
            )
        )

        fig.update_layout(
            title=f"Decision Confidence Distribution (n={len(confidence_scores)})",
            xaxis_title="Confidence Score",
            yaxis_title="Frequency",
            height=400,
        )

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    def _create_bottleneck_visualization(self) -> str:
        """Create bottleneck analysis visualization."""
        bottlenecks = self.analytics.identify_bottlenecks()

        categories = [
            "Slow Queries",
            "Failed Tools",
            "Low Confidence",
            "High Resource Usage",
        ]
        counts = [
            len(bottlenecks["bottlenecks"]["slow_queries"]),
            len(bottlenecks["bottlenecks"]["failed_tools"]),
            len(bottlenecks["bottlenecks"]["low_confidence_decisions"]),
            len(bottlenecks["bottlenecks"]["high_resource_usage"]),
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(x=categories, y=counts, marker_color="red", name="Bottleneck Count")
        )

        fig.update_layout(
            title="Performance Bottlenecks",
            xaxis_title="Bottleneck Type",
            yaxis_title="Count",
            height=400,
        )

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    def _get_node_color(self, node_type: str) -> str:
        """Get color for node type."""
        color_map = {
            "Agent": "red",
            "Task": "blue",
            "Tool": "green",
            "Concept": "orange",
            "State": "purple",
        }
        return color_map.get(node_type, "gray")

    def _create_dashboard_html(
        self,
        ontology_viz: str,
        performance_charts: str,
        workflow_explorer: str,
        decision_analysis: str,
    ) -> str:
        """Create complete dashboard HTML."""
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ontology-ML Agent Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        .chart-container {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .full-width {{
            grid-column: 1 / -1;
        }}
        .ontology-viz {{
            height: 600px;
        }}
        .performance-charts {{
            height: 800px;
        }}
        h1, h2 {{
            color: #333;
        }}
        .tabs {{
            display: flex;
            margin-bottom: 20px;
        }}
        .tab {{
            padding: 10px 20px;
            background: #ddd;
            border: none;
            cursor: pointer;
            margin-right: 5px;
        }}
        .tab.active {{
            background: #007acc;
            color: white;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Ontology-Driven ML Agent Dashboard</h1>
        <p>Interactive exploration of ontology structures and agent performance</p>
        <p><em>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</em></p>
    </div>

    <div class="tabs">
        <button class="tab active" onclick="showTab('overview')">Overview</button>
        <button class="tab" onclick="showTab('ontology')">Ontology Graph</button>
        <button class="tab" onclick="showTab('performance')">Performance</button>
        <button class="tab" onclick="showTab('workflow')">Workflow Analysis</button>
    </div>

    <div id="overview" class="tab-content active">
        <div class="dashboard-grid">
            <div class="chart-container">
                <h2>Agent Performance Overview</h2>
                {performance_charts}
            </div>
            <div class="chart-container">
                <h2>Workflow Stage Analysis</h2>
                {workflow_explorer}
            </div>
            <div class="chart-container full-width">
                <h2>Decision Analysis</h2>
                {decision_analysis}
            </div>
        </div>
    </div>

    <div id="ontology" class="tab-content">
        <div class="chart-container ontology-viz">
            <h2>Ontology Relationship Graph</h2>
            {ontology_viz}
        </div>
    </div>

    <div id="performance" class="tab-content">
        <div class="dashboard-grid">
            <div class="chart-container">
                <h2>Performance Timeline</h2>
                {self._create_performance_timeline({})}
            </div>
            <div class="chart-container">
                <h2>Confidence Distribution</h2>
                {self._create_confidence_distribution({})}
            </div>
            <div class="chart-container full-width">
                <h2>Bottleneck Analysis</h2>
                {self._create_bottleneck_visualization()}
            </div>
        </div>
    </div>

    <div id="workflow" class="tab-content">
        <div class="chart-container">
            <h2>Workflow Explorer</h2>
            <p>Detailed workflow breakdown and performance metrics would be shown here.</p>
            <p>This section would include step-by-step analysis of agent workflows,
            showing where time is spent, where decisions are made, and where improvements can be made.</p>
        </div>
    </div>

    <script>
        function showTab(tabName) {{
            // Hide all tab contents
            const contents = document.querySelectorAll('.tab-content');
            contents.forEach(content => content.classList.remove('active'));

            // Remove active class from all tabs
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => tab.classList.remove('active'));

            // Show selected tab content
            document.getElementById(tabName).classList.add('active');

            // Add active class to clicked tab
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>
        """
        return html_template

    def _create_performance_dashboard_html(
        self,
        timeline_chart: str,
        confidence_chart: str,
        bottleneck_chart: str,
        agent_name: str | None,
    ) -> str:
        """Create performance-focused dashboard HTML."""
        agent_title = f" - {agent_name}" if agent_name else " - All Agents"

        # Get real metrics from performance data
        perf_summary = self.analytics.get_agent_performance_summary(
            agent_name=agent_name, days=7
        )
        agent_perf = perf_summary.get("agent_performance", {})

        # Calculate aggregate metrics
        total_sessions = perf_summary.get("total_sessions", 0)
        if agent_perf:
            total_successes = sum(
                stats.get("total_successes", 0) for stats in agent_perf.values()
            )
            total_duration = sum(
                stats.get("total_duration", 0) for stats in agent_perf.values()
            )
            total_conf = sum(
                stats.get("avg_confidence", 0) * stats.get("total_sessions", 0)
                for stats in agent_perf.values()
            )
            total_conf_sessions = sum(
                stats.get("total_sessions", 0) for stats in agent_perf.values()
            )

            success_rate = (
                (total_successes / total_sessions * 100) if total_sessions > 0 else 0.0
            )
            avg_duration = (
                (total_duration / total_sessions) if total_sessions > 0 else 0.0
            )
            avg_confidence = (
                (total_conf / total_conf_sessions) if total_conf_sessions > 0 else 0.0
            )
        else:
            success_rate = 0.0
            avg_duration = 0.0
            avg_confidence = 0.0

        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Performance Dashboard{agent_title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .chart-container {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .full-width {{
            grid-column: 1 / -1;
        }}
        h1, h2 {{
            color: #333;
        }}
        .metrics-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #007acc;
        }}
        .metric-label {{
            color: #666;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Agent Performance Dashboard{agent_title}</h1>
        <p>Detailed performance metrics and analytics</p>
        <p><em>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</em></p>
    </div>

    <div class="metrics-summary">
        <div class="metric-card">
            <div class="metric-value">{success_rate:.1f}%</div>
            <div class="metric-label">Success Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{avg_duration:.1f}s</div>
            <div class="metric-label">Avg Duration</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{avg_confidence:.2f}</div>
            <div class="metric-label">Avg Confidence</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{total_sessions}</div>
            <div class="metric-label">Total Sessions</div>
        </div>
    </div>

    <div class="dashboard-grid">
        <div class="chart-container">
            <h2>Performance Timeline</h2>
            {timeline_chart}
        </div>
        <div class="chart-container">
            <h2>Confidence Distribution</h2>
            {confidence_chart}
        </div>
        <div class="chart-container full-width">
            <h2>Bottleneck Analysis</h2>
            {bottleneck_chart}
        </div>
    </div>
</body>
</html>
        """
        return html_template


# Convenience functions
def create_interactive_dashboard(
    ontology_path: str = "assets/ontologies/core.ttl",
    data_dir: str = "outputs/agent_data",
    workflow_data_dir: str = "outputs/workflow_data",
) -> InteractiveDashboard:
    """Create an interactive dashboard instance."""
    return InteractiveDashboard(ontology_path, data_dir, workflow_data_dir)


def generate_full_dashboard(
    ontology_path: str = "assets/ontologies/core.ttl",
    data_dir: str = "outputs/agent_data",
    workflow_data_dir: str = "outputs/workflow_data",
    days: int = 7,
) -> str:
    """Generate complete interactive dashboard."""
    dashboard = InteractiveDashboard(ontology_path, data_dir, workflow_data_dir)
    return dashboard.generate_full_dashboard(days)


def generate_performance_dashboard(
    agent_name: str | None = None,
    ontology_path: str = "assets/ontologies/core.ttl",
    data_dir: str = "outputs/agent_data",
    workflow_data_dir: str = "outputs/workflow_data",
) -> str:
    """Generate performance-focused dashboard."""
    dashboard = InteractiveDashboard(ontology_path, data_dir, workflow_data_dir)
    return dashboard.generate_performance_focused_dashboard(agent_name)
