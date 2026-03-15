# managers/Display/parser/gui_smart_standardizer.py
#
# A mixin that normalizes "Universal Rhyme" schema into the flat schema 
# expected by concrete widget creators.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio
# Version 20260118.4

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()


class SmartWidgetStandardizerMixin:
    """
    Normalizes the configuration of a widget. 
    It translates the structured 'Universal Rhyme' schema into the flat parameters 
    expected by existing creators.
    """

    def _standardize_widget_config(self, config):
        """
        Translates a structured config into a flat one.
        Handles _SmartMeter, _SmartKnob, _SmartFader, _SmartGraph aliases.
        Supports the new 5-pillar homogenized schema and abbreviation lexicon.
        """
        if not isinstance(config, dict):
            return config

        # --- 0. Homogenized Schema & Lexicon Processing ---
        config = self._process_homogenized_schema(config)

        # --- 1. Handle Style Parents (Inheritance) ---
        # We look up styles in the root configuration (stored in self.config_data)
        styles_registry = getattr(self, "config_data", {}).get("styles", {})
        style_parent_name = config.get("style_parent")
        if style_parent_name and style_parent_name in styles_registry:
            parent_style = styles_registry[style_parent_name]
            # Deep merge: parent_style provides defaults, config overrides
            # Simplified merge: shallow merge for now, but prioritizes config
            new_config = parent_style.copy()
            new_config.update(config)
            config = new_config

        # 1. Identity Mappings (Top level or nested in 'labels')
        labels = config.get("labels", {})
        if "label" in config: 
            config["label_active"] = config["label"]
        if "main" in labels: 
            config["label_active"] = labels["main"]
        if "v1" in labels: 
            config["label_v1"] = labels["v1"]
        if "v2" in labels: 
            config["label_v2"] = labels["v2"]
        if "visible" in labels: 
            config["show_label"] = labels["visible"]
            config["label_visible"] = labels["visible"]
        if "show_units" in labels: 
            config["show_units"] = labels["show_units"]
        if "unit_text" in labels:
            config["unit_text"] = labels["unit_text"]
            config["units"] = labels["unit_text"]

        if "notes" in config:
            config["description"] = config["notes"]

        # 2. Extract Stanzas (The "Universal Rhyme" Structure)
        geometry = config.get("geometry", config.get("layout", {})) # Allow 'layout' as fallback
        domain = config.get("domain", config.get("scale", {})) # Allow 'scale' as fallback
        dynamics = config.get("dynamics", config.get("physics", {})) # Allow 'physics' as fallback
        style_block = config.get("style", {}) # New photorealistic style block
        cosmetics = config.get("cosmetics", {}) # Legacy style/cosmetics block
        readout = config.get("readout", {})
        interaction = config.get("interaction", {})

        # 2.1 Map COSMETICS/STYLE -> The Look (Apply early as DEFAULTS)
        colors = cosmetics.get("colors", {})
        
        # New "Industrial Backlit" specific mappings
        # Mapping: font_on_colour -> active_text_color
        # Mapping: font_off_colour -> text_color
        # Mapping: colour_light -> active_color
        # Mapping: colour_button_on_bg -> active_bg_color
        # Mapping: colour_button_off_bg -> bg_color
        
        # Check style_block, cosmetics, cosmetics.colors, and top-level
        def get_styled_val(key_list, default=None):
            for k in key_list:
                if k in style_block: return style_block[k]
                if k in config: return config[k]
                if k in colors: return colors[k]
                if k in cosmetics: return cosmetics[k]
            return default

        # ⚡ OPTIMIZATION: Flatten everything from the 'style' block if it exists
        if style_block:
            for k, v in style_block.items():
                config[k] = v

        # Apply Font Settings
        if "active_text_color" not in config:
            config["active_text_color"] = get_styled_val(["font_on_colour", "font_on_color", "active_font_color", "active_text_color"], "#1a1a1a")
        if "text_color" not in config:
            config["text_color"] = get_styled_val(["font_off_colour", "font_off_color", "inactive_font_color", "text_color"], "#888888")
        
        config["active_font_style"] = get_styled_val(["font_on_style", "active_font_style"], "bold")
        config["active_font_size"] = get_styled_val(["font_on_size", "active_font_size"], None)
        config["inactive_font_style"] = get_styled_val(["font_off_style", "inactive_font_style"], "normal")
        config["inactive_font_size"] = get_styled_val(["font_off_size", "inactive_font_size"], None)

        if "active_color" not in config:
            config["active_color"] = get_styled_val(["colour_light", "color_light", "glow_color", "active_color"], "#FF9900")
        
        if "active_bg_color" not in config:
            config["active_bg_color"] = get_styled_val(["colour_button_on_bg", "color_button_on_bg", "active_bg_color"], "#000000")
        if "bg_color" not in config:
            config["bg_color"] = get_styled_val(["colour_button_off_bg", "color_button_off_bg", "bg_color", "bg_colour"], "#2b2b2b")

        config["glow_intensity"] = get_styled_val(["colour_light_intensity", "color_light_intensity", "glow_intensity"], 1.0)

        # Standard Mappings
        if "primary" in colors:
            c = colors["primary"]
            config["indicator_color"] = c
            config["Pointer_colour"] = c
            config["Lower_range_colour"] = c
            config["fader_grip_color"] = c
            config["cap_color"] = c
        elif "active" in colors:
            c = colors["active"]
            config["indicator_color"] = c
            config["Pointer_colour"] = c
            config["Lower_range_colour"] = c

        if "cap" in colors:
            config["cap_color"] = colors["cap"]
        if "cap_highlight" in colors:
            config["cap_highlight_color"] = colors["cap_highlight"]
        if "cap_highlights" in colors:
            config["cap_highlight_color"] = colors["cap_highlights"]

        if "secondary" in colors:
            c = colors["secondary"]
            config["tick_color"] = c
            config["secondary_color"] = c
            config["fader_track_color"] = c
        
        if "alert" in colors or "clipping" in colors:
            c = colors.get("alert") or colors.get("clipping")
            config["upper_range_Colour"] = c
            config["Peak_display_colour"] = c
            
        if "warning" in colors:
            config["Middle_range_colour"] = colors["warning"]

        if "highlight" in colors:
            config["value_highlight_color"] = colors["highlight"]

        if "background" in colors:
            config["bg"] = colors["background"]
            config["background_color"] = colors["background"]

        style_flags = cosmetics.get("style_flags", {})
        ticks_config = cosmetics.get("ticks", {})
        show_ticks = ticks_config.get("show", style_flags.get("show_grid"))
        if show_ticks is not None:
            config["show_ticks"] = show_ticks
            config["Ticks_visible"] = show_ticks
            config["show_grid"] = show_ticks
        
        if "style" in ticks_config: config["tick_style"] = ticks_config["style"]
        if "interval" in ticks_config: config["tick_interval"] = ticks_config["interval"]

        if "fill_shape" in style_flags:
            config["fill_With_Value"] = style_flags["fill_shape"]
            config["piechart"] = style_flags["fill_shape"]
        
        # 3. Map GEOMETRY -> Space
        if "width" in geometry:
            config["width"] = geometry["width"]
        if "height" in geometry:
            config["height"] = geometry["height"]
        
        orientation = "vertical" # Default
        if "orientation" in geometry:
            ori = str(geometry["orientation"]).lower()
            if ori.startswith("vert"): 
                orientation = "vertical"
            elif ori.startswith("horiz"): 
                orientation = "horizontal"
            else: 
                orientation = ori
        config["Orientation"] = orientation

        if "padding" in geometry:
            config["padding"] = geometry["padding"]
        
        if "fader_cap_scale" in geometry:
            config["fader_cap_scale"] = geometry["fader_cap_scale"]
        
        cap_geom = geometry.get("cap", {})
        if isinstance(cap_geom, dict):
            # Support "children X and Y" as requested for cap scaling
            if "x" in cap_geom: config["cap_width"] = cap_geom["x"]
            if "y" in cap_geom: config["cap_height"] = cap_geom["y"]
            if "w" in cap_geom: config["cap_width"] = cap_geom["w"]
            if "h" in cap_geom: config["cap_height"] = cap_geom["h"]
            if "width" in cap_geom: config["cap_width"] = cap_geom["width"]
            if "height" in cap_geom: config["cap_height"] = cap_geom["height"]
            
        # --- NEW SEMANTIC LAYOUT MODEL (Align, Anchor, Stretch) ---
        # Alignment (Justification): Sit without resizing
        # Anchoring (Pinned): Stick to edge
        # Stretching (Opposing Anchors): Change size to fill
        
        sticky_parts = set()
        
        stretch = geometry.get("stretch", "").lower()
        anchor = geometry.get("anchor", "").lower()
        align = geometry.get("align", "").lower()
        
        # 1. Handle Stretching (Size Change)
        # Stretches ALWAYS override width/height constraints in Tkinter
        if stretch in ["width", "horizontal", "ew"]:
            sticky_parts.update(["e", "w"])
        elif stretch in ["height", "vertical", "ns"]:
            sticky_parts.update(["n", "s"])
        elif stretch in ["both", "all", "fill", "nsew"]:
            sticky_parts.update(["n", "s", "e", "w"])
            
        # 2. Handle Anchoring (Pinned Position)
        anchor_map = {
            "top": "n", "bottom": "s", "left": "w", "right": "e",
            "north": "n", "south": "s", "west": "w", "east": "e",
            "nw": "nw", "ne": "ne", "sw": "sw", "se": "se"
        }
        for part in anchor_map.get(anchor, ""):
            sticky_parts.add(part)
            
        # 3. Handle Alignment (Justification)
        # Only apply if not stretching in that axis
        if "e" not in sticky_parts and "w" not in sticky_parts:
            if align in ["left", "west"]: sticky_parts.add("w")
            if align in ["right", "east"]: sticky_parts.add("e")
        if "n" not in sticky_parts and "s" not in sticky_parts:
            if align in ["top", "north"]: sticky_parts.add("n")
            if align in ["bottom", "south"]: sticky_parts.add("s")
            
        # 4. Fallback to Deprecated 'sticky' (ONLY if new model not used)
        if not (stretch or anchor or align) and "sticky" in geometry:
            sticky_parts.update(list(geometry["sticky"].lower()))
            
        # --- 5. SAFETY: Fixed Size Enforcement ---
        # If we have an explicit width but NO horizontal stretch, 
        # ensure we aren't pinned to both E and W (which forces stretching)
        has_fixed_width = "width" in geometry or "width" in config
        if has_fixed_width and stretch not in ["width", "both", "horizontal", "fill", "nsew"]:
            if "e" in sticky_parts and "w" in sticky_parts:
                # Default to centering if conflicted
                sticky_parts.discard("e")
                sticky_parts.discard("w")

        has_fixed_height = "height" in geometry or "height" in config
        if has_fixed_height and stretch not in ["height", "both", "vertical", "fill", "nsew"]:
            if "n" in sticky_parts and "s" in sticky_parts:
                # Default to top-pinning if conflicted
                sticky_parts.discard("s")
                if not align: sticky_parts.add("n")

        final_sticky = "".join(sorted(list(sticky_parts)))
        
        # Layout specific properties (Grid)
        if "layout" not in config: config["layout"] = {}
        config["layout"]["sticky"] = final_sticky
        
        for k in ["col_span", "row_span", "weight", "minwidth", "font", "colour", "padx", "pady", "weight_y"]:
            val = geometry.get(k)
            if val is not None:
                config["layout"][k] = val

        # 4. Handle "Smart" Aliases (Orientation & Style Aware)
        widget_type = config.get("type", "")
        if widget_type == "_SmartMeter":
            # Check for visualization preference in cosmetics
            viz = cosmetics.get("style_flags", {}).get("visualization", "bar").lower()
            if viz == "needle":
                config["type"] = "_NeedleVUMeter"
            else:
                config["type"] = "_BarGraph"
        elif widget_type == "_SmartKnob":
            config["type"] = "_Knob"
        elif widget_type == "_SmartFader":
            if orientation == "horizontal":
                config["type"] = "_CustomHorizontalFader"
            else:
                config["type"] = "_CustomFader"
        elif widget_type in ["_DataGraph", "_SmartGraph", "_Plot"]:
            config["type"] = "DynamicGraph"
        elif widget_type in ["_SmartVUKnob", "_BarGraphKnob", "_VUMeterKnob"]:
            config["type"] = "_VUMeterKnob"
        elif widget_type == "_CustomLTP":
            # Hybrid Fader/Knob - keep type but standardize contents
            pass
        elif widget_type == "_SmartToggle":
            config["type"] = "_GuiButtonToggle"
        elif widget_type == "_SmartToggler":
            config["type"] = "_GuiButtonToggler"
        elif widget_type == "_SmartCheckbox":
            config["type"] = "_GuiCheckbox"
        elif widget_type in ["_GuiActuator", "_SmartActuator", "_ButtonActuator"]:
            config["type"] = "_GuiActuator"
        elif widget_type in ["_Value", "_SmartValue", "_ValueBox", "_GuiValue"]:
            config["type"] = "_Value"
        elif widget_type in ["OcaTable", "GuiTable", "DynamicGuiTable", "_Table"]:
            config["type"] = "OcaTable"
        elif widget_type == "Block":
            config["type"] = "OcaBlock"
        elif widget_type == "_SmartIncDec":
            config["type"] = "_IncDecButtons"
        elif widget_type == "_SmartNav":
            config["type"] = "_DirectionalButtons"
        elif widget_type == "_SmartList":
            config["type"] = "_GuiListbox"
        elif widget_type == "_SmartInput":
            config["type"] = "_TextInput"
        elif widget_type == "_SmartValue":
            config["type"] = "_Value"
        elif widget_type == "_SmartLabel":
            config["type"] = "_Label"
        elif widget_type == "_SmartLink":
            config["type"] = "_WebLink"
        elif widget_type == "_SmartProgress":
            config["type"] = "_ProgressBar"
        elif widget_type == "_SmartImage":
            config["type"] = "_ImageDisplay"
        elif widget_type == "_SmartAnimation":
            config["type"] = "_AnimationDisplay"
        elif widget_type == "_SmartLight":
            config["type"] = "_HeaderStatusLight"
            
        # Common Deep Mappings for Meters, Knobs, Faders, LTP
        if widget_type in ["_SmartMeter", "_SmartKnob", "_SmartFader", "_Knob", "_Fader", "_BarGraph", "_NeedleVUMeter", "_CustomLTP"]:
            # Pointer block
            ptr = cosmetics.get("pointer", {})
            if "style" in ptr: config["pointer_style"] = ptr["style"]
            if "length" in ptr: config["pointer_length"] = ptr["length"]
            if "offset" in ptr: config["pointer_offset"] = ptr["offset"]
            if "show" in ptr: config["pointer"] = ptr["show"]
            if "thickness" in ptr: config["Needle_thickness"] = ptr["thickness"]
            if "primary_color" in ptr: config["Pointer_colour"] = ptr["primary_color"]
            if "secondary_color" in ptr: config["Pointer_colour_2"] = ptr["secondary_color"]
            if "secondary_style" in ptr: config["Pointer_Style_2"] = ptr["secondary_style"]
            if "secondary_thickness" in ptr: config["Needle_thickness_2"] = ptr["secondary_thickness"]
            if "pivot_size" in ptr: config["Pivot_size"] = ptr["pivot_size"]
            if "pivot_color" in ptr: config["Pivot_colour"] = ptr["pivot_color"]
            if "pivot_crop" in ptr: config["pivot_crop"] = ptr["pivot_crop"]
            
            # Scale (Ticks) block
            scl = cosmetics.get("scale", {})
            if "show" in scl: 
                config["show_ticks"] = scl["show"]
                config["Ticks_visible"] = scl["show"]
            if "style" in scl: config["tick_style"] = scl["style"]
            if "length" in scl: config["tick_length"] = scl["length"]
            if "thickness" in scl: config["tick_thickness"] = scl["thickness"]
            if "size" in scl: config["tick_size"] = scl["size"]
            if "upper_range" in scl: config["upper_range"] = scl["upper_range"]
            
            # Styling block
            sty = cosmetics.get("styling", {})
            if "gradient" in sty: config["gradient_level"] = sty["gradient"]
            if "teeth" in sty: config["knob_teeth"] = sty["teeth"]
            if "outline_thickness" in sty: config["knob_outline_thickness"] = sty["outline_thickness"]
            if "outline_color" in sty: config["knob_outline_color"] = sty["outline_color"]
            if "fill_color" in sty: config["knob_fill_color"] = sty["fill_color"]
            if "tick_style" in sty: config["knob_tick_style"] = sty["tick_style"]
            if "arc_width" in sty: config["arc_width"] = sty["arc_width"]
            if "no_center" in sty: config["no_center"] = sty["no_center"]
            if "cap_radius" in sty: config["cap_radius"] = sty["cap_radius"]
            if "cap_color" in sty: config["cap_color"] = sty["cap_color"]

            # Knob-specific cosmetics for hybrid widgets
            k_cos = cosmetics.get("knob", {})
            if "visualization" in k_cos: config["knob_shape"] = k_cos["visualization"]
            if "width" in k_cos: config["knob_width"] = k_cos["width"]
            if "height" in k_cos: config["knob_height"] = k_cos["height"]
            
            k_ptr = k_cos.get("pointer", {})
            if "style" in k_ptr: config["knob_pointer_style"] = k_ptr["style"]
            
            k_sty = k_cos.get("styling", {})
            if "fill_color" in k_sty: config["knob_fill_color"] = k_sty["fill_color"]
            if "outline_color" in k_sty: config["knob_outline_color"] = k_sty["outline_color"]

            # style_overrides block (Universal unpacking for specialized widget params)
            ovr = cosmetics.get("style_overrides", {})
            for k, v in ovr.items():
                config[k] = v

        # Knob Specifics
        if widget_type == "_SmartKnob":
            viz = cosmetics.get("visualization", "circle").lower()
            if viz in ["dial", "panner"]:
                config["knob_style"] = viz
            else:
                config["shape"] = viz

        # 5. Map DOMAIN -> The Math
        primary = domain.get("primary", domain) # Fallback to domain root
        
        # Mapping standard domain keys
        mapping = {
            "min": ["min", "value_min"],
            "max": ["max", "value_max"],
            "value_default": ["value_default", "value", "default_value"],
            "unit": ["units", "unit", "unit_text"],
            "zero_point": ["reff_point"],
            "step": ["step"]
        }
        
        for k, targets in mapping.items():
            val = primary.get(k)
            if val is not None:
                for t in targets:
                    config[t] = val
        
        # Axis support for Hybrid widgets (LTP, VUMeterKnob)
        linear = domain.get("linear", {})
        rotation = domain.get("rotation", {})
        knob_domain = domain.get("knob", {})
        
        if linear:
            if "min" in linear: config["value_min"] = linear["min"]
            if "max" in linear: config["value_max"] = linear["max"]
            if "value" in linear: config["value_default"] = linear["value"]
            if "zero_point" in linear: config["reff_point"] = linear["zero_point"]
            
        if rotation:
            if "value" in rotation: config["rotation_default"] = rotation["value"]

        if knob_domain:
            if "min" in knob_domain: config["knob_min"] = knob_domain["min"]
            if "max" in knob_domain: config["knob_max"] = knob_domain["max"]
            if "value" in knob_domain: config["knob_value_default"] = knob_domain["value"]
            if "path" in knob_domain: config["knob_path"] = knob_domain["path"]

        if "delta_absolute" in primary: config["delta_absolute"] = primary["delta_absolute"]
        
        # Dual value support (for _CustomDualHorizontalFader and Stereo Meters)
        if "value_v1" in primary: 
            config["value_default_v1"] = primary["value_v1"]
            if "value_default" not in config: config["value_default"] = primary["value_v1"]
        if "value_v2" in primary: 
            config["value_default_v2"] = primary["value_v2"]

        if primary.get("law") == "log":
            config["log_exponent"] = 2.0
        elif "log_exponent" in primary:
            config["log_exponent"] = primary["log_exponent"]

        # 6. Map DYNAMICS -> The Movement
        if "fps_limit" in dynamics:
            config["refresh_rate_ms"] = int(1000 / dynamics["fps_limit"])
        
        smoothing = dynamics.get("smoothing")
        if smoothing is not None:
            config["glide_time"] = smoothing * 1000
            config["attack_ms"] = smoothing * 1000
        
        retention = dynamics.get("retention")
        if retention is not None:
            config["fall_time"] = retention
            config["release_ms"] = retention
            config["peak_hold_time"] = retention
            
        # Support attack_ms / release_ms directly if provided in physics
        if "attack_ms" in dynamics: config["glide_time"] = dynamics["attack_ms"]
        if "release_ms" in dynamics: config["fall_time"] = dynamics["release_ms"]
        if "peak_hold_ms" in dynamics: config["peak_hold_time"] = dynamics["peak_hold_ms"]
        if "resting_point" in dynamics: config["resting_point"] = dynamics["resting_point"]

        # Response Profiles
        profile = dynamics.get("ballistics", dynamics.get("response_profile", "")).lower()
        if profile == "vu":
            config["glide_time"] = 300
            config["fall_time"] = 300
        elif profile == "ppm" or profile == "fast":
            config["glide_time"] = 10
            config["fall_time"] = 1500
        elif profile == "slow":
            config["glide_time"] = 1000
            config["fall_time"] = 4000

        # 7. Map COSMETICS -> The Look (Standard Mappings handled above)

        # 8. Map READOUT -> Display
        if "show_value" in readout:
            config["show_value"] = readout["show_value"]
        if "location" in readout:
            config["Value_text_position"] = readout["location"]
        if "units" in readout:
            config["units"] = readout["units"]
        
        # ⚡ OPTIMIZATION: Default to 2 decimal places for numeric widgets if not specified
        if "decimal_places" in readout:
            config["decimal_places"] = readout["decimal_places"]
        elif config.get("type") in ["_Knob", "_Fader", "_CustomFader", "_CustomHorizontalFader", "_CustomLTP", "_VUMeterKnob", "_NeedleVUMeter", "_BarGraph", "_SmartMeter", "_SmartKnob", "_SmartFader"]:
            config["decimal_places"] = 2
        
        if "text_inside" in readout:
            config["text_inside"] = readout["text_inside"]
        if "font_size" in readout:
            config["font_size"] = readout["font_size"]
        if "font_size_closed" in readout:
            config["font_size_closed"] = readout["font_size_closed"]
        if "label_position" in readout:
            config["label_Text_position"] = readout["label_position"]

        # 9. Map INTERACTION
        if "sensitivity" in interaction:
            config["sensitivity"] = interaction["sensitivity"]
        if "scroll_enabled" in interaction:
            config["scroll_enabled"] = interaction["scroll_enabled"]
        if "infinity" in interaction:
            config["infinity"] = interaction["infinity"]
        if "fine_pitch" in interaction:
            config["fine_pitch"] = interaction["fine_pitch"]
        if "delta_absolute" in interaction:
            config["delta_absolute"] = interaction["delta_absolute"]
        if "freestyle" in interaction:
            config["freestyle"] = interaction["freestyle"]
        if "options" in interaction:
            config["options"] = interaction["options"]

        return config

    def _process_homogenized_schema(self, config):
        """
        Detects and unpacks the 5-pillar homogenized schema.
        Handles the 'items' array for container widgets.
        """
        # 1. Expand Abbreviations at top-level if any
        config = self._expand_abbreviations(config)

        # 2. Detect Pillars
        has_pillars = any(k in config for k in ["identity", "geometry", "domain", "dynamics", "cosmetics"])
        
        if has_pillars:
            if "identity" in config:
                identity = self._expand_abbreviations(config.pop("identity"))
                config.update(identity)
            
            if "geometry" in config:
                geometry = self._expand_abbreviations(config.pop("geometry"))
                # Move w/h/pad/spans to top level as expected by existing creators/builder
                for k in ["width", "height", "padding", "layout_columns", "col_span", "row_span", "row", "column"]:
                    if k in geometry: config[k] = geometry[k]
                
                # Merge rest into layout (x/y/sticky etc)
                if "layout" not in config: config["layout"] = {}
                config["layout"].update(geometry)
            
            if "domain" in config:
                domain = self._expand_abbreviations(config.pop("domain"))
                config["domain"] = domain # Keep it for existing logic to pick up
                # Also flatten common ones
                for k in ["min", "max", "value_default", "units"]:
                    if k in domain: config[k] = domain[k]

            if "dynamics" in config:
                dynamics = self._expand_abbreviations(config.pop("dynamics"))
                config["dynamics"] = dynamics
                # Flatten poll -> refresh_rate_ms
                if "poll" in dynamics:
                    config["refresh_rate_ms"] = dynamics["poll"]
                if "path" in dynamics:
                    config["path"] = dynamics["path"]

            if "cosmetics" in config:
                cosmetics = self._expand_abbreviations(config.pop("cosmetics"))
                config["cosmetics"] = cosmetics
                # Flatten bg/fg
                if "bg_color" in cosmetics: config["bg_color"] = cosmetics["bg_color"]
                if "text_color" in cosmetics: config["text_color"] = cosmetics["text_color"]

        # 3. Handle 'items' -> mapping to fields/channels/datasets
        # UNCONDITIONAL: If we have items and no fields, map them. 
        # This allows root-level configs to be containers without being 'OcaBlock' types.
        if "items" in config and "fields" not in config:
            config["fields"] = {}
            for item in config["items"]:
                # Recursively standardize items
                item = self._standardize_widget_config(item)
                item_id = item.get("id") or item.get("identity", {}).get("id")
                if item_id:
                    config["fields"][item_id] = item
            
            # Additional mappings for specific types
            w_type = config.get("type")
            if w_type == "_CMDP":
                config["channels"] = config["items"]
            elif w_type in ["plot_widget", "DynamicGraph"]:
                config["datasets"] = config["items"]
            
        return config

    def _expand_abbreviations(self, data):
        """
        Maps Lexicon Abbreviations to engine-expected keys.
        Recursively expands dictionaries to support sub-configurations.
        """
        if not isinstance(data, dict):
            return data
        
        mapping = {
            "lbl": "label",
            "w": "width",
            "h": "height",
            "W": "width",
            "H": "height",
            "columns": "layout_columns",
            "colspan": "col_span",
            "rowspan": "row_span",
            "pad": "padding",
            "val": "value_default",
            "min": "min",
            "max": "max",
            "unit": "units",
            "sub": "path",
            "pub": "publish_path",
            "poll": "poll",
            "bg": "bg_color",
            "fg": "text_color"
        }
        
        # Create a copy to avoid mutation during iteration
        new_data = {}
        for k, v in data.items():
            # Recursively expand if value is a dict
            if isinstance(v, dict):
                v = self._expand_abbreviations(v)
            
            # Map the key if it exists in our mapping
            target_key = mapping.get(k, k)
            
            # ⚡ SPECIAL HANDLING: x/y should ONLY be row/column in a layout context
            # In a 'cap' or geometric context, they usually mean width/height (x=w, y=h)
            if k == "x":
                # If we are NOT in a layout-heavy dict, x likely means width
                if any(key in data for key in ["sticky", "weight", "col_span"]):
                    target_key = "row"
                else:
                    target_key = "width" # Fallback for cap.x etc.
            elif k == "y":
                if any(key in data for key in ["sticky", "weight", "row_span"]):
                    target_key = "column"
                else:
                    target_key = "height" # Fallback for cap.y etc.

            # Only overwrite if target key doesn't already exist or it's the same key
            if target_key not in new_data or target_key == k:
                new_data[target_key] = v
        
        return new_data
