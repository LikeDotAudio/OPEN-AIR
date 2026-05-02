# oaGui/Documentation/folder_fast_io_utility.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for the high-performance Rust FS scanner.

## 🚀 Overview
The `FastScanner` provides high-performance directory scanning using a native Rust core (`oa_fast_scanner_rs`). It is optimized for rapidly mapping large `oaGuiElements` trees.

## 🏗️ Partitioned Architecture
- **Layer**: FileReaders (UI Partition)
- **Role**: Native I/O Utility 🦀⚡

## 🔧 Core Functions
### `scan_directory()`
- **Purpose**: Scans a directory for files matching a specific extension. 📂
- **Mechanism**:
    1. Attempts to use the **Rust Fast Scanner** for maximum performance. 🏎️
    2. Falls back to a recursive Python `rglob` if the native module is unavailable. 🐢
- **Outputs**: Returns a list of absolute file paths.
