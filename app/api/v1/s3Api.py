import sys
import logging

from fastapi import APIRouter, Request, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse

from starlette import status

from api.v1.filename import filenames
from config import settings
from typing import Annotated
from api.v1.apiKeyHandler import get_api_key
from services import s3_client
import io

logging.basicConfig(format="%(message)s", level=settings.log_level, stream=sys.stdout)

logger = logging.getLogger("api")

rotes = APIRouter(prefix="/s3")


@rotes.get("files/all")
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


@rotes.post("/files/upload")
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

    filename = filenames(file)

    await s3_client.upload_file(content, filename, file.content_type)

    return {"message": "Uploaded", "filename": filename, "size": len(content)}


@rotes.get("/files/{filename:path}")
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


@rotes.get("/files")
async def list_files(
    request: Request,
    prefix: str = "pdf/",
    api_key: Annotated[str, Depends(get_api_key)] = None,
):
    files = await s3_client.list_files(prefix)
    return {"count": len(files), "files": files}


@rotes.delete("/files/{filename:path}")
async def delete_pdf(
    request: Request,
    filename: str,
    api_key: Annotated[str, Depends(get_api_key)] = None,
):
    await s3_client.delete_file(filename)
    return {"message": "File deleted", "filename": filename}
