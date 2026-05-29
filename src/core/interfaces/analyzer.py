"""
IAnalyzer — Interface Segregation Principle (ISP)
Analysis strategies are interchangeable. Open/Closed: add new analyzer without
modifying the pipeline.
"""

from abc import ABC, abstractmethod
from typing import Any


class IAnalyzer(ABC):
    """Abstract interface for all analysis strategies."""

    @abstractmethod
    def analyze(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze raw query results and return structured analysis output.
        Returns: {engineer_name: {score, signals, risk_level, root_cause}}
        """
        ...

    @abstractmethod
    def get_analysis_name(self) -> str:
        """Human-readable name of this analysis type."""
        ...
