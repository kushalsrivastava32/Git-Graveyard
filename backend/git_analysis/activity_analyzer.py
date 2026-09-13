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

    def analyze(self):
        """
        Adds activity metrics to each file.
        """
        results = []

        for file in self.file_activity:
            result = {
                **file,
                "days_since_last_modified": (
                    self._calculate_days_since_last_modified(
                        file["last_modified"]
                    )
                ),
                "file_age_days": (
                    self._calculate_file_age_days(
                        file["first_modified"]
                    )
                )
            }

            results.append(result)

        return results

