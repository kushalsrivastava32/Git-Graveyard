from git_analysis.repository_analyzer import RepositoryAnalyzer
from git_analysis.commit_analyzer import CommitAnalyzer


class RepositoryService:
    """Application layer between Flask routes and Git analysis."""

    def analyze_repository(self, path):
        repository_analyzer = RepositoryAnalyzer(path)

        repository_data = repository_analyzer.analyze()

        commit_analyzer = CommitAnalyzer(repository_analyzer.repo)

        commit_data = commit_analyzer.analyze()

        return {
            "repository": repository_data,
            "commits": commit_data,
        }