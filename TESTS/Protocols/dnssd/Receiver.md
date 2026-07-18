# DNS-SD (DNS Service Discovery) - Receiver Specification

## Overview
This document outlines the requirements for a standalone, open-source Receiver (Mock Device) for testing purposes.

## Requirements
A successful DNS-SD Receiver (Browser) must issue mDNS queries for specific service types (e.g., _http._tcp, _oca._tcp), correctly resolve SRV records to IP/Port, and parse TXT records for metadata.
