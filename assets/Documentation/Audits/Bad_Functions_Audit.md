Bad functions are excessively large and try to accomplish too much, resulting in muddled intent and ambiguity of purpose...

--- AUDIT RESULTS ---
The following functions violate clean code principles (too many arguments, too large, deep nesting, or flag arguments):

File: Installation/Setup.py
  - Function: main (Line 45)
    * Excessively large (123 lines)

File: Installation/TaskBarIcon.py
  - Function: install_icon (Line 43)
    * Excessively large (121 lines)
    * Deeply nested structure (depth 3)

File: Installation/dependancy/dependancy_checker.py
  - Function: _execute_pip_command (Line 94)
    * Too many arguments (4)
    * Excessively large (52 lines)
    * Deeply nested structure (depth 4)
  - Function: action_check_dependancies (Line 148)
    * Excessively large (91 lines)
    * Deeply nested structure (depth 9)
    * Uses flag argument: 'should_clean_install'
  - Function: run_interactive_pre_check (Line 241)
    * Uses flag argument: 'should_clean_install'

File: Installation/list_fonts.py
  - Function: list_fonts (Line 35)
    * Excessively large (44 lines)

File: OpenAir.py
  - Function: main (Line 65)
    * Excessively large (137 lines)
    * Deeply nested structure (depth 3)

File: assets/Stand Alone Utilities/Fluke Meter/flukeMeter.py
  - Function: select_serial_port (Line 7)
    * Deeply nested structure (depth 3)
  - Function: main (Line 39)
    * Excessively large (51 lines)

File: assets/Stand Alone Utilities/Log Viewer/LogViewer.py
  - Function: update_visuals (Line 160)
    * Too many arguments (4)
    * Excessively large (58 lines)

File: assets/Stand Alone Utilities/OSC monitor/OSC monitor.py
  - Function: _setup_ui (Line 33)
    * Excessively large (80 lines)
  - Function: _sync_ui (Line 175)
    * Too many arguments (4)
    * Excessively large (42 lines)
    * Deeply nested structure (depth 3)

File: assets/Stand Alone Utilities/SUB APP - CSV to json APP/core/csv_converter_engine.py
  - Function: build_hierarchy (Line 11)
    * Too many arguments (4)
    * Excessively large (57 lines)
    * Deeply nested structure (depth 6)

File: assets/Stand Alone Utilities/SUB APP - CSV to json APP/core/header_config_ui.py
  - Function: __init__ (Line 7)
    * Too many arguments (4)

File: assets/Stand Alone Utilities/SUB APP - CSV to json APP/core/json_preview_ui.py
  - Function: update (Line 31)
    * Deeply nested structure (depth 4)
  - Function: insert (Line 34)
    * Deeply nested structure (depth 4)

File: assets/Stand Alone Utilities/SUB APP - CSV to json APP/csvtojson.py
  - Function: convert (Line 98)
    * Deeply nested structure (depth 3)

File: assets/Testing/FlameGraph/core/ClearMQTT.py
  - Function: __init__ (Line 38)
    * Too many arguments (4)
  - Function: on_message (Line 45)
    * Too many arguments (4)
  - Function: sweep (Line 55)
    * Excessively large (64 lines)
    * Deeply nested structure (depth 3)

File: assets/Testing/FlameGraph/core/DeleteCache.py
  - Function: delete_local_data (Line 30)
    * Excessively large (45 lines)
    * Deeply nested structure (depth 3)

File: assets/Testing/FlameGraph/core/Wall_of_pitty.py
  - Function: generate_wall_of_pitty (Line 5)
    * Excessively large (168 lines)
    * Deeply nested structure (depth 4)

File: assets/Testing/FlameGraph/core/capture_data.py
  - Function: kill_all_profilers (Line 8)
    * Deeply nested structure (depth 3)

File: assets/Testing/FlameGraph/core/handle_events.py
  - Function: process_stats_for_ui (Line 6)
    * Excessively large (74 lines)
    * Deeply nested structure (depth 4)

File: assets/Testing/FlameGraph/core/make_graph.py
  - Function: generate_flamegraph_with_flameprof (Line 14)
    * Excessively large (65 lines)

File: assets/Testing/FlameGraph/core/make_html.py
  - Function: generate_final_html (Line 9)
    * Too many arguments (6)

File: assets/Testing/FlameGraph/core/wall_of_shame.py
  - Function: generate_wall_of_shame (Line 4)
    * Excessively large (63 lines)
    * Deeply nested structure (depth 5)

File: assets/Testing/FlameGraph/flamegraph.py
  - Function: synthesize_report (Line 37)
    * Excessively large (52 lines)

File: audit_bad_error_handling.py
  - Function: analyze_error_handling (Line 8)
    * Excessively large (50 lines)
    * Deeply nested structure (depth 6)

File: audit_bad_functions.py
  - Function: audit_file (Line 29)
    * Excessively large (64 lines)
    * Deeply nested structure (depth 6)

File: audit_bad_names.py
  - Function: analyze_naming (Line 15)
    * Excessively large (87 lines)
    * Deeply nested structure (depth 4)
  - Function: visit_Name (Line 36)
    * Deeply nested structure (depth 3)
  - Function: get_parent_assignment (Line 79)
    * Deeply nested structure (depth 4)

File: audit_bad_tests.py
  - Function: get_assertions_count (Line 25)
    * Deeply nested structure (depth 4)
  - Function: analyze_test_file (Line 36)
    * Deeply nested structure (depth 3)
  - Function: find_test_for_file (Line 61)
    * Deeply nested structure (depth 4)

File: audit_file_folder_names.py
  - Function: analyze_file_naming (Line 16)
    * Excessively large (58 lines)
    * Deeply nested structure (depth 4)

File: display/right_50/bottom_90/2_monitors/11_SNMP/00_Log/gui_snmp_log.py
  - Function: __init__ (Line 11)
    * Too many arguments (4)
  - Function: _setup_ui (Line 37)
    * Excessively large (57 lines)
  - Function: on_snmp_traffic (Line 96)
    * Too many arguments (6)
  - Function: _update_oid_state (Line 102)
    * Too many arguments (5)

File: display/right_50/bottom_90/2_monitors/11_SNMP/0_Status/gui_snmp_status.py
  - Function: _setup_ui (Line 38)
    * Excessively large (53 lines)

File: display/right_50/bottom_90/2_monitors/11_SNMP/3_MIB/gui_snmp_mib.py
  - Function: __init__ (Line 13)
    * Too many arguments (4)
  - Function: _check_for_disk_updates (Line 67)
    * Deeply nested structure (depth 3)
  - Function: load_mib_from_disk (Line 81)
    * Deeply nested structure (depth 3)
  - Function: save_mib_as (Line 102)
    * Deeply nested structure (depth 3)

File: display/right_50/bottom_90/2_monitors/11_SNMP/4_Verify_OID/gui_snmp_verify.py
  - Function: __init__ (Line 10)
    * Too many arguments (4)
  - Function: _setup_ui (Line 25)
    * Excessively large (44 lines)

File: display/right_50/bottom_90/2_monitors/11_SNMP/5_Verify_MIB/gui_snmp_verify_mib.py
  - Function: __init__ (Line 11)
    * Too many arguments (4)
  - Function: _setup_ui (Line 27)
    * Excessively large (45 lines)

File: display/right_50/bottom_90/2_monitors/1588_PTP_Monitor/core/ptp_dissector_engine.py
  - Function: populate (Line 7)
    * Deeply nested structure (depth 4)

File: display/right_50/bottom_90/2_monitors/1588_PTP_Monitor/core/ptp_meter_panel.py
  - Function: update (Line 28)
    * Deeply nested structure (depth 3)

File: display/right_50/bottom_90/2_monitors/1588_PTP_Monitor/gui_ptp_monitor.py
  - Function: __init__ (Line 30)
    * Too many arguments (4)

File: display/right_50/bottom_90/2_monitors/22_Yak_Monitor/gui_yak_monitor.py
  - Function: __init__ (Line 38)
    * Too many arguments (4)
  - Function: _setup_ui (Line 82)
    * Excessively large (97 lines)
    * Deeply nested structure (depth 3)
  - Function: _update_log (Line 192)
    * Excessively large (42 lines)
    * Deeply nested structure (depth 5)
  - Function: jump_to_latest_val_msg (Line 278)
    * Deeply nested structure (depth 4)
  - Function: _populate_dissector (Line 297)
    * Deeply nested structure (depth 4)

File: display/right_50/bottom_90/2_monitors/50_MIDI/gui_midi.py
  - Function: _process_activity (Line 111)
    * Deeply nested structure (depth 4)
  - Function: _add_log (Line 134)
    * Too many arguments (4)

File: display/right_50/bottom_90/2_monitors/55_OSC/gui_OSC.py
  - Function: _find_osc_manager (Line 36)
    * Deeply nested structure (depth 3)
  - Function: _setup_ui (Line 58)
    * Excessively large (59 lines)
  - Function: on_osc_activity (Line 140)
    * Too many arguments (5)
  - Function: _add_log_entry (Line 147)
    * Too many arguments (5)

File: display/right_50/bottom_90/3_Command_Router/gui_command_router.py
  - Function: _setup_ui (Line 37)
    * Excessively large (107 lines)
  - Function: on_select_packet (Line 181)
    * Excessively large (45 lines)
    * Deeply nested structure (depth 3)

File: display/right_50/bottom_90/4_Splinker/111_Logs/gui_splinker_logs.py
  - Function: _add_tree_entry (Line 118)
    * Deeply nested structure (depth 3)
  - Function: _refresh_investigation (Line 162)
    * Excessively large (45 lines)

File: display/right_50/bottom_90/4_Splinker/222_ Editor/gui_splinker_editor.py
  - Function: _setup_ui (Line 37)
    * Excessively large (92 lines)
  - Function: on_select_splink (Line 169)
    * Deeply nested structure (depth 3)

File: display/right_50/bottom_90/9_Zoo/1_buttons/2_Trapezoid/6_Media_Buttons/XXXXXXgui_Media_Buttons.py
  - Function: __init__ (Line 66)
    * Too many arguments (4)
  - Function: _construct_dynamic_gui (Line 130)
    * Excessively large (56 lines)

File: display/right_50/bottom_90/9_Zoo/4_data_graphing/1_XY_Graphs/2_Graphing_2/gui_Graphing_Cont.py
  - Function: __init__ (Line 54)
    * Too many arguments (4)
  - Function: _construct_dynamic_gui (Line 114)
    * Excessively large (52 lines)

File: display/right_50/bottom_90/9_Zoo/4_data_graphing/1_XY_Graphs/2_Graphing_3/gui_Graphing_Cont_1.py
  - Function: __init__ (Line 54)
    * Too many arguments (4)
  - Function: _construct_dynamic_gui (Line 116)
    * Excessively large (52 lines)

File: display/right_50/bottom_90/9_Zoo/xxxx_5_indicators/3_Metering/gui_Graphing_Elements.py
  - Function: __init__ (Line 54)
    * Too many arguments (4)
  - Function: _construct_dynamic_gui (Line 114)
    * Excessively large (52 lines)

File: managers/Display/array/array.py
  - Function: make_array (Line 70)
    * Too many arguments (4)
    * Excessively large (116 lines)
  - Function: _inject_data (Line 188)
    * Deeply nested structure (depth 5)

File: managers/Display/array/collapsible_block/collapsible_block.py
  - Function: _create_collapsible_block (Line 18)
    * Too many arguments (4)
    * Excessively large (85 lines)

File: managers/Display/breakoff_manager/hidden_breakoff_manager.py
  - Function: _check_breakoff_state (Line 65)
    * Deeply nested structure (depth 4)

File: managers/Display/builder/async_grid_renderer.py
  - Function: render (Line 25)
    * Too many arguments (8)
    * Deeply nested structure (depth 4)
  - Function: _process_fields (Line 60)
    * Too many arguments (9)
    * Excessively large (55 lines)
    * Deeply nested structure (depth 6)
  - Function: _check_done (Line 65)
    * Deeply nested structure (depth 3)

File: managers/Display/builder/core/batch_processing_engine.py
  - Function: __init__ (Line 6)
    * Too many arguments (4)
    * Uses flag argument: 'local_debug'
  - Function: process (Line 9)
    * Too many arguments (7)
    * Deeply nested structure (depth 4)

File: managers/Display/builder/core/directory_builder.py
  - Function: _add_instance_to_parent (Line 40)
    * Too many arguments (4)
  - Function: _build_from_directory (Line 54)
    * Too many arguments (5)
    * Excessively large (123 lines)
    * Deeply nested structure (depth 8)
  - Function: _process_default_directory_items (Line 179)
    * Too many arguments (4)
  - Function: _process_recursive (Line 153)
    * Deeply nested structure (depth 3)

File: managers/Display/builder/core/grid_topology_configurator.py
  - Function: configure (Line 5)
    * Deeply nested structure (depth 3)

File: managers/Display/builder/core/layout_cache_manager.py
  - Function: load (Line 17)
    * Deeply nested structure (depth 3)
  - Function: _make_cache_serializable (Line 40)
    * Deeply nested structure (depth 3)
  - Function: _restore_cache_paths (Line 50)
    * Deeply nested structure (depth 5)

File: managers/Display/builder/core/navigation_manager.py
  - Function: show_splinker_tab (Line 8)
    * Deeply nested structure (depth 6)
  - Function: _update_dashboard (Line 24)
    * Deeply nested structure (depth 3)

File: managers/Display/builder/core/tab_manager.py
  - Function: _on_tab_change (Line 24)
    * Deeply nested structure (depth 4)
  - Function: _handle_tab_visibility (Line 54)
    * Deeply nested structure (depth 4)
  - Function: _trigger_wysiwyg_editor (Line 79)
    * Deeply nested structure (depth 3)

File: managers/Display/builder/gui_batch_builder.py
  - Function: _create_dynamic_widgets (Line 67)
    * Too many arguments (8)

File: managers/Display/builder/gui_display.py
  - Function: __init__ (Line 47)
    * Too many arguments (13)
    * Excessively large (76 lines)

File: managers/Display/builder/gui_mqtt_manager.py
  - Function: _initialize_mqtt_context (Line 45)
    * Too many arguments (4)

File: managers/Display/builder/gui_rebuilder.py
  - Function: _rebuild_gui (Line 33)
    * Excessively large (65 lines)
    * Deeply nested structure (depth 3)

File: managers/Display/builder/window_manager.py
  - Function: tear_off_tab (Line 61)
    * Excessively large (80 lines)
    * Deeply nested structure (depth 3)

File: managers/Display/core/bootstrap_sequence.py
  - Function: __init__ (Line 21)
    * Too many arguments (6)
  - Function: run (Line 28)
    * Excessively large (53 lines)
  - Function: _launch_app (Line 83)
    * Too many arguments (5)

File: managers/Display/core/shutdown_coordinator.py
  - Function: __init__ (Line 7)
    * Too many arguments (4)
    * Uses flag argument: 'debug_enabled'
  - Function: on_closing (Line 12)
    * Deeply nested structure (depth 6)

File: managers/Display/core/ui_window_manager.py
  - Function: create_root_window (Line 9)
    * Excessively large (52 lines)

File: managers/Display/factory/asset_cache_manager.py
  - Function: get_asset_hash (Line 50)
    * Too many arguments (5)
  - Function: load_from_cache (Line 58)
    * Too many arguments (5)
    * Deeply nested structure (depth 3)
  - Function: save_to_cache (Line 91)
    * Too many arguments (6)

File: managers/Display/factory/button_canvas_base.py
  - Function: __init__ (Line 10)
    * Too many arguments (23)
    * Excessively large (62 lines)
    * Uses flag argument: 'pillow_mode'
  - Function: _generate_rect_glass_texture (Line 114)
    * Too many arguments (8)
    * Excessively large (60 lines)
  - Function: _generate_circular_glass_texture (Line 176)
    * Too many arguments (8)
    * Excessively large (51 lines)

File: managers/Display/factory/core/factory_mapping.py
  - Function: get_core_factory_mapping (Line 1)
    * Excessively large (82 lines)

File: managers/Display/factory/gui_widget_factory.py
  - Function: _lazy_wrap (Line 41)
    * Too many arguments (4)

File: managers/Display/factory/widget_registry.py
  - Function: scan_widgets (Line 95)
    * Excessively large (70 lines)
    * Deeply nested structure (depth 4)

File: managers/Display/loader/blueprint_loader.py
  - Function: load_blueprint (Line 74)
    * Excessively large (43 lines)
  - Function: _recursively_normalize (Line 121)
    * Excessively large (44 lines)
    * Deeply nested structure (depth 6)
  - Function: _load_default_config (Line 168)
    * Deeply nested structure (depth 3)

File: managers/Display/loader/gui_from_json.py
  - Function: __init__ (Line 50)
    * Too many arguments (4)

File: managers/Display/loader/module_loader.py
  - Function: __init__ (Line 40)
    * Too many arguments (5)
  - Function: load_module_from_path (Line 46)
    * Deeply nested structure (depth 3)
  - Function: instantiate_widget (Line 77)
    * Too many arguments (4)
  - Function: load_and_instantiate_gui (Line 103)
    * Too many arguments (4)
    * Excessively large (65 lines)
    * Deeply nested structure (depth 7)

File: managers/Display/open_air_ui.py
  - Function: main (Line 30)
    * Excessively large (42 lines)

File: managers/Display/parser/gui_smart_standardizer.py
  - Function: _standardize_widget_config (Line 11)
    * Excessively large (72 lines)
    * Deeply nested structure (depth 3)
  - Function: _process_homogenized_schema (Line 85)
    * Deeply nested structure (depth 3)

File: managers/Display/parser/layout_parser.py
  - Function: _scan_for_gui_files (Line 60)
    * Deeply nested structure (depth 6)
  - Function: parse_directory (Line 97)
    * Deeply nested structure (depth 3)
  - Function: parse_layout_data (Line 115)
    * Excessively large (59 lines)
    * Deeply nested structure (depth 6)
  - Function: _parse_directory_listing (Line 176)
    * Excessively large (81 lines)
    * Deeply nested structure (depth 3)

File: managers/Display/parser/standardizers/lexicon_expander.py
  - Function: expand (Line 27)
    * Deeply nested structure (depth 4)

File: managers/Display/parser/standardizers/semantic_layout_resolver.py
  - Function: resolve_sticky (Line 12)
    * Excessively large (46 lines)
    * Deeply nested structure (depth 3)

File: managers/Display/parser/widget_schema_normalizer.py
  - Function: normalize (Line 50)
    * Excessively large (180 lines)
    * Deeply nested structure (depth 4)
    * Long if/else/elif chain (4 levels)
  - Function: _process_homogenized_schema (Line 233)
    * Deeply nested structure (depth 3)

File: managers/Display/styling/gui_style_manager.py
  - Function: _blend_colors (Line 15)
    * Too many arguments (4)

File: managers/Display/telemetry/geometry_snitch/geometry_snitch.py
  - Function: _perform_geometry_publish (Line 46)
    * Too many arguments (5)
  - Function: _publish_geometry (Line 51)
    * Too many arguments (5)

File: managers/Display/telemetry/ui_tracking_service.py
  - Function: track (Line 28)
    * Too many arguments (5)
  - Function: _on_destroy (Line 89)
    * Deeply nested structure (depth 3)

File: managers/Display/transparency/transparency_manager.py
  - Function: apply_transparency (Line 30)
    * Too many arguments (4)
    * Excessively large (202 lines)
    * Deeply nested structure (depth 4)
  - Function: _perform_slice (Line 82)
    * Too many arguments (4)
    * Excessively large (138 lines)
    * Deeply nested structure (depth 4)

File: managers/Display/transparency/transparency_mixin.py
  - Function: _apply_transparency (Line 14)
    * Too many arguments (5)
  - Function: register_for_bg_sync (Line 18)
    * Too many arguments (5)

File: managers/PTP/PTPtester.py
  - Function: packet_callback (Line 131)
    * Excessively large (52 lines)
    * Deeply nested structure (depth 3)

File: managers/System_Core/open_air_core.py
  - Function: main (Line 67)
    * Excessively large (95 lines)
    * Deeply nested structure (depth 5)

File: managers/Visa_Fleet_Manager/Prototype/cli_visa_find.py
  - Function: check_host (Line 57)
    * Deeply nested structure (depth 5)
  - Function: hunt_for_devices (Line 91)
    * Deeply nested structure (depth 4)
  - Function: parse_resource_details (Line 144)
    * Deeply nested structure (depth 3)
  - Function: get_gateway_inventory (Line 166)
    * Deeply nested structure (depth 4)
  - Function: query_device_safe (Line 186)
    * Deeply nested structure (depth 3)
  - Function: main (Line 208)
    * Excessively large (132 lines)
    * Deeply nested structure (depth 3)

File: managers/Visa_Fleet_Manager/core/fleet_command_queue_mixin.py
  - Function: enqueue_command (Line 6)
    * Too many arguments (5)
    * Uses flag argument: 'query'

File: managers/Visa_Fleet_Manager/core/fleet_inventory_mixin.py
  - Function: _notify_response (Line 27)
    * Too many arguments (5)
  - Function: _notify_error (Line 31)
    * Too many arguments (4)

File: managers/Visa_Fleet_Manager/manager_fleet_mqtt_bridge.py
  - Function: __init__ (Line 39)
    * Too many arguments (4)
  - Function: _publish_flattened_dict (Line 135)
    * Excessively large (51 lines)
    * Deeply nested structure (depth 4)

File: managers/Visa_Fleet_Manager/manager_visa_Search.py
  - Function: probe_devices (Line 40)
    * Excessively large (139 lines)
    * Deeply nested structure (depth 6)

File: managers/Visa_Fleet_Manager/manager_visa_csv_builder.py
  - Function: build_csvs_from_json (Line 63)
    * Excessively large (47 lines)
    * Deeply nested structure (depth 4)
  - Function: _write_table_to_csv (Line 135)
    * Excessively large (50 lines)

File: managers/Visa_Fleet_Manager/manager_visa_json_builder.py
  - Function: save_query_response_to_json (Line 144)
    * Too many arguments (5)
  - Function: _group_devices_by_type_and_model (Line 174)
    * Excessively large (62 lines)
    * Deeply nested structure (depth 11)
  - Function: _flatten_grouped_inventory (Line 238)
    * Deeply nested structure (depth 10)

File: managers/Visa_Fleet_Manager/visa_fleet_manager.py
  - Function: __init__ (Line 28)
    * Too many arguments (4)
  - Function: set_callbacks (Line 53)
    * Too many arguments (5)

File: managers/Visa_Fleet_Manager/visa_proxy_fleet.py
  - Function: _query_safe_fleet (Line 53)
    * Excessively large (44 lines)
  - Function: __init__ (Line 107)
    * Too many arguments (6)
  - Function: enqueue_command (Line 191)
    * Too many arguments (4)
    * Uses flag argument: 'query'

File: managers/Visa_Fleet_Manager/visa_utility_parser.py
  - Function: parse_resource_details (Line 31)
    * Deeply nested structure (depth 3)
  - Function: query_device_safe (Line 54)
    * Too many arguments (4)
    * Excessively large (42 lines)
    * Deeply nested structure (depth 4)

File: managers/Visa_Scipi_dialog/manager_logic_connect_instrument.py
  - Function: connect_instrument_logic (Line 92)
    * Excessively large (58 lines)

File: managers/Visa_Scipi_dialog/manager_logic_disconnect_instrument.py
  - Function: disconnect_instrument (Line 40)
    * Deeply nested structure (depth 3)
  - Function: disconnect_instrument_logic (Line 89)
    * Excessively large (42 lines)

File: managers/Visa_Scipi_dialog/manager_logic_mqtt_listen.py
  - Function: __init__ (Line 46)
    * Too many arguments (6)
  - Function: _on_search_request (Line 113)
    * Deeply nested structure (depth 3)
  - Function: _on_device_select (Line 145)
    * Deeply nested structure (depth 4)
  - Function: _on_gui_connect_request (Line 180)
    * Deeply nested structure (depth 4)
  - Function: _on_gui_disconnect_request (Line 233)
    * Deeply nested structure (depth 4)
  - Function: _on_connect_request (Line 272)
    * Deeply nested structure (depth 3)

File: managers/Visa_Scipi_dialog/manager_logic_mqtt_publisher.py
  - Function: _update_found_devices_gui (Line 50)
    * Excessively large (101 lines)
    * Deeply nested structure (depth 3)

File: managers/Visa_Scipi_dialog/manager_visa_list_visa_resources.py
  - Function: list_visa_resources (Line 42)
    * Excessively large (45 lines)
    * Deeply nested structure (depth 4)

File: managers/Visa_Scipi_dialog/manager_visa_proxy.py
  - Function: _publish_proxy_response (Line 202)
    * Too many arguments (4)
  - Function: set_instrument_instance (Line 217)
    * Deeply nested structure (depth 3)

File: managers/Visa_Scipi_dialog/manager_visa_reboot.py
  - Function: __init__ (Line 40)
    * Too many arguments (4)
    * Deeply nested structure (depth 3)
  - Function: _setup_mqtt_subscriptions (Line 69)
    * Deeply nested structure (depth 3)
  - Function: _on_reboot_request (Line 84)
    * Deeply nested structure (depth 3)

File: managers/Visa_Scipi_dialog/manager_visa_reset.py
  - Function: __init__ (Line 42)
    * Too many arguments (4)
  - Function: _on_reset_request (Line 68)
    * Deeply nested structure (depth 3)

File: managers/Visa_Scipi_dialog/manager_visa_safe_query.py
  - Function: query_safe (Line 15)
    * Excessively large (58 lines)

File: managers/Visa_Scipi_dialog/manager_visa_search_results.py
  - Function: search_resources (Line 44)
    * Deeply nested structure (depth 4)

File: managers/Visa_Scipi_dialog/worker_visa_pre_flight_check.py
  - Function: list_visa_resources (Line 51)
    * Excessively large (69 lines)
    * Deeply nested structure (depth 4)

File: managers/configini/config_builder.py
  - Function: create_default_config_ini (Line 24)
    * Excessively large (72 lines)
    * Uses flag argument: 'silent'

File: managers/configini/config_reader.py
  - Function: get_instance (Line 36)
    * Deeply nested structure (depth 3)
  - Function: read_config (Line 54)
    * Excessively large (58 lines)
  - Function: s_get (Line 66)
    * Too many arguments (4)

File: managers/configini/console_encoder.py
  - Function: configure_console_encoding (Line 35)
    * Excessively large (46 lines)
    * Deeply nested structure (depth 3)

File: managers/configini/core/config_loader.py
  - Function: load (Line 11)
    * Deeply nested structure (depth 4)
    * Uses flag argument: 'local_debug'

File: managers/manager_launcher.py
  - Function: launch_core_managers (Line 55)
    * Excessively large (171 lines)

File: managers/yak/manager_yak_rx.py
  - Function: __init__ (Line 30)
    * Too many arguments (5)
  - Function: _on_rx_outbox_message (Line 55)
    * Deeply nested structure (depth 3)
  - Function: process_response (Line 97)
    * Too many arguments (4)
    * Excessively large (64 lines)
    * Deeply nested structure (depth 4)

File: managers/yak/yak_command_builder.py
  - Function: fill_scpi_placeholders (Line 41)
    * Deeply nested structure (depth 4)
  - Function: process_fleet (Line 83)
    * Excessively large (43 lines)
    * Deeply nested structure (depth 5)
  - Function: _process_staggered_queue (Line 152)
    * Too many arguments (4)

File: managers/yak/yak_translator.py
  - Function: _on_yak_trigger_message (Line 94)
    * Excessively large (63 lines)

File: managers/yak/yak_trigger_handler.py
  - Function: handle_yak_monitor_traffic (Line 45)
    * Deeply nested structure (depth 3)

File: run_audit.py
  - Function: process_file (Line 16)
    * Excessively large (77 lines)
    * Deeply nested structure (depth 8)

File: update_bad_function_suggestions.py
  - Function: get_function_source (Line 9)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/AES70/aes70.py
  - Function: __init__ (Line 26)
    * Uses flag argument: 'run_bridge'
  - Function: start (Line 56)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/MIDI/core/midi_port_controller.py
  - Function: get_port_info (Line 13)
    * Too many arguments (4)

File: workers/Command_Router/MIDI/midi_manager.py
  - Function: __init__ (Line 24)
    * Uses flag argument: 'run_bridge'
  - Function: _midi_listen_loop (Line 62)
    * Deeply nested structure (depth 5)
  - Function: publish (Line 85)
    * Too many arguments (4)
    * Deeply nested structure (depth 3)
  - Function: _on_protocol_event (Line 101)
    * Deeply nested structure (depth 4)

File: workers/Command_Router/Mqtt_Manager/Stand_Alone_Purge.py
  - Function: purge_mqtt (Line 21)
    * Excessively large (71 lines)

File: workers/Command_Router/Mqtt_Manager/mqtt_manager.py
  - Function: __init__ (Line 32)
    * Too many arguments (4)
  - Function: _publish_async (Line 64)
    * Too many arguments (4)
    * Uses flag argument: 'retain'
  - Function: _publish_worker (Line 68)
    * Deeply nested structure (depth 3)
  - Function: _system_status_loop (Line 82)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/OSC/osc_manager.py
  - Function: __init__ (Line 32)
    * Too many arguments (4)
    * Uses flag argument: 'run_bridge'
  - Function: _notify_monitor (Line 91)
    * Too many arguments (5)
  - Function: start (Line 96)
    * Deeply nested structure (depth 3)
  - Function: handle_incoming_osc (Line 139)
    * Excessively large (45 lines)
  - Function: send (Line 186)
    * Too many arguments (4)
    * Excessively large (57 lines)
  - Function: _on_protocol_event (Line 245)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/OSC/osc_rx_server.py
  - Function: __init__ (Line 31)
    * Too many arguments (4)

File: workers/Command_Router/OSC/osc_tx_client.py
  - Function: send_message (Line 47)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/SNMP/snmp_installer_generator.py
  - Function: generate (Line 6)
    * Excessively large (52 lines)

File: workers/Command_Router/SNMP/snmp_manager.py
  - Function: __init__ (Line 40)
    * Too many arguments (4)
    * Uses flag argument: 'run_bridge'
  - Function: _notify_monitor (Line 79)
    * Too many arguments (6)
    * Deeply nested structure (depth 3)
  - Function: start (Line 89)
    * Deeply nested structure (depth 3)
  - Function: publish (Line 126)
    * Too many arguments (4)
  - Function: run_verification (Line 162)
    * Uses flag argument: 'force_raw'
  - Function: _update_oid_map (Line 176)
    * Excessively large (44 lines)
  - Function: _state_to_file_loop (Line 222)
    * Excessively large (58 lines)
    * Deeply nested structure (depth 6)
  - Function: _file_to_sql_loop (Line 282)
    * Deeply nested structure (depth 7)

File: workers/Command_Router/SNMP/snmp_mib_generator.py
  - Function: generate (Line 15)
    * Excessively large (86 lines)
    * Deeply nested structure (depth 3)
  - Function: write_nodes (Line 77)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/SNMP/snmp_tester.py
  - Function: verify_oid_tree (Line 20)
    * Excessively large (105 lines)
    * Deeply nested structure (depth 4)

File: workers/Command_Router/SNMP/snmp_tree_builder.py
  - Function: generate_master_script (Line 23)
    * Excessively large (76 lines)
  - Function: generate_pass_script (Line 101)
    * Too many arguments (4)

File: workers/Command_Router/SNMP/snmp_utils.py
  - Function: initialize_oid_map (Line 10)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/State_Cache/cache_io_handler.py
  - Function: load_cache (Line 51)
    * Deeply nested structure (depth 4)
  - Function: save_cache (Line 85)
    * Deeply nested structure (depth 4)

File: workers/Command_Router/State_Cache/cache_traffic_controller.py
  - Function: process_traffic (Line 46)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/State_Cache/core/cache_save_engine.py
  - Function: __init__ (Line 9)
    * Too many arguments (4)
    * Uses flag argument: 'debug'
  - Function: _worker (Line 32)
    * Deeply nested structure (depth 5)

File: workers/Command_Router/State_Cache/gui_state_restorer.py
  - Function: restore_timeline (Line 43)
    * Deeply nested structure (depth 4)

File: workers/Command_Router/State_Cache/state_cache_manager.py
  - Function: handle_external_update (Line 99)
    * Too many arguments (5)
  - Function: handle_incoming_mqtt (Line 114)
    * Too many arguments (4)
    * Deeply nested structure (depth 4)

File: workers/Command_Router/State_Cache/state_comparator.py
  - Function: should_update (Line 40)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/mqtt/XXX worker_mqtt_data_flattening.py
  - Function: process_mqtt_message_and_pivot (Line 78)
    * Too many arguments (4)
    * Excessively large (76 lines)
    * Deeply nested structure (depth 3)
  - Function: _flush_buffer (Line 166)
    * Too many arguments (4)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/mqtt/broker_monitor.py
  - Function: _on_sys_message (Line 52)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/mqtt/delete_open_air.py
  - Function: delete_topics (Line 71)
    * Deeply nested structure (depth 4)

File: workers/Command_Router/mqtt/mqtt_connection_manager.py
  - Function: __new__ (Line 32)
    * Deeply nested structure (depth 3)
  - Function: publish (Line 67)
    * Too many arguments (5)
    * Uses flag argument: 'retain'
  - Function: connect_to_broker (Line 92)
    * Too many arguments (5)
  - Function: _mqtt_main_loop (Line 126)
    * Excessively large (46 lines)
  - Function: _queue_worker_task (Line 198)
    * Excessively large (77 lines)
    * Deeply nested structure (depth 6)

File: workers/Command_Router/mqtt/mqtt_publisher_service.py
  - Function: _publish_worker (Line 36)
    * Deeply nested structure (depth 4)
  - Function: start_publisher_worker (Line 62)
    * Deeply nested structure (depth 3)
  - Function: shutdown_publisher_worker (Line 71)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/mqtt/mqtt_subscriber_router.py
  - Function: subscribe_to_topic (Line 53)
    * Deeply nested structure (depth 4)
  - Function: unsubscribe_from_topic (Line 95)
    * Deeply nested structure (depth 5)
  - Function: _on_message (Line 121)
    * Too many arguments (4)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/mqtt/mqtt_topic_utils.py
  - Function: generate_topic_path_from_filepath (Line 12)
    * Excessively large (44 lines)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/mqtt/setup/config_reader.py
  - Function: __new__ (Line 51)
    * Deeply nested structure (depth 3)
  - Function: get_instance (Line 86)
    * Deeply nested structure (depth 3)
  - Function: read_config (Line 122)
    * Excessively large (65 lines)

File: workers/Command_Router/protocol_router/dispatch.py
  - Function: _dispatch_mqtt (Line 45)
    * Too many arguments (4)
  - Function: _dispatch_osc (Line 55)
    * Too many arguments (5)
  - Function: _dispatch_midi (Line 61)
    * Too many arguments (5)
  - Function: _dispatch_snmp (Line 66)
    * Too many arguments (4)

File: workers/Command_Router/protocol_router/dpi.py
  - Function: investigate_packet (Line 7)
    * Excessively large (42 lines)

File: workers/Command_Router/protocol_router/ingest.py
  - Function: normalize_and_ingest (Line 10)
    * Too many arguments (8)
    * Excessively large (107 lines)
    * Deeply nested structure (depth 3)
  - Function: create_silent_msg (Line 119)
    * Too many arguments (5)

File: workers/Command_Router/protocol_router/monitor.py
  - Function: get_splink_relationship (Line 37)
    * Deeply nested structure (depth 3)
  - Function: get_dpi_report (Line 64)
    * Excessively large (71 lines)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/protocol_router/router.py
  - Function: get_instance (Line 63)
    * Deeply nested structure (depth 3)
    * Uses flag argument: 'force_reload'
  - Function: ingest (Line 108)
    * Too many arguments (5)
  - Function: _ingest_silent (Line 115)
    * Too many arguments (5)
  - Function: _ingest_loop (Line 119)
    * Deeply nested structure (depth 4)
  - Function: _dispatch_loop (Line 147)
    * Deeply nested structure (depth 3)
  - Function: publish_splink (Line 165)
    * Too many arguments (5)

File: workers/Command_Router/protocol_router/settle.py
  - Function: is_parameter_locked (Line 23)
    * Deeply nested structure (depth 4)
  - Function: unlock_parameter (Line 42)
    * Deeply nested structure (depth 3)
  - Function: schedule_settling (Line 51)
    * Deeply nested structure (depth 3)

File: workers/Command_Router/protocol_router/strategy.py
  - Function: calculate_ui_tags (Line 27)
    * Deeply nested structure (depth 3)

File: workers/Showtime/core/showtime_draw_bargraph.py
  - Function: create_bar_graph_image (Line 5)
    * Too many arguments (7)
    * Excessively large (42 lines)

File: workers/Showtime/core/showtime_tab.py
  - Function: __init__ (Line 26)
    * Too many arguments (4)

File: workers/Showtime/core/showtime_tune_mixin.py
  - Function: on_tune_request_from_selection (Line 9)
    * Excessively large (44 lines)
    * Deeply nested structure (depth 4)

File: workers/Showtime/core/showtime_ui_mixin.py
  - Function: _create_button_with_bar_graph (Line 54)
    * Too many arguments (4)

File: workers/Showtime/worker_showtime_draw_bargraph.py
  - Function: create_bar_graph_image (Line 44)
    * Too many arguments (7)
    * Excessively large (54 lines)

File: workers/Showtime/worker_showtime_tune.py
  - Function: on_tune_request_from_selection (Line 40)
    * Excessively large (58 lines)
    * Deeply nested structure (depth 4)

File: workers/Splinker/handlers/base_handler.py
  - Function: execute (Line 7)
    * Too many arguments (5)

File: workers/Splinker/handlers/deadband_handler.py
  - Function: execute (Line 9)
    * Too many arguments (5)

File: workers/Splinker/handlers/debounce_handler.py
  - Function: execute (Line 11)
    * Too many arguments (5)

File: workers/Splinker/handlers/invert_handler.py
  - Function: execute (Line 8)
    * Too many arguments (5)
    * Deeply nested structure (depth 3)

File: workers/Splinker/handlers/scale_handler.py
  - Function: execute (Line 9)
    * Too many arguments (5)
    * Excessively large (47 lines)

File: workers/Splinker/manager/_broker_link.py
  - Function: _broker_link (Line 3)
    * Too many arguments (5)
    * Excessively large (50 lines)

File: workers/Splinker/manager/_broker_splice.py
  - Function: _broker_splice (Line 3)
    * Too many arguments (5)
    * Excessively large (51 lines)

File: workers/Splinker/manager/_load_splinks.py
  - Function: _load_splinks (Line 4)
    * Deeply nested structure (depth 3)

File: workers/Splinker/manager/_update_splink.py
  - Function: _update_splink (Line 3)
    * Deeply nested structure (depth 3)

File: workers/Splinker/manager/create_splink_with_params.py
  - Function: create_splink_with_params (Line 5)
    * Too many arguments (5)
    * Excessively large (86 lines)
    * Deeply nested structure (depth 3)

File: workers/Splinker/manager/process_router_event.py
  - Function: process_router_event (Line 4)
    * Excessively large (155 lines)
    * Deeply nested structure (depth 5)

File: workers/Splinker/pipeline.py
  - Function: _build_pipeline (Line 11)
    * Deeply nested structure (depth 3)
  - Function: process (Line 36)
    * Too many arguments (4)
    * Excessively large (54 lines)
    * Deeply nested structure (depth 3)

File: workers/Splinker/splinker_manager.py
  - Function: get_instance (Line 75)
    * Deeply nested structure (depth 3)

File: workers/Worker_Launcher.py
  - Function: launch_all_workers (Line 96)
    * Excessively large (64 lines)

File: workers/active/XXX worker_active_marker_tune_and_collect.py
  - Function: _handle_start_stop (Line 72)
    * Deeply nested structure (depth 4)
  - Function: _processing_loop (Line 106)
    * Deeply nested structure (depth 3)

File: workers/active/XXX-worker_active_peak_publisher.py
  - Function: _on_marker_message (Line 113)
    * Excessively large (54 lines)
  - Function: _republish_to_hierarchical_topic (Line 178)
    * Too many arguments (4)
    * Excessively large (79 lines)

File: workers/active/core/marker_repository_watcher.py
  - Function: on_marker_update (Line 15)
    * Deeply nested structure (depth 6)

File: workers/builder/break_line/hidden_BreakLine.py
  - Function: _create_break_line (Line 22)
    * Too many arguments (4)
    * Excessively large (125 lines)
    * Deeply nested structure (depth 3)
  - Function: redraw_line (Line 101)
    * Deeply nested structure (depth 3)

File: workers/builder/breakoff_manager/hidden_breakoff_manager.py
  - Function: _check_breakoff_state (Line 65)
    * Deeply nested structure (depth 4)

File: workers/builder/builder.py
  - Function: __init__ (Line 82)
    * Too many arguments (5)
    * Excessively large (120 lines)
    * Uses flag argument: 'use_grid'

File: workers/builder/button_actuator/button_actuator.py
  - Function: __init__ (Line 27)
    * Too many arguments (8)
  - Function: make_button_actuator (Line 77)
    * Too many arguments (4)

File: workers/builder/button_toggle/button_toggle.py
  - Function: make_button_toggle (Line 35)
    * Too many arguments (4)
    * Excessively large (153 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/button_toggler/button_toggler.py
  - Function: make_button_toggler (Line 41)
    * Too many arguments (4)
    * Excessively large (222 lines)
    * Deeply nested structure (depth 5)
  - Function: on_button_click (Line 166)
    * Deeply nested structure (depth 4)

File: workers/builder/button_trapezoid/button_trapezoid.py
  - Function: __init__ (Line 27)
    * Too many arguments (9)
    * Excessively large (44 lines)
  - Function: make_button_trapezoid (Line 108)
    * Too many arguments (4)

File: workers/builder/button_trapezoid/core/trapezoid_renderer_mixin.py
  - Function: _draw_trapezoid_button (Line 7)
    * Too many arguments (4)
    * Excessively large (77 lines)

File: workers/builder/button_trapezoid_toggler/button_trapezoid_toggler.py
  - Function: make_button_trapezoid_toggler (Line 44)
    * Too many arguments (4)
    * Excessively large (200 lines)
    * Deeply nested structure (depth 3)
  - Function: sync_to_bool (Line 203)
    * Too many arguments (5)

File: workers/builder/button_wink/button_wink.py
  - Function: make_button_wink (Line 30)
    * Too many arguments (4)
    * Excessively large (157 lines)
    * Deeply nested structure (depth 3)
  - Function: on_value_change (Line 119)
    * Deeply nested structure (depth 3)

File: workers/builder/button_wink/core/wink_config.py
  - Function: extract_wink_config (Line 3)
    * Excessively large (88 lines)

File: workers/builder/button_wink/core/wink_events.py
  - Function: bind_wink_events (Line 8)
    * Too many arguments (6)
    * Excessively large (81 lines)

File: workers/builder/button_wink/core/wink_physics.py
  - Function: update_physics (Line 1)
    * Too many arguments (4)
    * Deeply nested structure (depth 3)
  - Function: blink_loop (Line 38)
    * Too many arguments (5)

File: workers/builder/button_wink/core/wink_renderer.py
  - Function: _create_rounded_rect (Line 4)
    * Too many arguments (6)
  - Function: draw_circular_mask (Line 14)
    * Excessively large (46 lines)
  - Function: draw_rounded_mask (Line 62)
    * Too many arguments (4)
  - Function: draw_glass_lens (Line 102)
    * Too many arguments (8)
    * Excessively large (48 lines)
  - Function: draw_wink_visuals (Line 152)
    * Too many arguments (4)
    * Excessively large (100 lines)
    * Deeply nested structure (depth 5)

File: workers/builder/button_wink/winkdemo.py
  - Function: run_app (Line 114)
    * Excessively large (52 lines)
  - Function: __init__ (Line 4)
    * Too many arguments (12)
  - Function: update_visuals (Line 52)
    * Excessively large (58 lines)

File: workers/builder/button_wink_toggler/button_wink_toggler.py
  - Function: make_button_wink_toggler (Line 20)
    * Too many arguments (4)
    * Excessively large (189 lines)
    * Deeply nested structure (depth 4)
  - Function: sync_from_group (Line 141)
    * Too many arguments (5)
  - Function: sync_from_bool (Line 148)
    * Too many arguments (5)
    * Deeply nested structure (depth 3)

File: workers/builder/checkbox/checkbox.py
  - Function: make_checkbox (Line 58)
    * Too many arguments (4)
    * Excessively large (127 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/circular_motion_displacement_potentiometer/CMDP_tester.py
  - Function: update_table (Line 112)
    * Too many arguments (5)

File: workers/builder/circular_motion_displacement_potentiometer/circular_motion_displacement_potentiometer.py
  - Function: __init__ (Line 35)
    * Too many arguments (4)
  - Function: add_group_ui (Line 94)
    * Too many arguments (4)
    * Uses flag argument: 'iv'
  - Function: revert_to_defaults (Line 100)
    * Deeply nested structure (depth 3)
  - Function: make (Line 113)
    * Deeply nested structure (depth 4)
  - Function: make_circular_motion_displacement_potentiometer (Line 143)
    * Too many arguments (4)

File: workers/builder/circular_motion_displacement_potentiometer/cmdp_channel_handler.py
  - Function: __init__ (Line 11)
    * Too many arguments (12)
  - Function: rotate_point (Line 59)
    * Too many arguments (7)
  - Function: render (Line 64)
    * Excessively large (67 lines)

File: workers/builder/circular_motion_displacement_potentiometer/cmdp_file_handler.py
  - Function: import_json (Line 18)
    * Excessively large (41 lines)
    * Deeply nested structure (depth 5)
  - Function: export_json (Line 61)
    * Excessively large (52 lines)
    * Deeply nested structure (depth 3)
  - Function: find_data (Line 23)
    * Deeply nested structure (depth 3)

File: workers/builder/circular_motion_displacement_potentiometer/cmdp_group_handler.py
  - Function: add_group_ui (Line 24)
    * Too many arguments (5)
    * Uses flag argument: 'initial_visible'
    * Uses flag argument: 'initial_mute'
  - Function: _init_group_state (Line 35)
    * Too many arguments (5)
  - Function: _create_vis_btn (Line 100)
    * Too many arguments (4)
  - Function: _create_mute_btn (Line 108)
    * Too many arguments (4)
  - Function: _attach_group_traces (Line 121)
    * Too many arguments (7)
  - Function: _apply_group_mute (Line 149)
    * Deeply nested structure (depth 3)
  - Function: on_group_drag_move (Line 183)
    * Deeply nested structure (depth 3)

File: workers/builder/circular_motion_displacement_potentiometer/core/cmdp_group_mixin.py
  - Function: pick_group_color (Line 19)
    * Deeply nested structure (depth 3)
  - Function: on_group_drag_move (Line 49)
    * Deeply nested structure (depth 3)

File: workers/builder/circular_motion_displacement_potentiometer/core/cmdp_math.py
  - Function: rotate_point (Line 7)
    * Too many arguments (5)
  - Function: get_position (Line 15)
    * Too many arguments (4)
  - Function: get_angle (Line 22)
    * Too many arguments (4)

File: workers/builder/circular_motion_displacement_potentiometer/core/cmdp_tree_manager.py
  - Function: _on_click (Line 43)
    * Deeply nested structure (depth 3)
  - Function: _spawn_edit (Line 54)
    * Too many arguments (4)

File: workers/builder/circular_motion_displacement_potentiometer/core/ltp_fader.py
  - Function: __init__ (Line 13)
    * Too many arguments (8)
  - Function: render (Line 43)
    * Excessively large (45 lines)

File: workers/builder/composite_horizontal_dial_value/composite_horizontal_dial_value.py
  - Function: make_composite_horizontal_dial_value (Line 37)
    * Too many arguments (4)
    * Excessively large (97 lines)
    * Deeply nested structure (depth 3)
  - Function: make_knob (Line 136)
    * Too many arguments (4)

File: workers/builder/composite_horizontal_dial_value/core/state_sync.py
  - Function: sync_from_main (Line 25)
    * Too many arguments (7)
  - Function: calc_from_fader (Line 41)
    * Too many arguments (6)
  - Function: calc_from_dial (Line 50)
    * Too many arguments (8)
    * Deeply nested structure (depth 5)

File: workers/builder/composite_horizontal_dial_value/core/ui_components.py
  - Function: build_label (Line 8)
    * Too many arguments (6)
  - Function: build_entry (Line 21)
    * Too many arguments (11)
  - Function: build_unit_label (Line 46)
    * Too many arguments (7)

File: workers/builder/composite_mdp/composite_mdp.py
  - Function: __init__ (Line 23)
    * Too many arguments (4)
  - Function: make (Line 31)
    * Excessively large (53 lines)
  - Function: make_composite_mdp (Line 86)
    * Too many arguments (4)

File: workers/builder/composite_mdp/core/mdp_ltp_component.py
  - Function: __init__ (Line 8)
    * Too many arguments (8)

File: workers/builder/composite_mdp/core/mdp_math.py
  - Function: rotate_point (Line 7)
    * Too many arguments (5)

File: workers/builder/composite_mdp/tester.py
  - Function: __init__ (Line 8)
    * Too many arguments (6)
  - Function: rotate_point (Line 39)
    * Too many arguments (6)
  - Function: render (Line 46)
    * Excessively large (49 lines)
  - Function: __init__ (Line 106)
    * Excessively large (47 lines)
  - Function: get_fader_at (Line 155)
    * Deeply nested structure (depth 3)
  - Function: on_scroll (Line 228)
    * Deeply nested structure (depth 4)
  - Function: update_table (Line 244)
    * Too many arguments (7)

File: workers/builder/core/base_widget_creator.py
  - Function: build (Line 13)
    * Too many arguments (4)
    * Excessively large (42 lines)
    * Deeply nested structure (depth 4)
  - Function: _assemble_ui (Line 57)
    * Too many arguments (4)

File: workers/builder/core/builder_background_manager.py
  - Function: _apply_panel_background (Line 37)
    * Too many arguments (4)
    * Excessively large (49 lines)
    * Deeply nested structure (depth 4)
  - Function: _apply_generated_background (Line 88)
    * Too many arguments (5)
    * Deeply nested structure (depth 3)
  - Function: _trigger_background_sync (Line 129)
    * Uses flag argument: 'force'
  - Function: _perform_background_sync (Line 147)
    * Excessively large (51 lines)
    * Deeply nested structure (depth 3)
    * Uses flag argument: 'force'

File: workers/builder/core/builder_context_menu.py
  - Function: _show_wysiwyg_editor (Line 40)
    * Excessively large (49 lines)
    * Deeply nested structure (depth 5)
  - Function: _check_dependencies (Line 91)
    * Deeply nested structure (depth 3)

File: workers/builder/core/builder_slicing_registry.py
  - Function: register_for_slicing (Line 14)
    * Deeply nested structure (depth 4)
  - Function: _perform_batch_reslice (Line 52)
    * Excessively large (112 lines)
    * Deeply nested structure (depth 6)

File: workers/builder/core/ui_geometry_math.py
  - Function: value_to_pixel (Line 18)
    * Too many arguments (5)
    * Uses flag argument: 'reverse'
  - Function: rotate_point (Line 26)
    * Too many arguments (5)
  - Function: get_position (Line 35)
    * Too many arguments (4)
  - Function: get_angle (Line 43)
    * Too many arguments (4)

File: workers/builder/data_graphing/core/annotation_manager.py
  - Function: update (Line 7)
    * Excessively large (41 lines)
    * Deeply nested structure (depth 5)

File: workers/builder/data_graphing/core/graph_context_menu.py
  - Function: show (Line 10)
    * Too many arguments (5)
    * Excessively large (67 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/data_graphing/core/graph_interaction_mixin.py
  - Function: _on_pick (Line 7)
    * Deeply nested structure (depth 3)
  - Function: _on_motion (Line 16)
    * Deeply nested structure (depth 4)
  - Function: _on_marker_release (Line 35)
    * Deeply nested structure (depth 4)

File: workers/builder/data_graphing/core/graph_patina_mixin.py
  - Function: _on_patina_update (Line 12)
    * Excessively large (42 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/data_graphing/core/graph_state_mixin.py
  - Function: _initialize_state_mirroring (Line 19)
    * Deeply nested structure (depth 3)
  - Function: _on_dataset_var_change (Line 32)
    * Deeply nested structure (depth 3)
  - Function: _on_setting_var_change (Line 46)
    * Deeply nested structure (depth 7)

File: workers/builder/data_graphing/core/horizontal_meter_renderer.py
  - Function: __init__ (Line 13)
    * Too many arguments (5)

File: workers/builder/data_graphing/core/vertical_meter_renderer.py
  - Function: __init__ (Line 13)
    * Too many arguments (5)
  - Function: _on_value_change (Line 40)
    * Deeply nested structure (depth 3)

File: workers/builder/data_graphing/core/view_controller.py
  - Function: __init__ (Line 7)
    * Too many arguments (4)
  - Function: on_press (Line 12)
    * Deeply nested structure (depth 3)
  - Function: on_release (Line 28)
    * Deeply nested structure (depth 3)
  - Function: on_motion (Line 39)
    * Deeply nested structure (depth 4)
  - Function: _handle_axis_dblclick (Line 74)
    * Too many arguments (4)
    * Deeply nested structure (depth 4)
  - Function: _set_axis_mode (Line 90)
    * Too many arguments (5)

File: workers/builder/data_graphing/dynamic_bar_graph.py
  - Function: load_initial_data (Line 52)
    * Too many arguments (4)
  - Function: update_plot (Line 68)
    * Too many arguments (4)
  - Function: clear_plot (Line 106)
    * Deeply nested structure (depth 4)

File: workers/builder/data_graphing/dynamic_graph.py
  - Function: __init__ (Line 39)
    * Too many arguments (6)
  - Function: _init_dataset_config (Line 86)
    * Deeply nested structure (depth 4)
  - Function: _on_marker_var_change (Line 118)
    * Deeply nested structure (depth 3)
  - Function: _rename_marker (Line 145)
    * Deeply nested structure (depth 3)

File: workers/builder/data_graphing/graph_interactor.py
  - Function: setup_interaction (Line 13)
    * Too many arguments (4)

File: workers/builder/data_graphing/graph_styler.py
  - Function: apply_style (Line 38)
    * Too many arguments (4)
    * Excessively large (104 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/data_graphing/graph_updater.py
  - Function: update_graph_data (Line 24)
    * Too many arguments (6)
  - Function: load_initial_data (Line 33)
    * Too many arguments (6)

File: workers/builder/data_graphing/plot_widget_adapter.py
  - Function: _create_plot_widget (Line 17)
    * Too many arguments (4)
  - Function: _create_bar_graph_widget (Line 44)
    * Too many arguments (4)

File: workers/builder/data_json_tree/core/json_data_manager.py
  - Function: load (Line 19)
    * Deeply nested structure (depth 4)
  - Function: discover_columns (Line 74)
    * Deeply nested structure (depth 7)

File: workers/builder/data_json_tree/core/json_tree_editor_mixin.py
  - Function: _update_data_from_tree_id (Line 48)
    * Deeply nested structure (depth 3)

File: workers/builder/data_json_tree/core/json_tree_renderer_mixin.py
  - Function: _insert_node_iterative (Line 6)
    * Too many arguments (5)
    * Deeply nested structure (depth 5)
    * Uses flag argument: 'show_values'
  - Function: refresh_tree_display (Line 40)
    * Uses flag argument: 'show_values'

File: workers/builder/data_json_tree/data_json_tree.py
  - Function: __init__ (Line 37)
    * Too many arguments (5)
  - Function: _setup_ui (Line 59)
    * Excessively large (57 lines)
  - Function: make_data_json_tree (Line 159)
    * Too many arguments (4)

File: workers/builder/data_radar/data_radar.py
  - Function: make_data_radar (Line 29)
    * Too many arguments (4)
    * Excessively large (241 lines)
    * Deeply nested structure (depth 5)
  - Function: draw_static_grid (Line 111)
    * Deeply nested structure (depth 5)
  - Function: _perform_draw (Line 158)
    * Deeply nested structure (depth 3)

File: workers/builder/fader/core/cap.py
  - Function: get_3d_fader_cap (Line 12)
    * Too many arguments (5)
    * Excessively large (115 lines)

File: workers/builder/fader/core/fader_renderer_mixin.py
  - Function: _sync_fader_cap_position (Line 9)
    * Too many arguments (4)
  - Function: _draw_fader (Line 38)
    * Too many arguments (4)
    * Excessively large (54 lines)

File: workers/builder/fader/core/fader_state_mixin.py
  - Function: _submit_manual_entry (Line 27)
    * Deeply nested structure (depth 3)

File: workers/builder/fader/core/readout.py
  - Function: draw_floating_value (Line 7)
    * Too many arguments (6)
  - Function: update_static_label (Line 18)
    * Too many arguments (4)

File: workers/builder/fader/core/scale.py
  - Function: draw (Line 8)
    * Too many arguments (5)
  - Function: _get_smart_interval (Line 50)
    * Deeply nested structure (depth 3)
  - Function: _calc_text_offset (Line 98)
    * Too many arguments (7)
  - Function: _calc_tick_y (Line 114)
    * Too many arguments (4)
  - Function: _draw_tick_line (Line 122)
    * Too many arguments (8)
  - Function: _draw_tick_label (Line 132)
    * Too many arguments (7)

File: workers/builder/fader/core/track.py
  - Function: draw (Line 7)
    * Too many arguments (7)

File: workers/builder/fader/fader.py
  - Function: __init__ (Line 35)
    * Too many arguments (7)
    * Excessively large (44 lines)
  - Function: make (Line 85)
    * Excessively large (61 lines)
    * Deeply nested structure (depth 3)
  - Function: make_fader (Line 148)
    * Too many arguments (4)

File: workers/builder/fader_bar_graph/core/fader_bar_asset_generator.py
  - Function: get_3d_cap (Line 13)
    * Too many arguments (5)
    * Excessively large (55 lines)

File: workers/builder/fader_bar_graph/core/fader_bar_interaction_mixin.py
  - Function: _get_val_from_y (Line 13)
    * Too many arguments (4)

File: workers/builder/fader_bar_graph/core/fader_bar_renderer_mixin.py
  - Function: _draw_static (Line 8)
    * Deeply nested structure (depth 3)

File: workers/builder/fader_bar_graph/fader_bar_graph.py
  - Function: __init__ (Line 31)
    * Too many arguments (8)
  - Function: make_fader_bar_graph (Line 83)
    * Too many arguments (4)

File: workers/builder/fader_dual/core/dual_fader_asset_generator.py
  - Function: get_3d_dual_fader_cap (Line 10)
    * Too many arguments (6)
    * Excessively large (61 lines)
    * Uses flag argument: 'is_vertical'

File: workers/builder/fader_dual/core/dual_fader_renderer_mixin.py
  - Function: _draw_fader (Line 7)
    * Excessively large (42 lines)

File: workers/builder/fader_dual/fader_dual.py
  - Function: __init__ (Line 26)
    * Too many arguments (8)
  - Function: make (Line 74)
    * Deeply nested structure (depth 3)
  - Function: make_fader_dual (Line 95)
    * Too many arguments (4)

File: workers/builder/fader_ganged_controlled_array/core/gca_asset_generator.py
  - Function: get_3d_bridge (Line 13)
    * Too many arguments (5)
    * Excessively large (42 lines)

File: workers/builder/fader_ganged_controlled_array/core/gca_controller_mixin.py
  - Function: _update_children_from_master (Line 15)
    * Deeply nested structure (depth 3)
    * Uses flag argument: 'broadcast'
  - Function: _update_master_from_children (Line 25)
    * Uses flag argument: 'broadcast'

File: workers/builder/fader_ganged_controlled_array/core/gca_interaction_mixin.py
  - Function: _on_press (Line 7)
    * Deeply nested structure (depth 4)
  - Function: _on_drag (Line 33)
    * Deeply nested structure (depth 3)
  - Function: _on_mousewheel (Line 53)
    * Deeply nested structure (depth 3)

File: workers/builder/fader_ganged_controlled_array/core/gca_renderer_mixin.py
  - Function: _draw_ticks (Line 13)
    * Too many arguments (4)
  - Function: _draw_channel_lines (Line 37)
    * Too many arguments (4)
  - Function: _draw_channel_labels (Line 68)
    * Too many arguments (4)
  - Function: _draw_macro_view (Line 114)
    * Too many arguments (6)
  - Function: _draw_micro_view (Line 125)
    * Too many arguments (5)
  - Function: _calculate_smart_interval (Line 156)
    * Deeply nested structure (depth 3)

File: workers/builder/fader_ganged_controlled_array/fader_ganged_controlled_array.py
  - Function: __init__ (Line 33)
    * Too many arguments (7)
    * Excessively large (82 lines)
  - Function: make (Line 121)
    * Deeply nested structure (depth 3)
  - Function: make_fader_ganged_controlled_array (Line 156)
    * Too many arguments (4)

File: workers/builder/fader_horizontal/core/horizontal_fader_asset_generator.py
  - Function: get_3d_cap (Line 13)
    * Too many arguments (6)
    * Excessively large (47 lines)

File: workers/builder/fader_horizontal/core/horizontal_fader_renderer_mixin.py
  - Function: _draw_ticks (Line 43)
    * Too many arguments (5)

File: workers/builder/fader_horizontal/fader_horizontal.py
  - Function: __init__ (Line 27)
    * Too many arguments (6)
  - Function: make_fader_horizontal (Line 98)
    * Too many arguments (4)

File: workers/builder/fader_input/fader_input.py
  - Function: make_fader_input (Line 29)
    * Too many arguments (4)
    * Excessively large (61 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/fader_linear_travelling_potentiometer/core/ltp_asset_generator.py
  - Function: get_3d_knob (Line 13)
    * Too many arguments (6)
    * Excessively large (56 lines)
    * Deeply nested structure (depth 3)
  - Function: draw_shape (Line 36)
    * Too many arguments (6)
    * Deeply nested structure (depth 3)

File: workers/builder/fader_linear_travelling_potentiometer/core/ltp_interaction_mixin.py
  - Function: _set_linear_from_event (Line 51)
    * Too many arguments (4)
  - Function: _broadcast_changes (Line 57)
    * Uses flag argument: 'only_linear'

File: workers/builder/fader_linear_travelling_potentiometer/core/ltp_renderer_mixin.py
  - Function: _draw_knob_on_handle (Line 53)
    * Too many arguments (4)

File: workers/builder/fader_linear_travelling_potentiometer/fader_linear_travelling_potentiometer.py
  - Function: __init__ (Line 32)
    * Too many arguments (7)
    * Excessively large (42 lines)
  - Function: make_fader_linear_travelling_potentiometer (Line 101)
    * Too many arguments (4)

File: workers/builder/images_animation_display/images_animation_display.py
  - Function: make_images_animation_display (Line 41)
    * Too many arguments (4)
    * Excessively large (144 lines)
    * Deeply nested structure (depth 3)
  - Function: _update_frame (Line 152)
    * Deeply nested structure (depth 3)

File: workers/builder/images_image_display/images_image_display.py
  - Function: make_images_image_display (Line 47)
    * Too many arguments (4)
    * Excessively large (117 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/images_progress_bar/images_progress_bar.py
  - Function: make_images_progress_bar (Line 21)
    * Too many arguments (4)
    * Excessively large (108 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/input_directional_buttons/input_directional_buttons.py
  - Function: make_input_directional_buttons (Line 46)
    * Too many arguments (4)
    * Excessively large (101 lines)

File: workers/builder/input_inc_dec_buttons/input_inc_dec_buttons.py
  - Function: make_input_inc_dec_buttons (Line 43)
    * Too many arguments (4)
    * Excessively large (108 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/input_mousewheel_mixin/input_mousewheel_mixin.py
  - Function: _on_mousewheel (Line 54)
    * Deeply nested structure (depth 3)

File: workers/builder/knob/core/knob_config.py
  - Function: extract_knob_config (Line 3)
    * Excessively large (76 lines)

File: workers/builder/knob/core/knob_renderer.py
  - Function: draw_knob_visuals (Line 5)
    * Too many arguments (5)
    * Excessively large (140 lines)
    * Deeply nested structure (depth 4)
  - Function: _draw_body (Line 147)
    * Too many arguments (11)
    * Deeply nested structure (depth 4)
  - Function: _draw_track (Line 167)
    * Too many arguments (12)
  - Function: _draw_ticks (Line 184)
    * Too many arguments (10)
    * Deeply nested structure (depth 3)
  - Function: _draw_pointer (Line 203)
    * Too many arguments (11)
  - Function: _get_poly_points (Line 227)
    * Too many arguments (5)
  - Function: _get_gear_points (Line 236)
    * Too many arguments (6)

File: workers/builder/knob/core/knob_renderer_mixin.py
  - Function: _draw_visuals (Line 8)
    * Excessively large (104 lines)
    * Deeply nested structure (depth 4)
  - Function: _draw_body (Line 114)
    * Too many arguments (11)
    * Deeply nested structure (depth 4)
  - Function: _draw_track (Line 131)
    * Too many arguments (12)
  - Function: _draw_ticks (Line 140)
    * Too many arguments (10)
    * Deeply nested structure (depth 3)
  - Function: _draw_pointer (Line 153)
    * Too many arguments (11)
  - Function: _get_poly_points (Line 174)
    * Too many arguments (6)
  - Function: _get_gear_points (Line 183)
    * Too many arguments (7)

File: workers/builder/knob/effects/knob_3d_effects.py
  - Function: draw_knob_3d_effects (Line 4)
    * Too many arguments (6)
    * Excessively large (67 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/knob/knob.py
  - Function: __init__ (Line 29)
    * Too many arguments (8)
  - Function: _assemble_ui (Line 105)
    * Too many arguments (4)
  - Function: make_knob (Line 135)
    * Too many arguments (4)

File: workers/builder/knob_rotary_selector/knob_rotary_selector.py
  - Function: __init__ (Line 32)
    * Too many arguments (7)
    * Uses flag argument: 'continuous'
  - Function: _draw_selector (Line 49)
    * Too many arguments (8)
  - Function: _calc_layout (Line 70)
    * Too many arguments (4)
  - Function: _draw_track (Line 86)
    * Too many arguments (6)
  - Function: _draw_ticks_and_labels (Line 95)
    * Too many arguments (7)
  - Function: _draw_knob_elements (Line 113)
    * Too many arguments (7)
  - Function: _draw_text_overlays (Line 122)
    * Too many arguments (6)
  - Function: make_knob_rotary_selector (Line 144)
    * Excessively large (163 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/listbox/core/listbox_options_manager.py
  - Function: process_mqtt_update (Line 11)
    * Too many arguments (4)

File: workers/builder/listbox/core/listbox_sync_engine.py
  - Function: handle_selection (Line 26)
    * Too many arguments (6)

File: workers/builder/listbox/listbox.py
  - Function: make_listbox (Line 28)
    * Too many arguments (4)
    * Excessively large (65 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/meter_bar/core/ballistics.py
  - Function: update (Line 28)
    * Excessively large (100 lines)
    * Deeply nested structure (depth 5)

File: workers/builder/meter_bar/core/config_parser.py
  - Function: from_dict (Line 101)
    * Excessively large (135 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/meter_bar/core/layout_calculator.py
  - Function: calculate (Line 41)
    * Too many arguments (4)
    * Excessively large (186 lines)
    * Deeply nested structure (depth 5)
  - Function: get_dynamic_coords (Line 229)
    * Too many arguments (6)
    * Excessively large (75 lines)
    * Deeply nested structure (depth 3)
  - Function: get_poly (Line 110)
    * Too many arguments (4)
  - Function: get_poly (Line 237)
    * Too many arguments (4)

File: workers/builder/meter_bar/meter_bar.py
  - Function: make_meter_bar (Line 31)
    * Excessively large (61 lines)
    * Deeply nested structure (depth 4)

File: workers/builder/meter_bar/renderers/tk_canvas_renderer.py
  - Function: draw_static (Line 20)
    * Excessively large (61 lines)
    * Deeply nested structure (depth 4)
  - Function: update_dynamic (Line 83)
    * Too many arguments (4)
    * Deeply nested structure (depth 3)
  - Function: _interpolate_color (Line 127)
    * Too many arguments (4)

File: workers/builder/meter_bar/smart_meter.py
  - Function: __init__ (Line 15)
    * Too many arguments (6)

File: workers/builder/meter_knob_with_vu_meter/meter_knob_with_vu_meter.py
  - Function: make_meter_knob_with_vu_meter (Line 40)
    * Too many arguments (4)
    * Excessively large (116 lines)
    * Deeply nested structure (depth 4)

File: workers/builder/meter_needle/animation/animator.py
  - Function: __init__ (Line 4)
    * Too many arguments (5)
  - Function: animate (Line 42)
    * Excessively large (83 lines)
    * Deeply nested structure (depth 4)

File: workers/builder/meter_needle/config/meter_config.py
  - Function: __getattr__ (Line 66)
    * Deeply nested structure (depth 3)

File: workers/builder/meter_needle/core/needle.py
  - Function: draw_needle (Line 26)
    * Too many arguments (18)
  - Function: draw_with_config (Line 45)
    * Too many arguments (4)
  - Function: _try_update_existing (Line 82)
    * Too many arguments (7)
    * Deeply nested structure (depth 3)
  - Function: _draw_line (Line 104)
    * Too many arguments (8)
  - Function: _draw_taper (Line 109)
    * Too many arguments (8)
  - Function: _draw_knife_edge (Line 117)
    * Too many arguments (8)
  - Function: _draw_baton (Line 125)
    * Too many arguments (8)
  - Function: _draw_teardrop (Line 133)
    * Too many arguments (8)
  - Function: _draw_hollow_diamond (Line 156)
    * Too many arguments (8)

File: workers/builder/meter_needle/core/number.py
  - Function: draw_labels (Line 9)
    * Too many arguments (16)
    * Deeply nested structure (depth 4)

File: workers/builder/meter_needle/core/peak.py
  - Function: draw_peak_dot (Line 6)
    * Too many arguments (9)

File: workers/builder/meter_needle/core/pivot.py
  - Function: draw_pivot (Line 5)
    * Too many arguments (7)

File: workers/builder/meter_needle/core/rendering_engine.py
  - Function: from_config (Line 41)
    * Too many arguments (4)
  - Function: render (Line 67)
    * Too many arguments (8)
    * Uses flag argument: 'full_redraw'
  - Function: _draw_meter_geometry (Line 115)
    * Too many arguments (6)
  - Function: _update_dynamic_elements (Line 159)
    * Too many arguments (8)
  - Function: _draw_static_chassis (Line 184)
    * Deeply nested structure (depth 4)
  - Function: _finalize_z_order (Line 206)
    * Deeply nested structure (depth 3)

File: workers/builder/meter_needle/core/scale.py
  - Function: draw_ticks (Line 10)
    * Too many arguments (21)
    * Excessively large (90 lines)
    * Deeply nested structure (depth 4)
  - Function: draw_arcs (Line 103)
    * Too many arguments (17)
    * Excessively large (82 lines)

File: workers/builder/meter_needle/core/shadow.py
  - Function: draw_shadow (Line 16)
    * Too many arguments (17)
  - Function: draw_with_config (Line 34)
    * Too many arguments (4)
  - Function: _get_shadow_pt (Line 69)
    * Too many arguments (5)
  - Function: _try_update_existing (Line 78)
    * Too many arguments (8)
    * Deeply nested structure (depth 3)
  - Function: _draw_line (Line 108)
    * Too many arguments (8)
  - Function: _draw_taper (Line 115)
    * Too many arguments (8)
  - Function: _draw_knife_edge (Line 127)
    * Too many arguments (8)
  - Function: _draw_baton (Line 139)
    * Too many arguments (8)
  - Function: _draw_teardrop (Line 150)
    * Too many arguments (8)

File: workers/builder/meter_needle/core/visual_helpers.py
  - Function: draw_rounded_rect_poly (Line 5)
    * Too many arguments (8)

File: workers/builder/meter_needle/cosmetics/background.py
  - Function: draw (Line 6)
    * Too many arguments (6)

File: workers/builder/meter_needle/cosmetics/bezel.py
  - Function: draw (Line 6)
    * Too many arguments (6)

File: workers/builder/meter_needle/cosmetics/geometry.py
  - Function: get_scaling_params (Line 36)
    * Too many arguments (4)
    * Deeply nested structure (depth 4)
  - Function: get_bezel_points (Line 58)
    * Too many arguments (7)

File: workers/builder/meter_needle/cosmetics/label.py
  - Function: draw (Line 5)
    * Too many arguments (5)
    * Excessively large (41 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/meter_needle/cosmetics/lens.py
  - Function: draw (Line 9)
    * Too many arguments (6)
    * Excessively large (46 lines)

File: workers/builder/meter_needle/cosmetics/lighting_overlay.py
  - Function: generate_overlay (Line 27)
    * Too many arguments (7)
    * Excessively large (125 lines)
  - Function: _draw_hill_mask (Line 155)
    * Too many arguments (6)
  - Function: photo_image (Line 197)
    * Too many arguments (7)

File: workers/builder/meter_needle/cosmetics/mask.py
  - Function: draw (Line 20)
    * Too many arguments (6)
  - Function: _draw_hill (Line 46)
    * Too many arguments (7)
  - Function: _get_base_y (Line 67)
    * Too many arguments (4)

File: workers/builder/meter_needle/integration/state_linker.py
  - Function: __init__ (Line 16)
    * Too many arguments (5)

File: workers/builder/meter_needle/meter_modifyer.py
  - Function: draw_labels (Line 18)
    * Too many arguments (5)
  - Function: draw_background_faceplate (Line 23)
    * Too many arguments (6)
  - Function: draw_lighting_effects (Line 28)
    * Too many arguments (6)
  - Function: draw_glass_layer (Line 33)
    * Too many arguments (6)
  - Function: draw_foreground_overlay (Line 75)
    * Too many arguments (6)
  - Function: _draw_chassis_mask (Line 87)
    * Too many arguments (6)
    * Excessively large (57 lines)

File: workers/builder/meter_needle/meter_needle.py
  - Function: make_meter_needle (Line 29)
    * Too many arguments (4)
    * Excessively large (42 lines)
    * Deeply nested structure (depth 3)
  - Function: render_cb (Line 50)
    * Uses flag argument: 'full_redraw'

File: workers/builder/meter_needle/ui/frame_factory.py
  - Function: calculate_dimensions (Line 19)
    * Excessively large (60 lines)
  - Function: create_canvas (Line 82)
    * Too many arguments (4)

File: workers/builder/midi_keyboard/builder_midi_keyboard.py
  - Function: _setup_keys (Line 68)
    * Excessively large (44 lines)
  - Function: handle_midi (Line 119)
    * Excessively large (44 lines)
    * Deeply nested structure (depth 5)

File: workers/builder/panel_screw/screw_generator.py
  - Function: generate_screw (Line 19)
    * Excessively large (190 lines)

File: workers/builder/panels/core/layer_metal_fold.py
  - Function: generate_metal_fold (Line 6)
    * Excessively large (65 lines)

File: workers/builder/panels/core/layer_screws.py
  - Function: generate_screws (Line 7)
    * Too many arguments (4)
    * Excessively large (43 lines)
    * Deeply nested structure (depth 4)

File: workers/builder/panels/core/layer_vignette.py
  - Function: generate_vignette (Line 18)
    * Too many arguments (4)

File: workers/builder/panels/core/substrate_factory.py
  - Function: generate_streaks (Line 6)
    * Too many arguments (4)
    * Uses flag argument: 'vertical'

File: workers/builder/panels/panel_generator.py
  - Function: generate_panel (Line 29)
    * Excessively large (162 lines)
    * Deeply nested structure (depth 5)
    * Long if/else/elif chain (4 levels)

File: workers/builder/panels/tiled_panel_generator.py
  - Function: generate_tiled (Line 28)
    * Too many arguments (4)
    * Excessively large (48 lines)
  - Function: _process_single_tile (Line 79)
    * Too many arguments (8)

File: workers/builder/slider_value/slider_value.py
  - Function: make_slider_value (Line 59)
    * Too many arguments (4)
    * Excessively large (194 lines)
    * Deeply nested structure (depth 5)
  - Function: _update_slider_from_entry_var (Line 200)
    * Deeply nested structure (depth 4)

File: workers/builder/status_light/status_light.py
  - Function: __init__ (Line 31)
    * Too many arguments (6)
    * Excessively large (44 lines)
    * Deeply nested structure (depth 3)
  - Function: _update_status_light (Line 77)
    * Deeply nested structure (depth 3)
  - Function: _build_header_status_light (Line 164)
    * Too many arguments (4)

File: workers/builder/text_gui_dropdown_option/core/dropdown_data_manager.py
  - Function: determine_initial_state (Line 19)
    * Too many arguments (4)

File: workers/builder/text_gui_dropdown_option/text_gui_dropdown_option.py
  - Function: make_text_gui_dropdown_option (Line 27)
    * Too many arguments (4)
    * Excessively large (76 lines)
    * Deeply nested structure (depth 4)
  - Function: on_select (Line 64)
    * Deeply nested structure (depth 3)

File: workers/builder/text_label/text_label.py
  - Function: make_text_label (Line 33)
    * Too many arguments (4)
    * Excessively large (110 lines)
    * Deeply nested structure (depth 4)

File: workers/builder/text_label_from_config/text_label_from_config.py
  - Function: make_text_label_from_config (Line 30)
    * Too many arguments (4)

File: workers/builder/text_table/Table_CSV_Reader.py
  - Function: read_from_csv (Line 34)
    * Deeply nested structure (depth 3)

File: workers/builder/text_table/Table_CSV_Writer.py
  - Function: write_to_csv (Line 35)
    * Too many arguments (4)
    * Deeply nested structure (depth 3)

File: workers/builder/text_table/Table_CSV_check.py
  - Function: initialize_from_csv (Line 46)
    * Too many arguments (4)
    * Deeply nested structure (depth 4)

File: workers/builder/text_table/core/table_sync_engine.py
  - Function: __init__ (Line 9)
    * Too many arguments (7)
  - Function: update_full (Line 14)
    * Deeply nested structure (depth 3)
  - Function: update_incremental (Line 41)
    * Excessively large (42 lines)
    * Deeply nested structure (depth 6)

File: workers/builder/text_table/table_editing_inplace_mixin.py
  - Function: commit_edit (Line 114)
    * Excessively large (48 lines)

File: workers/builder/text_table/table_editing_manager.py
  - Function: __init__ (Line 57)
    * Too many arguments (7)
    * Uses flag argument: 'allow_sort'
    * Uses flag argument: 'allow_undo'
    * Uses flag argument: 'allow_delete'

File: workers/builder/text_table/table_editing_row_ops_mixin.py
  - Function: add_row (Line 51)
    * Excessively large (55 lines)
  - Function: delete_selection (Line 116)
    * Deeply nested structure (depth 3)
  - Function: import_data (Line 164)
    * Excessively large (45 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/text_table/table_editing_sort_mixin.py
  - Function: _sort_column (Line 60)
    * Excessively large (55 lines)

File: workers/builder/text_table/table_editing_undo_mixin.py
  - Function: undo (Line 50)
    * Excessively large (70 lines)
    * Deeply nested structure (depth 6)

File: workers/builder/text_table/text_table.py
  - Function: make_text_table (Line 28)
    * Too many arguments (4)
    * Excessively large (69 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/text_value_box/text_value_box.py
  - Function: make_text_value_box (Line 59)
    * Too many arguments (4)
    * Excessively large (203 lines)
    * Deeply nested structure (depth 4)

File: workers/builder/text_value_with_units/text_value_with_units.py
  - Function: make_text_value_with_units (Line 47)
    * Too many arguments (4)
    * Excessively large (147 lines)
    * Deeply nested structure (depth 3)

File: workers/builder/text_web_link/text_web_link.py
  - Function: make_text_web_link (Line 44)
    * Too many arguments (4)
    * Excessively large (99 lines)
    * Deeply nested structure (depth 3)

File: workers/discovery_agents/agent_mdns_zeroconf.py
  - Function: _check_host (Line 72)
    * Deeply nested structure (depth 5)
  - Function: discover_ip_devices (Line 103)
    * Deeply nested structure (depth 5)
  - Function: update_service (Line 29)
    * Too many arguments (4)
  - Function: remove_service (Line 32)
    * Too many arguments (4)
  - Function: add_service (Line 36)
    * Too many arguments (4)

File: workers/discovery_agents/agent_static_ip_prober.py
  - Function: discover_gateway_devices (Line 27)
    * Deeply nested structure (depth 5)

File: workers/discovery_agents/agent_usb_enumerator.py
  - Function: discover_usb_devices (Line 20)
    * Deeply nested structure (depth 3)

File: workers/discovery_agents/discovery_orchestrator.py
  - Function: _discovery_worker_loop (Line 84)
    * Deeply nested structure (depth 3)
  - Function: update_fleet_inventory (Line 146)
    * Excessively large (42 lines)
    * Deeply nested structure (depth 4)

File: workers/exporters/utils_csv_writer.py
  - Function: write_scan_data_to_csv (Line 45)
    * Too many arguments (5)
    * Excessively large (127 lines)
    * Deeply nested structure (depth 4)
    * Uses flag argument: 'append_mode'

File: workers/importers/core/tree_cell_editor.py
  - Function: start (Line 10)
    * Too many arguments (5)

File: workers/importers/core/tree_navigation_engine.py
  - Function: navigate (Line 8)
    * Too many arguments (5)
    * Deeply nested structure (depth 7)
    * Long if/else/elif chain (5 levels)

File: workers/importers/core/tree_sorting_engine.py
  - Function: sort (Line 7)
    * Uses flag argument: 'ascending'

File: workers/importers/formats/worker_importer_from_csv_unknown.py
  - Function: Marker_convert_csv_unknow_report_to_csv (Line 54)
    * Excessively large (91 lines)
    * Deeply nested structure (depth 9)

File: workers/importers/formats/worker_importer_from_ias_html.py
  - Function: Marker_convert_IAShtml_report_to_csv (Line 55)
    * Excessively large (234 lines)
    * Deeply nested structure (depth 13)

File: workers/importers/formats/worker_importer_from_shure_wwb_shw.py
  - Function: Marker_convert_WWB_SHW_File_report_to_csv (Line 57)
    * Excessively large (127 lines)
    * Deeply nested structure (depth 4)

File: workers/importers/formats/worker_importer_from_shure_wwb_zip.py
  - Function: Marker_convert_wwb_zip_report_to_csv (Line 56)
    * Excessively large (112 lines)
    * Deeply nested structure (depth 6)

File: workers/importers/formats/worker_importer_from_soundbase_pdf_v1.py
  - Function: Marker_convert_SB_PDF_File_report_to_csv (Line 58)
    * Excessively large (184 lines)
    * Deeply nested structure (depth 6)

File: workers/importers/formats/worker_importer_from_soundbase_pdf_v2.py
  - Function: Marker_convert_SB_v2_PDF_File_report_to_csv (Line 54)
    * Excessively large (98 lines)
    * Deeply nested structure (depth 6)

File: workers/importers/worker_importer_editor.py
  - Function: start_editing_cell (Line 34)
    * Too many arguments (4)
  - Function: navigate_cells (Line 39)
    * Too many arguments (4)
  - Function: delete_selected_row (Line 77)
    * Deeply nested structure (depth 3)

File: workers/importers/worker_importer_loader.py
  - Function: maker_file_check_for_markers_file (Line 63)
    * Deeply nested structure (depth 3)

File: workers/importers/worker_importer_saver.py
  - Function: save_open_air_file (Line 80)
    * Excessively large (45 lines)

File: workers/importers/worker_marker_csv_to_json_mqtt.py
  - Function: csv_to_json_and_publish (Line 75)
    * Excessively large (103 lines)
    * Deeply nested structure (depth 6)

File: workers/initialization/debug_cleaner.py
  - Function: clear_debug_directory (Line 36)
    * Deeply nested structure (depth 6)

File: workers/logger/log_filter_engine.py
  - Function: handle_filter_update (Line 69)
    * Deeply nested structure (depth 3)

File: workers/logger/logger.py
  - Function: initialize_logging (Line 112)
    * Excessively large (80 lines)

File: workers/logger/set_debug_state.py
  - Function: update_debug_flags (Line 54)
    * Excessively large (79 lines)
    * Deeply nested structure (depth 5)

File: workers/logic/core/sync_queue_mixin.py
  - Function: _process_queue (Line 36)
    * Deeply nested structure (depth 4)

File: workers/logic/manifest/builder.py
  - Function: create_manifest (Line 13)
    * Too many arguments (4)
    * Excessively large (48 lines)

File: workers/logic/state_mirror_engine.py
  - Function: __init__ (Line 35)
    * Too many arguments (5)
  - Function: register_widget (Line 65)
    * Too many arguments (7)
  - Function: initialize_widget_state (Line 88)
    * Deeply nested structure (depth 3)
  - Function: sync_incoming_mqtt_to_gui (Line 149)
    * Deeply nested structure (depth 4)
  - Function: _safe_execute_callback (Line 182)
    * Too many arguments (4)

File: workers/logic/work_stealing_pool.py
  - Function: _worker_loop (Line 50)
    * Deeply nested structure (depth 4)

File: workers/markers/XXXX worker_marker_peak_re_publisher.py
  - Function: _on_nab_output_and_republish_peak (Line 139)
    * Excessively large (59 lines)
    * Deeply nested structure (depth 4)

File: workers/markers/worker_marker_logic.py
  - Function: calculate_frequency_range (Line 53)
    * Deeply nested structure (depth 3)

File: workers/monitoring/fleet_status_monitor.py
  - Function: _on_scan_complete (Line 92)
    * Deeply nested structure (depth 3)

File: workers/presets/XXX worker_preset_pusher.py
  - Function: Tune_to_preset (Line 100)
    * Excessively large (147 lines)
  - Function: publish_message (Line 253)
    * Too many arguments (5)
    * Uses flag argument: 'retain'

File: workers/presets/XXXworker_preset_from_device.py
  - Function: publish_presets_to_repository (Line 188)
    * Excessively large (49 lines)
  - Function: publish_message (Line 292)
    * Too many arguments (5)
    * Uses flag argument: 'retain'

File: workers/splash_screen/core/gif_animator.py
  - Function: load (Line 18)
    * Deeply nested structure (depth 3)

File: workers/splash_screen/makegif.py
  - Function: create_layer (Line 62)
    * Too many arguments (4)
  - Function: update (Line 111)
    * Excessively large (51 lines)
  - Function: update_set (Line 140)
    * Too many arguments (4)

File: workers/splash_screen/splash_screen.py
  - Function: __init__ (Line 16)
    * Too many arguments (4)

File: workers/styling/theme_applier.py
  - Function: apply_theme (Line 6)
    * Excessively large (151 lines)

File: workers/watchdog/watchdog.py
  - Function: _get_main_thread_stack (Line 54)
    * Deeply nested structure (depth 3)
  - Function: _heartbeat_loop (Line 151)
    * Excessively large (104 lines)
    * Deeply nested structure (depth 5)

File: workers/wysiwyg_editor/core/event_bus.py
  - Function: unsubscribe (Line 31)
    * Deeply nested structure (depth 3)
  - Function: publish (Line 38)
    * Deeply nested structure (depth 3)

File: workers/wysiwyg_editor/core/file_io_handler.py
  - Function: save_file (Line 46)
    * Excessively large (44 lines)
    * Deeply nested structure (depth 3)

File: workers/wysiwyg_editor/core/state_manager.py
  - Function: update_state (Line 55)
    * Too many arguments (4)
    * Deeply nested structure (depth 4)
  - Function: batch_update (Line 93)
    * Deeply nested structure (depth 4)
  - Function: reorder_element (Line 119)
    * Too many arguments (4)
  - Function: move_element (Line 161)
    * Too many arguments (4)

File: workers/wysiwyg_editor/grab_bag/grab_bag_loader.py
  - Function: scan_library (Line 24)
    * Excessively large (50 lines)
    * Deeply nested structure (depth 8)

File: workers/wysiwyg_editor/grab_bag/grab_bag_view.py
  - Function: _on_destroy (Line 47)
    * Deeply nested structure (depth 3)
  - Function: _add_component (Line 129)
    * Excessively large (56 lines)
    * Deeply nested structure (depth 4)

File: workers/wysiwyg_editor/run_builder.py
  - Function: main (Line 28)
    * Excessively large (100 lines)

File: workers/wysiwyg_editor/workspaces/core/layout/focus_manager.py
  - Function: handle_focus_request (Line 11)
    * Deeply nested structure (depth 4)

File: workers/wysiwyg_editor/workspaces/core/layout/overlay_manager.py
  - Function: _recursive_clear (Line 17)
    * Deeply nested structure (depth 3)
  - Function: _recursive_apply (Line 25)
    * Deeply nested structure (depth 3)
  - Function: _inject_controls (Line 37)
    * Deeply nested structure (depth 3)

File: workers/wysiwyg_editor/workspaces/core/layout/preview_engine.py
  - Function: _strip_constraints (Line 47)
    * Deeply nested structure (depth 3)

File: workers/wysiwyg_editor/workspaces/core/layout_tools_mixin.py
  - Function: _render_alignment_quick_tools (Line 7)
    * Excessively large (43 lines)
    * Deeply nested structure (depth 5)
  - Function: _render_sticky_quick_tools (Line 52)
    * Excessively large (42 lines)
    * Deeply nested structure (depth 4)
  - Function: _update_tool_highlights (Line 96)
    * Too many arguments (5)
  - Function: set_align (Line 16)
    * Deeply nested structure (depth 5)
    * Long if/else/elif chain (5 levels)
  - Function: set_sticky_preset (Line 61)
    * Deeply nested structure (depth 4)

File: workers/wysiwyg_editor/workspaces/core/leaf_editor_factory.py
  - Function: create (Line 9)
    * Too many arguments (5)
  - Function: _create_color_editor (Line 26)
    * Too many arguments (5)
  - Function: _create_text_editor (Line 47)
    * Too many arguments (6)
  - Function: _bind_entry_focus (Line 69)
    * Too many arguments (6)
    * Deeply nested structure (depth 4)
  - Function: focus_out (Line 73)
    * Deeply nested structure (depth 4)

File: workers/wysiwyg_editor/workspaces/core/property_renderer_mixin.py
  - Function: _render_recursive_properties (Line 9)
    * Too many arguments (6)
    * Deeply nested structure (depth 4)
  - Function: _render_section (Line 29)
    * Too many arguments (8)
  - Function: _render_list_info (Line 64)
    * Too many arguments (4)
  - Function: _render_virtual_leaf (Line 70)
    * Too many arguments (5)

File: workers/wysiwyg_editor/workspaces/layout_overlays/alignment.py
  - Function: apply (Line 5)
    * Too many arguments (5)
    * Excessively large (55 lines)
    * Deeply nested structure (depth 6)
  - Function: sync (Line 41)
    * Too many arguments (4)
  - Function: _toggle (Line 16)
    * Deeply nested structure (depth 5)
    * Long if/else/elif chain (5 levels)

File: workers/wysiwyg_editor/workspaces/layout_overlays/blocks.py
  - Function: apply (Line 4)
    * Too many arguments (5)
    * Deeply nested structure (depth 3)
  - Function: sync (Line 21)
    * Too many arguments (4)

File: workers/wysiwyg_editor/workspaces/layout_overlays/colors.py
  - Function: apply (Line 6)
    * Too many arguments (5)
  - Function: _open_color_picker (Line 36)
    * Deeply nested structure (depth 4)
    * Long if/else/elif chain (4 levels)
  - Function: sync (Line 16)
    * Too many arguments (4)

File: workers/wysiwyg_editor/workspaces/layout_overlays/columns.py
  - Function: apply (Line 4)
    * Too many arguments (5)
    * Deeply nested structure (depth 3)
  - Function: sync (Line 25)
    * Too many arguments (4)
  - Function: sync (Line 19)
    * Too many arguments (4)

File: workers/wysiwyg_editor/workspaces/layout_overlays/selection.py
  - Function: apply (Line 5)
    * Too many arguments (5)
    * Excessively large (55 lines)
  - Function: sync (Line 45)
    * Too many arguments (4)

File: workers/wysiwyg_editor/workspaces/layout_overlays/sizing.py
  - Function: apply (Line 5)
    * Too many arguments (5)
    * Excessively large (95 lines)
    * Deeply nested structure (depth 4)
  - Function: _show_resize_tooltip (Line 19)
    * Too many arguments (7)
  - Function: _on_drag (Line 42)
    * Deeply nested structure (depth 3)
  - Function: _on_release (Line 58)
    * Deeply nested structure (depth 4)
  - Function: sync (Line 90)
    * Too many arguments (4)

File: workers/wysiwyg_editor/workspaces/layout_overlays/sticky.py
  - Function: apply (Line 5)
    * Too many arguments (5)
  - Function: sync (Line 25)
    * Too many arguments (4)

File: workers/wysiwyg_editor/workspaces/layout_overlays/structure.py
  - Function: apply (Line 4)
    * Too many arguments (5)
  - Function: sync (Line 16)
    * Too many arguments (4)

File: workers/wysiwyg_editor/workspaces/tree_refactor.py
  - Function: _build_ui (Line 60)
    * Excessively large (49 lines)
  - Function: _populate_tree (Line 120)
    * Excessively large (75 lines)
    * Deeply nested structure (depth 4)
  - Function: _on_drag_stop (Line 246)
    * Deeply nested structure (depth 3)

File: workers/wysiwyg_editor/wysiwyg_editor.py
  - Function: __init__ (Line 37)
    * Too many arguments (7)
    * Uses flag argument: 'is_standalone'
  - Function: _build_ui (Line 64)
    * Excessively large (74 lines)

