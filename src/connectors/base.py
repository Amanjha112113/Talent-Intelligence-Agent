"""
BaseConnector — Liskov Substitution Principle (LSP) + Open/Closed Principle (OCP)
All connectors extend this. CoralEngine can swap any connector without breaking.
Subclasses override _load_records() — base class handles file reading + schema.
"""

import json
import os
from pathlib import Path
from abc import abstractmethod
from typing import Any

from src.core.interfaces import IDataSource
from src.core.config import get_settings


class BaseConnector(IDataSource):
    """
    Base connector class. Implements common mock-data loading logic.
    Subclasses only need to define their table-to-file mappings.
    LSP: All subclasses are fully interchangeable with IDataSource.
    """

    def __init__(self):
        self._settings = get_settings()
        self._mock_dir = Path(self._settings.mock_data_dir)
        self._use_mock = self._settings.use_mock_data
        self._schema_cache: dict[str, list[str]] | None = None

    # ── IDataSource implementation ─────────────────────────────────────────────

    def fetch(self, table: str, filters: dict[str, Any] | None = None) -> list[dict]:
        """Load records from mock file or live API based on configuration."""
        if self._use_mock:
            return self._load_from_file(table)
        return self._fetch_live(table, filters or {})

    def get_schema(self) -> dict[str, dict[str, str]]:
        """Auto-discover schema and types from available files/API tables."""
        if self._schema_cache is not None:
            return self._schema_cache

        schema = {}
        for table_name, filename in self._table_map().items():
            records = self._load_from_file(table_name)
            if records:
                col_defs = {}
                for k, v in records[0].items():
                    if isinstance(v, bool):
                        col_defs[k] = "BOOLEAN"
                    elif isinstance(v, int):
                        col_defs[k] = "INTEGER"
                    elif isinstance(v, float):
                        col_defs[k] = "DOUBLE"
                    else:
                        col_defs[k] = "VARCHAR"
                schema[table_name] = col_defs
            else:
                schema[table_name] = {}

        self._schema_cache = schema
        return schema

    def health_check(self) -> bool:
        """For mock mode, check if data files exist."""
        if self._use_mock:
            return all(
                (self._mock_dir / filename).exists()
                for filename in self._table_map().values()
            )
        return self._check_live_connection()

    # ── Abstract methods subclasses must implement ─────────────────────────────

    @abstractmethod
    def _table_map(self) -> dict[str, str]:
        """Return mapping of table_name → mock_filename."""
        ...

    def _fetch_live(self, table: str, filters: dict[str, Any]) -> list[dict]:
        """Override this to implement live API fetching."""
        raise NotImplementedError(f"Live API not implemented for {self.source_name}")

    def _check_live_connection(self) -> bool:
        """Override this to check live API connectivity."""
        return False

    # ── Protected helpers ─────────────────────────────────────────────────────

    def _load_from_file(self, table: str) -> list[dict]:
        """Load JSONL mock data for a given table name."""
        filename = self._table_map().get(table)
        if not filename:
            return []

        filepath = self._mock_dir / filename
        if not filepath.exists():
            print(f"  [Warning] Mock file not found: {filepath}")
            return []

        records = []
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
