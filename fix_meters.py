import json
import re

# 1. Modify reference_meters.json
json_file = "/home/anthony/Documents/OPEN-AIR/FrontEnd/Gui_Frames/5_Samples/2_Metering/1_Needle/0_REF/reference_meters.json"
with open(json_file, "r") as f:
    data = json.load(f)

root_key = "Zoo_Metering_Needle_REF"
blocks = data[root_key]["blocks"]

for block_key, block in blocks.items():
    if "fields" in block:
        # Better spaced out: maybe use 3 columns instead of whatever it is?
        # Or just change width/height of the meters.
        for field_key, field in block["fields"].items():
            if "geometry" in field:
                # Make them bigger
                field["geometry"]["width"] = 280
                field["geometry"]["height"] = 200

with open(json_file, "w") as f:
    json.dump(data, f, indent=2)


# 2. Modify NeedleMeter.jsx
jsx_file = "/home/anthony/Documents/OPEN-AIR/FrontEnd/libControl/metering/NeedleMeter/NeedleMeter.jsx"
with open(jsx_file, "r") as f:
    jsx_code = f.read()

# We need to move the Scale geometry section up.
scale_geom_regex = re.compile(r"(\s*// --- Scale geometry \(tilt \+ direction\) ---.*?const nAng = angRad\(boundedVal\);)", re.DOTALL)
scale_geom_match = scale_geom_regex.search(jsx_code)
if scale_geom_match:
    scale_geom_text = scale_geom_match.group(1)
    # Remove from original position
    jsx_code = jsx_code.replace(scale_geom_text, "")
    
    # Insert before Bezel body
    bezel_regex = re.compile(r"(\s*// --- Bezel body \+ clipped face ---)")
    jsx_code = bezel_regex.sub(scale_geom_text + r"\n\1", jsx_code)

    # Now update the arc drawing
    old_arc = "ctx.beginPath(); ctx.arc(centerX, centerY, arcRadius + 5, Math.PI, 0); ctx.lineTo(centerX, centerY); ctx.closePath();"
    new_arc = "const padDeg = 18;\n        ctx.beginPath(); ctx.arc(centerX, centerY, arcRadius + 5, toRad(startDeg + padDeg), toRad(endDeg - padDeg), false); ctx.lineTo(centerX, centerY); ctx.closePath();"
    jsx_code = jsx_code.replace(old_arc, new_arc)

    with open(jsx_file, "w") as f:
        f.write(jsx_code)
    print("NeedleMeter.jsx and reference_meters.json modified successfully!")
else:
    print("Could not find Scale geometry block to move.")
