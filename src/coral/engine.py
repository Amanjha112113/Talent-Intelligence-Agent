"""
CoralEngine — Single Responsibility Principle (SRP)
This module only executes SQL queries against registered data sources. Nothing else.

Coral features implemented here:
  ✅ Query anything as SQL (DuckDB in-memory)
  ✅ Cross-source JOINs (5 sources, 1 query)
  ✅ Smart caching (CoralCache with TTL)
  ✅ Read-only enforcement (blocks INSERT/UPDATE/DELETE)
  ✅ 100% local (DuckDB in-memory, no data leaves the machine)
  ✅ Schema learning (SchemaRegistry integration)
"""

import time
import duckdb
import json
import tempfile
import os
from pathlib import Path
from typing import Any

from src.core.interfaces import IDataSource
from src.coral.cache import CoralCache
from src.coral.schema_registry import SchemaRegistry
from src.coral.source_registry import SourceRegistry


class CoralEngine:
    """
    The heart of Coral: executes cross-source SQL queries using DuckDB.
    Dependency Inversion: depends on IDataSource, not any concrete connector.
    """

    _READ_ONLY_VIOLATIONS = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE")

    def __init__(
        self,
        source_registry: SourceRegistry,
        cache: CoralCache,
        schema_registry: SchemaRegistry,
    ):
        # DIP: constructor injection — engine doesn't create its dependencies
        self._sources = source_registry
        self._cache = cache
        self._schema = schema_registry
        self._conn = duckdb.connect(":memory:")
        self._tables_loaded: set[str] = set()

    # ── Public API ────────────────────────────────────────────────────────────

    def query(self, sql: str, force_refresh: bool = False) -> list[dict[str, Any]]:
        """
        Execute a SQL query across all registered data sources.
        Coral cross-source JOIN made possible by loading all sources into DuckDB.

        Returns: list of result dicts (one per row)
        """
        self._enforce_read_only(sql)

        # Check cache first
        if not force_refresh:
            cached = self._cache.get(sql)
            if cached is not None:
                print(f"  [Coral Cache] ⚡ HIT — served from cache")
                return cached

        # Load all sources into DuckDB as in-memory tables
        self._load_all_sources()

        # Execute the cross-source SQL query
        start = time.perf_counter()
        try:
            result = self._conn.execute(sql).fetchdf()
            elapsed_ms = (time.perf_counter() - start) * 1000
            rows = result.to_dict(orient="records")
            print(f"  [Coral Engine] ✅ Query completed in {elapsed_ms:.1f}ms — {len(rows)} rows")
            self._cache.set(sql, rows)
            return rows
        except Exception as e:
            raise CoralQueryError(f"SQL execution failed: {e}\n\nQuery:\n{sql}") from e

    def discover_schema(self) -> str:
        """
        Coral feature: Schema learning — discover and describe all source schemas.
        Returns human-readable schema description for LLM context.
        """
        self._load_all_sources()
        return self._schema.describe()

    def get_cache_stats(self) -> dict[str, Any]:
        return self._cache.stats()

    # ── Private ───────────────────────────────────────────────────────────────

    def _load_all_sources(self) -> None:
        """Load each registered source into DuckDB as a queryable table."""
        for source_name, source in self._sources.get_all().items():
            schema = source.get_schema()
            for table_name in schema.keys():
                table_key = f"{source_name}_{table_name}"
                if table_key not in self._tables_loaded:
                    self._load_table(source, source_name, table_name, table_key, schema.get(table_name, []))

    def _load_table(
        self, source: IDataSource, source_name: str, table_name: str, table_key: str, columns: dict[str, str] | list[str]
    ) -> None:
        """Load a single table from a source into DuckDB via a temp JSONL file."""
        records = source.fetch(table_name)
        if not records:
            if columns:
                if isinstance(columns, dict):
                    cols_def = ", ".join([f"{col} {typ}" for col, typ in columns.items()])
                else:
                    cols_def = ", ".join([f"{col} VARCHAR" for col in columns])
                self._conn.execute(f"CREATE OR REPLACE TABLE {table_key} ({cols_def})")
            else:
                self._conn.execute(f"CREATE OR REPLACE TABLE {table_key} AS SELECT 1 WHERE 1=0")
            self._tables_loaded.add(table_key)
            return

        # Learn the schema
        self._schema.learn(source_name, table_name, records)

        # Write records to a temp JSONL file — DuckDB reads files natively
        tmp_path = os.path.join(tempfile.gettempdir(), f"coral_{table_key}.jsonl")
        with open(tmp_path, "w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

        self._conn.execute(
            f"CREATE OR REPLACE TABLE {table_key} AS "
            f"SELECT * FROM read_json('{tmp_path}', format='newline_delimited', auto_detect=true)"
        )
        self._tables_loaded.add(table_key)
        print(f"  [Coral] 📊 Loaded {table_key} ({len(records)} records)")

    def _enforce_read_only(self, sql: str) -> None:
        """
        Coral feature: Read-only enforcement.
        Blocks any mutating SQL statement to protect source systems.
        """
        sql_upper = sql.strip().upper()
        for keyword in self._READ_ONLY_VIOLATIONS:
            if sql_upper.startswith(keyword):
                raise CoralReadOnlyError(
                    f"Coral enforces read-only access. '{keyword}' statements are not allowed."
                )


class CoralQueryError(Exception):
    """Raised when a Coral SQL query fails."""


class CoralReadOnlyError(Exception):
    """Raised when a mutating SQL statement is attempted."""
