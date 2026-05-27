"""Tests for edge cases and error scenarios."""
import pytest
from app.pipeline import process_document
from app.ingest import extract_text_from_pdf
from app.llm_extractor import extract_with_llm, extract_with_rules


class TestPDFEdgeCases:
    """Test PDF processing edge cases."""

    def test_empty_pdf(self):
        """Test handling of empty PDF."""
        empty_pdf = b"%PDF-1.4\n"
        text = extract_text_from_pdf(empty_pdf)

        assert text is not None
        assert isinstance(text, str)

    def test_malformed_pdf(self):
        """Test handling of corrupted/malformed PDF."""
        malformed = b"This is not a PDF at all"
        text = extract_text_from_pdf(malformed)

        # Should handle gracefully, returning empty or error text
        assert text is not None
        assert isinstance(text, str)

    def test_very_large_pdf_content(self):
        """Test handling of very large PDF."""
        # Create fake large PDF
        large_pdf = b"%PDF-1.4\n" + (b"A" * (100 * 1024))
        text = extract_text_from_pdf(large_pdf)

        assert text is not None
        assert isinstance(text, str)


class TestTextExtractionEdgeCases:
    """Test text extraction error handling."""

    def test_extract_from_binary_garbage(self):
        """Test extraction from binary garbage."""
        garbage = b"\x00\x01\x02\x03\xFF\xFE\xFD" * 100
        text = extract_text_from_pdf(garbage)

        assert text is not None

    def test_extract_empty_bytes(self):
        """Test extraction from empty bytes."""
        text = extract_text_from_pdf(b"")

        assert text is not None


class TestLLMExtractionEdgeCases:
    """Test LLM extraction error handling."""

    def test_extract_with_llm_empty_text(self, mock_ollama):
        """Test LLM extraction with empty input."""
        result = extract_with_llm("")

        assert result is not None
        # Should fall back gracefully

    def test_extract_with_llm_very_long_text(self, mock_ollama):
        """Test LLM extraction with very long text."""
        long_text = "Invoice content " * 10000
        result = extract_with_llm(long_text)

        assert result is not None

    def test_extract_with_llm_special_characters(self, mock_ollama):
        """Test LLM extraction with special characters."""
        text_with_special = "Vendor: Über Café™ © 2024\nTotal: €1,250.50\nDate: 2024-01-15"
        result = extract_with_llm(text_with_special)

        assert result is not None


class TestRulesExtractionEdgeCases:
    """Test rules-based extraction edge cases."""

    def test_extract_with_rules_empty_text(self):
        """Test rules extraction with empty text."""
        result = extract_with_rules("")

        assert result is not None
        assert result.doc_type is not None

    def test_extract_with_rules_no_recognized_fields(self):
        """Test rules extraction when no fields match."""
        random_text = "Lorem ipsum dolor sit amet consectetur adipiscing elit"
        result = extract_with_rules(random_text)

        assert result is not None
        # Should still produce a valid ExtractedData

    def test_extract_with_rules_partial_data(self):
        """Test rules extraction with only some fields present."""
        partial_text = "Vendor: ACME Corp\nDate: 2024-01-15"
        result = extract_with_rules(partial_text)

        assert result.vendor == "ACME Corp"
        assert result.invoice_date == "2024-01-15"
        # Other fields may be None


class TestPipelineEdgeCases:
    """Test full pipeline with edge cases."""

    def test_process_empty_pdf(self):
        """Test processing empty PDF."""
        empty_pdf = b"%PDF-1.4\n"
        result = process_document(empty_pdf, mode="rules")

        assert result is not None

    def test_process_malformed_pdf(self):
        """Test processing malformed PDF."""
        malformed = b"Not a PDF"
        result = process_document(malformed, mode="rules")

        assert result is not None

    def test_process_document_with_timeout_mock(self, sample_invoice_bytes, mock_ollama_timeout):
        """Test pipeline handles LLM timeout."""
        # When LLM times out, should fall back
        result = process_document(sample_invoice_bytes, mode="llm")

        assert result is not None
        # Should have fallen back successfully

    def test_process_document_with_invalid_json_mock(self, sample_invoice_bytes, mock_ollama_invalid_json):
        """Test pipeline handles invalid JSON from LLM."""
        result = process_document(sample_invoice_bytes, mode="llm")

        assert result is not None
        # Should handle gracefully


class TestDataValidationEdgeCases:
    """Test data validation edge cases."""

    def test_extract_with_invalid_amounts(self):
        """Test extraction with invalid amount formats."""
        text = "Total: not_a_number\nVendor: Test Co"
        result = extract_with_rules(text)

        # Should handle gracefully
        assert result is not None
        # Amount may be None

    def test_extract_with_invalid_dates(self):
        """Test extraction with invalid date formats."""
        text = "Date: invalid_date\nTotal: $100"
        result = extract_with_rules(text)

        assert result is not None

    def test_extract_with_special_amount_formats(self):
        """Test extraction with various amount formats."""
        text = "Total: 1,250.50 USD\nVendor: Test"
        result = extract_with_rules(text)

        assert result is not None
        if result.total_amount:
            assert isinstance(result.total_amount, float)


class TestConcurrencyEdgeCases:
    """Test concurrent/sequential processing."""

    def test_process_multiple_documents_sequentially(self, sample_invoice_bytes, sample_receipt_bytes):
        """Test processing multiple documents in sequence."""
        result1 = process_document(sample_invoice_bytes, mode="rules")
        result2 = process_document(sample_receipt_bytes, mode="rules")

        assert result1 is not None
        assert result2 is not None

    def test_process_same_document_multiple_times(self, sample_invoice_bytes):
        """Test processing the same document multiple times."""
        result1 = process_document(sample_invoice_bytes, mode="rules")
        result2 = process_document(sample_invoice_bytes, mode="rules")

        assert result1 is not None
        assert result2 is not None
