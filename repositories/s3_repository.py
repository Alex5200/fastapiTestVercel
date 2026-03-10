# repositories/s3_repository.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class S3Repository(ABC):
    @abstractmethod
    async def list_files(self, prefix: str = "") -> List[Dict[str, str | int]]:
        pass

    @abstractmethod
    async def upload_file(
        self,
        file_data: bytes,
        filename: str,
        content_type: Optional[str] = None,
    ) -> bool:
        pass

    @abstractmethod
    async def download_file(self, filename: str) -> Optional[bytes]:
        pass

    @abstractmethod
    async def delete_file(self, filename: str) -> bool:
        pass
