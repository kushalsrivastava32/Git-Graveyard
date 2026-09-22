"""
GraveyardAnalyzer — scores each file for potential abandonment.

Takes the output of ActivityAnalyzer (per-file metrics) and the
output of RepositoryAnalyzer (repo-level context), and produces
a weighted score plus a classification bucket per file.

Scoring model (v1):
    base = (0.70 * inactivity) + (0.30 * historical)
    final = base * repo_context_multiplier * 100

Where repo_context_multiplier amplifies the score when the repo is
active (stale file in active repo = suspicious) and dampens it when
the repo itself is dormant (old file in abandoned repo is expected).

Classification buckets:
    0-29   -> healthy
    30-59  -> inactive
    60-79  -> suspicious
    80-100 -> potentially_abandoned
"""


class GraveyardAnalyzer:
    """Scores files by abandonment likelihood."""

    WEIGHT_INACTIVITY = 0.70
    WEIGHT_HISTORICAL = 0.30

    def __init__(self, activity_data, repository_data):
        self.activity_data = activity_data
        self.repository_data = repository_data

    def analyze(self):
        repo_days = self.repository_data.get(
            "repository_days_since_last_commit"
        )
        multiplier = self._repo_multiplier(repo_days)

        results = []
        for file in self.activity_data:
            days_since = file.get("days_since_last_modified")
            commit_count = file.get("commit_count", 0)

            s_inactivity = self._score_inactivity(days_since)
            s_historical = self._score_historical(
                commit_count, days_since
            )

            base = (
                self.WEIGHT_INACTIVITY * s_inactivity
                + self.WEIGHT_HISTORICAL * s_historical
            )
            score = round(base * multiplier * 100)

            results.append({
                "path": file["path"],
                "commit_count": commit_count,
                "days_since_last_modified": days_since,
                "file_age_days": file.get("file_age_days"),
                "staleness_score": score,
                "classification": self._classify(score),
                "signals": {
                    "inactivity": round(s_inactivity, 2),
                    "historical": round(s_historical, 2),
                    "repo_multiplier": round(multiplier, 2),
                },
            })

        results.sort(key=lambda r: r["staleness_score"], reverse=True)
        return results

    # ------------------------------------------------------------------
    # Signal scorers
    # ------------------------------------------------------------------

    def _score_inactivity(self, days_since):
        if days_since is None:
            return 0.5
        if days_since > 365:
            return 1.0
        if days_since > 180:
            return 0.8
        if days_since > 90:
            return 0.5
        if days_since > 30:
            return 0.2
        return 0.0

    def _score_historical(self, commit_count, days_since):
        """Higher score = more likely a file that was active but stopped."""
        if days_since is None:
            return 0.5
        if commit_count >= 10 and days_since > 180:
            return 1.0
        if commit_count >= 5 and days_since > 180:
            return 0.7
        if commit_count >= 5 and days_since > 90:
            return 0.5
        if commit_count <= 1:
            return 0.1
        return 0.2

    def _repo_multiplier(self, repo_days):
        """Amplify or dampen based on repo activity."""
        if repo_days is None:
            return 0.8
        if repo_days < 30:
            return 1.0     # active repo
        if repo_days < 180:
            return 0.7
        return 0.4         # dormant repo

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def _classify(self, score):
        if score >= 80:
            return "potentially_abandoned"
        if score >= 60:
            return "suspicious"
        if score >= 30:
            return "inactive"
        return "healthy"