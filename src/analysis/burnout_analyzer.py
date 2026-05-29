"""
BurnoutAnalyzer — SRP: only responsible for analyzing burnout patterns.
Implements IAnalyzer (DIP). Uses RiskScorer internally (composition over inheritance).
"""

from typing import Any
from src.core.interfaces import IAnalyzer
from src.analysis.risk_scorer import RiskScorer, RiskProfile, RiskLevel


class BurnoutAnalyzer(IAnalyzer):
    """
    Analyzes raw Coral query results to produce burnout risk profiles.
    DIP: depends on IAnalyzer interface. Injected into the agent pipeline.
    """

    def __init__(self, scorer: RiskScorer | None = None):
        self._scorer = scorer or RiskScorer()

    def get_analysis_name(self) -> str:
        return "Burnout Risk Analysis"

    def analyze(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze Coral query results and return structured burnout analysis.

        Args:
            data: {"master_results": [...rows...]}
        Returns:
            {"profiles": [...], "summary": {...}, "high_risk": [...]}
        """
        rows = data.get("master_results", [])
        profiles = self._scorer.score_all(rows)

        high_risk = [p for p in profiles if p.risk_level == RiskLevel.HIGH]
        medium_risk = [p for p in profiles if p.risk_level == RiskLevel.MEDIUM]
        low_risk = [p for p in profiles if p.risk_level == RiskLevel.LOW]

        return {
            "profiles": profiles,
            "high_risk": high_risk,
            "medium_risk": medium_risk,
            "low_risk": low_risk,
            "summary": {
                "total_engineers": len(profiles),
                "high_risk_count": len(high_risk),
                "medium_risk_count": len(medium_risk),
                "low_risk_count": len(low_risk),
                "avg_risk_score": round(
                    sum(p.burnout_risk_score for p in profiles) / len(profiles), 1
                ) if profiles else 0,
                "most_at_risk": profiles[0].engineer_name if profiles else "None",
                "top_signal": self._top_signal_across_team(profiles),
            },
        }

    # ── Private ───────────────────────────────────────────────────────────────

    def _top_signal_across_team(self, profiles: list[RiskProfile]) -> str:
        """Find the most common dominant signal across all engineers."""
        if not profiles:
            return "None"
        signal_counts: dict[str, int] = {}
        for p in profiles:
            signal_counts[p.dominant_signal] = signal_counts.get(p.dominant_signal, 0) + 1
        return max(signal_counts, key=signal_counts.get)
