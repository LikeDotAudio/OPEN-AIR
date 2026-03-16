# Clean Code Audit: Bad File/Folder Naming & Containerization Report

## Executive Summary
Analyzed the project structure for intention-revealing names, noise words, redundant prefixes, and flat directories.
- **Naming Violations Identified**: 252
- **Scattered Alike Files (Duplication risk)**: 5

## Top Offenders (Flat Directories & Over-coupling)

### `workers/Splinker/manager`
- Directory contains 23 Python files. Consider grouping into sub-containers (e.g., 'core/', 'utils/', 'ui/').

### `workers/SPLINKER - early thigns - archive`
- Directory contains 16 Python files. Consider grouping into sub-containers (e.g., 'core/', 'utils/', 'ui/').

## Naming Violations

### Noise Word in File Name
- `assets/Testing/FlameGraph/core/capture_data.py`: File 'capture_data.py' contains redundant word 'Data'.
- `managers/Visa_Fleet_Manager/manager_visa_csv_builder.md`: File 'manager_visa_csv_builder.md' contains redundant word 'Builder'.
- `managers/Visa_Fleet_Manager/visa_fleet_manager.md`: File 'visa_fleet_manager.md' contains redundant word 'Manager'.
- `managers/Visa_Fleet_Manager/manager_visa_json_builder.md`: File 'manager_visa_json_builder.md' contains redundant word 'Builder'.
- `managers/Visa_Fleet_Manager/manager_visa_json_builder.py`: File 'manager_visa_json_builder.py' contains redundant word 'Builder'.
- `managers/Visa_Fleet_Manager/visa_fleet_manager.py`: File 'visa_fleet_manager.py' contains redundant word 'Manager'.
- `managers/Visa_Fleet_Manager/manager_visa_csv_builder.py`: File 'manager_visa_csv_builder.py' contains redundant word 'Builder'.
- `managers/configini/config_builder.py`: File 'config_builder.py' contains redundant word 'Builder'.
- `managers/configini/config_builder.md`: File 'config_builder.md' contains redundant word 'Builder'.
- `managers/configini/core/identity_manager.py`: File 'identity_manager.py' contains redundant word 'Manager'.
- `managers/Display/factory/asset_cache_manager.md`: File 'asset_cache_manager.md' contains redundant word 'Manager'.
- `managers/Display/factory/asset_cache_manager.py`: File 'asset_cache_manager.py' contains redundant word 'Manager'.
- `managers/Display/breakoff_manager/hidden_breakoff_manager.py`: File 'hidden_breakoff_manager.py' contains redundant word 'Manager'.
- `managers/Display/breakoff_manager/hidden_breakoff_manager.md`: File 'hidden_breakoff_manager.md' contains redundant word 'Manager'.
- `managers/Display/transparency/transparency_manager.py`: File 'transparency_manager.py' contains redundant word 'Manager'.
- ... and 86 more.

### Naming Convention Violation
- `assets/Stand Alone Utilities/OSC monitor/OSC monitor.py`: File 'OSC monitor.py' uses non-standard characters (should use underscores).
- `managers/yak/Documentation/How to make a yak json.md`: File 'How to make a yak json.md' uses non-standard characters (should use underscores).
- `workers/active/XXX-worker_active_peak_publisher.py`: File 'XXX-worker_active_peak_publisher.py' uses non-standard characters (should use underscores).
- `workers/active/XXX-worker_active_peak_publisher.md`: File 'XXX-worker_active_peak_publisher.md' uses non-standard characters (should use underscores).
- `workers/active/XXX worker_active_marker_tune_and_collect.py`: File 'XXX worker_active_marker_tune_and_collect.py' uses non-standard characters (should use underscores).
- `workers/active/XXX worker_active_marker_tune_and_collect.md`: File 'XXX worker_active_marker_tune_and_collect.md' uses non-standard characters (should use underscores).
- `workers/presets/XXX worker_preset_pusher.md`: File 'XXX worker_preset_pusher.md' uses non-standard characters (should use underscores).
- `workers/presets/XXX worker_preset_pusher.py`: File 'XXX worker_preset_pusher.py' uses non-standard characters (should use underscores).
- `workers/markers/XXXX worker_marker_peak_re_publisher.md`: File 'XXXX worker_marker_peak_re_publisher.md' uses non-standard characters (should use underscores).
- `workers/markers/XXXX worker_marker_peak_re_publisher.py`: File 'XXXX worker_marker_peak_re_publisher.py' uses non-standard characters (should use underscores).
- `workers/Command_Router/mqtt/XXX worker_mqtt_data_flattening.py`: File 'XXX worker_mqtt_data_flattening.py' uses non-standard characters (should use underscores).
- `workers/Command_Router/mqtt/XXX worker_mqtt_data_flattening.md`: File 'XXX worker_mqtt_data_flattening.md' uses non-standard characters (should use underscores).
- `workers/SPLINKER - early thigns - archive/XXX - utils_display_monitor.py`: File 'XXX - utils_display_monitor.py' uses non-standard characters (should use underscores).
- `workers/SPLINKER - early thigns - archive/XXX - utils_display_monitor.py`: File 'XXX - utils_display_monitor.py' uses non-standard characters (should use underscores).
- `workers/SPLINKER - early thigns - archive/xxx - utils_scan_view.py`: File 'xxx - utils_scan_view.py' uses non-standard characters (should use underscores).
- ... and 19 more.

### Noise Word in Folder Name
- `managers`: Folder 'managers' contains redundant word 'Manager'.
- `managers/Visa_Fleet_Manager`: Folder 'Visa_Fleet_Manager' contains redundant word 'Manager'.
- `managers/Display/breakoff_manager`: Folder 'breakoff_manager' contains redundant word 'Manager'.
- `managers/Display/builder`: Folder 'builder' contains redundant word 'Builder'.
- `workers`: Folder 'workers' contains redundant word 'Worker'.
- `workers/Splinker/manager`: Folder 'manager' contains redundant word 'Manager'.
- `workers/builder`: Folder 'builder' contains redundant word 'Builder'.
- `workers/builder/breakoff_manager`: Folder 'breakoff_manager' contains redundant word 'Manager'.
- `workers/builder/data_json_tree`: Folder 'data_json_tree' contains redundant word 'Data'.
- `workers/builder/data_radar`: Folder 'data_radar' contains redundant word 'Data'.
- `workers/builder/data_graphing`: Folder 'data_graphing' contains redundant word 'Data'.
- `workers/Command_Router/Mqtt_Manager`: Folder 'Mqtt_Manager' contains redundant word 'Manager'.
- `display/right_50/bottom_90/10_datasets`: Folder '10_datasets' contains redundant word 'Data'.
- `display/right_50/bottom_90/10_datasets/3_AES70/70_AES70_Object_Model`: Folder '70_AES70_Object_Model' contains redundant word 'Object'.
- `display/right_50/bottom_90/9_Zoo/4_data_graphing`: Folder '4_data_graphing' contains redundant word 'Data'.
- ... and 3 more.

### Redundant Prefix
- `managers/manager_launcher.py`: File 'manager_launcher.py' uses prefix 'manager_' already implied by its parent directory.
- `managers/manager_launcher.md`: File 'manager_launcher.md' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet_Manager/manager_visa_parse_idn.py`: File 'manager_visa_parse_idn.py' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet_Manager/manager_visa_known_types.md`: File 'manager_visa_known_types.md' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet_Manager/manager_visa_csv_builder.md`: File 'manager_visa_csv_builder.md' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet_Manager/manager_visa_json_builder.md`: File 'manager_visa_json_builder.md' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet_Manager/manager_visa_json_builder.py`: File 'manager_visa_json_builder.py' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet_Manager/manager_fleet_mqtt_bridge.py`: File 'manager_fleet_mqtt_bridge.py' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet_Manager/manager_fleet_mqtt_bridge.md`: File 'manager_fleet_mqtt_bridge.md' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet_Manager/manager_visa_Search.md`: File 'manager_visa_Search.md' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet_Manager/manager_visa_csv_builder.py`: File 'manager_visa_csv_builder.py' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet_Manager/manager_visa_Search.py`: File 'manager_visa_Search.py' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet_Manager/manager_visa_known_types.py`: File 'manager_visa_known_types.py' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Fleet_Manager/manager_visa_parse_idn.md`: File 'manager_visa_parse_idn.md' uses prefix 'manager_' already implied by its parent directory.
- `managers/Visa_Scipi_dialog/manager_logic_mqtt_publisher.py`: File 'manager_logic_mqtt_publisher.py' uses prefix 'manager_' already implied by its parent directory.
- ... and 82 more.

## Scattered Alike Files (Conceptual Affinity Issues)
These files share the exact same name but are located in different directories. This often indicates a failure to containerize shared logic or a violation of conceptual affinity.

### `config_reader.py`
- `managers/configini/config_reader.py`
- `workers/Command_Router/mqtt/setup/config_reader.py`

### `hidden_breakoff_manager.py`
- `managers/Display/breakoff_manager/hidden_breakoff_manager.py`
- `workers/builder/breakoff_manager/hidden_breakoff_manager.py`

### `builder.py`
- `workers/builder/builder.py`
- `workers/logic/manifest/builder.py`

### `scale.py`
- `workers/builder/fader/core/scale.py`
- `workers/builder/meter_needle/core/scale.py`

### `constants.py`
- `workers/builder/meter_needle/constants.py`
- `workers/Command_Router/protocol_router/constants.py`

