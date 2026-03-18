from fastapi import APIRouter
from app.api.v1 import s3Api

api_router = APIRouter()

api_router.include_router(s3Api.rotes, tags={"s3"})
