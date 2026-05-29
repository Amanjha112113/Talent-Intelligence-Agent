"""
AgentPipeline — Dependency Inversion Principle (DIP)
The pipeline depends on abstractions (IAnalyzer, IReporter, IActionExecutor),
not on concrete implementations. All dependencies injected via constructor.

6-node pipeline:
  Node 1: schema_node      → Coral schema discovery
  Node 2: query_node       → Coral cross-source SQL execution
  Node 3: analysis_node    → Burnout risk analysis
  Node 4: action_gen_node  → Generate intervention actions
  Node 5: action_exec_node → Execute/draft actions
  Node 6: report_node      → Generate final report
"""

import time
import uuid
from typing import Any

from src.agent.state import AgentState
from src.coral.engine import CoralEngine
from src.core.interfaces import IAnalyzer, IReporter, IActionExecutor, IGrader
from src.queries.burnout_queries import BurnoutQueries
from src.queries.performance_queries import PerformanceQueries
from src.analysis.risk_scorer import RiskLevel


class AgentPipeline:
    """
    6-node agent pipeline for burnout detection.
    DIP: all dependencies are injected, not instantiated internally.
    """

    def __init__(
        self,
        coral: CoralEngine,
        analyzers: list[IAnalyzer],
        grader: IGrader,
        reporter: IReporter,
        executor: IActionExecutor,
    ):
        self._coral = coral
        self._analyzers = analyzers
        self._grader = grader
        self._reporter = reporter
        self._executor = executor

    def run(self) -> AgentState:
        """Execute the full 6-node pipeline and return final state."""
        state = AgentState(run_id=str(uuid.uuid4())[:8])

        print(f"\n{'='*60}")
        print(f"  🧠 Talent Intelligence Agent — Run {state.run_id}")
        print(f"{'='*60}\n")

        state = self._node_schema_discovery(state)
        state = self._node_query_execution(state)
        state = self._node_analysis(state)
        state = self._node_action_generation(state)
        state = self._node_action_execution(state)
        state = self._node_report(state)

        return state

    # ── Node 1: Schema Discovery ──────────────────────────────────────────────

    def _node_schema_discovery(self, state: AgentState) -> AgentState:
        print("📡 Node 1: Schema Discovery (Coral)")
        print("  Coral is auto-learning schema from all 3 data sources...\n")
        try:
            state.schema_description = self._coral.discover_schema()
            print(f"\n{state.schema_description}")
        except Exception as e:
            state.errors.append(f"Schema discovery failed: {e}")
        return state

    # ── Node 2: Coral Query Execution ─────────────────────────────────────────

    def _node_query_execution(self, state: AgentState) -> AgentState:
        print("\n🔍 Node 2: Cross-Source Query Execution (Coral)\n")
        print("  Running master burnout query across GitHub + Slack + Calendar...")

        # Pre-load all sources into memory so API fetch latency is not 
        # counted towards Coral SQL execution time.
        self._coral._load_all_sources()

        start = time.perf_counter()
        try:
            state.master_results = self._coral.query(BurnoutQueries.MASTER_BURNOUT_QUERY)

            # Run individual signal queries for drill-down
            print("  Running individual signal queries...")
            state.signal_results = {
                "late_commits": self._coral.query(BurnoutQueries.LATE_NIGHT_COMMITS),
                "slack": self._coral.query(BurnoutQueries.SLACK_ENGAGEMENT_DECAY),
                "meetings": self._coral.query(BurnoutQueries.MEETING_OVERLOAD),
            }

            # Run performance grade query
            perf_rows = self._coral.query(PerformanceQueries.PERFORMANCE_GRADE_QUERY)
            state.performance_grades = self._grader.grade_all(perf_rows)

            state.query_time_ms = (time.perf_counter() - start) * 1000
            state.cache_stats = self._coral.get_cache_stats()
            print(f"\n  ✅ All queries complete in {state.query_time_ms:.0f}ms")
            print(f"  📊 {len(state.master_results)} engineers analyzed")
            print(f"  🏆 Performance graded for {len(state.performance_grades)} engineers")

        except Exception as e:
            state.errors.append(f"Query execution failed: {e}")
            print(f"  ❌ Error: {e}")

        return state

    # ── Node 3: Analysis ──────────────────────────────────────────────────────

    def _node_analysis(self, state: AgentState) -> AgentState:
        print("\n🧮 Node 3: Multi-dimensional Analysis\n")
        try:
            # Prepare common data bag for analyzers
            data = {
                "master_results": state.master_results,
                "performance_grades": state.performance_grades,
            }
            
            for analyzer in self._analyzers:
                print(f"  Running {analyzer.get_analysis_name()}...")
                result = analyzer.analyze(data)
                
                # Merge results based on analyzer type
                if analyzer.get_analysis_name() == "Burnout Risk Analysis":
                    state.analysis.update(result)
                elif analyzer.get_analysis_name() == "Layoff Risk Detection":
                    state.layoff_risks = result

            summary = state.analysis.get("summary", {})
            print(f"\n  ✅ Analysis complete:")
            print(f"     🔴 High Burnout Risk: {summary.get('high_risk_count', 0)}")
            print(f"     🦸 Silent Heroes: {sum(1 for r in state.layoff_risks.values() if r.is_silent_hero)}")
            print(f"     ⚠️  Overrated: {sum(1 for r in state.layoff_risks.values() if r.is_overrated)}")
        except Exception as e:
            state.errors.append(f"Analysis failed: {e}")
            print(f"  ❌ Error: {e}")
        return state

    # ── Node 4: Action Generation ─────────────────────────────────────────────

    def _node_action_generation(self, state: AgentState) -> AgentState:
        print("\n⚡ Node 4: Generating Intervention Actions\n")
        high_risk = state.analysis.get("high_risk", [])
        medium_risk = state.analysis.get("medium_risk", [])

        actions = []
        for profile in high_risk:
            actions.append({"type": "draft_manager_alert", "profile": profile})
            actions.append({"type": "draft_slack_message", "profile": profile})

        for profile in medium_risk:
            actions.append({"type": "draft_hr_brief", "profile": profile})

        state.actions = actions
        print(f"  ✅ {len(actions)} interventions generated")
        return state

    # ── Node 5: Action Execution ──────────────────────────────────────────────

    def _node_action_execution(self, state: AgentState) -> AgentState:
        print("\n🚀 Node 5: Executing Actions\n")
        results = []
        for action in state.actions:
            if self._executor.can_execute(action["type"]):
                result = self._executor.execute(action)
                results.append(result)
                status = "✅" if result.success else "❌"
                print(f"  {status} [{result.action_type}] → {result.target}")

        state.executed_actions = results
        print(f"\n  Total actions executed: {len(results)}")
        return state

    # ── Node 6: Report Generation ─────────────────────────────────────────────

    def _node_report(self, state: AgentState) -> AgentState:
        print("\n📋 Node 6: Generating Report\n")
        try:
            state.report = self._reporter.generate(state.analysis)
            print("  ✅ Report generated successfully")
        except Exception as e:
            state.errors.append(f"Report generation failed: {e}")
            print(f"  ❌ Error: {e}")
        return state
