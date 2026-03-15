# workers/icons/make_icon.py
#
# This script generates the application icon as an SVG file.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260118.000000.1

import os
import pathlib

def generate_icon():
    """
    Generates the OPEN-AIR application icon as an SVG file.
    The icon consists of a rounded dark rectangle with "OA" text.
    """
    svg_content = """<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" rx="60" fill="#2E3440" />
  <text x="50%" y="54%" font-family="Arial, sans-serif" font-size="160" font-weight="bold" text-anchor="middle" dominant-baseline="central">
    <tspan fill="#FF8C00" dx="-5">O</tspan><tspan fill="#007BFF" dx="5">A</tspan>
  </text>
</svg>"""

    # Get the project root directory
    current_script_path = pathlib.Path(__file__).resolve()
    project_root = current_script_path.parent.parent.parent
    
    # Define the output path
    output_dir = project_root / "assets" / "images"
    output_path = output_dir / "open_air_icon.svg"
    
    # Ensure the directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write the SVG content
    with open(output_path, "w") as f:
        f.write(svg_content)
    
    print(f"✅ Icon generated and saved to: {output_path}")

if __name__ == "__main__":
    generate_icon()