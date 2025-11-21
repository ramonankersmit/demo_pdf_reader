# Demo PDF Table Reader

Deze repository bevat een minimale CLI applicatie om verschillende table-extraction technieken op PDF-bestanden uit te proberen. Alle dependencies zijn lokaal te installeren en tijdens runtime zijn er geen netwerkverbindingen nodig.

## Installatie

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Gebruik

Toon beschikbare engines:

```bash
python app.py list-engines
```

Voer extractie uit met alle engines:

```bash
python app.py extract pad/naar/bestand.pdf
```

Alleen specifieke engines gebruiken:

```bash
python app.py extract pad/naar/bestand.pdf -e pdfplumber -e easyocr -e pymupdf4llm
```

Snel vergelijken (standaard `pymupdf4llm` en `camelot`, of specificeer zelf):

```bash
python app.py compare pad/naar/bestand.pdf
python app.py compare pad/naar/bestand.pdf -e pymupdf4llm -e camelot -e pdfplumber
```

Resultaten opslaan als JSON:

```bash
python app.py extract pad/naar/bestand.pdf --output tabels.json
```

Resultaten opslaan als Excel en de JSON direct bekijken:

```bash
python app.py extract pad/naar/bestand.pdf --excel tabellen.xlsx --view-json
```

Meerdere PDF-bestanden in één keer verwerken en per bestand een JSON (en optioneel
Excel) opslaan:

```bash
python app.py extract-directory samples output_map --excel
```

## Architectuur

- `pdf_reader/engines/base.py` bevat het abstracte contract.
- `pdf_reader/engines/text_layer.py` gebruikt pdfplumber om tabellen uit de tekstlaag te halen.
- `pdf_reader/engines/easyocr_engine.py` gebruikt EasyOCR en PyMuPDF om pagina's als afbeeldingen te verwerken.
- `pdf_reader/engines/pymupdf4llm_engine.py` zet het document om naar Markdown met `pymupdf4llm` en parseert daaruit de tabellen.
- `pdf_reader/engines/docling_engine.py` gebruikt Docling om een documentstructuur op te bouwen en daaruit de tabellen te lezen.
- `pdf_reader/engines/camelot_engine.py` gebruikt Camelot om tabellen rechtstreeks uit PDF-pagina's te detecteren.
- `pdf_reader/table_extractor.py` beheert de verschillende engines.

Deze opzet maakt het eenvoudig om later extra engines toe te voegen.
