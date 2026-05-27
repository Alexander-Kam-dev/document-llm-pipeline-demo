"""Shared pytest fixtures for document processing tests."""
import pytest
import json
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config import settings
from app.storage import Base, Document


@pytest.fixture
def sample_invoice_bytes():
    """Load native-text invoice PDF for testing."""
    pdf_path = Path(__file__).parent.parent / "samples" / "native-text-invoice.pdf"
    if pdf_path.exists():
        with open(pdf_path, "rb") as f:
            return f.read()
    return b"%PDF-1.4\nTest invoice content"


@pytest.fixture
def sample_receipt_bytes():
    """Load scanned receipt PDF for testing."""
    pdf_path = Path(__file__).parent.parent / "samples" / "scanned-receipt.pdf"
    if pdf_path.exists():
        with open(pdf_path, "rb") as f:
            return f.read()
    return b"%PDF-1.4\nTest receipt content"


@pytest.fixture
def sample_invoice_json():
    """Expected output for invoice extraction."""
    return {
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
            },
            {
                "description": "Cloud Hosting Services",
                "quantity": 1.0,
                "unit_price": 250.0,
                "total": 250.0
            }
        ]
    }


@pytest.fixture
def sample_receipt_json():
    """Expected output for receipt extraction."""
    return {
        "doc_type": "receipt",
        "vendor": "COFFEE SHOP",
        "invoice_number": None,
        "invoice_date": "2024-01-30",
        "total_amount": 17.01,
        "currency": "USD",
        "line_items": []
    }


@pytest.fixture
def mock_ollama(mocker):
    """Mock Ollama API responses."""
    def mock_post(url, json=None, timeout=None):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "response": json.dumps({
                "doc_type": "invoice",
                "vendor": "Test Vendor",
                "invoice_number": "TEST-001",
                "total_amount": 100.0
            })
        }
        return response

    return mocker.patch("requests.post", side_effect=mock_post)


@pytest.fixture
def mock_ollama_timeout(mocker):
    """Mock Ollama API timeout."""
    def mock_post_timeout(*args, **kwargs):
        import requests
        raise requests.Timeout("Connection timeout")

    return mocker.patch("requests.post", side_effect=mock_post_timeout)


@pytest.fixture
def mock_ollama_invalid_json(mocker):
    """Mock Ollama API returning invalid JSON."""
    def mock_post_invalid(*args, **kwargs):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "response": "not valid json {{"
        }
        return response

    return mocker.patch("requests.post", side_effect=mock_post_invalid)


@pytest.fixture
def mock_tesseract(mocker):
    """Mock Tesseract OCR."""
    return mocker.patch(
        "pytesseract.image_to_string",
        return_value="Mocked OCR text content"
    )


@pytest.fixture
def mock_tesseract_failure(mocker):
    """Mock Tesseract OCR failure."""
    import pytesseract
    return mocker.patch(
        "pytesseract.image_to_string",
        side_effect=pytesseract.TesseractNotFoundError("Tesseract not available")
    )


@pytest.fixture
def test_settings(mocker):
    """Override settings for testing."""
    test_config = {
        "api_key": "test-api-key",
        "rate_limit_requests": 100,
        "max_file_size_mb": 50,
        "enable_auth": True,
        "extraction_mode": "rules",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3",
        "sqlite_db_path": ":memory:",
        "json_output_dir": "/tmp/test_outputs",
        "tesseract_cmd": "/usr/bin/tesseract"
    }

    for key, value in test_config.items():
        mocker.patch.object(settings, key, value)

    return settings


@pytest.fixture
def client(test_settings):
    """FastAPI TestClient for endpoint testing."""
    return TestClient(app)


@pytest.fixture
def async_client(test_settings):
    """Async HTTP client for API testing."""
    try:
        import httpx
        return httpx.AsyncClient(app=app, base_url="http://test")
    except ImportError:
        pytest.skip("httpx not installed")


@pytest.fixture
def temp_db():
    """Temporary in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def temp_json_dir():
    """Temporary directory for JSON output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
