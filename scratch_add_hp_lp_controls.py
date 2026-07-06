import json
import collections

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'r') as f:
    data = json.load(f)

band_controls = data['Zoo_Metering_EQ']['blocks']['Parametric_EQ_Demo']['fields']['Band_Controls']
band_controls['layout_columns'] = 7

old_fields = band_controls['fields']
new_fields = {}

# LoCut block
locut_block = {
    "type": "OcaBlock",
    "layout_columns": 1,
    "description": { "En": "LoCut" },
    "fields": {
        "Freq_Knob": {
            "type": "_Knob",
            "label": { "En": "Freq" },
            "domain": {
                "primary": { "min": 20, "max": 400, "value_default": 20 }
            },
            "cosmetics": {
                "visualization": "wbs-elma",
                "colors": { "primary": "#546E7A", "cap": "#BDBDBD", "tick": "#aaaaaa" },
                "styling": { "fill_color": "#546E7A", "cap_color": "#BDBDBD", "outline_color": "#000", "outline_thickness": 1 },
                "flutes": 18,
                "cap": { "show": True, "color": "#BDBDBD" },
                "pointer_tip": { "show": True, "color": "#546E7A", "length": 0.2 },
                "line": { "color": "#000" },
                "scale": { "show": True, "style": "numeric", "count": 5, "length": 8, "thickness": 1 }
            },
            "layout": { "width": 120, "height": 120 },
            "topic": "OpenAir/Gui/EQ_Params/LoCut/Freq",
            "logarithmic": True
        },
        "Spacer_1": {
            "type": "_Label",
            "label": { "En": "" },
            "layout": { "width": "100%", "height": 30 }
        },
        "Q_Knob": {
            "type": "_Knob",
            "label": { "En": "Q" },
            "domain": {
                "primary": { "min": 0.1, "max": 10, "value_default": 0.7 }
            },
            "cosmetics": {
                "visualization": "wbs-elma",
                "colors": { "primary": "#546E7A", "cap": "#BDBDBD", "tick": "#aaaaaa" },
                "styling": { "fill_color": "#546E7A", "cap_color": "#BDBDBD", "outline_color": "#000", "outline_thickness": 1 },
                "flutes": 18,
                "cap": { "show": True, "color": "#BDBDBD" },
                "pointer_tip": { "show": True, "color": "#546E7A", "length": 0.2 },
                "line": { "color": "#000" },
                "scale": { "show": True, "style": "numeric", "count": 5, "length": 8, "thickness": 1 }
            },
            "layout": { "width": 120, "height": 120 },
            "topic": "OpenAir/Gui/EQ_Params/LoCut/Q"
        }
    }
}

new_fields['Band_LoCut'] = locut_block

# Copy old bands
for k, v in old_fields.items():
    if k.startswith("Band_") and k not in ['Band_LoCut', 'Band_HiCut']:
        new_fields[k] = v

# HiCut block
hicut_block = {
    "type": "OcaBlock",
    "layout_columns": 1,
    "description": { "En": "HiCut" },
    "fields": {
        "Freq_Knob": {
            "type": "_Knob",
            "label": { "En": "Freq" },
            "domain": {
                "primary": { "min": 1000, "max": 20000, "value_default": 20000 }
            },
            "cosmetics": {
                "visualization": "wbs-elma",
                "colors": { "primary": "#546E7A", "cap": "#BDBDBD", "tick": "#aaaaaa" },
                "styling": { "fill_color": "#546E7A", "cap_color": "#BDBDBD", "outline_color": "#000", "outline_thickness": 1 },
                "flutes": 18,
                "cap": { "show": True, "color": "#BDBDBD" },
                "pointer_tip": { "show": True, "color": "#546E7A", "length": 0.2 },
                "line": { "color": "#000" },
                "scale": { "show": True, "style": "numeric", "count": 5, "length": 8, "thickness": 1 }
            },
            "layout": { "width": 120, "height": 120 },
            "topic": "OpenAir/Gui/EQ_Params/HiCut/Freq",
            "logarithmic": True
        },
        "Spacer_1": {
            "type": "_Label",
            "label": { "En": "" },
            "layout": { "width": "100%", "height": 30 }
        },
        "Q_Knob": {
            "type": "_Knob",
            "label": { "En": "Q" },
            "domain": {
                "primary": { "min": 0.1, "max": 10, "value_default": 0.7 }
            },
            "cosmetics": {
                "visualization": "wbs-elma",
                "colors": { "primary": "#546E7A", "cap": "#BDBDBD", "tick": "#aaaaaa" },
                "styling": { "fill_color": "#546E7A", "cap_color": "#BDBDBD", "outline_color": "#000", "outline_thickness": 1 },
                "flutes": 18,
                "cap": { "show": True, "color": "#BDBDBD" },
                "pointer_tip": { "show": True, "color": "#546E7A", "length": 0.2 },
                "line": { "color": "#000" },
                "scale": { "show": True, "style": "numeric", "count": 5, "length": 8, "thickness": 1 }
            },
            "layout": { "width": 120, "height": 120 },
            "topic": "OpenAir/Gui/EQ_Params/HiCut/Q"
        }
    }
}

new_fields['Band_HiCut'] = hicut_block

# Copy spacers if any
for k, v in old_fields.items():
    if k.startswith("Spacer_"):
        new_fields[k] = v

band_controls['fields'] = new_fields

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Added HP and LP controls to EQ.json!")
