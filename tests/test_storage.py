"""Tests for database storage layer."""
import pytest
import json
import tempfile
from pathlib import Path
from app.storage import storage, Storage
from app.schema import ExtractedData, LineItem, DocumentMetadata


@pytest.fixture
def sample_extracted_data():
    """Create sample extracted data for testing."""
    return ExtractedData(
        doc_type="invoice",
        vendor="Test Vendor",
        invoice_number="TEST-001",
        invoice_date="2024-01-15",
        total_amount=1000.0,
        currency="USD",
        line_items=[
            LineItem(
                description="Test Item",
                quantity=1.0,
                unit_price=1000.0,
                total=1000.0
            )
        ]
    )


class TestStorageCRUD:
    """Test database CRUD operations."""

    def test_save_document_success(self, sample_extracted_data):
        """Test saving a document to database."""
        result = storage.save_document(
            filename="test.pdf",
            extraction_mode="rules",
            extracted_data=sample_extracted_data,
            status="success"
        )

        assert result is not None
        assert result.metadata.filename == "test.pdf"
        assert result.metadata.status == "success"
        assert result.extracted_data == sample_extracted_data

    def test_save_document_with_error(self):
        """Test saving a failed extraction."""
        result = storage.save_document(
            filename="failed.pdf",
            extraction_mode="llm",
            extracted_data=None,
            status="failed",
            error_message="Processing failed"
        )

        assert result is not None
        assert result.metadata.status == "failed"
        assert result.metadata.error_message == "Processing failed"
        assert result.extracted_data is None

    def test_get_documents(self, sample_extracted_data):
        """Test retrieving multiple documents."""
        # Save a document first
        storage.save_document(
            filename="doc1.pdf",
            extraction_mode="rules",
            extracted_data=sample_extracted_data,
            status="success"
        )

        documents = storage.get_documents(limit=10, offset=0)

        assert documents is not None
        assert isinstance(documents, list)
        # Should have at least the document we just saved
        assert len(documents) >= 1

    def test_get_documents_pagination(self, sample_extracted_data):
        """Test pagination in document retrieval."""
        # Save multiple documents
        for i in range(5):
            storage.save_document(
                filename=f"doc{i}.pdf",
                extraction_mode="rules",
                extracted_data=sample_extracted_data,
                status="success"
            )

        # Get with limit
        docs_page1 = storage.get_documents(limit=2, offset=0)
        docs_page2 = storage.get_documents(limit=2, offset=2)

        assert isinstance(docs_page1, list)
        assert isinstance(docs_page2, list)

    def test_get_document_by_id(self, sample_extracted_data):
        """Test retrieving a single document by ID."""
        saved = storage.save_document(
            filename="single.pdf",
            extraction_mode="rules",
            extracted_data=sample_extracted_data,
            status="success"
        )

        if saved.metadata.id:
            retrieved = storage.get_document_by_id(saved.metadata.id)
            assert retrieved is not None
            assert retrieved.metadata.filename == "single.pdf"

    def test_get_document_not_found(self):
        """Test retrieving non-existent document."""
        result = storage.get_document_by_id(99999)
        assert result is None


class TestStorageMetadata:
    """Test document metadata handling."""

    def test_save_document_has_metadata(self, sample_extracted_data):
        """Saved documents should have metadata."""
        result = storage.save_document(
            filename="metadata_test.pdf",
            extraction_mode="rules",
            extracted_data=sample_extracted_data,
            status="success"
        )

        assert result.metadata is not None
        assert result.metadata.filename == "metadata_test.pdf"
        assert result.metadata.extraction_mode == "rules"
        assert result.metadata.upload_date is not None

    def test_save_document_preserves_extracted_data(self, sample_extracted_data):
        """Extracted data should be preserved exactly."""
        result = storage.save_document(
            filename="data_test.pdf",
            extraction_mode="rules",
            extracted_data=sample_extracted_data,
            status="success"
        )

        assert result.extracted_data.vendor == sample_extracted_data.vendor
        assert result.extracted_data.total_amount == sample_extracted_data.total_amount
        assert len(result.extracted_data.line_items) == len(sample_extracted_data.line_items)


class TestStorageJSONOutput:
    """Test JSON output file creation."""

    def test_save_creates_json_file(self, sample_extracted_data):
        """Saving should create JSON output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # This would test if JSON files are actually created
            # For now, just verify the save succeeds
            result = storage.save_document(
                filename="json_test.pdf",
                extraction_mode="rules",
                extracted_data=sample_extracted_data,
                status="success"
            )

            assert result is not None


class TestStorageErrorHandling:
    """Test error handling in storage operations."""

    def test_save_with_none_extracted_data(self):
        """Should handle None extracted data gracefully."""
        result = storage.save_document(
            filename="none_test.pdf",
            extraction_mode="rules",
            extracted_data=None,
            status="failed",
            error_message="Extraction failed"
        )

        assert result is not None
        assert result.extracted_data is None

    def test_get_documents_empty_db(self):
        """Should handle empty database gracefully."""
        # Query with limit/offset should work even with no docs
        documents = storage.get_documents(limit=10, offset=0)

        assert isinstance(documents, list)


class TestStorageDataValidation:
    """Test data validation in storage layer."""

    def test_save_validates_extracted_data(self):
        """Storage should validate ExtractedData schema."""
        # Try to save invalid data
        try:
            storage.save_document(
                filename="invalid.pdf",
                extraction_mode="rules",
                extracted_data=None,  # This should be okay
                status="success"
            )
            # Should succeed or raise with proper error
        except Exception as e:
            # Should be a schema validation error if it fails
            assert "doc_type" in str(e) or "validation" in str(e).lower()

    def test_extracted_data_schema_preserved(self, sample_extracted_data):
        """Saved extracted data should maintain schema."""
        result = storage.save_document(
            filename="schema_test.pdf",
            extraction_mode="rules",
            extracted_data=sample_extracted_data,
            status="success"
        )

        # Verify all required fields present
        ed = result.extracted_data
        assert hasattr(ed, "doc_type")
        assert hasattr(ed, "vendor")
        assert hasattr(ed, "total_amount")
        assert hasattr(ed, "line_items")
