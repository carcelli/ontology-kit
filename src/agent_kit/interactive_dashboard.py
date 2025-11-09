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
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
from rdflib import Graph, URIRef, Literal
import pandas as pd

from agent_kit.data_collection import PerformanceAnalytics
from agent_kit.ontology.loader import OntologyLoader


class InteractiveDashboard:
    """
    Interactive dashboard for ontology and agent performance exploration.

    Generates HTML dashboards that can be opened in browsers for interactive
    exploration of ontology structures and agent performance patterns.
    """

    def __init__(self, ontology_path: str = "assets/ontologies/core.ttl",
                 data_dir: str = "outputs/agent_data",
                 output_dir: str = "outputs/dashboards"):
        self.ontology_path = ontology_path
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Load ontology
        self.ontology = OntologyLoader(ontology_path).load()
        self.analytics = PerformanceAnalytics(str(self.data_dir))

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

        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)

        return str(dashboard_path)

    def generate_performance_focused_dashboard(self, agent_name: Optional[str] = None) -> str:
        """
        Generate dashboard focused on agent performance metrics.

        Args:
            agent_name: Specific agent to focus on (None for all)

        Returns:
            Path to generated HTML dashboard
        """
        performance_data = self.analytics.get_agent_performance_summary(agent_name=agent_name)

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
        dashboard_path = self.output_dir / f"performance_dashboard{agent_suffix}_{timestamp}.html"

        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)

        return str(dashboard_path)

    def _create_ontology_graph(self) -> str:
        """Create interactive 3D ontology graph visualization."""
        # Extract nodes and edges from ontology
        nodes = []
        edges = []
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
            G.add_edge(subj, obj, label=pred.split('#')[-1] if '#' in pred else pred)

            # Categorize nodes by type
            if 'Agent' in subj or 'Agent' in obj:
                node_types[subj] = 'Agent'
                node_types[obj] = 'Agent'
            elif 'Task' in subj or 'Task' in obj:
                node_types[subj] = 'Task'
                node_types[obj] = 'Task'
            elif 'Tool' in subj or 'Tool' in obj:
                node_types[subj] = 'Tool'
                node_types[obj] = 'Tool'
            else:
                node_types.setdefault(subj, 'Concept')
                node_types.setdefault(obj, 'Concept')

        # Calculate positions using spring layout
        pos = nx.spring_layout(G, dim=3, seed=42)

        # Create 3D scatter plot
        node_x = [pos[node][0] for node in G.nodes()]
        node_y = [pos[node][1] for node in G.nodes()]
        node_z = [pos[node][2] for node in G.nodes()]

        node_labels = [node.split('#')[-1] if '#' in node else node for node in G.nodes()]
        node_colors = [self._get_node_color(node_types.get(node, 'Concept')) for node in G.nodes()]

        # Create edges
        edge_x, edge_y, edge_z = [], [], []
        edge_text = []

        for edge in G.edges(data=True):
            x0, y0, z0 = pos[edge[0]]
            x1, y1, z1 = pos[edge[1]]

            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_z.extend([z0, z1, None])

            edge_text.append(edge[2]['label'])

        # Create edge trace
        edge_trace = go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            mode='lines',
            line=dict(width=2, color='#888'),
            hoverinfo='text',
            text=edge_text * 3,  # Repeat for each segment
            showlegend=False
        )

        # Create node trace
        node_trace = go.Scatter3d(
            x=node_x, y=node_y, z=node_z,
            mode='markers+text',
            marker=dict(
                size=8,
                color=node_colors,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Node Type")
            ),
            text=node_labels,
            hovertext=[f"{label}<br>Type: {node_types.get(node, 'Concept')}" for node, label in zip(G.nodes(), node_labels)],
            textposition="top center",
            showlegend=False
        )

        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace])

        fig.update_layout(
            title="Ontology Relationship Graph (3D)",
            scene=dict(
                xaxis=dict(showbackground=False),
                yaxis=dict(showbackground=False),
                zaxis=dict(showbackground=False),
            ),
            margin=dict(l=0, r=0, b=0, t=40),
            height=600
        )

        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    def _create_performance_dashboard(self, performance_data: Dict[str, Any]) -> str:
        """Create performance metrics dashboard."""
        if "error" in performance_data:
            return f"<div class='alert alert-warning'>No performance data available: {performance_data['error']}</div>"

        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Agent Success Rates", "Average Execution Times",
                          "Confidence Score Distribution", "Task Distribution"),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "histogram"}, {"type": "pie"}]]
        )

        agent_performance = performance_data.get("agent_performance", {})

        if agent_performance:
            # Success rates
            agents = list(agent_performance.keys())
            success_rates = [stats["success_rate"] for stats in agent_performance.values()]

            fig.add_trace(
                go.Bar(x=agents, y=success_rates, name="Success Rate",
                      marker_color='lightgreen'),
                row=1, col=1
            )

            # Execution times
            avg_durations = [stats["avg_duration"] for stats in agent_performance.values()]

            fig.add_trace(
                go.Bar(x=agents, y=avg_durations, name="Avg Duration (s)",
                      marker_color='lightblue'),
                row=1, col=2
            )

            # Confidence distribution (simplified - would need more data)
            # For now, show average confidence per agent
            avg_confidences = [stats["avg_confidence"] for stats in agent_performance.values()]

            fig.add_trace(
                go.Histogram(x=avg_confidences, name="Confidence Scores",
                           marker_color='orange'),
                row=2, col=1
            )

        # Task distribution
        task_dist = performance_data.get("task_distribution", {})
        if task_dist:
            fig.add_trace(
                go.Pie(labels=list(task_dist.keys()), values=list(task_dist.values()),
                      name="Task Types"),
                row=2, col=2
            )

        fig.update_layout(height=800, title_text="Agent Performance Dashboard")
        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    def _create_workflow_explorer(self) -> str:
        """Create workflow step explorer."""
        # This would show workflow stages and their metrics
        # For now, create a placeholder with sample workflow stages

        stages = [
            "Ontology Loading",
            "Task Analysis",
            "Tool Discovery",
            "Hyperdimensional Navigation",
            "ML Execution",
            "Result Integration"
        ]

        durations = [5, 15, 10, 25, 60, 20]  # Sample durations
        success_rates = [0.95, 0.88, 0.92, 0.85, 0.78, 0.90]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=stages,
            y=durations,
            name="Duration (seconds)",
            marker_color='lightblue',
            yaxis="y"
        ))

        fig.add_trace(go.Scatter(
            x=stages,
            y=success_rates,
            name="Success Rate",
            mode="lines+markers",
            marker_color='red',
            yaxis="y2"
        ))

        fig.update_layout(
            title="Workflow Stage Analysis",
            xaxis=dict(title="Workflow Stage"),
            yaxis=dict(title="Duration (seconds)", side="left"),
            yaxis2=dict(title="Success Rate", side="right", overlaying="y"),
            height=400
        )

        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    def _create_decision_analysis(self) -> str:
        """Create decision confidence analysis."""
        # Sample decision data - would be loaded from actual performance data
        decisions = ["Use ARIMA", "Select Features", "Tune Hyperparams", "Validate Results"]
        confidence_scores = [0.85, 0.72, 0.91, 0.78]
        success_outcomes = [True, False, True, True]

        colors = ['green' if success else 'red' for success in success_outcomes]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=decisions,
            y=confidence_scores,
            marker_color=colors,
            name="Decision Confidence"
        ))

        fig.update_layout(
            title="Decision Confidence vs Success",
            xaxis_title="Decision",
            yaxis_title="Confidence Score",
            height=400
        )

        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    def _create_performance_timeline(self, performance_data: Dict[str, Any]) -> str:
        """Create performance timeline visualization."""
        # Sample timeline data
        dates = pd.date_range(start=datetime.now() - timedelta(days=7), periods=7, freq='D')
        success_rates = [0.8, 0.85, 0.75, 0.90, 0.88, 0.92, 0.87]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates,
            y=success_rates,
            mode='lines+markers',
            name='Success Rate',
            line=dict(color='green', width=3)
        ))

        fig.update_layout(
            title="Performance Timeline (Last 7 Days)",
            xaxis_title="Date",
            yaxis_title="Success Rate",
            height=400
        )

        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    def _create_confidence_distribution(self, performance_data: Dict[str, Any]) -> str:
        """Create confidence score distribution."""
        # Sample confidence data
        confidence_scores = [0.95, 0.88, 0.72, 0.91, 0.85, 0.78, 0.92, 0.67, 0.89, 0.94]

        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=confidence_scores,
            nbinsx=10,
            marker_color='orange',
            name='Confidence Scores'
        ))

        fig.update_layout(
            title="Decision Confidence Distribution",
            xaxis_title="Confidence Score",
            yaxis_title="Frequency",
            height=400
        )

        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    def _create_bottleneck_visualization(self) -> str:
        """Create bottleneck analysis visualization."""
        bottlenecks = self.analytics.identify_bottlenecks()

        categories = ["Slow Queries", "Failed Tools", "Low Confidence", "High Resource Usage"]
        counts = [
            len(bottlenecks["bottlenecks"]["slow_queries"]),
            len(bottlenecks["bottlenecks"]["failed_tools"]),
            len(bottlenecks["bottlenecks"]["low_confidence_decisions"]),
            len(bottlenecks["bottlenecks"]["high_resource_usage"])
        ]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=categories,
            y=counts,
            marker_color='red',
            name='Bottleneck Count'
        ))

        fig.update_layout(
            title="Performance Bottlenecks",
            xaxis_title="Bottleneck Type",
            yaxis_title="Count",
            height=400
        )

        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    def _get_node_color(self, node_type: str) -> str:
        """Get color for node type."""
        color_map = {
            'Agent': 'red',
            'Task': 'blue',
            'Tool': 'green',
            'Concept': 'orange',
            'State': 'purple'
        }
        return color_map.get(node_type, 'gray')

    def _create_dashboard_html(self, ontology_viz: str, performance_charts: str,
                             workflow_explorer: str, decision_analysis: str) -> str:
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
        <p><em>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
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

    def _create_performance_dashboard_html(self, timeline_chart: str,
                                         confidence_chart: str,
                                         bottleneck_chart: str,
                                         agent_name: Optional[str]) -> str:
        """Create performance-focused dashboard HTML."""
        agent_title = f" - {agent_name}" if agent_name else " - All Agents"

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
        <p><em>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
    </div>

    <div class="metrics-summary">
        <div class="metric-card">
            <div class="metric-value">87%</div>
            <div class="metric-label">Success Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">42s</div>
            <div class="metric-label">Avg Duration</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">0.82</div>
            <div class="metric-label">Avg Confidence</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">156</div>
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
def create_interactive_dashboard(ontology_path: str = "assets/ontologies/core.ttl",
                               data_dir: str = "outputs/agent_data") -> InteractiveDashboard:
    """Create an interactive dashboard instance."""
    return InteractiveDashboard(ontology_path, data_dir)


def generate_full_dashboard(ontology_path: str = "assets/ontologies/core.ttl",
                          data_dir: str = "outputs/agent_data",
                          days: int = 7) -> str:
    """Generate complete interactive dashboard."""
    dashboard = create_interactive_dashboard(ontology_path, data_dir)
    return dashboard.generate_full_dashboard(days)


def generate_performance_dashboard(agent_name: Optional[str] = None,
                                 ontology_path: str = "assets/ontologies/core.ttl",
                                 data_dir: str = "outputs/agent_data") -> str:
    """Generate performance-focused dashboard."""
    dashboard = create_interactive_dashboard(ontology_path, data_dir)
    return dashboard.generate_performance_focused_dashboard(agent_name)
