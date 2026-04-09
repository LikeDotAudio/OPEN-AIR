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
            res = widget_id_str.lstrip("/")
        else:
            # Also filter tab_name
            tab_parts = str(tab_name).split("/")
            # ⚡ V3.1.9 NAMESPACE CONSOLIDATION: Strip GUI/oaGui
            tab_parts = [p for p in tab_parts if p.lower() not in ["oagui", "gui"]]
            
            clean_tab_parts = [p for p in tab_parts if p.lower() not in ["display", "assets", "oaguielements"]]
            clean_tab = "/".join(clean_tab_parts)

            if (base_topic_str and clean_tab and 
                clean_tab.startswith(base_topic_str)):
                clean_tab = clean_tab[len(base_topic_str) :].strip("/")
            
            res = "/".join([p for p in [base_topic_str, clean_tab, 
                            widget_id_str.lstrip("/")] if p]).replace("//", "/")
        
        self._cache[cache_key] = res
        return res
