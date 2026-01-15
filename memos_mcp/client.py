"""API client for Memos instance."""
from typing import Any

import httpx
from pydantic import BaseModel

from .config import settings


class MemosResponse(BaseModel):
    """Generic API response wrapper."""

    data: Any | None = None
    error: dict[str, str] | None = None


class MemosClient:
    """Client for interacting with Memos API."""

    def __init__(self) -> None:
        """Initialize the Memos client."""
        self.base_url = settings.api_base_url
        self.timeout = settings.timeout

    def _get_headers(self) -> dict[str, str]:
        """Get headers with authentication."""
        return {
            "Authorization": f"Bearer {settings.api_token}",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an HTTP request to the Memos API."""
        # Handle absolute URLs (for v2 endpoints) or relative (for v1 default)
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                **kwargs,
            )
            response.raise_for_status()
            return response.json()

    @property
    def api_v2_url(self) -> str:
        """Get the API v2 base URL."""
        # Need to reconstruct URL since instance_url is on settings, not self
        # Or access via settings import
        return f"{settings.instance_url.rstrip('/')}/api/v2"

    async def get(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a GET request."""
        return await self._request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a POST request."""
        return await self._request("POST", endpoint, **kwargs)

    async def patch(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a PATCH request."""
        return await self._request("PATCH", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a DELETE request."""
        return await self._request("DELETE", endpoint, **kwargs)

    async def upload_resource(
        self,
        file_path: str,
        filename: str | None = None,
        memo_id: int | None = None,
    ) -> dict[str, Any]:
        """Upload a file as a resource to Memos.

        Args:
            file_path: Path to the file to upload
            filename: Optional filename (defaults to basename of file_path)
            memo_id: Optional memo ID to associate the resource with

        Returns:
            The created resource data
        """
        import os
        import mimetypes
        import base64

        # Use correct Memos API v1 endpoint
        url = f"{self.base_url}/attachments"
        filename = filename or os.path.basename(file_path)
        
        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        # Read and encode file content as base64
        with open(file_path, "rb") as f:
            file_content = f.read()
            base64_content = base64.b64encode(file_content).decode('utf-8')

        # Prepare JSON payload
        payload = {
            "filename": filename,
            "type": mime_type,
            "content": base64_content,
        }
        
        # Add memo reference if provided
        if memo_id:
            payload["memo"] = f"memos/{memo_id}"

        headers = self._get_headers()
        headers["Content-Type"] = "application/json"

        # Use longer timeout for file uploads (120 seconds)
        upload_timeout = httpx.Timeout(120.0, connect=30.0)

        async with httpx.AsyncClient(timeout=upload_timeout) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()


client = MemosClient()
