# Bad Tests Audit Report

## Executive Summary
Total modules analyzed: 468
- **Missing Tests**: 467
- **Bad Quality Tests**: 1
- **Healthy Tests**: 0

**Test Coverage Rate**: 0.21%

## Top Offenders (Missing Tests)
These modules have no identified test or tester file. High priority for new test creation.

- managers/Display/array/array.py
- managers/Display/array/collapsible_block/collapsible_block.py
- managers/Display/breakoff_manager/hidden_breakoff_manager.py
- managers/Display/builder/async_grid_renderer.py
- managers/Display/builder/core/batch_processing_engine.py
- managers/Display/builder/core/directory_builder.py
- managers/Display/builder/core/grid_topology_configurator.py
- managers/Display/builder/core/layout_cache_manager.py
- managers/Display/builder/core/navigation_manager.py
- managers/Display/builder/core/structural_assembler.py
- managers/Display/builder/core/tab_manager.py
- managers/Display/builder/gui_batch_builder.py
- managers/Display/builder/gui_display.py
- managers/Display/builder/gui_mqtt_manager.py
- managers/Display/builder/gui_rebuilder.py
- managers/Display/builder/window_manager.py
- managers/Display/context/widget_context.py
- managers/Display/core/bootstrap_sequence.py
- managers/Display/core/shutdown_coordinator.py
- managers/Display/core/ui_window_manager.py

... and 447 more.

## Poor Quality Tests
These modules have tests, but they violate clean testing principles.

### workers/builder/composite_mdp/composite_mdp.py
**Test File:** workers/builder/composite_mdp/tester.py
**Issues:**
- Test file exists but contains no test functions

