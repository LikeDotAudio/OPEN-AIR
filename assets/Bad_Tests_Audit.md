# Quality Assurance Audit: Bad Tests & Missing Coverage

**Date:** Sunday, March 15, 2026
**Project:** OPEN-AIR
**Scope:** Test Modules and Functional Components in `managers/` and `workers/`
**Overall Test Health:** CRITICAL (Severe Under-coverage)

---

## Executive Summary
The OPEN-AIR project is currently operating with a significant deficit in automated testing. Out of several hundred functional modules, only **5** Python files were identified as tests or diagnostic "testers." Most core architectural components—including the display builder, protocol router, and hardware managers—have zero automated test coverage. The few existing tests are primarily manual diagnostic scripts ("testers") rather than self-validating unit tests.

---

## Top Offenders: Components with NO Tests

### 1. `workers/Splinker/` (The Splinker Manager)
- **Status:** NO TESTS FOUND.
- **Concern:** This is a mission-critical component handling the state-mirroring engine, deadband logic, and scaling. It processes high-frequency data streams. A failure here could lead to system-wide data corruption or instability.
- **Risk:** High.

### 2. `workers/Command_Router/` (MQTT/OSC/MIDI/SNMP Routing)
- **Status:** NO TESTS FOUND (excluding a basic `snmp_tester.py`).
- **Concern:** The protocol router is the "nervous system" of OPEN-AIR. There are no automated validations for topic routing, message ingestion, or protocol translation strategies.
- **Risk:** High.

### 3. `managers/Display/` (GUI Builder & Display Manager)
- **Status:** NO TESTS FOUND.
- **Concern:** The dynamic GUI generation logic (Layout Parser, Async Grid Renderer, Widget Factory) is complex and recursive. There is no automated way to verify that a JSON layout will render correctly or that widget state remains synchronized.
- **Risk:** Medium-High.

### 4. `managers/Visa_Fleet_Manager/` (Hardware Discovery & Management)
- **Status:** NO TESTS FOUND.
- **Concern:** Responsible for identifying physical instruments over USB/IP. Without tests, regressions in IDN parsing or fleet inventory management are likely to go undetected until physical hardware is connected.
- **Risk:** Medium.

### 5. `managers/configini/` (Application Configuration)
- **Status:** NO TESTS FOUND.
- **Concern:** Handles project-wide settings and validation. A bug in the config reader can prevent the entire application from launching or lead to silent failures in subsystem initialization.
- **Risk:** Medium.

---

## Audit of Existing Tests

| Test File | Type | Quality Assessment |
| :--- | :--- | :--- |
| `PTPtester.py` | Diagnostic | **Poor.** Requires root, manual observation of output, and a live network. No assertions. |
| `snmp_tester.py` | Diagnostic | **Poor.** Manual script for checking SNMP responses. No `unittest` integration. |
| `test_dynamic_gui_mousewheel_mixin.py` | Unit Test | **Good.** Uses `unittest`, has assertions, and tests a specific bug fix. This is the only "Clean Test" in the project. |
| `CMDP_tester.py` | Diagnostic | **Poor.** Manual verification script for the circular motion potentiometer. |
| `tester.py` (Composite MDP) | Diagnostic | **Poor.** Similar to CMDP_tester. |

---

## Patterns of "Bad Testing"
1. **The "Tester" Anti-Pattern:** Instead of writing repeatable unit tests, developers have created "testers"—standalone scripts that require manual execution and visual verification of logs or MQTT traffic. These do not satisfy the **Self-Validating** or **Fast** requirements of F.I.R.S.T.
2. **Missing Assertions:** Most existing "testers" print results to the console but do not use `assert` statements to programmatically catch failures.
3. **Environment Dependency:** Tools like `PTPtester.py` require specific network configurations and root privileges, violating the **Repeatable** principle.
4. **Lack of Boundary Testing:** There is no evidence of tests for edge cases (e.g., malformed MQTT payloads, disconnected hardware, empty JSON layouts).

---

## Strategic Recommendations

1. **Implement a Domain-Specific Testing Language (DSTL):**
   - Create a `test_utils` module that provides high-level abstractions for mocking MQTT messages, simulating widget clicks, and validating registry states.
   - *Example:* `self.simulate_mqtt_arrival("topic", payload)` instead of manually setting up a client.

2. **Adopt the "Tester to Test" Migration:**
   - Convert existing diagnostic "testers" into `unittest` or `pytest` suites. Replace `print()` statements with `self.assertEqual()` and `self.assertTrue()`.

3. **Establish a Core Coverage Mandate:**
   - Prioritize writing unit tests for the **Splinker** handlers (Scale, Invert, Deadband) as these are pure-math functions and easy to isolate.
   - Implement "Schema Validation" tests for the `managers/Display/` parser to ensure JSON blueprints meet architectural standards.

4. **Integration of F.I.R.S.T. Principles:**
   - Ensure new tests run in a virtual/mocked environment so they are **Fast** and **Repeatable** without needing physical hardware.

---
*Report generated by the QA Lead for OPEN-AIR.*
