# 🗺️ OPEN-AIR Documentation Map

This document provides a comprehensive mapping of the OPEN-AIR project structure and its key modules.

## Managers
Managers are passive components that handle state and control logic.

├-----**Display/**<br>
     ├----> **array/**<br>
        |   -> **collapsible_block/**<br>
             ├------->[collapsible_block](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/array/collapsible_block/collapsible_block.md) — *Collapsible Block*<br>
        |   -> [array](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/array/array.md) — *Array*<br>
     ├----> **breakoff_manager/**<br>
        |   -> [hidden_breakoff_manager](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/breakoff/hidden_breakoff.md) — *Hidden Breakoff Manager*<br>
     ├----> **builder/**<br>
        |   -> [DYNAMIC_GUI_GUIDE](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/builder/DYNAMIC_GUI_GUIDE.md) — *Dynamic Gui Guide*<br>
        |   -> [async_grid_renderer](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/builder/async_grid_renderer.md) — *Async Grid Renderer*<br>
        |   -> [gui_batch_builder](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/builder/gui_batch.md) — *Gui Batch Builder*<br>
        |   -> [gui_display](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/builder/gui_display.md) — *Gui Display*<br>
        |   -> [gui_mqtt_manager](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/builder/gui_mqtt.md) — *Gui Mqtt Manager*<br>
        |   -> [gui_rebuilder](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/builder/gui_re.md) — *Gui Rebuilder*<br>
        |   -> [window_manager](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/builder/window.md) — *Window Manager*<br>
     ├----> **context/**<br>
        |   -> [widget_context](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/context/widget_context.md) — *Widget Context*<br>
     ├----> **factory/**<br>
        |   -> [asset_cache_manager](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/factory/asset_cache.md) — *Asset Cache Manager*<br>
        |   -> [button_canvas_base](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/factory/button_canvas_base.md) — *Button Canvas Base*<br>
        |   -> [gui_widget_factory](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/factory/gui_widget_factory.md) — *Gui Widget Factory*<br>
        |   -> [widget_registry](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/factory/widget_registry.md) — *Widget Registry*<br>
     ├----> **loader/**<br>
        |   -> [blueprint_loader](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/loader/blueprint_loader.md) — *Blueprint Loader*<br>
        |   -> [gui_file_loader](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/loader/gui_file_loader.md) — *Gui File Loader*<br>
        |   -> [gui_from_json](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/loader/gui_from_json.md) — *Gui From Json*<br>
        |   -> [module_loader](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/loader/module_loader.md) — *Module Loader*<br>
     ├----> **parser/**<br>
        |   -> [HOMOGENIZED_SCHEMA_SPEC](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/parser/HOMOGENIZED_SCHEMA_SPEC.md) — *Homogenized Schema Spec*<br>
        |   -> [gui_batch_builder](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/parser/gui_batch.md) — *Gui Batch Builder*<br>
        |   -> [gui_file_loader](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/parser/gui_file_loader.md) — *Gui File Loader*<br>
        |   -> [gui_mqtt_manager](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/parser/gui_mqtt.md) — *Gui Mqtt Manager*<br>
        |   -> [gui_rebuilder](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/parser/gui_re.md) — *Gui Rebuilder*<br>
        |   -> [gui_smart_standardizer](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/parser/gui_smart_standardizer.md) — *Gui Smart Standardizer*<br>
        |   -> [gui_style_manager](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/parser/gui_style.md) — *Gui Style Manager*<br>
        |   -> [gui_widget_factory](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/parser/gui_widget_factory.md) — *Gui Widget Factory*<br>
        |   -> [layout_parser](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/parser/layout_parser.md) — *Layout Parser*<br>
        |   -> [widget_schema_normalizer](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/parser/widget_schema_normalizer.md) — *Widget Schema Normalizer*<br>
     ├----> **styling/**<br>
        |   -> [gui_style_manager](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/styling/gui_style.md) — *Gui Style Manager*<br>
     ├----> **telemetry/**<br>
        |   -> **geometry_snitch/**<br>
             ├------->[geometry_snitch](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/telemetry/geometry_snitch/geometry_snitch.md) — *Geometry Snitch*<br>
             ├------->[hidden_geometry_manager](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/telemetry/geometry_snitch/hidden_geometry.md) — *Hidden Geometry Manager*<br>
        |   -> **visibility_snitch/**<br>
             ├------->[hidden_visibility_manager](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/telemetry/visibility_snitch/hidden_visibility.md) — *Hidden Visibility Manager*<br>
             ├------->[visibility_snitch](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/telemetry/visibility_snitch/visibility_snitch.md) — *Visibility Snitch*<br>
        |   -> [ui_tracking_service](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/telemetry/ui_tracking_service.md) — *Ui Tracking Service*<br>
     ├----> **transparency/**<br>
        |   -> [transparency_manager](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/transparency/transparency.md) — *Transparency Manager*<br>
        |   -> [transparency_mixin](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/transparency/transparency_mixin.md) — *Transparency Mixin*<br>
     ├----> [open_air_ui](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Display/open_air_ui.md) — *Open Air Ui*<br>
├-----**PTP/**<br>
     ├----> [PTPtester](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/PTP/PTPtester.md) — *Ptptester*<br>
     ├----> [ptp_manager](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/PTP/ptp.md) — *Ptp Manager*<br>
├-----**System_Core/**<br>
     ├----> [open_air_core](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/System_Core/open_air_core.md) — *Open Air Core*<br>
├-----**Visa_Fleet_Manager/**<br>
     ├----> **Prototype/**<br>
        |   -> [cli_visa_find](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Fleet/Prototype/cli_visa_find.md) — *Cli Visa Find*<br>
     ├----> [manager_fleet_mqtt_bridge](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Fleet/fleet_mqtt_bridge.md) — *Manager Fleet Mqtt Bridge*<br>
     ├----> [manager_visa_Search](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Fleet/visa_Search.md) — *Manager Visa Search*<br>
     ├----> [manager_visa_csv_builder](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Fleet/visa_csv.md) — *Manager Visa Csv Builder*<br>
     ├----> [manager_visa_json_builder](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Fleet/visa_json.md) — *Manager Visa Json Builder*<br>
     ├----> [manager_visa_known_types](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Fleet/visa_known_types.md) — *Manager Visa Known Types*<br>
     ├----> [manager_visa_parse_idn](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Fleet/visa_parse_idn.md) — *Manager Visa Parse Idn*<br>
     ├----> [visa_fleet_manager](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Fleet/visa_fleet.md) — *Visa Fleet Manager*<br>
     ├----> [visa_proxy_fleet](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Fleet/visa_proxy_fleet.md) — *Visa Proxy Fleet*<br>
├-----**Visa_Scipi_dialog/**<br>
     ├----> [manager_logic_connect_instrument](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Scipi_dialog/logic_connect_instrument.md) — *Manager Logic Connect Instrument*<br>
     ├----> [manager_logic_disconnect_instrument](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Scipi_dialog/logic_disconnect_instrument.md) — *Manager Logic Disconnect Instrument*<br>
     ├----> [manager_logic_mqtt_listen](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Scipi_dialog/logic_mqtt_listen.md) — *Manager Logic Mqtt Listen*<br>
     ├----> [manager_logic_mqtt_publisher](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Scipi_dialog/logic_mqtt_publisher.md) — *Manager Logic Mqtt Publisher*<br>
     ├----> [manager_visa](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Scipi_dialog/visa.md) — *Manager Visa*<br>
     ├----> [manager_visa_list_visa_resources](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Scipi_dialog/visa_list_visa_resources.md) — *Manager Visa List Visa Resources*<br>
     ├----> [manager_visa_proxy](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Scipi_dialog/visa_proxy.md) — *Manager Visa Proxy*<br>
     ├----> [manager_visa_reboot](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Scipi_dialog/visa_reboot.md) — *Manager Visa Reboot*<br>
     ├----> [manager_visa_reset](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Scipi_dialog/visa_reset.md) — *Manager Visa Reset*<br>
     ├----> [manager_visa_safe_query](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Scipi_dialog/visa_safe_query.md) — *Manager Visa Safe Query*<br>
     ├----> [manager_visa_safe_writer](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Scipi_dialog/visa_safe_writer.md) — *Manager Visa Safe Writer*<br>
     ├----> [manager_visa_search_results](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Scipi_dialog/visa_search_results.md) — *Manager Visa Search Results*<br>
     ├----> [worker_visa_pre_flight_check](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/Visa_Scipi_dialog/visa_pre_flight_check.md) — *Worker Visa Pre Flight Check*<br>
├-----**configini/**<br>
     ├----> [config_builder](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/configini/config.md) — *Config Builder*<br>
     ├----> [config_reader](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/configini/config_reader.md) — *Config Reader*<br>
     ├----> [config_validator](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/configini/config_validator.md) — *Config Validator*<br>
     ├----> [console_encoder](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/configini/console_encoder.md) — *Console Encoder*<br>
├-----**yak/**<br>
     ├----> **Documentation/**<br>
        |   -> [How to make a yak json](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/yak/Documentation/How%20to%20make%20a%20yak%20json.md) — *How To Make A Yak Json*<br>
     ├----> [manager_yak_rx](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/yak/yak_rx.md) — *Manager Yak Rx*<br>
     ├----> [manager_yak_tx](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/yak/yak_tx.md) — *Manager Yak Tx*<br>
     ├----> [manager_yakety_yak](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/yak/yakety_yak.md) — *Manager Yakety Yak*<br>
     ├----> [yak_command_builder](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/yak/yak_command.md) — *Yak Command Builder*<br>
     ├----> [yak_repository_parser](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/yak/yak_repository_parser.md) — *Yak Repository Parser*<br>
     ├----> [yak_translator](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/yak/yak_translator.md) — *Yak Translator*<br>
     ├----> [yak_trigger_handler](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/yak/yak_trigger_handler.md) — *Yak Trigger Handler*<br>
------[manager_launcher](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/managers/launcher.md) — *Manager Launcher*<br>

## Workers
Workers are active background processes for data acquisition and system monitoring.

├-----**Showtime/**<br>
     ├----> [ptp_time](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/Showtime/ptp_time.md) — *Ptp Time*<br>
     ├----> [worker_showtime_buttons](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/Showtime/showtime_buttons.md) — *Worker Showtime Buttons*<br>
     ├----> [worker_showtime_clear_group_buttons](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/Showtime/showtime_clear_group_buttons.md) — *Worker Showtime Clear Group Buttons*<br>
     ├----> [worker_showtime_draw_bargraph](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/Showtime/showtime_draw_bargraph.md) — *Worker Showtime Draw Bargraph*<br>
     ├----> [worker_showtime_group](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/Showtime/showtime_group.md) — *Worker Showtime Group*<br>
     ├----> [worker_showtime_on_group_toggle](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/Showtime/showtime_on_group_toggle.md) — *Worker Showtime On Group Toggle*<br>
     ├----> [worker_showtime_on_marker_button_click](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/Showtime/showtime_on_marker_button_click.md) — *Worker Showtime On Marker Button Click*<br>
     ├----> [worker_showtime_on_zone_toggle](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/Showtime/showtime_on_zone_toggle.md) — *Worker Showtime On Zone Toggle*<br>
     ├----> [worker_showtime_read](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/Showtime/showtime_read.md) — *Worker Showtime Read*<br>
     ├----> [worker_showtime_tune](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/Showtime/showtime_tune.md) — *Worker Showtime Tune*<br>
├-----**active/**<br>
     ├----> [XXX worker_active_marker_tune_and_collect](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/active/XXX%20worker_active_marker_tune_and_collect.md) — *Xxx Worker Active Marker Tune And Collect*<br>
     ├----> [XXX-worker_active_peak_publisher](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/active/active_peak_publisher.md) — *Xxx-Worker Active Peak Publisher*<br>
├-----**builder/**<br>
     ├----> **break_line/**<br>
        |   -> [hidden_BreakLine](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/break_line/hidden_BreakLine.md) — *Hidden Breakline*<br>
     ├----> **breakoff_manager/**<br>
        |   -> [hidden_breakoff_manager](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/breakoff/hidden_breakoff.md) — *Hidden Breakoff Manager*<br>
     ├----> **button_actuator/**<br>
        |   -> [button_actuator](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/button_actuator/button_actuator.md) — *Button Actuator*<br>
     ├----> **button_toggle/**<br>
        |   -> [button_toggle](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/button_toggle/button_toggle.md) — *Button Toggle*<br>
     ├----> **button_toggler/**<br>
        |   -> [button_toggler](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/button_toggler/button_toggler.md) — *Button Toggler*<br>
     ├----> **button_trapezoid/**<br>
        |   -> [button_trapezoid](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/button_trapezoid/button_trapezoid.md) — *Button Trapezoid*<br>
     ├----> **button_trapezoid_toggler/**<br>
        |   -> [button_trapezoid_toggler](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/button_trapezoid_toggler/button_trapezoid_toggler.md) — *Button Trapezoid Toggler*<br>
     ├----> **button_wink/**<br>
        |   -> **core/**<br>
             ├------->[wink_config](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/button_wink/core/wink_config.md) — *Wink Config*<br>
             ├------->[wink_events](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/button_wink/core/wink_events.md) — *Wink Events*<br>
             ├------->[wink_physics](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/button_wink/core/wink_physics.md) — *Wink Physics*<br>
             ├------->[wink_renderer](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/button_wink/core/wink_renderer.md) — *Wink Renderer*<br>
             ├------->[wink_state](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/button_wink/core/wink_state.md) — *Wink State*<br>
        |   -> [button_wink](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/button_wink/button_wink.md) — *Button Wink*<br>
        |   -> [winkdemo](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/button_wink/winkdemo.md) — *Winkdemo*<br>
     ├----> **button_wink_toggler/**<br>
        |   -> [button_wink_toggler](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/button_wink_toggler/button_wink_toggler.md) — *Button Wink Toggler*<br>
     ├----> **checkbox/**<br>
        |   -> [checkbox](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/checkbox/checkbox.md) — *Checkbox*<br>
     ├----> **circular_motion_displacement_potentiometer/**<br>
        |   -> [CMDP_tester](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/circular_motion_displacement_potentiometer/CMDP_tester.md) — *Cmdp Tester*<br>
        |   -> [circular_motion_displacement_potentiometer](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/circular_motion_displacement_potentiometer/circular_motion_displacement_potentiometer.md) — *Circular Motion Displacement Potentiometer*<br>
        |   -> [cmdp_channel_handler](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/circular_motion_displacement_potentiometer/cmdp_channel_handler.md) — *Cmdp Channel Handler*<br>
        |   -> [cmdp_file_handler](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/circular_motion_displacement_potentiometer/cmdp_file_handler.md) — *Cmdp File Handler*<br>
        |   -> [cmdp_group_handler](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/circular_motion_displacement_potentiometer/cmdp_group_handler.md) — *Cmdp Group Handler*<br>
     ├----> **composite_horizontal_dial_value/**<br>
        |   -> [composite_horizontal_dial_value](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/composite_horizontal_dial_value/composite_horizontal_dial_value.md) — *Composite Horizontal Dial Value*<br>
     ├----> **composite_mdp/**<br>
        |   -> [README](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/composite_mdp/README.md) — *Readme*<br>
        |   -> [composite_mdp](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/composite_mdp/composite_mdp.md) — *Composite Mdp*<br>
        |   -> [tester](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/composite_mdp/tester.md) — *Tester*<br>
     ├----> **data_graphing/**<br>
        |   -> [Meter_to_display_units](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/graphing/Meter_to_display_units.md) — *Meter To Display Units*<br>
        |   -> [dynamic_bar_graph](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/graphing/dynamic_bar_graph.md) — *Dynamic Bar Graph*<br>
        |   -> [dynamic_graph](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/graphing/dynamic_graph.md) — *Dynamic Graph*<br>
        |   -> [graph_builder](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/graphing/graph.md) — *Graph Builder*<br>
        |   -> [graph_interactor](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/graphing/graph_interactor.md) — *Graph Interactor*<br>
        |   -> [graph_styler](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/graphing/graph_styler.md) — *Graph Styler*<br>
        |   -> [graph_updater](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/graphing/graph_updater.md) — *Graph Updater*<br>
        |   -> [meter_widget_adapter](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/graphing/meter_widget_adapter.md) — *Meter Widget Adapter*<br>
        |   -> [plot_widget_adapter](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/graphing/plot_widget_adapter.md) — *Plot Widget Adapter*<br>
     ├----> **data_json_tree/**<br>
        |   -> [data_json_tree](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/json_tree/json_tree.md) — *Data Json Tree*<br>
     ├----> **data_radar/**<br>
        |   -> [data_radar](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/radar/radar.md) — *Data Radar*<br>
     ├----> **fader/**<br>
        |   -> **core/**<br>
             ├------->[cap](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/fader/core/cap.md) — *Cap*<br>
             ├------->[readout](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/fader/core/readout.md) — *Readout*<br>
             ├------->[scale](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/fader/core/scale.md) — *Scale*<br>
             ├------->[track](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/fader/core/track.md) — *Track*<br>
        |   -> [fader](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/fader/fader.md) — *Fader*<br>
     ├----> **fader_bar_graph/**<br>
        |   -> [fader_bar_graph](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/fader_bar_graph/fader_bar_graph.md) — *Fader Bar Graph*<br>
     ├----> **fader_dual/**<br>
        |   -> [fader_dual](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/fader_dual/fader_dual.md) — *Fader Dual*<br>
     ├----> **fader_ganged_controlled_array/**<br>
        |   -> [README](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/fader_ganged_controlled_array/README.md) — *Readme*<br>
        |   -> [fader_ganged_controlled_array](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/fader_ganged_controlled_array/fader_ganged_controlled_array.md) — *Fader Ganged Controlled Array*<br>
     ├----> **fader_horizontal/**<br>
        |   -> [fader_horizontal](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/fader_horizontal/fader_horizontal.md) — *Fader Horizontal*<br>
     ├----> **fader_input/**<br>
        |   -> [fader_input](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/fader_input/fader_input.md) — *Fader Input*<br>
     ├----> **fader_linear_travelling_potentiometer/**<br>
        |   -> [README](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/fader_linear_travelling_potentiometer/README.md) — *Readme*<br>
        |   -> [fader_linear_travelling_potentiometer](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/fader_linear_travelling_potentiometer/fader_linear_travelling_potentiometer.md) — *Fader Linear Travelling Potentiometer*<br>
     ├----> **images_animation_display/**<br>
        |   -> [images_animation_display](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/images_animation_display/images_animation_display.md) — *Images Animation Display*<br>
     ├----> **images_image_display/**<br>
        |   -> [images_image_display](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/images_image_display/images_image_display.md) — *Images Image Display*<br>
     ├----> **images_progress_bar/**<br>
        |   -> [images_progress_bar](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/images_progress_bar/images_progress_bar.md) — *Images Progress Bar*<br>
     ├----> **input_directional_buttons/**<br>
        |   -> [input_directional_buttons](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/input_directional_buttons/input_directional_buttons.md) — *Input Directional Buttons*<br>
     ├----> **input_inc_dec_buttons/**<br>
        |   -> [input_inc_dec_buttons](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/input_inc_dec_buttons/input_inc_dec_buttons.md) — *Input Inc Dec Buttons*<br>
     ├----> **input_mousewheel_mixin/**<br>
        |   -> [input_mousewheel_mixin](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/input_mousewheel_mixin/input_mousewheel_mixin.md) — *Input Mousewheel Mixin*<br>
        |   -> [test_dynamic_gui_mousewheel_mixin](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/input_mousewheel_mixin/test_dynamic_gui_mousewheel_mixin.md) — *Test Dynamic Gui Mousewheel Mixin*<br>
     ├----> **knob/**<br>
        |   -> **core/**<br>
             ├------->[knob_config](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/knob/core/wink_config.md) — *Knob Config*<br>
             ├------->[knob_events](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/knob/core/wink_events.md) — *Knob Events*<br>
             ├------->[knob_renderer](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/knob/core/wink_renderer.md) — *Knob Renderer*<br>
             ├------->[knob_state](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/knob/core/wink_state.md) — *Knob State*<br>
        |   -> **effects/**<br>
             ├------->[knob_3d_effects](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/knob/effects/knob_3d_effects.md) — *Knob 3D Effects*<br>
        |   -> [knob](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/knob/knob.md) — *Knob*<br>
     ├----> **knob_rotary_selector/**<br>
        |   -> [knob_rotary_selector](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/knob_rotary_selector/knob_rotary_selector.md) — *Knob Rotary Selector*<br>
     ├----> **listbox/**<br>
        |   -> [listbox](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/listbox/listbox.md) — *Listbox*<br>
     ├----> **meter_bar/**<br>
        |   -> **core/**<br>
             ├------->[ballistics](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_bar/core/ballistics.md) — *Ballistics*<br>
             ├------->[config_parser](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_bar/core/config_parser.md) — *Config Parser*<br>
             ├------->[layout_calculator](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_bar/core/layout_calculator.md) — *Layout Calculator*<br>
        |   -> **renderers/**<br>
             ├------->[tk_canvas_renderer](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_bar/renderers/tk_canvas_renderer.md) — *Tk Canvas Renderer*<br>
        |   -> [meter_bar](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_bar/meter_bar.md) — *Meter Bar*<br>
        |   -> [smart_meter](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_bar/smart_meter.md) — *Smart Meter*<br>
     ├----> **meter_knob_with_vu_meter/**<br>
        |   -> [meter_knob_with_vu_meter](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_knob_with_vu_meter/meter_knob_with_vu_meter.md) — *Meter Knob With Vu Meter*<br>
     ├----> **meter_needle/**<br>
        |   -> **animation/**<br>
             ├------->[animator](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/animation/animator.md) — *Animator*<br>
        |   -> **config/**<br>
             ├------->[meter_config](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/config/meter_config.md) — *Meter Config*<br>
        |   -> **core/**<br>
             ├------->[needle](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/core/needle.md) — *Needle*<br>
             ├------->[number](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/core/number.md) — *Number*<br>
             ├------->[peak](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/core/peak.md) — *Peak*<br>
             ├------->[pivot](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/core/pivot.md) — *Pivot*<br>
             ├------->[scale](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/core/scale.md) — *Scale*<br>
             ├------->[shadow](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/core/shadow.md) — *Shadow*<br>
        |   -> **cosmetics/**<br>
             ├------->[background](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/cosmetics/background.md) — *Background*<br>
             ├------->[bezel](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/cosmetics/bezel.md) — *Bezel*<br>
             ├------->[geometry](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/cosmetics/geometry.md) — *Geometry*<br>
             ├------->[label](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/cosmetics/label.md) — *Label*<br>
             ├------->[lens](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/cosmetics/lens.md) — *Lens*<br>
             ├------->[lighting_overlay](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/cosmetics/lighting_overlay.md) — *Lighting Overlay*<br>
             ├------->[mask](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/cosmetics/mask.md) — *Mask*<br>
        |   -> **integration/**<br>
             ├------->[state_linker](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/integration/state_linker.md) — *State Linker*<br>
        |   -> **ui/**<br>
             ├------->[frame_factory](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/ui/frame_factory.md) — *Frame Factory*<br>
        |   -> [constants](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/constants.md) — *Constants*<br>
        |   -> [meter_modifyer](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/meter_modifyer.md) — *Meter Modifyer*<br>
        |   -> [meter_needle](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/meter_needle/meter_needle.md) — *Meter Needle*<br>
     ├----> **panel_screw/**<br>
        |   -> [screw_generator](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/panel_screw/screw_generator.md) — *Screw Generator*<br>
     ├----> **panels/**<br>
        |   -> [HOW_TO_USE_BACKGROUNDS](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/panels/HOW_TO_USE_BACKGROUNDS.md) — *How To Use Backgrounds*<br>
        |   -> [panel_generator](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/panels/panel_generator.md) — *Panel Generator*<br>
     ├----> **slider_value/**<br>
        |   -> [slider_value](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/slider_value/slider_value.md) — *Slider Value*<br>
     ├----> **status_light/**<br>
        |   -> [status_light](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/status_light/status_light.md) — *Status Light*<br>
     ├----> **text_gui_dropdown_option/**<br>
        |   -> [text_gui_dropdown_option](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/text_gui_dropdown_option/text_gui_dropdown_option.md) — *Text Gui Dropdown Option*<br>
     ├----> **text_label/**<br>
        |   -> [text_label](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/text_label/text_label.md) — *Text Label*<br>
     ├----> **text_label_from_config/**<br>
        |   -> [text_label_from_config](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/text_label_from_config/text_label_from_config.md) — *Text Label From Config*<br>
     ├----> **text_table/**<br>
        |   -> [Table_CSV_Reader](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/text_table/Table_CSV_Reader.md) — *Table Csv Reader*<br>
        |   -> [Table_CSV_Writer](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/text_table/Table_CSV_Writer.md) — *Table Csv Writer*<br>
        |   -> [Table_CSV_check](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/text_table/Table_CSV_check.md) — *Table Csv Check*<br>
        |   -> [table_editing_inplace_mixin](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/text_table/table_editing_inplace_mixin.md) — *Table Editing Inplace Mixin*<br>
        |   -> [table_editing_manager](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/text_table/table_editing.md) — *Table Editing Manager*<br>
        |   -> [table_editing_row_ops_mixin](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/text_table/table_editing_row_ops_mixin.md) — *Table Editing Row Ops Mixin*<br>
        |   -> [table_editing_sort_mixin](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/text_table/table_editing_sort_mixin.md) — *Table Editing Sort Mixin*<br>
        |   -> [table_editing_undo_mixin](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/text_table/table_editing_undo_mixin.md) — *Table Editing Undo Mixin*<br>
        |   -> [text_table](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/text_table/text_table.md) — *Text Table*<br>
     ├----> **text_value_box/**<br>
        |   -> [text_value_box](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/text_value_box/text_value_box.md) — *Text Value Box*<br>
     ├----> **text_value_with_units/**<br>
        |   -> [text_value_with_units](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/text_value_with_units/text_value_with_units.md) — *Text Value With Units*<br>
     ├----> **text_web_link/**<br>
        |   -> [text_web_link](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/text_web_link/text_web_link.md) — *Text Web Link*<br>
     ├----> [builder](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/builder/builder.md) — *Builder*<br>
├-----**exporters/**<br>
     ├----> [utils_csv_writer](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/exporters/utils_csv_writer.md) — *Utils Csv Writer*<br>
     ├----> [worker_file_csv_export](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/exporters/file_csv_export.md) — *Worker File Csv Export*<br>
├-----**handlers/**<br>
     ├----> [json_validator](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/handlers/json_validator.md) — *Json Validator*<br>
     ├----> [widget_event_binder](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/handlers/widget_event_binder.md) — *Widget Event Binder*<br>
├-----**icons/**<br>
     ├----> [make_icon](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/icons/make_icon.md) — *Make Icon*<br>
├-----**importers/**<br>
     ├----> **formats/**<br>
        |   -> [worker_importer_from_csv_unknown](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/importers/formats/from_csv_unknown.md) — *Worker Importer From Csv Unknown*<br>
        |   -> [worker_importer_from_ias_html](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/importers/formats/from_ias_html.md) — *Worker Importer From Ias Html*<br>
        |   -> [worker_importer_from_shure_wwb_shw](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/importers/formats/from_shure_wwb_shw.md) — *Worker Importer From Shure Wwb Shw*<br>
        |   -> [worker_importer_from_shure_wwb_zip](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/importers/formats/from_shure_wwb_zip.md) — *Worker Importer From Shure Wwb Zip*<br>
        |   -> [worker_importer_from_soundbase_pdf_v1](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/importers/formats/from_soundbase_pdf_v1.md) — *Worker Importer From Soundbase Pdf V1*<br>
        |   -> [worker_importer_from_soundbase_pdf_v2](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/importers/formats/from_soundbase_pdf_v2.md) — *Worker Importer From Soundbase Pdf V2*<br>
     ├----> [worker_importer_appender](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/importers/appender.md) — *Worker Importer Appender*<br>
     ├----> [worker_importer_editor](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/importers/editor.md) — *Worker Importer Editor*<br>
     ├----> [worker_importer_loader](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/importers/loader.md) — *Worker Importer Loader*<br>
     ├----> [worker_importer_saver](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/importers/saver.md) — *Worker Importer Saver*<br>
     ├----> [worker_marker_csv_to_json_mqtt](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/importers/marker_csv_to_json_mqtt.md) — *Worker Marker Csv To Json Mqtt*<br>
     ├----> [worker_marker_file_import_converter](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/importers/marker_file_import_converter.md) — *Worker Marker File Import Converter*<br>
├-----**initialization/**<br>
     ├----> [application_initializer](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/initialization/application_initializer.md) — *Application Initializer*<br>
     ├----> [debug_cleaner](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/initialization/debug_cleaner.md) — *Debug Cleaner*<br>
     ├----> [path_initializer](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/initialization/path_initializer.md) — *Path Initializer*<br>
     ├----> [worker_project_paths](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/initialization/project_paths.md) — *Worker Project Paths*<br>
├-----**logger/**<br>
     ├----> [logger](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/logger/logger.md) — *Logger*<br>
├-----**logic/**<br>
     ├----> [state_mirror_engine](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/logic/state_mirror_engine.md) — *State Mirror Engine*<br>
├-----**markers/**<br>
     ├----> [XXXX worker_marker_peak_re_publisher](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/markers/XXXX%20worker_marker_peak_re_publisher.md) — *Xxxx Worker Marker Peak Re Publisher*<br>
     ├----> [worker_marker_logic](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/markers/marker_logic.md) — *Worker Marker Logic*<br>
├-----**monitoring/**<br>
     ├----> [fleet_status_monitor](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/monitoring/fleet_status_monitor.md) — *Fleet Status Monitor*<br>
├-----**presets/**<br>
     ├----> [XXX worker_preset_pusher](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/presets/XXX%20worker_preset_pusher.md) — *Xxx Worker Preset Pusher*<br>
     ├----> [XXXworker_preset_from_device](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/presets/preset_from_device.md) — *Xxxworker Preset From Device*<br>
├-----**splash_screen/**<br>
     ├----> [lyrics_data](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/splash_screen/lyrics.md) — *Lyrics Data*<br>
     ├----> [makegif](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/splash_screen/makegif.md) — *Makegif*<br>
     ├----> [splash_screen](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/splash_screen/splash_screen.md) — *Splash Screen*<br>
├-----**styling/**<br>
     ├----> [style](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/styling/style.md) — *Style*<br>
     ├----> [theme_applier](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/styling/theme_applier.md) — *Theme Applier*<br>
├-----**watchdog/**<br>
     ├----> [watchdog](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/watchdog/watchdog.md) — *Watchdog*<br>
├-----**wysiwyg_editor/**<br>
     ├----> **core/**<br>
        |   -> [event_bus](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/core/event_bus.md) — *Event Bus*<br>
        |   -> [file_io_handler](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/core/file_io_handler.md) — *File Io Handler*<br>
        |   -> [state_manager](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/core/state.md) — *State Manager*<br>
     ├----> **grab_bag/**<br>
        |   -> [grab_bag_loader](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/grab_bag/grab_bag_loader.md) — *Grab Bag Loader*<br>
        |   -> [grab_bag_view](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/grab_bag/grab_bag_view.md) — *Grab Bag View*<br>
     ├----> **workspaces/**<br>
        |   -> **layout_overlays/**<br>
             ├------->[alignment](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/workspaces/layout_overlays/alignment.md) — *Alignment*<br>
             ├------->[blocks](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/workspaces/layout_overlays/blocks.md) — *Blocks*<br>
             ├------->[colors](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/workspaces/layout_overlays/colors.md) — *Colors*<br>
             ├------->[columns](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/workspaces/layout_overlays/columns.md) — *Columns*<br>
             ├------->[selection](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/workspaces/layout_overlays/selection.md) — *Selection*<br>
             ├------->[sizing](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/workspaces/layout_overlays/sizing.md) — *Sizing*<br>
             ├------->[sticky](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/workspaces/layout_overlays/sticky.md) — *Sticky*<br>
             ├------->[structure](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/workspaces/layout_overlays/structure.md) — *Structure*<br>
        |   -> [element_properties](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/workspaces/element_properties.md) — *Element Properties*<br>
        |   -> [interactive_layout](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/workspaces/interactive_layout.md) — *Interactive Layout*<br>
        |   -> [json_editor](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/workspaces/json_editor.md) — *Json Editor*<br>
     ├----> [run_builder](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/run.md) — *Run Builder*<br>
     ├----> [wysiwyg_editor](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/wysiwyg_editor/wysiwyg_editor.md) — *Wysiwyg Editor*<br>
    ├----> [Worker_Launcher](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/workers/Launcher.md) — *Worker Launcher*<br>

---
*Last Updated: 2026-03-13 | Generated by OPEN-AIR Documentation Engine*
