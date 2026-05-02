# oaGui/Managers/display/app_igniter.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Handles the initial build kickoff for the GUI display.

import pathlib
from loguru import logger

def ignite_application_build(display_instance, root_dir: pathlib.Path):
    """Triggers the asynchronous initial GUI build sequence."""
    try:
        display_instance.after(
            10, 
            lambda: display_instance._build_from_directory(
                path=root_dir, 
                parent_widget=display_instance, 
                on_complete=display_instance._on_initial_build_complete
            )
        )
    except Exception as error:
        logger.exception(f"🖥️🏗️🎨 [DISPLAY] CRITICAL: App ignition failed: {error}")
