# ==========================================
# Header: migrate_gui.py
# Purpose: migrate_gui.py implementation.
# Description: Logic and implementation for migrate_gui.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

import os
import glob
import re

FRONTEND_DIR = "/home/anthony/Documents/OPEN-AIR/frontEnd"
GUI_FRAMES_DIR = "/home/anthony/Documents/OPEN-AIR/Gui_Frames/Window_2"

# Components to migrate (from find output)
components_py = [
    "right_50/top_100/9_Zoo/4_graphing/1_XY_Graphs/2_Graphing_2/Graphing_Cont.py",
    "right_50/top_100/9_Zoo/4_graphing/1_XY_Graphs/2_Graphing_3/Graphing_Cont_1.py",
    "right_50/top_100/9_Zoo/1_buttons/2_Trapezoid/6_Media_Buttons/Media_Buttons.py",
    "right_50/top_100/9_Zoo/5_Indicators/3_Metering/Graphing_Elements.py",
    "left_50/top_100/3_Commands/22_Yak_Monitor/yak_monitor.py",
    "left_50/top_100/3_Commands/1_Router/2_Matrix/protocol_matrix.py", # already deleted but let's handle JSON
    "left_50/top_100/3_Commands/1_Router/1_Router/command_router.py",
    "left_50/top_100/4_Protocals/2138_SMPTE_2138/smpte2138_monitor.py",
    "left_50/top_100/4_Protocals/66_NMOS/01_Websockets/nmos_websockets.py",
    "left_50/top_100/4_Protocals/66_NMOS/02_Connection/nmos_connection.py",
    "left_50/top_100/4_Protocals/66_NMOS/00_Commands/nmos_commands.py",
    "left_50/top_100/4_Protocals/50_MIDI/2_Output/midi_output.py",
    "left_50/top_100/4_Protocals/50_MIDI/1_Input/Midi_In.py",
    "left_50/top_100/4_Protocals/67_SAP/SAP_GUI_Pointer.py",
    "left_50/top_100/4_Protocals/70_AES70/AES70.py",
    "left_50/top_100/4_Protocals/99_EMBER/Ember.py",
    "left_50/top_100/4_Protocals/11_SNMP/00_Log/snmp_log.py",
    "left_50/top_100/4_Protocals/11_SNMP/3_MIB/snmp_mib.py",
    "left_50/top_100/4_Protocals/11_SNMP/0_Status/snmp_status.py",
    "left_50/top_100/4_Protocals/11_SNMP/5_Verify_MIB/snmp_verify_mib.py",
    "left_50/top_100/4_Protocals/11_SNMP/4_Verify_OID/snmp_verify.py",
    "left_50/top_100/4_Protocals/67_MDNS/MDNS_GUI_Pointer.py",
    "left_50/top_100/4_Protocals/44_REST/gui_REST.py",
    "left_50/top_100/4_Protocals/67_DNSSD/DNSSD_GUI_Pointer.py",
    "left_50/top_100/4_Protocals/55_OSC/gui_OSC.py"
]

react_imports = []

for py_file in components_py:
    abs_py_path = os.path.join(GUI_FRAMES_DIR, py_file)
    dir_name = os.path.dirname(abs_py_path)
    base_name = os.path.basename(py_file).replace(".py", "")
    
    # Capitalize component name (e.g. protocol_matrix -> ProtocolMatrix)
    comp_name = "".join([word.capitalize() for word in base_name.split("_")])
    if "GuiPointer" in comp_name:
        comp_name = comp_name.replace("GuiPointer", "")
    
    comp_type = f"_{comp_name}"
    
    # 1. Delete .py and .pyc
    if os.path.exists(abs_py_path):
        os.remove(abs_py_path)
        print(f"Deleted {abs_py_path}")
    
    pyc_pattern = os.path.join(dir_name, "__pycache__", f"{base_name}*.pyc")
    for pyc in glob.glob(pyc_pattern):
        os.remove(pyc)
        print(f"Deleted {pyc}")
        
    # 2. Create .json file
    json_path = os.path.join(dir_name, f"{base_name}.json")
    json_content = f"""{{
  "Migrated_{comp_name}": {{
    "type": "OcaBin",
    "id": "migrated.{base_name}",
    "geometry": {{ "anchor": "NSEW" }},
    "blocks": {{
      "MainBlock": {{
        "type": "OcaBlock",
        "label": {{
          "active": {{
            "text": {{ "En": "{comp_name}" }},
            "text_size": 14,
            "text_color": "#ffffff"
          }}
        }},
        "fields": {{
          "component": {{
            "type": "{comp_type}",
            "layout": {{ "width": 400, "height": 300 }}
          }}
        }}
      }}
    }}
  }}
}}"""
    with open(json_path, "w") as f:
        f.write(json_content)
    print(f"Created {json_path}")
    
    # 3. Create React Component
    react_dir = os.path.join(FRONTEND_DIR, "libControl", "special", comp_name)
    os.makedirs(react_dir, exist_ok=True)
    jsx_path = os.path.join(react_dir, f"{comp_name}.jsx")
    
    jsx_content = f"""// React implementation for {comp_name}
// Replaces {py_file}

window.{comp_type} = (props) => {{
    const [lang] = window.useMqttLang();
    
    return (
        <div style={{ padding: '20px', color: '#fff', backgroundColor: '#222', borderRadius: '5px', height: '100%', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ color: '#f4902c', marginTop: 0 }}>{comp_name}</h3>
            <p>This component has been migrated to React.</p>
            <div style={{ flexGrow: 1, border: '1px dashed #555', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888' }}>
                UI implementation goes here
            </div>
        </div>
    );
}};

// Register with WYSIWYG Editor
if (!window.OA_COMPONENTS) window.OA_COMPONENTS = {{}};
window.OA_COMPONENTS['{comp_type}'] = window.{comp_type};
"""
    if not os.path.exists(jsx_path):
        with open(jsx_path, "w") as f:
            f.write(jsx_content)
        print(f"Created {jsx_path}")
    
    # 4. Record React import
    rel_jsx = f"../../libControl/special/{comp_name}/{comp_name}.jsx?v=1"
    react_imports.append(f'    <script type="text/babel" src="{rel_jsx}"></script>')

# 5. Output script tags to inject into Launch/index.html
with open("react_imports.txt", "w") as f:
    f.write("\\n".join(react_imports))
print("Done. Saved react imports to react_imports.txt")
