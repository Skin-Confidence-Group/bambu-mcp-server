"""Configuration management for Bambu MCP Server."""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Bambu Cloud API credentials
    bambu_email: str
    bambu_password: str
    bambu_token: Optional[str] = None
    bambu_device_id: str = "0948BB5B1200532"

    # Server configuration
    port: int = 8000
    mcp_server_name: str = "bambu-printer"
    mcp_server_version: str = "0.1.0"

    # Setup security (optional - protects /setup endpoints)
    setup_key: Optional[str] = None

    # Railway environment detection
    railway_environment: Optional[str] = None

    @property
    def is_production(self) -> bool:
        """Check if running in Railway production."""
        return self.railway_environment is not None


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
