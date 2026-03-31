# OPEN-AIR User Manual

## 05. Customization

One of OPEN-AIR's greatest strengths is its deep customization through simple, human-readable configuration.

### Customizing the UI Layout
To reorganize your dashboard:
1.  **Rearrange Folders:** Move folders within the `oaGuiDefinitions/` directory. For example, moving a folder from `left_50/top_10` to `right_50/top_10` will move that entire UI block to the right column.
2.  **Add New Tabs:** Create a new folder (e.g., `5_My_Dashboard`) within a container directory. The system will automatically add it as a new tab.

### Editing Widget Configurations
Most UI elements are defined in `.json` files. You can modify these files to change widget behavior:
- **Change Labels:** Update the `"label"` key for any block or widget.
- **Adjust Colors:** Set `"background_color"` or `"text_color"` to hexadecimal values (e.g., `#2b2b2b`).
- **Scale Widgets:** Change `"width"` and `"height"` properties.

### "Next Gen" Meter Customization
You can apply photorealistic bezels to any meter by adding `style_overrides` to its JSON definition:

```json
"style_overrides": {
    "bezel_shape": "gem",
    "bezel_width": 12,
    "bezel_color": "#ff0000",
    "lighting": true,
    "aperture_mask": "smile"
}
```

**Supported Bezel Shapes:** `gem`, `pyramid`, `cylinder`, `hex`, `squircle`, `badge`, `crest`.

### Global System Configuration
The `config.ini` file in the root directory manages system-level settings:
- **`broker_address`:** IP address of your MQTT broker.
- **`enable_debug_mode`:** Set to `True` for verbose logging.
- **`mission_critical_mode`:** If enabled, the supervisor will automatically restart any partitions that crash.

### Background and Screws
OPEN-AIR can automatically generate industrial backgrounds and panel screws for your UI.
- **Default Panels:** If a JSON GUI doesn't specify a background, it defaults to the configuration in `oaGuiDefinitions/default_panel.json`.
- **Panel Screws:** The system can render realistic hardware screws on your panels, with customizable styles (e.g., Phillips, Slotted, Hex).
