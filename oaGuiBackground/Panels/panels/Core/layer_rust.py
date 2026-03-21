from PIL import Image, ImageChops, ImageFilter

class RustLayer:
    @staticmethod
    def generate_rust_spots(width, height, intensity):
        noise = Image.effect_noise((width, height), sigma=50)
        mask = noise.point(lambda p: 255 if p > (255 - (intensity * 50)) else 0).convert("L")
        mask = mask.filter(ImageFilter.MaxFilter(size=3)).filter(ImageFilter.GaussianBlur(radius=2))
        rust_img = Image.new("RGBA", (width, height), (110, 50, 20, 0))
        rust_img.putalpha(mask)
        r, g, b, a = rust_img.split()
        return Image.merge("RGBA", (r, g, b, ImageChops.multiply(a, noise.convert("L"))))
