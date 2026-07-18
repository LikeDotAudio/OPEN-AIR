# mDNS (Multicast DNS) - Transmitter Specification

## Overview
This document outlines the requirements for a standalone, open-source Transmitter (Generator) for testing purposes.

## Requirements
A successful mDNS Transmitter (Responder) must listen on 224.0.0.251:5353, process incoming queries, and multicast responses containing A/AAAA/PTR/SRV/TXT records.
