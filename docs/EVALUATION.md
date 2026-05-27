# AI evaluation harness (report-only)

This repository includes a *report-only* evaluation harness to help you improve extraction quality quickly and safely.

## What it does

- Runs extraction on each `samples/*.pdf`
- Compares output to golden expected JSON in `samples/expected/*.json`
- Prints a field-level diff report
- **Does not fail** (report-only)

## Run it

```bash
# LLM mode (requires Ollama running)
python cli.py eval --mode llm

# Rules mode
python cli.py eval --mode rules
```

## Add new samples

1. Add a new PDF to `samples/` (e.g., `samples/my-new-invoice.pdf`)
2. Create the expected output JSON at `samples/expected/my-new-invoice.json`
3. Run `python cli.py eval --mode llm` and iterate until it passes.

## Normalization rules

Comparison is *field-level* and applies light normalization to reduce false failures:
- dates: attempts to normalize to `YYYY-MM-DD` (supports `MM/DD/YYYY`, `MM-DD-YYYY`)
- currency: uppercased
- numbers: commas stripped, rounded to 2 decimals

If you need tighter/looser matching, edit `app/eval.py`.
