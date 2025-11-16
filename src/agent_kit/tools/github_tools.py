# src/agent_kit/tools/github_tools.py
from agents.tools import function_tool


@function_tool
def write_to_github(repo: str, file_path: str, content: str) -> str:
    """
    Writes content to a file in a GitHub repository.
    This is a mock tool.
    """
    return f"Successfully wrote content to {file_path} in {repo}."
