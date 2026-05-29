"""
IReporter — Interface Segregation Principle (ISP)
Reporters only know how to generate reports. They do not analyze or execute actions.
"""

from abc import ABC, abstractmethod
from typing import Any


class IReporter(ABC):
    """Abstract interface for all report generators."""

    @abstractmethod
    def generate(self, analysis_results: dict[str, Any]) -> str:
        """
        Generate a report from analysis results.
        Returns: formatted report string (Markdown, text, etc.)
        """
        ...

    @abstractmethod
    def get_format(self) -> str:
        """Return the output format: 'markdown', 'text', 'json', 'html'."""
        ...
