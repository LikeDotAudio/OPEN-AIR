# 🏷️ Meter Modifyer

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
workers/builder/meter_needle/meter_modifyer.py

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class MeterModifier`
Applies cosmetic modifications (Bezels, Overlays) to a Needle Meter Canvas.
Orchestrates specialized drawers for Background, Lighting, Masks, and Bezel
Frames.

##### `draw_labels(canvas, cx, cy, cosmetics, current_value)`
Draws configurable text labels on the meter face.

**Parameters:**
- `canvas`: [TODO: Detail meaning, valid ranges, special cases]
- `cx`: [TODO: Detail meaning, valid ranges, special cases]
- `cy`: [TODO: Detail meaning, valid ranges, special cases]
- `cosmetics`: [TODO: Detail meaning, valid ranges, special cases]
- `current_value`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `draw_background_faceplate(canvas, cx, cy, w, h, cosmetics)`
Draws the solid background shape behind the meter.

**Parameters:**
- `canvas`: [TODO: Detail meaning, valid ranges, special cases]
- `cx`: [TODO: Detail meaning, valid ranges, special cases]
- `cy`: [TODO: Detail meaning, valid ranges, special cases]
- `w`: [TODO: Detail meaning, valid ranges, special cases]
- `h`: [TODO: Detail meaning, valid ranges, special cases]
- `cosmetics`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `draw_lighting_effects(canvas, cx, cy, w, h, cosmetics)`
Legacy lighting - disabled in favor of draw_glass_layer

**Parameters:**
- `canvas`: [TODO: Detail meaning, valid ranges, special cases]
- `cx`: [TODO: Detail meaning, valid ranges, special cases]
- `cy`: [TODO: Detail meaning, valid ranges, special cases]
- `w`: [TODO: Detail meaning, valid ranges, special cases]
- `h`: [TODO: Detail meaning, valid ranges, special cases]
- `cosmetics`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `draw_glass_layer(canvas, cx, cy, w, h, cosmetics)`
Draws the PIL-generated Glass/Glow overlay.

**Parameters:**
- `canvas`: [TODO: Detail meaning, valid ranges, special cases]
- `cx`: [TODO: Detail meaning, valid ranges, special cases]
- `cy`: [TODO: Detail meaning, valid ranges, special cases]
- `w`: [TODO: Detail meaning, valid ranges, special cases]
- `h`: [TODO: Detail meaning, valid ranges, special cases]
- `cosmetics`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `draw_foreground_overlay(canvas, cx, cy, w, h, cosmetics)`
Draws the aperture mask (bottom cover) and the bezel frame (top outline).

**Parameters:**
- `canvas`: [TODO: Detail meaning, valid ranges, special cases]
- `cx`: [TODO: Detail meaning, valid ranges, special cases]
- `cy`: [TODO: Detail meaning, valid ranges, special cases]
- `w`: [TODO: Detail meaning, valid ranges, special cases]
- `h`: [TODO: Detail meaning, valid ranges, special cases]
- `cosmetics`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_draw_chassis_mask(canvas, cx, cy, w, h, cosmetics)`
Creates an inverted mask of the bezel and fills it with the panel texture.
This hides anything drawn 'outside' the meter area (like pivots/tails).

**Parameters:**
- `canvas`: [TODO: Detail meaning, valid ranges, special cases]
- `cx`: [TODO: Detail meaning, valid ranges, special cases]
- `cy`: [TODO: Detail meaning, valid ranges, special cases]
- `w`: [TODO: Detail meaning, valid ranges, special cases]
- `h`: [TODO: Detail meaning, valid ranges, special cases]
- `cosmetics`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
