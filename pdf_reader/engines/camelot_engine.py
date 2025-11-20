"""Table extraction using Camelot."""
from __future__ import annotations

from pathlib import Path
from typing import List, Sequence

from .base import Cell, Table, TableExtractionEngine

try:  # pragma: no cover - optional dependency
    import camelot  # type: ignore
except Exception:  # pragma: no cover - keep import optional
    camelot = None  # type: ignore


class CamelotTableEngine(TableExtractionEngine):
    """Use Camelot's lattice/stream extraction to gather tables."""

    def __init__(self, flavor: str = "lattice") -> None:
        super().__init__(name="camelot")
        self.flavor = flavor

    def _ensure_dependency(self):  # type: ignore[return-value]
        if camelot is None:
            raise RuntimeError(
                "camelot is niet geïnstalleerd. Voeg het toe aan requirements en installeer het."
            )
        return camelot

    def extract(self, pdf_path: Path) -> Sequence[Table]:  # type: ignore[override]
        module = self._ensure_dependency()
        tables: List[Table] = []
        collection = module.read_pdf(str(pdf_path), pages="all", flavor=self.flavor)
        for table in collection:
            dataframe = table.df
            tables.append([[Cell(text=str(cell)) for cell in row] for row in dataframe.values.tolist()])
        return tables
