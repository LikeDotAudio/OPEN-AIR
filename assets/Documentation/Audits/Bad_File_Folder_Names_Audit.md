# Clean Code Audit: Bad File/Folder Naming & Containerization Report

## Executive Summary
Analyzed the project structure for intention-revealing names, noise words, redundant prefixes, and flat directories.
- **Naming Violations Identified**: 252
- **Scattered Alike Files (Duplication risk)**: 5

## Top Offenders (Flat Directories & Over-coupling)

### `workers/Splinker/core`
- Directory contains 23 Python files. Consider grouping into sub-containers (e.g., 'core/', 'utils/', 'ui/').

### `workers/splinker_archive`
- Directory contains 16 Python files. Consider grouping into sub-containers (e.g., 'core/', 'utils/', 'ui/').

## Naming Violations

### Noise Word in File Name
- `assets/Testing/FlameGraph/core/capture.py`: File 'capture_data.py' contains redundant word 'Data'.
- `managers/Visa_Fleet/visa_csv.md`: File 'manager_visa_csv_builder.md' contains redundant word 'Builder'.
- `managers/Visa_Fleet/visa_fleet.md`: File 'visa_fleet_manager.md' contains redundant word 'Manager'.
- `managers/Visa_Fleet/visa_json.md`: File 'manager_visa_json_builder.md' contains redundant word 'Builder'.
- `managers/Visa_Fleet/visa_json.py`: File 'manager_visa_json_builder.py' contains redundant word 'Builder'.
- `managers/Visa_Fleet/visa_fleet.py`: File 'visa_fleet_manager.py' contains redundant word 'Manager'.
- `managers/Visa_Fleet/visa_csv.py`: File 'manager_visa_csv_builder.py' contains redundant word 'Builder'.
- `managers/configini/config.py`: File 'config_builder.py' contains redundant word 'Builder'.
- `managers/configini/config.md`: File 'config_builder.md' contains redundant word 'Builder'.
- `managers/configini/core/identity.py`: File 'identity_manager.py' contains redundant word 'Manager'.
- `managers/Display/factory/asset_cache.md`: File 'asset_cache_manager.md' contains redundant word 'Manager'.
- `managers/Display/factory/asset_cache.py`: File 'asset_cache_manager.py' contains redundant word 'Manager'.
- `managers/Display/breakoff/hidden_breakoff.py`: File 'hidden_breakoff_manager.py' contains redundant word 'Manager'.
- `managers/Display/breakoff/hidden_breakoff.md`: File 'hidden_breakoff_manager.md' contains redundant word 'Manager'.
- `managers/Display/transparency/transparency.py`: File 'transparency_manager.py' contains redundant word 'Manager'.
- ... and 86 more.

### Naming Convention Violation
- `assets/Stand_Alone_Utilities/OSC_monitor/OSC_monitor.py`: File 'OSC monitor.py' uses non-standard characters (should use underscores).
- `managers/yak/Documentation/How_to_make_a_yak_json.md`: File 'How to make a yak json.md' uses non-standard characters (should use underscores).
- `workers/active/active_peak_publisher.py`: File 'XXX-worker_active_peak_publisher.py' uses non-standard characters (should use underscores).
- `workers/active/active_peak_publisher.md`: File 'XXX-worker_active_peak_publisher.md' uses non-standard characters (should use underscores).
- `workers/active/active_marker_tune_and_collect.py`: File 'XXX worker_active_marker_tune_and_collect.py' uses non-standard characters (should use underscores).
- `workers/active/active_marker_tune_and_collect.md`: File 'XXX worker_active_marker_tune_and_collect.md' uses non-standard characters (should use underscores).
- `workers/presets/preset_pusher.md`: File 'XXX worker_preset_pusher.md' uses non-standard characters (should use underscores).
- `workers/presets/preset_pusher.py`: File 'XXX worker_preset_pusher.py' uses non-standard characters (should use underscores).
- `workers/markers/marker_peak_re_publisher.md`: File 'XXXX worker_marker_peak_re_publisher.md' uses non-standard characters (should use underscores).
- `workers/markers/marker_peak_re_publisher.py`: File 'XXXX worker_marker_peak_re_publisher.py' uses non-standard characters (should use underscores).
- `workers/Command_Router/mqtt/mqtt_flattening.py`: File 'XXX worker_mqtt_data_flattening.py' uses non-standard characters (should use underscores).
- `workers/Command_Router/mqtt/mqtt_flattening.md`: File 'XXX worker_mqtt_data_flattening.md' uses non-standard characters (should use underscores).
- `workers/splinker_archive/utils_display_monitor.py`: File 'XXX - utils_display_monitor.py' uses non-standard characters (should use underscores).
- `workers/splinker_archive/utils_display_monitor.py`: File 'XXX - utils_display_monitor.py' uses non-standard characters (should use underscores).
- `workers/splinker_archive/xxx_utils_scan_view.py`: File 'xxx - utils_scan_view.py' uses non-standard characters (should use underscores).
- ... and 19 more.

### Noise Word in Folder Name
- `managers`: Folder 'managers' contains redundant word 'Manager'.
- `managers/Visa_Fleet`: Folder 'Visa_Fleet_Manager' contains redundant word 'Manager'.
- `managers/Display/breakoff`: Folder 'breakoff_manager' contains redundant word 'Manager'.
- `managers/Display/builder`: Folder 'builder' contains redundant word 'Builder'.
- `workers`: Folder 'workers' contains redundant word 'Worker'.
- `workers/Splinker/core`: Folder 'manager' contains redundant word 'Manager'.
- `workers/builder`: Folder 'builder' contains redundant word 'Builder'.
- `workers/builder/breakoff`: Folder 'breakoff_manager' contains redundant word 'Manager'.
- `workers/builder/json_tree`: Folder 'data_json_tree' contains redundant word 'Data'.
- `workers/builder/radar`: Folder 'data_radar' contains redundant word 'Data'.
- `workers/builder/graphing`: Folder 'data_graphing' contains redundant word 'Data'.
- `workers/Command_Router/Mqtt`: Folder 'Mqtt_Manager' contains redundant word 'Manager'.
- `display/right_50/bottom_90/10_sets`: Folder '10_datasets' contains redundant word 'Data'.
- `display/right_50/bottom_90/10_sets/3_AES70/70_AES70_Object_Model`: Folder '70_AES70_Object_Model' contains redundant word 'Object'.
- `display/right_50/bottom_90/9_Zoo/4_graphing`: Folder '4_data_graphing' contains redundant word 'Data'.
- ... and 3 more.

### Redundant Prefix
- `managers/launcher.py`: File 'manager_launcher.py' uses prefix 'manager_' already implied by its parent directory.
- `managers/launcher.md`: File 'manager_launcher.md' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet/visa_parse_idn.py`: File 'manager_visa_parse_idn.py' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet/visa_known_types.md`: File 'manager_visa_known_types.md' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet/visa_csv.md`: File 'manager_visa_csv_builder.md' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet/visa_json.md`: File 'manager_visa_json_builder.md' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet/visa_json.py`: File 'manager_visa_json_builder.py' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet/fleet_mqtt_bridge.py`: File 'manager_fleet_mqtt_bridge.py' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet/fleet_mqtt_bridge.md`: File 'manager_fleet_mqtt_bridge.md' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet/visa_Search.md`: File 'manager_visa_Search.md' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet/visa_csv.py`: File 'manager_visa_csv_builder.py' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet/visa_Search.py`: File 'manager_visa_Search.py' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet/visa_known_types.py`: File 'manager_visa_known_types.py' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet/visa_parse_idn.md`: File 'manager_visa_parse_idn.md' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Scipi_dialog/logic_mqtt_publisher.py`: File 'manager_logic_mqtt_publisher.py' uses prefix 'manager_' already implied by its parent directory.
- ... and 82 more.

## Scattered Alike Files (Conceptual Affinity Issues)
These files share the exact same name but are located in different directories. This often indicates a failure to containerize shared logic or a violation of conceptual affinity.

### `config_reader.py`
- `managers/configini/config_reader.py`
- `workers/Command_Router/mqtt/setup/config_reader.py`

### `hidden_breakoff_manager.py`
- `managers/Display/breakoff/hidden_breakoff.py`
- `workers/builder/breakoff/hidden_breakoff.py`

### `builder.py`
- `workers/builder/builder.py`
- `workers/logic/manifest/builder.py`

### `scale.py`
- `workers/builder/fader/core/scale.py`
- `workers/builder/meter_needle/core/scale.py`

### `constants.py`
- `workers/builder/meter_needle/constants.py`
- `workers/Command_Router/protocol_router/constants.py`

