# MQTT (Message Queuing Telemetry Transport) - Transmitter Specification

## Overview
This document outlines the requirements for a standalone, open-source Transmitter (Generator) for testing purposes.

## Requirements
A successful MQTT Transmitter (Publisher) must establish a TCP/TLS connection to a broker, handle QoS (0,1,2), format topic strings correctly, and serialize JSON/binary payloads.
