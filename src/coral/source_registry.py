"""
SourceRegistry — Single Responsibility Principle (SRP)
This module only manages data source registration. Nothing else.
Coral feature: Unified source management — register once, query anywhere.
Open/Closed Principle: Adding a new source means calling register(), not modifying this class.
"""

from src.core.interfaces import IDataSource


class SourceRegistry:
    """
    Central registry of all connected data sources.
    Coral feature: Register any API/database/file as a queryable source.
    """

    def __init__(self):
        self._sources: dict[str, IDataSource] = {}

    def register(self, source: IDataSource) -> None:
        """Register a new data source. Open/Closed — no existing code changes."""
        self._sources[source.source_name] = source
        print(f"  [Coral] ✅ Registered source: {source.source_name}")

    def get(self, source_name: str) -> IDataSource | None:
        return self._sources.get(source_name)

    def get_all(self) -> dict[str, IDataSource]:
        return dict(self._sources)

    def list_sources(self) -> list[str]:
        return list(self._sources.keys())

    def health_check_all(self) -> dict[str, bool]:
        """Run health checks on all registered sources."""
        return {
            name: source.health_check()
            for name, source in self._sources.items()
        }

    def fetch_all_schemas(self) -> dict[str, dict[str, list[str]]]:
        """Fetch schema from all registered sources."""
        schemas = {}
        for name, source in self._sources.items():
            schemas[name] = source.get_schema()
        return schemas
