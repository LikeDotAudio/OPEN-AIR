import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# oaTests/Methods/FlameGraph/flame_html.py
#
# High-fidelity HTML report generator for performance intelligence.
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
# Version 20260329.0035.1
#
# Description:
# This module assembles the various components of a profiling session—SVG
# flame graphs, forensic tables, and categorical 'Walls'—into a standalone,
# interactive HTML report. It uses a template-based system to ensure a
# consistent visual identity for OPEN-AIR forensic assets.
#
# Architectural Role:
# - Report Orchestrator: Final stage of the FlameGraph pipeline.
# - UI Component Assembler: Merges SVG and statistical data into a single file.

import os
from pathlib import Path
from loguru import logger

def generate_final_html(svg_content, table_rows, root_buttons, wall_of_shame, wall_of_pitty, output_file):
    """
    Assembles SVG and statistical data into a standalone interactive HTML report.
    Loads the UI structure from a separate template file for modularity.
    """
    try:
        template_path = Path(__file__).parent / "templates" / "report_template.html"
        if not template_path.exists():
            logger.error(f"? HTML Template not found at: {template_path}")
            return False

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # Perform surgical string replacements
        replacements = {
            "{{SVG_CONTENT}}": svg_content,
            "{{TABLE_ROWS}}": table_rows,
            "{{ROOT_FILTER_BUTTONS}}": root_buttons,
            "{{WALL_OF_SHAME}}": wall_of_shame,
            "{{WALL_OF_PITTY}}": wall_of_pitty
        }

        content = template
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)

        with open(output_file, 'w', encoding="utf-8") as f:
            f.write(content)
            
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"? Standalone Performance Report generated: {output_file}", "SUCCESS")
        return True

    except Exception as e:
        logger.exception(f"? Failed to generate FlameGraph HTML: {e}")
        return False
