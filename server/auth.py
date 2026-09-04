import os
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials

CALENDAR_API_TOKEN = os.getenv("CALENDAR_API_TOKEN", "default-token")

security = HTTPBearer()


def verify_token(credentials: HTTPAuthCredentials = Depends(security)) -> str:
    """Verify the Bearer token matches the configured API token."""
    if credentials.credentials != CALENDAR_API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")
    return credentials.credentials
