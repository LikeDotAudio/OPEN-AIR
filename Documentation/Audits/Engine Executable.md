# Audit: Engine Executable - Deployment & Distribution Strategy

## Overview

This audit investigates the optimal strategy for distributing a backend "Engine" as three platform-specific executables (Windows, macOS, Linux). These binaries will run on a user's local machine or server and communicate via MQTT to feed data to a shared, web-based frontend application.

This document outlines the best practices for building, distributing, and connecting these binaries, as well as an evaluation of the MQTT broker deployment options.

## 1. MQTT Broker Deployment Strategy

The central piece connecting the local Engine Executables and the shared frontend is the MQTT Broker.

### Is Docker with MQTT the "Best/Simplest" Way?

**Yes and No, depending on your desire to manage infrastructure.**

If you are hosting the MQTT broker yourself on a cloud VPS (Virtual Private Server like DigitalOcean, AWS, Linode), **Docker is unequivocally the best and simplest method.** Using the official `eclipse-mosquitto` Docker image allows you to spin up a secure, reproducible, and easily upgradable broker using a simple `docker-compose.yml` file. 

However, because you have a shared web frontend connecting to multiple disparate clients, you must carefully consider how they connect:

#### Option A: Self-Hosted Docker Container (Mosquitto) - *Recommended for control/cost*
*   **Pros:** Very low operating cost, complete control over data privacy, and no arbitrary message/connection limits. Docker simplifies the deployment significantly.
*   **Cons:** You must manage the Linux server, handle domain names, configure TLS/SSL certificates (via Let's Encrypt / Certbot), and ensure system security.
*   **Crucial Requirement:** The broker MUST be configured to support **MQTT over WebSockets** (usually port 9001 or 443 with path routing). Standard MQTT (TCP port 1883) cannot be accessed directly by a web browser due to browser security sandboxing.

#### Option B: Fully Managed Cloud MQTT (e.g., HiveMQ Cloud, EMQX Cloud) - *Recommended for pure simplicity*
*   **Pros:** Zero server maintenance, instant setup, automatic scaling, high availability out of the box. TLS and WebSockets are pre-configured.
*   **Cons:** Can become expensive at scale. You do not own the underlying infrastructure.
*   **Verdict:** If you want the *absolute simplest* way to get started and validate your architecture without touching Linux server administration, use a managed cloud broker. Most offer generous free tiers perfect for development.

## 2. Engine Executable (Backend) Strategy

The backend engine needs to be compiled for Windows, macOS, and Linux, and seamlessly connect to the centralized broker.

### Technology Choice
To easily produce 3 standalone binaries, you should build the engine using a language that supports cross-compilation and produces **statically linked binaries**:
*   **Go (Golang):** Highly recommended for this specific use case. Producing binaries for all three OS architectures is as simple as changing environment variables (`GOOS` and `GOARCH`). The resulting binary is self-contained and requires no runtime or dependencies to be installed on the user's machine.
*   **Rust:** Excellent for performance and safety, and also great for standalone binaries. Cross-compiling can require slightly more setup than Go but is a very robust option.
*   **Node.js/Python (Packaged):** Tools like `pkg` (Node) or `PyInstaller` (Python) can bundle the runtime with the app. However, these produce bloated binaries, can be slower to start, and frequently trigger false positives in Windows Defender/Antivirus software.

### Connection Architecture
1.  **Authentication:** The Engine needs a secure way to authenticate with the MQTT broker. Do not hardcode credentials in the binary. 
    *   **Strategy:** The Engine generates a unique UUID on its first run and displays it. The user enters this UUID into their authenticated session on the web frontend. The backend then provisions MQTT ACLs (Access Control Lists) for that UUID.
2.  **Topics:** Use a strictly defined topic structure to prevent collisions between users. Example: `app/users/{user_id}/engine/status`.

## 3. Shipping and Distribution Strategy

How do users acquire and run the binaries?

### The "Web Download" Approach (Simplest UX)
*   The shared frontend features a "Download Engine" dashboard.
*   The web app detects the user's Operating System via the browser's User-Agent string and offers the correct binary for download (`.exe` for Windows, `.tar.gz` for Linux/macOS).
*   For advanced users, you can provide a single-line installation script (e.g., a `curl | bash` script for Linux/Mac, or a PowerShell script for Windows).

### CI/CD Automation (Best Practice)
Do not build these binaries manually on your local machine. Use an automated pipeline like **GitHub Actions**.
*   Every time you push a new version tag (e.g., `v1.0.0`), a GitHub Action automatically spins up temporary workers to compile the code for Windows (`amd64`), macOS (`amd64` & `arm64` for Apple Silicon), and Linux (`amd64`, `arm64`).
*   The action automatically creates a Release and attaches the compiled binary files.
*   If using Go, tools like **GoReleaser** can automate this entire cross-compilation and packaging pipeline with a single configuration file.

## 4. Web Frontend Integration

The shared web frontend needs to communicate with the distributed Engines.

*   **Protocol:** As mentioned, the frontend MUST connect to the MQTT broker using **Secure WebSockets (`wss://`)**. Libraries like `MQTT.js` are industry standard for this and handle browser environments seamlessly.
*   **Shared State:** The frontend subscribes to the user's specific Engine topics. When the user runs the Engine on their machine, it connects to the broker via standard secure MQTT (TCP port 8883) and starts publishing data. The frontend immediately receives this data via WebSockets and updates the UI in real-time.

## Summary & Recommended Action Plan

1.  **Broker:** Start with a free-tier Cloud MQTT broker (like HiveMQ Cloud) for immediate prototyping. Once the product matures and you need more control, deploy `eclipse-mosquitto` via Docker on a low-cost VPS. Ensure both standard TCP (for the Engine) and WebSockets (for the Frontend) are configured behind TLS.
2.  **Engine:** Build the backend Engine in Go or Rust. Connect it to the broker using standard secure MQTT over TCP.
3.  **Frontend:** Build your shared interface with a modern framework and use `MQTT.js` to connect via Secure WebSockets (`wss://`).
4.  **Distribution:** Implement GitHub Actions (with GoReleaser if using Go) to automate the building of Win/Mac/Linux binaries. Host these binaries as GitHub Releases or in an S3 bucket, and link to them directly from the shared frontend.
