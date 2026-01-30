"""Orchestrates the document processing pipeline."""
from typing import Tuple
from app.config import settings
from app.schema import ExtractedData
from app.ingest import extract_text_from_pdf
from app.llm_extractor import extract_with_llm, extract_with_rules


def process_document(pdf_bytes: bytes, mode: str = None) -> ExtractedData:
    """
    Process a PDF document through the complete pipeline.
    
    Steps:
    1. Extract text from PDF (with OCR fallback)
    2. Extract structured data using LLM or rules
    3. Validate with Pydantic schema
    
    Args:
        pdf_bytes: PDF file content as bytes
        mode: Extraction mode ("llm" or "rules"). Uses config default if None.
        
    Returns:
        ExtractedData object with validated structured data
        
    Raises:
        Exception: If any step in the pipeline fails
    """
    # Step 1: Text extraction
    print("Step 1: Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_bytes)
    
    if not text or len(text.strip()) < 10:
        raise Exception("Failed to extract sufficient text from PDF")
    
    print(f"Extracted {len(text)} characters of text")
    
    # Step 2: Structured extraction
    extraction_mode = mode or settings.extraction_mode
    print(f"Step 2: Extracting structured data using '{extraction_mode}' mode...")
    
    if extraction_mode == "llm":
        extracted_data = extract_with_llm(text)
    elif extraction_mode == "rules":
        extracted_data = extract_with_rules(text)
    else:
        raise ValueError(f"Invalid extraction mode: {extraction_mode}")
    
    # Step 3: Validation (already done by Pydantic in extract_with_* functions)
    print("Step 3: Validation complete")
    
    return extracted_data
