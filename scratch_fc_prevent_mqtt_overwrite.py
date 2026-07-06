import re

with open('FrontEnd/frameLayout/FieldComponent.jsx', 'r') as f:
    code = f.read()

old_merge = """        // Deep merge sub-configs to avoid MQTT state wiping out tree.json configs
        knob_config: { ...(rawNode.knob_config || {}), ...(_v.knob_config || {}) },
        fader_config: { ...(rawNode.fader_config || {}), ...(_v.fader_config || {}) },
        cosmetics: { ...(rawNode.cosmetics || {}), ...(_v.cosmetics || {}) },"""

new_merge = """        // CRITICAL: NEVER allow MQTT state (_v) to overwrite aesthetic configs from tree.json!
        // The retained MQTT state might contain old UI configs that wipe out colors.
        knob_config: rawNode.knob_config,
        fader_config: rawNode.fader_config,
        cosmetics: rawNode.cosmetics,"""

code = code.replace(old_merge, new_merge)

with open('FrontEnd/frameLayout/FieldComponent.jsx', 'w') as f:
    f.write(code)

