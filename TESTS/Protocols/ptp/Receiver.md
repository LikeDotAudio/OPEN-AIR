# PTP (Precision Time Protocol - IEEE 1588) - Receiver Specification

## Overview
This document outlines the requirements for a standalone, open-source Receiver (Mock Device) for testing purposes.

## Requirements
A successful PTP Receiver (Ordinary Clock) must listen for Sync messages, send Delay_Req, process Delay_Resp, and continuously correct its local clock drift/offset.
