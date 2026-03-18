from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

from app.api.v1.router import api_router

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from middleware import LoggingMiddleware, SecurityHeadersMiddleware
from exceptions import global_exception_handler, validation_exception_handler
from fastapi.exceptions import RequestValidationError
from datetime import datetime


app = FastAPI(title="PDF Storage API", version="1.0.0", description="Приложение для хранения PDF файлов с поддержкой S3 и API ключей")
app.include_router(api_router)

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


@app.get("/health")
async def health_check(request: Request):
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
