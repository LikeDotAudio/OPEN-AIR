# oaTests/Core/Report_Builder/ReportBuilder_FlameGraph.py
import os

def build_tab(project_root):
    """
    Returns an HTML snippet pointing to the latest FlameGraph report.
    """
    flame_report_path = os.path.join(project_root, "oaDataLogs", "Reports", "FlameGraph", "flamegraph.html")
    
    if os.path.exists(flame_report_path):
        # We use an iframe or a direct link to the standalone report
        return f"""
        <h3>Performance Flame Graph</h3>
        <p>A specialized performance report was generated during the last profiling session.</p>
        <div style="margin: 20px 0;">
            <a href="FlameGraph/flamegraph.html" target="_blank" class="tab-btn" style="text-decoration: none; display: inline-block;">
                🚀 OPEN FULL PERFORMANCE REPORT
            </a>
        </div>
        <p><i>Note: The full report contains interactive SVG graphs, Event Analysis Engine, and the Wall of Pitty.</i></p>
        <iframe src="FlameGraph/flamegraph.html" style="width: 100%; height: 600px; border: 1px solid #444; border-radius: 8px;"></iframe>
        """
    else:
        return "<h3>No FlameGraph Found</h3><p>Run the Flame Test (profiling session) to generate performance data.</p>"
