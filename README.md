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
For detailed information, please refer to the modular documentation:

- **[GUI Module](oaGui/Documentation/Summary.md)**: Deep dive into the Dynamic GUI Builder, Widget Registry, and Folder-Driven Layouts.
- **[User Manual](oaDocumentation/Manual/01_Introduction.md)**: Start here to learn how to use the software.
- **[Translator Module](oaTranslator/Documentation/Summary.md)**: Details on the YAK Command Translation and State Mirroring.
- **[Logging Matrix](oaConfigurationManager/Documentation/logging_matrix.md)**: Learn how the hierarchical debug system works.
- **[Installation Guide](oaDocumentation/Landmarks/Installation_Guide.md)**: Setup, dependencies, and environment configuration.
- **[Documentation Map](oaDocumentation/Project_Map/Documentation_Map.md)**: Deep dive into the project structure and modules.
- **[SMPTE2138 Bridge](oaComProtocols/oaComSMPTE2138/Documentation/Summary.md)**: Details on the SMPTE ST 2138 Protobuf interface.
- **[Communication Broker](oaComBroker/Documentation/README.md)**: Details on the Protocol Router and Unified Message Schema.
- **[WYSIWYG Editor](oaGuiEditorWYSIWYG/Documentation/wysiwyg_editor.md)**: Learn how to interactively design and build GUI definitions.
- **[Patent Details](oaDocumentation/Patent/01_abstract.md)**: Technical descriptions of the novel architecture.
- **[Schematic Engine](../GitProjects/SchemWeb/crate-engine/Summary.md)**: High-performance Rust/WASM graph processing for the Partitioned Architecture.
- **[Core Backend](../GitProjects/SchemWeb/backend/Summary.md)**: High-performance Express.js API serving the Partitioned Architecture and Widget Registry.
- **[Frontend UI](../GitProjects/SchemWeb/frontend/src/Summary.md)**: React-based schematic visualization and orchestration layer following the Partitioned Architecture.

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
