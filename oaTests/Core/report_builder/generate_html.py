# Report_Builder/generate_html.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import html

class HTMLGenerator:
    @staticmethod
    def render(html_path, timestamp, summary, details, extra_tabs):
        # HTML Report Template
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>OPEN-AIR Unified Intelligence Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background: #1e1e1e; color: #dcdcdc; }}
        .header {{ background: #2b2b2b; padding: 20px 40px; border-bottom: 2px solid #33A1FD; }}
        h1 {{ color: #ffffff; margin: 0; font-size: 1.8em; }}
        .container {{ padding: 30px 40px; }}
        
        /* Tabs Styling */
        .tab-box {{ display: flex; border-bottom: 1px solid #444; margin-bottom: 20px; }}
        .tab-btn {{ padding: 12px 25px; cursor: pointer; background: #2b2b2b; border: none; color: #888; border-radius: 5px 5px 0 0; margin-right: 5px; transition: 0.3s; font-weight: 600; }}
        .tab-btn:hover {{ background: #333; color: #fff; }}
        .tab-btn.active {{ background: #33A1FD; color: white; }}
        .tab-content {{ display: none; background: #2b2b2b; padding: 25px; border-radius: 0 0 8px 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
        .tab-content.active {{ display: block; }}

        /* Summary Stats */
        .summary-box {{ display: flex; gap: 20px; margin-bottom: 30px; }}
        .stat {{ flex: 1; padding: 15px; border-radius: 6px; text-align: center; color: white; font-weight: bold; font-size: 1.1em; }}
        .total {{ background: #444; }}
        .passed {{ background: #27ae60; }}
        .failed {{ background: #e74c3c; }}
        .errors {{ background: #f39c12; }}

        /* Tables */
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; table-layout: auto; background: #333; }}
        th, td {{ border: 1px solid #444; padding: 12px; text-align: left; vertical-align: top; word-wrap: break-word; }}
        th {{ background-color: #3d3d3d; color: #aaa; font-weight: 600; text-transform: uppercase; font-size: 0.8em; letter-spacing: 0.05em; }}
        tr:nth-child(even) {{ background-color: #383838; }}
        tr:hover {{ background-color: #404040; }}
        .status-passed {{ color: #2ecc71; font-weight: bold; }}
        .status-failed {{ color: #e74c3c; font-weight: bold; }}
        .status-error {{ color: #f39c12; font-weight: bold; }}
        .description {{ font-size: 0.9em; color: #bbb; line-height: 1.4; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }}
        .test-name {{ font-family: 'Consolas', monospace; font-size: 0.85em; color: #33A1FD; white-space: pre-wrap; word-break: break-all; }}

        /* Log Entry Styles */
        .log-entry {{ background: #1a1a1a; border: 1px solid #444; border-radius: 5px; margin-bottom: 20px; overflow: hidden; }}
        .log-header {{ background: #333; padding: 10px 15px; border-bottom: 1px solid #444; display: flex; justify-content: space-between; align-items: center; }}
        .log-filename {{ color: #33A1FD; font-weight: bold; font-family: monospace; }}
        .log-time {{ color: #666; font-size: 0.85em; }}
        .log-content {{ padding: 15px; margin: 0; font-family: 'Consolas', monospace; font-size: 0.9em; white-space: pre-wrap; color: #ccc; max-height: 400px; overflow-y: auto; }}
        .error-log {{ border-left: 5px solid #e74c3c; }}
    </style>
    <script>
        function openTab(evt, tabName) {{
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {{
                tabcontent[i].style.display = "none";
                tabcontent[i].classList.remove("active");
            }}
            tablinks = document.getElementsByClassName("tab-btn");
            for (i = 0; i < tablinks.length; i++) {{
                tablinks[i].classList.remove("active");
            }}
            document.getElementById(tabName).style.display = "block";
            document.getElementById(tabName).classList.add("active");
            evt.currentTarget.classList.add("active");
        }}
    </script>
</head>
<body>
    <div class="header">
        <h1>OPEN-AIR Unified Intelligence Report</h1>
        <p style="color: #666; margin: 5px 0 0 0;">Generated on: <strong>{timestamp}</strong></p>
    </div>

    <div class="container">
        <div class="tab-box">
            <button class="tab-btn active" onclick="openTab(event, 'TestResults')">Test Results</button>
            <button class="tab-btn" onclick="openTab(event, 'AuditReports')">Audit Reports</button>
            <button class="tab-btn" onclick="openTab(event, 'ChangeLogs')">Change Logs</button>
            <button class="tab-btn" onclick="openTab(event, 'BugLogs')">Bug Logs</button>
            <button class="tab-btn" onclick="openTab(event, 'ErrorLogs')">Error Logs</button>
            <button class="tab-btn" onclick="openTab(event, 'RunLogs')">Application Run Logs</button>
            <button class="tab-btn" onclick="openTab(event, 'FlameGraph')">Flame Graph</button>
        </div>

        <!-- TAB 1: Test Results -->
        <div id="TestResults" class="tab-content active">
            <div class="summary-box">
                <div class="stat total">Total: {total}</div>
                <div class="stat passed">Passed: {passed}</div>
                <div class="stat failed">Failed: {failed}</div>
                <div class="stat errors">Errors: {errors}</div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Test Case</th>
                        <th>Goal & Achievement</th>
                        <th>Failure Cause</th>
                        <th>Status</th>
                        <th>Duration</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>

        <!-- TAB 2: Audit Reports -->
        <div id="AuditReports" class="tab-content">
            {audit_html}
        </div>

        <!-- TAB 3: Change Logs -->
        <div id="ChangeLogs" class="tab-content">
            {changelog_html}
        </div>

        <!-- TAB 3.5: Bug Logs -->
        <div id="BugLogs" class="tab-content">
            {buglog_html}
        </div>

        <!-- TAB 4: Error Logs -->
        <div id="ErrorLogs" class="tab-content">
            {error_html}
        </div>

        <!-- TAB 5: Application Run Logs -->
        <div id="RunLogs" class="tab-content">
            {runlog_html}
        </div>

        <!-- TAB 6: Flame Graph -->
        <div id="FlameGraph" class="tab-content">
            {flamegraph_html}
        </div>
    </div>
</body>
</html>
"""
        table_rows = []
        def status_weight(status):
            return {"error": 0, "failed": 1, "warning": 2}.get(status, 3)
            
        sorted_results = sorted(details, key=lambda x: (status_weight(x['status']), x['name']))

        for r in sorted_results:
            row = f"""
                <tr>
                    <td class="test-name">{html.escape(r['name'])}</td>
                    <td class="description">{html.escape(r['description'])}</td>
                    <td class="description">{html.escape(r.get('cause', ''))}</td>
                    <td class="status-{r['status']}">{r['status'].capitalize()}</td>
                    <td>{r['duration']}</td>
                </tr>
            """
            table_rows.append(row)

        html_content = html_template.format(
            timestamp=timestamp,
            total=summary["total"],
            passed=summary["passed"],
            failed=summary["failed"],
            errors=summary["errors"],
            table_rows="".join(table_rows),
            audit_html=extra_tabs.get("audit", ""),
            changelog_html=extra_tabs.get("changelog", ""),
            buglog_html=extra_tabs.get("buglog", ""),
            error_html=extra_tabs.get("error", ""),
            runlog_html=extra_tabs.get("runlog", ""),
            flamegraph_html=extra_tabs.get("flamegraph", "No FlameGraph data available.")
        )
        
        with open(html_path, "w") as f:
            f.write(html_content)
