# `_WinkButton` Widget Documentation

The `_WinkButton` is a highly customizable, animated button widget for the OPEN-AIR GUI. It features a unique "shutter" animation that transitions between an inactive ("closed") state and an active ("open") state, mimicking a mechanical eye or camera shutter.

This widget is ideal for status indicators, toggles, momentary triggers, and visual alarms.

## 1. Basic Usage

To use a `_WinkButton` in your JSON layout, set the `widget_type` to `_WinkButton` and provide a unique `path`.

```json
{
  "widget_type": "_WinkButton",
  "label_active": "Power",
  "path": "system/power",
  "color": "#00FF00" 
}
```

## 2. Key Parameters

### Appearance
*   **`color`** (string): The color of the "neon" center when the eye is OPEN (active). Supports hex codes (`#FF0000`) and standard color names (`red`). Default: `#00FF00` (Lime).
*   **`shutter_color`** (string): The color of the eyelids/shutters when CLOSED (inactive). Default: `#333333` (Dark Gray).
*   **`border_thickness`** (int): Thickness of the outer border. Default: `2`.
*   **`shape_type`** (string): The geometry of the button.
    *   `"round"` (Default): A circular button with a circular iris.
    *   `"rect"` or `"square"`: A rectangular button with linear shutters.
*   **`radius`** (int): Corner radius for `"rect"` or `"square"` shapes. Default: `0` (sharp corners).
*   **`width`**, **`height`** (int): Dimensions of the widget in pixels.

### Behavior
*   **`latching`** (bool):
    *   `true`: Click to toggle ON/OFF. State persists.
    *   `false` (Default): Momentary action. ON while held, OFF when released.
*   **`blink_interval`** (int): Time in milliseconds for automatic blinking when active. Set to `0` to disable blinking. Default: `0` (Steady ON).

### Text & Labels
*   **`text_inside`** (string): Text displayed in the center when OPEN (active). e.g., "ON", "LIVE".
*   **`text_inside_color`** (string): Color of the active text. Default: Automatic contrast (black/white).
*   **`text_closed`** (string): Text displayed on the shutters when CLOSED (inactive). e.g., "OFF", "WAIT".
*   **`text_closed_color`** (string): Color of the inactive text. Default: Automatic contrast.
*   **`label_active`** (string): An external label displayed above or next to the button.

### Animation Timing
The transition animation can be fine-tuned for different "ballistics" (snappy, lazy, slow).
*   **`open_speed`** (float): Speed factor for opening (0.01 to 1.0). Higher is faster. Default: `0.2`.
*   **`close_speed`** (float): Speed factor for closing (0.01 to 1.0). Higher is faster. Default: `0.2`.

## 3. Advanced Examples

### The "Black-to-Color" Reveal
A sleek effect where the button looks like a black void until activated, revealing a neon color and text.

```json
{
  "widget_type": "_WinkButton",
  "label_active": "Stealth Mode",
  "path": "audio/stealth",
  "color": "#00FFFF",        // Neon Cyan Reveal
  "shutter_color": "black",  // Invisible when off
  "text_inside": "ACTIVE",
  "text_closed": "",         // No text when closed
  "shape_type": "round"
}
```

### The "Alarm" Blinker
A red warning light that flashes rapidly when active.

```json
{
  "widget_type": "_WinkButton",
  "label_active": "Alert",
  "path": "system/alert",
  "color": "#FF0000",
  "blink_interval": 200,     // Fast 200ms blink
  "text_inside": "ERROR",
  "latching": true
}
```

### The "Mechanical" Toggle
A slow, deliberate toggle switch with text on both states.

```json
{
  "widget_type": "_WinkButton",
  "label_active": "Engine",
  "path": "engine/state",
  "color": "#FFA500",
  "shutter_color": "#444444",
  "open_speed": 0.05,        // Slow opening
  "close_speed": 0.05,       // Slow closing
  "text_inside": "RUNNING",
  "text_closed": "STOPPED",
  "latching": true,
  "shape_type": "rect",
  "width": 100,
  "height": 50,
  "radius": 5
}
```

## 4. Technical Details

*   **Implementation**: `workers/builder/builder_audio/dynamic_gui_create_wink.py`
*   **State Management**: Mirrors state via MQTT. 
    *   Payload `1.0` / `True` -> OPEN
    *   Payload `0.0` / `False` -> CLOSED
*   **Animation**: Uses a threaded animation loop to smoothly interpolate the "aperture" or "shutter" position without blocking the main GUI thread.
