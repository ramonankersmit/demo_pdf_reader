"""Table extraction using EasyOCR and simple heuristics."""
from __future__ import annotations

from pathlib import Path
from typing import List, Sequence, Tuple

import fitz  # PyMuPDF
import numpy as np

from .base import Cell, Table, TableExtractionEngine


class EasyOCRTableEngine(TableExtractionEngine):
    """Very light-weight table extraction using OCR bounding boxes."""

    def __init__(self, languages: Sequence[str] | None = None, text_threshold: float = 0.5) -> None:
        super().__init__(name="easyocr")
        self.languages = list(languages) if languages else ["nl", "en"]
        self.text_threshold = text_threshold
        self._reader: Reader | None = None

    def _ensure_reader(self) -> Reader:
        if self._reader is None:
            from easyocr import Reader

            self._reader = Reader(self.languages, gpu=False)
        return self._reader

    def _page_to_image(self, page: fitz.Page) -> np.ndarray:
        zoom = 2.0  # improve accuracy
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = np.frombuffer(pix.samples, dtype=np.uint8)
        img = img.reshape(pix.height, pix.width, pix.n)
        return img

    def _group_boxes(self, boxes: List[Tuple[int, int, int, int]], texts: List[str]) -> Table:
        # naive grouping by y coordinate
        combined = sorted(zip(boxes, texts), key=lambda item: (item[0][1], item[0][0]))
        rows: List[List[Cell]] = []
        current_row: List[Cell] = []
        last_y = None
        tolerance = 25
        for (x0, y0, x1, y1), text in combined:
            if last_y is None or abs(y0 - last_y) <= tolerance:
                current_row.append(Cell(text=text))
                last_y = y0 if last_y is None else (last_y + y0) / 2
            else:
                rows.append(current_row)
                current_row = [Cell(text=text)]
                last_y = y0
        if current_row:
            rows.append(current_row)
        return rows

    def extract(self, pdf_path: Path) -> Sequence[Table]:  # type: ignore[override]
        reader = self._ensure_reader()
        doc = fitz.open(pdf_path)
        tables: List[Table] = []
        for page in doc:
            image = self._page_to_image(page)
            results = reader.readtext(image)
            boxes: List[Tuple[int, int, int, int]] = []
            texts: List[str] = []
            for bbox, text, conf in results:
                if conf < self.text_threshold:
                    continue
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                boxes.append((min(x_coords), min(y_coords), max(x_coords), max(y_coords)))
                texts.append(text)
            if boxes:
                tables.append(self._group_boxes(boxes, texts))
        doc.close()
        return tables
