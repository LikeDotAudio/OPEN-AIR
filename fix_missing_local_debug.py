import os
import re

def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # Check if LOCAL_DEBUG = True already exists
    content = "".join(lines)
    if re.search(r'\bLOCAL_DEBUG\s*=', content):
        return False
    if re.search(r'import\s+.*LOCAL_DEBUG', content):
        return False
    
    # Find insertion point
    insertion_index = -1
    
    # Rule 2: If there is a section marked '# --- Standard Debug Logging Setup ---', place it there.
    for i, line in enumerate(lines):
        if '# --- Standard Debug Logging Setup ---' in line:
            insertion_index = i + 1
            break
    
    # Rule 1: Otherwise, after existing imports and before any class/function definitions.
    if insertion_index == -1:
        last_import_index = -1
        first_def_index = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                last_import_index = i
            elif (stripped.startswith('def ') or stripped.startswith('class ')) and first_def_index == -1:
                first_def_index = i
        
        if last_import_index != -1:
            insertion_index = last_import_index + 1
        elif first_def_index != -1:
            insertion_index = first_def_index
        else:
            # Fallback to after comments at the top
            for i, line in enumerate(lines):
                if not line.strip().startswith('#') and line.strip():
                    insertion_index = i
                    break
            if insertion_index == -1:
                insertion_index = len(lines)
    
    # Avoid inserting in middle of docstrings or other stuff if possible.
    # If we are at first_def_index, let's make sure we have a newline.
    
    new_line = "LOCAL_DEBUG = True\n"
    # Ensure it's not already there (double check)
    if any("LOCAL_DEBUG =" in line for line in lines):
        return False

    lines.insert(insertion_index, new_line)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    return True

# Use the list from previous step
files_to_fix = [
"./oaOchestration/Methods/widget_event_binder.py",
"./oaOchestration/Methods/debug_cleaner.py",
"./oaStateCache/FileReaders/cache_io_handler.py",
"./oaStateCache/Methods/preset_pusher.py",
"./oaStateCache/Methods/preset_from_device.py",
"./oaFileImportPDF/FileReaders/from_soundbase_pdf_v1.py",
"./oaFileImportPDF/FileReaders/from_soundbase_pdf_v2.py",
"./oaComAES70/Core/aes70.py",
"./oaGuiElements/Core/text/text_gui_dropdown_option/text_gui_dropdown_option.py",
"./oaWatchdog/Managers/fleet_status_monitor.py",
"./oaComVisa/Workers/agent_static_ip_prober.py",
"./oaComVisa/Workers/logic_disconnect_instrument.py",
"./oaComVisa/Workers/logic_connect_instrument.py",
"./oaComVisa/Workers/logic_mqtt_publisher.py",
"./oaComVisa/Workers/agent_usb_enumerator.py",
"./oaComVisa/FileWriters/visa_csv.py",
"./oaComVisa/FileWriters/visa_json.py",
"./oaComVisa/Methods/visa_Search.py",
"./oaComVisa/Methods/visa_list_visa_resources.py",
"./oaComVisa/Methods/visa_reset.py",
"./oaComVisa/Methods/visa_reboot.py",
"./oaGuiBuilder/Core/context_menu.py",
"./oaComMidi/Interface/midi_dashboard.py",
"./oaThreadManager/Workers/Launcher.py",
"./oaInstallation/Core/TaskBarIcon.py",
"./oaInstallation/Managers/DependencyManager.py",
"./oaFileImportShow/FileReaders/saver.py",
"./oaFileImportShow/FileReaders/appender.py",
"./oaFileImportShow/Methods/marker_csv_to_json_mqtt.py",
"./oaFileExportCSV/FileWriters/file_csv_export.py",
"./oaFileExportCSV/Methods/utils_csv_writer.py",
"./oaGuiDefinitions/Assets/right_50/bottom_90/2138_SMPTE_2138/smpte2138_monitor.py",
"./oaGuiDefinitions/Assets/right_50/bottom_90/9_Zoo/4_graphing/1_XY_Graphs/2_Graphing_2/Graphing_Cont.py",
"./oaGuiDefinitions/Assets/right_50/bottom_90/9_Zoo/4_graphing/1_XY_Graphs/2_Graphing_3/Graphing_Cont_1.py",
"./oaGuiDefinitions/Assets/right_50/bottom_90/9_Zoo/1_buttons/2_Trapezoid/6_Media_Buttons/Media_Buttons.py",
"./oaGuiDefinitions/Assets/right_50/bottom_90/9_Zoo/5_Indicators/3_Metering/Graphing_Elements.py",
"./oaGuiDefinitions/Assets/right_50/bottom_90/11_SNMP/00_Log/snmp_log.py",
"./oaGuiTelemetry/Methods/active_peak_publisher.py",
"./oaGuiTelemetry/Methods/marker_logic.py",
"./oaGuiEditorWYSIWYG/FileReaders/grab_bag_loader.py",
"./oaFileImportCSV/FileReaders/from_csv_unknown.py",
"./oaComMQTT/Workers/mqtt_async_worker.py",
"./oaComMQTT/Managers/mqtt_connection.py",
"./oaComMQTT/Methods/mqtt_flattening.py",
"./oaGuiBuildShell/Workers/async_grid_renderer.py",
"./oaGuiBuildShell/Core/directory.py",
"./oaGuiBuildShell/Core/window.py",
"./oaGuiBuildShell/Core/layout_cache.py",
"./oaComSNMP/Workers/snmp_tester.py",
"./oaTests/Methods/DebugToggler.py"
]

for file_path in files_to_fix:
    if fix_file(file_path):
        print(f"Fixed: {file_path}")
    else:
        print(f"Skipped/Failed: {file_path}")
