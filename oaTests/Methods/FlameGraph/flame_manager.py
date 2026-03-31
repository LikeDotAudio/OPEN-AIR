import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# oaTests/Methods/FlameGraph/flame_manager.py
#
# Main manager for the OpenAir Performance Intelligence Engine.
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
# Version 20260329.0015.1
#
# Description:
# The FlameManager coordinates the lifecycle of a performance profiling
# session. It handles the installation of multi-threaded hooks, collection
# of call-stack statistics, and synthesis of the final intelligence report
# including SVG flame graphs and forensic analysis tables.
#
# Architectural Role:
# - Performance Lifecycle Manager: Controls start/stop of profiling hooks.
# - Intelligence Synthesizer: Aggregates raw stats into human-readable reports.

import sys
import pathlib
import os
import threading
import json
from loguru import logger

# 1. Setup Environment
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 2. Import Modular Core (using new naming convention)
from oaTests.Methods.FlameGraph.flame_capture import MultiThreadProfiler
from oaTests.Methods.FlameGraph.flame_graph import generate_flamegraph_with_flameprof
from oaTests.Methods.FlameGraph.flame_events import process_stats_for_ui, generate_table_rows
from oaTests.Methods.FlameGraph.flame_wall_shame import generate_wall_of_shame
from oaTests.Methods.FlameGraph.flame_wall_pity import generate_wall_of_pity
from oaTests.Methods.FlameGraph.flame_html import generate_final_html

from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()

# Global lock to prevent multiple synthesis runs
report_lock = threading.Lock()
report_generated = False

class FlameManager:
    """Manages the lifecycle of a profiling session."""
    def __init__(self, output_dir=None):
        self.project_root = project_root
        if output_dir:
            self.data_dir = pathlib.Path(output_dir)
        else:
            self.data_dir = self.project_root / "oaDataLogs" / "FlameGraph"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.mtp = MultiThreadProfiler()
        self.report_generated = False

    def start_profiling(self):
        """Starts the multi-threaded profiler."""
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🔥 [FLAME] Starting Multi-Thread Profiling...", "INFO")
        self.mtp.install()

    def stop_profiling(self):
        """Stops the profiler."""
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🔥 [FLAME] Stopping Profiler...", "INFO")
        self.mtp.stop()

    def generate_report(self):
        """Synthesizes the final intelligence report from collected stats."""
        global report_generated
        
        with report_lock:
            if self.report_generated:
                return None
            self.report_generated = True

        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🔥 [FLAME] Synthesizing Intelligence Report...", "INFO")
        
        ps = self.mtp.get_stats()
        svg_file = self.data_dir / "flamegraph.svg"
        html_file = self.data_dir / "flamegraph.html"
        
        # D. Process Stats
        performance_stats = process_stats_for_ui(ps)
        
        # E. Generate Components
        svg_content = generate_flamegraph_with_flameprof(ps, svg_file) or "<!-- SVG Failed -->"
        table_rows = generate_table_rows(performance_stats)
        wall_of_shame_text = generate_wall_of_shame(performance_stats, ps)
        wall_of_pity_text = generate_wall_of_pity(performance_stats, ps)
        
        # F. Generate JSON Outputs
        try:
            # 1. Event Analysis Engine Data
            with open(self.data_dir / "event_analysis.json", "w") as f:
                # Sanitize performance_stats for JSON (remove non-serializable raw_key if present)
                serializable_stats = []
                for s in performance_stats:
                    s_copy = s.copy()
                    if 'raw_key' in s_copy: del s_copy['raw_key']
                    serializable_stats.append(s_copy)
                json.dump(serializable_stats, f, indent=4)
            
            # 2. Wall of Shame Data
            with open(self.data_dir / "wall_of_shame.json", "w") as f:
                json.dump({"report": wall_of_shame_text}, f, indent=4)
                
            # 3. Wall of Pity Data
            with open(self.data_dir / "wall_of_pity.json", "w") as f:
                json.dump({"report": wall_of_pity_text}, f, indent=4)
                
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔥 [FLAME] JSON components saved to {self.data_dir}", "DEBUG")
        except Exception as e:
            logger.error(f"🔥 [FLAME] Failed to save JSON components: {e}")

        # Extract unique roots for the filter buttons
        all_roots = sorted(list(set(r for s in performance_stats for r in s['roots'])))
        root_buttons = "".join([f'<button class="filter-btn active" id="btn-root-{l}" onclick="toggleRoot(\'{l}\')">{l}</button>' for l in all_roots])
        
        # G. Assemble Final Report
        success = generate_final_html(
            svg_content=svg_content,
            table_rows=table_rows,
            root_buttons=root_buttons,
            wall_of_shame=wall_of_shame_text,
            wall_of_pitty=wall_of_pity_text,
            output_file=html_file
        )
        
        if success:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔥 [FLAME] Intelligence Report: {html_file}", "SUCCESS")
            return str(html_file)
        else:
            logger.error("🔥 [FLAME] Failed to generate HTML report.")
            return None
