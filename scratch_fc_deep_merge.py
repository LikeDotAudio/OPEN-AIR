import re

with open('FrontEnd/frameLayout/FieldComponent.jsx', 'r') as f:
    code = f.read()

old_merge = """    const _d = (rawNode && rawNode.domain) || {};
    const _v = (rawNode && rawNode.value) || {};
    const _numU = (x) => { const n = parseFloat(x); return Number.isNaN(n) ? undefined : n; };
    const node = (rawNode && (rawNode.domain || rawNode.value)) ? {
        ...rawNode, ..._d, ..._v,"""

new_merge = """    const _d = (rawNode && rawNode.domain) || {};
    const _v = (rawNode && rawNode.value) || {};
    const _numU = (x) => { const n = parseFloat(x); return Number.isNaN(n) ? undefined : n; };
    const node = (rawNode && (rawNode.domain || rawNode.value)) ? {
        ...rawNode, ..._d, ..._v,
        // Deep merge sub-configs to avoid MQTT state wiping out tree.json configs
        knob_config: { ...(rawNode.knob_config || {}), ...(_v.knob_config || {}) },
        fader_config: { ...(rawNode.fader_config || {}), ...(_v.fader_config || {}) },
        cosmetics: { ...(rawNode.cosmetics || {}), ...(_v.cosmetics || {}) },"""

code = code.replace(old_merge, new_merge)

with open('FrontEnd/frameLayout/FieldComponent.jsx', 'w') as f:
    f.write(code)

