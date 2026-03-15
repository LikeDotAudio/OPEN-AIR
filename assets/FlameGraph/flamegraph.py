# assets/FlameGraph/flamegraph.py
#
# Main entry point for the OpenAir Performance Intelligence Engine.
# Orchestrates multi-threaded profiling and modular report generation.
#
# Author: Anthony Peter Kuzub
# Version 20260218.Modular.1

import sys
import pathlib
import os
import threading

# 1. Setup Environment
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 2. Import Modular Core
from core.capture_data import MultiThreadProfiler
from core.make_graph import generate_flamegraph_with_flameprof
from core.handle_events import process_stats_for_ui, generate_table_rows
from core.wall_of_shame import generate_wall_of_shame
from core.Wall_of_pitty import generate_wall_of_pitty
from core.make_html import generate_final_html
from core.DeleteCache import delete_local_data
from core.ClearMQTT import MQTTSweeper

from managers.configini.config_reader import Config
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
    
    ps = mtp.get_stats()
    svg_file = current_dir / "flamegraph.svg"
    html_file = current_dir / "flamegraph.html"
    
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

    # G. Post-Analysis Cleanup
    print("🧹 Cleaning up MQTT state...")
    try:
        sweeper = MQTTSweeper(
            app_constants.MQTT_BROKER_ADDRESS, 
            int(app_constants.MQTT_BROKER_PORT), 
            app_constants.MQTT_BASE_TOPIC
        )
        sweeper.sweep()
    except Exception as e:
        print(f"⚠️ MQTT Cleanup failed: {e}")

def main():
    # 0. Pre-Flight Cleanup (Fresh Start)
    print("🧹 Clearing DATA cache for a fresh start...")
    delete_local_data()

    # A. Initialize and Install Profiler
    mtp = MultiThreadProfiler()
    mtp.install()
    
    # B. Register Panic Callback (Handle "Halting and Catching Fire")
    try:
        from workers.watchdog.watchdog import register_panic_callback
        # Use a lambda to capture mtp but ensure it only runs once via our lock
        register_panic_callback(lambda: synthesize_report(mtp))
    except ImportError:
        pass

    # C. Launch the Application
    import OpenAir
    try:
        OpenAir.main()
    except SystemExit:
        pass
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        synthesize_report(mtp)

if __name__ == "__main__":
    main()
