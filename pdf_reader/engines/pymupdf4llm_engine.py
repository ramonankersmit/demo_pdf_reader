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

    def _extract_with_pymupdf(self, pdf_path: Path) -> List[Table]:
        tables: List[Table] = []
        try:
            # ``fitz`` is the public import name of PyMuPDF, the same library
            # pymupdf4llm builds on top of. Using it directly lets us leverage
            # its native table detector without changing engines.
            import fitz  # type: ignore
        except Exception:
            return tables

        doc = fitz.open(pdf_path)
        try:
            for page in doc:
                try:
                    page_tables = page.find_tables()
                except Exception:
                    continue
                for table in page_tables.tables:
                    extracted = table.extract()
                    if not extracted:
                        continue
                    row_cells: List[List[Cell]] = []
                    for row in extracted:
                        row_cells.append(
                            [Cell(text=cell or "") for cell in row]
                        )
                    cleaned = self._remove_empty_columns(row_cells)
                    if cleaned and any(len(row) >= self.min_columns for row in cleaned):
                        tables.append(cleaned)
        finally:
            doc.close()
        return tables

    def _remove_empty_columns(self, table: Table) -> Table:
        if not table:
            return table

        column_count = max(len(row) for row in table)
        keep_indices: List[int] = []
        for idx in range(column_count):
            if any(idx < len(row) and row[idx].text.strip() for row in table):
                keep_indices.append(idx)

        if len(keep_indices) == column_count:
            return table

        cleaned: Table = []
        for row in table:
            cleaned.append([row[idx] for idx in keep_indices if idx < len(row)])
        return cleaned

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
        tables = self._extract_with_pymupdf(pdf_path)
        if tables:
            return tables

        module = self._ensure_dependency()
        markdown = module.to_markdown(str(pdf_path))
        if isinstance(markdown, tuple):
            markdown = markdown[0]
        return self._markdown_to_tables(markdown)
