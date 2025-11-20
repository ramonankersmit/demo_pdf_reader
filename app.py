"""CLI applicatie om tabellen uit PDF bestanden te halen."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from openpyxl import Workbook

import typer

from pdf_reader.engines.base import summarize_tables
from pdf_reader.table_extractor import ExtractionResult, TableExtractor

app = typer.Typer(help="Experimenteer met verschillende tabel engines voor PDF's")


@app.command()
def list_engines() -> None:
    """Toon beschikbare engines."""
    extractor = TableExtractor()
    typer.echo("Beschikbare engines:")
    for engine in extractor.engines:
        typer.echo(f"- {engine}")


def _write_outputs(
    data: dict,
    results: List[ExtractionResult],
    output: Path | None,
    excel_output: Path | None,
    view_json: bool,
) -> None:
    if output:
        output.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        typer.echo(f"Resultaat opgeslagen in {output}")

    if excel_output:
        workbook = Workbook()
        # Remove the default empty sheet
        default_sheet = workbook.active
        workbook.remove(default_sheet)
        for result in results:
            engine_name = result.engine
            tables = data[engine_name]
            worksheet = workbook.create_sheet(engine_name[:31] or "result")
            if not tables:
                worksheet.append(["Geen tabellen gevonden"])
                continue
            for idx, table in enumerate(tables, start=1):
                worksheet.append([f"Table {idx}"])
                for row in table:
                    worksheet.append(row)
                worksheet.append([])  # lege regel tussen tabellen
        workbook.save(excel_output)
        typer.echo(f"Excel bestand opgeslagen in {excel_output}")

    if view_json:
        typer.echo("Volledige JSON output:")
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))


def _extract_pdf(
    pdf: Path,
    extractor: TableExtractor,
    engines: Optional[List[str]],
    tune_pdfplumber: bool,
    tuning_depth: int,
    min_words: Optional[List[int]],
) -> tuple[List[ExtractionResult], dict]:
    results = extractor.extract(
        pdf,
        engines=engines,
        tune_pdfplumber=tune_pdfplumber,
        tuning_depth=tuning_depth,
        min_word_options=min_words,
    )
    for result in results:
        typer.secho(f"Resultaten voor {result.engine}", fg=typer.colors.GREEN, bold=True)
        if not result.tables:
            typer.echo("Geen tabellen gevonden\n")
            continue
        typer.echo(summarize_tables(result.tables))
        typer.echo("")

    data = {
        result.engine: [
            [[cell.text for cell in row] for row in table]
            for table in result.tables
        ]
        for result in results
    }
    return results, data


@app.command()
def extract(
    pdf: Path = typer.Argument(..., exists=True, readable=True, help="Pad naar het PDF bestand"),
    engine: Optional[List[str]] = typer.Option(None, "--engine", "-e", help="Naam van de engine(s)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Schrijf JSON resultaat naar dit bestand"),
    excel_output: Optional[Path] = typer.Option(
        None,
        "--excel",
        help="Schrijf een Excel bestand met de tabellen per engine",
    ),
    view_json: bool = typer.Option(
        False,
        "--view-json",
        help="Toon de volledige JSON output in de terminal",
    ),
    tune_pdfplumber: bool = typer.Option(
        False,
        "--tune-pdfplumber",
        help=(
            "Gebruik pymupdf4llm als referentie en pas pdfplumber-instellingen"
            " recursief aan om dichter bij het referentieresultaat te komen"
        ),
    ),
    tuning_depth: int = typer.Option(
        4,
        "--tuning-depth",
        min=0,
        help="Aantal recursiestappen voor het afstemmen van pdfplumber",
    ),
    min_words: Optional[List[int]] = typer.Option(
        None,
        "--min-words",
        help="Optionele lijst met min_words kandidaten voor het afstemmen",
    ),
) -> None:
    """Voer tabel extractie uit."""
    extractor = TableExtractor()
    results, data = _extract_pdf(
        pdf,
        extractor,
        engine,
        tune_pdfplumber,
        tuning_depth,
        min_words,
    )
    _write_outputs(data, results, output, excel_output, view_json)


@app.command()
def extract_directory(
    input_dir: Path = typer.Argument(
        ..., exists=True, file_okay=False, help="Map met PDF-bestanden om te verwerken"
    ),
    output_dir: Path = typer.Argument(..., file_okay=False, help="Map om resultaten op te slaan"),
    engine: Optional[List[str]] = typer.Option(
        None, "--engine", "-e", help="Naam van de engine(s)"
    ),
    view_json: bool = typer.Option(
        False, "--view-json", help="Toon de volledige JSON output in de terminal"
    ),
    tune_pdfplumber: bool = typer.Option(
        False,
        "--tune-pdfplumber",
        help=(
            "Gebruik pymupdf4llm als referentie en pas pdfplumber-instellingen"
            " recursief aan om dichter bij het referentieresultaat te komen"
        ),
    ),
    tuning_depth: int = typer.Option(
        4,
        "--tuning-depth",
        min=0,
        help="Aantal recursiestappen voor het afstemmen van pdfplumber",
    ),
    min_words: Optional[List[int]] = typer.Option(
        None,
        "--min-words",
        help="Optionele lijst met min_words kandidaten voor het afstemmen",
    ),
    excel: bool = typer.Option(
        False,
        "--excel",
        help="Sla ook per PDF een Excel-bestand op naast de JSON-output",
    ),
) -> None:
    """Verwerk alle PDF-bestanden in een map en sla per bestand resultaten op."""
    extractor = TableExtractor()
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = sorted(file for file in input_dir.iterdir() if file.suffix.lower() == ".pdf")

    if not pdf_files:
        typer.echo(f"Geen PDF-bestanden gevonden in {input_dir}")
        raise typer.Exit(code=1)

    for pdf in pdf_files:
        typer.secho(f"\nVerwerken: {pdf.name}", fg=typer.colors.BLUE, bold=True)
        results, data = _extract_pdf(
            pdf,
            extractor,
            engine,
            tune_pdfplumber,
            tuning_depth,
            min_words,
        )
        json_path = output_dir / f"{pdf.stem}.json"
        excel_path = (output_dir / f"{pdf.stem}.xlsx") if excel else None
        _write_outputs(data, results, json_path, excel_path, view_json)


if __name__ == "__main__":
    app()
