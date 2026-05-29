"""
AgentState — SRP: only holds state for the LangGraph pipeline. Nothing else.
Typed dataclass passed between nodes.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    """Typed state object flowing through the 6-node LangGraph pipeline."""

    # Node 1: Schema Discovery
    schema_description: str = ""
    sources_loaded: list[str] = field(default_factory=list)

    # Node 2: Query Execution (Coral)
    master_results: list[dict] = field(default_factory=list)
    signal_results: dict[str, list[dict]] = field(default_factory=dict)
    cache_stats: dict[str, Any] = field(default_factory=dict)
    query_time_ms: float = 0.0

    # Node 3: Analysis
    analysis: dict[str, Any] = field(default_factory=dict)
    performance_grades: list[Any] = field(default_factory=list) # list[PerformanceGrade]
    layoff_risks: dict[str, Any] = field(default_factory=dict) # dict[str, LayoffRiskProfile]

    # Node 4: Action Generation
    actions: list[dict] = field(default_factory=list)

    # Node 5: Action Execution
    executed_actions: list[Any] = field(default_factory=list)

    # Node 6: Report
    report: str = ""

    # Meta
    errors: list[str] = field(default_factory=list)
    run_id: str = ""
