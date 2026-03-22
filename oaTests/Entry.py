# oaTests/Entry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import sys
import time
import glob
import webbrowser
import select
import subprocess
from datetime import datetime

# Ensure project root is in sys.path for module resolution
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import modular components using requested filenames
from oaTests.Core.report_runner.run_test import TestRunner
from oaTests.Core.report_runner.collate_data import collate_extra_tabs
from oaTests.Core.report_runner.run_report_builder import ReportGenerator
from oaTests.Core.report_runner import DiscoverTests
from oaTests.Core.CleanupUtilities import clear_logs

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
        """Callback for TestRunner to log results into the internal summary."""
        self.summary["total"] += 1
        if status == "passed": self.summary["passed"] += 1
        elif status == "failed": self.summary["failed"] += 1
        elif status == "error": self.summary["errors"] += 1
        elif status == "skipped": self.summary["skipped"] += 1

        description = getattr(test, "_testMethodDoc", "") or "No description provided."
        # Ensure newlines in docstrings render as HTML breaks
        description = description.strip().replace("\n", "<br>")

        self.test_results.append({
            "classname": test.__class__.__name__,
            "name": str(test),
            "status": status,
            "message": message,
            "cause": cause,
            "description": description,
            "duration": f"{duration:.4f}s"
        })

    def _run_timed_prompt(self, label, question, script_path):
        """Helper to handle the repetitive timeout-based prompts."""
        print(f"\n{label} {question} (y/N)")
        print("   (Automatically cancelling in 10 seconds...)")
        
        rlist, _, _ = select.select([sys.stdin], [], [], 10)
        if rlist:
            response = sys.stdin.readline().strip().lower()
            if response == 'y':
                print(f"🚀 Launching {os.path.basename(script_path)}...")
                try:
                    subprocess.run([sys.executable, script_path])
                except Exception as e:
                    print(f"⚠️ Task failed: {e}")
            else:
                print("⏭️ Skipping task.")
        else:
            print("⏰ Timeout reached. Skipping task.")

    def execute(self):
        # 1. Optional Flame Test
        flame_path = os.path.join(self.project_root, "oaTests", "Core", "FlameGraph", "Entry.py")
        self._run_timed_prompt("🔥 [FLAME TEST]", "Would you like to run a flame test?", flame_path)

        # 2. run_test.py (IMPORT & DISCOVERY FIX)
        print(f"\n🔬 Starting Deep Test Discovery...")
        
        # Identify directories containing tests
        found_dirs = DiscoverTests.identify_test_directories(self.project_root)
        DiscoverTests.print_discovery_summary(self.project_root, found_dirs)

        # Execute the runner. 
        # By passing [self.project_root], we give unittest a valid 'importable' start point.
        runner = TestRunner(self._record_result)
        runner.run([self.project_root], top_level_dir=self.project_root)

        # 3. collate_data.py
        print(f"\n📊 Collating extra report data...")
        extra_tabs = collate_extra_tabs(self.project_root)

        # 4. run_report_builder.py
        print(f"📝 Generating unified reports...")
        generator = ReportGenerator(self.html_path, self.json_path, self.timestamp)
        generator.generate_json(self.summary, self.test_results)
        generator.generate_html(self.summary, self.test_results, extra_tabs)

        print(f"✅ Reports generated:")
        print(f"   - JSON: {self.json_path}")
        print(f"   - HTML: {self.html_path}")

        # 5. clear_logs.py
        # [DISABLED] Do not delete source audits or logs as they are needed for historical analysis.
        # clear_logs.cleanup_logs(self.html_path)

        # 6. Optional Cleanup Prompts
        mqtt_path = os.path.join(self.project_root, "oaTests", "Core", "CleanupUtilities", "ClearMQTT.py")
        cache_path = os.path.join(self.project_root, "oaTests", "Core", "CleanupUtilities", "DeleteCache.py")
        
        self._run_timed_prompt("🧹 [CLEANUP]", "Would you like to blow away the MQTT topic tree?", mqtt_path)
        self._run_timed_prompt("🧹 [CLEANUP]", "Would you like to blow away all cached items?", cache_path)

        # 7. Finalize
        print("\n🎉 MISSION ACCOMPLISHED: Unified Intelligence Report is ready.")
        
        # 8. Auto-Open
        print(f"🌐 Launching report...")
        webbrowser.open('file://' + os.path.realpath(self.html_path))

if __name__ == "__main__":
    orchestrator = UnifiedOrchestrator()
    orchestrator.execute()
