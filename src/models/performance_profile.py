"""
PerformanceProfile — Data containers for the performance grading system.
SRP: Pure data representation, zero logic.
"""

from dataclasses import dataclass

@dataclass
class PerformanceGrade:
    engineer_name: str
    code_score: float
    collab_score: float
    reliability_score: float
    availability_score: float
    overall_score: float
    grade: str  # A, B, C, D, or F

@dataclass
class LayoffRiskProfile:
    engineer_name: str
    perception_gap: float
    is_silent_hero: bool
    is_overrated: bool
    strength: str = ""
    focus_area: str = ""
    insight: str = ""
