"""Flatten / Rename tab for the Sample Analyzer (RenameMixin).

Previews and applies a flatten + rename of a folder tree: encodes each file's
relative path into a flat name, optionally appends BPM, prepends the group /
subgroup, removes repeated words, sorts into subfolders, and auto-suffixes name
clashes so every target stays unique.
"""
import os
import re
import json
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config import DEFAULT_DIR


class RenameMixin:
    AUDIO_EXTS = (".wav", ".aif", ".aiff", ".aifc", ".mp3", ".flac", ".ogg", ".m4a")

    # .PEAK fields shown as columns in the renamer: (key, header, width).
    RENAME_PEAK_COLS = [
        ("group", "Group", 70), ("subgroup", "Subgroup", 105), ("timbre", "Timbre", 70),
        ("length_class", "Len tier", 60), ("root", "Root", 46), ("pitch", "Pitch", 55), ("length", "Len s", 50),
        ("transients", "Tr", 34), ("sustained", "Sust", 40), ("audit", "Audit", 44),
        ("bpm", "BPM", 46), ("channels", "Ch", 46), ("sample_rate", "SR", 50),
        ("bit_depth", "Bits", 38), ("harmonicity", "Harm", 46), ("centroid", "Bright", 55),
        ("complexity", "Cplx", 50), ("cluster", "Clu", 38), ("reason", "Reason", 170),
    ]

    def _build_rename_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Flatten / Rename")

        top = ttk.Frame(tab, padding=6)
        top.pack(fill=tk.X)
        ttk.Button(top, text="Pick Directory…", command=self._rename_pick).pack(side=tk.LEFT)
        self.rename_dir = tk.StringVar(value=DEFAULT_DIR if os.path.isdir(DEFAULT_DIR) else "No directory selected")
        ttk.Label(top, textvariable=self.rename_dir, foreground="#c47a1a", wraplength=360).pack(side=tk.LEFT, padx=8)

        opt = ttk.Frame(tab, padding=(6, 0))
        opt.pack(fill=tk.X)
        self.rename_flatten = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt, text="Flatten into the picked folder (move files up)",
                        variable=self.rename_flatten, command=self._rename_scan).pack(side=tk.LEFT)
        self.rename_audio_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt, text="Audio files only", variable=self.rename_audio_only,
                        command=self._rename_scan).pack(side=tk.LEFT, padx=12)

        drow = ttk.Frame(tab, padding=(6, 0))
        drow.pack(fill=tk.X)
        ttk.Button(drow, text="Destination…", command=self._rename_pick_dest).pack(side=tk.LEFT)
        self.rename_dest = tk.StringVar(value="/home/anthony/Documents/Renamed Samples")
        try:
            os.makedirs(self.rename_dest.get(), exist_ok=True)  # so the default routes on first preview
        except OSError:
            pass
        self.rename_copy = tk.BooleanVar(value=True)
        ttk.Checkbutton(drow, text="COPY into destination (keep originals)",
                        variable=self.rename_copy).pack(side=tk.LEFT, padx=6)
        ttk.Label(drow, textvariable=self.rename_dest, foreground="#2a7", wraplength=300).pack(side=tk.LEFT, padx=6)
        ttk.Button(drow, text="Clear", command=lambda: (self.rename_dest.set(""), self._rename_scan())).pack(side=tk.RIGHT)

        grow = ttk.Frame(tab, padding=(6, 0))
        grow.pack(fill=tk.X)
        self.rename_group_sort = tk.BooleanVar(value=False)
        ttk.Checkbutton(grow, text="Sort into subfolders by", variable=self.rename_group_sort,
                        command=self._rename_scan).pack(side=tk.LEFT)
        self.rename_group_field = tk.StringVar(value="Group")
        gcb = ttk.Combobox(grow, textvariable=self.rename_group_field, state="readonly", width=10,
                           values=["Group", "Subgroup", "Timbre", "Cluster"])
        gcb.pack(side=tk.LEFT, padx=4)
        gcb.bind("<<ComboboxSelected>>", lambda e: self._rename_scan())
        ttk.Label(grow, text="then").pack(side=tk.LEFT, padx=(8, 2))
        self.rename_group_field2 = tk.StringVar(value="(none)")
        gcb2 = ttk.Combobox(grow, textvariable=self.rename_group_field2, state="readonly", width=10,
                            values=["(none)", "Group", "Subgroup", "Timbre", "Cluster", "Len tier"])
        gcb2.pack(side=tk.LEFT, padx=4)
        gcb2.bind("<<ComboboxSelected>>", lambda e: self._rename_scan())
        self.rename_add_root = tk.BooleanVar(value=False)
        ttk.Checkbutton(grow, text="Append ROOT-note", variable=self.rename_add_root,
                        command=self._rename_scan).pack(side=tk.LEFT, padx=(16, 4))
        self.rename_add_bpm = tk.BooleanVar(value=False)
        ttk.Checkbutton(grow, text="Append ###BPM (when > 10)", variable=self.rename_add_bpm,
                        command=self._rename_scan).pack(side=tk.LEFT, padx=(16, 4))

        grow2 = ttk.Frame(tab, padding=(6, 0))
        grow2.pack(fill=tk.X)
        self.rename_prepend_group = tk.BooleanVar(value=False)
        ttk.Checkbutton(grow2, text="Prepend", variable=self.rename_prepend_group,
                        command=self._rename_scan).pack(side=tk.LEFT)
        self.rename_prepend_fields = tk.StringVar(value="group")
        pcb = ttk.Combobox(grow2, textvariable=self.rename_prepend_fields, state="readonly", width=24,
                           values=["group", "group - subgroup", "group - subgroup - timbre"])
        pcb.pack(side=tk.LEFT, padx=4)
        pcb.bind("<<ComboboxSelected>>", lambda e: self._rename_scan())
        ttk.Label(grow2, text='to file names (e.g. "Snare - Acoustic - ")').pack(side=tk.LEFT, padx=(2, 0))
        self.rename_dedup = tk.BooleanVar(value=False)
        ttk.Checkbutton(grow2, text="Remove repeated words", variable=self.rename_dedup,
                        command=self._rename_scan).pack(side=tk.LEFT, padx=(16, 4))

        ctl = ttk.Frame(tab, padding=(6, 4))
        ctl.pack(fill=tk.X)
        ttk.Button(ctl, text="Rescan", command=self._rename_scan).pack(side=tk.LEFT)
        ttk.Button(ctl, text="Apply Rename", command=self._rename_apply).pack(side=tk.LEFT, padx=8)
        self.rename_summary = ttk.Label(ctl, text="Pick a directory to preview.", foreground="#888")
        self.rename_summary.pack(side=tk.RIGHT)

        wrap = ttk.Frame(tab)
        wrap.pack(fill=tk.BOTH, expand=True)
        cols = ("old", "new", "err") + tuple(k for k, _h, _w in self.RENAME_PEAK_COLS)
        tv = ttk.Treeview(wrap, columns=cols, show="headings")
        tv.heading("old", text="Old folder structure  (relative)", command=lambda: self._tv_sort(tv, "old", False))
        tv.column("old", width=260, anchor=tk.W)
        tv.heading("new", text="New file name", command=lambda: self._tv_sort(tv, "new", False))
        tv.column("new", width=240, anchor=tk.W)
        tv.heading("err", text="Note", command=lambda: self._tv_sort(tv, "err", False))
        tv.column("err", width=100, anchor=tk.W)
        for k, h, w in self.RENAME_PEAK_COLS:
            tv.heading(k, text=h, command=lambda c=k: self._tv_sort(tv, c, False))
            tv.column(k, width=w, anchor=tk.W, stretch=False)
        vs = ttk.Scrollbar(wrap, orient=tk.VERTICAL, command=tv.yview)
        hs = ttk.Scrollbar(wrap, orient=tk.HORIZONTAL, command=tv.xview)
        tv.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        vs.pack(side=tk.RIGHT, fill=tk.Y)
        hs.pack(side=tk.BOTTOM, fill=tk.X)
        tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tv.tag_configure("suffixed", foreground="#3a7ca5")  # auto-numbered (info, not an error)
        tv.tag_configure("noop", foreground="#777")
        self.rename_tv = tv
        self.rename_map = []

    def _peak_for(self, abspath):
        """Find the analysis record for a file: prefer its sidecar <stem>.PEAK,
        else fall back to the loaded aggregate records (matched by path).
        Returns a dict or None (guards against a .PEAK file matching itself,
        whose contents are a list, and other non-record JSON)."""
        side = os.path.splitext(abspath)[0] + ".PEAK"
        if side != abspath and os.path.isfile(side):
            try:
                with open(side, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        r = self.records_by_path.get(abspath)
        return r if isinstance(r, dict) else None

    @staticmethod
    def _safe_folder(name):
        return re.sub(r'[\\/:*?"<>|]+', "_", str(name)).strip() or "Unsorted"

    # Name/keyword → (group, subgroup) rules, mirroring the Rust analyzer's
    # categorize() so the renamer can still sort by name (e.g. "Bass Drum" → Kick)
    # when a file has no .PEAK record. (group, subgroup, phrases, abbrev-tokens).
    _NAME_RULES = [
        ("IR", "", ["impulse response", "impulse", "convolution", "convol", "cabinet", "guitar cab", "reverb ir"], ["ir", "cab", "conv"]),
        ("Kick", "", ["kick", "kik", "bass drum", "bassdrum"], ["bd", "kk", "kik", "kic", "kck"]),
        ("Snare", "", ["snare"], ["sd", "sn", "snr"]),
        ("HiHat", "", ["hihat", "hi hat", "closed hat", "open hat", "pedal hat", "hat"], ["hh", "chh", "ohh", "ch", "oh", "ph"]),
        ("Ride", "", ["ride bell", "ride cymbal", "ride"], ["rd", "rdcym"]),
        ("Cymbal", "", ["crash cymbal", "splash cymbal", "cymbal", "crash", "splash"], ["cy", "cym", "crsh"]),
        ("Clap", "", ["handclap", "hand clap", "clap"], ["cp", "clp"]),
        ("Rim", "", ["rimshot", "rim shot", "cross stick", "crossstick", "rim"], ["rs", "rm"]),
        ("Tom Hi", "", ["high tom", "hi tom", "rack tom 1", "tom 1", "hitom"], ["ht", "hitom"]),
        ("Tom Mid", "", ["mid tom", "middle tom", "rack tom 2", "tom 2", "midtom"], ["mt", "midtom"]),
        ("Tom Lo", "", ["low tom", "floor tom", "tom 3", "lotom"], ["lt", "ft", "lotom"]),
        ("Tom", "", ["tom"], ["tm"]),
        ("Perc", "Cowbell", ["cowbell", "cow bell"], ["cb", "cow", "cowb"]),
        ("Perc", "Conga", ["conga", "tumba", "quinto"], ["cg", "con", "cng"]),
        ("Perc", "Bongo", ["bongo"], ["bng"]),
        ("Perc", "Clave", ["claves", "clave"], ["cv", "clv"]),
        ("Perc", "Shaker", ["shaker", "maracas", "cabasa"], ["shk", "sh"]),
        ("Perc", "Block", ["woodblock", "wood block", "block"], ["wb"]),
        ("Perc", "", ["percussion", "auxiliary", "perc"], ["prc"]),
        ("Guitar", "", ["guitar", "gtr", "acoustic gt", "electric gt"], ["gtr", "gt"]),
        ("Strings", "", ["strings", "string", "violin", "viola", "cello", "orchestra", "ensemble", "pizz", "arco"], []),
        ("Bass", "", ["bass", "sub bass"], ["sub"]),
        ("Vocal", "", ["vocal", "voice", "vox"], ["vx"]),
        ("Keyboards", "Electric Piano", ["electric piano", "rhodes", "wurlitzer", "wurli", "e-piano", "epiano"], ["ep"]),
        ("Keyboards", "Organ", ["organ", "hammond"], ["org"]),
        ("Keyboards", "Clav", ["clavinet", "clav"], []),
        ("Keyboards", "Piano", ["grand piano", "upright piano", "piano"], ["pno"]),
        ("Keyboards", "Synth", ["synthesizer", "synth"], ["syn"]),
        ("Keyboards", "", ["keyboard", "keys"], ["kb", "keyb"]),
        ("Scratch", "", ["scratches", "scratch"], ["scr"]),
        ("DJ", "", ["turntable", "deck"], ["dj"]),
        ("FX", "", ["sound effect", "foley", "atmosphere", "atmos", "riser", "sweep", "noise",
                    "impact", "boom", "zap", "glitch", "drone", "whoosh", "reverse", "downlifter",
                    "uplifter", "sfx", "fx"], ["fx", "sfx"]),
        ("Loops/Patterns", "", ["loop", "groove", "beat"], ["lp"]),
    ]

    @staticmethod
    def _normalize_name(name):
        """Lower-case, non-alnum runs → spaces, split letter↔digit boundaries
        ('Tom2' → 'tom 2') — mirrors the Rust analyzer's normalize_name."""
        out, prev = [], 0  # prev: 0=sep, 1=alpha, 2=digit
        for c in name.lower():
            kind = 1 if (c.isascii() and c.isalpha()) else 2 if (c.isascii() and c.isdigit()) else 0
            if kind == 0:
                if out and out[-1] != " ":
                    out.append(" ")
            else:
                if prev not in (0, kind):
                    out.append(" ")
                out.append(c)
            prev = kind
        return "".join(out)

    @classmethod
    def _classify_name(cls, text):
        """Fallback (group, subgroup) from a file path's keywords."""
        norm = cls._normalize_name(text)
        if "cym" in norm:
            return ("Cymbal", "")
        toks = set(norm.split())
        for group, sub, phrases, abbrevs in cls._NAME_RULES:
            if any(p in norm for p in phrases) or any(a in toks for a in abbrevs):
                return (group, sub)
        return ("Unclassified", "")

    @staticmethod
    def _dedup_words(stem):
        """Drop later word repeats (case-insensitive) by prefix/stem: a word is
        dropped when an already-seen word (>=3 chars) is a prefix of it, so
        'Snare' also swallows 'Snaredrums' and 'SNAREDRUM'. Splits on ' - ', '_',
        spaces and '-', so 'BASSDRUM - Bassdrum-01' keeps the trailing '01'; a
        kept word keeps the delimiter that originally followed it."""
        tokens = re.split(r'( - | |_|-)', stem)
        words = tokens[0::2]
        delims = tokens[1::2]              # delims[i] sits between words[i] and words[i+1]
        seen = []                          # kept words, lowercased, in order
        out_words, out_delims, pending = [], [], None
        for i, w in enumerate(words):
            following = delims[i] if i < len(delims) else None
            key = w.strip().lower()
            dup = key and any(key == s or (len(s) >= 3 and key.startswith(s)) for s in seen)
            if w and dup:
                continue                  # drop the repeat; keep `pending` for the next kept word
            if key:
                seen.append(key)
            if out_words:
                out_delims.append(pending if pending is not None else " - ")
            out_words.append(w)
            pending = following
        result = out_words[0] if out_words else ""
        for d, w in zip(out_delims, out_words[1:]):
            result += d + w
        return re.sub(r'^(?: - | |_|-)+|(?: - | |_|-)+$', "", result)

    def _tv_sort(self, tv, col, reverse):
        """Sort a Treeview by a clicked column (numeric-aware, toggles order)."""
        items = [(tv.set(iid, col), iid) for iid in tv.get_children("")]

        def keyf(pair):
            v = pair[0]
            try:
                return (0, float(v))
            except (TypeError, ValueError):
                return (1, str(v).lower())
        items.sort(key=keyf, reverse=reverse)
        for idx, (_v, iid) in enumerate(items):
            tv.move(iid, "", idx)
        tv.heading(col, command=lambda: self._tv_sort(tv, col, not reverse))

    def _peak_cols(self, r):
        if not r:
            return ["" for _ in self.RENAME_PEAK_COLS]

        def fmt(key):
            v = r.get(key)
            if v is None:
                return ""
            if key in ("sustained", "audit"):
                return "yes" if v else ""
            if key == "channels":
                return {1: "mono", 2: "stereo"}.get(v, str(v))
            if key in ("pitch", "centroid", "complexity", "sample_rate"):
                return f"{v:.0f}"
            if key in ("length", "harmonicity", "bpm"):
                return f"{v:.2f}" if v else ("" if key == "bpm" else f"{v:.2f}")
            return str(v)
        return [fmt(k) for k, _h, _w in self.RENAME_PEAK_COLS]

    def _rename_pick(self):
        d = filedialog.askdirectory(title="Select folder to flatten / rename")
        if d:
            self.rename_dir.set(d)
            self._rename_scan()

    def _rename_pick_dest(self):
        d = filedialog.askdirectory(title="Select destination folder for renamed files")
        if d:
            self.rename_dest.set(d)
            self._rename_scan()

    def _encode_name(self, root, abspath):
        """B/C/D.wav (relative to the picked root, root name NOT included)
        -> 'B - C - D.wav'."""
        rel = os.path.relpath(abspath, root)
        parts = [p for p in rel.replace("\\", "/").split("/") if p]
        return " - ".join(parts)

    def _rename_scan(self):
        tv = self.rename_tv
        tv.delete(*tv.get_children())
        self.rename_map = []
        root = self.rename_dir.get()
        if not os.path.isdir(root):
            return
        flatten = self.rename_flatten.get()
        audio_only = self.rename_audio_only.get()
        dest = self.rename_dest.get()
        dest_ok = bool(dest) and os.path.isdir(dest)
        sort_grp = self.rename_group_sort.get()
        FMAP = {"Group": "group", "Subgroup": "subgroup", "Timbre": "timbre",
                "Cluster": "cluster", "Len tier": "length_class"}
        gfield = FMAP.get(self.rename_group_field.get(), "group")
        gfield2 = FMAP.get(self.rename_group_field2.get())  # None for "(none)"
        add_root = self.rename_add_root.get()
        add_bpm = self.rename_add_bpm.get()
        prepend_group = self.rename_prepend_group.get()
        prepend_keys = {
            "group": ["group"],
            "group - subgroup": ["group", "subgroup"],
            "group - subgroup - timbre": ["group", "subgroup", "timbre"],
        }.get(self.rename_prepend_fields.get(), ["group"])
        dedup = self.rename_dedup.get()
        targets = {}   # new_abs -> count (collision detection)
        rows = []
        for dirpath, _dirs, files in os.walk(root):
            for fn in sorted(files):
                if fn.startswith("."):
                    continue
                if fn.lower().endswith(".peak"):
                    continue  # analysis sidecars aren't samples
                if audio_only and not fn.lower().endswith(self.AUDIO_EXTS):
                    continue
                abspath = os.path.join(dirpath, fn)
                new_name = self._encode_name(root, abspath)
                rec = self._peak_for(abspath)
                # Effective group/subgroup: prefer the PEAK record, else fall back
                # to a name-based classification of the path, so e.g. "Bass Drum"
                # sorts to Kick even when the file has no analysis record.
                egroup = (rec.get("group") if rec else "") or ""
                esub = (rec.get("subgroup") if rec else "") or ""
                if not egroup or egroup == "Unclassified":
                    fg, fsg = self._classify_name(os.path.relpath(abspath, root))
                    if fg != "Unclassified" or not egroup:
                        egroup = fg
                    if not esub:
                        esub = fsg
                # Append ROOT-<note> before the extension (when a root is known),
                # ahead of the BPM tag so the name reads "… - ROOT-A3 - 120BPM".
                if add_root and rec and rec.get("root"):
                    stem, ext = os.path.splitext(new_name)
                    new_name = f"{stem} - ROOT-{rec['root']}{ext}"
                # Append the BPM before the extension (any real tempo, bpm > 10).
                if add_bpm and rec and (rec.get("bpm") or 0) > 10:
                    stem, ext = os.path.splitext(new_name)
                    new_name = f"{stem} - {round(rec['bpm'])}BPM{ext}"
                # Prepend the category (e.g. "Snare - " or "Snare - Acoustic - ").
                # Strip the group out of the subgroup so "Snare - Snare Medium"
                # collapses to "Snare - Medium" (independent of the dedup option).
                if prepend_group:
                    kv = {"group": egroup, "subgroup": esub}
                    vals = [self._safe_folder(kv[k]) for k in prepend_keys if kv.get(k)]
                    if vals:
                        prefix = self._dedup_words(" - ".join(vals))
                        new_name = prefix + " - " + new_name
                # Collapse repeated words (case-insensitive), keeping the extension.
                if dedup:
                    stem, ext = os.path.splitext(new_name)
                    new_name = self._dedup_words(stem) + ext
                base = dest if dest_ok else (root if flatten else dirpath)
                sub_parts = []
                if sort_grp:
                    def folder_for(field):
                        if field == "group":
                            v = egroup
                        elif field == "subgroup":
                            v = esub
                        else:
                            v = rec.get(field) if rec else None
                        return self._safe_folder(v) if v not in (None, "") else "Unsorted"
                    f1 = folder_for(gfield)
                    sub_parts.append(f1)
                    # Strip the group out of the subgroup folder so
                    # Loop/"Loop Guitar" -> Loop/Guitar and Loop/Loop -> Loop.
                    if gfield2:
                        combined = self._dedup_words(f1 + " - " + folder_for(gfield2))
                        f2 = combined[len(f1):].lstrip(" -_")
                        if f2 and f2.lower() != f1.lower():
                            sub_parts.append(f2)
                if sub_parts:
                    dest_dir = os.path.join(base, *sub_parts)
                    disp_new = os.path.join(*sub_parts, new_name)
                else:
                    dest_dir = base
                    disp_new = new_name
                new_abs = os.path.join(dest_dir, new_name)
                rel = os.path.relpath(abspath, root)
                rows.append([abspath, rel, disp_new, new_abs, rec])
                targets[new_abs] = targets.get(new_abs, 0) + 1

        n_change = n_noop = n_suffixed = 0
        used = set()
        for r in rows:                       # pre-seed no-op targets so we don't clobber them
            if r[3] == r[0]:
                used.add(r[3])
        for r in rows:
            abspath, rel, disp_new, new_abs, rec = r
            note = ""
            if new_abs == abspath:
                tags = ("noop",); n_noop += 1
            else:
                if targets[new_abs] > 1:
                    # Two files reduce to the same name: append a numeric suffix
                    # (-2, -3, …) so each target stays unique. This is resolved
                    # automatically — it is NOT an error.
                    uniq = self._dedupe(new_abs, used)
                    if uniq != new_abs:
                        uname = os.path.basename(uniq)
                        parent = os.path.dirname(disp_new)
                        disp_new = os.path.join(parent, uname) if parent else uname
                        new_abs = uniq
                        r[2], r[3] = disp_new, new_abs   # keep rename_map in sync for apply
                        note = "auto-numbered"; n_suffixed += 1
                used.add(new_abs)
                tags = ("suffixed",) if note else ()
                n_change += 1
            tv.insert("", "end", values=(rel, disp_new, note, *self._peak_cols(rec)), tags=tags)
        self.rename_map = rows
        self.rename_summary.config(
            text=f"{len(rows)} files · {n_change} to rename · {n_noop} unchanged · "
                 f"{n_suffixed} auto-numbered to keep names unique")

    def _rename_apply(self):
        if not self.rename_map:
            messagebox.showinfo("Apply Rename", "Nothing to rename — pick a directory first.")
            return
        flatten = self.rename_flatten.get()
        todo = [r for r in self.rename_map if r[3] != r[0]]
        if not todo:
            messagebox.showinfo("Apply Rename", "All files are already named correctly.")
            return
        dest = self.rename_dest.get()
        copy = self.rename_copy.get()
        verb = "COPIED" if copy else "MOVED"
        if dest and os.path.isdir(dest):
            where = f"Files will be {verb} to:\n{dest}\n"
        elif flatten:
            where = f"Files will be {verb} up into the picked folder.\n"
        else:
            where = ("Renamed copies made in place.\n" if copy else "Files renamed in place.\n")
        if self.rename_group_sort.get():
            where += f"Sorted into subfolders by {self.rename_group_field.get()}.\n"
        if not messagebox.askyesno(
                "Apply Rename",
                f"{'Copy' if copy else 'Rename'} {len(todo)} file(s)?\n\n" + where + "This modifies files on disk. Continue?"):
            return

        used = set()
        # Pre-seed with files that keep their name (no-ops) so we don't clobber them.
        for abspath, rel, _disp, new_abs, _rec in self.rename_map:
            if new_abs == abspath:
                used.add(new_abs)
        ok = fail = 0
        errors = []
        for abspath, rel, _disp, new_abs, _rec in todo:
            target = self._dedupe(new_abs, used)
            used.add(target)
            try:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                if copy:
                    shutil.copy2(abspath, target)
                else:
                    shutil.move(abspath, target)
                ok += 1
            except Exception as e:
                fail += 1
                errors.append(f"{rel}: {e}")
        msg = f"{'Copied' if copy else 'Renamed'} {ok} file(s)."
        if fail:
            msg += f"\n{fail} failed:\n" + "\n".join(errors[:8])
        messagebox.showinfo("Apply Rename", msg)
        self._rename_scan()

    @staticmethod
    def _dedupe(path, used):
        if path not in used and not os.path.exists(path):
            return path
        base, ext = os.path.splitext(path)
        i = 2
        while True:
            cand = f"{base}-{i}{ext}"
            if cand not in used and not os.path.exists(cand):
                return cand
            i += 1
