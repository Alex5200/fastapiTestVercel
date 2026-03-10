from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.security import APIKeyHeader
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from services import s3_client
from middleware import LoggingMiddleware, SecurityHeadersMiddleware
from exceptions import global_exception_handler, validation_exception_handler
from fastapi.exceptions import RequestValidationError
import io
import uuid
import logging
from datetime import datetime

logging.basicConfig(format="%(message)s", level=settings.log_level, stream=sys.stdout)

logger = logging.getLogger("api")

app = FastAPI(title="PDF Storage API", version="1.0.0")

app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

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


@app.get("/health")
async def health_check(request: Request):
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/v1/files/all")
async def getAllFiles(
    request: Request, api_key: Annotated[str, Depends(get_api_key)] = None
):
    try:
        data = await s3_client.getAll_files()
        print(data)
        return data
    except Exception as e:
        logger(f"Error getAllFiles {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Server error"
        )


@app.post("/api/v1/files/upload")
async def upload_pdf(
    request: Request,
    file: UploadFile = File(...),
    api_key: Annotated[str, Depends(get_api_key)] = None,
):
    if file.content_type not in ["application/pdf"]:
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    content = await file.read()

    if len(content) > settings.max_file_size:
        raise HTTPException(status_code=400, detail="File too large")

    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Invalid PDF content")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"pdf/{timestamp}_{unique_id}_{file.filename}"

    await s3_client.upload_file(content, filename, file.content_type)

    return {"message": "Uploaded", "filename": filename, "size": len(content)}


@app.get("/api/v1/files/{filename:path}")
async def download_pdf(
    request: Request,
    filename: str,
    api_key: Annotated[str, Depends(get_api_key)] = None,
):
    content = await s3_client.download_file(filename)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename.split('/')[-1]}"
        },
    )


@app.get("/api/v1/files")
async def list_files(
    request: Request,
    prefix: str = "pdf/",
    api_key: Annotated[str, Depends(get_api_key)] = None,
):
    files = await s3_client.list_files(prefix)
    return {"count": len(files), "files": files}


@app.delete("/api/v1/files/{filename:path}")
async def delete_pdf(
    request: Request,
    filename: str,
    api_key: Annotated[str, Depends(get_api_key)] = None,
):
    await s3_client.delete_file(filename)
    return {"message": "File deleted", "filename": filename}