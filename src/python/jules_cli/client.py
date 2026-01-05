import aiohttp
from typing import Any, AsyncGenerator
from src.python.jules_cli.models import (
    Source, Session, Activity, ListSourcesResponse, ListSessionsResponse,
    ListActivitiesResponse
)

class JulesClient:
    """
    Client for interacting with the Jules API.
    See: https://developers.google.com/jules/api
    """
    def __init__(self, api_key: str):
        self._api_key = api_key
        if not self._api_key:
            raise ValueError("API key must be provided")
        self._base_url = "https://jules.googleapis.com/v1alpha"
        self._headers = {
            "X-Goog-Api-Key": self._api_key,
            "Content-Type": "application/json"
        }
        self._session = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(headers=self._headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def _get(self, endpoint: str, params: dict | None = None) -> Any:
        url = f"{self._base_url}{endpoint}"
        async with self._session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()

    async def _post(self, endpoint: str, data: dict | None = None) -> Any:
        url = f"{self._base_url}{endpoint}"
        async with self._session.post(url, json=data) as response:
            response.raise_for_status()
            return await response.json()

    async def list_sources(self) -> AsyncGenerator[Source, None]:
        next_page_token = None
        while True:
            params = {}
            if next_page_token:
                params["pageToken"] = next_page_token

            data = await self._get("/sources", params=params)
            response = ListSourcesResponse(**data)

            for source in response.sources:
                yield source

            next_page_token = response.next_page_token
            if not next_page_token:
                break

    async def list_sessions(self, page_size: int = 10) -> AsyncGenerator[Session, None]:
        next_page_token = None
        while True:
            params = {"pageSize": page_size}
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
        # Assuming session_id is the full resource name or the API handles it
        data = await self._get(f"/{session_id}")
        return Session(**data)

    async def list_activities(self, session_id: str, page_size: int = 30) -> AsyncGenerator[Activity, None]:
        next_page_token = None
        while True:
            params = {"pageSize": page_size}
            if next_page_token:
                params["pageToken"] = next_page_token

            data = await self._get(f"/{session_id}/activities", params=params)
            response = ListActivitiesResponse(**data)

            for activity in response.activities:
                yield activity

            next_page_token = response.next_page_token
            if not next_page_token:
                break

    async def send_message(self, session_id: str, message: str) -> Any:
        payload = {"prompt": message}
        return await self._post(f"/{session_id}:sendMessage", data=payload)

    async def approve_plan(self, session_id: str) -> Any:
        return await self._post(f"/{session_id}:approvePlan")
