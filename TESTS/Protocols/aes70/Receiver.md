# AES70 (OCA - Open Control Architecture) - Receiver Specification

## Overview
This document outlines the requirements for a standalone, open-source Receiver (Mock Device) for testing purposes.

## Requirements
A successful AES70 Receiver (Device) must advertise itself via mDNS/DNS-SD, accept OCP.1 connections on the advertised port, and correctly maintain an internal object model. It must respond to GET/SET commands, emit notifications for property changes, and enforce AES70 state synchronization.
