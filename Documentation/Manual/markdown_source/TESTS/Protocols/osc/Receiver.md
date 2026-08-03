# OSC (Open Sound Control) - Receiver Specification

## Overview
This document outlines the requirements for a standalone, open-source Receiver (Mock Device) for testing purposes.

## Requirements
A successful OSC Receiver must bind to a UDP port, parse packets (including Bundles and Timestamps), map addresses via a routing tree, and dispatch actions.
