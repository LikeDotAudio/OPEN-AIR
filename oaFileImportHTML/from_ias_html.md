# 🏷️ Worker Importer From Ias Html

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
formats/worker_importer_from_ias_html.py

This module contains the logic for converting IAS HTML frequency coordination
reports
into a standardized CSV format.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)

Professional services for customizing and tailoring this software to your
specific
application can be negotiated. There is no charge to use, modify, or fork this
software.

Build Log: https://like.audio/category/software/spectrum-scanner/
Source Code: https://github.com/APKaudio/
Feature Requests can be emailed to i @ like . audio

Version 20250821.200641.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Global Functions
#### `Marker_convert_IAShtml_report_to_csv(html_content)`
Converts the HTML frequency coordination report into a list of dictionaries
suitable for CSV output, handling multiple zones. This version is based on
the IAS HTML to CSV.py prototype for accurate extraction.
All frequencies are converted to MHz for consistency.

Inputs:
    html_content (str): The full HTML content of the report.

Returns:
    tuple: A tuple containing:
           - list: A list of strings representing the CSV headers.
           - list: A list of dictionaries, where each dictionary represents a
row
                   in the CSV and keys are column headers.

**Parameters:**
- `html_content`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
