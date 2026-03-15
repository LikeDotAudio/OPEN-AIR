# 🏷️ Logger

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
workers/logger/logger.py

Standardized Logging Framework using Loguru.
Implements Custom Types (Categories), Partitions, and Consolidated Sinks.
Updated to use PTP (Precision Time Protocol) time for timestamps.

Author: Anthony Peter Kuzub (Refactored by Gemini)
Version 20260222.Consolidated.3

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Global Functions
#### `_get_cached_config()`
Returns the cached config instance to avoid redundant lookups and imports.

**Parameters:**
- None

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

#### `ptp_patcher(record)`
Patches the log record with PTP (TAI) time.
Optimized: Caches the HHMMSS part to avoid redundant string formatting.

**Parameters:**
- `record`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

#### `initialize_logging(config, log_dir, partition)`
Initializes Loguru sinks based on the application configuration.
Consolidates specialized logs into labeled entries in the Master and Firehose
logs.

**Parameters:**
- `config`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `log_dir`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `partition`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

#### `set_log_directory(directory, partition)`
Compatibility wrapper for existing entry points.

**Parameters:**
- `directory`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `partition`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

#### `get_logger(category)`
Returns a logger instance bound to a specific category.

**Parameters:**
- `category`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

#### `debug_logger(message, *args, **kwargs)`
Compatibility wrapper for legacy calls. Deprecated: use logger directly.

**Parameters:**
- `message`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `*args`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `**kwargs`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

#### `console_log(message)`
Simple console logger wrapper.

**Parameters:**
- `message`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
