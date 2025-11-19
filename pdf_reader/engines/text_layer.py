"""Table extraction using pdfplumber's built-in table detection."""
from __future__ import annotations

from pathlib import Path
from typing import List, Sequence

import pdfplumber

from .base import Cell, Table, TableExtractionEngine


class PDFPlumberTableEngine(TableExtractionEngine):
    """Use pdfplumber's extraction heuristics."""

    def __init__(self, min_words: int = 2, snap_tolerance: float = 3.0) -> None:
        super().__init__(name="pdfplumber")
        self.min_words = min_words
        self.snap_tolerance = snap_tolerance

    def extract(self, pdf_path: Path) -> Sequence[Table]:  # type: ignore[override]
        tables: List[Table] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                raw_tables = page.extract_tables(
                    table_settings={
                        "snap_tolerance": self.snap_tolerance,
                        "min_words_horizontal": self.min_words,
                        "min_words_vertical": self.min_words,
                    }
                )
                for raw_table in raw_tables:
                    table: Table = []
                    for raw_row in raw_table:
                        row = [Cell(text=cell.strip() if cell else "") for cell in raw_row]
                        table.append(row)
                    if table:
                        tables.append(table)
        return tables
