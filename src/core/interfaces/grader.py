"""
IGrader — Interface Segregation Principle (ISP)
Defines a focused interface for performance grading.
"""

from abc import ABC, abstractmethod
from src.models.performance_profile import PerformanceGrade

class IGrader(ABC):
    @abstractmethod
    def grade(self, row: dict) -> PerformanceGrade:
        """Assign a grade to a single query result row."""
        ...

    @abstractmethod
    def grade_all(self, rows: list[dict]) -> list[PerformanceGrade]:
        """Assign grades to a list of query result rows."""
        ...
