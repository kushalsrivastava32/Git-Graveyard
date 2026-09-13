class FileActivityAnalyzer:
    """
    Analyzes the Git activity of individual files.
    """

    def __init__(self, repo):
        self.repo = repo
    
    def _get_tracked_files(self):
        """
        Returns the paths of files tracked by Git.
        """
        return self.repo.git.ls_files().splitlines()
    
    def _get_file_commits(self, file_path):
        """
        Returns all commits that affected a specific file.
        """
        return list(
            self.repo.iter_commits(
                rev="--all",
                paths=file_path
            )
        )

    def _build_file_activity(self, file_path):
        """
        Builds activity information for a single file.
        """
        commits = self._get_file_commits(file_path)

        if not commits:
            return {
                "path": file_path,
                "commit_count": 0,
                "first_modified": None,
                "last_modified": None,
            }

        latest_commit = max(
            commits,
            key=lambda commit: commit.committed_datetime
        )

        oldest_commit = min(
            commits,
            key=lambda commit: commit.committed_datetime
        )

        return {
            "path": file_path,
            "commit_count": len(commits),
            "first_modified": oldest_commit.committed_datetime.isoformat(),
            "last_modified": latest_commit.committed_datetime.isoformat(),
        }

    def analyze(self):
        """
        Runs the complete file activity analysis.
        """
        files = self._get_tracked_files()

        return [
            self._build_file_activity(file_path)
            for file_path in files
        ]
