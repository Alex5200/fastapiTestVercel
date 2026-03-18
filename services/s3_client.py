import aioboto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from typing import List, Dict
from config import settings
import botocore.config

from exceptions import logger
from repositories.s3_repository import S3Repository


class S3Client(S3Repository):
    def __init__(self):
        self.session = aioboto3.Session()
        self.endpoint_url = f"https://{settings.get_s3_url()}"

    def _get_client(self):
        config = botocore.config.Config(
            connect_timeout=10,
            read_timeout=30,
            retries={"max_attempts": 3, "mode": "standard"},
        )

        return self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=config,
            verify=True,
        )

    async def getAll_files(self, prefix: str = "") -> List[dict]:
        """Return list all files in bucket with support pagination"""
        try:
            async with self._get_client() as s3:
                files = []
                continuation_token = None

                while True:
                    kwargs = {
                        "Bucket": settings.s3_bucket,
                        "Prefix": prefix,
                        "MaxKeys": 1000,
                    }
                    if continuation_token:
                        kwargs["ContinuationToken"] = continuation_token

                    response = await s3.list_objects_v2(**kwargs)

                    # add object in List
                    for obj in response.get("Contents", []):
                        files.append(
                            {
                                "filename": obj["Key"],
                                "size": obj["Size"],
                                "last_modified": obj["LastModified"].isoformat(),
                            }
                        )

                    if not response.get("IsTruncated"):
                        break
                    continuation_token = response.get("NextContinuationToken")

                return files

        except ClientError as e:
            logger.error(f"S3 list error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve file list",
            )

    async def upload_file(
        self, file_data: bytes, filename: str, content_type: str = "application/pdf"
    ) -> str:
        try:
            async with self._get_client() as s3:
                await s3.put_object(
                    Bucket=settings.s3_bucket,
                    Key=filename,
                    Body=file_data,
                    ContentType=content_type,
                )
                return filename
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 upload error: {str(e)}",
            )

    async def download_file(self, filename: str) -> bytes:
        try:
            async with self._get_client() as s3:
                response = await s3.get_object(Bucket=settings.s3_bucket, Key=filename)
                return await response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File '{filename}' not found",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 download error: {str(e)}",
            )

    async def delete_file(self, filename: str) -> bool:
        try:
            async with self._get_client() as s3:
                await s3.delete_object(Bucket=settings.s3_bucket, Key=filename)
                return True
        except ClientError as e:
            logger.error(f"S3 delete error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 delete error: {str(e)}",
            )

    async def list_files(self, prefix: str = "", max_keys: int = 1000) -> List[Dict]:
        try:
            async with self._get_client() as s3:
                files = []
                continuation_token = None

                while True:
                    kwargs = {
                        "Bucket": settings.s3_bucket,
                        "Prefix": prefix,
                        "MaxKeys": max_keys,
                    }
                    if continuation_token:
                        kwargs["ContinuationToken"] = continuation_token

                    response = await s3.list_objects_v2(**kwargs)

                    for obj in response.get("Contents", []):
                        files.append(
                            {
                                "filename": obj["Key"],
                                "size": obj["Size"],
                                "last_modified": obj["LastModified"].isoformat(),
                            }
                        )

                    if not response.get("IsTruncated"):
                        break
                    continuation_token = response.get("NextContinuationToken")

                return files
        except ClientError as e:
            logger.error(f"S3 list error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="S3 list error",
            )


s3_client = S3Client()
