"""
RiskScorer — SRP: only responsible for scoring and classifying burnout risk.
No analysis, no reporting, no actions. Pure scoring logic.
"""

from dataclasses import dataclass
from enum import Enum
from src.core.config import get_settings


class RiskLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class RiskProfile:
    engineer_name: str
    email: str
    team: str
    manager_email: str
    burnout_risk_score: float
    risk_level: RiskLevel
    dominant_signal: str
    signal_breakdown: dict[str, float]
    raw_data: dict


class RiskScorer:
    """
    Converts raw Coral query results into typed RiskProfile objects.
    SRP: only knows about scoring. Not analysis, not actions.
    """

    def __init__(self):
        cfg = get_settings()
        self._high_threshold = cfg.high_risk_threshold
        self._medium_threshold = cfg.medium_risk_threshold

    def score(self, row: dict) -> RiskProfile:
        """Convert a single query result row into a RiskProfile."""
        score = float(row.get("burnout_risk_score", 0))
        signal_breakdown = self._build_signal_breakdown(row)
        dominant = max(signal_breakdown, key=signal_breakdown.get)

        return RiskProfile(
            engineer_name=row.get("engineer_name", "Unknown"),
            email=row.get("email", ""),
            team=row.get("team", "Unknown"),
            manager_email=row.get("manager_email", ""),
            burnout_risk_score=score,
            risk_level=self._classify(score),
            dominant_signal=dominant,
            signal_breakdown=signal_breakdown,
            raw_data=row,
        )

    def score_all(self, rows: list[dict]) -> list[RiskProfile]:
        """Score a list of query result rows."""
        profiles = [self.score(row) for row in rows]
        return sorted(profiles, key=lambda p: p.burnout_risk_score, reverse=True)

    # ── Private ───────────────────────────────────────────────────────────────

    def _classify(self, score: float) -> RiskLevel:
        if score >= self._high_threshold:
            return RiskLevel.HIGH
        if score >= self._medium_threshold:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _build_signal_breakdown(self, row: dict) -> dict[str, float]:
        """Decompose total score into named signal contributions."""
        return {
            "Late Night Commits":  float(row.get("late_night_commits", 0)) * 3.5,
            "Meeting Overload":    float(row.get("weekly_meeting_hours", 0)) * 1.8,
            "Slack Complaints":    float(row.get("slack_complaints", 0)) * 2.5,
            "On-Call Fatigue":     float(row.get("night_weekend_pages", 0)) * 5.0,
        }
