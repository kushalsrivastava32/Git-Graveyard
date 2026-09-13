"""
GitHub provider — NOT implemented yet.

This file exists so the architecture is ready when you get to it.
Right now it raises NotImplementedError, which is fine: you can wire
the route to accept a GitHub URL and let this raise until you fill it in.
"""

from .base import RepositoryProvider


class GitHubRepositoryProvider(RepositoryProvider):
    """Placeholder for GitHub-based analysis. Fill in as next milestone."""

    def __init__(self, owner: str, repo: str, token: str | None = None):
        self.owner = owner
        self.repo_name = repo
        self.token = token

    def get_repo(self):
        raise NotImplementedError(
            "GitHub provider is not implemented yet. "
            "Next milestone: use PyGithub to fetch metadata and file tree."
        )

    def get_source_type(self) -> str:
        return "github"