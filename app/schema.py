"""Pydantic schemas for data validation."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class LineItem(BaseModel):
    """Schema for a line item in a document."""
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None


class ExtractedData(BaseModel):
    """Schema for structured data extracted from a document."""
    doc_type: str = Field(..., description="Document type (e.g., invoice, receipt, contract)")
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = "USD"
    line_items: List[LineItem] = Field(default_factory=list)
    
    @field_validator('doc_type')
    @classmethod
    def validate_doc_type(cls, v):
        """Ensure doc_type is not empty."""
        if not v or not v.strip():
            raise ValueError("doc_type cannot be empty")
        return v.strip()


class DocumentMetadata(BaseModel):
    """Metadata for a processed document."""
    id: Optional[int] = None
    filename: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    extraction_mode: str
    status: str = "success"
    error_message: Optional[str] = None


class DocumentResponse(BaseModel):
    """Response model for document processing."""
    metadata: DocumentMetadata
    extracted_data: Optional[ExtractedData] = None
