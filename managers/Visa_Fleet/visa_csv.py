# managers/Visa_Fleet/visa_csv.py
#
# Generates CSV representations of the VISA fleet inventory from JSON state.
#
# Primary Responsibilities:
# - Recursively traversing the fleet JSON structure to identify data tables.
# - Converting JSON-based instrument metadata into flat CSV files.
# - Sanitizing MQTT topic paths for use as valid filesystem filenames.
# - Providing an automated export mechanism for external tool integration.
#
# Assumptions and Constraints:
# - Assumes the existence of a source JSON file (STATE_VISA_FLEET.json).
# - Clears the target CSV directory before each build to ensure consistency.
# - Uses the keys of the first data row to dynamically determine CSV headers.
# - Requires write permissions in the target output directory.
#
# Author: Gemini Agent / Anthony Peter Kuzub

import orjson
import os
import csv
import re

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config
import workers.initialization.project_paths as app_paths

app_constants = Config.get_instance()

# --- Constants ---
STATE_VISA_FLEET_JSON_PATH = str(app_paths.STATE_VISA_FLEET_JSON_PATH)
CSV_OUTPUT_DIR = os.path.join(
    os.path.dirname(STATE_VISA_FLEET_JSON_PATH), 
    "CSV"
)

class VisaCsvBuilder:
    """
    Handles the transformation of JSON fleet inventory into CSV export files.
    """
    def __init__(self, json_path=STATE_VISA_FLEET_JSON_PATH, 
                 csv_dir=CSV_OUTPUT_DIR):
        """
        Initializes the CSV builder with source and destination paths.

        Parameters:
        - json_path: Absolute path to the source STATE_VISA_FLEET.json file.
        - csv_dir: Directory where the generated CSV files will be stored.

        Returns:
        - A new VisaCsvBuilder instance.
        """
        self.json_path = json_path
        self.csv_dir = csv_dir
        if LOCAL_DEBUG:
            logger.debug(f"Initializing with JSON Path: {self.json_path}")
            logger.debug(f"CSV Output Directory: {self.csv_dir}")

    def build_csvs_from_json(self):
        """
        Loads the fleet JSON and generates a separate CSV for each identified table.

        Returns:
        - None.

        Side Effects & Thread-Safety:
        - Creates the `csv_dir` if it does not exist.
        - Deletes all existing `.csv` files in the `csv_dir`.
        - Performs significant disk I/O (read/write).
        """
        if LOCAL_DEBUG:
            logger.debug("Starting CSV build process (per table)...")
            
        if not os.path.exists(self.json_path):
            logger.error(f"JSON file not found at {self.json_path}")
            return

        os.makedirs(self.csv_dir, exist_ok=True)

        # Clear existing CSV files to prevent stale data from lingering.
        if LOCAL_DEBUG:
            logger.debug(f"Clearing existing CSV files from {self.csv_dir}...")
            
        for filename in os.listdir(self.csv_dir):
            if filename.endswith(".csv"):
                file_path = os.path.join(self.csv_dir, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    if LOCAL_DEBUG:
                        logger.debug(f"  Removed old file: {filename}")

        with open(self.json_path, "rb") as f:
            raw_data = f.read()

        # ⚡ PRE-VALIDATION: Structural integrity check
        stripped_data = raw_data.strip()
        if not stripped_data.startswith(b"{") or not stripped_data.endswith(b"}"):
            logger.error(f"❌ Error: JSON structural validation failed for {self.json_path}. Corrupted file?")
            return

        data = orjson.loads(raw_data)

        # Start the recursive traversal from the root node.
        self._traverse_and_build(data, ["OPEN-AIR"])
        if LOCAL_DEBUG:
            logger.debug("CSV build process complete.")

    def _traverse_and_build(self, node, current_path):
        """
        Recursively explores the JSON tree searching for "Table" markers.

        Parameters:
        - node: The current dictionary or list in the JSON structure.
        - current_path: A list of strings representing the breadcrumb path.

        Returns:
        - None.
        """
        if not isinstance(node, dict):
            return

        for key, value in node.items():
            new_path = current_path + [key]

            # In our schema, a "Table" key indicates a collection of records.
            if key == "Table" and isinstance(value, dict):
                self._write_table_to_csv(value, new_path)
            else:
                self._traverse_and_build(value, new_path)

    def _write_table_to_csv(self, table_node, table_path):
        """
        Extracts data from a table node and writes it to a specific CSV file.

        Parameters:
        - table_node: The dictionary containing the "data" map.
        - table_path: The hierarchical path used to name the output file.

        Returns:
        - None.

        Side Effects & Thread-Safety:
        - Writes a new CSV file to the `csv_dir`.
        """
        data_dict = table_node.get("data")

        if not isinstance(data_dict, dict) or not data_dict:
            if LOCAL_DEBUG:
                logger.debug(f"Warning: Skipping path {'/'.join(table_path)} "
                             f"because it has no data.")
            return

        data_list = list(data_dict.values())
        
        # Dynamically determine headers from the first data row.
        # Assumes all rows in the same table share the same schema.
        headers = list(data_list[0].keys())

        # Sanitize the full topic path to create a safe filesystem filename.
        topic_string = "/".join(table_path)
        sanitized_filename = (re.sub(r"[^a-zA-Z0-9_-]", "_", topic_string) 
                              + ".csv")
        csv_filepath = os.path.join(self.csv_dir, sanitized_filename)

        if LOCAL_DEBUG:
            logger.debug(f"Writing table for topic '{topic_string}' "
                         f"to '{csv_filepath}'...")

        # We assume csv_dir is created and writable.
        with open(csv_filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=headers, extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(data_list)
        
        if LOCAL_DEBUG:
            if os.path.exists(csv_filepath):
                logger.success(f"  Successfully wrote {len(data_list)} rows to {csv_filepath}")
            else:
                logger.error(f"  Failed to write CSV file {csv_filepath}")


if __name__ == "__main__":
    # Standalone execution for testing and manual export.
    print("Running VisaCsvBuilder in standalone mode...")
    builder = VisaCsvBuilder()
    builder.build_csvs_from_json()
    print("Standalone run complete.")
