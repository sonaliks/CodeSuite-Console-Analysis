"""CodeCommit MCP Server - Tool handler implementations."""

import boto3
from botocore.exceptions import ClientError


def _get_client():
    """Create a boto3 CodeCommit client."""
    return boto3.client("codecommit")


async def list_files(repository_name: str, branch: str = "main") -> dict:
    """
    List files at the root of a CodeCommit repository.

    Args:
        repository_name: The name of the CodeCommit repository.
        branch: The branch name (defaults to 'main').

    Returns:
        Dictionary with 'files' and 'folders' arrays.
    """
    client = _get_client()

    try:
        response = client.get_folder(
            repositoryName=repository_name,
            commitSpecifier=branch,
            folderPath="/",
        )

        files = [f["relativePath"] for f in response.get("files", [])]
        folders = [f["relativePath"] for f in response.get("subFolders", [])]

        return {
            "repository_name": repository_name,
            "branch": branch,
            "path": "/",
            "files": files,
            "folders": folders,
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "RepositoryDoesNotExistException":
            raise ValueError(
                f"Repository '{repository_name}' does not exist. "
                "Please verify the repository name and try again."
            )
        elif error_code == "CommitDoesNotExistException":
            raise ValueError(
                f"Branch '{branch}' does not exist in repository '{repository_name}'. "
                "Please verify the branch name and try again."
            )
        else:
            raise ValueError(f"AWS CodeCommit error: {e.response['Error']['Message']}")


async def get_file_content(
    repository_name: str, file_path: str, branch: str = "main"
) -> dict:
    """
    Get the content of a specific file from a CodeCommit repository.

    Args:
        repository_name: The name of the CodeCommit repository.
        file_path: The path to the file within the repository.
        branch: The branch name (defaults to 'main').

    Returns:
        Dictionary with file path and content.
    """
    client = _get_client()

    try:
        response = client.get_file(
            repositoryName=repository_name,
            commitSpecifier=branch,
            filePath=file_path,
        )

        content = response["fileContent"].decode("utf-8")

        return {
            "repository_name": repository_name,
            "branch": branch,
            "file_path": file_path,
            "content": content,
            "file_size": response.get("fileSize", len(content)),
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "RepositoryDoesNotExistException":
            raise ValueError(
                f"Repository '{repository_name}' does not exist. "
                "Please verify the repository name and try again."
            )
        elif error_code == "FileDoesNotExistException":
            raise ValueError(
                f"File '{file_path}' does not exist in repository '{repository_name}' "
                f"on branch '{branch}'. Please verify the file path and try again."
            )
        elif error_code == "CommitDoesNotExistException":
            raise ValueError(
                f"Branch '{branch}' does not exist in repository '{repository_name}'. "
                "Please verify the branch name and try again."
            )
        else:
            raise ValueError(f"AWS CodeCommit error: {e.response['Error']['Message']}")


async def get_repository_metadata(repository_name: str) -> dict:
    """
    Get metadata about a CodeCommit repository.

    Args:
        repository_name: The name of the CodeCommit repository.

    Returns:
        Dictionary with repository metadata.
    """
    client = _get_client()

    try:
        response = client.get_repository(repositoryName=repository_name)
        metadata = response["repositoryMetadata"]

        return {
            "repository_name": metadata.get("repositoryName"),
            "default_branch": metadata.get("defaultBranch", "main"),
            "clone_url_http": metadata.get("cloneUrlHttp"),
            "clone_url_ssh": metadata.get("cloneUrlSsh"),
            "arn": metadata.get("Arn"),
            "description": metadata.get("repositoryDescription", ""),
            "creation_date": metadata.get("creationDate"),
            "last_modified_date": metadata.get("lastModifiedDate"),
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "RepositoryDoesNotExistException":
            raise ValueError(
                f"Repository '{repository_name}' does not exist. "
                "Please verify the repository name and try again."
            )
        else:
            raise ValueError(f"AWS CodeCommit error: {e.response['Error']['Message']}")
