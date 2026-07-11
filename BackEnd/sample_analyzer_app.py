#!/usr/bin/env python3
"""Sample Analyzer GUI.

The heavy DSP now lives in the Rust binary `oa_sample_analyzer` (see
sample_analyzer_rs/). This script is only the GUI: it picks a folder, launches
the Rust analyzer (30 parallel workers), reads its streamed JSON progress, and
draws a LIVE scatter of the "magic" — pitch (x) vs spectral complexity (y),
point size = sample length — while the analysis runs. The Rust process writes
`sample_cloud_data.PEAK` with each file's name + folder.
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

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

HERE = os.path.dirname(os.path.abspath(__file__))


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

        # live scatter data
        self.px, self.py, self.ps = [], [], []

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

        # Live scatter
        self.fig = Figure(figsize=(7, 4.4), dpi=100, facecolor="#1b1b1b")
        self.ax = self.fig.add_subplot(111, facecolor="#0f0f0f")
        self._style_axes()
        self.scatter = self.ax.scatter([], [], c="#f4902c", alpha=0.6, edgecolors="w", linewidths=0.3)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 10))

    def _style_axes(self):
        self.ax.set_xlabel("Pitch (Hz)", color="#aaa")
        self.ax.set_ylabel("Complexity / Timbre", color="#aaa")
        self.ax.set_title("Live sample cloud — size = length", color="#f4902c")
        self.ax.tick_params(colors="#666")
        for s in self.ax.spines.values():
            s.set_color("#333")

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
        self.px, self.py, self.ps = [], [], []
        self.ax.clear(); self._style_axes()
        self.scatter = self.ax.scatter([], [], c="#f4902c", alpha=0.6, edgecolors="w", linewidths=0.3)
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
                        self.px.append(msg.get("pitch", 0.0))
                        self.py.append(msg.get("complexity", 0.0))
                        self.ps.append(8 + min(28, (msg.get("length", 0.1) or 0.1) * 6))
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
        if redraw and self.px:
            import numpy as np
            self.scatter.set_offsets(np.column_stack([self.px, self.py]))
            self.scatter.set_sizes(self.ps)
            self.ax.set_xlim(0, max(self.px) * 1.1 + 1)
            self.ax.set_ylim(0, max(self.py) * 1.1 + 1)
            self.canvas.draw_idle()
        self.root.after(80, self._drain_queue)


def main():
    root = tk.Tk()
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    AnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
