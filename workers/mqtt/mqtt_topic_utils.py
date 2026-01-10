# mqtt/mqtt_topic_utils.py
#
# Provides utility functions for generating standardized MQTT topic strings from various inputs like path components or file paths.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1
import re
from pathlib import Path

TOPIC_DELIMITER = "/"


# Generates a standardized MQTT topic string by joining non-empty arguments with '/'.
# This function constructs a hierarchical topic path from multiple string components,
# automatically filtering out any empty parts to ensure a clean topic.
# Inputs:
#     *args (str): Variable number of string arguments representing topic components.
# Outputs:
#     str: The concatenated MQTT topic string.
def get_topic(*args: str) -> str:
    """
    Generates a standardized MQTT topic string by joining non-empty arguments with '/'.
    """
    return TOPIC_DELIMITER.join(arg for arg in args if arg)


# Generates a hierarchical MQTT topic path from a given file path.
# This function converts a file system path into an MQTT topic by:
# 1. Making it relative to the project root.
# 2. Filtering out structural directory names (e.g., "display", "left_").
# 3. Removing numerical prefixes from directory names.
# Inputs:
#     file_path (Path): The `pathlib.Path` object for the file.
#     project_root (Path): The `pathlib.Path` object for the project's root directory.
# Outputs:
#     str: The generated MQTT topic path, or an empty string on error.
def generate_topic_path_from_filepath(file_path: Path, project_root: Path) -> str:
    """
    Generates a hierarchical MQTT topic path from a given file path,
    filtering out structural directories and handling component transformations.
    """
    try:
        relative_path = file_path.relative_to(project_root)
        path_parts = list(relative_path.parts)
        if file_path.is_file():
            path_parts = path_parts[:-1]  # Remove the filename

        filtered_parts = []
        for part in path_parts:
            # Filter out structural elements
            if (
                part in ["display", "GUI", "gui"]
                or part.startswith("left_")
                or part.startswith("right_")
                or part.startswith("top_")
                or part.startswith("bottom_")
            ):
                continue

            # General rule: remove numerical prefix, preserve case
            processed_part = re.sub(r"^\d+_", "", part)

            # Ensure the processed part is not empty after transformations
            if processed_part:
                filtered_parts.append(processed_part)

        # Join the processed parts to form the MQTT topic path
        return TOPIC_DELIMITER.join(filtered_parts)
    except ValueError:
        # Handle cases where file_path is not relative to project_root
        return ""
    except Exception as e:
        # Log any other unexpected errors during path processing
        print(f"Error generating topic path from filepath {file_path}: {e}")
        return ""


# Generates a standardized base MQTT topic string by prepending "OPEN-AIR/" to a module name.
# This function provides a consistent way to construct a top-level topic
# for a given application module or component.
# Inputs:
#     module_name (str): The name of the module (e.g., "yak/bandwidth").
# Outputs:
#     str: The full base MQTT topic string (e.g., "OPEN-AIR/yak/bandwidth").
def generate_base_topic(module_name: str) -> str:
    """
    Generates a standardized base topic string.
    e.g., OPEN-AIR/yak/bandwidth
    """
    # module_name could be something like "yak/bandwidth", so we just prepend OPEN-AIR
    return f"OPEN-AIR/{module_name}"


# Generates a standardized MQTT topic string for a specific widget.
# This function concatenates a base topic with a widget's ID to create a unique
# topic path for that widget.
# Inputs:
#     base_topic (str): The base MQTT topic for a group of widgets.
#     widget_id (str): The unique identifier for the widget.
# Outputs:
#     str: The full MQTT topic string for the widget.
def generate_widget_topic(base_topic: str, widget_id: str) -> str:
    """
    Generates a standardized widget topic string from a base topic and a widget ID.
    """
    return f"{base_topic}/{widget_id}"