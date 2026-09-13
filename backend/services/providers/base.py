"""
Base interface for repository providers.

A provider's only job: give the analyzers access to repository data,
regardless of whether that data lives on disk or on GitHub.
"""

from abc import ABC, abstractmethod


class RepositoryProvider(ABC):
    """Common interface for local and GitHub repository sources."""

    @abstractmethod
    def get_repo(self):
        """
        Return the underlying repository handle.

        For LocalRepositoryProvider: a GitPython `Repo` object.
        For GitHubRepositoryProvider: a PyGithub `Repository` object
        (or a wrapper that mimics the GitPython methods you use).

        Your analyzers currently expect a GitPython Repo, so for
        GitHub you will eventually need an adapter — but that is a
        later milestone. For now, local returns the real thing.
        """
        raise NotImplementedError

    @abstractmethod
    def get_source_type(self) -> str:
        """Return 'local' or 'github'."""
        raise NotImplementedError