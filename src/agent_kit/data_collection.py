"""
Agent Performance Data Collection System

This module provides comprehensive data collection capabilities for tracking
agent performance in ontology-driven ML workflows. It collects:

1. Execution Metrics: Timing, success rates, resource usage
2. Decision Quality: Confidence scores, accuracy, consistency
3. Ontology Navigation: Query patterns, entity relationships discovered
4. Tool Usage: Which tools are used when, success rates
5. Learning Progress: Performance improvement over time
6. Error Analysis: Failure patterns and recovery strategies

Data is stored in structured format for analysis and visualization.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import psutil
import threading
from contextlib import contextmanager


@dataclass
class ExecutionMetrics:
    """Metrics collected during agent execution."""
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class OntologyQueryMetrics:
    """Metrics for ontology queries performed by agents."""
    query_type: str  # SPARQL, entity_lookup, relationship_query, etc.
    query_text: str
    execution_time_seconds: float
    result_count: int
    entities_discovered: List[str] = field(default_factory=list)
    relationships_found: List[str] = field(default_factory=list)
    cache_hit: bool = False


@dataclass
class ToolUsageMetrics:
    """Metrics for tool usage by agents."""
    tool_name: str
    tool_category: str  # ml_training, visualization, data_processing, etc.
    execution_time_seconds: float
    success: bool
    input_parameters: Dict[str, Any] = field(default_factory=dict)
    output_summary: Optional[str] = None
    error_details: Optional[str] = None


@dataclass
class DecisionMetrics:
    """Metrics for agent decision-making."""
    decision_context: str
    confidence_score: float
    alternatives_considered: int
    final_decision: str
    ontology_entities_used: List[str] = field(default_factory=list)
    tools_consulted: List[str] = field(default_factory=list)
    outcome_success: Optional[bool] = None
    outcome_quality_score: Optional[float] = None


@dataclass
class AgentPerformanceRecord:
    """Complete performance record for an agent execution."""
    agent_name: str
    task_type: str
    task_description: str
    session_id: str
    timestamp: datetime

    # Core metrics
    execution: ExecutionMetrics
    ontology_queries: List[OntologyQueryMetrics] = field(default_factory=list)
    tool_usage: List[ToolUsageMetrics] = field(default_factory=list)
    decisions: List[DecisionMetrics] = field(default_factory=list)

    # Derived metrics (calculated)
    total_query_time: float = 0.0
    total_tool_time: float = 0.0
    average_confidence: float = 0.0
    success_rate: float = 0.0

    # Context
    ontology_version: Optional[str] = None
    agent_version: Optional[str] = None
    environment_info: Dict[str, Any] = field(default_factory=dict)


class AgentDataCollector:
    """
    Collects comprehensive performance data during agent execution.

    Usage:
        collector = AgentDataCollector()

        with collector.track_execution("forecast_agent", "revenue_forecast", session_id):
            # Agent execution code here
            with collector.track_ontology_query("SPARQL", query_text):
                results = ontology.query(query)

            with collector.track_tool_usage("forecast_model"):
                prediction = forecast_tool.predict(data)

            collector.record_decision("Use ARIMA model", 0.85, ["ARIMA", "Prophet"])
    """

    def __init__(self, data_dir: str = "outputs/agent_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.current_record: Optional[AgentPerformanceRecord] = None
        self._lock = threading.Lock()

    @contextmanager
    def track_execution(self, agent_name: str, task_type: str, task_description: str,
                       session_id: Optional[str] = None):
        """
        Context manager to track complete agent execution.

        Args:
            agent_name: Name of the executing agent
            task_type: Type of task (forecast, optimize, analyze, etc.)
            task_description: Detailed task description
            session_id: Optional session identifier (generated if None)
        """
        if session_id is None:
            session_id = f"{agent_name}_{task_type}_{int(time.time())}"

        execution_metrics = ExecutionMetrics(start_time=datetime.now())

        # Start resource monitoring
        process = psutil.Process()
        initial_cpu = process.cpu_percent(interval=None)
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        try:
            self.current_record = AgentPerformanceRecord(
                agent_name=agent_name,
                task_type=task_type,
                task_description=task_description,
                session_id=session_id,
                timestamp=datetime.now(),
                execution=execution_metrics
            )

            yield self.current_record

            # Mark as successful
            self.current_record.execution.success = True

        except Exception as e:
            # Record failure
            self.current_record.execution.success = False
            self.current_record.execution.error_message = str(e)
            raise
        finally:
            # Complete execution metrics
            end_time = datetime.now()
            self.current_record.execution.end_time = end_time
            self.current_record.execution.duration_seconds = (
                end_time - self.current_record.execution.start_time
            ).total_seconds()

            # Resource usage
            final_cpu = process.cpu_percent(interval=None)
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            self.current_record.execution.cpu_usage_percent = final_cpu - initial_cpu
            self.current_record.execution.memory_usage_mb = final_memory - initial_memory

            # Calculate derived metrics
            self._calculate_derived_metrics()

            # Save the record
            self._save_record(self.current_record)

    @contextmanager
    def track_ontology_query(self, query_type: str, query_text: str):
        """
        Context manager to track ontology query execution.

        Args:
            query_type: Type of query (SPARQL, entity_lookup, etc.)
            query_text: The actual query text
        """
        if not self.current_record:
            raise RuntimeError("No active execution record. Use track_execution() first.")

        start_time = time.time()
        query_metrics = OntologyQueryMetrics(
            query_type=query_type,
            query_text=query_text,
            execution_time_seconds=0.0,
            result_count=0
        )

        try:
            yield query_metrics
        finally:
            query_metrics.execution_time_seconds = time.time() - start_time
            self.current_record.ontology_queries.append(query_metrics)

    @contextmanager
    def track_tool_usage(self, tool_name: str, tool_category: str = "general",
                        input_params: Optional[Dict[str, Any]] = None):
        """
        Context manager to track tool usage.

        Args:
            tool_name: Name of the tool being used
            tool_category: Category of tool (ml_training, visualization, etc.)
            input_params: Input parameters passed to the tool
        """
        if not self.current_record:
            raise RuntimeError("No active execution record. Use track_execution() first.")

        start_time = time.time()
        tool_metrics = ToolUsageMetrics(
            tool_name=tool_name,
            tool_category=tool_category,
            execution_time_seconds=0.0,
            success=False,
            input_parameters=input_params or {}
        )

        try:
            yield tool_metrics
            tool_metrics.success = True
        except Exception as e:
            tool_metrics.success = False
            tool_metrics.error_details = str(e)
            raise
        finally:
            tool_metrics.execution_time_seconds = time.time() - start_time
            self.current_record.tool_usage.append(tool_metrics)

    def record_decision(self, decision_context: str, final_decision: str,
                       confidence_score: float, alternatives: Optional[List[str]] = None,
                       ontology_entities: Optional[List[str]] = None,
                       tools_consulted: Optional[List[str]] = None) -> None:
        """
        Record an agent decision with context.

        Args:
            decision_context: Context in which decision was made
            final_decision: The decision that was made
            confidence_score: Agent's confidence in the decision (0-1)
            alternatives: Alternative options considered
            ontology_entities: Ontology entities used in decision
            tools_consulted: Tools consulted for decision
        """
        if not self.current_record:
            raise RuntimeError("No active execution record. Use track_execution() first.")

        decision_metrics = DecisionMetrics(
            decision_context=decision_context,
            confidence_score=confidence_score,
            alternatives_considered=len(alternatives) if alternatives else 0,
            ontology_entities_used=ontology_entities or [],
            tools_consulted=tools_consulted or [],
            final_decision=final_decision
        )

        self.current_record.decisions.append(decision_metrics)

    def update_decision_outcome(self, decision_index: int, success: bool,
                               quality_score: Optional[float] = None) -> None:
        """
        Update the outcome of a previously recorded decision.

        Args:
            decision_index: Index of decision in current record
            success: Whether the decision led to success
            quality_score: Quality score of the outcome (0-1)
        """
        if not self.current_record:
            raise RuntimeError("No active execution record. Use track_execution() first.")

        if 0 <= decision_index < len(self.current_record.decisions):
            self.current_record.decisions[decision_index].outcome_success = success
            self.current_record.decisions[decision_index].outcome_quality_score = quality_score

    def _calculate_derived_metrics(self) -> None:
        """Calculate derived performance metrics."""
        if not self.current_record:
            return

        record = self.current_record

        # Total query time
        record.total_query_time = sum(q.execution_time_seconds for q in record.ontology_queries)

        # Total tool time
        record.total_tool_time = sum(t.execution_time_seconds for t in record.tool_usage)

        # Average confidence
        if record.decisions:
            record.average_confidence = (
                sum(d.confidence_score for d in record.decisions) / len(record.decisions)
            )

        # Success rate (decisions with positive outcomes)
        successful_decisions = [
            d for d in record.decisions
            if d.outcome_success is not None and d.outcome_success
        ]
        if record.decisions:
            record.success_rate = len(successful_decisions) / len(record.decisions)

    def _save_record(self, record: AgentPerformanceRecord) -> None:
        """Save performance record to persistent storage."""
        # Create date-based directory structure
        date_dir = self.data_dir / record.timestamp.strftime("%Y-%m-%d")
        date_dir.mkdir(exist_ok=True)

        # Save as JSON
        filename = f"{record.agent_name}_{record.session_id}.json"
        filepath = date_dir / filename

        # Convert dataclasses to dictionaries for JSON serialization
        record_dict = self._record_to_dict(record)

        with open(filepath, 'w') as f:
            json.dump(record_dict, f, indent=2, default=str)

        # Also save to daily summary file for quick analysis
        self._update_daily_summary(record)

    def _record_to_dict(self, record: AgentPerformanceRecord) -> Dict[str, Any]:
        """Convert performance record to dictionary for JSON serialization."""
        return {
            "agent_name": record.agent_name,
            "task_type": record.task_type,
            "task_description": record.task_description,
            "session_id": record.session_id,
            "timestamp": record.timestamp.isoformat(),

            "execution": {
                "start_time": record.execution.start_time.isoformat(),
                "end_time": record.execution.end_time.isoformat() if record.execution.end_time else None,
                "duration_seconds": record.execution.duration_seconds,
                "cpu_usage_percent": record.execution.cpu_usage_percent,
                "memory_usage_mb": record.execution.memory_usage_mb,
                "success": record.execution.success,
                "error_message": record.execution.error_message,
                "retry_count": record.execution.retry_count
            },

            "ontology_queries": [
                {
                    "query_type": q.query_type,
                    "query_text": q.query_text,
                    "execution_time_seconds": q.execution_time_seconds,
                    "result_count": q.result_count,
                    "entities_discovered": q.entities_discovered,
                    "relationships_found": q.relationships_found,
                    "cache_hit": q.cache_hit
                }
                for q in record.ontology_queries
            ],

            "tool_usage": [
                {
                    "tool_name": t.tool_name,
                    "tool_category": t.tool_category,
                    "execution_time_seconds": t.execution_time_seconds,
                    "success": t.success,
                    "input_parameters": t.input_parameters,
                    "output_summary": t.output_summary,
                    "error_details": t.error_details
                }
                for t in record.tool_usage
            ],

            "decisions": [
                {
                    "decision_context": d.decision_context,
                    "confidence_score": d.confidence_score,
                    "alternatives_considered": d.alternatives_considered,
                    "ontology_entities_used": d.ontology_entities_used,
                    "tools_consulted": d.tools_consulted,
                    "final_decision": d.final_decision,
                    "outcome_success": d.outcome_success,
                    "outcome_quality_score": d.outcome_quality_score
                }
                for d in record.decisions
            ],

            "derived_metrics": {
                "total_query_time": record.total_query_time,
                "total_tool_time": record.total_tool_time,
                "average_confidence": record.average_confidence,
                "success_rate": record.success_rate
            },

            "context": {
                "ontology_version": record.ontology_version,
                "agent_version": record.agent_version,
                "environment_info": record.environment_info
            }
        }

    def _update_daily_summary(self, record: AgentPerformanceRecord) -> None:
        """Update daily performance summary for quick analytics."""
        date_str = record.timestamp.strftime("%Y-%m-%d")
        summary_file = self.data_dir / f"daily_summary_{date_str}.json"

        # Load existing summary or create new one
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                summary = json.load(f)
        else:
            summary = {
                "date": date_str,
                "total_sessions": 0,
                "agent_performance": {},
                "task_distribution": {},
                "success_rates": {},
                "average_durations": {},
                "error_patterns": []
            }

        # Update summary statistics
        summary["total_sessions"] += 1

        # Agent performance
        agent = record.agent_name
        if agent not in summary["agent_performance"]:
            summary["agent_performance"][agent] = {
                "session_count": 0,
                "total_successes": 0,
                "total_duration": 0.0,
                "avg_confidence": 0.0
            }

        agent_stats = summary["agent_performance"][agent]
        agent_stats["session_count"] += 1
        agent_stats["total_successes"] += 1 if record.execution.success else 0
        agent_stats["total_duration"] += record.execution.duration_seconds or 0
        agent_stats["avg_confidence"] = (
            (agent_stats["avg_confidence"] * (agent_stats["session_count"] - 1) +
             record.average_confidence) / agent_stats["session_count"]
        )

        # Task distribution
        task = record.task_type
        summary["task_distribution"][task] = summary["task_distribution"].get(task, 0) + 1

        # Success rates
        summary["success_rates"][agent] = (
            agent_stats["total_successes"] / agent_stats["session_count"]
        )

        # Average durations
        summary["average_durations"][agent] = (
            agent_stats["total_duration"] / agent_stats["session_count"]
        )

        # Error tracking
        if not record.execution.success and record.execution.error_message:
            summary["error_patterns"].append({
                "agent": agent,
                "task": task,
                "error": record.execution.error_message,
                "timestamp": record.timestamp.isoformat()
            })

        # Keep only recent errors (last 10)
        summary["error_patterns"] = summary["error_patterns"][-10:]

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)


class PerformanceAnalytics:
    """
    Analytics engine for analyzing collected performance data.

    Provides insights into agent performance, bottlenecks, and improvement opportunities.
    """

    def __init__(self, data_dir: str = "outputs/agent_data"):
        self.data_dir = Path(data_dir)

    def get_agent_performance_summary(self, agent_name: Optional[str] = None,
                                    days: int = 7) -> Dict[str, Any]:
        """
        Get performance summary for agents over recent days.

        Args:
            agent_name: Specific agent to analyze (None for all)
            days: Number of recent days to analyze

        Returns:
            Performance summary statistics
        """
        summary_files = list(self.data_dir.glob("daily_summary_*.json"))
        summary_files.sort(reverse=True)  # Most recent first

        # Load recent summaries
        summaries = []
        for summary_file in summary_files[:days]:
            try:
                with open(summary_file, 'r') as f:
                    summaries.append(json.load(f))
            except (json.JSONDecodeError, FileNotFoundError):
                continue

        if not summaries:
            return {"error": "No performance data found"}

        # Aggregate statistics
        total_sessions = sum(s.get("total_sessions", 0) for s in summaries)

        # Agent-specific analysis
        agent_performance = {}
        for summary in summaries:
            for agent, stats in summary.get("agent_performance", {}).items():
                if agent_name and agent != agent_name:
                    continue

                if agent not in agent_performance:
                    agent_performance[agent] = {
                        "total_sessions": 0,
                        "total_successes": 0,
                        "total_duration": 0.0,
                        "avg_confidence": 0.0,
                        "success_rate": 0.0
                    }

                agent_stats = agent_performance[agent]
                agent_stats["total_sessions"] += stats["session_count"]
                agent_stats["total_successes"] += stats["total_successes"]
                agent_stats["total_duration"] += stats["total_duration"]
                # Weighted average for confidence
                total_sessions_so_far = agent_stats["total_sessions"] - stats["session_count"]
                agent_stats["avg_confidence"] = (
                    (agent_stats["avg_confidence"] * total_sessions_so_far +
                     stats["avg_confidence"] * stats["session_count"]) /
                    agent_stats["total_sessions"]
                )

        # Calculate final success rates
        for agent_stats in agent_performance.values():
            agent_stats["success_rate"] = (
                agent_stats["total_successes"] / agent_stats["total_sessions"]
                if agent_stats["total_sessions"] > 0 else 0
            )
            agent_stats["avg_duration"] = (
                agent_stats["total_duration"] / agent_stats["total_sessions"]
                if agent_stats["total_sessions"] > 0 else 0
            )

        return {
            "period_days": days,
            "total_sessions": total_sessions,
            "agent_performance": agent_performance,
            "top_performing_agents": sorted(
                agent_performance.items(),
                key=lambda x: x[1]["success_rate"],
                reverse=True
            )[:5]
        }

    def identify_bottlenecks(self) -> Dict[str, Any]:
        """
        Identify performance bottlenecks from collected data.

        Returns:
            Analysis of bottlenecks and recommendations
        """
        # Load recent detailed records
        record_files = list(self.data_dir.glob("*/*.json"))
        record_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        bottlenecks = {
            "slow_queries": [],
            "failed_tools": [],
            "low_confidence_decisions": [],
            "high_resource_usage": []
        }

        for record_file in record_files[:50]:  # Analyze last 50 records
            try:
                with open(record_file, 'r') as f:
                    record_data = json.load(f)

                # Check for slow ontology queries
                for query in record_data.get("ontology_queries", []):
                    if query["execution_time_seconds"] > 5.0:  # >5 seconds
                        bottlenecks["slow_queries"].append({
                            "agent": record_data["agent_name"],
                            "query_type": query["query_type"],
                            "duration": query["execution_time_seconds"],
                            "timestamp": record_data["timestamp"]
                        })

                # Check for failed tools
                for tool in record_data.get("tool_usage", []):
                    if not tool["success"]:
                        bottlenecks["failed_tools"].append({
                            "agent": record_data["agent_name"],
                            "tool": tool["tool_name"],
                            "error": tool["error_details"],
                            "timestamp": record_data["timestamp"]
                        })

                # Check for low confidence decisions
                for decision in record_data.get("decisions", []):
                    if decision["confidence_score"] < 0.5:
                        bottlenecks["low_confidence_decisions"].append({
                            "agent": record_data["agent_name"],
                            "decision": decision["final_decision"],
                            "confidence": decision["confidence_score"],
                            "context": decision["decision_context"],
                            "timestamp": record_data["timestamp"]
                        })

                # Check for high resource usage
                execution = record_data.get("execution", {})
                if execution.get("cpu_usage_percent", 0) > 50 or execution.get("memory_usage_mb", 0) > 500:
                    bottlenecks["high_resource_usage"].append({
                        "agent": record_data["agent_name"],
                        "cpu_percent": execution.get("cpu_usage_percent"),
                        "memory_mb": execution.get("memory_usage_mb"),
                        "duration": execution.get("duration_seconds"),
                        "timestamp": record_data["timestamp"]
                    })

            except (json.JSONDecodeError, FileNotFoundError):
                continue

        # Generate recommendations
        recommendations = []

        if bottlenecks["slow_queries"]:
            recommendations.append(
                "Optimize ontology queries - consider caching frequently accessed patterns"
            )

        if bottlenecks["failed_tools"]:
            recommendations.append(
                "Improve tool reliability - add error handling and fallback mechanisms"
            )

        if bottlenecks["low_confidence_decisions"]:
            recommendations.append(
                "Enhance decision confidence - expand training data or ontology coverage"
            )

        if bottlenecks["high_resource_usage"]:
            recommendations.append(
                "Optimize resource usage - implement batching or async processing"
            )

        return {
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat()
        }


# Convenience functions
def create_data_collector(data_dir: str = "outputs/agent_data") -> AgentDataCollector:
    """Create a new data collector instance."""
    return AgentDataCollector(data_dir)


def create_performance_analytics(data_dir: str = "outputs/agent_data") -> PerformanceAnalytics:
    """Create a new performance analytics instance."""
    return PerformanceAnalytics(data_dir)
