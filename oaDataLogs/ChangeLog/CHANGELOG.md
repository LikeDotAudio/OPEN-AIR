**************************************
Commit: 503cd94143944fff71e5e6284abc661634e0526c
Date: 2026-03-19 01:33:19
Message: Initial Commit
**************************************
## [2026-03-19 10:00:00] Initial Commit

- Initial setup and commit.

## [2026-03-20 00:45:00] Fixed Invisible XY Graphs and Graphing Instantiation

- FIXED: `FluxPlotter` (XY Graphs) invisibility by ensuring plot patches remain active during patina sync and forcing an initial redraw to capture background fabric for the blit engine.
- FIXED: `AttributeError` in `_VUMeterKnob` by correctly registering `_NeedleVUMeter` and updating the composite creator to use the factory pattern.
- FIXED: `Unknown functional widget` errors for `DynamicGraph` and `DynamicBarGraph` by adding the missing lazy-wrappers to `factory_mapping.py`.
- CREATED: Detailed Bug Log at `oaDocumentation/BugLog/BUG_20260320_004500.md`.

## [2026-03-20 00:40:00] Fixed Composite Widgets, Graphing, and Asset Loading

- FIXED: `AttributeError` in `_VUMeterKnob` by correctly registering `_NeedleVUMeter` and updating the composite creator to use the factory pattern instead of direct builder calls.
- FIXED: `Unknown functional widget` errors for `DynamicGraph` and `DynamicBarGraph` by adding the missing lazy-wrappers to `factory_mapping.py`.
- FIXED: Animation loading failures by correcting GIF paths in JSON definitions to point to the valid asset location in `oaGuiMediaElements/Assets/`.
- FIXED: Registry warning for `ProgressBar` by adding the missing static `make` method.
- CREATED: Detailed Bug Log at `oaDocumentation/BugLog/BUG_20260320_004000.md`.

## [2026-03-20 00:30:00] Fixed Scrolling and Visibility for Dynamic GUIs

- FIXED: `DynamicGuiBuilder` scrollable area was broken because `scroll_frame` was incorrectly changed to a `tk.Canvas` with propagation disabled. Changed back to `tk.Frame` with propagation enabled to allow the scrollregion to correctly calculate based on gridded children.
- FIXED: `GuiTable` path resolution in `make_text_table` to ensure widgets without explicit `path` in JSON are correctly registered and initialized.
- RESTORED: Visibility of `7_Data/2_demo` and other large panels that were previously hidden or clipped.
- CREATED: Detailed Bug Log at `oaDocumentation/BugLog/BUG_20260320_003000.md`.

## [2026-03-20 00:25:00] Comprehensive GUI Rendering and Stability Fixes

- FIXED: `GuiTable` (Data Demo) crash during bootstrap by suppressing MQTT publication during initial configuration data sync in `TableSyncEngine`.
- FIXED: `_WinkButton` and `_VUMeterKnob` not rendering by standardizing `widget_type` to `type` in `blinky_winky.json` and `VU_Meter_Knob.json`.
- FIXED: `CMDP` AttributeError `refresh_pop_tree` by adding the missing method to `CMDPWidget`.
- FIXED: `XY Graphs` (FluxPlotter) invisibility by ensuring plot patches remain active during patina sync and forcing an initial redraw to capture background fabric for the blit engine.
- IMPROVED: Error resilience in `BuilderBackgroundManagerMixin` during background color extraction.
- CREATED: Detailed Bug Log at `oaDocumentation/BugLog/BUG_20260320_002500.md`.

## [2026-03-20 00:10:00] Bug Fixes: Widget Type Resolution and black_to_wink_2.json

- FIXED: Widgets using `widget_type` key were not rendering because `WidgetTypeResolver` only checked the `type` key. Updated resolver to handle both.
- UPDATED: `black_to_wink_2.json` to use the standard `type` key for all widgets.
- CREATED: Detailed Bug Log at `oaDocumentation/BugLog/BUG_20260320_001000.md`.

## [2026-03-19 23:55:00] Bug Fixes: Import Path Normalization in oaGuiManager

- FIXED: `ModuleNotFoundError: No module named 'oaGuiManager.Core.Constants'` in `widget_schema_normalizer.py` by converting relative imports to absolute imports.
- FIXED: `ModuleNotFoundError` in `blueprint_loader.py` and `schema_utils.py` by enforcing absolute import paths for `oaGuiManager` submodules.
- CREATED: Detailed Bug Log at `oaDocumentation/BugLog/BUG_20260319_235300.md`.

## [2026-03-19 23:35:00] Bug Fixes: Toggler TypeError, Registry Warnings, and Runner Path

- FIXED: `TypeError` in `CanvasButton._on_release` by adding `try-except TypeError` to support both 0-arg and 1-arg command callbacks. Resolves Toggler group click failures.
- FIXED: Added missing static `make` method to `BuilderButtonToggleCreator` in `oaGuiElements/Core/buttons/button_toggle/button_toggle.py` to eliminate heavy log spam from `WidgetRegistry` discovery.
- FIXED: Corrected `runner_path` in `oaGuiBuilder/Core/context_menu.py` to point to the correct location of `oaGuiEditorWYSIWYG/Managers/run_builder.py`.
- CREATED: Detailed Bug Log at `oaDocumentation/BugLog/BUG_20260319_233000.md`.
