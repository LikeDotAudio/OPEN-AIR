# managers/yak_manager/yak_command_builder.py
#
# This file (yak_command_builder.py) provides functionality to build SCPI commands by filling placeholders in a template with values from inputs.
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
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

LOCAL_DEBUG_ENABLE = False


def fill_scpi_placeholders(scpi_command_template: str, Input: dict):
    """
    Takes an SCPI command template and replaces placeholders with values from inputs.
    """
    current_function_name = inspect.currentframe().f_code.co_name
    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message=f"🔍🔵 Entering {current_function_name} to fill SCPI placeholders.",
            **_get_log_args(),
        )

    filled_command = scpi_command_template

    if Input:
        for key, details in Input.items():
            placeholder = f"<{key}>"
            value_to_substitute = str(details.get("value", ""))

            # --- NEW FIX: Replace the placeholder value with a single double quote for the path terminator ---
            filled_command = filled_command.replace('"', '"')

            if placeholder == "<path_terminator>" and placeholder in filled_command:
                filled_command = filled_command.replace(placeholder, '"')
                value_to_substitute = '"'

            if placeholder == "<path_starter>" and placeholder in filled_command:
                filled_command = filled_command.replace(placeholder, '"')
                value_to_substitute = '"'

            if placeholder in filled_command:
                filled_command = filled_command.replace(
                    placeholder, value_to_substitute
                )
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🔁 Replaced placeholder '{placeholder}' with value '{value_to_substitute}'.",
                        **_get_log_args(),
                    )
    debug_logger(message=f"✅ Filled SCPI Command: {filled_command}", **_get_log_args())
    return filled_command
