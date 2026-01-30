"""FastAPI application with document processing endpoints."""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
import traceback

from app.config import settings
from app.schema import DocumentResponse, ExtractedData
from app.pipeline import process_document
from app.storage import storage

app = FastAPI(
    title="Document LLM Pipeline Demo",
    description="PDF document processing with AI-powered structured data extraction",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Document LLM Pipeline Demo",
        "version": "1.0.0",
        "endpoints": {
            "extract": "POST /extract - Process a PDF document",
            "documents": "GET /documents - List processed documents",
            "health": "GET /health - Check service health"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Returns current configuration and service status.
    """
    return {
        "status": "healthy",
        "mode": settings.extraction_mode,
        "model": settings.ollama_model if settings.extraction_mode == "llm" else "N/A",
        "ollama_url": settings.ollama_base_url if settings.extraction_mode == "llm" else "N/A"
    }


@app.post("/extract", response_model=DocumentResponse)
async def extract_document(
    file: UploadFile = File(..., description="PDF file to process"),
    mode: Optional[str] = Form(None, description="Extraction mode: 'llm' or 'rules'")
):
    """
    Extract structured data from an uploaded PDF document.
    
    Process flow:
    1. Upload PDF via multipart form
    2. Extract text (with OCR fallback for scanned docs)
    3. Extract structured fields using LLM or rules
    4. Validate with Pydantic schema
    5. Persist to SQLite and save JSON artifact
    6. Return structured data
    
    Args:
        file: PDF file upload
        mode: Override extraction mode (optional)
        
    Returns:
        DocumentResponse with metadata and extracted data
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Validate mode if provided
    if mode and mode not in ["llm", "rules"]:
        raise HTTPException(status_code=400, detail="Mode must be 'llm' or 'rules'")
    
    try:
        # Read file content
        pdf_bytes = await file.read()
        
        # Process through pipeline
        extracted_data = process_document(pdf_bytes, mode=mode)
        
        # Save to storage
        result = storage.save_document(
            filename=file.filename,
            extraction_mode=mode or settings.extraction_mode,
            extracted_data=extracted_data,
            status="success"
        )
        
        return result
        
    except Exception as e:
        # Log error and save failed document
        error_msg = str(e)
        print(f"Error processing document: {error_msg}")
        print(traceback.format_exc())
        
        result = storage.save_document(
            filename=file.filename,
            extraction_mode=mode or settings.extraction_mode,
            status="failed",
            error_message=error_msg
        )
        
        raise HTTPException(status_code=500, detail=f"Processing failed: {error_msg}")


@app.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    limit: int = 100,
    offset: int = 0
):
    """
    List processed documents with their metadata and extraction results.
    
    Args:
        limit: Maximum number of documents to return (default: 100)
        offset: Number of documents to skip for pagination (default: 0)
        
    Returns:
        List of DocumentResponse objects
    """
    try:
        documents = storage.get_documents(limit=limit, offset=offset)
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")


@app.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: int):
    """
    Retrieve a specific document by ID.
    
    Args:
        doc_id: Document ID
        
    Returns:
        DocumentResponse with metadata and extracted data
    """
    try:
        document = storage.get_document_by_id(doc_id)
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
        
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
