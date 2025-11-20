"""Table extraction using pymupdf4llm markdown conversion."""
from __future__ import annotations

from pathlib import Path
from typing import List, Sequence
import re

from .base import Cell, Table, TableExtractionEngine

try:  # pragma: no cover - optional dependency
    import pymupdf4llm  # type: ignore
except Exception:  # pragma: no cover - keep import optional
    pymupdf4llm = None  # type: ignore


class PyMuPDF4LLMTableEngine(TableExtractionEngine):
    """Use pymupdf4llm to convert the PDF into Markdown tables."""

    def __init__(self, min_columns: int = 2) -> None:
        super().__init__(name="pymupdf4llm")
        self.min_columns = min_columns

    def _ensure_dependency(self):  # type: ignore[return-value]
        if pymupdf4llm is None:
            raise RuntimeError(
                "pymupdf4llm is niet geïnstalleerd. Voeg het toe aan requirements en installeer het."
            )
        return pymupdf4llm

    def _is_separator_row(self, cells: List[str]) -> bool:
        return all(cell and all(ch in "-: " for ch in cell) for cell in cells)

    def _looks_like_placeholder(self, text: str) -> bool:
        return bool(re.fullmatch(r"col\d+", text.strip().lower()))

    def _repair_header_row(self, rows: List[List[Cell]]) -> None:
        if not rows:
            return

        header = rows[0]
        if not any(self._looks_like_placeholder(cell.text) for cell in header[1:]):
            return

        raw_header_text = header[0].text.replace("<br>", " ")
        split_tokens = raw_header_text.split()
        if len(split_tokens) < len(header):
            return

        rows[0] = [Cell(text=token) for token in split_tokens[: len(header)]]

    def _finalize_table(self, rows: List[List[Cell]], tables: List[Table]) -> None:
        if rows and any(len(row) >= self.min_columns for row in rows):
            self._repair_header_row(rows)
            tables.append([list(row) for row in rows])
        rows.clear()

    def _markdown_to_tables(self, markdown: str) -> List[Table]:
        tables: List[Table] = []
        current_rows: List[List[Cell]] = []
        for raw_line in markdown.splitlines() + [""]:
            line = raw_line.strip()
            if line.startswith("|") and "|" in line[1:]:
                normalized = line
                if not normalized.endswith("|"):
                    normalized += "|"
                cells = [cell.strip() for cell in normalized.strip("|").split("|")]
                if not cells or self._is_separator_row(cells):
                    continue
                current_rows.append([Cell(text=cell) for cell in cells])
            else:
                if current_rows:
                    self._finalize_table(current_rows, tables)
        return tables

    def extract(self, pdf_path: Path) -> Sequence[Table]:  # type: ignore[override]
        module = self._ensure_dependency()
        markdown = module.to_markdown(str(pdf_path))
        if isinstance(markdown, tuple):
            markdown = markdown[0]
        return self._markdown_to_tables(markdown)
