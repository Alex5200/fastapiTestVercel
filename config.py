# config.py
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os


class Settings(BaseSettings):
    # S3
    s3_endpoint: str = Field(default="localhost")
    #s3_port: int = Field(default=9000)
    s3_region: str = Field(default="us-east-1")
    s3_bucket: str = Field(default="my-bucket")
    s3_access_key: str = Field(default="")
    s3_secret_key: str = Field(default="")
    s3_use_ssl: bool = Field(default=True)

    # API Keys
    api_keys_raw: str = Field(default="", alias="API_KEYS")
    api_master_key: Optional[str] = Field(default=None)

    # Logging
    log_level: str = Field(default="INFO")
    log_json: bool = Field(default=True)

    # Security
    max_file_size: int = Field(default=10 * 1024 * 1024)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,

    )

    @field_validator("api_keys_raw", mode="before")
    @classmethod
    def parse_api_keys_raw(cls, v):
        if v is None:
            return ""
        return str(v)

    @property
    def api_keys(self) -> List[str]:
        if not self.api_keys_raw:
            return []
        return [key.strip() for key in self.api_keys_raw.split(",") if key.strip()]

    def get_s3_url(self) -> str:
        return f"{self.s3_endpoint}"

    def is_valid_key(self, key: str) -> bool:
        if not key:
            return False
        if key in self.api_keys:
            return True
        if self.api_master_key and key == self.api_master_key:
            return True
        return False


settings = Settings()