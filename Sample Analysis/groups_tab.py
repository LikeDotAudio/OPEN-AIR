"""Groups / CSV tab for the Sample Analyzer (GroupsMixin)."""
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class GroupsMixin:
    GROUP_COLS = ("folder", "reason", "timbre", "cluster", "pitch", "length", "tr")

    def _build_groups_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Groups / CSV")

        ctl = ttk.Frame(tab, padding=6)
        ctl.pack(fill=tk.X)
        ttk.Label(ctl, text="Group by:").pack(side=tk.LEFT, padx=(0, 4))
        self.group_by = tk.StringVar(value="Name group")
        cb = ttk.Combobox(ctl, textvariable=self.group_by, state="readonly", width=13,
                          values=["Name group", "Timbre", "Cluster"])
        cb.pack(side=tk.LEFT, padx=4)
        cb.bind("<<ComboboxSelected>>", lambda e: self._rebuild_groups())
        ttk.Button(ctl, text="Expand all", command=lambda: self._groups_expand(True)).pack(side=tk.LEFT, padx=(10, 2))
        ttk.Button(ctl, text="Collapse all", command=lambda: self._groups_expand(False)).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctl, text="Export CSV…", command=self._export_csv).pack(side=tk.LEFT, padx=(10, 2))
        self.groups_summary = ttk.Label(ctl, text="No analysis yet", foreground="#888")
        self.groups_summary.pack(side=tk.RIGHT)

        wrap = ttk.Frame(tab)
        wrap.pack(fill=tk.BOTH, expand=True)
        tv = ttk.Treeview(wrap, columns=self.GROUP_COLS, show="tree headings")
        tv.heading("#0", text="Group / File")
        tv.column("#0", width=260, stretch=True)
        heads = {"folder": ("Folder", 160), "reason": ("Reason in group", 180), "timbre": ("Timbre", 90),
                 "cluster": ("Clust", 50), "pitch": ("Pitch", 60), "length": ("Len s", 60), "tr": ("Trans", 50)}
        for c in self.GROUP_COLS:
            label, w = heads[c]
            tv.heading(c, text=label)
            tv.column(c, width=w, anchor=tk.W)
        vs = ttk.Scrollbar(wrap, orient=tk.VERTICAL, command=tv.yview)
        tv.configure(yscrollcommand=vs.set)
        vs.pack(side=tk.RIGHT, fill=tk.Y)
        tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.groups_tv = tv

    def _group_key(self, rec):
        by = self.group_by.get()
        if by == "Timbre":
            return rec.get("timbre") or "Other"
        if by == "Cluster":
            return "Cluster " + str(rec.get("cluster", -1))
        return rec.get("group") or "Other"

    def _rebuild_groups(self):
        tv = self.groups_tv
        tv.delete(*tv.get_children())
        buckets = {}
        for r in self.records:
            buckets.setdefault(self._group_key(r), []).append(r)
        for g in sorted(buckets):
            rows = buckets[g]
            parent = tv.insert("", "end", text=f"{g}  ({len(rows)})", open=False,
                               values=("", "", "", "", "", "", ""))
            for r in sorted(rows, key=lambda x: x.get("name", "")):
                tv.insert(parent, "end", text=r.get("name", ""), values=(
                    r.get("folder", ""), r.get("reason", ""), r.get("timbre", ""),
                    r.get("cluster", ""), f"{r.get('pitch', 0):.0f}",
                    f"{r.get('length', 0):.2f}", r.get("transients", "")))
        self.groups_summary.config(text=f"{len(self.records)} files · {len(buckets)} groups")

    def _groups_expand(self, opened):
        for item in self.groups_tv.get_children():
            self.groups_tv.item(item, open=opened)

    def _export_csv(self):
        if not self.records:
            messagebox.showinfo("Export CSV", "No analysis loaded yet.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile="sample_groups.csv",
            filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if not path:
            return
        cols = ["group_dimension", "group", "name", "folder", "reason", "timbre", "cluster",
                "pitch", "complexity", "centroid", "harmonicity", "attack", "length",
                "transients", "bpm", "sample_rate", "bit_depth"]
        by = self.group_by.get()
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(cols)
                for r in sorted(self.records, key=lambda x: (self._group_key(x), x.get("name", ""))):
                    w.writerow([by, self._group_key(r)] + [r.get(c, "") for c in
                                ["name", "folder", "reason", "timbre", "cluster", "pitch",
                                 "complexity", "centroid", "harmonicity", "attack", "length",
                                 "transients", "bpm", "sample_rate", "bit_depth"]])
            messagebox.showinfo("Export CSV", f"Wrote {len(self.records)} rows to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export CSV", str(e))
