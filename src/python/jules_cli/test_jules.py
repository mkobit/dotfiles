import pytest

from jules_cli.client import JulesClient
from jules_cli.models import Session

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
    # Mock aiohttp session
    class MockResponse:
        def __init__(self, data: dict) -> None:
            self._data = data

        async def json(self) -> dict:
            return self._data

        @property
        def ok(self) -> bool:
            return True

        async def text(self) -> str:
            return ""

        async def __aenter__(self) -> MockResponse:
            return self

        async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
            pass

    class MockSession:
        def get(self, url: str, params: dict | None = None) -> MockResponse:
            if "sessions/123" in url:
                return MockResponse(MOCK_SESSION_DATA)
            return MockResponse({})

        def post(self, url: str, json: dict | None = None) -> MockResponse:
            return MockResponse({})

        async def close(self) -> None:
            pass

    client = JulesClient(api_key="test_key")
    # We are mocking internal _session which is typed as aiohttp.ClientSession
    # So we need ignore here or make MockSession compatible.
    client._session = MockSession()  # type: ignore

    session = await client.get_session("123")
    assert session.id == "123"


@pytest.mark.asyncio
async def test_client_list_sessions() -> None:
    class MockResponse:
        def __init__(self, data: dict) -> None:
            self._data = data

        async def json(self) -> dict:
            return self._data

        @property
        def ok(self) -> bool:
            return True

        async def text(self) -> str:
            return ""

        async def __aenter__(self) -> MockResponse:
            return self

        async def __aexit__(self, *args: object) -> None:
            pass

    class MockSession:
        def get(self, url: str, params: dict | None = None) -> MockResponse:
            if params and params.get("pageToken") == "page-2-token":
                return MockResponse(MOCK_LIST_SESSIONS_PAGE_2)
            return MockResponse(MOCK_LIST_SESSIONS_PAGE_1)

        async def close(self) -> None:
            pass

    client = JulesClient(api_key="test_key")
    client._session = MockSession()  # type: ignore

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
