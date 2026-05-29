"""
PerformanceGrader — SRP: Only grades. Does not analyze, report, or act.
Implements: IGrader
"""

from src.core.interfaces.grader import IGrader
from src.models.performance_profile import PerformanceGrade

class PerformanceGrader(IGrader):
    """Assigns letter grades based on the 4-sector weighted performance score."""

    GRADE_THRESHOLDS = {
        "A": 80.0,
        "B": 60.0,
        "C": 40.0,
        "D": 20.0,
    }

    def grade(self, row: dict) -> PerformanceGrade:
        """Assign a grade to a single query result row."""
        code = float(row.get("code_score", 0.0))
        collab = float(row.get("collab_score", 0.0))
        reliability = float(row.get("reliability_score", 0.0))
        availability = float(row.get("availability_score", 0.0))

        overall = min(100.0, round(
            code * 0.40 +
            collab * 0.25 +
            reliability * 0.20 +
            availability * 0.15,
            1
        ))

        return PerformanceGrade(
            engineer_name=row.get("engineer_name", "Unknown"),
            code_score=code,
            collab_score=collab,
            reliability_score=reliability,
            availability_score=availability,
            overall_score=overall,
            grade=self._letter_grade(overall)
        )

    def grade_all(self, rows: list[dict]) -> list[PerformanceGrade]:
        """Assign grades to a list of query result rows."""
        grades = [self.grade(row) for row in rows]
        # Sort by highest grade
        return sorted(grades, key=lambda p: p.overall_score, reverse=True)

    def _letter_grade(self, score: float) -> str:
        """Convert a numerical score to a letter grade."""
        for letter, threshold in self.GRADE_THRESHOLDS.items():
            if score >= threshold:
                return letter
        return "F"
