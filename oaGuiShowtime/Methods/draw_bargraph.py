import os
from PIL import Image, ImageDraw, ImageFont
import oaOchestration.Constants.project_paths as project_paths

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
    """
    # Clamp value for safety
    value = max(-100, min(0, value))

    # Create a new image with a transparent background
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
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
