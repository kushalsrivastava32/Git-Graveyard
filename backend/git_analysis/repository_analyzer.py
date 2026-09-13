import importlib
import os
import sys
from pathlib import Path
from datetime import datetime, timezone


def _import_gitpython():
    """Load GitPython's `git` module.

    This project folder is also named `git`, which would hide GitPython
    if we imported `git` normally. Temporarily hide this package, import
    GitPython, then restore our local package.
    """
    backend_dir = str(Path(__file__).resolve().parent.parent)
    original_sys_path = sys.path.copy()
    local_git_modules = {
        name: sys.modules.pop(name)
        for name in list(sys.modules)
        if name == "git" or name.startswith("git.")
    }

    sys.path = [
        entry for entry in sys.path
        if Path(entry).resolve() != Path(backend_dir).resolve()
    ]

    try:
        gitpython_module = importlib.import_module("git")
    finally:
        sys.path = original_sys_path
        for name, module in local_git_modules.items():
            sys.modules[name] = module

    return gitpython_module


gitpython = _import_gitpython()
Repo = gitpython.Repo
InvalidGitRepositoryError = gitpython.exc.InvalidGitRepositoryError
NoSuchPathError = gitpython.exc.NoSuchPathError


class PathNotFoundError(Exception):
    """Raised when the supplied path does not exist."""


class NotAGitRepositoryError(Exception):
    """Raised when the path exists but is not a Git repository."""


class RepositoryAnalyzer:
    """Reads basic information from a local Git repository."""

    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.repo = None

    def analyze(self):
        """Return a dictionary of repository details."""
        self._validate_path()
        self._open_repository()

        latest_commit = self._get_latest_commit()

        repository_days_since_last_commit = (
            self._calculate_days_since_last_commit(
                latest_commit["date"] if latest_commit else None
            )
        )

        return {
            "name": self._get_repository_name(),
            "path": self.path,
            "current_branch": self._get_current_branch(),
            "total_commits": self._count_commits(),
            "latest_commit": latest_commit,
            "repository_days_since_last_commit": repository_days_since_last_commit,
        }

    def _validate_path(self):
        if not os.path.exists(self.path):
            raise PathNotFoundError(f"Path does not exist: {self.path}")

    def _open_repository(self):
        try:
            self.repo = Repo(self.path)
        except NoSuchPathError:
            raise PathNotFoundError(f"Path does not exist: {self.path}")
        except InvalidGitRepositoryError:
            raise NotAGitRepositoryError(
                f"Path is not a Git repository: {self.path}"
            )

    def _get_repository_name(self):
        return os.path.basename(self.path)

    def _get_current_branch(self):
        try:
            if self.repo.head.is_detached:
                return None
            return self.repo.active_branch.name
        except (TypeError, ValueError):
            return None

    def _count_commits(self):
        try:
            return sum(1 for _ in self.repo.iter_commits("--all"))
        except (ValueError, gitpython.exc.GitCommandError):
            return 0

    def _get_latest_commit(self):
        try:
            commit = self.repo.head.commit
        except (ValueError, AttributeError):
            return None

        return {
            "hash": commit.hexsha,
            "author_name": commit.author.name,
            "author_email": commit.author.email,
            "date": commit.committed_datetime.isoformat(),
            "message": commit.message.strip(),
        }
    
    def _calculate_days_since_last_commit(self, last_commit_date):
        """
        Calculates the number of days since the repository's latest commit.
        """
        if last_commit_date is None:
            return None

        commit_datetime = datetime.fromisoformat(last_commit_date)

        if commit_datetime.tzinfo is None:
            commit_datetime = commit_datetime.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(timezone.utc)

        difference = now - commit_datetime

        return difference.days