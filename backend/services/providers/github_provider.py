"""
GitHub provider — clones a remote repository and hands it to the
existing local analyzers.

Strategy:
    Full clone into a temporary directory. The clone is deleted when
    the provider is closed, so analysis must happen inside the
    `with` block.

Auth:
    Uses a server-side Personal Access Token from the GITHUB_TOKEN
    env var. Public repos work without a token; private repos
    require one.
"""

import os
import sys
import importlib
from pathlib import Path

from .base import RepositoryProvider


def _import_gitpython():
    """
    Import GitPython's `git` module safely.

    The project folder is named `git_analysis`, and this module may
    be imported from a context where a local `git` package would
    shadow GitPython. Same workaround pattern used in
    repository_analyzer.py.
    """
    backend_dir = str(Path(__file__).resolve().parents[2])
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


class GitHubRepoTooLargeError(Exception):
    """Raised when the repository exceeds the size limit."""


class GitHubCloneError(Exception):
    """Raised when cloning fails (bad URL, auth, network)."""


class GitHubRepositoryProvider(RepositoryProvider):
    """Provides access to a GitHub repository via a local full clone."""

    # Reject repositories larger than this (in KB) before cloning.
    # GitHub's API reports repo size in KB.
    MAX_REPO_SIZE_KB = 200 * 1024  # 200 MB

    def __init__(self, owner: str, repo: str, token: str | None = None):
        if not owner or not repo:
            raise ValueError("owner and repo are required.")

        self.owner = owner
        self.repo_name = repo
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self._temp_dir = None
        self._repo = None
        self.path = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __enter__(self):
        """Clone the repository and return self."""
        self._clone()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the temporary directory when leaving the context."""
        self.cleanup()
        return False

    def cleanup(self):
        """Delete the cloned repository and its temp directory."""
        if self._temp_dir is not None:
            try:
                self._temp_dir.cleanup()
            except Exception:
                pass
            self._temp_dir = None
            self._repo = None
            self.path = None

    # ------------------------------------------------------------------
    # RepositoryProvider interface
    # ------------------------------------------------------------------

    def get_repo(self):
        """Return the GitPython Repo object for the cloned repo."""
        if self._repo is None:
            raise RuntimeError(
                "Repository not cloned yet. Use the provider as a "
                "context manager: `with GitHubRepositoryProvider(...) as p:`"
            )
        return self._repo

    def get_source_type(self) -> str:
        return "github"

    # ------------------------------------------------------------------
    # Cloning
    # ------------------------------------------------------------------

    def _clone(self):
        """Clone the repo into a fresh temporary directory."""
        import tempfile

        # Build the clone URL. Token is optional — public repos
        # don't need it.
        if self.token:
            clone_url = (
                f"https://x-access-token:{self.token}"
                f"@github.com/{self.owner}/{self.repo_name}.git"
            )
        else:
            clone_url = (
                f"https://github.com/{self.owner}/{self.repo_name}.git"
            )

        # Create a temp directory that will be auto-cleaned on exit.
        self._temp_dir = tempfile.TemporaryDirectory(
            prefix=f"git_graveyard_{self.owner}_{self.repo_name}_"
        )

        try:
            self._repo = Repo.clone_from(
                clone_url,
                self._temp_dir.name,
                # Full clone (no depth argument) — preserves history.
            )
        except gitpython.exc.GitCommandError as e:
            self.cleanup()
            raise GitHubCloneError(
                f"Failed to clone {self.owner}/{self.repo_name}: {e}"
            ) from e

        self.path = self._temp_dir.name