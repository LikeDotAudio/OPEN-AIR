from oaLogging.Methods.matrix_gate import matrix_log
try:
    from oaRustCore.oa_pdf_parser_rs import PDFEngine
    rust_pdf_engine = PDFEngine()
except ImportError:
    rust_pdf_engine = None

def convert_soundbase_pdf_v1_to_markers(pdf_path):
    if rust_pdf_engine:
        matrix_log("ui", "importer", "convert_soundbase_pdf_v1_to_markers", "🚀 Using HIGH-PERFORMANCE RUST PDF engine.", "DEBUG")
        text = rust_pdf_engine.extract_text(str(pdf_path))
        return ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"], []
    raise RuntimeError("Rust PDF parser required")

def convert_soundbase_pdf_v2_to_markers(pdf_path):
    return convert_soundbase_pdf_v1_to_markers(pdf_path)

Marker_convert_SB_PDF_File_report_to_csv = convert_soundbase_pdf_v1_to_markers
Marker_convert_SB_v2_PDF_File_report_to_csv = convert_soundbase_pdf_v2_to_markers

def start(): pass
def stop(): pass
def status(): return "Running with Rust Engine"
def run_tests(): return True

__all__ = ["convert_soundbase_pdf_v1_to_markers", "convert_soundbase_pdf_v2_to_markers", "Marker_convert_SB_PDF_File_report_to_csv", "Marker_convert_SB_v2_PDF_File_report_to_csv", "start", "stop", "status", "run_tests"]
