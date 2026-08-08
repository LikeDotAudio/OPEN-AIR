# Deep Dive: AMWA NMOS Testing Tool Integration

## Overview
The [AMWA NMOS Testing Tool (`nmos-testing`)](https://github.com/AMWA-TV/nmos-testing) is the official, industry-standard Python-based test suite used for the JT-NM (Joint Task Force on Networked Media) Tested program. It is designed to automatically validate the compliance of NMOS Nodes, Registries, and Controllers against the core IS-04 (Discovery and Registration) and IS-05 (Connection Management) specifications.

As OPEN-AIR operates primarily as an **Orchestrator and Controller**, the AMWA NMOS Testing Tool offers a robust, automated pathway to certify OPEN-AIR's compliance, eventually replacing or complementing the manual test fixtures built around `nmos-cpp`.

## Architectural Shift for OPEN-AIR

Currently, our testing schema uses the `nmos-cpp` mock node and registry as static fixtures. The AMWA Testing Tool fundamentally changes this by acting as a highly dynamic, observable mock environment that actively grades OPEN-AIR's behavior.

### How it Works (Controller Testing Mode)
When testing a Controller (OPEN-AIR):
1. **Mock Infrastructure**: The AMWA tool spins up a Mock IS-04 Registry and several Mock IS-04/IS-05 Nodes.
2. **Stimulus**: OPEN-AIR is instructed (either manually or via an automated testing API) to discover the mock nodes and execute a route (e.g., connect Mock Node A's sender to Mock Node B's receiver).
3. **Validation**: The AMWA tool monitors its own mock endpoints. It automatically scores OPEN-AIR based on:
   - Did OPEN-AIR correctly query the Mock Registry (IS-04 Query API)?
   - Did OPEN-AIR correctly negotiate WebSocket subscriptions for registry updates?
   - Did OPEN-AIR send correctly formatted, valid JSON PATCH requests to the Mock Node's IS-05 Connection API?
   - Did OPEN-AIR handle 4xx/5xx HTTP error codes correctly?

## Proposed NMOS Test Set Architecture

To build a world-class, automated NMOS test set for OPEN-AIR using the AMWA tools, we should implement the following architecture:

### 1. Dockerized Testing Environment
The `nmos-testing` suite should be deployed alongside OPEN-AIR using Docker Compose. This ensures a pristine, isolated network environment where mDNS broadcasts and HTTP traffic are fully captured.

```yaml
# docker-compose.test.yml
services:
  nmos-testing:
    image: amwatv/nmos-testing:latest
    ports:
      - "5000:5000" # Testing Tool UI / API
    networks:
      - nmos_test_net

  open-air-core:
    build: .
    environment:
      - NMOS_REGISTRY_MODE=static
      - NMOS_REGISTRY_IP=nmos-testing
    networks:
      - nmos_test_net
```

### 2. Fully Automated Controller Testing (Non-Interactive Mode)
The AMWA Testing tool exposes its own REST API, allowing us to trigger test suites programmatically from OPEN-AIR's CI/CD pipeline (e.g., GitHub Actions).

**Test Execution Flow**:
1. **Setup**: CI spins up the `docker-compose` environment.
2. **Trigger**: CI sends a POST request to the `nmos-testing` API to begin the "Testing Controllers" suite.
3. **Action**: A specialized Python test script (e.g., `TESTS/Protocols/nmos/amwa_runner.py`) uses the OPEN-AIR API to simulate a user routing an audio stream.
4. **Result Retrieval**: The test script polls the `nmos-testing` API for the final JSON report.
5. **Assertion**: CI passes if all mandatory AMWA tests return `Pass`, and fails if any return `Fail`.

### 3. Transition Strategy
- **Phase 1 (Current)**: Utilize `nmos-cpp-registry` and `nmos-cpp-node` to ensure OPEN-AIR's foundational HTTP/JSON logic is functional.
- **Phase 2**: Introduce `nmos-testing` locally. Developers run the tool via the web UI (port 5000) and manually trigger OPEN-AIR routing commands to see AMWA's compliance scores.
- **Phase 3**: Implement "Fully Automated Testing of Controllers". Replace the `nmos-cpp` fixtures in CI with headless `nmos-testing` API calls to achieve continuous compliance.

## Key Test Suites to Target
- **IS-04 Query API (Controller)**: Ensures OPEN-AIR can paginate, filter, and parse the Registry correctly.
- **IS-05 Connection API (Controller)**: Ensures OPEN-AIR correctly stages and activates transport parameters (SDP validation).
- **BCP-003-01 (TLS)**: Ensures OPEN-AIR can securely interact with HTTPS-enabled Nodes and Registries, managing certificates appropriately.
- **IS-07 (Event & Tally)**: If OPEN-AIR implements GPIO/Tally routing, this validates MQTT and WebSocket event transport.
