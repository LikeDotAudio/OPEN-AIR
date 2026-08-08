# NMOS (Networked Media Open Specifications - IS-04/IS-05) - Transmitter Specification

## Overview
This document outlines the requirements for a standalone, open-source Transmitter (Generator/Mock Device) for testing purposes.

## Implementation: `nmos-cpp` Mock Device
For the OPEN-AIR test suite, we are actively utilizing the integrated `nmos-cpp-master` library to spin up a mock NMOS device (Node). This mock device serves as our baseline test fixture for incoming IS-04 and IS-05 interaction.

## Requirements
A successful NMOS Transmitter (Node) must expose an HTTP API (IS-04), advertise to a Registry via mDNS/HTTP, and expose connection management endpoints (IS-05) for senders/receivers. The mock device must successfully register its simulated video/audio/ancillary senders and receivers with our designated test registry so that OPEN-AIR can manipulate them.
