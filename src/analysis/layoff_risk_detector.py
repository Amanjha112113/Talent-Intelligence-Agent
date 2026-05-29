"""
LayoffRiskDetector — SRP: Detects perception gap between actual performance and visibility.
Implements: IAnalyzer
"""

import statistics
from typing import Any
from src.core.interfaces.analyzer import IAnalyzer
from src.models.performance_profile import LayoffRiskProfile, PerformanceGrade

class LayoffRiskDetector(IAnalyzer):
    """
    Identifies 'Silent Heroes' (high actual work, low visibility)
    and 'Overrated' engineers (low actual work, high visibility).
    """

    def analyze(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Receives pre-computed PerformanceGrades and detects perception gaps.
        Returns a dictionary mapping engineer_name to their LayoffRiskProfile.
        """
        grades: list[PerformanceGrade] = data.get("performance_grades", [])
        if not grades:
            return {}

        # Calculate medians to establish baselines
        code_scores = [g.code_score for g in grades]
        collab_scores = [g.collab_score for g in grades]
        
        median_code = statistics.median(code_scores) if code_scores else 0
        median_collab = statistics.median(collab_scores) if collab_scores else 0

        risk_profiles = {}
        for g in grades:
            # Silent Hero: Above median code, below median collaboration/visibility
            is_silent_hero = g.code_score >= median_code and g.collab_score < median_collab
            
            # Overrated: Below median code, above median collaboration/visibility
            is_overrated = g.code_score < median_code and g.collab_score >= median_collab
            
            # Perception Gap: Actual performance vs Visibility (Collab/Meetings)
            # A positive gap means they perform better than they are seen.
            # A negative gap means they are seen more than they perform.
            perception_gap = g.overall_score - g.collab_score

            scores = {
                "Code Contribution": g.code_score,
                "Collaboration": g.collab_score,
                "Reliability": g.reliability_score,
                "Availability": g.availability_score
            }
            sorted_scores = sorted(scores.items(), key=lambda x: x[1])
            focus_area = sorted_scores[0][0]
            strength = sorted_scores[-1][0]

            # Generate fully dynamic individual insight using code
            insight_parts = []
            if perception_gap > 10:
                insight_parts.append(f"Highly underestimated by visibility metrics.")
            elif perception_gap < -10:
                insight_parts.append(f"High visibility often masks lower raw output.")
            else:
                insight_parts.append(f"Visibility accurately matches output.")

            insight_parts.append(f"This engineer anchors the team in {strength}, but struggles primarily with {focus_area}.")

            if strength == "Code Contribution" and focus_area == "Collaboration":
                insight_parts.append("They are a heads-down coder who could benefit from sharing knowledge more publicly.")
            elif strength == "Collaboration" and focus_area == "Code Contribution":
                insight_parts.append("They are great at coordinating, but need to ship more direct code impact.")
            elif strength == "Reliability":
                insight_parts.append("They are an unsung hero of system stability and resolving incidents.")
            elif focus_area == "Availability":
                insight_parts.append("They have very low meeting attendance and overall availability signals.")

            insight = " ".join(insight_parts)

            risk_profiles[g.engineer_name] = LayoffRiskProfile(
                engineer_name=g.engineer_name,
                perception_gap=perception_gap,
                is_silent_hero=is_silent_hero,
                is_overrated=is_overrated,
                strength=strength,
                focus_area=focus_area,
                insight=insight
            )

        return risk_profiles

    def get_analysis_name(self) -> str:
        return "Layoff Risk Detection"
