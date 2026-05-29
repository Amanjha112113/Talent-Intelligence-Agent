"""
main.py — Dependency Injection Root (Composition Root)
This is the ONLY place where concrete classes are instantiated.
All other modules depend on abstractions (interfaces).
DIP: wires everything together here, keeping the rest of the code clean.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import get_settings
from src.coral.cache import CoralCache
from src.coral.schema_registry import SchemaRegistry
from src.coral.source_registry import SourceRegistry
from src.coral.engine import CoralEngine
from src.connectors import (
    GitHubConnector, SlackConnector, CalendarConnector
)
from src.analysis.burnout_analyzer import BurnoutAnalyzer
from src.analysis.risk_scorer import RiskScorer
from src.analysis.performance_grader import PerformanceGrader
from src.analysis.layoff_risk_detector import LayoffRiskDetector
from src.actions.report_generator import ReportGenerator
from src.actions.intervention_drafter import InterventionDrafter
from src.agent.pipeline import AgentPipeline


def build_agent() -> AgentPipeline:
    """
    Composition Root — wire all dependencies together.
    DIP: AgentPipeline never creates its own dependencies.
    """
    cfg = get_settings()

    # ── Layer 1: Coral Infrastructure ────────────────────────────────────────
    cache = CoralCache(ttl_seconds=cfg.coral_cache_ttl_seconds)
    schema_registry = SchemaRegistry()
    source_registry = SourceRegistry()

    # ── Layer 2: Data Connectors (OCP — add new connectors here freely) ───────
    print("\n🔌 Registering data sources with Coral...\n")
    source_registry.register(GitHubConnector())
    source_registry.register(SlackConnector())
    source_registry.register(CalendarConnector())


    # ── Layer 3: Coral Engine ──────────────────────────────────────────────────
    coral = CoralEngine(
        source_registry=source_registry,
        cache=cache,
        schema_registry=schema_registry,
    )

    # ── Layer 4: Analysis (DIP — inject via IAnalyzer interface) ─────────────
    scorer = RiskScorer()
    burnout_analyzer = BurnoutAnalyzer(scorer=scorer)
    layoff_detector = LayoffRiskDetector()
    grader = PerformanceGrader()

    # ── Layer 5: Actions (DIP — inject via IReporter + IActionExecutor) ──────
    reporter = ReportGenerator()
    executor = InterventionDrafter()

    # ── Layer 6: Agent Pipeline (pure DIP — depends on interfaces only) ───────
    return AgentPipeline(
        coral=coral,
        analyzers=[burnout_analyzer, layoff_detector],
        grader=grader,
        reporter=reporter,
        executor=executor,
    )


def main():
    """CLI entry point."""
    print("\n" + "=" * 60)
    print("  🧠 Engineering Talent Intelligence Agent")
    print("  Powered by Coral — 4 sources, 1 SQL query")
    print("=" * 60)

    agent = build_agent()
    state = agent.run()

    # ── Print Report ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  📋 FINAL REPORT")
    print("=" * 60)
    print(state.report)

    # ── Print Action Artifacts ────────────────────────────────────────────────
    if state.executed_actions:
        print("\n" + "=" * 60)
        print("  📨 GENERATED INTERVENTION DRAFTS")
        print("=" * 60)
        for action in state.executed_actions:
            if action.artifact:
                print(f"\n--- {action.action_type.upper()} → {action.target} ---")
                print(action.artifact)
                print()

    # ── Cache Stats ───────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  ⚡ CORAL CACHE PERFORMANCE")
    print("=" * 60)
    for k, v in state.cache_stats.items():
        print(f"  {k}: {v}")

    if state.errors:
        print(f"\n⚠️ Errors encountered: {state.errors}")

    print(f"\n✅ Agent run complete. Query time: {state.query_time_ms:.0f}ms")
    print("  Run 'streamlit run dashboard/app.py' for the visual dashboard.\n")


if __name__ == "__main__":
    main()
