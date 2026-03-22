# 🏷️ Worker Importer From Soundbase Pdf V1

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
formats/worker_importer_from_soundbase_pdf_v1.py

This module contains the logic for converting Sound Base PDF files (version 1)
into a standardized CSV format.

Author: Anthony Peter Kuzub

specific
application can be negotiated. There is no charge to use, modify, or fork this
software.


Version 20250821.200641.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Global Functions
#### `Marker_convert_SB_PDF_File_report_to_csv(pdf_file_path)`
Parses a PDF file (Sound Base format) and extracts frequency data, converting it
into a standardized CSV format. This function maps PDF fields to the MARKERS.CSV
structure as follows:
- PDF 'Group' -> CSV 'ZONE'
- PDF 'Model' -> CSV 'GROUP'
- PDF 'Name' -> CSV 'NAME'
- PDF 'Frequency' -> CSV 'FREQ' (in MHz)
- CSV 'DEVICE' is constructed from PDF 'Model', 'Band', and 'Preset'.

Inputs:
    pdf_file_path (str): The full path to the PDF file.
    console_print_func (function, optional): A function to use for printing
messages
                                             to the console. If None, uses
standard print.
Outputs:
    tuple: A tuple containing:
           - headers (list): A list of strings representing the CSV header row.
           - csv_data (list): A list of dictionaries, where each dictionary
                              represents a row of data with keys matching the
headers.
Raises:
    FileNotFoundError: If the specified PDF file does not exist.
    Exception: For other parsing or data extraction errors.

**Parameters:**
- `pdf_file_path`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
