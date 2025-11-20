# Tuning results

## sample1_ckv.pdf
- Command: `python app.py extract samples/sample1_ckv.pdf --tune-pdfplumber --engine pdfplumber --engine pymupdf4llm`
- Best pdfplumber settings: `snap_tolerance=6.50`, `min_words=2`
- Outcome: tuned pdfplumber detected a single table aligning with the pymupdf4llm baseline table count for this sample.
