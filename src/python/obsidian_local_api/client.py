import ssl
from typing import Any
from urllib.parse import quote

import aiohttp


class ObsidianClient:
    def __init__(
        self,
        token: str,
        port: int = 27124,
        host: str = "127.0.0.1"
    ) -> None:
        self.token = token
        self.base_url = f"https://{host}:{port}"
        # Create an SSL context that trusts the self-signed certificate if needed
        # In a real scenario, the user should provide the cert or we should verify
        # it properly.
        # For now, we will verify=False but warn, or handle it via aiohttp's connector.
        # The Obsidian Local REST API generates a self-signed cert.
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"

        # Default Content-Type to application/json if not set
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        url = f"{self.base_url}{path}"

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=self.ssl_context)
        ) as session:
            async with session.request(
                method, url, headers=headers, **kwargs
            ) as response:
                if response.status == 204:
                    return None
                try:
                    return await response.json()
                except Exception:
                    return await response.text()

    async def get_file(self, path: str) -> Any:
        """Get the content of a file."""
        # Ensure path starts with /vault/
        if not path.startswith("/vault/"):
            path = f"/vault/{path}"
        return await self._request("GET", path)

    async def create_file(self, path: str, content: str) -> Any:
        """Create or update a file."""
        if not path.startswith("/vault/"):
            path = f"/vault/{path}"
        return await self._request(
            "PUT",
            path,
            data=content,
            headers={"Content-Type": "text/markdown"}
        )

    async def delete_file(self, path: str) -> Any:
        """Delete a file."""
        if not path.startswith("/vault/"):
            path = f"/vault/{path}"
        return await self._request("DELETE", path)

    async def list_files(self, folder: str = "/") -> Any:
        """List files in the vault."""
        # Clean up folder path
        if folder == "/":
            folder = ""
        elif folder.startswith("/"):
            folder = folder[1:]

        return await self._request("GET", f"/vault/{folder}")

    async def search(self, query: str) -> Any:
        """Search for files."""
        # Assuming /search/simple?query=... based on common patterns or /search/
        return await self._request(
            "GET",
            f"/search/simple?query={quote(query)}"
        )
