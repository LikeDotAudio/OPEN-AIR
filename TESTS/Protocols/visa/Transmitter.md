# VISA (Virtual Instrument Software Architecture) - Transmitter Specification

## Overview
This document outlines the requirements for a standalone, open-source Transmitter (Generator) for testing purposes.

## Requirements
A successful VISA Transmitter (Controller) must discover instruments over TCP/IP (VXI-11 / HiSLIP / LXI) and format SCPI commands (e.g., *IDN?) over the network stream.
