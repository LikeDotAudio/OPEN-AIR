from loguru import logger
import os

def handle_file_read_error(filepath, exception, fallback=None):
    """
    Standardized handler for file reading exceptions.
    Logs the error and returns a safe fallback value.
    """
    logger.error(f"📂🚫 [READ ERROR] Failed to read file: {filepath}")
    logger.error(f"  └─ Reason: {exception}")
    
    # Optional: Logic to notify UI or trigger system recovery could be added here
    return fallback

def handle_file_write_error(filepath, exception):
    """
    Standardized handler for file writing exceptions.
    Logs the error and returns False to indicate failure.
    """
    logger.error(f"📂💾🚫 [WRITE ERROR] Failed to write file: {filepath}")
    logger.error(f"  └─ Reason: {exception}")
    
    # Logic for handling disk full, permission denied, etc.
    return False
