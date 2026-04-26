# FileWriters/ReportBuilder_Dependencies.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Generates HTML content for the Dependencies tab in the Unified Report.

import importlib

# EXTERNAL_PACKAGES: Maps human-friendly names to actual Python import paths.
# Re-using the list from DependencyManager for consistency.
EXTERNAL_PACKAGES = {
    "numpy": "numpy",
    "pandas": "pandas",
    "matplotlib": "matplotlib",
    "Pillow": "PIL",
    "pdfplumber": "pdfplumber",
    "beautifulsoup4 (bs4)": "bs4",
    "pyvisa": "pyvisa",
    "pyusb": "usb.core",
    "python-usbtmc": "usbtmc",
    "python-vxi11": "vxi11",
    "pyserial": "serial",
    "psutil": "psutil",
    "zeroconf": "zeroconf",
    "scapy": "scapy",
    "paho-mqtt": "paho.mqtt.client",
    "aiomqtt": "aiomqtt",
    "orjson": "orjson",
    "flameprof": "flameprof",
    "loguru": "loguru",
    "python-osc": "pythonosc",
    "mido": "mido",
    "python-rtmidi": "rtmidi",
    "textual": "textual",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
}

def build_tab():
    """
    Scans the current environment for dependencies and builds an HTML table.
    """
    html = """
    <div class="markdown-content">
        <h2>System Dependency Status</h2>
        <p>Verification of essential Python libraries required for the OPEN-AIR platform.</p>
        
        <table>
            <thead>
                <tr>
                    <th>Package (Friendly Name)</th>
                    <th>Import Path</th>
                    <th>Status</th>
                    <th>Version</th>
                </tr>
            </thead>
            <tbody>
    """

    for friendly, import_path in EXTERNAL_PACKAGES.items():
        try:
            module = importlib.import_module(import_path)
            version = getattr(module, "__version__", "Unknown")
            status_class = "status-passed"
            status_text = "PASSED"
        except ImportError:
            version = "N/A"
            status_class = "status-failed"
            status_text = "MISSING"

        html += f"""
                <tr>
                    <td>{friendly}</td>
                    <td><code>{import_path}</code></td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{version}</td>
                </tr>
        """

    html += """
            </tbody>
        </table>
    </div>
    """
    return html
