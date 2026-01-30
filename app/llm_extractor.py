"""LLM-based structured extraction using Ollama."""
import json
import re
import requests
from typing import Dict, Any, Optional
from app.config import settings
from app.schema import ExtractedData


def extract_with_llm(text: str) -> ExtractedData:
    """
    Extract structured data from text using Ollama LLM.
    
    Args:
        text: Cleaned text to extract from
        
    Returns:
        ExtractedData object with extracted fields
        
    Raises:
        Exception: If LLM request fails or response is invalid
    """
    prompt = _build_extraction_prompt(text)
    
    # Call Ollama API
    response = _call_ollama(prompt)
    
    # Parse JSON from response
    extracted_json = _parse_json_response(response)
    
    # Validate and return as ExtractedData
    return ExtractedData(**extracted_json)


def extract_with_rules(text: str) -> ExtractedData:
    """
    Extract structured data using regex and template matching.
    Fallback option when LLM is not available.
    
    Args:
        text: Cleaned text to extract from
        
    Returns:
        ExtractedData object with extracted fields
    """
    data = {
        "doc_type": _extract_doc_type(text),
        "vendor": _extract_vendor(text),
        "invoice_number": _extract_invoice_number(text),
        "invoice_date": _extract_date(text),
        "total_amount": _extract_total(text),
        "currency": _extract_currency(text),
        "line_items": []
    }
    
    return ExtractedData(**data)


def _build_extraction_prompt(text: str) -> str:
    """Build a prompt for the LLM to extract structured data."""
    return f"""You are a document parser. Extract structured information from the following document text and return ONLY valid JSON with no additional explanation.

Required JSON structure:
{{
  "doc_type": "invoice|receipt|contract|other",
  "vendor": "vendor/company name or null",
  "invoice_number": "invoice/document number or null",
  "invoice_date": "date in YYYY-MM-DD format or null",
  "total_amount": numeric value or null,
  "currency": "USD|EUR|GBP|etc or null",
  "line_items": [
    {{"description": "item description", "quantity": number or null, "unit_price": number or null, "total": number or null}}
  ]
}}

Document text:
{text[:3000]}

Return only the JSON object:"""


def _call_ollama(prompt: str) -> str:
    """
    Call Ollama API to generate a response.
    
    Args:
        prompt: The prompt to send to Ollama
        
    Returns:
        Generated text response
        
    Raises:
        Exception: If API call fails
    """
    url = f"{settings.ollama_base_url}/api/generate"
    
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ollama API call failed: {str(e)}")


def _parse_json_response(response: str) -> Dict[str, Any]:
    """
    Parse JSON from LLM response.
    
    Args:
        response: LLM generated text
        
    Returns:
        Parsed JSON dictionary
    """
    # Try to find JSON in the response
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    
    if json_match:
        json_str = json_match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # If direct parsing fails, try to clean and parse
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON from LLM response: {str(e)}")


# Rules-based extraction helpers

def _extract_doc_type(text: str) -> str:
    """Detect document type from text."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["invoice", "bill", "facture"]):
        return "invoice"
    elif any(word in text_lower for word in ["receipt", "reçu"]):
        return "receipt"
    elif any(word in text_lower for word in ["contract", "agreement"]):
        return "contract"
    else:
        return "other"


def _extract_vendor(text: str) -> Optional[str]:
    """Extract vendor/company name from text."""
    # Look for common patterns
    patterns = [
        r"(?:from|vendor|seller):\s*([A-Z][A-Za-z\s&.,]+?)(?:\n|$)",
        r"^([A-Z][A-Za-z\s&.,]{3,30})",  # First line often contains vendor
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            return match.group(1).strip()
    
    return None


def _extract_invoice_number(text: str) -> Optional[str]:
    """Extract invoice number from text."""
    patterns = [
        r"invoice\s*#?:?\s*([A-Z0-9-]+)",
        r"invoice\s+number:?\s*([A-Z0-9-]+)",
        r"#\s*([0-9]{4,})",
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None


def _extract_date(text: str) -> Optional[str]:
    """Extract date from text."""
    patterns = [
        r"(\d{4}-\d{2}-\d{2})",  # YYYY-MM-DD
        r"(\d{2}/\d{2}/\d{4})",  # MM/DD/YYYY
        r"(\d{2}-\d{2}-\d{4})",  # DD-MM-YYYY
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return None


def _extract_total(text: str) -> Optional[float]:
    """Extract total amount from text."""
    patterns = [
        r"total:?\s*\$?\s*([\d,]+\.?\d*)",
        r"amount:?\s*\$?\s*([\d,]+\.?\d*)",
        r"grand\s+total:?\s*\$?\s*([\d,]+\.?\d*)",
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(",", "")
            try:
                return float(amount_str)
            except ValueError:
                continue
    
    return None


def _extract_currency(text: str) -> str:
    """Extract currency from text."""
    if "$" in text or "usd" in text.lower():
        return "USD"
    elif "€" in text or "eur" in text.lower():
        return "EUR"
    elif "£" in text or "gbp" in text.lower():
        return "GBP"
    else:
        return "USD"  # Default
