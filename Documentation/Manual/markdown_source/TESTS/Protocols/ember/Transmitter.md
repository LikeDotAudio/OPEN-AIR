# Ember+ (Lawo/L-S-B) - Transmitter Specification

## Overview
This document outlines the requirements for a standalone, open-source Transmitter (Generator) for testing purposes.

## Requirements
A successful Ember+ Transmitter (Consumer) must initiate a TCP connection, parse the BER-encoded ASN.1 tree (Glow), send getDirectory requests to discover the tree, and send parameter set requests.
