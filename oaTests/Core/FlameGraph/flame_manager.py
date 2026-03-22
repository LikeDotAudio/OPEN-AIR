# oaTests/Core/FlameGraph/flame_manager.py
#
# Main manager for the OpenAir Performance Intelligence Engine.
# Orchestrates multi-threaded profiling and modular report generation.
#

import sys
import pathlib
import os
import threading
from loguru import logger

# 1. Setup Environment
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 2. Import Modular Core (using new naming convention)
from oaTests.Core.FlameGraph.flame_capture import MultiThreadProfiler
from oaTests.Core.FlameGraph.flame_graph import generate_flamegraph_with_flameprof
from oaTests.Core.FlameGraph.flame_events import process_stats_for_ui, generate_table_rows
from oaTests.Core.FlameGraph.flame_wall_shame import generate_wall_of_shame
from oaTests.Core.FlameGraph.flame_wall_pity import generate_wall_of_pity
from oaTests.Core.FlameGraph.flame_html import generate_final_html

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
            self.data_dir = self.project_root / "oaDataLogs" / "Reports" / "FlameGraph"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.mtp = MultiThreadProfiler()
        self.report_generated = False

    def start_profiling(self):
        """Starts the multi-threaded profiler."""
        logger.info("🔥 [FLAME] Starting Multi-Thread Profiling...")
        self.mtp.install()

    def stop_profiling(self):
        """Stops the profiler."""
        logger.info("🔥 [FLAME] Stopping Profiler...")
        self.mtp.stop()

    def generate_report(self):
        """Synthesizes the final intelligence report from collected stats."""
        global report_generated
        
        with report_lock:
            if self.report_generated:
                return None
            self.report_generated = True

        logger.info("🔥 [FLAME] Synthesizing Intelligence Report...")
        
        ps = self.mtp.get_stats()
        svg_file = self.data_dir / "flamegraph.svg"
        html_file = self.data_dir / "flamegraph.html"
        
        # D. Process Stats
        stats_list = process_stats_for_ui(ps)
        
        # E. Generate Components
        svg_content = generate_flamegraph_with_flameprof(ps, svg_file) or "<!-- SVG Failed -->"
        table_rows = generate_table_rows(stats_list)
        wall_of_shame_text = generate_wall_of_shame(stats_list, ps)
        wall_of_pity_text = generate_wall_of_pity(stats_list, ps)
        
        # Extract unique roots for the filter buttons
        all_roots = sorted(list(set(r for s in stats_list for r in s['roots'])))
        root_buttons = "".join([f'<button class="filter-btn active" id="btn-root-{l}" onclick="toggleRoot(\'{l}\')">{l}</button>' for l in all_roots])
        
        # F. Assemble Final Report
        success = generate_final_html(
            svg_content=svg_content,
            table_rows=table_rows,
            root_buttons=root_buttons,
            wall_of_shame=wall_of_shame_text,
            wall_of_pitty=wall_of_pity_text,
            output_file=html_file
        )
        
        if success:
            logger.success(f"🔥 [FLAME] Intelligence Report: {html_file}")
            return str(html_file)
        else:
            logger.error("🔥 [FLAME] Failed to generate HTML report.")
            return None
