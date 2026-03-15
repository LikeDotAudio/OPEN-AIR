# OPEN-AIR User Manual

## 03. Interface Guide

The OPEN-AIR interface is designed for real-time monitoring and high-fidelity interaction.

### The "Filesystem is the UI" Concept
Your dashboard layout is dynamically generated based on the `display/` directory structure.

- **Vertical Splits:** A folder named `left_50` or `right_50` creates a vertical column taking 50% of the screen width.
- **Horizontal Splits:** Folders like `top_10` or `bottom_90` create rows within those columns.
- **Tabbed Interfaces:** If a directory contains multiple folders without percentage names, they are rendered as tabs in a Notebook interface.

### "Next Gen" Photorealistic Instrumentation
OPEN-AIR features a unique rendering engine that breathes life into standard software meters.

#### Bezel Shapes
The dashboard supports several "Next Gen" bezel shapes that surround the instrument faces:
- **Gem:** A vintage hexagonal roof with a flat base.
- **Triangle:** A pyramid-inspired base.
- **Cylinder:** A smooth, stadium-shaped housing.
- **Hex/Squircle/Badge/Crest:** Bolder, modern-industrial frames.

#### Lighting & Depth
Custom meters feature **dynamic lighting effects**, including radial glow (warm bulb simulation) and inner shadow-depth, giving the instrument a physical presence. Industrial transparency ensures widgets blend seamlessly into your custom backgrounds.

### Common UI Elements
- **Actuators:** Large, tactile buttons for high-stakes actions.
- **Rotary Selectors:** Vintage-style knobs for switching modes or ranges.
- **Trapezoid Toggles:** Industrial toggle switches with clear visual feedback.
- **Wink Buttons:** High-interactivity buttons with physics-based feedback.

### Dashboards & Panels
You can navigate different panels through the tab system at the top of each container. Each tab corresponds to a specific instrument (e.g., Spectrum Analyzer) or a system-wide view (e.g., Fleet Display).
