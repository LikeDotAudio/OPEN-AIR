# Audit Report: `Bad_Tests_Audit.md`

**Date of Run:** March 17, 2026
**Overall Test Coverage Health:** **CRITICAL RED**. 
While foundational tests have been established in `assets/Documentation/Testing/`, the legacy test infrastructure is fundamentally broken, and 90%+ of the functional modules in `managers/` and `workers/` remain unverified.

---

## 1. Top Offenders: Missing Test Coverage
The following critical functional areas have **ZERO** automated unit tests:

### **A. Protocol Management & Communication**
- `workers/Command_Router/MIDI/midi.py`: Handles MIDI hardware abstraction and mapping. High risk of regressions during refactoring.
- `workers/Command_Router/SNMP/snmp.py`: Manages MIB generation and OID trees. (Note: `snmp_tester.py` is a manual tool, not a test).
- `workers/Command_Router/AES70/aes70.py`: Zero coverage for OCA/AES70 protocol.
- `workers/Command_Router/State_Cache/state_cache.py`: Critical persistence and recovery logic.

### **B. Core Hardware & System Managers**
- `managers/Visa_Fleet/visa_fleet.py`: Main orchestrator for instrument discovery and inventory.
- `managers/Visa_Fleet/visa_proxy_fleet.py`: Manages the proxy queue for fleet-wide SCPI commands.
- `managers/System_Core/open_air_core.py`: The heart of the hardware partition.

### **C. UI Orchestration & Dynamic Building**
- `managers/Display/open_air_ui.py`: The main GUI entry point.
- `workers/builder/builder.py`: The core engine that interprets JSON/Python and constructs the UI.
- `managers/Display/loader/module_loader.py`: Responsible for dynamic Python GUI discovery.

---

## 2. Analysis of "Bad Tests" (The Wall of Shame)

### **Offender 1: Mocking the Target (Circular Logic)**
- **Files:** 
  - `tests/managers/configini/test_config_reader.py`
  - `tests/workers/Command_Router/mqtt/test_mqtt_publisher_service.py`
- **Issue:** These tests define a `MockClass` *inside the test file* that mimics the production class, and then run assertions against that mock. 
- **Result:** These tests pass 100% of the time regardless of whether the production code is broken. They provide a false sense of security.
- **Violation:** Self-Validating (F.I.R.S.T.) and Violation of "Test the Production Code".

### **Offender 2: The "Tester" Script Fallacy**
- **Files:** 
  - `workers/builder/widgets/utils/circular_motion_displacement_potentiometer/CMDP_tester.py`
  - `workers/Command_Router/SNMP/snmp_tester.py`
- **Issue:** These are interactive GUI applications or manual CLI utilities. They require human intervention to "see" if they work.
- **Result:** They cannot be integrated into a CI/CD pipeline and are not repeatable.
- **Violation:** Fast, Repeatable, Self-Validating (F.I.R.S.T.).

---

## 3. The Remediation Strategy (Action Plan)

### **Phase 1: Standardize and Relocate (Immediate)**
1. Move high-quality tests from `assets/Documentation/Testing/` to the root `tests/` directory.
2. Delete `tests/` files that test their own mocks to prevent confusion.
3. Standardize all automated tests to use `unittest` or `pytest` with the `test_*.py` naming convention.

### **Phase 2: Establish the "Big Three" Coverage (Critical)**
Write real unit tests for:
1. `managers/Visa_Fleet/visa_fleet.py` (Instrument Inventory Logic)
2. `workers/Command_Router/State_Cache/state_cache.py` (Persistence Integrity)
3. `workers/Command_Router/MIDI/midi.py` (Hardware Mapping Logic)

### **Phase 3: Domain-Specific Testing Language (DSTL)**
Create a `tests/conftest.py` or a testing utility module that provides:
- `mock_mqtt_message()`: Standard generator for MqttMessage objects.
- `mock_ui_variable()`: Quick generator for tk.StringVar/IntVar with tracing.
- `assert_mqtt_published(topic, val)`: Custom assertion for router verification.

---

## 4. Suggestions for GOOD Tests

### **Example: Correcting `test_config_reader.py`**
```python
import unittest
from unittest.mock import patch, mock_open
from managers.configini.config_reader import Config

class TestConfigReader(unittest.TestCase):
    def test_singleton_integrity(self):
        """BUILD: Request two instances. CHECK: Assert they are identical."""
        c1 = Config.get_instance()
        c2 = Config.get_instance()
        self.assertIs(c1, c2)

    @patch("builtins.open", new_callable=mock_open, read_data="[MQTT]\nBROKER_ADDRESS=10.0.0.1")
    def test_config_loading_from_file(self, mock_file):
        """BUILD: Mock file content. OPERATE: Load. CHECK: Assert specific value."""
        config = Config.get_instance()
        config.read_config("mock_config.ini")
        self.assertEqual(config.MQTT_BROKER_ADDRESS, "10.0.0.1")
```

### **Example: For `visa_fleet.py`**
```python
def test_fleet_inventory_addition():
    """Verify that adding a new device updates the inventory correctly."""
    fleet = VisaFleetManager()
    device_data = {"IDN": "TEK,DPO1234", "RESOURCE": "USB0::1::2"}
    
    fleet.add_device("scope_1", device_data)
    
    assert fleet.get_device("scope_1")["model"] == "DPO1234"
    assert "scope_1" in fleet.active_inventory
```

---
**QA Lead Recommendation:** The project must move away from "manual testers" and "mock-only tests" immediately. Every new PR must include a `test_*.py` file that tests real logic in the production module.
