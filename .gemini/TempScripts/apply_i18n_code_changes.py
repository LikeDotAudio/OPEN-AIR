import os
import re
import pathlib

FILES_TO_PROCESS = [
    "oaGuiElements/Core/utils/knob/knob.py",
    "oaGuiElements/Core/utils/checkbox/checkbox.py",
    "oaGuiElements/Core/utils/knob_rotary_selector/knob_rotary_selector.py",
    "oaGuiElements/Core/images/images_image_display/images_image_display.py",
    "oaGuiElements/Core/images/images_animation_display/images_animation_display.py",
    "oaGuiElements/Core/images/images_progress_bar/images_progress_bar.py",
    "oaGuiElements/Core/metering/meter_bar/meter_bar.py",
    "oaGuiElements/Core/graphing/radar/radar.py",
    "oaGuiElements/Core/Knobs/knob/knob.py",
    "oaGuiElements/Core/Knobs/knob_rotary_selector/knob_rotary_selector.py",
    "oaGuiElements/Core/faders/fader_input/fader_input.py",
    "oaGuiElements/Core/faders/fader_ganged_controlled_array/fader_ganged_controlled_array.py",
    "oaGuiElements/Core/text/text_value_box/text_value_box.py",
    "oaGuiElements/Core/text/text_value_with_units/text_value_with_units.py",
    "oaGuiElements/Core/text/text_web_link/text_web_link.py",
    "oaGuiElements/Core/input/input_directional_buttons/input_directional_buttons.py",
    "oaGuiElements/Core/input/input_inc_dec_buttons/input_inc_dec_buttons.py",
    "oaGuiElements/Core/input/checkbox/checkbox.py",
    "oaGuiElements/Core/buttons/button_wink_toggler/button_wink_toggler.py",
    "oaGuiElements/Core/buttons/button_trapezoid_toggler/button_trapezoid_toggler.py",
    "oaGuiElements/Core/buttons/button_trapezoid/button_trapezoid.py",
    "oaGuiElements/Core/buttons/button_toggle/button_toggle.py",
    "oaGuiElements/Core/buttons/button_toggler/button_toggler.py",
    "oaGuiElements/Core/buttons/button_wink/button_wink.py"
]

def process_file(filepath):
    if not os.path.exists(filepath):
        print(f"Skipping missing file: {filepath}")
        return

    with open(filepath, 'r') as f:
        content = f.read()

    # 1. Add import if not present
    import_stmt = "from oaGuiFramework.Methods.i18n_utils import get_text"
    if "from oaGuiFramework.Methods.i18n_utils import get_text" not in content:
        # Find a good place for import - usually after other oaGui imports or at the top
        content = re.sub(r"(from oaGuiManager.*?\n)", r"\1" + import_stmt + "\n", content, count=1)
        if import_stmt not in content:
            # Fallback to after first line
            content = re.sub(r"(.*?)\n", r"\1\n" + import_stmt + "\n", content, count=1)

    # 2. Replace label assignments
    # Replace config_data.get("label_active") or config_data.get("label", "Fallback")
    content = re.sub(
        r"config_data\.get\([\"\'](label_active)['\"]\)\s*or\s*config_data\.get\([\"\'](label)['\"],\s*([\"\'].*?[\"\'])\)",
        r"get_text(config_data.get('\1')) or get_text(config_data.get('\2'), \3)",
        content
    )
    
    # Replace config_data.get("label_active") or config_data.get("label", "")
    content = re.sub(
        r"config_data\.get\([\"\'](label_active)['\"]\)\s*or\s*config_data\.get\([\"\'](label)['\"]\)",
        r"get_text(config_data.get('\1')) or get_text(config_data.get('\2'))",
        content
    )

    # Replace simple config_data.get("label_active")
    content = re.sub(
        r"config_data\.get\([\"\'](label_active)['\"]\)",
        r"get_text(config_data.get('\1'))",
        content
    )

    # Replace simple config_data.get("label")
    content = re.sub(
        r"config_data\.get\([\"\'](label)['\"]\)",
        r"get_text(config_data.get('\1'))",
        content
    )
    
    # Replace simple config_data.get("label", "Default")
    content = re.sub(
        r"config_data\.get\([\"\'](label)['\"],\s*([\"\'].*?[\"\'])\)",
        r"get_text(config_data.get('\1'), \2)",
        content
    )

    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Processed: {filepath}")

if __name__ == "__main__":
    for f in FILES_TO_PROCESS:
        process_file(f)
