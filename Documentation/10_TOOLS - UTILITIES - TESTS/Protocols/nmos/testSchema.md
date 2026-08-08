# NMOS (Networked Media Open Specifications - IS-04/IS-05) - Test Schema

## Framework
This schema defines the integration test boundary between the standalone testing tools (the integrated `nmos-cpp-master` test registry and mock device) and the OPEN-AIR core.

## Automated Test Flow: 
1. **Infrastructure Spin-up**: Start the `nmos-cpp-registry` (Test Registry) on a known port.
2. **Device Spin-up**: Start the `nmos-cpp` mock device (Node) and configure it to point to the test registry.
3. **Node Registration Verification (IS-04)**: OPEN-AIR queries the test registry to confirm the mock device is fully indexed and actively maintaining its heartbeats.
4. **Connection Management (IS-05)**: OPEN-AIR issues a route (PATCH request) to the mock device's receiver endpoints.
5. **SDP Payload Validation**: Validate that the mock device correctly accepted and adopted the simulated SDP parameters provided by OPEN-AIR.
