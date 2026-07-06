import re

with open('FrontEnd/libControl/faders/LTPFader/LTPFader.jsx', 'r') as f:
    code = f.read()

old_elma_config = """                                    pointer_tip: { show: true, color: "#546E7A", length: 0.2 },
                                    line: { color: "#ffffff" }
                                }"""

new_elma_config = """                                    pointer_tip: { show: true, color: "#546E7A", length: 0.2 },
                                    line: { color: config?.cosmetics?.line?.color || "#ffffff" }
                                }"""

code = code.replace(old_elma_config, new_elma_config)

with open('FrontEnd/libControl/faders/LTPFader/LTPFader.jsx', 'w') as f:
    f.write(code)

