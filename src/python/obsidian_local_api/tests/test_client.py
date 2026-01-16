from unittest.mock import AsyncMock, patch

import pytest

from src.python.obsidian_local_api.client import ObsidianClient


@pytest.mark.asyncio
async def test_client_get_file() -> None:
    token = "test-token"
    client = ObsidianClient(token)

    with patch("aiohttp.ClientSession.request") as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"content": "test content"}
        mock_response.text.return_value = '{"content": "test content"}'
        mock_request.return_value.__aenter__.return_value = mock_response

        # Test basic get
        result = await client.get_file("test.md")
        assert result == {"content": "test content"}

        # Verify URL construction
        args, kwargs = mock_request.call_args
        assert args[1] == "https://127.0.0.1:27124/vault/test.md"
        assert kwargs["headers"]["Authorization"] == "Bearer test-token"


@pytest.mark.asyncio
async def test_client_create_file() -> None:
    token = "test-token"
    client = ObsidianClient(token)

    with patch("aiohttp.ClientSession.request") as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_request.return_value.__aenter__.return_value = mock_response

        await client.create_file("new.md", "content")

        args, kwargs = mock_request.call_args
        assert args[0] == "PUT"
        assert args[1] == "https://127.0.0.1:27124/vault/new.md"
        assert kwargs["data"] == "content"
        # Verify Content-Type is set to markdown
        assert kwargs["headers"]["Content-Type"] == "text/markdown"


@pytest.mark.asyncio
async def test_client_delete_file() -> None:
    token = "test-token"
    client = ObsidianClient(token)

    with patch("aiohttp.ClientSession.request") as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 204  # No content for delete usually
        mock_request.return_value.__aenter__.return_value = mock_response

        await client.delete_file("del.md")

        args, kwargs = mock_request.call_args
        assert args[0] == "DELETE"
        assert args[1] == "https://127.0.0.1:27124/vault/del.md"


@pytest.mark.asyncio
async def test_client_list_files_root() -> None:
    token = "test-token"
    client = ObsidianClient(token)

    with patch("aiohttp.ClientSession.request") as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = ["file1.md", "file2.md"]
        mock_request.return_value.__aenter__.return_value = mock_response

        await client.list_files("/")

        args, kwargs = mock_request.call_args
        assert args[0] == "GET"
        assert args[1] == "https://127.0.0.1:27124/vault/"


@pytest.mark.asyncio
async def test_client_list_files_subdir() -> None:
    token = "test-token"
    client = ObsidianClient(token)

    with patch("aiohttp.ClientSession.request") as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_request.return_value.__aenter__.return_value = mock_response

        await client.list_files("/subdir")

        args, kwargs = mock_request.call_args
        assert args[0] == "GET"
        assert args[1] == "https://127.0.0.1:27124/vault/subdir"
