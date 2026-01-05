import os
import aiohttp
from typing import List, Optional, Any
from src.python.jules_cli.models import (
    Source, Session, Activity, ListSourcesResponse, ListSessionsResponse,
    ListActivitiesResponse
)

class JulesClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("JULES_API_KEY")
        if not self.api_key:
            raise ValueError("JULES_API_KEY environment variable is not set")
        self.base_url = "https://jules.googleapis.com/v1alpha"
        self.headers = {
            "X-Goog-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _get(self, endpoint: str, params: Optional[dict] = None) -> Any:
        url = f"{self.base_url}{endpoint}"
        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()

    async def _post(self, endpoint: str, data: Optional[dict] = None) -> Any:
        url = f"{self.base_url}{endpoint}"
        async with self.session.post(url, json=data) as response:
            response.raise_for_status()
            return await response.json()

    async def list_sources(self) -> List[Source]:
        data = await self._get("/sources")
        return ListSourcesResponse(**data).sources

    async def list_sessions(self, page_size: int = 10) -> List[Session]:
        data = await self._get("/sessions", params={"pageSize": page_size})
        return ListSessionsResponse(**data).sessions

    async def get_session(self, session_id: str) -> Session:
        # If the ID is just the numeric ID, prepend "sessions/" if needed,
        # or rely on how the API works. The docs show "sessions/ID" in responses.
        # But endpoints often take the full resource name or just the ID.
        # Docs say: curl 'https://jules.googleapis.com/v1alpha/sessions/SESSION_ID/activities'
        # So we probably need to handle both full name and ID.
        if session_id.startswith("sessions/"):
            resource_name = session_id
        else:
            resource_name = f"sessions/{session_id}"

        # Note: GetSession endpoint wasn't explicitly in the example list but implied.
        # Assuming GET /sessions/{id} exists or we filter list.
        # Actually, let's try GET /sessions/{id}
        data = await self._get(f"/{resource_name}")
        return Session(**data)

    async def create_session(self, source_name: str, prompt: str, title: str,
                             starting_branch: str = "main",
                             automation_mode: Optional[str] = None) -> Session:
        payload = {
            "prompt": prompt,
            "title": title,
            "sourceContext": {
                "source": source_name,
                "githubRepoContext": {
                    "startingBranch": starting_branch
                }
            }
        }
        if automation_mode:
            payload["automationMode"] = automation_mode

        data = await self._post("/sessions", data=payload)
        return Session(**data)

    async def list_activities(self, session_id: str, page_size: int = 30) -> List[Activity]:
        if not session_id.startswith("sessions/"):
            resource_name = f"sessions/{session_id}"
        else:
            resource_name = session_id

        data = await self._get(f"/{resource_name}/activities", params={"pageSize": page_size})
        return ListActivitiesResponse(**data).activities

    async def send_message(self, session_id: str, message: str) -> None:
        if not session_id.startswith("sessions/"):
            resource_name = f"sessions/{session_id}"
        else:
            resource_name = session_id

        payload = {"prompt": message}
        await self._post(f"/{resource_name}:sendMessage", data=payload)

    async def approve_plan(self, session_id: str) -> None:
        if not session_id.startswith("sessions/"):
            resource_name = f"sessions/{session_id}"
        else:
            resource_name = session_id

        await self._post(f"/{resource_name}:approvePlan")
