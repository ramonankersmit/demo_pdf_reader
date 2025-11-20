"""CLI applicatie om tabellen uit PDF bestanden te halen."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import typer

from pdf_reader.engines.base import summarize_tables
from pdf_reader.table_extractor import TableExtractor

app = typer.Typer(help="Experimenteer met verschillende tabel engines voor PDF's")


@app.command()
def list_engines() -> None:
    """Toon beschikbare engines."""
    extractor = TableExtractor()
    typer.echo("Beschikbare engines:")
    for engine in extractor.engines:
        typer.echo(f"- {engine}")


@app.command()
def extract(
    pdf: Path = typer.Argument(..., exists=True, readable=True, help="Pad naar het PDF bestand"),
    engine: Optional[List[str]] = typer.Option(None, "--engine", "-e", help="Naam van de engine(s)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Schrijf JSON resultaat naar dit bestand"),
) -> None:
    """Voer tabel extractie uit."""
    extractor = TableExtractor()
    results = extractor.extract(pdf, engines=engine)
    # We'll also print summary to console
    for result in results:
        typer.secho(f"Resultaten voor {result.engine}", fg=typer.colors.GREEN, bold=True)
        if not result.tables:
            typer.echo("Geen tabellen gevonden\n")
            continue
        typer.echo(summarize_tables(result.tables))
        typer.echo("")
    if output:
        data = {
            result.engine: [
                [[cell.text for cell in row] for row in table]
                for table in result.tables
            ]
            for result in results
        }
        output.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        typer.echo(f"Resultaat opgeslagen in {output}")


if __name__ == "__main__":
    app()
