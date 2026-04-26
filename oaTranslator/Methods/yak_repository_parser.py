# Methods/yak_repository_parser.py
# Author: Anthony Peter Kuzub
# Version: 20260330.0040.1
#
# Description: Utility module for traversing and resolving YAK command definitions.

import inspect

# --- Standard Debug Logging Setup ---
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()


def find_command_node(repo, command_path_parts, function_name):
    """
    Traverses the repository to locate the base node for a command and logs each step.
    Returns the command's base dictionary or None if not found.
    """
    matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, f"🔍🔵 Entering {function_name} to find command node for path: {command_path_parts}.", level="DEBUG")

    current_node = repo

    for part in command_path_parts:
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, f"🔍 Trying to get part: '{part}' from current_node.", level="DEBUG")

        current_node = current_node.get(part)

        if not current_node:
            logger.error("❌ Error: Command path not found at intermediate step.")
            return None

        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, f"🔍 Succeeded. Current node keys are now: {list(current_node.keys())}", level="DEBUG")

    return current_node


def resolve_scpi_command(command_node, model_key, command_path):
    """
    Resolves and returns the SCPI command string from a given command node.
    """
    current_function_name = inspect.currentframe().f_code.co_name

    scpi_details = command_node.get("scpi_details", {})
    scpi_value = scpi_details.get(model_key, {}).get("SCPI_value")

    scpi_path = command_path + [f"scpi_details/{model_key}/SCPI_value"]

    if scpi_value:
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, f"✅ SCPI Command resolved at path: {'/'.join(scpi_path)}", level="SUCCESS")
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, f"✅ SCPI Command: {scpi_value}", level="SUCCESS")
        return scpi_value
    else:
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, f"🟡 SCPI Command not found for model '{model_key}' at path: {'/'.join(scpi_path)}", level="DEBUG")
        return None


def retrieve_command_inputs(command_node, command_path):
    """
    Retrieves and returns the inputs for a given command node.
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
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, f"✅ Inputs retrieved at path: {'/'.join(Input_path)}", level="SUCCESS")
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, f"➡️ Input = {inputs_count} {input_details}", level="DEBUG")
        return Input
    else:
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, "🟡 No inputs found.", level="DEBUG")
        return None


def retrieve_command_outputs(command_node, command_path):
    """
    Retrieves and returns the outputs for a given command node.
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
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, f"✅ Outputs retrieved at path: {'/'.join(Outputs_path)}", level="SUCCESS")
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, f"⬅️ Outputs = {outputs_count} {output_details}", level="DEBUG")
        return Outputs
    else:
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, "🟡 No outputs found.", level="DEBUG")
        return None
