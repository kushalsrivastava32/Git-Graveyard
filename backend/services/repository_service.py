from git_analysis.repository_analyzer import RepositoryAnalyzer
from git_analysis.commit_analyzer import CommitAnalyzer
from git_analysis.file_analyzer import FileAnalyzer
from git_analysis.file_activity_analyzer import FileActivityAnalyzer


class RepositoryService:
    """Application layer between Flask routes and Git analysis."""

    def analyze_repository(self, path):
        repository_analyzer = RepositoryAnalyzer(path)
        repository_data = repository_analyzer.analyze()

        commit_analyzer = CommitAnalyzer(repository_analyzer.repo)
        commit_data = commit_analyzer.analyze()

        file_analyzer = FileAnalyzer(repository_analyzer.repo)
        file_data = file_analyzer.analyze()

        file_activity_analyzer = FileActivityAnalyzer(repository_analyzer.repo)
        file_activity_data = file_activity_analyzer.analyze()

        return {
            "repository": repository_data,
            "commits": commit_data,
            "files": file_data,
            "file_activity": file_activity_data,
        }