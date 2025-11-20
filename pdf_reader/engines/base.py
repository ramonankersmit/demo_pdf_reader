"""Abstract definitions for table extraction engines."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass
class Cell:
    """Representation of a table cell."""

    text: str


Table = List[List[Cell]]


class TableExtractionEngine(ABC):
    """Abstract interface that all engines must implement."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def extract(self, pdf_path: Path) -> Sequence[Table]:
        """Return a sequence of tables for the given PDF."""

    def flatten_text(self, table: Table) -> List[List[str]]:
        return [[cell.text for cell in row] for row in table]

    def extract_as_text(self, pdf_path: Path) -> List[List[List[str]]]:
        return [self.flatten_text(table) for table in self.extract(pdf_path)]


def summarize_tables(tables: Iterable[Table]) -> str:
    summary_lines = []
    for idx, table in enumerate(tables, start=1):
        summary_lines.append(f"Table {idx}:")
        for row in table:
            summary_lines.append(" | ".join(cell.text for cell in row))
        summary_lines.append("")
    return "\n".join(summary_lines).strip()
