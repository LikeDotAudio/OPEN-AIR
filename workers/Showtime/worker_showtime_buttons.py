# Showtime/worker_showtime_buttons.py
#
# A worker to create buttons with dynamically generated bar graph images.
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
# Version 20250821.200641.1

Current_Date = 20251129  ##Update on the day the change was made
Current_Time = 120000  ## update at the time it was edited and compiled
Current_iteration = 1  ## a running version number - incriments by one each time

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = Current_Date * Current_Time * Current_iteration

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from workers.Showtime.worker_showtime_draw_bargraph import create_bar_graph_image


# Creates a Tkinter button with a dynamically generated bar graph image.
# This function generates an image representing a bar graph based on a given value,
# embeds this image into a Tkinter button, and returns the configured button widget.
# Inputs:
#     parent: The parent widget for the button.
#     value (int): The numerical value to represent on the bar graph (typically -100 to 0).
#     text (str): The text label to potentially display within the bar graph image.
# Outputs:
#     ttk.Button: The created Tkinter button widget with the bar graph image.
def create_button_with_bar_graph(parent, value, text):
    """
    Creates a button with a bar graph image.

    Args:
        parent: The parent widget for the button.
        value (int): The value to represent on the bar graph, from -100 to 0.
        text (str): The text to display on the button.

    Returns:
        ttk.Button: The created button.
    """
    image_path = create_bar_graph_image(value, text)
    img = Image.open(image_path)
    photo = ImageTk.PhotoImage(img)

    button = ttk.Button(parent, image=photo)
    button.image = photo  # Keep a reference to the image to prevent garbage collection

    return button