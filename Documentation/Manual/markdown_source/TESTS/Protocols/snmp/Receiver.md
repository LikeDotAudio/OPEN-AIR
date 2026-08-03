# SNMP (Simple Network Management Protocol) - Receiver Specification

## Overview
This document outlines the requirements for a standalone, open-source Receiver (Mock Device) for testing purposes.

## Requirements
A successful SNMP Receiver (Agent) must maintain a MIB (Management Information Base), parse incoming ASN.1 OIDs, and return proper Response-PDUs. It should also send TRAP messages.
