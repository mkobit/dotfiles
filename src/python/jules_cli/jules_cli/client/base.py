from typing import Any, Self

import aiohttp


class BaseClient:
    """Base client for handling HTTP requests to the Jules API."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        if not self._api_key:
            raise ValueError("API key must be provided")
        self._base_url = "https://jules.googleapis.com/v1alpha"
        self._headers = {
            "X-Goog-Api-Key": self._api_key,
            "Content-Type": "application/json",
        }
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> Self:
        self._session = aiohttp.ClientSession(headers=self._headers)
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        if self._session:
            await self._session.close()

    async def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        if not self._session:
            raise RuntimeError("Client session not initialized")
        url = f"{self._base_url}{endpoint}"
        async with self._session.get(url, params=params) as response:
            if not response.ok:
                error_body = await response.text()
                raise Exception(f"API Error {response.status}: {error_body}")
            return await response.json()

    async def _post(self, endpoint: str, data: dict[str, Any] | None = None) -> Any:
        if not self._session:
            raise RuntimeError("Client session not initialized")
        url = f"{self._base_url}{endpoint}"
        async with self._session.post(url, json=data) as response:
            if not response.ok:
                error_body = await response.text()
                raise Exception(f"API Error {response.status}: {error_body}")
            return await response.json()
