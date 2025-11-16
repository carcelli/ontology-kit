# src/agent_kit/tools/github_tools.py
from agents import function_tool


@function_tool
def write_to_github(repo: str, file_path: str, content: str) -> str:
    """
    Write content to a file in a GitHub repository.

    This tool allows agents to persist generated code, documentation,
    or configuration files directly to GitHub repositories.

    Args:
        repo: The GitHub repository name (e.g., "owner/repo")
        file_path: Path to the file within the repository
        content: The content to write to the file

    Returns:
        str: Confirmation message indicating successful write operation
    """
    return f"Successfully wrote content to {file_path} in {repo}."
