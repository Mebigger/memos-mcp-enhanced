"""Configuration management for Memos MCP server."""
import os
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def find_env_file() -> Optional[str]:
    """
    Find .env file in common locations.
    
    Search order:
    1. Current working directory
    2. Package directory's parent (for local development)
    
    Returns None if not found (will rely on environment variables only).
    """
    # Check current working directory
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        return str(cwd_env)
    
    # Check package directory's parent (for local development)
    # This handles: project_root/memos_mcp/config.py -> project_root/.env
    package_dir = Path(__file__).parent.parent / ".env"
    if package_dir.exists():
        return str(package_dir)
    
    return None


class Settings(BaseSettings):
    """Memos MCP server settings."""

    # Note: env_prefix="MEMOS_" means all env vars should be prefixed with MEMOS_
    # e.g., instance_url -> MEMOS_INSTANCE_URL, api_token -> MEMOS_API_TOKEN
    # Priority: Environment variables > .env file > defaults
    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_prefix="MEMOS_",
        extra="ignore",
    )

    instance_url: str = Field(
        default="http://localhost:8080",
        description="Base URL of the Memos instance",
    )
    api_token: str = Field(
        default="",
        description="API token for authentication",
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
    )
    character_limit: int = Field(
        default=25000,
        description="Maximum number of characters in responses",
    )
    default_page_size: int = Field(
        default=20,
        description="Default page size for list operations",
    )
    max_page_size: int = Field(
        default=100,
        description="Maximum page size for list operations",
    )
    response_format: Literal["json", "markdown"] = Field(
        default="json",
        description="Default response format",
    )
    search_default_limit: int = Field(
        default=50,
        description="Default limit for search results",
    )
    search_max_limit: int = Field(
        default=100,
        description="Maximum limit for search results",
    )
    todo_tag: str = Field(
        default="todo",
        description="Tag used to identify todo items",
    )
    template_dir: str = Field(
        default="~/.memos-templates/",
        description="Directory containing memo templates",
    )
    obsidian_vault: str = Field(
        default="",
        description="Path to Obsidian vault for exports",
    )
    batch_limit: int = Field(
        default=100,
        description="Maximum number of memos for batch operations",
    )

    @property
    def api_base_url(self) -> str:
        """Get the API base URL."""
        return f"{self.instance_url.rstrip('/')}/api/v1"

    @property
    def is_configured(self) -> bool:
        """Check if the server is properly configured."""
        return bool(self.api_token)


settings = Settings()
