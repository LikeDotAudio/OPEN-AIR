# Report_Builder/ReportBuilder_FlameGraph.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import json
import pathlib
from oaTests.Methods.FlameGraph.flame_events import generate_table_rows

def build_tab(project_root):
    """
    Returns an HTML snippet containing the full interactive FlameGraph report.
    Loads data from JSON files in oaDataLogs/FlameGraph/.
    """
    data_dir = os.path.join(project_root, "oaDataLogs", "FlameGraph")
    
    event_json_path = os.path.join(data_dir, "event_analysis.json")
    shame_json_path = os.path.join(data_dir, "wall_of_shame.json")
    pity_json_path = os.path.join(data_dir, "wall_of_pity.json")
    svg_path = os.path.join(data_dir, "flamegraph.svg")
    
    # Check for core file
    if not os.path.exists(event_json_path):
        return "<h3>No FlameGraph Data Found</h3><p>Run the Flame Test (profiling session) to generate performance data.</p>"

    try:
        # 1. Load SVG
        svg_content = "<!-- SVG Missing -->"
        if os.path.exists(svg_path):
            with open(svg_path, 'r', encoding="utf-8") as f:
                svg_content = f.read()
                # Ensure it doesn't have the XML declaration if embedding
                if '<?xml' in svg_content:
                    svg_content = svg_content[svg_content.find('<svg'):]

        # 2. Load JSON components
        with open(event_json_path, 'r') as f:
            stats_list = json.load(f)
        
        with open(shame_json_path, 'r') as f:
            shame_report = json.load(f).get("report", "")
            
        with open(pity_json_path, 'r') as f:
            pity_report = json.load(f).get("report", "")

        # 3. Generate Table Rows and Buttons
        table_rows = generate_table_rows(stats_list)
        
        all_roots = sorted(list(set(r for s in stats_list for r in s.get('roots', []))))
        root_buttons = "".join([f'<button class="filter-btn active" id="btn-root-{l}" onclick="toggleRoot(\'{l}\')">{l}</button>' for l in all_roots])

        # 4. Load Template
        template_path = os.path.join(project_root, "oaTests", "Methods", "FlameGraph", "templates", "report_template.html")
        if not os.path.exists(template_path):
            return f"<h3>Error</h3><p>FlameGraph template missing at {template_path}</p>"
            
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # 5. Inject Data
        replacements = {
            "{{SVG_CONTENT}}": svg_content,
            "{{TABLE_ROWS}}": table_rows,
            "{{ROOT_FILTER_BUTTONS}}": root_buttons,
            "{{WALL_OF_SHAME}}": shame_report,
            "{{WALL_OF_PITTY}}": pity_report
        }

        content = template
        # Since the template is a full HTML doc, we might want to strip <html>/<body> tags
        # or just return it as is if it's going into an iframe or dedicated div.
        # For the Unified Report, we'll return the card-wrapped sections.
        
        # Extract styles from template and wrap in a unique ID to prevent bleed
        style_start = content.find("<style>")
        style_end = content.find("</style>")
        styles = content[style_start:style_end+8] if style_start != -1 else ""
        
        body_start = content.find("<body>")
        body_end = content.find("</body>")
        body = content[body_start+6:body_end] if body_start != -1 else content
        
        script_start = content.find("<script>")
        script_end = content.find("</script>")
        script = content[script_start:script_end+9] if script_start != -1 else ""

        final_html = f"{styles}\n<div id='flame-graph-root'>\n{body}\n</div>\n{script}"
        
        for placeholder, value in replacements.items():
            final_html = final_html.replace(placeholder, value)

        return final_html

    except Exception as e:
        import traceback
        return f"<h3>Error Generating FlameGraph Tab</h3><pre>{traceback.format_exc()}</pre>"
