# NMOS (Networked Media Open Specifications - IS-04/IS-05) - Receiver Specification

## Overview
This document outlines the requirements for a standalone, open-source Receiver (Controller/Registry) for testing purposes.

## Implementation: `nmos-cpp-registry` (Test Registry)
For the OPEN-AIR test suite, we are actively utilizing the integrated `nmos-cpp-master` library to run a Test Registry. The registry code (located under `nmos-cpp-master/Development/nmos-cpp-registry/`) provides the required IS-04 Registration API and Query API.

## Requirements
A successful NMOS Receiver (Controller/Registry) must discover nodes, index resources (devices, senders, receivers, flows), and issue PATCH requests for connection management (IS-05). Our test registry acts as the central hub where the mock device registers, allowing the OPEN-AIR core to predictably query and interact with an active, isolated NMOS inventory.
