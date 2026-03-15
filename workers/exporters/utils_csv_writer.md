# 🏷️ Utils Csv Writer

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
exporters/utils_csv_writer.py

This module provides utility functions for writing spectrum scan data to CSV
files.

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
#### `write_scan_data_to_csv(file_path, header, data, app_instance_ref, append_mode)`
Writes scan data to a CSV file. This function is designed to write raw frequency
and amplitude data collected from the spectrum analyzer. It handles creating
the necessary directory structure if it doesn't exist and conditionally writes
the header.

Inputs:
    file_path (str): The full path to the CSV file where the data will be
written.
    header (list or None): A list of strings representing the CSV header row.
                           If None, no header will be written.
    data (list): A list of lists or tuples, where each inner list/tuple
represents
                 a row of data (e.g., [frequency_MHz, level_dBm]).
    app_instance_ref (object): A reference to the main application instance.
    append_mode (bool): If True, data will be appended to the file if it exists.
                        If False, the file will be overwritten.
    console_print_func (function, optional): Function to use for console output.
                                              Defaults to  if None.
Raises:
    IOError: If there is an issue writing to the file.

**Parameters:**
- `file_path`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `header`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `data`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `app_instance_ref`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `append_mode`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
