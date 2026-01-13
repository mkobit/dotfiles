import os
from unittest.mock import AsyncMock, mock_open, patch

import pytest

from src.python.obsidian_local_api.cli import get_token
from src.python.obsidian_local_api.client import FileMetadata, ObsidianClient


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
        # Pydantic model expect real-ish structure or list of names
        mock_response.json.return_value = {"files": [
            {"name": "file1.md", "path": "file1.md"},
            {"name": "file2.md", "path": "file2.md"}
        ]}
        mock_request.return_value.__aenter__.return_value = mock_response

        result = await client.list_files("/")

        args, kwargs = mock_request.call_args
        assert args[0] == "GET"
        assert args[1] == "https://127.0.0.1:27124/vault/"
        assert len(result) == 2
        assert isinstance(result[0], FileMetadata)
        assert result[0].name == "file1.md"

@pytest.mark.asyncio
async def test_client_list_files_subdir() -> None:
    token = "test-token"
    client = ObsidianClient(token)

    with patch("aiohttp.ClientSession.request") as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"files": []}
        mock_request.return_value.__aenter__.return_value = mock_response

        await client.list_files("/subdir")

        args, kwargs = mock_request.call_args
        assert args[0] == "GET"
        assert args[1] == "https://127.0.0.1:27124/vault/subdir"

def test_token_loading_env_var_ignored() -> None:
    # Mock environment (Should NOT be read anymore)
    with patch.dict(os.environ, {"OBSIDIAN_API_TOKEN": "env_token"}, clear=True):
        # We need to mock .env loading to ensure it doesn't pick up something
        with patch("src.python.obsidian_local_api.cli.dotenv_values", return_value={}):
             # And ensure no token file
             with patch("os.path.exists", return_value=False):
                token = get_token()
                assert token is None, "OBSIDIAN_API_TOKEN env var should be ignored"

def test_token_loading_file_arg() -> None:
    # Mock token file arg
    token_file = "/tmp/mytoken"
    with patch("os.path.exists", side_effect=lambda p: p == token_file):
        with patch("builtins.open", mock_open(read_data="file_token_content")):
            token = get_token(token_file=token_file)
            assert token == "file_token_content"

def test_token_loading_file_arg_missing() -> None:
    # Mock token file arg missing
    token_file = "/tmp/missing_token"
    with patch("os.path.exists", side_effect=lambda p: False):
        with pytest.raises(FileNotFoundError):
            get_token(token_file=token_file)

def test_token_loading_dotenv() -> None:
    # Mock .env file
    with patch(
        "src.python.obsidian_local_api.cli.dotenv_values",
        return_value={"OBSIDIAN_API_TOKEN": "dotenv_token"},
    ):
        with patch("os.path.exists", return_value=False):
            token = get_token()
            assert token == "dotenv_token"
