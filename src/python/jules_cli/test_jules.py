import pytest

from src.python.jules_cli.client import JulesClient
from src.python.jules_cli.models import Session

# Mock data matches Pydantic camelCase conversion
MOCK_SESSION_DATA = {
    "name": "sessions/123",
    "id": "123",
    "title": "Test Session",
    "prompt": "Test Prompt",
    "sourceContext": {"source": "sources/github/test/repo"},
}

MOCK_LIST_SESSIONS_DATA = {"sessions": [MOCK_SESSION_DATA], "nextPageToken": None}


def test_session_model() -> None:
    session = Session(**MOCK_SESSION_DATA)
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

        def raise_for_status(self) -> None:
            pass

        async def __aenter__(self) -> "MockResponse":
            return self

        async def __aexit__(
            self, exc_type: object, exc_val: object, exc_tb: object
        ) -> None:
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

    session = await client.get_session("sessions/123")
    assert session.id == "123"


@pytest.mark.asyncio
async def test_client_list_sessions() -> None:
    class MockResponse:
        def __init__(self, data: dict) -> None:
            self._data = data

        async def json(self) -> dict:
            return self._data

        def raise_for_status(self) -> None:
            pass

        async def __aenter__(self) -> "MockResponse":
            return self

        async def __aexit__(self, *args: object) -> None:
            pass

    class MockSession:
        def get(self, url: str, params: dict | None = None) -> MockResponse:
            return MockResponse(MOCK_LIST_SESSIONS_DATA)

        async def close(self) -> None:
            pass

    client = JulesClient(api_key="test_key")
    client._session = MockSession()  # type: ignore

    sessions = []
    async for s in client.list_sessions():
        sessions.append(s)

    assert len(sessions) == 1
    assert sessions[0].id == "123"
