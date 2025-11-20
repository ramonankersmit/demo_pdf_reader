"""Table extraction using Docling's document converter."""
from __future__ import annotations

from pathlib import Path
from typing import Any, List, Sequence

from .base import Cell, Table, TableExtractionEngine

try:  # pragma: no cover - optional dependency
    from docling.document_converter import DocumentConverter, DocumentConversionSettings
except Exception:  # pragma: no cover - keep import optional
    DocumentConverter = None  # type: ignore
    DocumentConversionSettings = None  # type: ignore


class DoclingTableEngine(TableExtractionEngine):
    """Use Docling to parse documents and collect table data."""

    def __init__(self) -> None:
        super().__init__(name="docling")
        self._converter: Any | None = None

    def _ensure_converter(self) -> Any:
        if DocumentConverter is None:
            raise RuntimeError(
                "docling is niet geïnstalleerd. Voeg het toe aan requirements en installeer het."
            )
        if self._converter is None:
            settings = DocumentConversionSettings() if DocumentConversionSettings else None
            self._converter = DocumentConverter(conversion_settings=settings)
        return self._converter

    def _table_to_matrix(self, table_obj: Any) -> List[List[str]]:
        # Try common Docling table representations
        if hasattr(table_obj, "cells"):
            return [[str(cell) for cell in row] for row in table_obj.cells]  # type: ignore[attr-defined]
        if hasattr(table_obj, "data"):
            return [[str(cell) for cell in row] for row in table_obj.data]  # type: ignore[attr-defined]
        if hasattr(table_obj, "to_pandas"):
            dataframe = table_obj.to_pandas()  # type: ignore[assignment]
            return [[str(cell) for cell in row] for row in dataframe.values.tolist()]
        if hasattr(table_obj, "df"):
            dataframe = table_obj.df  # type: ignore[assignment]
            return [[str(cell) for cell in row] for row in dataframe.values.tolist()]
        if hasattr(table_obj, "as_dataframe"):
            dataframe = table_obj.as_dataframe()  # type: ignore[assignment]
            return [[str(cell) for cell in row] for row in dataframe.values.tolist()]
        return []

    def extract(self, pdf_path: Path) -> Sequence[Table]:  # type: ignore[override]
        converter = self._ensure_converter()
        document = converter.convert(str(pdf_path))
        tables: List[Table] = []
        for table_obj in getattr(document, "tables", []):
            matrix = self._table_to_matrix(table_obj)
            if not matrix:
                continue
            tables.append([[Cell(text=cell) for cell in row] for row in matrix])
        return tables
