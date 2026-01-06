import json
import os
import csv
import re

try:
    from workers.logger.logger import debug_logger
    from workers.logger.log_utils import _get_log_args
except (ImportError, ModuleNotFoundError):
    # Fallback for standalone execution
    def debug_logger(message, **kwargs):
        level = kwargs.get("level", "INFO")
        print(f"[{level}] {message}")

    def _get_log_args():
        return {}


# Define paths relative to this script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
VISA_FLEET_JSON_PATH = os.path.join(PROJECT_ROOT, "DATA", "VISA_FLEET.json")
CSV_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "DATA", "Tables")


class VisaCsvBuilder:
    def __init__(self, json_path=VISA_FLEET_JSON_PATH, csv_dir=CSV_OUTPUT_DIR):
        self.json_path = json_path
        self.csv_dir = csv_dir
        debug_logger(
            message=f"Initializing with JSON Path: {self.json_path}", **_get_log_args()
        )
        debug_logger(message=f"CSV Output Directory: {self.csv_dir}", **_get_log_args())

    def build_csvs_from_json(self):
        """
        Main method to load the VISA_FLEET.json and generate a CSV file for each table found.
        """
        debug_logger(
            message="Starting CSV build process (per table)...", **_get_log_args()
        )
        if not os.path.exists(self.json_path):
            debug_logger(
                message=f"JSON file not found at {self.json_path}",
                level="ERROR",
                **_get_log_args(),
            )
            return

        os.makedirs(self.csv_dir, exist_ok=True)

        # --- NEW: Clear existing CSV files ---
        debug_logger(
            message=f"Clearing existing CSV files from {self.csv_dir}...",
            **_get_log_args(),
        )
        for filename in os.listdir(self.csv_dir):
            if filename.endswith(".csv"):
                file_path = os.path.join(self.csv_dir, filename)
                try:
                    os.remove(file_path)
                    debug_logger(
                        message=f"  Removed old file: {filename}", **_get_log_args()
                    )
                except Exception as e:
                    debug_logger(
                        message=f"  Error removing file {file_path}: {e}",
                        level="ERROR",
                        **_get_log_args(),
                    )

        with open(self.json_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                debug_logger(
                    message=f"Error decoding JSON from {self.json_path}: {e}",
                    level="ERROR",
                    **_get_log_args(),
                )
                return

        # Start the recursive traversal from the root
        self._traverse_and_build(data, ["OPEN-AIR"])
        debug_logger(message="CSV build process complete.", **_get_log_args())

    def _traverse_and_build(self, node, current_path):
        """
        Recursively traverses the JSON structure. If a "Table" key is found,
        it triggers the CSV writing for that specific table's data.
        """
        if not isinstance(node, dict):
            return

        for key, value in node.items():
            new_path = current_path + [key]

            if key == "Table" and isinstance(value, dict):
                # Found a table, process it individually
                self._write_table_to_csv(value, new_path)
            else:
                # Continue traversing deeper
                self._traverse_and_build(value, new_path)

    def _write_table_to_csv(self, table_node, table_path):
        """
        Writes a single table's data to a CSV file.
        """
        headers = table_node.get("headers")
        data_dict = table_node.get("data")

        if not headers or not isinstance(data_dict, dict):
            debug_logger(
                message=f"Warning: Skipping path {'/'.join(table_path)} because it's not a valid table structure.",
                **_get_log_args(),
            )
            return

        data_list = list(data_dict.values())

        # Sanitize the topic path to create a valid filename
        topic_string = "/".join(table_path)
        sanitized_filename = re.sub(r"[^a-zA-Z0-9_-]", "_", topic_string) + ".csv"
        csv_filepath = os.path.join(self.csv_dir, sanitized_filename)

        debug_logger(
            message=f"Writing table for topic '{topic_string}' to '{csv_filepath}'...",
            **_get_log_args(),
        )

        try:
            with open(csv_filepath, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(
                    csvfile, fieldnames=headers, extrasaction="ignore"
                )
                writer.writeheader()
                writer.writerows(data_list)
            debug_logger(
                message=f"  Successfully wrote {len(data_list)} rows.",
                **_get_log_args(),
            )
        except Exception as e:
            debug_logger(
                message=f"  Error writing CSV file {csv_filepath}: {e}",
                level="ERROR",
                **_get_log_args(),
            )


if __name__ == "__main__":
    print("Running VisaCsvBuilder in standalone mode...")
    builder = VisaCsvBuilder()
    builder.build_csvs_from_json()
    print("Standalone run complete.")
