"""Basic tests for the document processing pipeline."""
import pytest
from app.schema import ExtractedData, LineItem
from app.llm_extractor import extract_with_rules


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
