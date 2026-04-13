# SUB_APP_CSV_to_json_APP/csvtojson.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized CSV to JSON Converter.

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import orjson
import os
from loguru import logger

# --- EXTRACTED CORE MODULES ---
from core.csv_converter_engine import CSVConverterEngine
from core.header_config_ui import HeaderConfigUI
from core.json_preview_ui import JSONPreviewUI

class CSVToJSONApp(tk.Tk):
    """Orchestrates the CSV to JSON conversion application."""

    def __init__(self):
        super().__init__()
        self.title("CSV to JSON Converter")
        self.geometry("1200x800")
        self.csv_filepath = ""
        self.headers = []
        self._setup_ui()

    def _setup_ui(self):
        # 1. Top Controls
        top = tk.Frame(self, padx=10, pady=10); top.pack(fill=tk.X)
        tk.Label(top, text="Input CSV:").grid(row=0, column=0, sticky="W")
        self.csv_en = tk.Entry(top, width=50); self.csv_en.grid(row=0, column=1, padx=5)
        tk.Button(top, text="Browse...", command=self.load_csv).grid(row=0, column=2)

        tk.Label(top, text="Output JSON:").grid(row=1, column=0, sticky="W")
        self.json_en = tk.Entry(top, width=50); self.json_en.grid(row=1, column=1, padx=5)
        tk.Button(top, text="Browse...", command=self.save_json_dlg).grid(row=1, column=2)

        tk.Label(top, text="Root Key:").grid(row=2, column=0, sticky="W")
        self.root_en = tk.Entry(top, width=20); self.root_en.insert(0, "root"); self.root_en.grid(row=2, column=1, sticky="W", padx=5)

        btns = tk.Frame(top); btns.grid(row=3, column=0, columnspan=3, pady=10)
        tk.Button(btns, text="Load Headers", command=self.load_headers).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="Preview JSON", command=self.preview).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="Convert & Save", command=self.convert).pack(side=tk.LEFT, padx=5)

        # 2. Main Content (Split View)
        main = tk.Frame(self, padx=10, pady=10); main.pack(fill=tk.BOTH, expand=True)
        
        # Left: Header Config
        l_frame = tk.LabelFrame(main, text="Header Configuration", padx=5, pady=5)
        l_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canv = tk.Canvas(l_frame); canv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(l_frame, orient=tk.VERTICAL, command=canv.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y); canv.configure(yscrollcommand=vsb.set)
        self.h_frame = tk.Frame(canv); canv.create_window((0,0), window=self.h_frame, anchor="nw")
        self.h_frame.bind("<Configure>", lambda e: canv.configure(scrollregion=canv.bbox("all")))

        # Right: Preview
        r_frame = tk.LabelFrame(main, text="JSON Preview", padx=5, pady=5)
        r_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.preview_ui = JSONPreviewUI(r_frame)

    def load_csv(self):
        fp = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if fp:
            self.csv_en.delete(0, tk.END); self.csv_en.insert(0, fp); self.csv_filepath = fp
            self.json_en.delete(0, tk.END); self.json_en.insert(0, os.path.splitext(fp)[0] + ".json")

    def save_json_dlg(self):
        fp = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if fp: self.json_en.delete(0, tk.END); self.json_en.insert(0, fp)

    def load_headers(self):
        if not self.csv_filepath or not os.path.exists(self.csv_filepath):
            return messagebox.showerror("Error", "Select valid CSV.")
        try:
            df = pd.read_csv(self.csv_filepath, nrows=1, keep_default_na=False)
            self.headers = list(df.columns)
            self.header_ui = HeaderConfigUI(self.h_frame, self.headers, self.preview)
        except Exception as e:
            logger.exception(f"Header loading failed: {e}")
            messagebox.showerror("Error", str(e))

    def generate_data(self):
        try:
            df = pd.read_csv(self.csv_filepath, keep_default_na=False)
            h_map = self.header_ui.get_config_map()
            sort_cols = [h for h, configuration in h_map.items() if configuration["role"] in ["Hierarchical Key", "Value as Key", "Key Name and Value"]]
            df.sort_values(by=sort_cols, inplace=True, kind="stable")
            result = CSVConverterEngine.build_hierarchy(df, h_map, "root", self.headers)
            return {self.root_en.get(): result}
        except Exception as e:
            logger.exception(f"Generation failed: {e}")
            messagebox.showerror("Error", f"Generation failed: {e}")
            return None

    def preview(self):
        data = self.generate_data()
        if data: self.preview_ui.update(data)

    def convert(self):
        path = self.json_en.get()
        if not path: return messagebox.showerror("Error", "Specify output path.")
        data = self.generate_data()
        if data:
            try:
                with open(path, "wb") as f: f.write(orjson.dumps(data))
                messagebox.showinfo("Success", f"Saved to {path}")
            except Exception as e:
                logger.exception(f"Conversion or file saving failed: {e}")
                messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    CSVToJSONApp().mainloop()
