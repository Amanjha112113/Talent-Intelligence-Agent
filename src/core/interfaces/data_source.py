"""
IDataSource — Interface Segregation Principle (ISP)
Every data connector implements exactly this interface. Nothing more, nothing less.
Coral uses this abstraction — it never depends on a concrete connector.
"""

from abc import ABC, abstractmethod
from typing import Any


class IDataSource(ABC):
    """
    Abstract interface for all data sources.
    Dependency Inversion: CoralEngine depends on this, not concrete connectors.
    Liskov Substitution: GitHubConnector, MockConnector etc. are fully interchangeable.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique name of this data source (e.g., 'github', 'slack')."""
        ...

    @abstractmethod
    def fetch(self, table: str, filters: dict[str, Any] | None = None) -> list[dict]:
        """
        Fetch records from a named table in this source.
        Handles auth, pagination, and rate limiting internally.
        """
        ...

    @abstractmethod
    def get_schema(self) -> dict[str, list[str]]:
        """
        Return the schema for all tables in this source.
        Format: {"table_name": ["col1", "col2", ...]}
        """
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the source is reachable and authenticated."""
        ...
