# Core/topic_calculator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

class TopicCalculator:
    """
    Generates fully qualified MQTT topic paths from widget IDs and tab names.
    Uses memoization to optimize recurring lookups.
    """

    def __init__(self, base_topic):
        self.base_topic = base_topic
        self._cache = {}

    def calculate(self, widget_id, tab_name):
        cache_key = (widget_id, tab_name)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Ensure base_topic is a string
        base_topic_str = str(self.base_topic)

        # Standardize hierarchical delimiters and strip structural tokens
        widget_id_str = str(widget_id).replace(".fields.", ".").replace(".", "/")

        # ⚡ V3.1.9 NAMESPACE CONSOLIDATION: Map 'oaGui' to 'GUI'
        parts = widget_id_str.split("/")
        # We don't map to GUI anymore to avoid it in the output path
        parts = [p for p in parts if p.lower() not in ["oagui", "gui"]]

        # ⚡ OPTIMIZATION: Strip structural tokens like 'display', 'Assets', 'oaGuiElements'
        filtered_parts = [p for p in parts if p.lower() not in ["display", "assets", "oaguielements"]]
        widget_id_str = "/".join(filtered_parts)

        if (widget_id_str.startswith(base_topic_str + "/") or
            widget_id_str.startswith("/")):
            result_topic = widget_id_str.lstrip("/")
        else:
            # Also filter tab_name
            tab_parts = str(tab_name).split("/")
            # ⚡ ALIGNMENT WITH WEB: tab_name from generate_topic_path_from_filepath
            # is the full file-walker hierarchy (Gui_Frames/Window/Spectrum/...).
            # The web frontend publishes under a flat OpenAir/Gui/<json_root>/...
            # shape, so collapse the file walk to just "Gui" here. Telemetry
            # snitches use a separate code path (get_topic) and keep the full
            # hierarchy for per-widget differentiation.
            if tab_parts and tab_parts[0].lower() == "gui_frames":
                tab_parts = ["Gui"]
            else:
                tab_parts = [p for p in tab_parts if p.lower() not in ["oagui", "gui"]]

            clean_tab_parts = [p for p in tab_parts if p.lower() not in ["display", "assets", "oaguielements"]]
            clean_tab = "/".join(clean_tab_parts)

            if (base_topic_str and clean_tab and
                clean_tab.startswith(base_topic_str)):
                clean_tab = clean_tab[len(base_topic_str) :].strip("/")

            result_topic = "/".join([p for p in [base_topic_str, clean_tab,
                            widget_id_str.lstrip("/")] if p]).replace("//", "/")

        self._cache[cache_key] = result_topic
        return result_topic
