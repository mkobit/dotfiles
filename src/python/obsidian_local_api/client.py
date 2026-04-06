import ssl
from typing import Any, NewType
from urllib.parse import quote

import aiohttp

Token = NewType("Token", str)
Host = NewType("Host", str)


class ObsidianClient:
    """Client for the Obsidian Local REST API.

    See: https://coddingtonbear.github.io/obsidian-local-rest-api/
    """

    def __init__(self, token: str, port: int = 27124, host: str = "127.0.0.1") -> None:
        self.token = Token(token)
        self.host = Host(host)
        self.base_url = f"https://{self.host}:{port}"
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"

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
        if not path.startswith("/vault/"):
            path = f"/vault/{path}"
        return await self._request("GET", path)

    async def create_file(self, path: str, content: str) -> Any:
        """Create or update a file."""
        if not path.startswith("/vault/"):
            path = f"/vault/{path}"
        return await self._request(
            "PUT", path, data=content, headers={"Content-Type": "text/markdown"}
        )

    async def delete_file(self, path: str) -> Any:
        """Delete a file."""
        if not path.startswith("/vault/"):
            path = f"/vault/{path}"
        return await self._request("DELETE", path)

    async def list_files(self, folder: str = "/") -> Any:
        """List files in the vault."""
        if folder == "/":
            folder = ""
        elif folder.startswith("/"):
            folder = folder[1:]

        return await self._request("GET", f"/vault/{folder}")

    async def search(self, query: str) -> Any:
        """Search for files using Simple Search."""
        return await self._request("GET", f"/search/simple?query={quote(query)}")

    async def get_active_file(self) -> Any:
        """Get the currently active file."""
        return await self._request("GET", "/active/")

    async def list_commands(self) -> Any:
        """List available commands."""
        return await self._request("GET", "/commands/")

    async def execute_command(self, command_id: str) -> Any:
        """Execute a command."""
        return await self._request("POST", f"/commands/{command_id}/")
