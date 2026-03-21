import os
import sys
import time
import glob
import webbrowser
import select
from datetime import datetime

# Ensure project root is in sys.path
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import modular components using requested filenames
from oaTests.Core.Report_Builder.run_test import TestRunner
from oaTests.Core.Report_Builder.collate_data import collate_extra_tabs
from oaTests.Core.Report_Builder.run_report_builder import ReportGenerator
from oaTests.Core.Report_Builder import clear_logs

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
        description = description.strip().replace(" " + chr(10), "<br>") # Explicitly handle newline

        self.test_results.append({
            "classname": test.__class__.__name__,
            "name": str(test),
            "status": status,
            "message": message,
            "cause": cause,
            "description": description,
            "duration": f"{duration:.4f}s"        })

    def run_flame_test_prompt(self):
        print() # Separate line for newline
        print('🔥 [FLAME TEST] Would you like to run a flame test? (y/N)') # Changed to single quotes
        print("   (Automatically cancelling in 10 seconds...)")
        
        # Non-blocking input with timeout
        rlist, _, _ = select.select([sys.stdin], [], [], 10)
        if rlist:
            response = sys.stdin.readline().strip().lower()
            if response == 'y':
                print("🚀 Launching Flame Test suite...")
                try:
                    import subprocess
                    flame_path = os.path.join(self.project_root, "oaTests", "Core", "FlameGraph", "wall_of_shame.py")
                    subprocess.run([sys.executable, flame_path])
                except Exception as e:
                    print(f"⚠️ Flame test failed: {e}")
            else:
                print("⏭️ Skipping Flame Test.")
        else:
            print("⏰ Timeout reached. Skipping Flame Test.")

    def run_cleanup_prompts(self):
        # 1. Clear MQTT Prompt
        print() # Separate line for newline
        print('🧹 [CLEANUP] Would you like to blow away the MQTT topic tree? (y/N)') # Changed to single quotes
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
        print() # Separate line for newline
        print('🧹 [CLEANUP] Would you like to blow away all cached items? (y/N)') # Changed to single quotes
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
        self.run_flame_test_prompt()

        # 2. run_test.py
        print(f"🔬 Starting Unified Test Runner...")
        test_dirs = glob.glob(os.path.join(self.project_root, "oa*", "Tests"))
        # Add the oaGuiElements tests specifically
        gui_elements_tests_dir = os.path.join(self.project_root, "oaGuiElements", "Tests")
        if os.path.exists(gui_elements_tests_dir):
            test_dirs.append(gui_elements_tests_dir)
        legacy_tests = os.path.join(self.project_root, 'tests')
        if os.path.exists(legacy_tests):
            test_dirs.append(legacy_tests)

        runner = TestRunner(self._record_result)
        runner.run(test_dirs, top_level_dir=self.project_root)

        # 3. collate_data.py
        print(f"📊 Collating extra report data...")
        extra_tabs = collate_extra_tabs(self.project_root)

        # 4. run_report_builder.py (Generate JSON and HTML via generate_html.py)
        print(f"📝 Generating unified reports...")
        generator = ReportGenerator(self.html_path, self.json_path, self.timestamp)
        generator.generate_json(self.summary, self.test_results)
        generator.generate_html(self.summary, self.test_results, extra_tabs)

        print(f"✅ Reports generated:")
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
