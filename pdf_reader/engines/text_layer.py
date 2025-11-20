"""Table extraction using pdfplumber's built-in table detection."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import pdfplumber

from .base import Cell, Table, TableExtractionEngine


@dataclass
class PDFPlumberSettings:
    min_words: int
    snap_tolerance: float


class PDFPlumberTableEngine(TableExtractionEngine):
    """Use pdfplumber's extraction heuristics."""

    def __init__(self, min_words: int = 2, snap_tolerance: float = 3.0) -> None:
        super().__init__(name="pdfplumber")
        self.min_words = min_words
        self.snap_tolerance = snap_tolerance

    def _extract_with_settings(self, pdf_path: Path, settings: PDFPlumberSettings) -> List[Table]:
        tables: List[Table] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                raw_tables = page.extract_tables(
                    table_settings={
                        "snap_tolerance": settings.snap_tolerance,
                        "min_words_horizontal": settings.min_words,
                        "min_words_vertical": settings.min_words,
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

    def _score_settings(
        self, tables: Sequence[Table], reference_tables: Sequence[Table]
    ) -> int:
        return abs(len(tables) - len(reference_tables))

    def _recursive_snap_search(
        self,
        pdf_path: Path,
        settings: PDFPlumberSettings,
        reference_tables: Sequence[Table],
        snap_range: Tuple[float, float],
        depth: int,
        max_depth: int,
        best: Tuple[int, PDFPlumberSettings, List[Table]],
    ) -> Tuple[int, PDFPlumberSettings, List[Table]]:
        mid_snap = (snap_range[0] + snap_range[1]) / 2
        trial_settings = PDFPlumberSettings(
            min_words=settings.min_words, snap_tolerance=mid_snap
        )
        tables = self._extract_with_settings(pdf_path, trial_settings)
        score = self._score_settings(tables, reference_tables)
        if score < best[0]:
            best = (score, trial_settings, tables)

        if score == 0 or depth >= max_depth or snap_range[1] - snap_range[0] < 0.25:
            return best

        # Too many tables: increase snap_tolerance to merge cells; too few: decrease it.
        if len(tables) > len(reference_tables):
            next_range = (mid_snap, snap_range[1])
        else:
            next_range = (snap_range[0], mid_snap)

        return self._recursive_snap_search(
            pdf_path,
            settings,
            reference_tables,
            next_range,
            depth + 1,
            max_depth,
            best,
        )

    def tune_to_reference(
        self,
        pdf_path: Path,
        reference_tables: Sequence[Table],
        snap_range: Tuple[float, float] = (1.0, 12.0),
        max_depth: int = 4,
        min_word_options: Iterable[int] | None = None,
    ) -> Tuple[List[Table], PDFPlumberSettings]:
        """Recursively adjust settings to approach the reference table count."""

        candidates = list(min_word_options) if min_word_options else []
        if not candidates:
            candidates = [self.min_words]
        else:
            candidates.append(self.min_words)
        best_tables: List[Table] = []
        best_settings = PDFPlumberSettings(min_words=self.min_words, snap_tolerance=self.snap_tolerance)
        best_score = float("inf")

        for min_words in sorted(set(candidates)):
            initial_settings = PDFPlumberSettings(min_words=min_words, snap_tolerance=self.snap_tolerance)
            initial_tables = self._extract_with_settings(pdf_path, initial_settings)
            initial_score = self._score_settings(initial_tables, reference_tables)
            best_candidate = (initial_score, initial_settings, initial_tables)

            tuned_candidate = self._recursive_snap_search(
                pdf_path,
                initial_settings,
                reference_tables,
                snap_range,
                depth=0,
                max_depth=max_depth,
                best=best_candidate,
            )

            if tuned_candidate[0] < best_score:
                best_score = tuned_candidate[0]
                best_settings = tuned_candidate[1]
                best_tables = tuned_candidate[2]

        return best_tables, best_settings

    def extract(self, pdf_path: Path) -> Sequence[Table]:  # type: ignore[override]
        default_settings = PDFPlumberSettings(
            min_words=self.min_words, snap_tolerance=self.snap_tolerance
        )
        return self._extract_with_settings(pdf_path, default_settings)
