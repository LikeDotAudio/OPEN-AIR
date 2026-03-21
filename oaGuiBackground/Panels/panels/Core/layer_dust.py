from PIL import Image
import numpy as np

class DustLayer:
    @staticmethod
    def generate_dust(width, height, intensity):
        """⚡ VECTORIZED: NumPy dust generation."""
        num = int((width * height) * 0.0005 * intensity)
        if num <= 0: return Image.new('RGBA', (width, height), (0,0,0,0))
        xs, ys = np.random.randint(0, width, num), np.random.randint(0, height, num)
        cols, alphas = np.random.randint(180, 241, num, dtype=np.uint8), np.random.randint(50, 151, num, dtype=np.uint8)
        arr = np.zeros((height, width, 4), dtype=np.uint8)
        arr[ys, xs, :3], arr[ys, xs, 3] = cols[:, np.newaxis], alphas
        return Image.fromarray(arr, mode='RGBA')
