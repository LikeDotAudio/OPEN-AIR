# AES70 (OCA - Open Control Architecture) - Transmitter Specification

## Overview
This document outlines the requirements for a standalone, open-source Transmitter (Generator) for testing purposes.

## Requirements
A successful AES70 Transmitter (Controller) must discover AES70 devices (via DNS-SD), establish an OCP.1 (TCP/IP) connection, and correctly serialize OCC messages to manipulate the object model (e.g. OcaGain, OcaSwitch). It must handle subscriptions and keep-alives.
