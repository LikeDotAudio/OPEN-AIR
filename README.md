# 🏷️ OPEN-AIR

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](![Status](https://img.shields.io/badge/status-active-success)

## 💡 Why OPEN-AIR?
**Traditional instrument software is rigid, vendor-locked, and visually dated.** 

OPEN-AIR was created to bridge the gap between raw hardware capabilities and high-fidelity, user-centric visualization. It transforms your laboratory into a professional, photorealistic cockpit, allowing you to orchestrate a fleet of instruments with the same ease as a single device.

### The Three Pillars:
1.  **Freedom from Vendor Lock-in:** Use one interface to control multiple brands of hardware through the YAK command abstraction.
2.  **Your Folders are Your Interface:** No complex UI designers. Reorganizing your `oaGuiDefinitions/` folders instantly redraws your dashboard.
3.  **Photorealistic "Next Gen" Visuals:** High-fidelity vintage meters and industrial aesthetics provide a tactile, professional monitoring experience.
4.  **Hierarchical Forensic Observability:** A refined, matrix-based logging system that allows for surgical debugging and dynamic runtime control.

---

## 🧭 Navigation
For detailed information, please refer to the modular documentation:

- **[User Manual](oaDocumentation/Manual/01_Introduction.md)**: Start here to learn how to use the software.
- **[Logging Matrix](oaConfigurationManager/Documentation/logging_matrix.md)**: Learn how the hierarchical debug system works.
- **[Installation Guide](oaDocumentation/Landmarks/Installation_Guide.md)**: Setup, dependencies, and environment configuration.
- **[Documentation Map](oaDocumentation/Project_Map/Documentation_Map.md)**: Deep dive into the project structure and modules.
- **[SMPTE2138 Bridge](oaComSMPTE2138/Documentation/Summary.md)**: Details on the SMPTE ST 2138 (SMPTE2138) Protobuf interface.
- **[Communication Broker](oaComBroker/Documentation/README.md)**: Details on the Protocol Router and Unified Message Schema.
- **[Patent Details](oaDocumentation/Patent/01_abstract.md)**: Technical descriptions of the novel architecture.

---

## 🚀 Quick Start
```bash
# Clone and setup
git clone https://github.com/LikeDotAudio/OPEN-AIR
cd OPEN-AIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Launch the full system
python3 OpenAir.py
```

*Developed by LikeDotAudio*


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
