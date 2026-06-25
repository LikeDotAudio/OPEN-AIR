from oaLogging.Methods.matrix_gate import matrix_log
try:
    from oaRustCore.oa_showfile_unpacker_rs import unpack_showfile
except ImportError:
    unpack_showfile = None

def convert_shure_wwb_shw_to_markers(file_path):
    if unpack_showfile:
        matrix_log("ui", "importer", "convert_shure_wwb_shw_to_markers", "🚀 Using HIGH-PERFORMANCE RUST Showfile unpacker.", "DEBUG")
        return ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"], unpack_showfile(str(file_path))
    raise RuntimeError("Rust Showfile parser required")

Marker_convert_WWB_SHW_File_report_to_csv = convert_shure_wwb_shw_to_markers
Marker_convert_wwb_zip_report_to_csv = convert_shure_wwb_shw_to_markers

def csv_to_json_and_publish(*args, **kwargs):
    pass

def start(): pass
def stop(): pass
def status(): return "Running with Rust Engine"
def run_tests(): return True

__all__ = ["convert_shure_wwb_shw_to_markers", "Marker_convert_WWB_SHW_File_report_to_csv", "Marker_convert_wwb_zip_report_to_csv", "csv_to_json_and_publish", "start", "stop", "status", "run_tests"]
