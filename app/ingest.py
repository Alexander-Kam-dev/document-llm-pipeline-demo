"""PDF text extraction with OCR fallback."""
import io
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from typing import Optional
from app.config import settings


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from a PDF. Uses pdfplumber for native text,
    falls back to Tesseract OCR if insufficient text is found.
    
    Args:
        pdf_bytes: PDF file content as bytes
        
    Returns:
        Extracted text as string
    """
    # Try native text extraction first
    text = _extract_with_pdfplumber(pdf_bytes)
    
    # If we got very little text, it's likely a scanned PDF
    if len(text.strip()) < 50:
        print("Low text content detected, falling back to OCR...")
        text = _extract_with_ocr(pdf_bytes)
    
    return clean_text(text)


def _extract_with_pdfplumber(pdf_bytes: bytes) -> str:
    """Extract text using pdfplumber."""
    text_parts = []
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    
    return "\n".join(text_parts)


def _extract_with_ocr(pdf_bytes: bytes) -> str:
    """Extract text using Tesseract OCR."""
    # Set tesseract command path
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    
    text_parts = []
    
    # Convert PDF to images
    images = convert_from_bytes(pdf_bytes)
    
    for image in images:
        # Run OCR on each page
        page_text = pytesseract.image_to_string(image)
        text_parts.append(page_text)
    
    return "\n".join(text_parts)


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    lines = [line.strip() for line in text.split('\n')]
    lines = [line for line in lines if line]
    
    # Join with single newlines
    cleaned = '\n'.join(lines)
    
    return cleaned
