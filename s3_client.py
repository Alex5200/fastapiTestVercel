# s3_client.py
import aioboto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from typing import List, Dict
from config import settings


class S3Client:
    def __init__(self):
        self.session = aioboto3.Session()
        protocol = "https" if settings.s3_use_ssl else "http"
        self.endpoint_url = f"{protocol}://{settings.get_s3_url()}"

    def _get_client(self):
        return self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            use_ssl=settings.s3_use_ssl
        )

    async def upload_file(self, file_data: bytes, filename: str, content_type: str = "application/pdf") -> str:
        try:
            async with self._get_client() as s3:
                await s3.put_object(
                    Bucket=settings.s3_bucket,
                    Key=filename,
                    Body=file_data,
                    ContentType=content_type
                )
                return filename
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 upload error: {str(e)}"
            )

    async def download_file(self, filename: str) -> bytes:
        try:
            async with self._get_client() as s3:
                response = await s3.get_object(
                    Bucket=settings.s3_bucket,
                    Key=filename
                )
                return await response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File '{filename}' not found"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 download error: {str(e)}"
            )

    async def delete_file(self, filename: str) -> bool:
        try:
            async with self._get_client() as s3:
                await s3.delete_object(
                    Bucket=settings.s3_bucket,
                    Key=filename
                )
                return True
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 delete error: {str(e)}"
            )

    async def list_files(self, prefix: str = "") -> List[Dict]:
        try:
            async with self._get_client() as s3:
                response = await s3.list_objects_v2(
                    Bucket=settings.s3_bucket,
                    Prefix=prefix
                )
                files = []
                for obj in response.get('Contents', []):
                    files.append({
                        'filename': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat()
                    })
                return files
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 list error: {str(e)}"
            )


s3_client = S3Client()