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
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/4.3.0/marked.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background: #1e1e1e; color: #dcdcdc; }}
        .header {{ background: #2b2b2b; padding: 20px 40px; border-bottom: 2px solid #33A1FD; }}
        h1 {{ color: #ffffff; margin: 0; font-size: 1.8em; }}
        .container {{ padding: 30px 40px; }}
        
        /* Markdown Styling */
        .markdown-content {{ line-height: 1.6; }}
        .markdown-content h1, .markdown-content h2, .markdown-content h3 {{ color: #33A1FD; border-bottom: 1px solid #444; padding-bottom: 5px; margin-top: 20px; }}
        .markdown-content code {{ background: #333; padding: 2px 5px; border-radius: 3px; font-family: 'Consolas', monospace; color: #e74c3c; }}
        .markdown-content pre {{ background: #000; padding: 15px; border-radius: 5px; overflow-x: auto; border: 1px solid #444; }}
        .markdown-content pre code {{ background: transparent; color: #2ecc71; padding: 0; }}
        .markdown-content ul, .markdown-content ol {{ padding-left: 25px; }}
        .markdown-content blockquote {{ border-left: 4px solid #33A1FD; margin: 0; padding-left: 15px; color: #888; font-style: italic; }}
        .markdown-content table {{ width: auto; margin: 20px 0; }}
        .markdown-content th, .markdown-content td {{ border: 1px solid #444; padding: 8px 12px; }}

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

        /* Log Browser Styling */
        .log-entry {{ background: #252525; border: 1px solid #333; border-radius: 8px; margin-bottom: 25px; overflow: hidden; }}
        .log-header {{ background: #333; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #444; }}
        .log-filename {{ font-weight: bold; color: #33A1FD; font-family: 'Consolas', monospace; }}
        .log-time {{ color: #888; font-size: 0.85em; }}
        
        .log-controls {{ 
            background: #2b2b2b; 
            padding: 10px 15px; 
            display: flex; 
            gap: 15px; 
            align-items: center; 
            border-bottom: 1px solid #444;
            flex-wrap: wrap;
        }}
        .log-search {{ 
            background: #111; 
            border: 1px solid #444; 
            color: #eee; 
            padding: 5px 10px; 
            border-radius: 4px; 
            flex-grow: 1;
            min-width: 200px;
        }}
        .log-filter-select {{
            background: #111;
            border: 1px solid #444;
            color: #eee;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        
        .log-content-scrollable {{ 
            padding: 0; 
            background: #000; 
            color: #bbb; 
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace; 
            font-size: 0.85em; 
            max-height: 700px; 
            overflow-y: auto; 
            line-height: 1.2;
        }}
        
        .log-table-header {{
            display: grid;
            grid-template-columns: 100px 80px 70px 100px 250px 1fr;
            background: #222;
            color: #888;
            font-weight: bold;
            font-size: 0.8em;
            text-transform: uppercase;
            padding: 8px 15px;
            border-bottom: 2px solid #333;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        .log-line {{ 
            display: grid;
            grid-template-columns: 100px 80px 70px 100px 250px 1fr;
            padding: 4px 15px;
            border-bottom: 1px solid #111;
            align-items: center;
        }}
        .log-line:hover {{ background: #111; }}
        
        .log-col {{ 
            padding: 0 5px; 
            overflow: hidden; 
            text-overflow: ellipsis; 
            white-space: nowrap;
        }}
        .log-col-message {{ white-space: pre-wrap; overflow: visible; text-overflow: clip; }}
        
        .log-timestamp {{ color: #555; font-size: 0.9em; }}
        .log-type {{ font-weight: bold; border-radius: 3px; text-align: center; padding: 1px 4px; }}
        .log-system {{ font-weight: bold; text-align: center; border-radius: 3px; border: 1px solid transparent; }}
        .log-element {{ color: #f39c12; font-weight: bold; }}
        .log-module {{ color: #666; font-size: 0.85em; }}
        .log-message {{ color: #ddd; }}
        
        /* Level Colors */
        .log-level-debug {{ color: #7f8c8d; }}
        .log-level-info {{ color: #3498db; }}
        .log-level-success {{ color: #2ecc71; }}
        .log-level-warning {{ color: #f1c40f; background: rgba(241, 196, 15, 0.1); }}
        .log-level-error {{ color: #e74c3c; background: rgba(231, 76, 60, 0.1); }}
        .log-level-critical {{ color: #ffffff; background: #e74c3c; }}
        .log-level-trace {{ color: #9b59b6; }}

        /* System Colors */
        .log-system-core {{ color: #e67e22; border: 1px solid rgba(230, 126, 34, 0.3); }}
        .log-system-ui {{ color: #33A1FD; border: 1px solid rgba(51, 161, 253, 0.3); }}
        .log-system-sup {{ color: #1abc9c; border: 1px solid rgba(26, 188, 156, 0.3); }}

        /* Subsystem Colors */
        .log-subsys-system {{ color: #f39c12; }}
        .log-subsys-router {{ color: #3498db; }}
        .log-subsys-data {{ color: #2ecc71; }}
        .log-subsys-comm {{ color: #e74c3c; }}
        .log-subsys-builder {{ color: #9b59b6; }}
        
        .log-message {{ color: #ddd; }}
        .error-log {{ border-left: 5px solid #e74c3c; }}
    </style>
    <script>
        function renderMarkdown() {{
            if (typeof marked === 'undefined') return;
            document.querySelectorAll('.markdown-content').forEach(el => {{
                if (el.getAttribute('data-rendered')) return;
                const raw = el.textContent;
                el.innerHTML = marked.parse(raw);
                el.setAttribute('data-rendered', 'true');
            }});
        }}

        function filterLogs(containerId) {{
            const container = document.getElementById(containerId);
            const searchTerm = container.querySelector('.log-search').value.toLowerCase();
            const levelFilter = container.querySelector('.filter-level').value.toLowerCase();
            const systemFilter = container.querySelector('.filter-system').value.toLowerCase();
            const elementFilter = container.querySelector('.filter-element') ? container.querySelector('.filter-element').value.toLowerCase() : "";
            const moduleFilter = container.querySelector('.filter-module') ? container.querySelector('.filter-module').value.toLowerCase() : "";
            
            const logEntries = container.querySelectorAll('.log-entry');
            logEntries.forEach(entry => {{
                const lines = entry.querySelectorAll('.log-line, .log-line-raw');
                lines.forEach(line => {{
                    let show = true;
                    const text = line.textContent.toLowerCase();
                    
                    if (searchTerm && !text.includes(searchTerm)) show = false;
                    
                    if (show && levelFilter) {{
                        const levelCol = line.querySelector('.log-type');
                        if (levelCol && !levelCol.textContent.toLowerCase().includes(levelFilter)) show = false;
                        else if (!levelCol) show = false;
                    }}
                    
                    if (show && systemFilter) {{
                        const systemCol = line.querySelector('.log-system');
                        if (systemCol && !systemCol.textContent.toLowerCase().includes(systemFilter)) show = false;
                        else if (!systemCol) show = false;
                    }}

                    if (show && elementFilter) {{
                        const elementCol = line.querySelector('.log-element');
                        if (elementCol && !elementCol.textContent.toLowerCase().includes(elementFilter)) show = false;
                        else if (!elementCol) show = false;
                    }}

                    if (show && moduleFilter) {{
                        const moduleCol = line.querySelector('.log-module');
                        if (moduleCol && !moduleCol.textContent.toLowerCase().includes(moduleFilter)) show = false;
                        else if (!moduleCol) show = false;
                    }}
                    
                    line.style.display = show ? 'grid' : 'none'; // Use 'grid' for aligned lines
                }});
            }});
        }}

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
            
            // Re-render markdown if switching to a tab that might have hidden content
            renderMarkdown();
        }}

        window.onload = function() {{
            renderMarkdown();
        }};
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
                    <td class="description markdown-content">{html.escape(r.get('description', 'No description provided.'))}</td>
                    <td class="description markdown-content">{html.escape(r.get('cause', ''))}</td>
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
