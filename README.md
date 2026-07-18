# 🏷️ OPEN-AIR

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

## 💡 Why OPEN-AIR?
**Traditional instrument software is rigid, vendor-locked, and visually dated.** 

OPEN-AIR was created to bridge the gap between raw hardware capabilities and 
high-fidelity, user-centric visualization. It transforms your laboratory into 
a professional, photorealistic cockpit, allowing you to orchestrate a fleet of 
instruments with the same ease as a single device.

### The Four Pillars:
1.  **Freedom from Vendor Lock-in:** Use one interface to control multiple 
    brands of hardware through the YAK command abstraction.
2.  **Partitioned Architecture (Core/UI):** High-performance separation of 
    real-time hardware logic from the visual rendering engine.
3.  **Encapsulated Module Standard:** The `oaGui` module follows a strict 
    12-subfolder structure, organized into 7 Functional Pillars (Loader, 
    Parser, Tab Maker, Json Parser, Persistence, Rendering, and Telemetry).
4.  **Your Folders are Your Interface:** No complex UI designers. 
    Reorganizing your `oaGui/Assets/` folders instantly redraws your 
    dashboard via the new Widget Registry.

---

## 🧭 Navigation
Currently under revision. Please refer to the root folders for components.

---

## 🚀 Quick Start
```bash
# Clone and setup
git clone https://github.com/APKaudio/OPEN-AIR
cd OPEN-AIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Launch the full system (Supervisor Mode)
python3 openair.py
```

*Developed by Anthony Peter Kuzub (LikeDotAudio)*


## MIT License

Copyright (c) 2026 Anthony Peter Kuzub

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
