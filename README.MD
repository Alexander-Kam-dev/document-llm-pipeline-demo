# Document LLM Pipeline Demo

A demonstration project for PDF document processing with AI-powered structured data extraction.

## Features

- **PDF Ingestion**: Upload PDFs via FastAPI endpoint or CLI
- **Text Extraction**: Uses pdfplumber for native text extraction with Tesseract OCR fallback for scanned documents
- **Dual Extraction Modes**:
  - **LLM Mode**: Leverages Ollama (llama3) for intelligent field extraction
  - **Rules Mode**: Uses regex/template patterns for offline processing
- **Schema Validation**: Pydantic-based validation ensures well-formed outputs
- **Persistence**: SQLite database storage + JSON file artifacts
- **REST API**: FastAPI endpoints for integration

## Quick Start

### Prerequisites

- Python 3.9+
- Tesseract OCR (`apt-get install tesseract-ocr` on Ubuntu)
- Ollama with llama3 model (for LLM mode)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example.txt .env
# Edit .env with your settings

# Create data directories
mkdir -p data/outputs
```

### Running the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

## API Endpoints

### POST /extract
Upload and process a PDF document.

```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@invoice.pdf" \
  -F "mode=llm"
```

### GET /documents
List all processed documents.

```bash
curl "http://localhost:8000/documents"
```

### GET /health
Check service health and configuration.

```bash
curl "http://localhost:8000/health"
```

## Sample Data

The `samples/` directory contains:
- `native-text.pdf` - A standard PDF with embedded text
- `scanned.pdf` - A scanned PDF requiring OCR
- `outputs/` - Example JSON extraction results

## Architecture

```
app/
├── main.py          # FastAPI application and routes
├── config.py        # Configuration management
├── schema.py        # Pydantic data models
├── ingest.py        # PDF text extraction and OCR
├── llm_extractor.py # Ollama integration
├── pipeline.py      # Extraction orchestration
└── storage.py       # SQLite persistence
```

## Configuration

Edit `.env` to customize:

- `OLLAMA_BASE_URL`: Ollama API endpoint (default: http://localhost:11434)
- `OLLAMA_MODEL`: Model name (default: llama3)
- `EXTRACTION_MODE`: "llm" or "rules" (default: llm)
- `SQLITE_DB_PATH`: Database file path
- `JSON_OUTPUT_DIR`: Directory for JSON outputs

## Development

```bash
# Run tests
pytest

# Format code
black app/

# Type checking
mypy app/
```

## License

MIT
