# ==========================================
# Header: create_zoo.py
# Purpose: create_zoo.py implementation.
# Description: Logic and implementation for create_zoo.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

import os
import json

base_dir = "/home/anthony/Documents/OPEN-AIR/FrontEnd/Gui_Frames/Window_2/right_50/top_100/9_Zoo"

files_to_create = {
    "1_buttons/4_HighVis/HighVis.json": {
        "Zoo_buttons_HighVis": {
            "type": "OcaBin",
            "behavior": { "overflow_ns": "auto", "overflow_ew": "auto", "fluid_ew": True },
            "blocks": {
                "HighVis_Buttons_Demo": {
                    "type": "OcaBlock",
                    "description": { "En": "High Visibility Buttons" },
                    "layout_columns": 2,
                    "fields": {
                        "btn_1": {
                            "type": "_HighVisButton",
                            "geometry": { "width": 80, "height": 45, "corner_radius": 6 },
                            "cosmetics": { "shape": "rect" },
                            "style": {
                                "active": { "text_color": "#ffffff", "rim_color": "#FAD02C", "inner_bg_color": "#222", "glow_intensity": 8 },
                                "inactive": { "text_color": "#aaaaaa", "rim_color": "#555", "inner_bg_color": "#111", "glow_intensity": 0 }
                            },
                            "interaction": {
                                "options": {
                                    "ON": { "label": { "active": { "text": "SOLO" } } },
                                    "OFF": { "label": { "inactive": { "text": "SOLO" } } }
                                }
                            }
                        },
                        "btn_2": {
                            "type": "_HighVisButton",
                            "geometry": { "width": 80, "height": 45, "corner_radius": 6 },
                            "cosmetics": { "shape": "rect" },
                            "style": {
                                "active": { "text_color": "#ffffff", "rim_color": "#4A6EAA", "inner_bg_color": "#222", "glow_intensity": 6 },
                                "inactive": { "text_color": "#aaaaaa", "rim_color": "#555", "inner_bg_color": "#111", "glow_intensity": 0 }
                            },
                            "interaction": {
                                "options": {
                                    "ON": { "label": { "active": { "text": "MUTE" } } },
                                    "OFF": { "label": { "inactive": { "text": "MUTE" } } }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "2_Knobs/3_Crafty/Crafty.json": {
        "Zoo_Knobs_Crafty": {
            "type": "OcaBin",
            "behavior": { "overflow_ns": "auto", "overflow_ew": "auto", "fluid_ew": True },
            "blocks": {
                "Crafty_Knobs_Demo": {
                    "type": "OcaBlock",
                    "description": { "En": "Crafty Knobs" },
                    "layout_columns": 3,
                    "fields": {
                        "knob_1": {
                            "type": "_SmartKnob",
                            "label": { "En": "Spoked", "show_label": True },
                            "geometry": { "width": 100, "height": 100 },
                            "cosmetics": { "visualization": "crafty", "variant": "spoked", "colors": { "primary": "#ffffff", "secondary": "#5a3d7c" } }
                        },
                        "knob_2": {
                            "type": "_SmartKnob",
                            "label": { "En": "Metallic", "show_label": True },
                            "geometry": { "width": 100, "height": 100 },
                            "cosmetics": { "visualization": "crafty", "variant": "metallic", "colors": { "primary": "#222", "secondary": "#444" } }
                        },
                        "knob_3": {
                            "type": "_SmartKnob",
                            "label": { "En": "LED Ring", "show_label": True },
                            "geometry": { "width": 100, "height": 100 },
                            "cosmetics": { "visualization": "crafty", "variant": "led_ring", "colors": { "primary": "#88e077", "secondary": "#444" } }
                        }
                    }
                }
            }
        }
    },
    "4_graphing/1_AudioDynamics/AudioDynamics.json": {
        "Zoo_graphing_AudioDynamics": {
            "type": "OcaBin",
            "behavior": { "overflow_ns": "auto", "overflow_ew": "auto", "fluid_ew": True },
            "blocks": {
                "AudioDynamics_Demo": {
                    "type": "OcaBlock",
                    "description": { "En": "Audio Dynamics Graph" },
                    "fields": {
                        "graph": {
                            "type": "_AudioDynamics",
                            "identity": { "label": "Stagebox Mic 53" },
                            "geometry": { "width": 400, "height": 400 },
                            "datasets": [
                                { "id": "curve", "initial_csv_data": "x,y\n-90,-90\n-40,-40\n-20,-20\n0,-12" }
                            ]
                        }
                    }
                }
            }
        }
    },
    "4_graphing/2_Equalization/Equalization.json": {
        "Zoo_graphing_Equalization": {
            "type": "OcaBin",
            "behavior": { "overflow_ns": "auto", "overflow_ew": "auto", "fluid_ew": True },
            "blocks": {
                "Equalization_Demo": {
                    "type": "OcaBlock",
                    "description": { "En": "Equalization Graph" },
                    "fields": {
                        "graph": {
                            "type": "_Equalization",
                            "identity": { "label": "Stagebox Mic 53" },
                            "geometry": { "width": 500, "height": 350 },
                            "datasets": [
                                { "id": "curve", "initial_csv_data": "x,y\n20,-32\n50,-10\n100,3\n150,2\n200,0\n300,-8\n500,-1\n1000,2\n2000,1\n5000,4\n10000,1\n20000,0" }
                            ]
                        }
                    }
                }
            }
        }
    }
}

for rel_path, data in files_to_create.items():
    full_path = os.path.join(base_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=2)

print("Zoo files generated.")
