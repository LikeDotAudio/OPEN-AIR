# text_table/Table_CSV_check.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: This module provides functionality to check for and initialize CSV files for table widgets, seeding MQTT with existing data or creating new files.

import os
import orjson

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from .Table_CSV_Reader import TableCsvReader
from .Table_CSV_Writer import TableCsvWriter
from oaComMQTT.Core import mqtt_publisher_service
from oaComMQTT.Methods.mqtt_topic_utils import get_topic


class TableCsvCheck:
    # Initializes the table data from a CSV file.
    # This function checks for the existence of a CSV file at the given path.
    # If the file exists, it reads its contents and publishes each row to MQTT
    # to seed the application's state cache. If the file does not exist,
    # it creates a new blank CSV file with the specified headers.
    # Inputs:
    #     csv_path (str): The full path to the CSV file.
    #     headers (list): A list of column headers for the CSV file.
    #     data_topic (str): The base MQTT topic for publishing data from the CSV.
    # Outputs:
    #     None.
    def initialize_from_csv(self, csv_path, headers, data_topic):
        """
        Checks for a CSV file. If it exists, reads it and publishes data to MQTT
        to seed the state cache. If not, creates a blank CSV with headers.
        """
        reader = TableCsvReader()
        writer = TableCsvWriter()

        if os.path.exists(csv_path):
            if LOCAL_DEBUG: logger.debug(f"Found existing CSV at {csv_path}. Publishing contents to seed state cache.")
            _headers, data_list = reader.read_from_csv(csv_path)

            if not data_list:
                return  # File exists but is empty

            key_preference = ["gpib_address", "serial_number", "resource_string"]

            for i, row in enumerate(data_list):
                item_key = None
                for key_name in key_preference:
                    if key_name in row and row[key_name]:
                        item_key = row[key_name]
                        break
                if not item_key:
                    item_key = f"row_{i}"

                # Publish to MQTT to seed the cache
                field_topic = get_topic(data_topic, "data", item_key)
                mqtt_publisher_service.publish_payload(field_topic, orjson.dumps(row).decode())
        else:
            if headers:  # Only create file if headers are known
                if LOCAL_DEBUG: logger.debug(f"No CSV found at {csv_path}. Creating blank file with headers.")
                # Create a blank file with just the headers
                writer.write_to_csv(csv_path, headers, [])
