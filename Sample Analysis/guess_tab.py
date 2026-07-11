"""Auto-Guess tab for the Sample Analyzer (GuessMixin).

Averages each named group's acoustic (name-independent) features into a
fingerprint, then guesses the group of the 'Other' / mismatched one-shots.
"""
import math
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np


class GuessMixin:
    # Acoustic (name-independent) features used to fingerprint each group.
    GUESS_FEATS = ["centroid", "harmonicity", "low", "mid", "high", "crest",
                   "attack", "zcr", "rolloff", "flatness", "sustain", "loglen"]

    def _feat_row(self, r):
        return [
            r.get("centroid", 0) or 0, r.get("harmonicity", 0) or 0,
            r.get("low", 0) or 0, r.get("mid", 0) or 0, r.get("high", 0) or 0,
            r.get("crest", 0) or 0, r.get("attack", 0) or 0, r.get("zcr", 0) or 0,
            r.get("rolloff", 0) or 0, r.get("flatness", 0) or 0, r.get("sustain", 0) or 0,
            math.log(1.0 + (r.get("length", 0) or 0)),
        ]

    def _build_guess_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Auto-Guess")

        ctl = ttk.Frame(tab, padding=6)
        ctl.pack(fill=tk.X)
        ttk.Button(ctl, text="Run guess", command=self._run_guess).pack(side=tk.LEFT)
        self.guess_scope = tk.StringVar(value="Only 'Unclassified' + mismatches")
        ttk.Combobox(ctl, textvariable=self.guess_scope, state="readonly", width=30,
                     values=["Only 'Unclassified' + mismatches", "All one-shots"]).pack(side=tk.LEFT, padx=8)
        ttk.Button(ctl, text="Play selected", command=self._guess_play).pack(side=tk.LEFT)
        self.guess_summary = ttk.Label(ctl, text="Averages each named group's acoustics, then guesses the rest.",
                                       foreground="#888")
        self.guess_summary.pack(side=tk.RIGHT)

        wrap = ttk.Frame(tab)
        wrap.pack(fill=tk.BOTH, expand=True)
        cols = ("folder", "current", "guess", "conf", "note")
        tv = ttk.Treeview(wrap, columns=cols, show="tree headings")
        tv.heading("#0", text="File")
        tv.column("#0", width=240)
        for c, (label, w) in {"folder": ("Folder", 150), "current": ("Current group", 100),
                              "guess": ("Best guess", 100), "conf": ("Conf %", 60),
                              "note": ("Note", 160)}.items():
            tv.heading(c, text=label)
            tv.column(c, width=w, anchor=tk.W)
        vs = ttk.Scrollbar(wrap, orient=tk.VERTICAL, command=tv.yview)
        tv.configure(yscrollcommand=vs.set)
        vs.pack(side=tk.RIGHT, fill=tk.Y)
        tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tv.tag_configure("other", foreground="#1565c0")
        tv.tag_configure("mismatch", foreground="#c33")
        self.guess_tv = tv

    def _run_guess(self):
        if not self.records:
            messagebox.showinfo("Auto-Guess", "No analysis loaded yet.")
            return
        # One-shots only (loops are a different animal).
        recs = [r for r in self.records if (r.get("group") or "Unclassified") != "Loops/Patterns"]
        if len(recs) < 3:
            messagebox.showinfo("Auto-Guess", "Not enough one-shot samples.")
            return

        mat = np.array([self._feat_row(r) for r in recs], dtype=float)
        mn = mat.min(axis=0)
        rng = np.where((mat.max(axis=0) - mn) > 1e-12, mat.max(axis=0) - mn, 1.0)
        norm = (mat - mn) / rng

        # Group fingerprints = mean normalized feature vector of confidently named files.
        known = [i for i, r in enumerate(recs) if (r.get("group") or "Unclassified") != "Unclassified"]
        cents = {}
        for i in known:
            g = recs[i].get("group")
            cents.setdefault(g, []).append(norm[i])
        cents = {g: np.mean(v, axis=0) for g, v in cents.items() if len(v) >= 2}
        if not cents:
            messagebox.showinfo("Auto-Guess", "No named groups with ≥2 samples to learn from.")
            return
        gnames = list(cents.keys())
        cmat = np.array([cents[g] for g in gnames])

        scope_all = self.guess_scope.get() == "All one-shots"
        tv = self.guess_tv
        tv.delete(*tv.get_children())
        rows = []
        for i, r in enumerate(recs):
            d = np.linalg.norm(cmat - norm[i], axis=1)
            order = np.argsort(d)
            g1 = gnames[order[0]]
            d1 = d[order[0]]
            d2 = d[order[1]] if len(order) > 1 else d1 + 1.0
            conf = int(max(0.0, min(1.0, (d2 - d1) / (d2 + 1e-9))) * 100)
            cur = r.get("group") or "Unclassified"
            drum = " [drum-tag]" if r.get("audit") else ""
            if cur == "Unclassified":
                note, tag = f"OTHER → likely {g1}{drum}", "other"
            elif cur != g1:
                note, tag = f"named {cur}, looks like {g1}", "mismatch"
            else:
                note, tag = "consistent", ""
            if not scope_all and tag == "":
                continue
            rows.append((r, cur, g1, conf, note, tag))

        rows.sort(key=lambda x: (x[5] == "", -x[3]))
        for r, cur, g1, conf, note, tag in rows:
            tv.insert("", "end", text=r.get("name", ""), tags=(tag,) if tag else (),
                      values=(r.get("folder", ""), cur, g1, conf, note))
        self.guess_summary.config(
            text=f"learned {len(gnames)} fingerprints · {len(rows)} shown "
                 f"({sum(1 for x in rows if x[5]=='other')} Unclassified, "
                 f"{sum(1 for x in rows if x[5]=='mismatch')} mismatches)")

    def _guess_play(self):
        sel = self.guess_tv.selection()
        if not sel:
            return
        name = self.guess_tv.item(sel[0], "text")
        rec = next((r for r in self.records if r.get("name") == name), None)
        if rec:
            path = self._resolve_path(rec)
            if path:
                self._play_file(path)
