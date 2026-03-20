from oaGuiManager.Core.parser.standardizers.lexicon_expander import LexiconExpander
from oaGuiManager.Core.parser.standardizers.semantic_layout_resolver import SemanticLayoutResolver
from oaGuiManager.Core.parser.standardizers.widget_type_resolver import WidgetTypeResolver

class SmartWidgetStandardizerMixin:
    """
    Refactored mixin that normalizes "Universal Rhyme" schema into the flat schema 
    expected by concrete widget creators.
    """

    def _standardize_widget_config(self, config):
        if not isinstance(config, dict):
            return config

        # 0. Homogenized Schema & Lexicon Processing
        config = self._process_homogenized_schema(config)

        # 1. Style Inheritance
        styles_registry = getattr(self, "config_data", {}).get("styles", {})
        style_parent_name = config.get("style_parent")
        if style_parent_name and style_parent_name in styles_registry:
            parent_style = styles_registry[style_parent_name]
            new_config = parent_style.copy()
            new_config.update(config)
            config = new_config

        # Extract structured blocks (Pillars)
        geometry = config.get("geometry", config.get("layout", {}))
        domain = config.get("domain", config.get("scale", {}))
        dynamics = config.get("dynamics", config.get("physics", {}))
        cosmetics = config.get("cosmetics", {})
        readout = config.get("readout", {})
        interaction = config.get("interaction", {})
        style_block = config.get("style", {})

        # Identity mappings
        labels = config.get("labels", {})
        if "label" in config: config["label_active"] = config["label"]
        if "main" in labels: config["label_active"] = labels["main"]
        if "v1" in labels: config["label_v1"] = labels["v1"]
        if "v2" in labels: config["label_v2"] = labels["v2"]
        if "visible" in labels: 
            config["show_label"] = labels["visible"]
            config["label_visible"] = labels["visible"]
        if "show_units" in labels: config["show_units"] = labels["show_units"]
        if "unit_text" in labels: config["units"] = labels["unit_text"]
        if "notes" in config: config["description"] = config["notes"]

        # Cosmetics & Styling
        colors = cosmetics.get("colors", {})
        def get_styled_val(key_list, default=None):
            for k in key_list:
                if k in style_block: return style_block[k]
                if k in config: return config[k]
                if k in colors: return colors[k]
                if k in cosmetics: return cosmetics[k]
            return default

        # Apply fonts and colors
        config["active_text_color"] = get_styled_val(["font_on_colour", "font_on_color", "active_font_color", "active_text_color"], "#1a1a1a")
        config["text_color"] = get_styled_val(["font_off_colour", "font_off_color", "inactive_font_color", "text_color"], "#888888")
        config["active_color"] = get_styled_val(["colour_light", "color_light", "glow_color", "active_color"], "#FF9900")
        config["active_bg_color"] = get_styled_val(["colour_button_on_bg", "color_button_on_bg", "active_bg_color"], "#000000")
        config["bg_color"] = get_styled_val(["colour_button_off_bg", "color_button_off_bg", "bg_color", "bg_colour"], "#2b2b2b")

        # Geometry & Orientation
        config["Orientation"] = str(geometry.get("orientation", "vertical")).lower()
        if config["Orientation"].startswith("horiz"): config["Orientation"] = "horizontal"
        
        # Semantic Layout
        config["layout"] = config.get("layout", {})
        config["layout"]["sticky"] = SemanticLayoutResolver.resolve_sticky(geometry, config)

        # Widget Type Aliasing
        config["type"] = WidgetTypeResolver.resolve_type(config, config["Orientation"])

        # Domain & Math
        primary = domain.get("primary", domain)
        for k, targets in {"min": ["min", "value_min"], "max": ["max", "value_max"], "step": ["step"]}.items():
            if k in primary:
                for t in targets: config[t] = primary[k]

        return config

    def _process_homogenized_schema(self, config):
        config = LexiconExpander.expand(config)
        pillars = ["identity", "geometry", "domain", "dynamics", "cosmetics"]
        if any(p in config for p in pillars):
            for p in pillars:
                if p in config:
                    block = LexiconExpander.expand(config.pop(p))
                    config.update(block)
        return config
