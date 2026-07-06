import re

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'r') as f:
    code = f.read()

old_shelf_parse = """                // Shelf overrides
                if (key.toLowerCase() === 'low' && String(messages[`OpenAir/Gui/EQ_Params/Low/Shelf`]) === '1') {
                    type = 'lowshelf';
                }
                if (key.toLowerCase() === 'high' && String(messages[`OpenAir/Gui/EQ_Params/High/Shelf`]) === '1') {
                    type = 'highshelf';
                }"""

new_shelf_parse = """                // Helper to unwrap MQTT value
                const unwrap = (v) => {
                    if (v === undefined || v === null) return undefined;
                    try {
                        let parsed = typeof v === 'string' ? JSON.parse(v) : v;
                        if (typeof parsed === 'object' && parsed !== null && parsed.value !== undefined) return parsed.value;
                        return parsed;
                    } catch(e) { return v; }
                };

                const lowShelf = unwrap(messages[`OpenAir/Gui/EQ_Params/Low/Shelf`]);
                const highShelf = unwrap(messages[`OpenAir/Gui/EQ_Params/High/Shelf`]);

                // Shelf overrides
                if (key.toLowerCase() === 'low' && (lowShelf == 1 || lowShelf === true)) {
                    type = 'lowshelf';
                }
                if (key.toLowerCase() === 'high' && (highShelf == 1 || highShelf === true)) {
                    type = 'highshelf';
                }"""

if old_shelf_parse in code:
    code = code.replace(old_shelf_parse, new_shelf_parse)
    with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'w') as f:
        f.write(code)
    print("Successfully replaced shelf parse logic!")
else:
    print("Failed to find old shelf parse logic! Let me try regex...")
    
    # Try regex fallback if spacing is wrong
    pattern = re.compile(r'// Shelf overrides.*?type = \'highshelf\';\s*}', re.DOTALL)
    if pattern.search(code):
        code = pattern.sub(new_shelf_parse, code)
        with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'w') as f:
            f.write(code)
        print("Successfully replaced shelf parse logic via regex!")
    else:
        print("Regex also failed!")
