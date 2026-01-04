import os
from .Table_CSV_Reader import TableCsvReader
from .Table_CSV_Writer import TableCsvWriter
from workers.mqtt import mqtt_publisher_service
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
import orjson

class TableCsvCheck:
    def initialize_from_csv(self, csv_path, headers, data_topic):
        """
        Checks for a CSV file. If it exists, reads it and publishes data to MQTT
        to seed the state cache. If not, creates a blank CSV with headers.
        """
        reader = TableCsvReader()
        writer = TableCsvWriter()

        if os.path.exists(csv_path):
            debug_logger(message=f"Found existing CSV at {csv_path}. Publishing contents to seed state cache.", **_get_log_args())
            _headers, data_list = reader.read_from_csv(csv_path)
            
            if not data_list:
                return # File exists but is empty

            key_preference = ['gpib_address', 'serial_number', 'resource_string']
            
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
                mqtt_publisher_service.publish_payload(field_topic, orjson.dumps(row))
        else:
            if headers: # Only create file if headers are known
                debug_logger(message=f"No CSV found at {csv_path}. Creating blank file with headers.", **_get_log_args())
                # Create a blank file with just the headers
                writer.write_to_csv(csv_path, headers, [])
