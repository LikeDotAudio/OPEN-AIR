# oaGui/Documentation/engine_render_scheduler.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for asynchronous widget rendering.

## 🚀 Overview
The `EngineRenderScheduler` orchestrates the non-blocking, asynchronous batching of functional widgets. It ensures that complex UIs are rendered in "chunks" to keep the application responsive.

## 🏗️ Partitioned Architecture
- **Layer**: Workers (UI Partition)
- **Role**: Batch Render Scheduler ⏳

## 🔧 Core Functions
### `process()`
- **Purpose**: Processes a single chunk of widgets.
- **Actions**:
    1. Determines the **Render Tier** (High-Res vs Fast). 🏎️
    2. Renders each widget in the chunk using modular rendering services.
    3. Applies the widget to the grid topology. 🛠️
    4. Schedules the next chunk using `parent.after(1, ...)` for non-blocking execution. ⚡
- **Outputs**: Triggers an `on_done` callback when all widgets in the sequence are rendered.
