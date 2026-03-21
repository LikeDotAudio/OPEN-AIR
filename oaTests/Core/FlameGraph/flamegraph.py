# assets/Testing/FlameGraph/flamegraph.py
#
# Main entry point for the OpenAir Performance Intelligence Engine.
# Orchestrates multi-threaded profiling and modular report generation.
#

import sys
import pathlib
import os
import threading

# --- Constants ---
VERSION = "20260218.Modular.1"

# 1. Setup Environment
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 2. Import Modular Core
from .capture import MultiThreadProfiler
from .make_graph import generate_flamegraph_with_flameprof
from .handle_events import process_stats_for_ui, generate_table_rows
from .wall_of_shame import generate_wall_of_shame
from .Wall_of_pitty import generate_wall_of_pitty
from .make_html import generate_final_html


from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()

# Global lock to prevent multiple synthesis runs
report_lock = threading.Lock()
report_generated = False

def synthesize_report(mtp):
    """Stops profiling and generates the final intelligence report."""
    global report_generated
    
    with report_lock:
        if report_generated:
            return
        report_generated = True

    # C. Synthesize Intelligence
    mtp.stop()
    print("\n🛑 OpenAir closed or frozen. Synthesizing Intelligence Report...")
    
    # ⚡ DATA RELOCATION: Reports now kept in oaDataLogs/testing
    data_dir = project_root / "oaDataLogs" / "testing" / "FlameGraph"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    ps = mtp.get_stats()
    svg_file = data_dir / "flamegraph.svg"
    html_file = data_dir / "flamegraph.html"
    
    # D. Process Stats
    stats_list = process_stats_for_ui(ps)
    
    # E. Generate Components
    svg_content = generate_flamegraph_with_flameprof(ps, svg_file) or "<!-- SVG Failed -->"
    table_rows = generate_table_rows(stats_list)
    wall_of_shame_text = generate_wall_of_shame(stats_list, ps)
    wall_of_pitty_text = generate_wall_of_pitty(stats_list, ps)
    
    # Extract unique roots for the filter buttons
    all_roots = sorted(list(set(r for s in stats_list for r in s['roots'])))
    root_buttons = "".join([f'<button class="filter-btn active" id="btn-root-{l}" onclick="toggleRoot(\'{l}\')">{l}</button>' for l in all_roots])
    
    # F. Assemble Final Report
    generate_final_html(
        svg_content=svg_content,
        table_rows=table_rows,
        root_buttons=root_buttons,
        wall_of_shame=wall_of_shame_text,
        wall_of_pitty=wall_of_pitty_text,
        output_file=html_file
    )
    
    print(f"✅ Intelligence Report: {html_file}")
    # Show the wordy report first in console
    print("\n" + wall_of_pitty_text[:1000] + "...\n[Report Truncated - Open HTML for full details]")

   
def main():
    # 0. Pre-Flight Cleanup (Fresh Start)
    print("🧹 Clearing DATA cache for a fresh start...")
   

    # A. Initialize and Install Profiler
    mtp = MultiThreadProfiler()
    mtp.install()
    
    # B. Register Panic Callback (Handle "Halting and Catching Fire")
    import importlib.util
    watchdog_path = "oaWatchdog.watchdog"
    if importlib.util.find_spec(watchdog_path):
        from oaWatchdog.Managers.watchdog import register_panic_callback
        # Use a lambda to capture mtp but ensure it only runs once via our lock
        register_panic_callback(lambda: synthesize_report(mtp))

    # C. Launch the Application
    import OpenAir
    # OpenAir.main() refactored to not raise exceptions or use sys.exit for control flow
    OpenAir.main()
    
    # Always synthesize report after main loop finishes
    synthesize_report(mtp)

if __name__ == "__main__":
    main()
