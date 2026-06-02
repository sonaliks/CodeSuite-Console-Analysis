"""Unit tests for CodeCommit MCP Server handlers using mocked boto3 responses."""

import sys
import os
import importlib
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

# Import codecommit handlers using importlib to avoid path conflicts
_codecommit_path = os.path.join(
    os.path.dirname(__file__), "..", "mcp-servers", "codecommit"
)
spec = importlib.util.spec_from_file_location(
    "codecommit_handlers",
    os.path.join(_codecommit_path, "handlers.py"),
)
codecommit_handlers = importlib.util.module_from_spec(spec)
sys.modules["codecommit_handlers"] = codecommit_handlers
spec.loader.exec_module(codecommit_handlers)

list_files = codecommit_handlers.list_files
get_file_content = codecommit_handlers.get_file_content
get_repository_metadata = codecommit_handlers.get_repository_metadata

# Patch target is the module we loaded
PATCH_TARGET = "codecommit_handlers._get_client"


def make_client_error(code: str, message: str = "Error") -> ClientError:
    """Helper to create a ClientError with a specific error code."""
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "operation_name",
    )


class TestListFiles:
    """Tests for the list_files handler."""

    @pytest.mark.asyncio
    async def test_list_files_success(self):
        """Should return files and folders at repository root."""
        mock_response = {
            "files": [
                {"relativePath": "index.html"},
                {"relativePath": "README.md"},
            ],
            "subFolders": [
                {"relativePath": "scripts"},
                {"relativePath": "styles"},
            ],
        }

        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_folder.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await list_files("my-repo", "main")

            assert result["repository_name"] == "my-repo"
            assert result["branch"] == "main"
            assert result["path"] == "/"
            assert result["files"] == ["index.html", "README.md"]
            assert result["folders"] == ["scripts", "styles"]

    @pytest.mark.asyncio
    async def test_list_files_empty_repo(self):
        """Should return empty arrays for an empty repository."""
        mock_response = {"files": [], "subFolders": []}

        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_folder.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await list_files("empty-repo", "main")

            assert result["files"] == []
            assert result["folders"] == []

    @pytest.mark.asyncio
    async def test_list_files_repo_not_found(self):
        """Should raise ValueError for non-existent repository."""
        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_folder.side_effect = make_client_error(
                "RepositoryDoesNotExistException"
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(ValueError, match="does not exist"):
                await list_files("nonexistent-repo", "main")

    @pytest.mark.asyncio
    async def test_list_files_branch_not_found(self):
        """Should raise ValueError for non-existent branch."""
        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_folder.side_effect = make_client_error(
                "CommitDoesNotExistException"
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(ValueError, match="Branch.*does not exist"):
                await list_files("my-repo", "nonexistent-branch")

    @pytest.mark.asyncio
    async def test_list_files_default_branch(self):
        """Should default to 'main' branch when not specified."""
        mock_response = {"files": [], "subFolders": []}

        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_folder.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await list_files("my-repo")

            assert result["branch"] == "main"
            mock_client.get_folder.assert_called_once_with(
                repositoryName="my-repo",
                commitSpecifier="main",
                folderPath="/",
            )


class TestGetFileContent:
    """Tests for the get_file_content handler."""

    @pytest.mark.asyncio
    async def test_get_file_content_success(self):
        """Should return file content as string."""
        mock_response = {
            "fileContent": b"<html><body>Hello</body></html>",
            "fileSize": 30,
        }

        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_file.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await get_file_content("my-repo", "index.html", "main")

            assert result["repository_name"] == "my-repo"
            assert result["file_path"] == "index.html"
            assert result["content"] == "<html><body>Hello</body></html>"
            assert result["file_size"] == 30

    @pytest.mark.asyncio
    async def test_get_file_content_repo_not_found(self):
        """Should raise ValueError for non-existent repository."""
        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_file.side_effect = make_client_error(
                "RepositoryDoesNotExistException"
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(ValueError, match="does not exist"):
                await get_file_content("nonexistent-repo", "file.txt", "main")

    @pytest.mark.asyncio
    async def test_get_file_content_file_not_found(self):
        """Should raise ValueError for non-existent file."""
        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_file.side_effect = make_client_error(
                "FileDoesNotExistException"
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(ValueError, match="File.*does not exist"):
                await get_file_content("my-repo", "missing.txt", "main")

    @pytest.mark.asyncio
    async def test_get_file_content_branch_not_found(self):
        """Should raise ValueError for non-existent branch."""
        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_file.side_effect = make_client_error(
                "CommitDoesNotExistException"
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(ValueError, match="Branch.*does not exist"):
                await get_file_content("my-repo", "file.txt", "bad-branch")


class TestGetRepositoryMetadata:
    """Tests for the get_repository_metadata handler."""

    @pytest.mark.asyncio
    async def test_get_repository_metadata_success(self):
        """Should return repository metadata."""
        mock_response = {
            "repositoryMetadata": {
                "repositoryName": "my-repo",
                "defaultBranch": "main",
                "cloneUrlHttp": "https://git-codecommit.us-east-1.amazonaws.com/v1/repos/my-repo",
                "cloneUrlSsh": "ssh://git-codecommit.us-east-1.amazonaws.com/v1/repos/my-repo",
                "Arn": "arn:aws:codecommit:us-east-1:123456789:my-repo",
                "repositoryDescription": "Test repo",
                "creationDate": "2024-01-01T00:00:00Z",
                "lastModifiedDate": "2024-06-01T00:00:00Z",
            }
        }

        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_repository.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await get_repository_metadata("my-repo")

            assert result["repository_name"] == "my-repo"
            assert result["default_branch"] == "main"
            assert "codecommit" in result["clone_url_http"]
            assert result["arn"] == "arn:aws:codecommit:us-east-1:123456789:my-repo"

    @pytest.mark.asyncio
    async def test_get_repository_metadata_not_found(self):
        """Should raise ValueError for non-existent repository."""
        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_repository.side_effect = make_client_error(
                "RepositoryDoesNotExistException"
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(ValueError, match="does not exist"):
                await get_repository_metadata("nonexistent-repo")
