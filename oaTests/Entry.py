import os
import sys
import time
import glob
import webbrowser
import select
from datetime import datetime
import threading

# Ensure project root is in sys.path
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import modular components using requested filenames
from oaTests.Core.Report_Builder.run_test import TestRunner
from oaTests.Core.Report_Builder.collate_data import collate_extra_tabs
from oaTests.Core.Report_Builder.run_report_builder import ReportGenerator
from oaTests.Core.Report_Builder import clear_logs

# Imports for FlameGraph Generation
from oaTests.Core.FlameGraph.capture import MultiThreadProfiler
from oaTests.Core.FlameGraph.make_graph import generate_flamegraph_with_flameprof
from oaTests.Core.FlameGraph.handle_events import process_stats_for_ui, generate_table_rows
from oaTests.Core.FlameGraph.wall_of_shame import generate_wall_of_shame
from oaTests.Core.FlameGraph.Wall_of_pitty import generate_wall_of_pitty
from oaTests.Core.FlameGraph.make_html import generate_final_html
from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()

class UnifiedOrchestrator:
    def __init__(self):
        self.project_root = os.getcwd()
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.file_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        self.reports_dir = os.path.join(self.project_root, 'oaDataLogs', 'Reports')
        os.makedirs(self.reports_dir, exist_ok=True)
        
        self.html_path = os.path.join(self.reports_dir, f'UnifiedReport_{self.file_timestamp}.html')
        self.json_path = os.path.join(self.reports_dir, f'UnifiedReport_{self.file_timestamp}.json')
        
        self.test_results = []
        self.summary = {
            "timestamp": self.timestamp,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0
        }

    def _record_result(self, test, status, message="", cause="", duration=0):
        self.summary["total"] += 1
        if status == "passed": self.summary["passed"] += 1
        elif status == "failed": self.summary["failed"] += 1
        elif status == "error": self.summary["errors"] += 1
        elif status == "skipped": self.summary["skipped"] += 1

        description = getattr(test, "_testMethodDoc", "") or "No description provided."
        description = description.strip().replace("
", "<br>")

        self.test_results.append({
            "classname": test.__class__.__name__,
            "name": str(test),
            "status": status,
            "message": message,
            "cause": cause,
            "description": description,
            "duration": f"{duration:.4f}s"
        })

    def generate_flamegraph_report(self):
        print("
🔥 [FLAME TEST] Running flame test...")
        try:
            # A. Initialize and Install Profiler
            mtp = MultiThreadProfiler()
            mtp.install()

            # B. Launch the Application (in a thread)
            import OpenAir
            app_thread = threading.Thread(target=OpenAir.main)
            app_thread.start()
            app_thread.join(timeout=60) # Run for a max of 60 seconds

            # C. Synthesize Intelligence
            mtp.stop()
            print("
🛑 OpenAir closed or frozen. Synthesizing Intelligence Report...")
            
            ps = mtp.get_stats()
            
            # D. Process Stats
            stats_list = process_stats_for_ui(ps)
            
            # E. Generate Components
            svg_content = generate_flamegraph_with_flameprof(ps, None) or "<!-- SVG Failed -->"
            table_rows = generate_table_rows(stats_list)
            wall_of_shame_text = generate_wall_of_shame(stats_list, ps)
            wall_of_pitty_text = generate_wall_of_pitty(stats_list, ps)
            
            # Extract unique roots for the filter buttons
            all_roots = sorted(list(set(r for s in stats_list for r in s['roots'])))
            root_buttons = "".join([f'<button class="filter-btn active" id="btn-root-{l}" onclick="toggleRoot('{l}')">{l}</button>' for l in all_roots])
            
            # F. Assemble Final Report
            return generate_final_html(
                svg_content=svg_content,
                table_rows=table_rows,
                root_buttons=root_buttons,
                wall_of_shame=wall_of_shame_text,
                wall_of_pitty=wall_of_pitty_text
            )
        except Exception as e:
            print(f"⚠️ Flame test failed: {e}")
            return f"<html><body><h1>Flame test failed</h1><p>{e}</p></body></html>"

    def run_cleanup_prompts(self):
        # 1. Clear MQTT Prompt
        print("
🧹 [CLEANUP] Would you like to blow away the MQTT topic tree? (y/N)")
        print("   (Automatically cancelling in 10 seconds...)")
        rlist, _, _ = select.select([sys.stdin], [], [], 10)
        if rlist and sys.stdin.readline().strip().lower() == 'y':
            print("🚀 Running ClearMQTT...")
            try:
                import subprocess
                mqtt_path = os.path.join(self.project_root, "oaTests", "Core", "CleanupUtilities", "ClearMQTT.py")
                subprocess.run([sys.executable, mqtt_path])
            except Exception as e:
                print(f"⚠️ MQTT cleanup failed: {e}")
        else:
            print("⏭️ Skipping MQTT cleanup.")

        # 2. Delete Cache Prompt
        print("
🧹 [CLEANUP] Would you like to blow away all cached items? (y/N)")
        print("   (Automatically cancelling in 10 seconds...)")
        rlist, _, _ = select.select([sys.stdin], [], [], 10)
        if rlist and sys.stdin.readline().strip().lower() == 'y':
            print("🚀 Running DeleteCache...")
            try:
                import subprocess
                cache_path = os.path.join(self.project_root, "oaTests", "Core", "CleanupUtilities", "DeleteCache.py")
                subprocess.run([sys.executable, cache_path])
            except Exception as e:
                print(f"⚠️ Cache deletion failed: {e}")
        else:
            print("⏭️ Skipping cache deletion.")

    def execute(self):
        # 1. Optional Flame Test
        flamegraph_html = self.generate_flamegraph_report()

        # 2. run_test.py
        print(f"
🔬 Starting Unified Test Runner...")
        test_dirs = glob.glob(os.path.join(self.project_root, "oa*", "Tests"))
        legacy_tests = os.path.join(self.project_root, 'tests')
        if os.path.exists(legacy_tests):
            test_dirs.append(legacy_tests)

        runner = TestRunner(self._record_result)
        runner.run(test_dirs, top_level_dir=self.project_root)

        # 3. collate_data.py
        print(f"
📊 Collating extra report data...")
        extra_tabs = collate_extra_tabs(self.project_root)
        extra_tabs['flamegraph'] = flamegraph_html

        # 4. run_report_builder.py (Generate JSON and HTML via generate_html.py)
        print(f"
📝 Generating unified reports...")
        generator = ReportGenerator(self.html_path, self.json_path, self.timestamp)
        generator.generate_json(self.summary, self.test_results)
        generator.generate_html(self.summary, self.test_results, extra_tabs)

        print(f"
✅ Reports generated:")
        print(f"   - JSON: {self.json_path}")
        print(f"   - HTML: {self.html_path}")

        # 5. clear_logs.py
        clear_logs.cleanup_logs(self.html_path)

        # 6. Optional Cleanup Prompts
        self.run_cleanup_prompts()

        # 7. Celebrate
        print("🎉 MISSION ACCOMPLISHED: Unified Intelligence Report is ready.")
        
        # 8. Auto-Open
        print(f"🌐 Launching report...")
        webbrowser.open('file://' + os.path.realpath(self.html_path))

if __name__ == "__main__":
    orchestrator = UnifiedOrchestrator()
    orchestrator.execute()
