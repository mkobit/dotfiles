import ssl
from typing import Any, NewType
from urllib.parse import quote

import aiohttp

Token = NewType("Token", str)


class ObsidianClient:
    """Client for the Obsidian Local REST API.

    See: https://coddingtonbear.github.io/obsidian-local-rest-api/
    """

    def __init__(
        self,
        token: str,
        port: int = 27124,
        host: str = "127.0.0.1"
    ) -> None:
        self.token = Token(token)
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
        """Get the content of a file.

        https://coddingtonbear.github.io/obsidian-local-rest-api/#/Vault%20Files/get_vault__filename_
        """
        if not path.startswith("/vault/"):
            path = f"/vault/{path}"
        return await self._request("GET", path)

    async def create_file(self, path: str, content: str) -> Any:
        """Create or update a file.

        https://coddingtonbear.github.io/obsidian-local-rest-api/#/Vault%20Files/put_vault__filename_
        """
        if not path.startswith("/vault/"):
            path = f"/vault/{path}"
        return await self._request(
            "PUT",
            path,
            data=content,
            headers={"Content-Type": "text/markdown"}
        )

    async def delete_file(self, path: str) -> Any:
        """Delete a file.

        https://coddingtonbear.github.io/obsidian-local-rest-api/#/Vault%20Files/delete_vault__filename_
        """
        if not path.startswith("/vault/"):
            path = f"/vault/{path}"
        return await self._request("DELETE", path)

    async def list_files(self, folder: str = "/") -> Any:
        """List files in the vault.

        https://coddingtonbear.github.io/obsidian-local-rest-api/#/Vault%20Files/get_vault_
        """
        if folder == "/":
            folder = ""
        elif folder.startswith("/"):
            folder = folder[1:]

        return await self._request("GET", f"/vault/{folder}")

    async def search(self, query: str) -> Any:
        """Search for files using Simple Search.

        https://coddingtonbear.github.io/obsidian-local-rest-api/#/Search/get_search_simple
        """
        return await self._request(
            "GET",
            f"/search/simple?query={quote(query)}"
        )

    async def get_active_file(self) -> Any:
        """Get the currently active file.

        https://coddingtonbear.github.io/obsidian-local-rest-api/#/Active%20File/get_active_
        """
        return await self._request("GET", "/active/")

    async def list_commands(self) -> Any:
        """List available commands.

        https://coddingtonbear.github.io/obsidian-local-rest-api/#/Commands/get_commands_
        """
        return await self._request("GET", "/commands/")

    async def execute_command(self, command_id: str) -> Any:
        """Execute a command.

        https://coddingtonbear.github.io/obsidian-local-rest-api/#/Commands/post_commands__commandId_
        """
        return await self._request("POST", f"/commands/{command_id}/")
