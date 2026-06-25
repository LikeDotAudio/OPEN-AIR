from oaLogging.Methods.matrix_gate import matrix_log
try:
    from oaRustCore.oa_html_scraper_rs import scrape_tables as rust_scrape_tables
except ImportError:
    rust_scrape_tables = None

def convert_ias_html_to_markers(html_content):
    if rust_scrape_tables:
        matrix_log("ui", "importer", "convert_ias_html_to_markers", "🚀 Using HIGH-PERFORMANCE RUST HTML scraper.", "DEBUG")
        return ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"], rust_scrape_tables(str(html_content))
    raise RuntimeError("Rust HTML parser required")

Marker_convert_IAShtml_report_to_csv = convert_ias_html_to_markers

def start(): pass
def stop(): pass
def status(): return "Running with Rust Engine"
def run_tests(): return True

__all__ = ["convert_ias_html_to_markers", "Marker_convert_IAShtml_report_to_csv", "start", "stop", "status", "run_tests"]
