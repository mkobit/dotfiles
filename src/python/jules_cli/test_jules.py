import pytest
from src.python.jules_cli.models import Session, SourceContext
from src.python.jules_cli.client import JulesClient

# Mock data
MOCK_SESSION_DATA = {
    "name": "sessions/123",
    "id": "123",
    "title": "Test Session",
    "prompt": "Test Prompt",
    "sourceContext": {
        "source": "sources/github/test/repo"
    }
}

def test_session_model():
    session = Session(**MOCK_SESSION_DATA)
    assert session.id == "123"
    assert session.title == "Test Session"
    assert session.sourceContext.source == "sources/github/test/repo"

@pytest.mark.asyncio
async def test_client_get_session(monkeypatch):
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

        async def close(self):
            pass

    client = JulesClient(api_key="test_key")
    client.session = MockSession()

    session = await client.get_session("123")
    assert session.id == "123"
