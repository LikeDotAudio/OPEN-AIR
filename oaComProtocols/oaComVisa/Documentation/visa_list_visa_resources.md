# 🏷️ Manager Visa List Visa Resources

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
`managers/VisaScipi/manager_visa_list_visa_resources.py`

This file provides a utility function for listing available VISA (Virtual Instrument Software Architecture) resources. It interfaces with the local VISA backend to discover connected hardware over USB, Ethernet (TCPIP), and Serial (ASRL) interfaces.

**Primary Responsibilities:**
- Query the VISA ResourceManager for all active instrument addresses.
- Categorize and prioritize discovered resources by interface type.
- Provide a sorted list for consistent GUI presentation.

Author: Anthony Peter Kuzub

## ⚙️ Assumptions & Constraints
- Requires a valid VISA backend installed on the host system (e.g., NI-VISA, Keysight, or PyVISA-py).
- TCPIP discovery may depend on the specific backend's ability to scan VXI-11 or HiSLIP devices.

## 📚 API Reference

### Global Functions
#### `list_visa_resources()`
Lists available VISA resources (instruments) discovered by the backend.

**Parameters:**
- None

**Returns:**
- A list of strings representing the VISA resource addresses.
- An empty list if no resources are found or if the backend fails.

**Side Effects & Thread-Safety:**
- Initializes a new `pyvisa.ResourceManager` instance.
- Performs blocking I/O to scan system hardware buses and network segments.

## 📝 Focus on Intent (Inline Comments)
- Search for all instrument types capturing USB, TCPIP, GPIB, and ASRL.
- Categorize discovered resources to provide a predictable order in the GUI.
- Prioritize the list (USB -> TCPIP -> Other) as USB is typically the most stable interface for local use.
