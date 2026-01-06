# managers/yak_manager/yak_repository_parser.py
#
# This file (yak_repository_parser.py) provides utility functions for parsing the YAK repository, enabling lookup of SCPI commands, inputs, and outputs based on a given command node.
# A complete and comprehensive pre-amble that describes the file and the functions within.
# The purpose is to provide clear documentation and versioning.
#
# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# As the current hour is 20, no change is needed.

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


import os
import inspect
import orjson

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.logger.log_utils import _get_log_args


def get_command_node(repo, command_path_parts, function_name):
    """
    Traverses the repository to find the base node for a command and logs each step.
    Returns the command's base dictionary or None if not found.
    """
    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message=f"🔍🔵 Entering {function_name} to get command node for path: {command_path_parts}.",
            **_get_log_args(),
        )

    current_node = repo

    for part in command_path_parts:
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔍 Trying to get part: '{part}' from current_node.",
                **_get_log_args(),
            )

        current_node = current_node.get(part)

        if not current_node:
            debug_logger(
                message=f"❌ Error: Command path not found at intermediate step.",
                **_get_log_args(),
            )
            return None

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔍 Succeeded. Current node keys are now: {list(current_node.keys())}",
                **_get_log_args(),
            )

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
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"✅ SCPI Command found at path: {'/'.join(scpi_path)}",
                **_get_log_args(),
            )
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(message=f"✅ SCPI Command: {scpi_value}", **_get_log_args())
        return scpi_value
    else:
        debug_logger(
            message=f"🟡 SCPI Command not found for model '{model_key}' at path: {'/'.join(scpi_path)}",
            **_get_log_args(),
        )
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
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"✅ Inputs found at path: {'/'.join(Input_path)}",
                **_get_log_args(),
            )
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"➡️ Input = {inputs_count} {input_details}", **_get_log_args()
            )
        return Input
    else:
        debug_logger(message="🟡 No inputs found.", **_get_log_args())
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
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"✅ Outputs found at path: {'/'.join(Outputs_path)}",
                **_get_log_args(),
            )
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"⬅️ Outputs = {outputs_count} {output_details}",
                **_get_log_args(),
            )
        return Outputs
    else:
        debug_logger(message="🟡 No outputs found.", **_get_log_args())
        return None
