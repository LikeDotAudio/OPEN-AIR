# standardizers/semantic_layout_resolver.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

class SemanticLayoutResolver:
    """
    Translates high-level layout intent (Align, Anchor, Stretch) into Tkinter sticky strings.
    """
    ANCHOR_MAP = {
        "top": "n", "bottom": "s", "left": "w", "right": "e",
        "north": "n", "south": "s", "west": "w", "east": "e",
        "nw": "nw", "ne": "ne", "sw": "sw", "se": "se"
    }

    @classmethod
    def resolve_sticky(cls, geometry, config):
        """
        Calculates the Tkinter sticky string based on semantic layout rules.
        """
        sticky_parts = set()
        stretch = geometry.get("stretch", "").lower()
        anchor = geometry.get("anchor", "").lower()
        align = geometry.get("align", "").lower()

        # 1. Handle Stretching (Size Change)
        if stretch in ["width", "horizontal", "ew"]:
            sticky_parts.update(["e", "w"])
        elif stretch in ["height", "vertical", "ns"]:
            sticky_parts.update(["n", "s"])
        elif stretch in ["both", "all", "fill", "nsew"]:
            sticky_parts.update(["n", "s", "e", "w"])

        # 2. Handle Anchoring (Pinned Position)
        for part in cls.ANCHOR_MAP.get(anchor, ""):
            sticky_parts.add(part)

        # 3. Handle Alignment (Justification)
        if "e" not in sticky_parts and "w" not in sticky_parts:
            if align in ["left", "west"]: sticky_parts.add("w")
            if align in ["right", "east"]: sticky_parts.add("e")
        if "n" not in sticky_parts and "s" not in sticky_parts:
            if align in ["top", "north"]: sticky_parts.add("n")
            if align in ["bottom", "south"]: sticky_parts.add("s")

        # 4. Fallback to Deprecated 'sticky'
        if not (stretch or anchor or align) and "sticky" in geometry:
            sticky_parts.update(list(geometry["sticky"].lower()))

        # 5. Fixed Size Enforcement
        has_fixed_width = "width" in geometry or "width" in config
        if has_fixed_width and stretch not in ["width", "both", "horizontal", "fill", "nsew"]:
            if "e" in sticky_parts and "w" in sticky_parts:
                sticky_parts.discard("e")
                sticky_parts.discard("w")

        has_fixed_height = "height" in geometry or "height" in config
        if has_fixed_height and stretch not in ["height", "both", "vertical", "fill", "nsew"]:
            if "n" in sticky_parts and "s" in sticky_parts:
                sticky_parts.discard("s")
                if not align: sticky_parts.add("n")

        return "".join(sorted(list(sticky_parts)))
