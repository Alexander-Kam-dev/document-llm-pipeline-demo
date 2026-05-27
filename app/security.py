"""Security utilities for API authentication and request tracing."""
import uuid
from typing import Optional
from fastapi import HTTPException, Request


def verify_api_key(api_key: str, expected_key: str) -> bool:
    """Verify that provided API key matches the expected key."""
    if not api_key or not expected_key:
        return False
    return api_key == expected_key


def get_request_id(request: Request) -> str:
    """Get or generate a request ID for tracing."""
    request_id = request.headers.get("X-Request-ID")
    if request_id:
        return request_id
    return str(uuid.uuid4())


async def authenticate_api_key(request: Request, api_key: str) -> Optional[str]:
    """
    Authenticate API key from request header.
    Returns request_id if authenticated, raises HTTPException otherwise.
    """
    request_id = get_request_id(request)

    auth_header = request.headers.get("X-API-Key")
    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide via X-API-Key header."
        )

    if not verify_api_key(auth_header, api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key."
        )

    return request_id
