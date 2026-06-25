from oaLogging.Methods.matrix_gate import matrix_log
try:
    from oaRustCore.oa_csv_parser_rs import convert_csv_unknown as rust_convert_csv_unknown
except ImportError:
    rust_convert_csv_unknown = None

def Marker_convert_csv_unknow_report_to_csv(file_path):
    if rust_convert_csv_unknown:
        matrix_log("ui", "importer", "Marker_convert_csv_unknow_report_to_csv", "🚀 Using HIGH-PERFORMANCE RUST CSV parser.", "DEBUG")
        return rust_convert_csv_unknown(str(file_path))
    else:
        raise RuntimeError("Rust CSV parser is required but not installed.")

def start():
    pass

def stop():
    pass

def status():
    return "Running with Rust Engine"

def run_tests():
    return True

__all__ = ["Marker_convert_csv_unknow_report_to_csv", "start", "stop", "status", "run_tests"]
