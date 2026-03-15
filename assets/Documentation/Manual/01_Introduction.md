# OPEN-AIR User Manual

## 01. Introduction

Welcome to **OPEN-AIR (Open-Air Instrumented Radio)**.

OPEN-AIR is a modular, high-performance software platform designed for radio frequency (RF) monitoring, signal analysis, and laboratory instrument orchestration. It bridges the gap between raw hardware capabilities and high-fidelity, user-centric visualization.

### Key Philosophy
Unlike traditional vendor-locked software, OPEN-AIR is built on three core pillars:
1.  **Partitioned Architecture:** Separation of safety-critical hardware communication (Core) from the high-performance visualization engine (UI).
2.  **Filesystem-Driven UI:** Your folder structure *is* your interface. Reorganizing files and folders instantly updates the dashboard layout.
3.  **Photorealistic Rendering:** "Next Gen" instrumentation provides an industrial, tactile feel through vintage meter bezels, lighting effects, and transparency.

### The System at a Glance
- **Supervisor (`OpenAir.py`):** The master controller that launches and monitors the system.
- **Partition A (Core):** The silent workhorse handling VISA, USB, and MQTT bridging.
- **Partition B (UI):** The visual engine that renders the "Next Gen" dashboards.
- **YAK Protocol:** A command abstraction layer that allows one UI to control many different types of hardware.

Whether you are a researcher, a hobbyist, or a lab manager, OPEN-AIR provides the tools to build professional, custom cockpits for your RF instrumentation.
