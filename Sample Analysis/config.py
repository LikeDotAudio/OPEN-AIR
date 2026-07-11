"""Shared constants + helpers for the Sample Analyzer GUI.

Kept in its own module so every tab mixin can import it without creating an
import cycle with the main app module.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))

# Folder pre-selected on startup (Browse to change).
DEFAULT_DIR = "/home/anthony/Documents/Music Samples"

# Same palette the web cloud uses, so the two graphs colour groups identically.
CLOUD_PALETTE = [
    "#f4902c", "#8ab4f8", "#4caf50", "#e57373", "#ba68c8", "#4dd0e1",
    "#ffd54f", "#a1887f", "#90a4ae", "#f06292", "#aed581", "#7986cb",
    "#ff8a65", "#4db6ac", "#dce775", "#9575cd", "#ffffff",
]


def find_binary():
    """Locate the built Rust analyzer binary (build it if missing)."""
    exe = "oa_sample_analyzer" + (".exe" if os.name == "nt" else "")
    candidates = [
        os.path.join(HERE, "sample_analyzer_rs", "target", "release", exe),
        os.path.join(HERE, "sample_analyzer_rs", "target", "debug", exe),
        shutil.which("oa_sample_analyzer"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None
