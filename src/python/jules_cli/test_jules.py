import pytest
import pytest_asyncio
from src.python.jules_cli.models import Session, SourceContext
from src.python.jules_cli.client import JulesClient

# Mock data matches Pydantic camelCase conversion
MOCK_SESSION_DATA = {
    "name": "sessions/123",
    "id": "123",
    "title": "Test Session",
    "prompt": "Test Prompt",
    "sourceContext": {
        "source": "sources/github/test/repo"
    }
}

MOCK_LIST_SESSIONS_DATA = {
    "sessions": [MOCK_SESSION_DATA],
    "nextPageToken": None
}

def test_session_model():
    session = Session(**MOCK_SESSION_DATA)
    assert session.id == "123"
    assert session.title == "Test Session"
    assert session.source_context.source == "sources/github/test/repo"

@pytest.mark.asyncio
async def test_client_init_error():
    with pytest.raises(ValueError):
        JulesClient(api_key="")

@pytest.mark.asyncio
async def test_client_get_session():
    # Mock aiohttp session
    class MockResponse:
        def __init__(self, data):
            self._data = data

        async def json(self):
            return self._data

        def raise_for_status(self):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockSession:
        def get(self, url, params=None):
            if "sessions/123" in url:
                return MockResponse(MOCK_SESSION_DATA)
            return MockResponse({})

        def post(self, url, json=None):
            return MockResponse({})

        async def close(self):
            pass

    client = JulesClient(api_key="test_key")
    client._session = MockSession()

    session = await client.get_session("sessions/123")
    assert session.id == "123"

@pytest.mark.asyncio
async def test_client_list_sessions():
    class MockResponse:
        def __init__(self, data):
            self._data = data
        async def json(self): return self._data
        def raise_for_status(self): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass

    class MockSession:
        def get(self, url, params=None):
            return MockResponse(MOCK_LIST_SESSIONS_DATA)
        async def close(self): pass

    client = JulesClient(api_key="test_key")
    client._session = MockSession()

    sessions = []
    async for s in client.list_sessions():
        sessions.append(s)

    assert len(sessions) == 1
    assert sessions[0].id == "123"
