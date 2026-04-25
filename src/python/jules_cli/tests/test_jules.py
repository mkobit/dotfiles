from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jules_cli.client import JulesClient
from jules_cli.models import CreateSessionRequest, Session, SourceContext

# Mock data matches Pydantic camelCase conversion
MOCK_SESSION_DATA = {
    "name": "sessions/123",
    "id": "123",
    "title": "Test Session",
    "prompt": "Test Prompt",
    "sourceContext": {"source": "sources/github/test/repo"},
}

MOCK_LIST_SESSIONS_PAGE_1 = {"sessions": [MOCK_SESSION_DATA], "nextPageToken": "page-2-token"}

MOCK_SESSION_DATA_2 = {
    "name": "sessions/456",
    "id": "456",
    "title": "Test Session 2",
    "prompt": "Test Prompt 2",
    "sourceContext": {"source": "sources/github/test/repo2"},
}
MOCK_LIST_SESSIONS_PAGE_2 = {"sessions": [MOCK_SESSION_DATA_2], "nextPageToken": None}


def test_session_model() -> None:
    session = Session.model_validate(MOCK_SESSION_DATA)
    assert session.id == "123"
    assert session.title == "Test Session"
    assert session.source_context.source == "sources/github/test/repo"


@pytest.mark.asyncio
async def test_client_init_error() -> None:
    with pytest.raises(ValueError):
        JulesClient(api_key="")


@pytest.mark.asyncio
async def test_client_get_session() -> None:
    client = JulesClient(api_key="test_key")

    async def mock_get(endpoint: str, params: dict | None = None) -> dict:
        if "123" in endpoint:
            return MOCK_SESSION_DATA
        return {}

    client._get = mock_get  # type: ignore

    session = await client.get_session("123")
    assert session.id == "123"


@pytest.mark.asyncio
async def test_client_list_sessions() -> None:
    client = JulesClient(api_key="test_key")

    async def mock_get(endpoint: str, params: dict | None = None) -> dict:
        if params and params.get("pageToken") == "page-2-token":
            return MOCK_LIST_SESSIONS_PAGE_2
        return MOCK_LIST_SESSIONS_PAGE_1

    client._get = mock_get  # type: ignore

    sessions = [s async for s in client.list_sessions()]

    assert len(sessions) == 2
    assert sessions[0].id == "123"
    assert sessions[1].id == "456"


MOCK_ACTIVITY_DATA = {
    "name": "sessions/123/activities/456",
    "id": "456",
    "description": "Test Activity",
    "createTime": "2024-03-20T10:00:00Z",
    "originator": "agent",
    "agentMessaged": {"agentMessage": "Hello from Jules"},
}

MOCK_LIST_ACTIVITIES_PAGE_1 = {"activities": [MOCK_ACTIVITY_DATA], "nextPageToken": "page-2-token"}

MOCK_ACTIVITY_DATA_2 = {
    "name": "sessions/123/activities/789",
    "id": "789",
    "description": "Test Activity 2",
    "createTime": "2024-03-20T10:05:00Z",
    "originator": "user",
    "userMessaged": {"userMessage": "Hello"},
}

MOCK_LIST_ACTIVITIES_PAGE_2 = {"activities": [MOCK_ACTIVITY_DATA_2], "nextPageToken": None}


@pytest.mark.asyncio
async def test_client_list_activities() -> None:
    client = JulesClient(api_key="test_key")

    async def mock_get(endpoint: str, params: dict | None = None) -> dict:
        assert params is not None
        assert params.get("pageSize") == 30
        if params and params.get("pageToken") == "page-2-token":
            return MOCK_LIST_ACTIVITIES_PAGE_2
        return MOCK_LIST_ACTIVITIES_PAGE_1

    client._get = mock_get  # type: ignore

    activities = [a async for a in client.list_activities("123")]

    assert len(activities) == 2
    assert activities[0].id == "456"
    assert activities[0].agent_messaged is not None
    assert activities[0].agent_messaged.agent_message == "Hello from Jules"
    assert activities[1].id == "789"
    assert activities[1].user_messaged is not None
    assert activities[1].user_messaged.user_message == "Hello"


@pytest.mark.asyncio
async def test_client_list_activities_custom_page_size() -> None:
    client = JulesClient(api_key="test_key")

    async def mock_get(endpoint: str, params: dict | None = None) -> dict:
        assert params is not None
        assert params.get("pageSize") == 50
        return MOCK_LIST_ACTIVITIES_PAGE_2

    client._get = mock_get  # type: ignore

    activities = [a async for a in client.list_activities("123", page_size=50)]

    assert len(activities) == 1
    assert activities[0].id == "789"


MOCK_SOURCE_DATA_1 = {
    "name": "sources/123",
    "id": "123",
    "githubRepo": {"owner": "test-owner", "repo": "test-repo"},
}

MOCK_LIST_SOURCES_PAGE_1 = {"sources": [MOCK_SOURCE_DATA_1], "nextPageToken": "page-2-token"}

MOCK_SOURCE_DATA_2 = {
    "name": "sources/456",
    "id": "456",
}

MOCK_LIST_SOURCES_PAGE_2 = {"sources": [MOCK_SOURCE_DATA_2], "nextPageToken": None}


@pytest.mark.asyncio
async def test_client_list_sources() -> None:
    client = JulesClient(api_key="test_key")

    async def mock_get(endpoint: str, params: dict | None = None) -> dict:
        if params and params.get("pageToken") == "page-2-token":
            return MOCK_LIST_SOURCES_PAGE_2
        return MOCK_LIST_SOURCES_PAGE_1

    client._get = mock_get  # type: ignore

    sources = [s async for s in client.list_sources()]

    assert len(sources) == 2
    assert sources[0].id == "123"
    assert sources[0].github_repo is not None
    assert sources[0].github_repo.owner == "test-owner"
    assert sources[0].github_repo.repo == "test-repo"
    assert sources[1].id == "456"
    assert sources[1].github_repo is None


@pytest.mark.asyncio
async def test_client_create_session() -> None:
    client = JulesClient(api_key="test_key")

    async def mock_post(endpoint: str, data: dict | None = None) -> dict:
        assert endpoint == "/sessions"
        assert data is not None
        assert data.get("prompt") == "New Session Prompt"
        return MOCK_SESSION_DATA

    client._post = mock_post  # type: ignore

    request = CreateSessionRequest(
        prompt="New Session Prompt",
        source_context=SourceContext(source="sources/github/test/repo"),
    )
    session = await client.create_session(request)

    assert session.id == "123"
    assert session.title == "Test Session"


@pytest.mark.asyncio
async def test_client_send_message() -> None:
    client = JulesClient(api_key="test_key")

    async def mock_post(endpoint: str, data: dict | None = None) -> dict:
        assert endpoint == "/sessions/123:sendMessage"
        assert data is not None
        assert data.get("prompt") == "Test Message"
        return {"status": "ok"}

    client._post = mock_post  # type: ignore

    response = await client.send_message("123", "Test Message")
    assert response.get("status") == "ok"


@pytest.mark.asyncio
async def test_client_approve_plan() -> None:
    client = JulesClient(api_key="test_key")

    async def mock_post(endpoint: str, data: dict | None = None) -> dict:
        assert endpoint == "/sessions/123:approvePlan"
        assert data is None
        return {"status": "approved"}

    client._post = mock_post  # type: ignore

    response = await client.approve_plan("123")
    assert response.get("status") == "approved"


@pytest.mark.asyncio
async def test_client_get_activity() -> None:
    client = JulesClient(api_key="test_key")

    async def mock_get(endpoint: str, params: dict | None = None) -> dict:
        if "sessions/123/activities/456" in endpoint:
            return MOCK_ACTIVITY_DATA
        return {}

    client._get = mock_get  # type: ignore

    activity = await client.get_activity("sessions/123/activities/456")
    assert activity.id == "456"
    assert activity.originator == "agent"


@pytest.mark.asyncio
async def test_client_get_source() -> None:
    client = JulesClient(api_key="test_key")

    async def mock_get(endpoint: str, params: dict | None = None) -> dict:
        if "sources/123" in endpoint:
            return MOCK_SOURCE_DATA_1
        return {}

    client._get = mock_get  # type: ignore

    source = await client.get_source("sources/123")
    assert source.id == "123"
    assert source.github_repo is not None
    assert source.github_repo.owner == "test-owner"


@pytest.mark.asyncio
async def test_client_context_manager() -> None:
    client = JulesClient(api_key="test_key")
    with patch("aiohttp.ClientSession") as mock_session_class:
        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session

        async with client as c:
            assert c._session == mock_session

        mock_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_client_uninitialized_session() -> None:
    client = JulesClient(api_key="test_key")
    with pytest.raises(RuntimeError, match="Client session not initialized"):
        await client._get("/test")
    with pytest.raises(RuntimeError, match="Client session not initialized"):
        await client._post("/test", data={})


class AsyncContextManagerMock:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.mark.asyncio
async def test_client_get_success() -> None:
    client = JulesClient(api_key="test_key")
    with patch("aiohttp.ClientSession") as mock_session_class:
        mock_session = MagicMock()
        mock_session.close = AsyncMock()
        mock_session_class.return_value = mock_session

        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": "ok"}

        mock_session.get.return_value = AsyncContextManagerMock(mock_response)

        async with client as c:
            c._session = mock_session
            result = await c._get("/test")
            assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_client_get_error() -> None:
    client = JulesClient(api_key="test_key")
    with patch("aiohttp.ClientSession") as mock_session_class:
        mock_session = MagicMock()
        mock_session.close = AsyncMock()
        mock_session_class.return_value = mock_session

        mock_response = AsyncMock()
        mock_response.ok = False
        mock_response.status = 500
        mock_response.text.return_value = "Internal Server Error"

        mock_session.get.return_value = AsyncContextManagerMock(mock_response)

        async with client as c:
            c._session = mock_session
            with pytest.raises(Exception, match="API Error 500: Internal Server Error"):
                await c._get("/test")


@pytest.mark.asyncio
async def test_client_post_success() -> None:
    client = JulesClient(api_key="test_key")
    with patch("aiohttp.ClientSession") as mock_session_class:
        mock_session = MagicMock()
        mock_session.close = AsyncMock()
        mock_session_class.return_value = mock_session

        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": "created"}

        mock_session.post.return_value = AsyncContextManagerMock(mock_response)

        async with client as c:
            c._session = mock_session
            result = await c._post("/test", data={"foo": "bar"})
            assert result == {"status": "created"}


@pytest.mark.asyncio
async def test_client_post_error() -> None:
    client = JulesClient(api_key="test_key")
    with patch("aiohttp.ClientSession") as mock_session_class:
        mock_session = MagicMock()
        mock_session.close = AsyncMock()
        mock_session_class.return_value = mock_session

        mock_response = AsyncMock()
        mock_response.ok = False
        mock_response.status = 400
        mock_response.text.return_value = "Bad Request"

        mock_session.post.return_value = AsyncContextManagerMock(mock_response)

        async with client as c:
            c._session = mock_session
            with pytest.raises(Exception, match="API Error 400: Bad Request"):
                await c._post("/test")
