# workers/utils/topic_utils.py
import re
from pathlib import Path

TOPIC_DELIMITER = "/"


def get_topic(*args: str) -> str:
    """
    Generates a standardized MQTT topic string by joining non-empty arguments with '/'.
    """
    return TOPIC_DELIMITER.join(arg for arg in args if arg)


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
            processed_part = re.sub(r"^\d+_", "", part).replace(" ", "_")

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


def generate_base_topic(module_name: str) -> str:
    """
    Generates a standardized base topic string.
    e.g., OPEN-AIR/yak/bandwidth
    """
    # module_name could be something like "yak/bandwidth", so we just prepend OPEN-AIR
    return f"OPEN-AIR/{module_name}"


def generate_widget_topic(base_topic: str, widget_id: str) -> str:
    """
    Generates a standardized widget topic string from a base topic and a widget ID.
    """
    return f"{base_topic}/{widget_id}"
