# oaGui/Documentation/engine_structural_assembler.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for structural container creation.

## 🚀 Overview
The `StructuralAssembler` manages the immediate creation and configuration of structural containers such as `OcaBlock` and `OcaBin`. It handles scrolling behavior, viewport synchronization, and transparency application.

## 🏗️ Partitioned Architecture
- **Layer**: Workers (UI Partition)
- **Role**: Structural Container Factory 🏗️

## 🔧 Core Functions
### `create_block()`
- **Purpose**: Creates a non-scrollable structural container (OcaBlock). 🧱
- **Actions**:
    1. Instantiates a transparent `tk.Canvas`.
    2. Enables grid propagation to allow the container to grow with its children.

### `create_bin()`
- **Purpose**: Creates a scrollable or overlay container (OcaBin). 📦
- **Actions**:
    1. Instantiates a Hull frame and a Viewport canvas.
    2. Optionally adds auto-hiding scrollbars. ↕️
    3. Estantiates an inner content frame and synchronizes its size to the viewport.
    4. Binds responsive sync logic to the Viewport's `<Configure>` event. 📏
