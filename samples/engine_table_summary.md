# Engine resultaten voor sample-PDF's

De onderstaande tabel toont per bestand het aantal gevonden tabellen en het aantal rijen in de eerste tabel per engine. Een engine voldoet aan de voorwaarde (“minimaal 1 tabel en de 1e tabel heeft ≥10 rijen”) wanneer zowel het aantal tabellen ≥1 is als het eerste-tabel-rijenaantal ≥10.

| PDF-bestand | pdfplumber (tabellen / 1e tabel rijen) | pymupdf4llm (tabellen / 1e tabel rijen) | easyocr | docling | camelot |
| --- | --- | --- | --- | --- | --- |
| _WiskundeB_4V_Per2.pdf | 9 / 30 ✅ | 1 / 30 ✅ | Error: libGL.so.1 ontbreekt | Error: kon document niet verwerken (model/download) | Error: camelot niet beschikbaar |
| sample1_ckv.pdf | 9 / 26 ✅ | 1 / 26 ✅ | Error: libGL.so.1 ontbreekt | Error: kon document niet verwerken (model/download) | Error: camelot niet beschikbaar |

**Engines die aan de voorwaarde voldoen:**
- Beide sample-bestanden: `pdfplumber` en `pymupdf4llm`.
- De overige engines gaven fouten bij het uitvoeren.
