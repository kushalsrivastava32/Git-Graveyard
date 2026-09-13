from pathlib import Path


class FileAnalyzer:
    """
    Analyzes files tracked by a Git repository.
    """

    def __init__(self, repo):
        self.repo = repo

    def _get_tracked_files(self):
        """
        Returns the paths of files tracked by Git.
        """
        return self.repo.git.ls_files().splitlines()

    def _get_file_sizes(self, files):
        """
        Returns the size of each tracked file in bytes.

        Git can report files that no longer exist on disk (for example
        after a rename or manual deletion that hasn't been committed yet).
        Those files are skipped rather than crashing the analysis.
        """
        sizes = {}

        for file_path in files:
            full_path = Path(self.repo.working_tree_dir) / file_path
            try:
                sizes[file_path] = full_path.stat().st_size
            except FileNotFoundError:
                # Tracked by Git but absent from the working tree — skip.
                continue

        return sizes

    def _build_file_summary(self, file_sizes):
        """
        Builds basic file count and total size information.
        """
        return {
            "total_files": len(file_sizes),
            "total_size_bytes": sum(file_sizes.values()),
        }

    def _build_extension_summary(self, file_sizes):
        """
        Groups files by their file extension.
        """
        extensions = {}

        for file_path in file_sizes:
            filename = file_path.rsplit("/", 1)[-1]

            if filename.startswith(".") and filename.count(".") == 1:
                extension = "other"
            elif "." in filename:
                extension = "." + filename.rsplit(".", 1)[-1].lower()
            else:
                extension = "other"

            extensions[extension] = extensions.get(extension, 0) + 1

        return extensions

    def _build_largest_files(self, file_sizes, limit=10):
        """
        Returns the largest tracked files.
        """
        largest = sorted(
            file_sizes.items(),
            key=lambda item: item[1],
            reverse=True
        )[:limit]

        return [
            {
                "path": file_path,
                "size_bytes": size,
            }
            for file_path, size in largest
        ]

    def analyze(self):
        """
        Runs the complete file analysis.
        """
        files = self._get_tracked_files()
        file_sizes = self._get_file_sizes(files)

        summary = self._build_file_summary(file_sizes)
        extensions = self._build_extension_summary(file_sizes)
        largest_files = self._build_largest_files(file_sizes)

        return {
            **summary,
            "files_by_extension": extensions,
            "largest_files": largest_files,
        }