# oaGui/FileReaders/widget_schema_normalizer.py
# Author: Anthony Peter Kuzub
# Version: 20260406.0040.1
#
# Description: Static Translation Engine for GUI Configuration Schema.

from oaGui.Constants.schema_defaults import DEFAULT_COLORS, PILLARS, STRUCT_TYPES
from oaGui.FileReaders.standardizers.schema_utils import (
    calculate_sticky,
    deep_merge,
    expand_abbreviations,
    get_styled_val,
)
from oaGui.FileReaders.standardizers.widget_type_resolver import WidgetTypeResolver


class WidgetSchemaNormalizer:
    """Static Translation Engine for GUI Configuration Schema."""

    @staticmethod
    def normalize(config, root_config=None):
        """Translates a structured config into a flat attribute set."""
        if not isinstance(config, dict): return config

        # 0. Lexicon Expansion & Pillar Unpacking
        config = WidgetSchemaNormalizer._process_homogenized_schema(config)

        # 1. Style Inheritance
        styles_registry = root_config.get("styles", {}) if root_config else {}
        parent_name = config.get("style_parent") or config.get("type", config.get("widget_type"))

        if parent_name in styles_registry:
            config = deep_merge(styles_registry[parent_name].copy(), config)

        # 2. Identity and Label Mapping
        labels = config.get("labels", {})
        # show_label now lives under label{} (migrated from top-level / labels /
        # style_flags). Hoist it to the flat config so every downstream reader
        # (config.get("show_label"), readout/labels fallbacks) keeps working.
        _label = config.get("label")
        if isinstance(_label, dict) and "show_label" in _label:
            config["show_label"] = _label["show_label"]
            config["label_visible"] = _label["show_label"]
        # Map label -> label_active, but never promote a flag-only {show_label}
        # dict to the visible title.
        if "label" in config and not (isinstance(_label, dict) and set(_label.keys()) <= {"show_label"}):
            config["label_active"] = config["label"]
        # Containers (OcaBlock/OcaArray/…) title themselves via `description`;
        # description.show_label toggles whether that title is displayed.
        _desc = config.get("description")
        if isinstance(_desc, dict) and "show_label" in _desc:
            config["show_label"] = _desc["show_label"]
            config["label_visible"] = _desc["show_label"]
        if "main" in labels: config["label_active"] = labels["main"]
        if "v1" in labels: config["label_v1"] = labels["v1"]
        if "v2" in labels: config["label_v2"] = labels["v2"]
        if "visible" in labels:
            config["show_label"] = labels["visible"]
            config["label_visible"] = labels["visible"]
        if "show_units" in labels: config["show_units"] = labels["show_units"]
        if "unit_text" in labels:
            config["unit_text"] = labels["unit_text"]
            config["units"] = labels["unit_text"]
        if "notes" in config: config["description"] = config["notes"]

        # 3. Universal Rhyme Extraction
        geometry = config.get("geometry", config.get("layout", {}))
        domain = config.get("domain", config.get("scale", {}))
        dynamics = config.get("dynamics", config.get("physics", {}))
        style_block = config.get("style", {})
        cosmetics = config.get("cosmetics", {})

        # 3.1 Aesthetics Flattening
        if style_block:
            for k, v in style_block.items(): config[k] = v

        # Resolve Colors/Fonts via modular helper
        if "active_text_color" not in config:
            config["active_text_color"] = get_styled_val(
                ["font_on_colour", "font_on_color", "active_text_color"],
                config, style_block, cosmetics, DEFAULT_COLORS["active_text"]
            )
        if "text_color" not in config:
            config["text_color"] = get_styled_val(
                ["font_off_colour", "font_off_color", "text_color"],
                config, style_block, cosmetics, DEFAULT_COLORS["inactive_text"]
            )

        config["active_font_style"] = get_styled_val(["font_on_style"], config, style_block, cosmetics, "bold")
        config["inactive_font_style"] = get_styled_val(["font_off_style"], config, style_block, cosmetics, "normal")

        if "active_color" not in config:
            config["active_color"] = get_styled_val(
                ["colour_light", "color_light", "active_color"],
                config, style_block, cosmetics, DEFAULT_COLORS["active_accent"]
            )

        is_struct = any(config.get(k) in STRUCT_TYPES for k in ["type", "widget_type"])
        if "bg_color" not in config:
            default_bg = "transparent" if is_struct else DEFAULT_COLORS["panel_bg"]
            config["bg_color"] = get_styled_val(["colour_button_off_bg", "bg_color"], config, style_block, cosmetics, default_bg)
            if is_struct: config["transparent"] = True

        # 4. Geometry and Space
        # Percent strings ("100%") on width/height mean "fill the parent" — they
        # become a stretch directive (so calculate_sticky picks them up) instead
        # of a literal pixel value.
        stretch_additions = []
        if "width" in geometry:
            w = geometry["width"]
            if isinstance(w, str) and w.strip().endswith("%"):
                stretch_additions.append("width")
            else:
                config["width"] = max(1, int(float(w)))
        if "height" in geometry:
            h = geometry["height"]
            if isinstance(h, str) and h.strip().endswith("%"):
                stretch_additions.append("height")
            else:
                config["height"] = max(1, int(float(h)))

        if stretch_additions:
            geometry = dict(geometry)
            existing_stretch = str(geometry.get("stretch", "")).strip()
            geometry["stretch"] = (existing_stretch + " " + " ".join(stretch_additions)).strip()

        final_sticky = calculate_sticky(geometry)
        if "layout" not in config: config["layout"] = {}
        if final_sticky: config["layout"]["sticky"] = final_sticky

        # 5. Centralized Alias Resolution
        orientation = str(geometry.get("orientation", "vertical")).lower()
        config["type"] = WidgetTypeResolver.resolve_type(config, orientation)

        # 6. Domain and Ballistics
        primary_domain = domain.get("primary", domain)
        config["value_min"] = primary_domain.get("min", 0.0)
        config["value_max"] = primary_domain.get("max", 1.0)
        config["value_default"] = primary_domain.get("value_default", 0.0)

        if "fps_limit" in dynamics:
            config["refresh_rate_ms"] = int(1000 / dynamics["fps_limit"])

        smoothing = dynamics.get("smoothing")
        if smoothing is not None: config["glide_time"] = smoothing * 1000

        return config

    @staticmethod
    def _process_homogenized_schema(config):
        """Unpacks the 5-pillar schema and maps 'items' to 'fields'."""
        config = expand_abbreviations(config)
        for pillar in PILLARS:
            if pillar in config:
                stanza = expand_abbreviations(config.pop(pillar))
                if pillar == "identity": config.update(stanza)
                else: config[pillar] = stanza

        if "items" in config and "fields" not in config:
            config["fields"] = config["items"]
        return config


