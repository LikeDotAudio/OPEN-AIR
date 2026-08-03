# SNMP (Simple Network Management Protocol) - Transmitter Specification

## Overview
This document outlines the requirements for a standalone, open-source Transmitter (Generator) for testing purposes.

## Requirements
A successful SNMP Transmitter (Manager) must construct valid SNMPv2c/v3 requests (GET, GETNEXT, SET), encode them in ASN.1 BER, and handle UDP timeouts/retries.
