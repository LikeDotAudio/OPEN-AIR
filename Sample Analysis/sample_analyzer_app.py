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

This module is the thin app shell: it wires the shared state, the analysis
subprocess, and file playback. Each notebook tab lives in its own module and is
mixed into AnalyzerApp:

    graph_tab.GraphMixin        — 3D cloud
    groups_tab.GroupsMixin      — Groups / CSV
    examiner_tab.ExaminerMixin  — PEAK Examiner
    guess_tab.GuessMixin        — Auto-Guess
    rename_tab.RenameMixin      — Flatten / Rename
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

from config import DEFAULT_DIR, find_binary
from graph_tab import GraphMixin
from groups_tab import GroupsMixin
from examiner_tab import ExaminerMixin
from guess_tab import GuessMixin
from rename_tab import RenameMixin


class AnalyzerApp(GraphMixin, GroupsMixin, ExaminerMixin, GuessMixin, RenameMixin):
    def __init__(self, root):
        self.root = root
        self.root.title("Sample Analyzer (Rust core)")
        self.root.geometry("820x640")

        _default = DEFAULT_DIR if os.path.isdir(DEFAULT_DIR) else "No directory selected"
        self.directory = tk.StringVar(value=_default)
        self.binary = find_binary()
        self.is_analyzing = False
        self.q = queue.Queue()
        self.proc = None

        # live cloud data — one entry per analyzed file
        self.d_pitch = []   # X
        self.d_cx = []      # Z (complexity)
        self.d_len = []     # size
        self.d_group = []   # name group -> Y depth + colour
        self.d_rec = []     # full streamed record per point (for click/inspect)
        self.n_loops = 0
        self._legend_groups = None  # last group set drawn in the legend
        self._zoom = 1.0            # scroll-wheel zoom factor
        self._pts = None            # (xs, ys, zs) of current cloud, for picking
        self._sel_txt = None        # overlay annotation for the selected point
        self._sel_marker = None     # highlight marker for the selected point

        self.group_vars = {}        # group name -> BooleanVar (visible?)
        self._group_box_keys = None # last set of groups drawn as checkboxes
        self._pt_recs = []          # records parallel to the plotted points

        # full records (from the .PEAK file) for the Groups / Examiner tabs
        self.records = []
        self.records_by_path = {}   # abs path -> record, for the renamer columns
        self.peak_path = None
        self.root_dir = None        # scanned root, to resolve sample paths

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

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self._build_cloud_tab()
        self._build_groups_tab()
        self._build_examiner_tab()
        self._build_guess_tab()
        self._build_rename_tab()

        # Enable Start if the default directory is valid and the binary is built.
        if self.binary and os.path.isdir(self.directory.get()):
            self.action_btn.config(state=tk.NORMAL)

    # ---- shared: file resolution + playback -------------------------------
    def _resolve_path(self, rec):
        if rec.get("path") and os.path.isfile(rec["path"]):
            return rec["path"]
        root = self.root_dir or (self.directory.get() if os.path.isdir(self.directory.get()) else None)
        if root:
            p = os.path.join(root, rec.get("folder", ""), rec.get("name", ""))
            if os.path.isfile(p):
                return p
        return None

    def _play_selected(self):
        if not self.selected_rec:
            return
        path = self._resolve_path(self.selected_rec)
        if path:
            self._play_file(path)
        else:
            self.sel_label.config(text="⚠ file not found")

    def _play_file(self, path):
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif os.name == "nt":
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                player = shutil.which("paplay") or shutil.which("aplay") or shutil.which("ffplay")
                if not player:
                    self.sel_label.config(text="⚠ no audio player (install pulseaudio/alsa)")
                    return
                cmd = [player, "-nodisp", "-autoexit", path] if player.endswith("ffplay") else [player, path]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            self.sel_label.config(text="⚠ " + str(e)[:30])

    # ---- analysis subprocess + streamed results ---------------------------
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
        self.root_dir = directory
        self.action_btn.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.d_pitch, self.d_cx, self.d_len, self.d_group, self.d_rec = [], [], [], [], []
        self.n_loops = 0
        self._legend_groups = None
        self._pts = None
        self.selected_rec = None
        self._sel_txt = None
        self._sel_marker = None
        self.play_btn.config(state=tk.DISABLED)
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
                        self.d_rec.append(msg)
                        if (msg.get("transients", 1) or 1) > 1:
                            self.n_loops += 1
                        redraw = True
                elif t == "done":
                    out = msg.get("out", "")
                    self.status.config(text=f"Done — {msg.get('count', 0)} samples → {out}", foreground="#2a7")
                    self._load_records(out)
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

    def _load_records(self, out_path):
        """Load the full .PEAK records (all fields) for the Groups + Examiner tabs."""
        try:
            with open(out_path, encoding="utf-8") as f:
                data = json.load(f)
            self.records = data if isinstance(data, list) else []
            self.records_by_path = {r.get("path"): r for r in self.records if r.get("path")}
            self.peak_path = out_path
            # Prefer the authoritative full records for click-inspect too.
            if self.records and len(self.records) == len(self.d_rec):
                self.d_rec = self.records
            self._rebuild_groups()
            # Auto-load the same file into the examiner.
            self.exam_records = self.records
            self.exam_path = out_path
            self._populate_examiner()
        except Exception as e:
            self.status.config(text="Loaded but could not read PEAK: " + str(e), foreground="#c33")


def main():
    root = tk.Tk()
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    AnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
