# Methods/makegif.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: This script generates a GIF animation of a dynamic wave pattern using Matplotlib, intended for splash screen display.

import os

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# Simulated constants that were originally imported from oaStyle
BAR_WIDTH = 0.08
BASE_HEIGHT_LAYER1 = 6
BASE_HEIGHT_LAYER2 = 8
BASE_HEIGHT_LAYER3 = 10
BASE_HEIGHT_LAYER4 = 7
BASE_HEIGHT_LAYER5 = 18
ENVELOPE_COEFFICIENT = -0.025
ENVELOPE_RANGE_LIMIT = 10
FPS = 20
FRAMES = 50
HEIGHT = 2.5
LINE_OFFSET_ELECTRIC = 0.3
LINE_OFFSET_STANDARD = 0.2
NUM_BARS = 120
SPIKE_TRIGGER_CENTER = 3.5
SPIKE_TRIGGER_STEEPNESS = -8
WIDTH = 6
Y_LIMIT_MAX = 22

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FILENAME = os.path.join(SCRIPT_DIR, "splash_logo.gif")

BG_COLOR = "black"

# --- Constants ---
X_LIMIT_MAX = 4 * np.pi


# --- Setup Figure ---
fig = plt.figure(figsize=(WIDTH, HEIGHT), facecolor=BG_COLOR)
fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

# --- 2. Setup Wave Axes ---
axes = fig.add_axes([0, 0.0, 1, 1.0], facecolor=BG_COLOR)
axes.set_axis_off()
axes.set_ylim(0, Y_LIMIT_MAX)
axes.set_xlim(0, X_LIMIT_MAX)

# --- 3. Data & Objects ---
num_bars = NUM_BARS
x_vals = np.linspace(0, X_LIMIT_MAX, num_bars)

# Gradient (Orange -> Blue)
colors = ["#FF4500", "#FF8C00", "#FFD700", "#40E0D0", "#1E90FF"]
colormap = LinearSegmentedColormap.from_list("orange_blue", colors, N=num_bars)
bar_colors = colormap(np.linspace(0, 1, num_bars))


def create_wave_layer(alpha_bar, color_line, width_line, alpha_line):
    bars = axes.bar(
        x_vals, np.zeros(num_bars), width=BAR_WIDTH, color=bar_colors, alpha=alpha_bar
    )
    line, = axes.plot([], [], color=color_line, linewidth=width_line, alpha=alpha_line)
    return bars, line


# --- CREATE 5 LAYERS (All Gradient) ---
bars1, line1 = create_wave_layer(0.15, "#1E90FF", 1.0, 0.3)
bars2, line2 = create_wave_layer(0.25, "#3633FD", 1.5, 0.5)
bars3, line3 = create_wave_layer(0.70, "white", 2.5, 0.9)
bars4, line4 = create_wave_layer(0.40, "#FFD700", 1.0, 0.7)
bars5, line5 = create_wave_layer(0.60, "#FFA600", 2.0, 0.9)

# --- ENVELOPE (Wide Edges) ---
envelope = np.exp(ENVELOPE_COEFFICIENT * (np.linspace(-ENVELOPE_RANGE_LIMIT, ENVELOPE_RANGE_LIMIT, num_bars)) ** 2)


def calculate_wave_height(time_phase, offset_x, offset_t):
    return np.abs(np.sin(x_vals + offset_x - time_phase) * np.sin(0.5 * x_vals + time_phase + offset_t))


def update_animation_frame(frame):
    progress = frame / FRAMES
    time_phase = 2 * np.pi * progress  # Perfect Loop

    # 1. Deep Background
    height_layer1 = calculate_wave_height(time_phase, 1.0, 0) * envelope * BASE_HEIGHT_LAYER1 * (1.0 + 0.1 * np.sin(time_phase))

    # 2. Ghost
    height_layer2 = calculate_wave_height(time_phase, 2.0, 1.5) * envelope * BASE_HEIGHT_LAYER2 * (1.0 + 0.15 * np.sin(2 * time_phase))

    # 3. Main
    raw_main = calculate_wave_height(time_phase, 0, 0) + (np.abs(np.sin(2 * x_vals - time_phase * 2) * 0.3))
    height_layer3 = raw_main * envelope * BASE_HEIGHT_LAYER3 * (1.0 + 0.1 * np.sin(time_phase))

    # 4. Electric
    raw_elec = calculate_wave_height(time_phase * 2, 0.5, 3.0)
    height_layer4 = raw_elec * envelope * BASE_HEIGHT_LAYER4 * (1.0 + 0.2 * np.sin(3 * time_phase))

    # 5. THE HARMONIC SPIKE
    spike_trigger = np.exp(SPIKE_TRIGGER_STEEPNESS * (time_phase - SPIKE_TRIGGER_CENTER) ** 2)
    harmonics = np.abs(np.sin(12 * x_vals - time_phase * 5) * np.sin(18 * x_vals + time_phase))
    height_layer5 = harmonics * envelope * BASE_HEIGHT_LAYER5 * spike_trigger

    def update_layer_set(bars, line, heights, line_offset):
        for bar, height in zip(bars, heights):
            bar.set_height(height)
        line.set_data(x_vals, heights + line_offset)

    update_layer_set(bars1, line1, height_layer1, LINE_OFFSET_STANDARD)
    update_layer_set(bars2, line2, height_layer2, LINE_OFFSET_STANDARD)
    update_layer_set(bars3, line3, height_layer3, LINE_OFFSET_STANDARD)
    update_layer_set(bars4, line4, height_layer4, LINE_OFFSET_ELECTRIC)
    update_layer_set(bars5, line5, height_layer5, LINE_OFFSET_STANDARD)

    return (
        list(bars1)
        + list(bars2)
        + list(bars3)
        + list(bars4)
        + list(bars5)
        + [line1, line2, line3, line4, line5]
    )


print(f"Generating {FRAMES} frames (Standard Colors)...")
ani = animation.FuncAnimation(fig, update_animation_frame, frames=FRAMES, blit=False)
ani.save(
    FILENAME, writer="pillow", fps=FPS, savefig_kwargs={"facecolor": BG_COLOR}, dpi=100
)
print(f"✅ Saved to: {FILENAME}")
