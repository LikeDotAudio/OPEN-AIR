import json
import os

TARGET_DIR = "/home/anthony/Documents/OPEN-AIR/oaGui/Assets/right_50/bottom_90/9_Zoo/4_images/4_BG"

STRATEGY = {
    "eggshell": {"base_material": {"color": "#f0ead6", "texture_type": "flat"}, "paint_layer": {"color": "#ffffff", "opacity": 0.1}},
    "heavy_rust": {"base_material": {"color": "#2a2a2a", "texture_type": "hammered"}, "rust": {"enabled": True, "intensity": 0.8}},
    "dusty_attic": {"base_material": {"color": "#444444", "texture_type": "wrinkle"}, "dust": {"enabled": True, "intensity": 0.7}},
    "dusty_antique": {"base_material": {"color": "#444444", "texture_type": "wrinkle"}, "dust": {"enabled": True, "intensity": 0.7}},
    "oily_shop": {"base_material": {"color": "#1a1a1a", "texture_type": "brushed"}, "grime": {"stain_count": 15, "opacity": 0.5}},
    "oily_tactical": {"base_material": {"color": "#1a1a1a", "texture_type": "brushed"}, "grime": {"stain_count": 15, "opacity": 0.5}},
    "subtle_wear": {"base_material": {"color": "#333333", "texture_type": "crosshatch"}, "panel_scratches": {"count": 10, "intensity": 0.3, "reveals_substrate": True}},
    "distressed": {"base_material": {"color": "#333333", "texture_type": "crosshatch"}, "panel_scratches": {"count": 10, "intensity": 0.3, "reveals_substrate": True}},
    "military_drab": {"base_material": {"color": "#4b5320", "texture_type": "enamel"}, "paint_layer": {"color": "#4b5320", "opacity": 0.9}, "edge_wear": {"enabled": True, "scratch_intensity": 0.6}},
    "hammertone_silver": {"base_material": {"color": "#c0c0c0", "texture_type": "hammered"}, "paint_layer": {"opacity": 0.3}},
    "hammertone_green": {"base_material": {"color": "#2e8b57", "texture_type": "hammered"}, "paint_layer": {"opacity": 0.3}},
    "black_wrinkle": {"base_material": {"color": "#111111", "texture_type": "wrinkle"}},
    "black_anodized": {"base_material": {"color": "#1a1a1a", "texture_type": "brushed"}},
    "black_gloss_enamel": {"base_material": {"color": "#050505", "texture_type": "flat"}, "paint_layer": {"opacity": 0.8, "gradient_intensity": 0.4}},
    "folded_metal": {"base_material": {"color": "#555555"}, "metal_fold": {"enabled": True, "width_px": 30}},
    "bakelite": {"base_material": {"color": "#4b2c20", "texture_type": "flat"}, "studio_haze": {"enabled": True, "intensity": 0.2}},
    "neve_grey": {"base_material": {"color": "#8b8d8e", "texture_type": "flat"}, "screws": {"enabled": True, "locations": ["top", "bottom"]}},
    "emi_cream": {"base_material": {"color": "#f5f5dc", "texture_type": "flat"}},
    "api_black": {"base_material": {"color": "#0a0a0a", "texture_type": "brushed"}},
    "rack_rash": {"base_material": {"color": "#333333"}, "edge_wear": {"enabled": True, "scratch_intensity": 0.8}},
    "cold_rolled_steel": {"base_material": {"color": "#777b7e", "texture_type": "brushed"}},
    "faded_silk_screen": {"base_material": {"color": "#2b2b2b"}, "paint_layer": {"color": "#ffffff", "opacity": 0.05}},
    "master_studio": {"base_material": {"color": "#1e1e1e"}, "studio_haze": {"enabled": True, "intensity": 0.1}, "screws": {"enabled": True}},
}

def get_background(path):
    path_lower = path.lower()
    # Try exact match first
    for key, value in STRATEGY.items():
        if key in path_lower:
            return value
    # Some fallbacks for specific names found earlier
    if "black_hammertone" in path_lower:
        return STRATEGY["black_wrinkle"] # fallback
    if "black_carbon" in path_lower or "stealth_black" in path_lower:
        return STRATEGY["api_black"] # fallback
    if "navy_night" in path_lower:
        return STRATEGY["master_studio"] # fallback
    if "sci_fi" in path_lower or "apocalypse" in path_lower:
        return STRATEGY["heavy_rust"] # fallback

    return STRATEGY["master_studio"] # default fallback

def update_json(file_path):
    print(f"Processing: {file_path}")
    try:
        with open(file_path) as f:
            data = json.load(f)

        bg_params = get_background(file_path)

        updated = False
        # Iterate over top-level keys
        for key in list(data.keys()):
            # If the value is an object and looks like it could be an OcaBin or the user wants it to be
            if isinstance(data[key], dict):
                obj = data[key]
                obj["type"] = "OcaBin"
                obj["geometry"] = {"anchor": "NSEW"}
                obj["behavior"] = {
                    "overflow": "auto",
                    "fluid_ew": True
                }
                obj["background"] = bg_params
                updated = True

        if updated:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Updated: {file_path}")
        else:
            print(f"No objects to update in: {file_path}")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    for root, dirs, files in os.walk(TARGET_DIR):
        for file in files:
            if file.endswith(".json"):
                full_path = os.path.join(root, file)
                update_json(full_path)

if __name__ == "__main__":
    main()
