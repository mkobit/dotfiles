from collections.abc import AsyncGenerator
from typing import Any

from jules_cli.client.base import BaseClient
from jules_cli.source import ListSourcesResponse, Source


class SourceClient(BaseClient):
    """Client for interacting with source-related Jules API endpoints."""

    async def get_source(self, source_name: str) -> Source:
        data = await self._get(f"/{source_name}")
        return Source(**data)

    async def list_sources(self) -> AsyncGenerator[Source, None]:
        next_page_token = None
        while True:
            params: dict[str, Any] = {}
            if next_page_token:
                params["pageToken"] = next_page_token

            data = await self._get("/sources", params=params)
            response = ListSourcesResponse(**data)

            for source in response.sources:
                yield source

            next_page_token = response.next_page_token
            if not next_page_token:
                break
