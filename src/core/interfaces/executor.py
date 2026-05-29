"""
IActionExecutor — Interface Segregation Principle (ISP)
Executors only execute actions. They do not analyze data or generate reports.
"""

from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass


@dataclass
class ActionResult:
    """Result of an executed action."""
    action_type: str
    target: str
    success: bool
    message: str
    artifact: str | None = None


class IActionExecutor(ABC):
    """Abstract interface for all action executors."""

    @abstractmethod
    def execute(self, action: dict[str, Any]) -> ActionResult:
        """
        Execute a single action and return the result.
        Action dict: {type, target, payload}
        """
        ...

    @abstractmethod
    def can_execute(self, action_type: str) -> bool:
        """Return True if this executor handles the given action type."""
        ...
