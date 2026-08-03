# SMPTE ST 2138 (Protobuf Interface) - Receiver Specification

## Overview
This document outlines the requirements for a standalone, open-source Receiver (Mock Device) for testing purposes.

## Requirements
A successful SMPTE 2138 Receiver must implement the gRPC server stub for ST 2138, deserialize incoming protobuf messages, and translate them into the internal model.
