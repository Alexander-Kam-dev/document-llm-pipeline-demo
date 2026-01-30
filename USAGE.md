# Usage Guide

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up Tesseract OCR (Ubuntu/Debian)
sudo apt-get install tesseract-ocr

# For LLM mode, install Ollama and pull the model
# Visit https://ollama.ai for installation
ollama pull llama3
```

### 2. Configuration

Copy the example environment file and customize:

```bash
cp .env.example.txt .env
```

Edit `.env` to configure:
- `OLLAMA_BASE_URL`: Ollama API endpoint (default: http://localhost:11434)
- `OLLAMA_MODEL`: Model name (default: llama3)
- `EXTRACTION_MODE`: "llm" or "rules" (default: llm)
- `SQLITE_DB_PATH`: Database path (default: ./data/documents.db)
- `JSON_OUTPUT_DIR`: JSON output directory (default: ./data/outputs)

### 3. Start the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

API Documentation: http://localhost:8000/docs

## API Examples

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "mode": "llm",
  "model": "llama3",
  "ollama_url": "http://localhost:11434"
}
```

### Extract Document (LLM Mode)

```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@invoice.pdf" \
  -F "mode=llm"
```

### Extract Document (Rules Mode)

```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@invoice.pdf" \
  -F "mode=rules"
```

Response:
```json
{
  "metadata": {
    "id": 1,
    "filename": "invoice.pdf",
    "upload_date": "2024-01-30T12:00:00",
    "extraction_mode": "rules",
    "status": "success",
    "error_message": null
  },
  "extracted_data": {
    "doc_type": "invoice",
    "vendor": "Acme Corporation",
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-01-15",
    "total_amount": 1250.0,
    "currency": "USD",
    "line_items": []
  }
}
```

### List Documents

```bash
curl http://localhost:8000/documents
```

### Get Specific Document

```bash
curl http://localhost:8000/documents/1
```

## CLI Usage

Process a document from the command line:

```bash
# Using LLM mode
python cli.py invoice.pdf --mode llm

# Using rules mode
python cli.py invoice.pdf --mode rules
```

## Testing with Sample Files

The project includes sample PDFs in the `samples/` directory:

```bash
# Test with native text invoice
python cli.py samples/native-text-invoice.pdf --mode rules

# Test with scanned receipt
python cli.py samples/scanned-receipt.pdf --mode rules
```

## Output Files

Processed documents are stored in two locations:

1. **SQLite Database**: `data/documents.db`
   - Contains metadata and extracted JSON for all documents
   
2. **JSON Files**: `data/outputs/document_N.json`
   - Individual JSON files for each successful extraction

## Extraction Modes

### LLM Mode
- Uses Ollama with llama3 model
- Requires Ollama running locally or accessible via network
- More accurate for complex documents
- Can extract line items and detailed information

### Rules Mode
- Uses regex patterns and heuristics
- No external dependencies (no LLM required)
- Faster but less accurate
- Good for simple, standardized documents

## Supported Document Types

The system can identify and extract data from:
- **Invoices**: Vendor, invoice number, date, total, line items
- **Receipts**: Vendor, date, total
- **Contracts**: Basic metadata extraction
- **Other**: Generic document processing

## Running Tests

```bash
pytest tests/ -v
```

## Troubleshooting

### OCR Not Working

Ensure Tesseract is installed and the path is correct in `.env`:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Verify installation
tesseract --version
```

### Ollama Connection Failed

When using LLM mode, ensure Ollama is running:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Start Ollama if not running
ollama serve
```

If Ollama is not available, switch to rules mode by setting `EXTRACTION_MODE=rules` in `.env` or passing `mode=rules` in the API request.

### Database Locked

If you get database locked errors, ensure no other processes are accessing the database:

```bash
# Remove the database and restart
rm data/documents.db
```
