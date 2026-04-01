# oaReports/Methods/report_gen.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2350.2
#
# Description: Pure Rust PDF report generator (No Python fallback).

import orjson
from .oaReportGen_rs.compiler_hook import ensure_compiled
ensure_compiled()
from .oaReportGen_rs import oareportgen_rs

class ReportGen:
    """
    High-performance PDF report generator using Rust.
    MANDATORY Rust implementation.
    """
    @staticmethod
    def build_pdf(schema_dict: dict, output_path: str):
        print("📄🛠️🔗 [REPORT] Using PURE RUST generator.")
        schema_json = orjson.dumps(schema_dict).decode()
        return oareportgen_rs.build_pdf(schema_json, output_path)
