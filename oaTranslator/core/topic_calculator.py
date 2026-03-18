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

        # Standardize hierarchical delimiters and strip structural tokens
        widget_id_str = str(widget_id).replace(".fields.", ".").replace(".", "/")
        
        # ⚡ OPTIMIZATION: Strip structural tokens like 'display' or 'gui'
        # The user's plan requires stripping forbidden layout tokens.
        parts = widget_id_str.split("/")
        filtered_parts = [p for p in parts if p not in ["display", "gui"]]
        widget_id_str = "/".join(filtered_parts)
        
        if (widget_id_str.startswith(self.base_topic + "/") or 
            widget_id_str.startswith("/")):
            res = widget_id_str.lstrip("/")
        else:
            # Also filter tab_name
            tab_parts = tab_name.split("/")
            clean_tab_parts = [p for p in tab_parts if p not in ["display", "gui"]]
            clean_tab = "/".join(clean_tab_parts)

            if (self.base_topic and clean_tab and 
                clean_tab.startswith(self.base_topic)):
                clean_tab = clean_tab[len(self.base_topic) :].strip("/")
            
            res = "/".join([p for p in [self.base_topic, clean_tab, 
                            widget_id_str.lstrip("/")] if p]).replace("//", "/")
        
        self._cache[cache_key] = res
        return res
