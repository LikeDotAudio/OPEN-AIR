# .gemini/TempScripts/fix_path_issue.py
# Author: Gemini CLI
# Version: 20260401.2330.3

import os
from pathlib import Path

FILES = [
    "./oaOchestration/Methods/debug_cleaner.py",
    "./oaComREST/Workers/uvicorn_worker.py",
    "./oaComREST/Methods/port_utils.py",
    "./oaStateCache/Core/cache_recovery_handler.py",
    "./oaFileImportPDF/FileReaders/from_soundbase_pdf_v1.py",
    "./oaFileImportPDF/FileReaders/from_soundbase_pdf_v2.py",
    "./oaConfiguration/Methods/console_encoder.py",
    "./oaConfiguration/Methods/config_validator.py",
    "./oaWatchdog/Managers/watchdog.py",
    "./oaComVisa/Workers/logic_mqtt_listen.py",
    "./oaComVisa/Workers/agent_static_ip_prober.py",
    "./oaComVisa/Workers/logic_mqtt_publisher.py",
    "./oaComVisa/Workers/agent_mdns_zeroconf.py",
    "./oaComVisa/Workers/visa_scanner.py",
    "./oaComVisa/Workers/agent_usb_enumerator.py",
    "./oaComVisa/Core/visa_fleet.py",
    "./oaComVisa/Core/fleet_scan_mixin.py",
    "./oaComVisa/Core/visa_safe_query.py",
    "./oaComVisa/Core/visa_safe_writer.py",
    "./oaComVisa/Managers/discovery_orchestrator.py",
    "./oaComVisa/FileWriters/visa_csv.py",
    "./oaComVisa/Methods/visa_Search.py",
    "./oaComVisa/Methods/network_utils.py",
    "./oaComVisa/Methods/visa_search_results.py",
    "./oaComMidi/Interface/midi_dashboard.py",
    "./oaThreadManager/Core/mqtt_subscriber_mixin.py",
    "./oaInstallation/Core/TaskBarIcon.py",
    "./oaInstallation/Managers/Setup.py",
    "./oaComBroker/Core/open_air_core.py",
    "./oaFileImportShow/FileReaders/editor.py",
    "./openair.py",
    "./oaFileImportHTML/FileReaders/from_ias_html.py",
    "./oaGuiDefinitions/Assets/right_50/bottom_90/2138_SMPTE_2138/smpte2138_monitor.py",
    "./oaGuiDefinitions/Assets/right_50/bottom_90/2_monitors/22_Yak_Monitor/yak_monitor.py",
    "./oaGuiDefinitions/Assets/right_50/bottom_90/2_monitors/1588_PTP_Monitor/ptp_monitor.py",
    "./oaGuiDefinitions/Assets/right_50/bottom_90/11_SNMP/3_MIB/snmp_mib.py",
    "./oaGuiDefinitions/Assets/right_50/bottom_90/4_Splinker/222_Editor/splinker_editor.py",
    "./oaGuiDefinitions/Assets/right_50/bottom_90/44_REST/gui_REST.py",
    "./oaGuiDefinitions/Assets/right_50/bottom_90/55_OSC/gui_OSC.py",
    "./oaGuiDefinitions/Assets/right_50/bottom_90/3_Command_Router/command_router.py",
    "./oaGuiManager/Core/factory/widget_registry.py",
    "./oaGuiSplashScreen/Methods/splash_screen.py",
    "./oaLogging/Managers/log_filter_engine.py",
    "./oaGuiTelemetry/Core/instrument_controller.py",
    "./oaGuiTelemetry/Methods/active_marker_tune_and_collect.py",
    "./oaGuiTelemetry/Methods/active_peak_publisher.py",
    "./oaGuiTelemetry/Methods/marker_repository_watcher.py",
    "./oaGuiEditorWYSIWYG/Core/workspaces/interactive_layout.py",
    "./oaGuiEditorWYSIWYG/Core/workspaces/Core/leaf_editor_factory.py",
    "./oaGuiEditorWYSIWYG/Core/workspaces/tree_refactor.py",
    "./oaGuiEditorWYSIWYG/Core/workspaces/json_editor.py",
    "./oaGuiEditorWYSIWYG/Core/event_bus.py",
    "./oaGuiEditorWYSIWYG/Core/file_io_handler.py",
    "./oaGuiEditorWYSIWYG/Methods/grab_bag/grab_bag_view.py",
    "./oaComMQTT/Workers/broker_monitor.py",
    "./oaComMQTT/Workers/mqtt_async_worker.py",
    "./oaComMQTT/Managers/mqtt_connection.py",
    "./oaComMQTT/Methods/delete_open_air.py",
    "./oaGuiBuildShell/Core/directory.py",
    "./oaComSNMP/Entry.py",
    "./oaTests/Workers/CleanupApps/Clear_JsonLines.py",
    "./oaTests/Workers/CleanupApps/Clear_audits.py",
    "./oaTests/Workers/CleanupApps/Clear_flamegraph.py",
    "./oaTests/Workers/CleanupApps/Clear_reports.py",
    "./oaTests/Workers/CleanupApps/Clear_cache.py",
    "./oaTests/Workers/CleanupApps/ClearMQTT.py",
    "./oaTests/Managers/configIniEditor/manager.py",
    "./oaTests/Methods/FlameGraph/flame_html.py",
    "./oaTests/Methods/FlameGraph/flame_capture.py",
    "./oaTests/Methods/FlameGraph/flame_manager.py",
]

def fix_file(file_path):
    p = Path(file_path)
    if not p.exists(): return

    lines = p.read_text().splitlines()
    
    setup_lines = []
    other_lines = []
    
    in_setup = False
    for line in lines:
        if "Setup Environment" in line or "current_dir =" in line or "project_root =" in line or "sys.path.insert" in line:
            setup_lines.append(line)
            in_setup = True
        elif in_setup and (line.strip() == "" or line.startswith("if")):
            setup_lines.append(line)
        else:
            in_setup = False
            if line.strip() in ["import sys", "import os", "import pathlib"]:
                setup_lines.insert(0, line)
            else:
                other_lines.append(line)

    if not setup_lines: return

    # Cleanup setup_lines (remove duplicates and empty lines at start/end)
    seen = set()
    final_setup = []
    for l in setup_lines:
        if l.strip() and l.strip() not in seen or not l.strip():
            final_setup.append(l)
            if l.strip(): seen.add(l.strip())
            
    final_content = "\n".join(final_setup) + "\n\n" + "\n".join(other_lines)
    p.write_text(final_content)
    print(f"✅ Fixed: {file_path}")

if __name__ == "__main__":
    for f in FILES: fix_file(f)
