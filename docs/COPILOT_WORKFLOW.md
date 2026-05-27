# Copilot-first development workflow

This repo is designed to move fast on *extraction quality* while keeping changes safe and reviewable.

## The workflow (Issue → Change → Evaluate → PR)

1. **Open an issue** using the templates in `.github/ISSUE_TEMPLATE/`.
   - Attach/describe a sample PDF (or provide extracted text)
   - Define the expected JSON fields
   - Add acceptance criteria

2. **Make a small, vertical PR**
   - Typical files touched:
     - `app/llm_extractor.py` (prompting, parsing)
     - `app/schema.py` (shape/validation)
     - `app/pipeline.py` (orchestration)
     - `tests/` (unit + evaluation)

3. **Run tests + evaluation locally**

   ```bash
   pytest -q
   python cli.py eval --mode llm
   ```

4. **Open the PR**
   - Include the evaluation output in the PR description
   - Keep PRs focused: one feature/fix at a time

## Report-only evaluation

The evaluation harness compares current extraction results against a small set of **golden expected JSON** files.

- It is **report-only**: it prints a report but does not fail tests/CI.
- It uses **field-level matching with normalization** (e.g., currency casing, numeric rounding, date normalization).

### Golden data layout

- PDFs: `samples/*.pdf`
- Expected outputs: `samples/expected/*.json`

File names should match:

- `samples/native-text-invoice.pdf` → `samples/expected/native-text-invoice.json`
- `samples/scanned-receipt.pdf` → `samples/expected/scanned-receipt.json`

## Tips for faster extraction improvements

- Add 1 new PDF + expected JSON whenever you fix a bug or add a capability.
- Prefer targeted improvements:
  - invoice number parsing
  - date normalization
  - total_amount robustness
  - vendor extraction
- Keep prompts deterministic and short; add schema-guided examples in prompts if needed.
