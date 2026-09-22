from datetime import datetime, timezone


class ActivityAnalyzer:
    """
    Analyzes the activity of files based on existing file activity data.
    """

    def __init__(self, file_activity):
        self.file_activity = file_activity

    def _calculate_days_since_last_modified(self, last_modified):
        """
        Calculates the number of days since a file was last modified.
        """
        if last_modified is None:
            return None

        modified_datetime = datetime.fromisoformat(last_modified)

        if modified_datetime.tzinfo is None:
            modified_datetime = modified_datetime.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(timezone.utc)

        difference = now - modified_datetime

        return difference.days

    def _calculate_file_age_days(self, first_modified):
        """
        Calculates the age of a file in days.
        """
        if first_modified is None:
            return None

        created_datetime = datetime.fromisoformat(first_modified)

        if created_datetime.tzinfo is None:
            created_datetime = created_datetime.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(timezone.utc)

        difference = now - created_datetime

        return difference.days

    def _classify_staleness(self, days_since_modified):
        """
        Rule-based v1 classification.

        Returns one of:
            unknown              -> missing data
            active               -> modified within 90 days
            inactive             -> 90-180 days
            stale                -> 180-365 days
            potentially_abandoned -> over 365 days
        """
        if days_since_modified is None:
            return "unknown"
        if days_since_modified > 365:
            return "potentially_abandoned"
        if days_since_modified > 180:
            return "stale"
        if days_since_modified > 90:
            return "inactive"
        return "active"

    def analyze(self):
        """
        Adds activity metrics and a v1 classification to each file.
        """
        results = []

        for file in self.file_activity:
            days_since = self._calculate_days_since_last_modified(
                file["last_modified"]
            )
            age_days = self._calculate_file_age_days(
                file["first_modified"]
            )

            result = {
                **file,
                "days_since_last_modified": days_since,
                "file_age_days": age_days,
                "recommendation": self._classify_staleness(days_since),
            }

            results.append(result)

        return results

