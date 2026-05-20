# Document LLM Pipeline

Production-ready PDF document extraction system with dual-mode AI processing (LLM + rules-based fallback). Built with FastAPI, Ollama, and Tesseract OCR. Handles invoices, receipts, and contracts with structured JSON output and persistence.

**Status:** Early-stage backend infrastructure. Suitable for small to medium document volumes with offline capability.

---

## Problem

Business documents (invoices, receipts, contracts) arrive in unstructured PDF format. Manual data entry is slow and error-prone. Existing solutions are either expensive (managed APIs) or brittle (rule-based only). This project demonstrates a cost-effective hybrid approach: LLM-powered extraction with offline regex fallback, deployed on commodity hardware.

---

## Architecture

```
┌─────────────┐
│   PDF File  │
└──────┬──────┘
       │ pdfplumber / Tesseract OCR
       ▼
┌─────────────────────────────┐
│   Text Extraction Layer     │
│ • Native text (pdfplumber)  │
│ • Scanned docs (Tesseract)  │
└──────┬──────────────────────┘
       │
       ├──────────────┬──────────────┐
       │              │              │
   LLM Mode      Rules Mode    (Future: Async)
       │              │
  Ollama/       Regex/         Job Queue /
  llama3      Templates        Worker Pool
       │              │
       └──────┬───────┘
              │ Pydantic Validation
              ▼
      ┌──────────────────┐
      │  Structured JSON │
      │  (by doc_type)   │
      └────────┬─────────┘
               │
        ┌──────┴──────┐
        │             │
      SQLite       JSON Files
      (DB)        (Artifacts)
```

---

## Current Results

**Sample Processing (v1.0):**

| Document Type | Mode | Extracted Fields | Status | Notes |
|---|---|---|---|---|
| Invoice (native text) | LLM | vendor, invoice_number, date, total, line_items (2) | ✓ Success | Acme Corporation invoice; 100% accuracy on structured fields |
| Receipt (scanned) | Rules | vendor, date, total | ✓ Success | Coffee shop receipt; total extracted correctly despite image quality |

**Extraction Coverage:**
- ✓ Vendor name / merchant
- ✓ Invoice / receipt number
- ✓ Transaction date
- ✓ Total amount & currency
- ✓ Line items (when present)
- ⚠ Partial: Tax/subtotal breakdown (rules mode only)
- ✗ Not yet: Payment terms, line-item taxes (LLM mode improvements planned)

---

## API Contract

### POST /extract
Process a PDF and extract structured data.

**Request:**
```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@invoice.pdf" \
  -F "mode=llm"
```

**Response (200):**
```json
{
  "metadata": {
    "id": 1,
    "filename": "invoice.pdf",
    "upload_date": "2024-01-15T10:30:00",
    "extraction_mode": "llm",
    "status": "success"
  },
  "extracted_data": {
    "doc_type": "invoice",
    "vendor": "Acme Corporation",
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-01-15",
    "total_amount": 1250.0,
    "currency": "USD",
    "line_items": [
      {
        "description": "Professional Services - January 2024",
        "quantity": 40.0,
        "unit_price": 25.0,
        "total": 1000.0
      }
    ]
  }
}
```

**Error Response (400):**
```json
{
  "detail": "Only PDF files are supported"
}
```

### GET /documents
List all processed documents.

```bash
curl "http://localhost:8000/documents?limit=10&offset=0"
```

### GET /health
Check service health.

```bash
curl "http://localhost:8000/health"
```

---

## Quick Start

### Prerequisites
- Python 3.9+
- Tesseract OCR: `apt-get install tesseract-ocr` (Ubuntu/Debian)
- Ollama with llama3 model (for LLM mode; rules mode works offline)

### Installation & Run

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example.txt .env
# Edit .env: set OLLAMA_BASE_URL, EXTRACTION_MODE, etc.

# Start server
uvicorn app.main:app --reload
```

API docs: `http://localhost:8000/docs`

---

## Project Structure

```
app/
├── main.py              # FastAPI routes & request handling
├── config.py            # Environment & settings
├── schema.py            # Pydantic models (current: generic)
├── ingest.py            # PDF text extraction (pdfplumber + Tesseract)
├── llm_extractor.py     # Ollama integration
├── pipeline.py          # Orchestration
└── storage.py           # SQLite & JSON persistence

samples/
├── native-text-invoice.pdf
├── scanned-receipt.pdf
└── outputs/             # Example JSON outputs
```

---

## Known Limitations

| Issue | Impact | Workaround | Roadmap |
|---|---|---|---|
| Generic schema (not typed by doc_type) | Harder to add doc-type-specific fields | N/A | v1.1: Typed schemas (Invoice, Receipt, Contract) |
| No rate limiting or auth | Not production-safe for shared deployment | Deploy behind API gateway | v1.1: Built-in API key auth + rate limits |
| LLM mode requires Ollama running | Can't run LLM extraction without local GPU/CPU | Use rules mode (slower, offline) | v1.1: Graceful fallback; v2: Optional cloud LLM |
| No structured logging | Hard to debug failures in production | Grep stdout logs | v1.1: Structured JSON logs + request IDs |
| Synchronous processing | Large files block requests | None currently | v2: Async job queue + status polling |
| Line-item extraction incomplete | Receipts often have no items | Manual review | Post-v1: Fine-tune on receipt data |
| No request size limits | Unbounded uploads possible | Nginx proxy | v1.1: Configurable max file size |

---

## Development

```bash
# Run tests (current: limited coverage)
pytest

# Code quality
black app/
mypy app/

# Lint
flake8 app/
```

---

## Roadmap

### v1.1 (Production Hardening)
- [ ] Typed schemas by doc_type (Invoice, Receipt, Contract)
- [ ] API key authentication + rate limiting
- [ ] Request size limits & error response envelopes
- [ ] Structured logging + request IDs + timing
- [ ] Docker & docker-compose
- [ ] Integration tests + malformed PDF tests + LLM timeout tests

### v1.2 (Reliability & Metrics)
- [ ] Field-level extraction metrics (accuracy, recall by doc type)
- [ ] Labeled test set + benchmark comparisons
- [ ] Graceful LLM fallback on timeout
- [ ] Health check + readiness probe

### v2.0 (Scale & Experience)
- [ ] Async job processing (submit → job ID → status/result endpoints)
- [ ] Worker pool with Celery/RQ
- [ ] Optional cloud LLM provider (OpenAI, Anthropic)
- [ ] CLI improvements (batch processing, output formats)
- [ ] Web UI for document review & corrections

---

## License

MIT
