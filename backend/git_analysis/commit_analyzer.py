# backend/git_analysis/commit_analyzer.py

from collections import defaultdict
from datetime import timezone
from git.exc import GitCommandError


class CommitAnalyzer:
    """
    Analyzes the commit history of a Git repository.

    This class expects an already validated GitPython Repo object.
    It does NOT validate repository paths, access databases, or handle HTTP.
    """

    def __init__(self, repo):
        """
        :param repo: A GitPython Repo object (from git import Repo)
        """
        self.repo = repo

    # ------------------------------------------------------------------
    # Public main method
    # ------------------------------------------------------------------

    def analyze(self):
        """
        Main entry point. Returns a dictionary with commit-history data.

        If the repository has no commits, returns a dict with zeroed/empty
        values instead of raising an error.
        """
        commits = self._get_all_unique_commits()

        if not commits:
            return self._empty_result()

        # Sort commits by committed date (oldest first) for easy indexing
        commits.sort(key=lambda c: c.committed_datetime)

        return {
            "total_commits": len(commits),
            "latest_commit": self._format_commit(commits[-1]),
            "first_commit": self._format_commit(commits[0]),
            "contributors": self._build_contributors(commits),
            "commit_activity": self._build_commit_activity(commits),
            "recent_commits": [
                self._format_commit(c) for c in commits[-10:][::-1]
            ],
        }

    # ------------------------------------------------------------------
    # Commit collection
    # ------------------------------------------------------------------

    def _get_all_unique_commits(self):
        """
        Collect commits from all refs using '--all', avoiding duplicates.

        Uses a dict keyed by commit hexsha to deduplicate shared history.
        Returns a list of GitPython Commit objects.
        """
        unique_commits = {}

        try:
            for commit in self.repo.iter_commits("--all"):
                # dict assignment naturally deduplicates by hexsha
                unique_commits[commit.hexsha] = commit
        except GitCommandError as e:
            raise RuntimeError(
                f"Git command failed while reading commits: {e}"
            ) from e
        except Exception as e:
            # Covers unusual/corrupt histories without hiding the cause
            raise RuntimeError(
                f"Unexpected error while reading commits: {e}"
            ) from e

        return list(unique_commits.values())

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    def _format_commit(self, commit):
        """
        Convert a GitPython Commit object into a JSON-friendly dict.
        Dates are returned as ISO 8601 strings (timezone-aware when possible).
        """
        return {
            "hash": commit.hexsha,
            "author_name": commit.author.name,
            "author_email": commit.author.email,
            "date": self._to_iso_string(commit.committed_datetime),
            "message": commit.message.strip(),
        }

    def _to_iso_string(self, dt):
        """
        Convert a datetime to an ISO 8601 string.
        Ensures timezone awareness (defaults to UTC if naive).
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    # ------------------------------------------------------------------
    # Contributors
    # ------------------------------------------------------------------

    def _build_contributors(self, commits):
        """
        Build contributor info: unique count + per-contributor commit counts.

        Contributors are keyed by email (falls back to name if email missing).
        """
        counts = defaultdict(int)
        names = {}

        for commit in commits:
            email = commit.author.email or commit.author.name or "unknown"
            counts[email] += 1
            # Keep the most recently seen display name
            names[email] = commit.author.name or "unknown"

        contributors_list = [
            {
                "name": names[email],
                "email": email,
                "commit_count": count,
            }
            for email, count in counts.items()
        ]

        # Sort by most active contributor first
        contributors_list.sort(key=lambda c: c["commit_count"], reverse=True)

        return {
            "total_contributors": len(contributors_list),
            "details": contributors_list,
        }

    # ------------------------------------------------------------------
    # Commit activity
    # ------------------------------------------------------------------

    def _build_commit_activity(self, commits):
        """
        Aggregate commits by year and by month (YYYY-MM).
        Useful later for determining repository activity/inactivity.
        """
        by_year = defaultdict(int)
        by_month = defaultdict(int)

        for commit in commits:
            dt = commit.committed_datetime
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            by_year[str(dt.year)] += 1
            by_month[dt.strftime("%Y-%m")] += 1

        return {
            "commits_by_year": dict(sorted(by_year.items())),
            "commits_by_month": dict(sorted(by_month.items())),
        }

    # ------------------------------------------------------------------
    # Empty repository result
    # ------------------------------------------------------------------

    def _empty_result(self):
        """
        Returned when a repository has no commits at all.
        """
        return {
            "total_commits": 0,
            "latest_commit": None,
            "first_commit": None,
            "contributors": {
                "total_contributors": 0,
                "details": [],
            },
            "commit_activity": {
                "commits_by_year": {},
                "commits_by_month": {},
            },
            "recent_commits": [],
        }