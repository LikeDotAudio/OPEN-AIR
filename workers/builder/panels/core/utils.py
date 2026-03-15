from PIL import Image

class PanelUtils:
    @staticmethod
    def hex_to_rgba(hex_str):
        if not isinstance(hex_str, str): return (128, 128, 128, 255)
        if hex_str.lower() == "transparent": return (0, 0, 0, 0)
        c = hex_str.lstrip('#')
        try:
            rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
            return rgb[:3] + (255,)
        except: return (128, 128, 128, 255)

    @staticmethod
    def hex_to_rgb(hex_str):
        if not isinstance(hex_str, str): return (128, 128, 128)
        if hex_str.lower() == "transparent": return (0, 0, 0) # Return 3-tuple for consistency
        c = hex_str.lstrip('#')
        try:
            rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
            return rgb[:3] # Ensure only 3 components
        except: return (128, 128, 128)
