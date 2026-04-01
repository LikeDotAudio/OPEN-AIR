import sys
import os

# Ensure the project root is in sys.path
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaReports.Methods.report_gen import ReportGen

def test_report_gen():
    schema = {
        "title": "Audit Report 2026",
        "sections": [
            {"name": "Hardware", "items": ["Router 1", "Switch 2"]},
            {"name": "Compliance", "status": "Passed"}
        ]
    }
    
    output_path = ".gemini/test_report.pdf"
    if os.path.exists(output_path): os.remove(output_path)
    
    ReportGen.build_pdf(schema, output_path)
    
    if os.path.exists(output_path):
        print(f"✅ SUCCESS: PDF report generated at {output_path} (Size: {os.path.getsize(output_path)} bytes)")
    else:
        print("❌ FAILURE: PDF report not generated.")

if __name__ == "__main__":
    test_report_gen()
