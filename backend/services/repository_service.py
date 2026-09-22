"""
RepositoryService — orchestration layer for Git Graveyard.

Responsibility:
    Coordinate all analyzers and combine their output into one dict.

Design note (3rd-year scope):
    This file does NOT know how to talk to GitHub or the filesystem.
    It only knows how to call analyzers in the right order.

    The SOURCE of repository data (local path vs GitHub) is handled
    by a small provider object passed in by the caller (the Flask route).
    This keeps RepositoryService source-agnostic and testable.

Backward compatibility:
    analyze_repository("D:\\path") still works — it internally
    builds a LocalRepositoryProvider for you.
"""

from git_analysis.repository_analyzer import RepositoryAnalyzer
from git_analysis.commit_analyzer import CommitAnalyzer
from git_analysis.file_analyzer import FileAnalyzer
from git_analysis.file_activity_analyzer import FileActivityAnalyzer
from git_analysis.activity_analyzer import ActivityAnalyzer
from git_analysis.graveyard_analyzer import GraveyardAnalyzer

from services.providers.local_provider import LocalRepositoryProvider


class RepositoryService:
    """Application layer between Flask routes and Git analysis."""

    def analyze_repository(self, source):
        """
        Analyze a repository. Accepts a local path (str) or a provider.
        If the provider supports context management (GitHub), its
        lifecycle is managed here.
        """
        provider = self._resolve_provider(source)

        if hasattr(provider, "__enter__") and hasattr(provider, "__exit__"):
            with provider:
                return self._run_analyzers(provider)
        else:
            return self._run_analyzers(provider)

    def _run_analyzers(self, provider):
        """Run all analyzers against the provider's repository."""
        repository_analyzer = RepositoryAnalyzer(provider.path)
        repository_data = repository_analyzer.analyze()
        repo = repository_analyzer.repo

        # For GitHub clones, the temp folder name is noise — use
        # the real repo name instead.
        if hasattr(provider, "repo_name") and provider.repo_name:
            repository_data["name"] = provider.repo_name

        commit_analyzer = CommitAnalyzer(repo)
        commit_data = commit_analyzer.analyze()

        file_analyzer = FileAnalyzer(repo)
        file_data = file_analyzer.analyze()

        file_activity_analyzer = FileActivityAnalyzer(repo)
        file_activity_data = file_activity_analyzer.analyze()

        activity_analyzer = ActivityAnalyzer(file_activity_data)
        activity_data = activity_analyzer.analyze()

        # Score each file for potential abandonment.
        graveyard_analyzer = GraveyardAnalyzer(
            activity_data, repository_data
        )
        graveyard_data = graveyard_analyzer.analyze()

        return {
            "repository": repository_data,
            "commits": commit_data,
            "files": file_data,
            "file_activity": file_activity_data,
            "activity": activity_data,
            "graveyard": graveyard_data,
        }
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_provider(self, source):
        """
        Turn whatever the caller passed into a RepositoryProvider.

        Accepts:
            - a string (local path)          -> LocalRepositoryProvider
            - a RepositoryProvider instance  -> used as-is
        """
        if isinstance(source, str):
            return LocalRepositoryProvider(source)

        # Duck-typing check: does it look like a provider?
        if hasattr(source, "get_repo"):
            return source

        raise TypeError(
            "analyze_repository() expects a local path (str) "
            "or a RepositoryProvider instance."
        )