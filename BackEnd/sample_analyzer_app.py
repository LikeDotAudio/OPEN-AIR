#!/usr/bin/env python3
"""Sample Analyzer GUI.

The heavy DSP now lives in the Rust binary `oa_sample_analyzer` (see
sample_analyzer_rs/). This script is only the GUI: it picks a folder, launches
the Rust analyzer (30 parallel workers), reads its streamed JSON progress, and
draws a LIVE 3D cloud of the "magic" while the analysis runs — the same cloud
the web front-end shows in SoundBrowse ▸ THE CLOUD:

    X = pitch (Hz)   ·   Y (depth) = name group   ·   Z = complexity / timbre
    point size = sample length   ·   colour = name group (legend)

The Rust process writes `sample_cloud_data.PEAK` with each file's name + folder.
"""
import os
import sys
import json
import queue
import shutil
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (registers the 3d projection)
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

HERE = os.path.dirname(os.path.abspath(__file__))

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


class AnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sample Analyzer (Rust core)")
        self.root.geometry("820x640")

        self.directory = tk.StringVar(value="No directory selected")
        self.binary = find_binary()
        self.is_analyzing = False
        self.q = queue.Queue()
        self.proc = None

        # live cloud data — one entry per analyzed file
        self.d_pitch = []   # X
        self.d_cx = []      # Z (complexity)
        self.d_len = []     # size
        self.d_group = []   # name group -> Y depth + colour
        self.n_loops = 0
        self._legend_groups = None  # last group set drawn in the legend

        self._build_ui()
        self.root.after(60, self._drain_queue)

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Directory:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(top, textvariable=self.directory, foreground="#c47a1a", wraplength=520).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(top, text="Browse…", command=self.browse).pack(side=tk.RIGHT)

        row = ttk.Frame(self.root, padding=(10, 0))
        row.pack(fill=tk.X)
        self.progress = ttk.Progressbar(row, orient=tk.HORIZONTAL, mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.action_btn = ttk.Button(row, text="Start Analysis", command=self.start, state=tk.DISABLED)
        self.action_btn.pack(side=tk.RIGHT)

        self.status = ttk.Label(self.root, text=("Rust binary: " + (self.binary or "NOT BUILT — run: cargo build --release in sample_analyzer_rs/")),
                                foreground=("#2a7" if self.binary else "#c33"), padding=(10, 4))
        self.status.pack(fill=tk.X)

        # Live 3D cloud
        self.fig = Figure(figsize=(7, 4.4), dpi=100, facecolor="#1b1b1b")
        self.ax = self.fig.add_subplot(111, projection="3d", facecolor="#0f0f0f")
        self._style_axes()
        self.scatter = self.ax.scatter([], [], [], depthshade=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 10))

    def _style_axes(self):
        self.ax.set_xlabel("Pitch (Hz)", color="#aaa", labelpad=8)
        self.ax.set_ylabel("Name group", color="#aaa", labelpad=12)
        self.ax.set_zlabel("Complexity / Timbre", color="#aaa", labelpad=6)
        self.ax.set_title("Live 3D sample cloud — depth = name group · size = length", color="#f4902c")
        self.ax.tick_params(colors="#888")
        try:
            self.ax.set_facecolor("#0f0f0f")
            for pane in (self.ax.xaxis, self.ax.yaxis, self.ax.zaxis):
                pane.set_pane_color((0.06, 0.06, 0.06, 1.0))
                pane._axinfo["grid"]["color"] = (0.2, 0.2, 0.2, 1.0)
        except Exception:
            pass

    def _color_for(self, groups, g):
        return CLOUD_PALETTE[max(0, groups.index(g)) % len(CLOUD_PALETTE)]

    def browse(self):
        if self.is_analyzing:
            return
        d = filedialog.askdirectory(title="Select Folder to Analyze")
        if d:
            self.directory.set(d)
            self.action_btn.config(state=(tk.NORMAL if self.binary else tk.DISABLED))

    def start(self):
        if self.is_analyzing or not self.binary:
            return
        directory = self.directory.get()
        if not os.path.isdir(directory):
            messagebox.showerror("Error", "Invalid directory.")
            return
        self.is_analyzing = True
        self.action_btn.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.d_pitch, self.d_cx, self.d_len, self.d_group = [], [], [], []
        self.n_loops = 0
        self._legend_groups = None
        self.ax.clear(); self._style_axes()
        self.scatter = self.ax.scatter([], [], [], depthshade=True)
        if self.ax.get_legend():
            self.ax.get_legend().remove()
        self.canvas.draw_idle()
        threading.Thread(target=self._run, args=(directory,), daemon=True).start()

    def _run(self, directory):
        try:
            self.proc = subprocess.Popen(
                [self.binary, directory, "--workers", "30"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
            )
            for line in self.proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    self.q.put(json.loads(line))
                except json.JSONDecodeError:
                    pass
            self.proc.wait()
        except Exception as e:
            self.q.put({"type": "error", "msg": str(e)})
        finally:
            self.q.put({"type": "finished"})

    def _drain_queue(self):
        redraw = False
        try:
            for _ in range(2000):
                msg = self.q.get_nowait()
                t = msg.get("type")
                if t == "start":
                    self.progress.config(maximum=max(1, msg.get("total", 1)))
                elif t in ("result", "skip"):
                    self.progress["value"] = msg.get("done", 0)
                    if t == "result":
                        self.d_pitch.append(msg.get("pitch", 0.0) or 0.0)
                        self.d_cx.append(msg.get("complexity", 0.0) or 0.0)
                        self.d_len.append(msg.get("length", 0.1) or 0.1)
                        self.d_group.append(msg.get("group", "Other") or "Other")
                        if (msg.get("transients", 1) or 1) > 1:
                            self.n_loops += 1
                        redraw = True
                elif t == "done":
                    self.status.config(text=f"Done — {msg.get('count', 0)} samples → {msg.get('out', '')}", foreground="#2a7")
                elif t == "error":
                    self.status.config(text="Error: " + msg.get("msg", ""), foreground="#c33")
                elif t == "finished":
                    self.is_analyzing = False
                    self.action_btn.config(state=tk.NORMAL)
        except queue.Empty:
            pass
        if redraw and self.d_pitch:
            self._redraw_cloud()
        self.root.after(120, self._drain_queue)

    def _redraw_cloud(self):
        # Preserve the user's current view angle across live updates.
        elev, azim = self.ax.elev, self.ax.azim

        groups = sorted(set(self.d_group))
        gidx = {g: i for i, g in enumerate(groups)}
        xs = np.array(self.d_pitch, dtype=float)
        ys = np.array([gidx[g] for g in self.d_group], dtype=float)  # depth = name group
        zs = np.array(self.d_cx, dtype=float)

        # size = length (bigger file span -> bigger dot).
        lmin = min(self.d_len); lmax = max(self.d_len)
        span = (lmax - lmin) or 1.0
        sizes = np.array([25 + ((l - lmin) / span) * 260 for l in self.d_len])
        colors = [self._color_for(groups, g) for g in self.d_group]

        # Update the single collection in place (keeps it fast + smooth).
        self.scatter._offsets3d = (xs, ys, zs)
        self.scatter.set_sizes(sizes)
        self.scatter.set_color(colors)
        self.scatter.set_edgecolor("none")

        self.ax.set_xlim(0, float(xs.max()) * 1.1 + 1)
        self.ax.set_zlim(0, float(zs.max()) * 1.1 + 1)
        self.ax.set_ylim(-0.5, len(groups) - 0.5)
        self.ax.set_yticks(range(len(groups)))
        self.ax.set_yticklabels(groups, fontsize=7, color="#bbb")

        # Rebuild the colour legend only when the set of groups changes.
        if groups != self._legend_groups:
            handles = [Line2D([0], [0], marker="o", linestyle="", markersize=6,
                              markerfacecolor=self._color_for(groups, g), markeredgecolor="none", label=g)
                       for g in groups]
            leg = self.ax.legend(handles=handles, loc="upper left", fontsize=7, ncol=1,
                                 facecolor="#1b1b1b", edgecolor="#333", labelcolor="#ccc",
                                 framealpha=0.85, bbox_to_anchor=(0.0, 1.0))
            if leg:
                leg.set_title("Name group", prop={"size": 7})
                if leg.get_title():
                    leg.get_title().set_color("#888")
            self._legend_groups = groups

        n = len(self.d_pitch)
        self.ax.set_title(
            f"{n} samples  ·  {len(groups)} groups  ·  {self.n_loops} loops  ·  size = length",
            color="#f4902c", fontsize=9)

        self.ax.view_init(elev=elev, azim=azim)
        self.canvas.draw_idle()


def main():
    root = tk.Tk()
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    AnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
