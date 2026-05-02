# oaGui/Documentation/registry_widget_store.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for the widget registry.

## 🚀 Overview
The `RegistryWidgetStore` is the centralized registry for all dynamic GUI widgets. It facilitates a pluggable UI architecture by auto-discovering widget modules and mapping them to specific "Universal Rhyme" identifiers.

## 🏗️ Partitioned Architecture
- **Layer**: Hooks (UI Partition)
- **Role**: Pluggable Registry 📋🔌

## 🔧 Core Functions
### `scan_widgets()`
- **Purpose**: Auto-discovers widget modules by recursively walking the `oaGuiElements` directory. 🔍
- **Mechanism**:
    1. Uses the **FastScanner** for high-speed module discovery. ⚡
    2. Dynamically imports each module, which triggers self-registration via the `@register` decorator. 📦
- **Outputs**: Populates the global `_registry` with widget creator classes.

### `register()`
- **Purpose**: Class decorator used by widget modules to register themselves with the store. 📝

### `get_creator()`
- **Purpose**: Retrieves the creator class for a specific widget type (e.g. "OcaFader"). 📡📥📥
