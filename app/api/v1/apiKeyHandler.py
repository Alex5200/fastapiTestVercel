from fastapi.security import APIKeyHeader
from fastapi import Request, Depends, HTTPException
from typing import Annotated

from starlette import status

from config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(
    request: Request, api_key: Annotated[str | None, Depends(api_key_header)]
) -> str:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key header missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    if not settings.is_valid_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key
