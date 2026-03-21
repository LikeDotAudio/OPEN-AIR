# oaTests/Core/make_html.py
# Modularized HTML Report Generator for FlameGraphs.
# Version 20260315.Modular.1

import os
from pathlib import Path
from loguru import logger
def generate_final_html(svg_content, table_rows, root_buttons, wall_of_shame, wall_of_pitty):
    """
    Assembles SVG and statistical data into a standalone interactive HTML report.
    Loads the UI structure from a separate template file for modularity.
    """
    try:
        # Template is in a subfolder of this script
        template_path = Path(__file__).parent / "templates" / "report_template.html"
        if not template_path.exists():
            logger.error(f"❌ HTML Template not found at: {template_path}")
            return "<html><body><h1>Error: Template not found</h1></body></html>"

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

        logger.success("✅ Standalone Performance Report generated in memory.")
        return content

    except Exception as e:
        logger.exception(f"❌ Failed to generate FlameGraph HTML: {e}")
        return f"<html><body><h1>Error: {e}</h1></body></html>"
