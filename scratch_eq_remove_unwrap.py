import re

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'r') as f:
    code = f.read()

# We need to find the inner unwrap definition inside parseBand and remove it.
# The inner one starts with "// Helper to unwrap MQTT value" and ends with "};" before "const lowShelf"
inner_unwrap_pattern = re.compile(r'\s*// Helper to unwrap MQTT value\s*const unwrap = \(v\) => \{[\s\S]*?catch\(e\) \{ return v; \}\s*\};\s*', re.DOTALL)

if inner_unwrap_pattern.search(code):
    code = inner_unwrap_pattern.sub('\n                ', code)
    with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'w') as f:
        f.write(code)
    print("Successfully removed the inner unwrap definition!")
else:
    print("Failed to find the inner unwrap definition!")
