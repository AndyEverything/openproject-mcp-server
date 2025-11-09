from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="OPENPROJECT_")

    url: AnyHttpUrl = Field(..., description="e.g. https://openproject.example.com")
    api_key: str = Field(..., description="API key with API v3 access")

    connect_timeout: float = 10.0
    read_timeout: float = 10.0
    max_retries: int = 3
    page_size_default: int = 25
    page_size_max: int = 200
