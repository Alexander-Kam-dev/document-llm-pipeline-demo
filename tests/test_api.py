"""Integration tests for FastAPI endpoints."""
import pytest
import json
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestAuthentication:
    """Test API key authentication."""

    def test_health_no_auth_required(self, client):
        """Health endpoint should not require authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()

    def test_root_without_api_key(self, client):
        """Root endpoint without API key should return 401."""
        response = client.get("/")
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "API key" in data["error"]

    def test_root_with_invalid_api_key(self, client):
        """Root endpoint with invalid API key should return 401."""
        response = client.get("/", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "Invalid API key" in data["error"]

    def test_root_with_valid_api_key(self, client):
        """Root endpoint with valid API key should return 200."""
        # Use the test API key from config
        response = client.get("/", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data


class TestResponseEnvelopes:
    """Test response envelope structure."""

    def test_success_response_structure(self, client):
        """Success responses should have envelope with success=true."""
        response = client.get("/", headers={"X-API-Key": "test-api-key"})
        data = response.json()

        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        assert "request_id" in data
        assert data["request_id"] is not None

    def test_error_response_structure(self, client):
        """Error responses should have envelope with success=false."""
        response = client.get("/", headers={"X-API-Key": "wrong-key"})
        data = response.json()

        assert "success" in data
        assert data["success"] is False
        assert "error" in data
        assert "request_id" in data

    def test_request_id_generation(self, client):
        """Request ID should be generated automatically."""
        response = client.get("/", headers={"X-API-Key": "test-api-key"})
        data = response.json()

        request_id = data.get("request_id")
        assert request_id is not None
        assert len(request_id) > 0

    def test_custom_request_id_passthrough(self, client):
        """Custom request ID should pass through."""
        custom_id = "custom-request-123"
        response = client.get(
            "/",
            headers={
                "X-API-Key": "test-api-key",
                "X-Request-ID": custom_id
            }
        )
        data = response.json()
        assert data["request_id"] == custom_id


class TestFileSizeLimit:
    """Test file size limiting."""

    def test_extract_file_within_limit(self, client, sample_invoice_bytes):
        """File within size limit should be accepted."""
        response = client.post(
            "/extract",
            files={"file": ("test.pdf", sample_invoice_bytes)},
            headers={"X-API-Key": "test-api-key"}
        )
        # Should succeed (or fail with processing error, not size error)
        assert response.status_code in [200, 500]

    def test_extract_file_exceeds_limit(self, client):
        """File exceeding size limit should return 413."""
        # Create a fake PDF larger than 50MB
        large_pdf = b"%PDF-1.4\n" + (b"X" * (51 * 1024 * 1024))

        response = client.post(
            "/extract",
            files={"file": ("large.pdf", large_pdf)},
            headers={"X-API-Key": "test-api-key"}
        )
        assert response.status_code == 413
        data = response.json()
        assert data["success"] is False
        assert "exceeds limit" in data["error"]


class TestDocumentListing:
    """Test document listing endpoints."""

    def test_list_documents_requires_auth(self, client):
        """Listing documents should require authentication."""
        response = client.get("/documents")
        assert response.status_code == 401

    def test_list_documents_with_auth(self, client):
        """Listing documents with auth should return success."""
        response = client.get(
            "/documents",
            headers={"X-API-Key": "test-api-key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_list_documents_pagination(self, client):
        """Pagination parameters should be accepted."""
        response = client.get(
            "/documents?limit=10&offset=0",
            headers={"X-API-Key": "test-api-key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["data"], list)


class TestExtractEndpoint:
    """Test document extraction endpoint."""

    def test_extract_requires_auth(self, client, sample_invoice_bytes):
        """Extract endpoint should require authentication."""
        response = client.post(
            "/extract",
            files={"file": ("test.pdf", sample_invoice_bytes)}
        )
        assert response.status_code == 401

    def test_extract_requires_pdf(self, client):
        """Extract endpoint should reject non-PDF files."""
        response = client.post(
            "/extract",
            files={"file": ("test.txt", b"not a pdf")},
            headers={"X-API-Key": "test-api-key"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "PDF" in data["error"]

    def test_extract_invalid_mode(self, client, sample_invoice_bytes):
        """Extract endpoint should reject invalid extraction mode."""
        response = client.post(
            "/extract",
            files={"file": ("test.pdf", sample_invoice_bytes)},
            data={"mode": "invalid"},
            headers={"X-API-Key": "test-api-key"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "mode" in data["error"].lower()

    def test_extract_valid_request(self, client, sample_invoice_bytes):
        """Valid extraction request should succeed."""
        response = client.post(
            "/extract",
            files={"file": ("test.pdf", sample_invoice_bytes)},
            data={"mode": "rules"},
            headers={"X-API-Key": "test-api-key"}
        )
        assert response.status_code in [200, 500]
        data = response.json()
        # Should have envelope structure
        assert "success" in data
        assert "request_id" in data


class TestDocumentRetrieval:
    """Test document retrieval endpoint."""

    def test_get_document_requires_auth(self, client):
        """Document retrieval should require authentication."""
        response = client.get("/documents/1")
        assert response.status_code == 401

    def test_get_document_not_found(self, client):
        """Non-existent document should return 404."""
        response = client.get(
            "/documents/99999",
            headers={"X-API-Key": "test-api-key"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["error"].lower()

    def test_get_document_with_auth(self, client):
        """Valid document ID request should return proper envelope."""
        response = client.get(
            "/documents/1",
            headers={"X-API-Key": "test-api-key"}
        )
        # 404 or 200 depending on DB
        assert response.status_code in [200, 404]
        data = response.json()
        assert "success" in data
        assert "request_id" in data
