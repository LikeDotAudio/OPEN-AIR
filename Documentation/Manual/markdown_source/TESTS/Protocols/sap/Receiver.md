# SAP (Session Announcement Protocol) - Receiver Specification

## Overview
This document outlines the requirements for a standalone, open-source Receiver (Mock Device) for testing purposes.

## Requirements
A successful SAP Receiver must listen on the multicast address, parse the SAP header, extract the SDP payload, and track session additions/deletions based on timeout or explicit deletion packets.
