"""Facade for extracting tables with multiple engines."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from .engines.base import Table, TableExtractionEngine
from .engines.easyocr_engine import EasyOCRTableEngine
from .engines.pymupdf4llm_engine import PyMuPDF4LLMTableEngine
from .engines.text_layer import PDFPlumberTableEngine


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

    def register(self, engine: TableExtractionEngine) -> None:
        self._engines[engine.name] = engine

    @property
    def engines(self) -> List[str]:
        return list(self._engines)

    def extract(self, pdf_path: Path, engines: Iterable[str] | None = None) -> List[ExtractionResult]:
        if engines is None:
            selected = self._engines.values()
        else:
            selected = []
            for name in engines:
                if name not in self._engines:
                    raise ValueError(f"Onbekende engine: {name}")
                selected.append(self._engines[name])
        results = []
        for engine in selected:
            tables = engine.extract(pdf_path)
            results.append(ExtractionResult(engine=engine.name, tables=tables))
        return results
