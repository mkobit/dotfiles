from collections.abc import AsyncGenerator
from typing import Any

from jules_cli.client.base import BaseClient
from jules_cli.session import CreateSessionRequest, ListSessionsResponse, Session


class SessionClient(BaseClient):
    """Client for interacting with session-related Jules API endpoints."""

    async def create_session(self, request: CreateSessionRequest) -> Session:
        data = await self._post(
            "/sessions",
            data=request.model_dump(mode="json", by_alias=True, exclude_none=True),
        )
        return Session(**data)

    async def list_sessions(self, page_size: int = 10) -> AsyncGenerator[Session, None]:
        next_page_token = None
        while True:
            params: dict[str, Any] = {"pageSize": page_size}
            if next_page_token:
                params["pageToken"] = next_page_token

            data = await self._get("/sessions", params=params)
            response = ListSessionsResponse(**data)

            for session in response.sessions:
                yield session

            next_page_token = response.next_page_token
            if not next_page_token:
                break

    async def get_session(self, session_id: str) -> Session:
        data = await self._get(f"/sessions/{session_id}")
        return Session(**data)

    async def send_message(self, session_id: str, message: str) -> Any:
        payload = {"prompt": message}
        return await self._post(f"/sessions/{session_id}:sendMessage", data=payload)

    async def approve_plan(self, session_id: str) -> Any:
        return await self._post(f"/sessions/{session_id}:approvePlan")
