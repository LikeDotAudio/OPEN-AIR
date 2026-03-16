# Clean Code Audit: Bad File/Folder Naming & Containerization Report

## Executive Summary
Analyzed the project structure for intention-revealing names, noise words, redundant prefixes, and flat directories.
- **Naming Violations Identified**: 20
- **Scattered Alike Files (Duplication risk)**: 8

## Top Offenders (Flat Directories & Over-coupling)

### `workers/Splinker/core`
- Directory contains 23 Python files. Consider grouping into sub-containers (e.g., 'core/', 'utils/', 'ui/').

### `workers/splinker_archive`
- Directory contains 16 Python files. Consider grouping into sub-containers (e.g., 'core/', 'utils/', 'ui/').

## Naming Violations

### Noise Word in Folder Name
- `managers`: Folder 'managers' contains redundant word 'Manager'.
- `managers/Display/breakoff/breakoff_manager`: Folder 'breakoff_manager' contains redundant word 'Manager'.
- `managers/Display/builder`: Folder 'builder' contains redundant word 'Builder'.
- `managers/Visa_Fleet/Visa_Fleet_Manager`: Folder 'Visa_Fleet_Manager' contains redundant word 'Manager'.
- `workers`: Folder 'workers' contains redundant word 'Worker'.
- `workers/Splinker/core/manager`: Folder 'manager' contains redundant word 'Manager'.
- `workers/builder`: Folder 'builder' contains redundant word 'Builder'.
- `workers/builder/breakoff/breakoff_manager`: Folder 'breakoff_manager' contains redundant word 'Manager'.
- `workers/Command_Router/Mqtt/Mqtt_Manager`: Folder 'Mqtt_Manager' contains redundant word 'Manager'.
- `display/right_50/bottom_90/10_sets/3_AES70/70_AES70_Object_Model`: Folder '70_AES70_Object_Model' contains redundant word 'Object'.
- `display/right_50/bottom_90/10_sets/3_AES70/70_AES70_Object_Model/70_AES70_Object_Model`: Folder '70_AES70_Object_Model' contains redundant word 'Object'.
- `display/right_50/bottom_90/10_sets/10_datasets`: Folder '10_datasets' contains redundant word 'Data'.
- `display/right_50/bottom_90/9_Zoo/7/7_Data`: Folder '7_Data' contains redundant word 'Data'.
- `display/right_50/bottom_90/6_Setup/0_Fleet/0_Fleet_Manager`: Folder '0_Fleet_Manager' contains redundant word 'Manager'.
- `display/left_50/top_100/0_Spectrum/4_Presets/DataSet`: Folder 'DataSet' contains redundant word 'Data'.

### Redundant Prefix
- `display/right_50/bottom_90/9_Zoo/7/1_dynamic_gui_table/gui_dynamic_gui_table.json`: File 'gui_dynamic_gui_table.json' uses prefix 'gui_' already implied by its parent directory.
- `display/right_50/bottom_90/9_Zoo/1_text/7_gui_listbox/gui_listbox.json`: File 'gui_listbox.json' uses prefix 'gui_' already implied by its parent directory.
- `display/right_50/bottom_90/9_Zoo/1_text/6_gui_dropdown_option/gui_dropdown_option.json`: File 'gui_dropdown_option.json' uses prefix 'gui_' already implied by its parent directory.

## Scattered Alike Files (Conceptual Affinity Issues)
These files share the exact same name but are located in different directories. This often indicates a failure to containerize shared logic or a violation of conceptual affinity.

### `config_reader.py`
- `managers/configini/config_reader.py`
- `workers/Command_Router/mqtt/setup/config_reader.py`

### `hidden_breakoff.py`
- `managers/Display/breakoff/hidden_breakoff.py`
- `workers/builder/breakoff/hidden_breakoff.py`

### `showtime_draw_bargraph.py`
- `workers/Showtime/showtime_draw_bargraph.py`
- `workers/Showtime/core/showtime_draw_bargraph.py`

### `constants.py`
- `workers/Splinker/constants.py`
- `workers/builder/meter_needle/constants.py`
- `workers/Command_Router/protocol_router/constants.py`

### `builder.py`
- `workers/builder/builder.py`
- `workers/logic/manifest/builder.py`

### `scale.py`
- `workers/builder/fader/core/scale.py`
- `workers/builder/meter_needle/core/scale.py`

### `background.py`
- `workers/builder/meter_needle/cosmetics/background.py`
- `workers/builder/core/background.py`

### `settle.py`
- `workers/logic/manifest/settle.py`
- `workers/Command_Router/protocol_router/settle.py`

