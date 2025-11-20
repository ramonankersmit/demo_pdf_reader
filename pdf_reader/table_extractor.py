"""Facade for extracting tables with multiple engines."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from .engines.base import Table, TableExtractionEngine
from .engines.camelot_engine import CamelotTableEngine
from .engines.docling_engine import DoclingTableEngine
from .engines.easyocr_engine import EasyOCRTableEngine
from .engines.pymupdf4llm_engine import PyMuPDF4LLMTableEngine
from .engines.text_layer import PDFPlumberSettings, PDFPlumberTableEngine


@dataclass
class ExtractionResult:
    engine: str
    tables: Sequence[Table]


class TableExtractor:
    """Registry for multiple engines."""

    def __init__(self) -> None:
        self._engines: Dict[str, TableExtractionEngine] = {}
        self.register(PDFPlumberTableEngine())
        self.register(EasyOCRTableEngine())
        self.register(PyMuPDF4LLMTableEngine())
        self.register(DoclingTableEngine())
        self.register(CamelotTableEngine())

    def register(self, engine: TableExtractionEngine) -> None:
        self._engines[engine.name] = engine

    @property
    def engines(self) -> List[str]:
        return list(self._engines)

    def _validate_selection(
        self, engines: Iterable[str] | None
    ) -> List[TableExtractionEngine]:
        if engines is None:
            return list(self._engines.values())

        selected = []
        for name in engines:
            if name not in self._engines:
                raise ValueError(f"Onbekende engine: {name}")
            selected.append(self._engines[name])
        return selected

    def _tune_pdfplumber(
        self,
        pdf_path: Path,
        tuning_depth: int,
        min_word_options: Iterable[int] | None,
    ) -> List[ExtractionResult]:
        results: List[ExtractionResult] = []
        pymupdf_engine = self._engines["pymupdf4llm"]
        reference_tables = pymupdf_engine.extract(pdf_path)
        results.append(ExtractionResult(engine=pymupdf_engine.name, tables=reference_tables))

        pdfplumber_engine = self._engines["pdfplumber"]
        tuned_tables, settings = pdfplumber_engine.tune_to_reference(
            pdf_path,
            reference_tables,
            max_depth=tuning_depth,
            min_word_options=min_word_options,
        )
        tuned_label = self._format_tuned_label(settings)
        results.append(ExtractionResult(engine=tuned_label, tables=tuned_tables))
        return results

    def _format_tuned_label(self, settings: PDFPlumberSettings) -> str:
        return (
            "pdfplumber (tuned) "
            f"[snap={settings.snap_tolerance:.2f}, min_words={settings.min_words}]"
        )

    def extract(
        self,
        pdf_path: Path,
        engines: Iterable[str] | None = None,
        tune_pdfplumber: bool = False,
        tuning_depth: int = 4,
        min_word_options: Iterable[int] | None = None,
    ) -> List[ExtractionResult]:
        selected = self._validate_selection(engines)
        results: List[ExtractionResult] = []

        if tune_pdfplumber:
            results.extend(
                self._tune_pdfplumber(
                    pdf_path, tuning_depth=tuning_depth, min_word_options=min_word_options
                )
            )

        for engine in selected:
            if tune_pdfplumber and engine.name == "pymupdf4llm":
                # Already ran as baseline for tuning
                continue
            tables = engine.extract(pdf_path)
            results.append(ExtractionResult(engine=engine.name, tables=tables))
        return results
