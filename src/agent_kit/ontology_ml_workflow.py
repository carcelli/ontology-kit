"""
Ontology-Driven Machine Learning Workflow Breakdown

This module provides a comprehensive breakdown of how agents use ontologies
to navigate machine learning tasks. It includes:

1. Workflow decomposition into clear stages
2. Data collection for agent performance tracking
3. Visualization of ontology navigation paths
4. Metrics for measuring agent effectiveness
5. Learning analytics for continuous improvement

Key Components:
- Ontology Navigation: How agents traverse semantic spaces
- Task Decomposition: Breaking ML problems into ontology-aligned subtasks
- Decision Tracking: Recording agent choices and their outcomes
- Performance Analytics: Measuring success across different task types
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os
from pathlib import Path

from agent_kit.ontology.loader import OntologyLoader
from agent_kit.tools.hyperdim_viz import generate_hyperdim_viz


@dataclass
class WorkflowStage:
    """Represents a stage in the ontology-ML workflow."""
    name: str
    description: str
    ontology_entities: List[str]
    required_tools: List[str]
    expected_outputs: List[str]
    success_metrics: List[str]
    duration_estimate: float  # in seconds


@dataclass
class AgentDecision:
    """Tracks individual agent decisions during workflow execution."""
    timestamp: datetime
    agent_name: str
    task_context: str
    ontology_query: str
    decision_made: str
    confidence_score: float
    outcome: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    """Complete execution record of an ontology-ML workflow."""
    workflow_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    stages: List[WorkflowStage] = field(default_factory=list)
    decisions: List[AgentDecision] = field(default_factory=list)
    final_outcome: Optional[str] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)


class OntologyMLWorkflowAnalyzer:
    """
    Analyzes and breaks down ontology-driven ML workflows.

    Provides tools for:
    - Decomposing workflows into understandable stages
    - Tracking agent decisions and performance
    - Generating visualizations of navigation paths
    - Collecting data for continuous improvement
    """

    def __init__(self, ontology_path: str = "assets/ontologies/core.ttl"):
        self.ontology = OntologyLoader(ontology_path).load()
        self.workflows: Dict[str, WorkflowExecution] = {}
        self.decision_log: List[AgentDecision] = []
        self.data_dir = Path("outputs/workflow_data")
        self.data_dir.mkdir(exist_ok=True)

    def define_workflow_stages(self) -> List[WorkflowStage]:
        """
        Define the standard stages of ontology-driven ML workflows.

        Returns:
            List of workflow stages with their requirements and metrics.
        """
        return [
            WorkflowStage(
                name="Ontology Loading & Validation",
                description="Load and validate ontology structure for ML task alignment",
                ontology_entities=["Ontology", "Agent", "Task", "Tool"],
                required_tools=["OntologyLoader", "SPARQLValidator"],
                expected_outputs=["ValidatedOntology", "EntityMappings"],
                success_metrics=["LoadTime", "ValidationErrors", "EntityCoverage"],
                duration_estimate=5.0
            ),
            WorkflowStage(
                name="Task Semantic Analysis",
                description="Analyze ML task requirements against ontology concepts",
                ontology_entities=["Task", "Concept", "similarTo"],
                required_tools=["SemanticAnalyzer", "EmbeddingComparator"],
                expected_outputs=["TaskEmbedding", "ConceptSimilarities", "NavigationPath"],
                success_metrics=["SemanticMatchScore", "ConceptCoverage", "PathEfficiency"],
                duration_estimate=15.0
            ),
            WorkflowStage(
                name="Tool Discovery & Selection",
                description="Find appropriate ML tools using ontology relationships",
                ontology_entities=["Tool", "requiresTool", "hasCapability"],
                required_tools=["ToolDiscovery", "CapabilityMatcher"],
                expected_outputs=["SelectedTools", "ToolCapabilities", "ExecutionPlan"],
                success_metrics=["ToolMatchAccuracy", "CapabilityCoverage", "SelectionTime"],
                duration_estimate=10.0
            ),
            WorkflowStage(
                name="Hyperdimensional Navigation",
                description="Navigate vector space using ontology-guided decisions",
                ontology_entities=["State", "navigatesTo", "transitionsTo"],
                required_tools=["VectorNavigator", "StateTracker"],
                expected_outputs=["NavigationPath", "StateTransitions", "DecisionConfidence"],
                success_metrics=["NavigationAccuracy", "PathOptimality", "DecisionSpeed"],
                duration_estimate=25.0
            ),
            WorkflowStage(
                name="ML Model Execution",
                description="Execute ML operations with ontology validation",
                ontology_entities=["Action", "executesAction", "accomplishes"],
                required_tools=["MLExecutor", "ResultValidator"],
                expected_outputs=["ModelOutputs", "PerformanceMetrics", "ValidationResults"],
                success_metrics=["ExecutionSuccess", "OutputQuality", "ValidationScore"],
                duration_estimate=60.0
            ),
            WorkflowStage(
                name="Result Integration & Learning",
                description="Integrate results back into ontology and learn from outcomes",
                ontology_entities=["Insight", "derivedFrom", "informs"],
                required_tools=["ResultIntegrator", "LearningUpdater"],
                expected_outputs=["UpdatedOntology", "LearnedPatterns", "PerformanceInsights"],
                success_metrics=["IntegrationAccuracy", "LearningEffectiveness", "PatternQuality"],
                duration_estimate=20.0
            )
        ]

    def start_workflow_tracking(self, workflow_id: str, task_description: str) -> WorkflowExecution:
        """
        Start tracking a new workflow execution.

        Args:
            workflow_id: Unique identifier for the workflow
            task_description: Description of the ML task being performed

        Returns:
            WorkflowExecution object for tracking
        """
        workflow = WorkflowExecution(
            workflow_id=workflow_id,
            start_time=datetime.now(),
            stages=self.define_workflow_stages()
        )

        # Add initial decision for workflow start
        initial_decision = AgentDecision(
            timestamp=datetime.now(),
            agent_name="WorkflowManager",
            task_context=task_description,
            ontology_query="SELECT DISTINCT ?task WHERE { ?task a :Task }",
            decision_made=f"Started workflow for: {task_description}",
            confidence_score=1.0,
            metadata={"workflow_id": workflow_id, "stage": "initialization"}
        )

        workflow.decisions.append(initial_decision)
        self.workflows[workflow_id] = workflow
        self.decision_log.append(initial_decision)

        return workflow

    def record_decision(self, workflow_id: str, decision: AgentDecision) -> None:
        """
        Record an agent decision during workflow execution.

        Args:
            workflow_id: ID of the active workflow
            decision: Decision details to record
        """
        if workflow_id in self.workflows:
            self.workflows[workflow_id].decisions.append(decision)
            self.decision_log.append(decision)

            # Save decision to file for persistence
            self._save_decision(decision)

    def complete_workflow(self, workflow_id: str, outcome: str, metrics: Dict[str, float]) -> None:
        """
        Mark a workflow as completed and record final metrics.

        Args:
            workflow_id: ID of the completed workflow
            outcome: Description of the final outcome
            metrics: Performance metrics from the workflow
        """
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            workflow.end_time = datetime.now()
            workflow.final_outcome = outcome
            workflow.performance_metrics = metrics

            # Save complete workflow data
            self._save_workflow(workflow)

    def generate_workflow_visualization(self, workflow_id: str) -> str:
        """
        Generate visualization of workflow execution path.

        Args:
            workflow_id: ID of workflow to visualize

        Returns:
            Path to generated visualization file
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.workflows[workflow_id]

        # Extract key terms for visualization
        terms = []
        for decision in workflow.decisions:
            # Extract ontology entities from queries
            if "SELECT" in decision.ontology_query:
                # Simple extraction - could be more sophisticated
                terms.extend([decision.task_context, decision.decision_made])

        # Add stage names
        terms.extend([stage.name for stage in workflow.stages])

        # Remove duplicates and limit size
        terms = list(set(terms))[:20]

        # Generate visualization
        output_file = f"outputs/workflow_{workflow_id}_viz.png"
        return generate_hyperdim_viz(
            terms=terms,
            n_components=2,
            output_file=output_file
        )

    def analyze_agent_performance(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze agent performance across all tracked workflows.

        Args:
            agent_name: Optional filter for specific agent

        Returns:
            Performance analysis results
        """
        decisions = self.decision_log
        if agent_name:
            decisions = [d for d in decisions if d.agent_name == agent_name]

        if not decisions:
            return {"error": "No decisions found for analysis"}

        # Calculate performance metrics
        total_decisions = len(decisions)
        avg_confidence = sum(d.confidence_score for d in decisions) / total_decisions

        successful_decisions = [d for d in decisions if d.outcome == "success"]
        success_rate = len(successful_decisions) / total_decisions if total_decisions > 0 else 0

        avg_execution_time = (
            sum(d.execution_time for d in decisions if d.execution_time) /
            len([d for d in decisions if d.execution_time])
        ) if any(d.execution_time for d in decisions) else None

        # Group by task context
        task_performance = {}
        for decision in decisions:
            task = decision.task_context
            if task not in task_performance:
                task_performance[task] = []
            task_performance[task].append(decision.confidence_score)

        return {
            "total_decisions": total_decisions,
            "average_confidence": avg_confidence,
            "success_rate": success_rate,
            "average_execution_time": avg_execution_time,
            "task_performance": {
                task: {
                    "count": len(scores),
                    "avg_confidence": sum(scores) / len(scores)
                }
                for task, scores in task_performance.items()
            },
            "recent_trends": self._calculate_recent_trends(decisions)
        }

    def _calculate_recent_trends(self, decisions: List[AgentDecision]) -> Dict[str, Any]:
        """Calculate performance trends over recent decisions."""
        if len(decisions) < 10:
            return {"insufficient_data": True}

        # Sort by timestamp
        sorted_decisions = sorted(decisions, key=lambda d: d.timestamp)

        # Split into recent and older
        midpoint = len(sorted_decisions) // 2
        recent = sorted_decisions[midpoint:]
        older = sorted_decisions[:midpoint]

        recent_avg = sum(d.confidence_score for d in recent) / len(recent)
        older_avg = sum(d.confidence_score for d in older) / len(older)

        return {
            "recent_avg_confidence": recent_avg,
            "older_avg_confidence": older_avg,
            "confidence_trend": recent_avg - older_avg,
            "trend_direction": "improving" if recent_avg > older_avg else "declining"
        }

    def _save_decision(self, decision: AgentDecision) -> None:
        """Save decision to persistent storage."""
        decision_file = self.data_dir / f"decisions_{decision.timestamp.date()}.jsonl"

        with open(decision_file, 'a') as f:
            json.dump({
                "timestamp": decision.timestamp.isoformat(),
                "agent_name": decision.agent_name,
                "task_context": decision.task_context,
                "ontology_query": decision.ontology_query,
                "decision_made": decision.decision_made,
                "confidence_score": decision.confidence_score,
                "outcome": decision.outcome,
                "execution_time": decision.execution_time,
                "metadata": decision.metadata
            }, f)
            f.write('\n')

    def _save_workflow(self, workflow: WorkflowExecution) -> None:
        """Save complete workflow to persistent storage."""
        workflow_file = self.data_dir / f"workflow_{workflow.workflow_id}.json"

        workflow_data = {
            "workflow_id": workflow.workflow_id,
            "start_time": workflow.start_time.isoformat(),
            "end_time": workflow.end_time.isoformat() if workflow.end_time else None,
            "final_outcome": workflow.final_outcome,
            "performance_metrics": workflow.performance_metrics,
            "stages_completed": len(workflow.stages),
            "decisions_made": len(workflow.decisions),
            "duration_seconds": (
                (workflow.end_time - workflow.start_time).total_seconds()
                if workflow.end_time else None
            )
        }

        with open(workflow_file, 'w') as f:
            json.dump(workflow_data, f, indent=2)

    def generate_learning_report(self) -> str:
        """
        Generate a comprehensive learning report from collected data.

        Returns:
            Path to generated report file
        """
        report_path = self.data_dir / f"learning_report_{datetime.now().date()}.md"

        performance_data = self.analyze_agent_performance()

        report_content = f"""# Ontology-ML Agent Learning Report
Generated: {datetime.now().isoformat()}

## Overall Performance Metrics
- Total Decisions Tracked: {performance_data.get('total_decisions', 0)}
- Average Confidence Score: {performance_data.get('average_confidence', 0):.3f}
- Success Rate: {performance_data.get('success_rate', 0):.1%}
- Average Execution Time: {performance_data.get('average_execution_time', 'N/A')}

## Task Performance Breakdown
"""

        for task, metrics in performance_data.get('task_performance', {}).items():
            report_content += f"### {task}\n"
            report_content += f"- Decisions: {metrics['count']}\n"
            report_content += f"- Average Confidence: {metrics['avg_confidence']:.3f}\n\n"

        trends = performance_data.get('recent_trends', {})
        if not trends.get('insufficient_data'):
            report_content += f"""## Performance Trends
- Recent Average Confidence: {trends.get('recent_avg_confidence', 0):.3f}
- Older Average Confidence: {trends.get('older_avg_confidence', 0):.3f}
- Trend: {trends.get('trend_direction', 'unknown').title()}

## Recommendations
"""

            if trends.get('confidence_trend', 0) > 0.1:
                report_content += "- Agent performance is improving - continue current learning patterns\n"
            elif trends.get('confidence_trend', 0) < -0.1:
                report_content += "- Agent performance is declining - review recent changes\n"
            else:
                report_content += "- Agent performance is stable - consider introducing new challenges\n"

        with open(report_path, 'w') as f:
            f.write(report_content)

        return str(report_path)


# Convenience functions for easy access
def create_workflow_analyzer(ontology_path: str = "assets/ontologies/core.ttl") -> OntologyMLWorkflowAnalyzer:
    """Create a new workflow analyzer instance."""
    return OntologyMLWorkflowAnalyzer(ontology_path)


def start_tracking_workflow(analyzer: OntologyMLWorkflowAnalyzer, workflow_id: str, task: str) -> WorkflowExecution:
    """Start tracking a new workflow."""
    return analyzer.start_workflow_tracking(workflow_id, task)


def record_agent_decision(analyzer: OntologyMLWorkflowAnalyzer, workflow_id: str,
                         agent_name: str, task_context: str, ontology_query: str,
                         decision: str, confidence: float) -> None:
    """Record an agent decision."""
    decision_obj = AgentDecision(
        timestamp=datetime.now(),
        agent_name=agent_name,
        task_context=task_context,
        ontology_query=ontology_query,
        decision_made=decision,
        confidence_score=confidence
    )
    analyzer.record_decision(workflow_id, decision_obj)


def generate_performance_report(analyzer: OntologyMLWorkflowAnalyzer) -> str:
    """Generate a performance analysis report."""
    return analyzer.generate_learning_report()
