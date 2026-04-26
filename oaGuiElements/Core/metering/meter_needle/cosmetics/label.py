# cosmetics/label.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose


class BezelLabel:
    @staticmethod
    def draw(canvas, cx, cy, cosmetics, current_value=None):
        """
        Draws custom text labels on the meter face.
        Labels are defined in cosmetics['labels'] as a list of dictionaries.
        """
        labels = cosmetics.get("labels", [])
        if not labels:
            return

        default_color = cosmetics.get("colors", {}).get("foreground", "white")

        for label_cfg in labels:
            text = label_cfg.get("text", "")

            # --- Implement Value Overlay Logic ---
            if label_cfg.get("value_overlay", False) and current_value is not None:
                sig_fig = label_cfg.get("sig_fig", 3)
                try:
                    text = f"{float(current_value):.{sig_fig}f}"
                except (ValueError, TypeError):
                    text = str(current_value)

            if not text:
                continue

            # Position relative to pivot (cx, cy)
            rel_x = label_cfg.get("x", 0)
            rel_y = label_cfg.get("y", 0)

            x = cx + rel_x
            y = cy + rel_y

            # Style
            font_family = label_cfg.get("font", "Helvetica")
            font_size = label_cfg.get("size", 10)
            font_weight = label_cfg.get("weight", "normal")
            color = label_cfg.get("color", default_color)
            anchor = label_cfg.get("anchor", "center")

            font_spec = (font_family, font_size, font_weight)

            canvas.create_text(x, y, text=text, fill=color, font=font_spec, anchor=anchor, tags="nextgen_foreground")
