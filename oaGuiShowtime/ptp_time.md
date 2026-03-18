# 🏷️ Ptp Time

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
workers/Showtime/ptp_time.py

Provides Precision Time Protocol (PTP) synchronized time using CLOCK_TAI.
Optimized: Performs clock discovery at load time to ensure zero-overhead
retrieval.

Author: Anthony Peter Kuzub
Version 20260222.Optimized.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Global Functions
#### `get_ptp_time()`
Retrieves the current PTP (TAI) time if available.
Zero-overhead: uses the pre-discovered best available clock function.

**Parameters:**
- None

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

#### `is_using_ptp()`
Returns True if the system is currently using CLOCK_TAI.

**Parameters:**
- None

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

#### `get_ptp_timestamp_str(format_str)`
Returns a formatted string of the current PTP time.
Useful for logging and UI displays.

**Parameters:**
- `format_str`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
