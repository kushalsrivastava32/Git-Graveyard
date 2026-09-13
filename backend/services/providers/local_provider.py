"""
Local filesystem provider — wraps the existing GitPython logic.

This is deliberately thin. It just loads the repo and hands it over.
All the actual analysis still happens in your existing analyzers.
"""

import os
import sys
from pathlib import Path

from .base import RepositoryProvider


class LocalRepositoryProvider(RepositoryProvider):
    """Provides access to a repository stored on the local filesystem."""

    def __init__(self, path: str):
        if not path:
            raise ValueError("Local repository path is required.")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path does not exist: {path}")
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Path is not a directory: {path}")

        self.path = path
        self._repo = None  # lazy-load

    def get_repo(self):
        """Return a GitPython Repo object for this path."""
        if self._repo is None:
            # Reuse the same workaround pattern as repository_analyzer.py
            # to avoid the local `git` folder shadowing GitPython.
            project_root = str(Path(__file__).resolve().parents[2])
            removed = False
            if project_root in sys.path:
                sys.path.remove(project_root)
                removed = True

            try:
                import git
                self._repo = git.Repo(self.path)
            finally:
                if removed:
                    sys.path.insert(0, project_root)

        return self._repo

    def get_source_type(self) -> str:
        return "local"