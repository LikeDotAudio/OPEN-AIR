# workers/worker_draw_bargraph.py
#
# A worker to generate a horizontal bar graph image.
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
# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# As the current hour is 20, no change is needed.

Current_Date = 20251129  ##Update on the day the change was made
Current_Time = 120000  ## update at the time it was edited and compiled
Current_iteration = 1  ## a running version number - incriments by one each time

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = Current_Date * Current_Time * Current_iteration

import os
from PIL import Image, ImageDraw, ImageFont
import workers.setup.worker_project_paths as project_paths


def create_bar_graph_image(
    value,
    text,
    width=200,
    height=60,
    bg_color=(200, 200, 200),
    bar_color=(0, 0, 255),
    text_color=(0, 0, 0),
):
    """
    Creates a horizontal bar graph image with text.

    Args:
        value (int): The value to represent, from -100 to 0.
        text (str): The text to display on the image.
        width (int): The width of the image.
        height (int): The height of the image.
        bg_color (tuple): The background color of the image.
        bar_color (tuple): The color of the bar.
        text_color (tuple): The color of the text.

    Returns:
        str: The path to the saved image.
    """
    if not -100 <= value <= 0:
        raise ValueError("Value must be between -100 and 0.")

    # Create a new image with a light gray background
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Calculate the width of the bar
    bar_height = 10
    bar_y_position = height - bar_height - 5
    bar_width = (value + 100) * width / 100

    # Draw the bar
    draw.rectangle(
        [(0, bar_y_position), (bar_width, bar_y_position + bar_height)], fill=bar_color
    )

    # Draw the text
    try:
        font = ImageFont.truetype("arial.ttf", 10)
    except IOError:
        font = ImageFont.load_default()

    draw.text((5, 5), text, font=font, fill=text_color)

    # Save the image to the DATA folder
    image_name = f"bar_graph_{value}.png"
    image_path = os.path.join(project_paths.DATA_DIR, image_name)
    img.save(image_path)

    return image_path
