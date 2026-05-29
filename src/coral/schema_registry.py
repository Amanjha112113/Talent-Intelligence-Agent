"""
SchemaRegistry — Single Responsibility Principle (SRP)
This module only learns and stores schema information. Nothing else.
Coral feature: Schema learning — automatically discovers columns and relationships.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ColumnInfo:
    name: str
    inferred_type: str
    sample_values: list[Any] = field(default_factory=list)
    nullable: bool = True


@dataclass
class TableSchema:
    source: str
    table: str
    columns: list[ColumnInfo]
    row_count: int = 0
    relationships: list[str] = field(default_factory=list)  # "other_source.other_table.col"


class SchemaRegistry:
    """
    Auto-learns schema from data sources.
    Coral feature: Schema learning — Coral automatically learns the schema
    of your data sources so you can write SQL without manual schema definition.
    """

    def __init__(self):
        self._schemas: dict[str, TableSchema] = {}  # key: "source.table"

    # ── Schema Learning ───────────────────────────────────────────────────────

    def learn(self, source: str, table: str, records: list[dict]) -> TableSchema:
        """
        Infer schema from a list of records.
        Automatically discovers column names, types, and sample values.
        """
        if not records:
            schema = TableSchema(source=source, table=table, columns=[])
            self._register(schema)
            return schema

        columns: list[ColumnInfo] = []
        sample = records[:5]

        for col_name in records[0].keys():
            values = [r.get(col_name) for r in sample if r.get(col_name) is not None]
            inferred_type = self._infer_type(values)
            columns.append(ColumnInfo(
                name=col_name,
                inferred_type=inferred_type,
                sample_values=values[:3],
                nullable=any(r.get(col_name) is None for r in records),
            ))

        schema = TableSchema(
            source=source,
            table=table,
            columns=columns,
            row_count=len(records),
        )
        self._register(schema)
        return schema

    def learn_relationships(self, source_a: str, table_a: str, col_a: str,
                            source_b: str, table_b: str, col_b: str) -> None:
        """Register a join relationship between two tables."""
        key_a = f"{source_a}.{table_a}"
        key_b = f"{source_b}.{table_b}"
        rel = f"{source_b}.{table_b}.{col_b}"
        if key_a in self._schemas and rel not in self._schemas[key_a].relationships:
            self._schemas[key_a].relationships.append(rel)

    # ── Query ─────────────────────────────────────────────────────────────────

    def get_schema(self, source: str, table: str) -> TableSchema | None:
        return self._schemas.get(f"{source}.{table}")

    def get_all_schemas(self) -> dict[str, TableSchema]:
        return dict(self._schemas)

    def describe(self) -> str:
        """Human-readable schema description for LLM context."""
        lines = ["# Available Data Sources & Tables\n"]
        for key, schema in self._schemas.items():
            cols = ", ".join(f"{c.name}({c.inferred_type})" for c in schema.columns)
            lines.append(f"**{key}** ({schema.row_count} rows)")
            lines.append(f"  Columns: {cols}")
            if schema.relationships:
                lines.append(f"  Joins: {', '.join(schema.relationships)}")
            lines.append("")
        return "\n".join(lines)

    # ── Private ───────────────────────────────────────────────────────────────

    def _register(self, schema: TableSchema) -> None:
        self._schemas[f"{schema.source}.{schema.table}"] = schema

    @staticmethod
    def _infer_type(values: list[Any]) -> str:
        if not values:
            return "unknown"
        sample = values[0]
        if isinstance(sample, bool):
            return "boolean"
        if isinstance(sample, int):
            return "integer"
        if isinstance(sample, float):
            return "float"
        if isinstance(sample, str):
            # Check if it looks like a datetime
            if "T" in sample and ("Z" in sample or "+" in sample):
                return "datetime"
            if len(sample) == 10 and sample.count("-") == 2:
                return "date"
            return "string"
        if isinstance(sample, list):
            return "array"
        if isinstance(sample, dict):
            return "object"
        return "unknown"
