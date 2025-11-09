"""
Task Flow Visualizer for Ontology-Guided Agent Workflows

This module provides visualization capabilities for understanding how agents
navigate through ontology-guided ML workflows. It creates interactive flowcharts
showing:

1. Workflow stage progression with timing and success metrics
2. Ontology navigation paths (which concepts/entities were visited)
3. Decision points with confidence scores and alternatives considered
4. Tool usage patterns and their outcomes
5. Bottleneck identification and optimization opportunities

Visualizations help users understand the "thinking process" of ontology-driven agents.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import graphviz
from graphviz import Digraph
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx

from agent_kit.data_collection import PerformanceAnalytics


@dataclass
class FlowNode:
    """Represents a node in the task flow visualization."""
    id: str
    label: str
    node_type: str  # 'stage', 'decision', 'tool', 'ontology_entity', 'outcome'
    duration: Optional[float] = None
    confidence: Optional[float] = None
    success: Optional[bool] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowEdge:
    """Represents a connection between flow nodes."""
    from_node: str
    to_node: str
    label: str = ""
    weight: float = 1.0
    edge_type: str = "sequence"  # 'sequence', 'decision', 'parallel', 'ontology_link'


class TaskFlowVisualizer:
    """
    Visualizes agent task execution flows with ontology navigation.

    Creates interactive flowcharts showing how agents move through ontology-guided
    workflows, make decisions, and use tools.
    """

    def __init__(self, data_dir: str = "outputs/agent_data",
                 output_dir: str = "outputs/flow_visualizations"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.analytics = PerformanceAnalytics(str(self.data_dir))

    def visualize_workflow_execution(self, session_id: str) -> str:
        """
        Create detailed visualization of a specific workflow execution.

        Args:
            session_id: Session ID of the workflow to visualize

        Returns:
            Path to generated visualization file
        """
        # Load execution data
        execution_data = self._load_execution_data(session_id)
        if not execution_data:
            raise FileNotFoundError(f"No execution data found for session {session_id}")

        # Create flow nodes and edges
        nodes, edges = self._build_flow_graph(execution_data)

        # Generate GraphViz visualization
        return self._generate_graphviz_flow(nodes, edges, session_id)

    def visualize_agent_workflow_pattern(self, agent_name: str,
                                       sessions: int = 10) -> str:
        """
        Visualize common workflow patterns for a specific agent.

        Args:
            agent_name: Name of agent to analyze
            sessions: Number of recent sessions to analyze

        Returns:
            Path to generated pattern visualization
        """
        # Load recent sessions for this agent
        recent_sessions = self._find_recent_sessions(agent_name, sessions)

        # Aggregate workflow patterns
        pattern_data = self._aggregate_workflow_patterns(recent_sessions)

        # Generate pattern visualization
        return self._generate_pattern_visualization(pattern_data, agent_name)

    def visualize_ontology_navigation(self, session_id: str) -> str:
        """
        Visualize how the agent navigated through ontology concepts.

        Args:
            session_id: Session ID to visualize

        Returns:
            Path to ontology navigation visualization
        """
        execution_data = self._load_execution_data(session_id)
        if not execution_data:
            return ""

        # Extract ontology navigation path
        navigation_path = self._extract_ontology_navigation(execution_data)

        # Generate navigation visualization
        return self._generate_navigation_visualization(navigation_path, session_id)

    def create_decision_flow_diagram(self, session_id: str) -> str:
        """
        Create diagram showing decision points and their outcomes.

        Args:
            session_id: Session ID to visualize

        Returns:
            Path to decision flow diagram
        """
        execution_data = self._load_execution_data(session_id)
        if not execution_data:
            return ""

        # Extract decision points
        decisions = execution_data.get("decisions", [])

        # Build decision flow
        nodes, edges = self._build_decision_flow(decisions)

        # Generate decision diagram
        return self._generate_decision_diagram(nodes, edges, session_id)

    def generate_interactive_flow_dashboard(self, session_id: str) -> str:
        """
        Generate interactive HTML dashboard showing multiple flow perspectives.

        Args:
            session_id: Session ID to visualize

        Returns:
            Path to interactive dashboard
        """
        execution_data = self._load_execution_data(session_id)
        if not execution_data:
            raise FileNotFoundError(f"No execution data found for session {session_id}")

        # Create multiple visualizations
        workflow_flow = self.visualize_workflow_execution(session_id)
        ontology_nav = self.visualize_ontology_navigation(session_id)
        decision_flow = self.create_decision_flow_diagram(session_id)

        # Create performance timeline
        performance_timeline = self._create_performance_timeline(execution_data)

        # Generate HTML dashboard
        return self._generate_interactive_dashboard(
            execution_data, workflow_flow, ontology_nav, decision_flow, performance_timeline
        )

    def _load_execution_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load execution data for a specific session."""
        # Search through data directory for the session
        for json_file in self.data_dir.rglob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    if data.get("session_id") == session_id:
                        return data
            except (json.JSONDecodeError, FileNotFoundError):
                continue
        return None

    def _find_recent_sessions(self, agent_name: str, limit: int) -> List[Dict[str, Any]]:
        """Find recent sessions for a specific agent."""
        sessions = []

        # Find all session files
        for json_file in self.data_dir.rglob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    if data.get("agent_name") == agent_name:
                        sessions.append(data)
            except (json.JSONDecodeError, FileNotFoundError):
                continue

        # Sort by timestamp and return most recent
        sessions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return sessions[:limit]

    def _build_flow_graph(self, execution_data: Dict[str, Any]) -> Tuple[List[FlowNode], List[FlowEdge]]:
        """Build flow graph from execution data."""
        nodes = []
        edges = []

        session_id = execution_data.get("session_id", "unknown")

        # Add execution node
        execution = execution_data.get("execution", {})
        exec_node = FlowNode(
            id=f"{session_id}_execution",
            label="Agent Execution",
            node_type="stage",
            duration=execution.get("duration_seconds"),
            success=execution.get("success"),
            metadata={"error": execution.get("error_message")}
        )
        nodes.append(exec_node)

        # Add ontology query nodes
        for i, query in enumerate(execution_data.get("ontology_queries", [])):
            query_node = FlowNode(
                id=f"{session_id}_query_{i}",
                label=f"Query: {query['query_type']}",
                node_type="tool",
                duration=query["execution_time_seconds"],
                metadata={
                    "query_text": query["query_text"][:50] + "...",
                    "result_count": query["result_count"]
                }
            )
            nodes.append(query_node)
            edges.append(FlowEdge(
                from_node=exec_node.id,
                to_node=query_node.id,
                label="executes",
                edge_type="sequence"
            ))

        # Add tool usage nodes
        for i, tool in enumerate(execution_data.get("tool_usage", [])):
            tool_node = FlowNode(
                id=f"{session_id}_tool_{i}",
                label=f"Tool: {tool['tool_name']}",
                node_type="tool",
                duration=tool["execution_time_seconds"],
                success=tool["success"],
                metadata={
                    "category": tool["tool_category"],
                    "error": tool["error_details"]
                }
            )
            nodes.append(tool_node)
            edges.append(FlowEdge(
                from_node=exec_node.id,
                to_node=tool_node.id,
                label="uses",
                edge_type="parallel"
            ))

        # Add decision nodes
        for i, decision in enumerate(execution_data.get("decisions", [])):
            decision_node = FlowNode(
                id=f"{session_id}_decision_{i}",
                label=f"Decision: {decision['final_decision'][:30]}...",
                node_type="decision",
                confidence=decision["confidence_score"],
                success=decision.get("outcome_success"),
                metadata={
                    "context": decision["decision_context"],
                    "alternatives": decision["alternatives_considered"]
                }
            )
            nodes.append(decision_node)
            edges.append(FlowEdge(
                from_node=exec_node.id,
                to_node=decision_node.id,
                label="makes",
                edge_type="sequence"
            ))

        return nodes, edges

    def _generate_graphviz_flow(self, nodes: List[FlowNode],
                               edges: List[FlowEdge], session_id: str) -> str:
        """Generate GraphViz flow visualization."""
        dot = Digraph(comment=f'Workflow Flow - {session_id}')
        dot.attr(rankdir='TB', size='12,8')

        # Define node styles
        node_styles = {
            "stage": {"shape": "box", "style": "filled", "fillcolor": "lightblue"},
            "decision": {"shape": "diamond", "style": "filled", "fillcolor": "lightgreen"},
            "tool": {"shape": "ellipse", "style": "filled", "fillcolor": "lightyellow"},
            "ontology_entity": {"shape": "circle", "style": "filled", "fillcolor": "pink"},
            "outcome": {"shape": "box", "style": "filled", "fillcolor": "lightgray"}
        }

        # Add nodes
        for node in nodes:
            style = node_styles.get(node.node_type, {"shape": "box"})
            label = node.label

            # Add metrics to label
            if node.duration:
                label += ".1f"            if node.confidence:
                label += ".2f"            if node.success is not None:
                label += f"\nSuccess: {node.success}"

            dot.node(node.id, label, **style)

        # Add edges
        for edge in edges:
            dot.edge(edge.from_node, edge.to_node, label=edge.label)

        # Save visualization
        output_path = self.output_dir / f"workflow_flow_{session_id}.gv"
        dot.render(str(output_path.with_suffix('')), format='png', cleanup=True)

        return str(output_path.with_suffix('.png'))

    def _aggregate_workflow_patterns(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate workflow patterns across multiple sessions."""
        patterns = {
            "common_stages": {},
            "decision_patterns": {},
            "tool_usage_patterns": {},
            "ontology_queries": {},
            "success_rates": {},
            "average_durations": {}
        }

        for session in sessions:
            # Aggregate stages
            execution = session.get("execution", {})
            duration = execution.get("duration_seconds", 0)
            success = execution.get("success", False)

            patterns["success_rates"]["overall"] = patterns["success_rates"].get("overall", []) + [success]
            patterns["average_durations"]["overall"] = patterns["average_durations"].get("overall", []) + [duration]

            # Aggregate tool usage
            for tool in session.get("tool_usage", []):
                tool_name = tool["tool_name"]
                if tool_name not in patterns["tool_usage_patterns"]:
                    patterns["tool_usage_patterns"][tool_name] = []
                patterns["tool_usage_patterns"][tool_name].append(tool["execution_time_seconds"])

            # Aggregate decisions
            for decision in session.get("decisions", []):
                confidence = decision["confidence_score"]
                patterns["decision_patterns"]["confidence_scores"] = \
                    patterns["decision_patterns"].get("confidence_scores", []) + [confidence]

        # Calculate averages
        for pattern_type, pattern_data in patterns.items():
            if isinstance(pattern_data, dict):
                for key, values in pattern_data.items():
                    if isinstance(values, list) and values:
                        pattern_data[key] = sum(values) / len(values)

        return patterns

    def _generate_pattern_visualization(self, pattern_data: Dict[str, Any], agent_name: str) -> str:
        """Generate workflow pattern visualization."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Tool Usage Patterns", "Decision Confidence Distribution",
                          "Success Rate Trends", "Duration Distribution"),
            specs=[[{"type": "bar"}, {"type": "histogram"}],
                   [{"type": "scatter"}, {"type": "histogram"}]]
        )

        # Tool usage patterns
        tool_names = list(pattern_data["tool_usage_patterns"].keys())
        tool_times = [pattern_data["tool_usage_patterns"][name] for name in tool_names]

        fig.add_trace(
            go.Bar(x=tool_names, y=tool_times, name="Avg Tool Time"),
            row=1, col=1
        )

        # Decision confidence
        confidence_scores = pattern_data["decision_patterns"].get("confidence_scores", [])
        if confidence_scores:
            fig.add_trace(
                go.Histogram(x=confidence_scores, name="Confidence Scores"),
                row=1, col=2
            )

        # Success rate (simplified - would need time series data)
        success_rate = sum(pattern_data["success_rates"]["overall"]) / len(pattern_data["success_rates"]["overall"])
        fig.add_trace(
            go.Scatter(x=["Current"], y=[success_rate], mode="markers",
                      marker=dict(size=20, color="green"), name="Success Rate"),
            row=2, col=1
        )

        # Duration distribution
        durations = pattern_data["average_durations"]["overall"]
        if durations:
            fig.add_trace(
                go.Histogram(x=durations, name="Execution Times"),
                row=2, col=2
            )

        fig.update_layout(height=800, title_text=f"Workflow Patterns - {agent_name}")
        output_path = self.output_dir / f"patterns_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        fig.write_html(str(output_path))

        return str(output_path)

    def _extract_ontology_navigation(self, execution_data: Dict[str, Any]) -> List[str]:
        """Extract ontology navigation path from execution data."""
        navigation_path = []

        # Add entities discovered through queries
        for query in execution_data.get("ontology_queries", []):
            navigation_path.extend(query.get("entities_discovered", []))

        # Add entities used in decisions
        for decision in execution_data.get("decisions", []):
            navigation_path.extend(decision.get("ontology_entities_used", []))

        # Remove duplicates while preserving order
        seen = set()
        unique_path = []
        for entity in navigation_path:
            if entity not in seen:
                seen.add(entity)
                unique_path.append(entity)

        return unique_path

    def _generate_navigation_visualization(self, navigation_path: List[str], session_id: str) -> str:
        """Generate ontology navigation visualization."""
        if not navigation_path:
            return ""

        # Create simple linear navigation visualization
        fig = go.Figure()

        # Add nodes
        for i, entity in enumerate(navigation_path):
            fig.add_trace(go.Scatter(
                x=[i], y=[0],
                mode='markers+text',
                marker=dict(size=30, color=i, colorscale='Viridis'),
                text=[entity],
                textposition="bottom center",
                name=entity,
                showlegend=False
            ))

        # Add connecting lines
        if len(navigation_path) > 1:
            for i in range(len(navigation_path) - 1):
                fig.add_trace(go.Scatter(
                    x=[i, i+1], y=[0, 0],
                    mode='lines',
                    line=dict(width=3, color='gray'),
                    showlegend=False
                ))

        fig.update_layout(
            title=f"Ontology Navigation Path - {session_id}",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=400
        )

        output_path = self.output_dir / f"ontology_nav_{session_id}.html"
        fig.write_html(str(output_path))

        return str(output_path)

    def _build_decision_flow(self, decisions: List[Dict[str, Any]]) -> Tuple[List[FlowNode], List[FlowEdge]]:
        """Build decision flow graph."""
        nodes = []
        edges = []

        for i, decision in enumerate(decisions):
            # Decision node
            decision_node = FlowNode(
                id=f"decision_{i}",
                label=f"Decision {i+1}",
                node_type="decision",
                confidence=decision["confidence_score"],
                success=decision.get("outcome_success"),
                metadata={
                    "decision": decision["final_decision"],
                    "context": decision["decision_context"]
                }
            )
            nodes.append(decision_node)

            # Alternative nodes
            for j, alt in enumerate(decision.get("alternatives_considered", [])):
                alt_node = FlowNode(
                    id=f"decision_{i}_alt_{j}",
                    label=f"Alt: {alt[:20]}...",
                    node_type="outcome",
                    metadata={"alternative": alt}
                )
                nodes.append(alt_node)

                # Edge from decision to alternative (not chosen)
                edges.append(FlowEdge(
                    from_node=decision_node.id,
                    to_node=alt_node.id,
                    label="considered",
                    edge_type="decision",
                    weight=0.3
                ))

            # Chosen outcome
            chosen_node = FlowNode(
                id=f"decision_{i}_chosen",
                label=f"Chosen: {decision['final_decision'][:25]}...",
                node_type="outcome",
                success=decision.get("outcome_success"),
                metadata={"chosen": True}
            )
            nodes.append(chosen_node)

            edges.append(FlowEdge(
                from_node=decision_node.id,
                to_node=chosen_node.id,
                label="selected",
                edge_type="decision",
                weight=1.0
            ))

        return nodes, edges

    def _generate_decision_diagram(self, nodes: List[FlowNode],
                                  edges: List[FlowEdge], session_id: str) -> str:
        """Generate decision flow diagram."""
        dot = Digraph(comment=f'Decision Flow - {session_id}')
        dot.attr(rankdir='TB')

        for node in nodes:
            style = {"shape": "diamond" if node.node_type == "decision" else "box"}
            label = node.label

            if node.confidence:
                label += ".2f"
            if node.success is not None:
                color = "lightgreen" if node.success else "lightcoral"
                style["fillcolor"] = color
                style["style"] = "filled"

            dot.node(node.id, label, **style)

        for edge in edges:
            color = "red" if edge.weight < 1.0 else "black"
            dot.edge(edge.from_node, edge.to_node, label=edge.label, color=color)

        output_path = self.output_dir / f"decision_flow_{session_id}.gv"
        dot.render(str(output_path.with_suffix('')), format='png', cleanup=True)

        return str(output_path.with_suffix('.png'))

    def _create_performance_timeline(self, execution_data: Dict[str, Any]) -> str:
        """Create performance timeline for dashboard."""
        # Extract timing data from execution
        execution = execution_data.get("execution", {})
        duration = execution.get("duration_seconds", 0)

        # Create simple timeline
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=["Start", "End"],
            y=[0, duration],
            mode='lines+markers',
            name='Execution Timeline'
        ))

        fig.update_layout(
            title="Execution Timeline",
            xaxis_title="Phase",
            yaxis_title="Time (seconds)",
            height=300
        )

        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    def _generate_interactive_dashboard(self, execution_data: Dict[str, Any],
                                      workflow_flow: str, ontology_nav: str,
                                      decision_flow: str, performance_timeline: str) -> str:
        """Generate interactive flow dashboard."""
        session_id = execution_data.get("session_id", "unknown")
        agent_name = execution_data.get("agent_name", "Unknown Agent")

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Flow Dashboard - {session_id}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .dashboard-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .chart-container {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .full-width {{ grid-column: 1 / -1; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 20px; }}
        .metric {{ background: #f0f0f0; padding: 10px; border-radius: 5px; text-align: center; }}
        .metric-value {{ font-size: 1.5em; font-weight: bold; }}
        .tabs {{ display: flex; margin-bottom: 20px; }}
        .tab {{ padding: 10px 20px; background: #ddd; border: none; cursor: pointer; margin-right: 5px; }}
        .tab.active {{ background: #007acc; color: white; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Task Flow Dashboard</h1>
        <h2>{agent_name} - Session {session_id}</h2>
        <p>Interactive exploration of agent workflow execution</p>
    </div>

    <div class="metrics">
        <div class="metric">
            <div class="metric-value">{execution_data.get('execution', {}).get('duration_seconds', 0):.1f}s</div>
            <div>Total Duration</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(execution_data.get('decisions', []))}</div>
            <div>Decisions Made</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(execution_data.get('tool_usage', []))}</div>
            <div>Tools Used</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(execution_data.get('ontology_queries', []))}</div>
            <div>Ontology Queries</div>
        </div>
    </div>

    <div class="tabs">
        <button class="tab active" onclick="showTab('overview')">Overview</button>
        <button class="tab" onclick="showTab('workflow')">Workflow Flow</button>
        <button class="tab" onclick="showTab('ontology')">Ontology Navigation</button>
        <button class="tab" onclick="showTab('decisions')">Decision Flow</button>
    </div>

    <div id="overview" class="tab-content active">
        <div class="dashboard-grid">
            <div class="chart-container">
                <h3>Performance Timeline</h3>
                {performance_timeline}
            </div>
            <div class="chart-container">
                <h3>Execution Summary</h3>
                <p><strong>Task:</strong> {execution_data.get('task_description', 'N/A')}</p>
                <p><strong>Success:</strong> {'Yes' if execution_data.get('execution', {}).get('success') else 'No'}</p>
                <p><strong>Average Confidence:</strong> {execution_data.get('derived_metrics', {}).get('average_confidence', 0):.2f}</p>
            </div>
        </div>
    </div>

    <div id="workflow" class="tab-content">
        <div class="chart-container full-width">
            <h3>Workflow Execution Flow</h3>
            <img src="{workflow_flow}" alt="Workflow Flow" style="max-width: 100%;">
        </div>
    </div>

    <div id="ontology" class="tab-content">
        <div class="chart-container full-width">
            <h3>Ontology Navigation Path</h3>
            <iframe src="{ontology_nav}" width="100%" height="400" frameborder="0"></iframe>
        </div>
    </div>

    <div id="decisions" class="tab-content">
        <div class="chart-container full-width">
            <h3>Decision Flow Diagram</h3>
            <img src="{decision_flow}" alt="Decision Flow" style="max-width: 100%;">
        </div>
    </div>

    <script>
        function showTab(tabName) {{
            const contents = document.querySelectorAll('.tab-content');
            contents.forEach(content => content.classList.remove('active'));
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => tab.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>
        """

        output_path = self.output_dir / f"flow_dashboard_{session_id}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(output_path)


# Convenience functions
def create_task_flow_visualizer(data_dir: str = "outputs/agent_data") -> TaskFlowVisualizer:
    """Create a task flow visualizer instance."""
    return TaskFlowVisualizer(data_dir)


def visualize_workflow_flow(session_id: str, data_dir: str = "outputs/agent_data") -> str:
    """Create workflow flow visualization for a session."""
    visualizer = create_task_flow_visualizer(data_dir)
    return visualizer.visualize_workflow_execution(session_id)


def generate_interactive_flow_dashboard(session_id: str,
                                       data_dir: str = "outputs/agent_data") -> str:
    """Generate interactive flow dashboard for a session."""
    visualizer = create_task_flow_visualizer(data_dir)
    return visualizer.generate_interactive_flow_dashboard(session_id)
