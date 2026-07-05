# ==========================================
# Header: generate_icons.py
# Purpose: generate_icons.py implementation.
# Description: Logic and implementation for generate_icons.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

#!/usr/bin/env python3
"""
OPEN-AIR Icon Generator
Run this script to generate the favicon and PWA icons.
Requires Pillow: pip install Pillow
"""
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow is not installed.")
    print("Please install it by running: pip install Pillow")
    sys.exit(1)

import math

# Inline comment: Logic for generate_base_logo
def generate_base_logo(size):
    # Transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw rounded rectangle for the app icon background (black)
    rad = size * 0.225
    draw.rounded_rectangle([0, 0, size, size], radius=rad, fill=(8, 8, 8, 255))
    
    # Draw audio spectrum wave (vertical bars)
    num_bars = 45
    bar_width = size * 0.8 / num_bars
    gap = bar_width * 0.4
    bar_actual_width = bar_width - gap
    
    start_x = size * 0.1 + gap/2
    center_y = size * 0.65
    
    for i in range(num_bars):
        x = start_x + i * bar_width
        t = i / (num_bars - 1)
        
        # Color gradient: Orange -> Yellow/Green -> Blue
        if t < 0.5:
            t_color = t * 2
            r = int(244 + (180 - 244) * t_color)
            g = int(144 + (220 - 144) * t_color)
            b = int(44 + (44 - 44) * t_color)
        else:
            t_color = (t - 0.5) * 2
            r = int(180 + (0 - 180) * t_color)
            g = int(220 + (170 - 220) * t_color)
            b = int(44 + (255 - 44) * t_color)
            
        color = (r, g, b, 255)
        
        # Height function (superposition of gaussians)
        h1 = math.exp(-((t - 0.25) ** 2) / 0.008) * 0.3 * size
        h2 = math.exp(-((t - 0.5) ** 2) / 0.01) * 0.15 * size
        h3 = math.exp(-((t - 0.75) ** 2) / 0.008) * 0.25 * size
        noise = abs(math.sin(t * 40)) * 0.02 * size
        
        h = max(size * 0.02, h1 + h2 + h3 + noise)
        
        draw.rounded_rectangle([x, center_y - h, x + bar_actual_width, center_y + h * 0.15], radius=bar_actual_width/2, fill=color)

    # Stylized geometric "O A" text
    ox = size * 0.35
    oy = size * 0.25
    orad = size * 0.08
    stroke = int(size * 0.035)
    
    # O (Orange)
    draw.ellipse([ox - orad, oy - orad, ox + orad, oy + orad], outline=(244, 144, 44, 255), width=stroke)
    
    # A (Blue)
    ax = size * 0.65
    ay = size * 0.25
    draw.line([ax, ay - orad, ax - orad*0.7, ay + orad], fill=(0, 170, 255, 255), width=stroke, joint="curve")
    draw.line([ax, ay - orad, ax + orad*0.7, ay + orad], fill=(0, 170, 255, 255), width=stroke, joint="curve")
    draw.line([ax - orad*0.35, ay + orad*0.2, ax + orad*0.35, ay + orad*0.2], fill=(0, 170, 255, 255), width=stroke)
    
    return img

# Inline comment: Logic for main
def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("🎨 Generating base 512x512 logo...")
    img_512 = generate_base_logo(512)
    path_512 = os.path.join(script_dir, "icon-512.png")
    img_512.save(path_512)
    print(f"✅ Saved {path_512}")
    
    print("🎨 Resizing to 192x192...")
    resample_filter = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS
    img_192 = img_512.resize((192, 192), resample_filter)
    path_192 = os.path.join(script_dir, "icon-192.png")
    img_192.save(path_192)
    print(f"✅ Saved {path_192}")
    
    print("🎨 Generating favicon.ico...")
    img_32 = img_512.resize((32, 32), resample_filter)
    path_ico = os.path.join(script_dir, "favicon.ico")
    img_32.save(path_ico, format='ICO')
    print(f"✅ Saved {path_ico}")
    
    print("\n🎉 All icons generated successfully!")

if __name__ == "__main__":
    main()
