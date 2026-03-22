# Methods/yak_repository_parser.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import inspect
import orjson

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()


def get_command_node(repo, command_path_parts, function_name):
    """
    Traverses the repository to find the base node for a command and logs each step.
    Returns the command's base dictionary or None if not found.
    """
    if LOCAL_DEBUG: logger.debug(f"🔍🔵 Entering {function_name} to get command node for path: {command_path_parts}.")

    current_node = repo

    for part in command_path_parts:
        if LOCAL_DEBUG: logger.debug(f"🔍 Trying to get part: '{part}' from current_node.")

        current_node = current_node.get(part)

        if not current_node:
            logger.error(f"❌ Error: Command path not found at intermediate step.")
            return None

        if LOCAL_DEBUG: logger.debug(f"🔍 Succeeded. Current node keys are now: {list(current_node.keys())}")

    return current_node


def lookup_scpi_command(command_node, model_key, command_path):
    """
    Looks up and returns the SCPI command string from a given command node.
    """
    current_function_name = inspect.currentframe().f_code.co_name

    scpi_details = command_node.get("scpi_details", {})
    scpi_value = scpi_details.get(model_key, {}).get("SCPI_value")

    scpi_path = command_path + [f"scpi_details/{model_key}/SCPI_value"]

    if scpi_value:
        if LOCAL_DEBUG: logger.success(f"✅ SCPI Command found at path: {'/'.join(scpi_path)}")
        if LOCAL_DEBUG: logger.success(f"✅ SCPI Command: {scpi_value}")
        return scpi_value
    else:
        if LOCAL_DEBUG: logger.debug(f"🟡 SCPI Command not found for model '{model_key}' at path: {'/'.join(scpi_path)}")
        return None


def lookup_inputs(command_node, command_path):
    """
    Looks up and returns the inputs for a given command node.
    """
    current_function_name = inspect.currentframe().f_code.co_name

    Input_path = command_path + ["Input"]
    Input = command_node.get("Input")

    if Input:
        inputs_count = len(Input)
        input_details = " ".join(
            [
                f"({key} = {details.get('value', 'N/A')})"
                for key, details in Input.items()
            ]
        )
        if LOCAL_DEBUG: logger.success(f"✅ Inputs found at path: {'/'.join(Input_path)}")
        if LOCAL_DEBUG: logger.debug(f"➡️ Input = {inputs_count} {input_details}")
        return Input
    else:
        if LOCAL_DEBUG: logger.debug("🟡 No inputs found.")
        return None


def lookup_outputs(command_node, command_path):
    """
    Looks up and returns the outputs for a given command node.
    """
    current_function_name = inspect.currentframe().f_code.co_name

    Outputs_path = command_path + ["Outputs"]
    Outputs = command_node.get("Outputs")

    if Outputs:
        outputs_count = len(Outputs)
        output_details = " ".join(
            [
                f"({key} = {details.get('value', 'N/A')})"
                for key, details in Outputs.items()
            ]
        )
        if LOCAL_DEBUG: logger.success(f"✅ Outputs found at path: {'/'.join(Outputs_path)}")
        if LOCAL_DEBUG: logger.debug(f"⬅️ Outputs = {outputs_count} {output_details}")
        return Outputs
    else:
        if LOCAL_DEBUG: logger.debug("🟡 No outputs found.")
        return None
