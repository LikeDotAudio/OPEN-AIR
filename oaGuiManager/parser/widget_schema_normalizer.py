# managers/Display/parser/widget_schema_normalizer.py
#
# Semantic Schema Normalization for the OPEN-AIR Dynamic GUI.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260314.120000.REV01

"""
widget_schema_normalizer.py - Semantic Schema Translation Engine.

Purpose:
    Acts as a bridge between the high-level "Universal Rhyme" JSON schema
    and the flat attribute-heavy schema expected by individual widget 
    creators. It performs recursive normalization, style inheritance,
    and abbreviation expansion.

Responsibilities:
    - Translate structured 5-pillar stanzas (Identity, Geometry, Domain,
      Dynamics, Cosmetics) into flat configuration dictionaries.
    - Implement a cascading style system allowing widgets to inherit and
      override properties from a central 'styles' registry.
    - Resolve "Smart" aliases (e.g., _SmartMeter) into concrete widget 
      types based on their orientation and visualization metadata.
    - Enforce industrial theme defaults (colors, fonts, ballistics) when
      specific properties are omitted.

Constraints:
    - Normalization is a stateless operation.
    - Deep merging is used for nested style blocks to prevent accidental
      erasure of inherited layout properties.
"""

from oaStyle.style import THEMES, DEFAULT_THEME
from .standardizers.widget_type_resolver import WidgetTypeResolver

class WidgetSchemaNormalizer:
    """
    Static Translation Engine for GUI Configuration Schema.
    """

    @staticmethod
    def normalize(config, root_config=None):
        """
        Translates a structured config into a flat attribute set.

        Lead with action: Expands abbreviations, processes style inheritance,
        maps semantic blocks to internal keys, and resolves smart widget
        types.

        Inputs:
            config (dict): The raw widget configuration branch.
            root_config (dict, optional): The root blueprint for style lookup.

        Outputs:
            dict: The flattened and normalized configuration.
        """
        if not isinstance(config, dict):
            return config

        # 0. --- Lexicon Expansion ---
        # Handle the 5-pillar homogenized schema and common abbreviations.
        config = WidgetSchemaNormalizer._process_homogenized_schema(config)

        # 1. --- Style Inheritance (Cascading) ---
        styles_registry = root_config.get("styles", {}) if root_config else {}
        
        # Determine the style parent (either explicit or by widget type).
        style_parent_name = config.get("style_parent")
        widget_type_name = config.get("type", config.get("widget_type"))
        
        if not style_parent_name and widget_type_name in styles_registry:
            style_parent_name = widget_type_name

        if style_parent_name and style_parent_name in styles_registry:
            parent_style = styles_registry[style_parent_name]
            # Perform a deep merge: Parent provides defaults, child overrides.
            new_config = parent_style.copy()
            for k, v in config.items():
                if (isinstance(v, dict) and k in new_config and 
                    isinstance(new_config[k], dict)):
                    merged_dict = new_config[k].copy()
                    merged_dict.update(v)
                    new_config[k] = merged_dict
                else:
                    new_config[k] = v
            config = new_config

        # 2. --- Identity and Label Mapping ---
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

        # 3. --- Stanza Unpacking (Universal Rhyme) ---
        geometry = config.get("geometry", config.get("layout", {}))
        domain = config.get("domain", config.get("scale", {}))
        dynamics = config.get("dynamics", config.get("physics", {}))
        style_block = config.get("style", {})
        cosmetics = config.get("cosmetics", {})
        readout = config.get("readout", {})
        interaction = config.get("interaction", {})

        # 3.1 --- Aesthetics and Cosmetics ---
        colors = cosmetics.get("colors", {})
        
        def get_styled_val(key_list, default=None):
            """Internal helper to probe multiple blocks for a style value."""
            for k in key_list:
                if k in style_block: return style_block[k]
                if k in config: return config[k]
                if k in colors: return colors[k]
                if k in cosmetics: return cosmetics[k]
            return default

        # Flatten the modern photorealistic style block into the top level.
        if style_block:
            for k, v in style_block.items():
                config[k] = v

        # Resolve Font and Color Defaults.
        if "active_text_color" not in config:
            config["active_text_color"] = get_styled_val(
                ["font_on_colour", "font_on_color", "active_text_color"], 
                "#1a1a1a"
            )
        if "text_color" not in config:
            config["text_color"] = get_styled_val(
                ["font_off_colour", "font_off_color", "text_color"], 
                "#888888"
            )
        
        config["active_font_style"] = get_styled_val(["font_on_style"], "bold")
        config["inactive_font_style"] = get_styled_val(["font_off_style"], 
                                                        "normal")

        if "active_color" not in config:
            config["active_color"] = get_styled_val(
                ["colour_light", "color_light", "active_color"], "#FF9900"
            )
        
        # Detect structural types to handle transparency defaults.
        STRUCT_TYPES = ["OcaBlock", "OcaBin", "OcaArray", "Block", "Array"]
        is_struct = any(config.get(k) in STRUCT_TYPES 
                        for k in ["type", "widget_type"])
        
        if "bg_color" not in config:
            default_bg = "transparent" if is_struct else "#2b2b2b"
            config["bg_color"] = get_styled_val(
                ["colour_button_off_bg", "bg_color"], default_bg
            )
            if is_struct:
                config["transparent"] = True

        # 4. --- Geometry and Space ---
        if "width" in geometry: config["width"] = geometry["width"]
        if "height" in geometry: config["height"] = geometry["height"]
        
        # 4.1 --- Semantic Layout Model (Align/Anchor/Stretch) ---
        sticky_parts = set()
        stretch = str(geometry.get("stretch", "")).lower()
        anchor = str(geometry.get("anchor", "")).lower()
        align = str(geometry.get("align", "")).lower()
        
        if any(p in ["width", "fill", "nsew"] for p in stretch.split()):
            sticky_parts.update(["e", "w"])
        if any(p in ["height", "fill", "nsew"] for p in stretch.split()):
            sticky_parts.update(["n", "s"])
            
        anchor_map = {"top": "n", "bottom": "s", "left": "w", "right": "e"}
        for p in anchor.split():
            if p in anchor_map: sticky_parts.add(anchor_map[p])
            
        # Compile sticky bits into a Tkinter-compatible string (e.g., "nsew").
        final_sticky = "".join(sorted(list(sticky_parts)))
        if "layout" not in config: config["layout"] = {}
        if final_sticky: config["layout"]["sticky"] = final_sticky

        # 5. --- Centralized Alias Resolution ---
        orientation = str(geometry.get("orientation", "vertical")).lower()
        config["type"] = WidgetTypeResolver.resolve_type(config, orientation)

        # 6. --- Domain and Ballistics ---
        primary_domain = domain.get("primary", domain)
        config["value_min"] = primary_domain.get("min", 0.0)
        config["value_max"] = primary_domain.get("max", 1.0)
        config["value_default"] = primary_domain.get("value_default", 0.0)
        
        if "fps_limit" in dynamics:
            config["refresh_rate_ms"] = int(1000 / dynamics["fps_limit"])
        
        smoothing = dynamics.get("smoothing")
        if smoothing is not None:
            config["glide_time"] = smoothing * 1000

        return config

    @staticmethod
    def _process_homogenized_schema(config):
        """Unpacks the 5-pillar schema and maps 'items' to 'fields'."""
        config = WidgetSchemaNormalizer._expand_abbreviations(config)
        
        # Pillar Detection and Unpacking.
        for pillar in ["identity", "geometry", "domain", "dynamics", "cosmetics"]:
            if pillar in config:
                stanza = WidgetSchemaNormalizer._expand_abbreviations(
                    config.pop(pillar)
                )
                if pillar == "identity":
                    config.update(stanza)
                else:
                    config[pillar] = stanza

        # Handle 'items' as a generic container for child widgets.
        if "items" in config and "fields" not in config:
            # ⚡ SRP: Preserve order. If it's a list, keep it as a list for the renderer.
            # Only map to a dict if explicitly requested or if it's already a dict.
            if isinstance(config["items"], dict):
                config["fields"] = {}
                for key, item in config["items"].items():
                    config["fields"][key] = item
            # If it's a list, we leave it as 'items' or move to 'fields' as a list.
            # The Renderer now supports both formats.
            else:
                config["fields"] = config["items"]
        return config

    @staticmethod
    def _expand_abbreviations(data):
        """Recursively translates Lexicon Abbreviations to Engine Keys."""
        if not isinstance(data, dict):
            return data
        
        lexicon = {
            "lbl": "label", "w": "width", "h": "height", 
            "val": "value_default", "min": "min", "max": "max",
            "bg": "bg_color", "fg": "text_color", "unit": "units"
        }
        
        new_data = {}
        for k, v in data.items():
            if isinstance(v, dict):
                v = WidgetSchemaNormalizer._expand_abbreviations(v)
            
            target_key = lexicon.get(k, k)
            new_data[target_key] = v
        return new_data
