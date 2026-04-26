# Report_Builder/run_report_builder.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import json

from oaTests.FileWriters.generate_html import HTMLGenerator


class ReportGenerator:
    def __init__(self, html_path, json_path, timestamp):
        self.html_path = html_path
        self.json_path = json_path
        self.timestamp = timestamp

    def generate_json(self, summary, details):
        with open(self.json_path, "w") as f:
            json.dump({"summary": summary, "details": details}, f, indent=4)

    def generate_html(self, summary, details, extra_tabs):
        HTMLGenerator.render(
            self.html_path,
            self.timestamp,
            summary,
            details,
            extra_tabs
        )
