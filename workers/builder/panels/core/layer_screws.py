from PIL import Image
import random
from workers.builder.panel_screw.screw_generator import ScrewGenerator

class ScrewLayer:
    @staticmethod
    def generate_screws(width, height, config, fold_cfg=None):
        layer = Image.new('RGBA', (width, height), (0,0,0,0))
        size, margin = int(config.get("size_px", 24)), 30
        
        # 1. Determine enabled locations from config
        loc_cfg = config.get("locations", ["top", "bottom", "middle"])
        if isinstance(loc_cfg, str): loc_cfg = [loc_cfg]
        loc_cfg = [l.lower() for l in loc_cfg]
        
        positions = []
        if "top" in loc_cfg:
            positions.extend([(margin, margin), (width-margin, margin)])
        if "bottom" in loc_cfg:
            positions.extend([(margin, height-margin), (width-margin, height-margin)])
        if "middle" in loc_cfg:
            positions.extend([(width//2, margin), (width//2, height-margin)])

        # 2. Check for Metal Fold Repetition
        if fold_cfg and fold_cfg.get("enabled") and fold_cfg.get("repeat_screws"):
            for crease in fold_cfg.get("creases", []):
                orientation = crease.get("orientation", "vertical").lower()
                pos_pct = float(crease.get("position_pct", 0.5))
                
                if orientation == "vertical":
                    x = int(width * pos_pct)
                    if "top" in loc_cfg: positions.append((x, margin))
                    if "bottom" in loc_cfg: positions.append((x, height-margin))
                else:
                    # Horizontal Fold Repetition (Screws on Left and Right)
                    # We place them ABOVE and BELOW the fold to secure both panels.
                    y = int(height * pos_pct)
                    # Screws in bottom of upper panel
                    positions.append((margin, y - margin))
                    positions.append((width - margin, y - margin))
                    # Screws in top of lower panel
                    positions.append((margin, y + margin))
                    positions.append((width - margin, y + margin))

        # 3. Draw Screws
        for cx, cy in positions:
            img = ScrewGenerator.generate_screw(size, {**config, "angle": random.randint(0, 90)})
            layer.alpha_composite(img, (cx - img.width // 2, cy - img.height // 2))
            
        return layer
