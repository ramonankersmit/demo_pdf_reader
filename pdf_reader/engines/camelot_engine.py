"""Table extraction using Camelot."""
from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
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
        self._patched_tempdir = False

    def _ensure_dependency(self):  # type: ignore[return-value]
        if camelot is None:
            raise RuntimeError(
                "camelot is niet geïnstalleerd. Voeg het toe aan requirements en installeer het."
            )
        return camelot

    def _patch_tempdir(self, module) -> None:
        """Replace Camelot's tempdir helper so cleanup happens immediately.

        Camelot registers temporary directories for deletion via ``atexit``
        (see ``camelot.utils.TemporaryDirectory``). On Windows this can raise
        ``PermissionError`` if the underlying files are still locked when the
        interpreter shuts down. By swapping in a temp directory implementation
        that cleans up during context exit—and ignores lingering locks—we avoid
        noisy shutdown errors while keeping the temporary workspace isolated.
        """

        if self._patched_tempdir:
            return

        # ``module`` is the imported Camelot package; patch both the shared
        # utils class and the copy imported in ``camelot.handlers``.
        class _ImmediateTempDir:
            def __enter__(self):
                self._tempdir = tempfile.TemporaryDirectory()
                return self._tempdir.__enter__()

            def __exit__(self, exc_type, exc_val, exc_tb):
                try:
                    return self._tempdir.__exit__(exc_type, exc_val, exc_tb)
                finally:
                    # Best-effort cleanup to avoid Windows file-lock errors.
                    shutil.rmtree(self._tempdir.name, ignore_errors=True)

        module.utils.TemporaryDirectory = _ImmediateTempDir
        if hasattr(module, "handlers"):
            module.handlers.TemporaryDirectory = _ImmediateTempDir
        self._patched_tempdir = True

    def extract(self, pdf_path: Path) -> Sequence[Table]:  # type: ignore[override]
        module = self._ensure_dependency()
        self._patch_tempdir(module)
        tables: List[Table] = []
        collection = module.read_pdf(str(pdf_path), pages="all", flavor=self.flavor)
        for table in collection:
            dataframe = table.df
            tables.append([[Cell(text=str(cell)) for cell in row] for row in dataframe.values.tolist()])
        return tables
