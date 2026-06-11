from collections.abc import AsyncGenerator
from typing import Any

from jules_cli.activity import Activity, ListActivitiesResponse
from jules_cli.client.base import BaseClient


class ActivityClient(BaseClient):
    """Client for interacting with activity-related Jules API endpoints."""

    async def list_activities(self, session_id: str, page_size: int = 30) -> AsyncGenerator[Activity, None]:
        next_page_token = None
        while True:
            params: dict[str, Any] = {"pageSize": page_size}
            if next_page_token:
                params["pageToken"] = next_page_token

            data = await self._get(f"/sessions/{session_id}/activities", params=params)
            response = ListActivitiesResponse(**data)

            for activity in response.activities:
                yield activity

            next_page_token = response.next_page_token
            if not next_page_token:
                break

    async def get_activity(self, activity_name: str) -> Activity:
        data = await self._get(f"/{activity_name}")
        return Activity(**data)
