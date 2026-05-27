"""Basic tests for the document processing pipeline."""
import pytest
from app.schema import ExtractedData, LineItem
from app.llm_extractor import extract_with_rules
from app.ingest import extract_text_from_pdf, clean_text
from app.pipeline import process_document
import requests


def test_schema_validation():
    """Test that Pydantic schema validation works."""
    # Valid data
    data = ExtractedData(
        doc_type="invoice",
        vendor="Test Corp",
        invoice_number="INV-001",
        invoice_date="2024-01-01",
        total_amount=100.00,
        currency="USD",
        line_items=[]
    )
    assert data.doc_type == "invoice"
    assert data.vendor == "Test Corp"
    assert data.total_amount == 100.00


def test_schema_validation_fails_empty_doc_type():
    """Test that empty doc_type raises validation error."""
    with pytest.raises(ValueError):
        ExtractedData(
            doc_type="",
            vendor="Test Corp"
        )


def test_line_item_schema():
    """Test LineItem schema."""
    item = LineItem(
        description="Test item",
        quantity=2.0,
        unit_price=50.0,
        total=100.0
    )
    assert item.description == "Test item"
    assert item.quantity == 2.0


def test_rules_extractor():
    """Test rules-based extraction."""
    sample_text = """
    INVOICE
    Acme Corporation
    123 Business St

    Invoice Number: INV-2024-001
    Date: 2024-01-15

    Professional Services    $1,000.00

    Total: $1,000.00
    """

    result = extract_with_rules(sample_text)

    assert result.doc_type == "invoice"
    assert result.vendor == "Acme Corporation"
    assert result.invoice_number is not None
    assert result.invoice_date == "2024-01-15"
    assert result.total_amount == 1000.0
    assert result.currency == "USD"


# Text Extraction Tests

def test_extract_text_from_pdf_native(sample_invoice_bytes):
    """Test native text extraction from PDF with embedded text."""
    text = extract_text_from_pdf(sample_invoice_bytes)
    assert text is not None
    assert len(text) > 0
    assert isinstance(text, str)


def test_extract_text_from_pdf_empty():
    """Test handling of empty/invalid PDF."""
    empty_pdf = b"%PDF-1.4\n"
    result = extract_text_from_pdf(empty_pdf)
    assert result is not None
    assert isinstance(result, str)


def test_clean_text():
    """Test text normalization."""
    dirty_text = "  Invoice  \n\n  Acme   Corp  \t\t123 Main St  "
    clean = clean_text(dirty_text)

    assert clean is not None
    assert len(clean) < len(dirty_text)
    assert "\n\n" not in clean
    assert "\t" not in clean


def test_clean_text_with_special_chars():
    """Test cleaning text with special characters."""
    text_with_special = "Price: $1,250.00\nVendor: Acme® Corp™"
    clean = clean_text(text_with_special)

    assert clean is not None
    assert len(clean) > 0


# LLM Extraction Tests

def test_extract_with_llm_success(mock_ollama):
    """Test successful LLM extraction with mocked Ollama."""
    from app.llm_extractor import extract_with_llm

    sample_text = "Vendor: Test Company\nTotal: $500.00\nDate: 2024-01-15"
    result = extract_with_llm(sample_text)

    assert result is not None
    assert result.doc_type == "invoice"
    assert result.vendor == "Test Vendor"


def test_extract_with_llm_timeout(mock_ollama_timeout):
    """Test LLM extraction timeout handling."""
    from app.llm_extractor import extract_with_llm

    sample_text = "Vendor: Test Company"

    # Should fall back to rules when LLM times out
    result = extract_with_llm(sample_text)
    assert result is not None
    # Rules extractor should handle it


def test_extract_with_llm_invalid_json(mock_ollama_invalid_json):
    """Test LLM extraction with invalid JSON response."""
    from app.llm_extractor import extract_with_llm

    sample_text = "Vendor: Test Company\nTotal: $500.00"

    # Should handle gracefully
    result = extract_with_llm(sample_text)
    assert result is not None


def test_extract_with_rules_various_formats():
    """Test rules extraction with different text formats."""
    # Invoice format
    invoice_text = "Total Amount: $1250\nVendor: ACME Corp\nDate: 2024-01-15"
    result = extract_with_rules(invoice_text)
    assert result.total_amount == 1250.0

    # Receipt format
    receipt_text = "Total: $17.01\nDate: 01/30/2024"
    result = extract_with_rules(receipt_text)
    assert result is not None


# Pipeline Integration Tests

def test_process_document_rules_mode(sample_invoice_bytes):
    """Test full pipeline with rules extraction mode."""
    result = process_document(sample_invoice_bytes, mode="rules")

    assert result is not None
    assert isinstance(result, ExtractedData)
    assert result.doc_type in ["invoice", "receipt", "contract"]


def test_process_document_invalid_mode(sample_invoice_bytes):
    """Test pipeline with invalid extraction mode."""
    with pytest.raises(ValueError):
        process_document(sample_invoice_bytes, mode="invalid")


def test_process_document_with_mock_llm(sample_invoice_bytes, mock_ollama):
    """Test pipeline with mocked LLM extraction."""
    result = process_document(sample_invoice_bytes, mode="llm")

    assert result is not None
    assert isinstance(result, ExtractedData)
    assert result.vendor == "Test Vendor"


def test_process_document_result_structure(sample_invoice_bytes):
    """Test that pipeline result has required fields."""
    result = process_document(sample_invoice_bytes, mode="rules")

    assert hasattr(result, "doc_type")
    assert hasattr(result, "vendor")
    assert hasattr(result, "invoice_date")
    assert hasattr(result, "total_amount")
    assert hasattr(result, "currency")
    assert hasattr(result, "line_items")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

