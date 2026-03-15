import re

class StringUtils:
    """Utility functions for string manipulation within the importer."""

    @staticmethod
    def increment_trailing_digits(text):
        """Increments any trailing digits found in a string, preserving leading zeros."""
        match = re.search(r"(\d+)$", text)
        if match:
            num_str = match.group(1)
            num_int = int(num_str)
            incremented_num = num_int + 1
            new_num_str = str(incremented_num).zfill(len(num_str))
            return text[: -len(num_str)] + new_num_str
        return text
