import tkinter as tk
from tkinter import ttk

class HeaderConfigUI:
    """Manages the dynamic row of widgets for each CSV header."""

    def __init__(self, parent, headers, on_change_callback):
        self.parent = parent
        self.headers = headers
        self.on_change = on_change_callback
        self.widgets = {}
        self._setup_table()

    def _setup_table(self):
        for w in self.parent.winfo_children(): w.destroy()
        
        cols = [("JSON Key Name", 0), ("Role", 1), ("Nested Under", 2), ("Part Name (e.g., 'contents')", 3)]
        for text, col in cols:
            tk.Label(self.parent, text=text, font=("Arial", 10, "bold")).grid(row=0, column=col, padx=5, pady=2)

        roles = ["Hierarchical Key", "Sub Key", "Simple Value", "Value as Key", "Key Name and Value", "Skip"]
        
        for i, header in enumerate(self.headers):
            row = i + 1
            h_entry = tk.Entry(self.parent, width=20)
            h_entry.insert(0, header)
            h_entry.grid(row=row, column=0, sticky="W", padx=5, pady=2)

            role_var = tk.StringVar()
            role_dd = ttk.Combobox(self.parent, textvariable=role_var, state="readonly", values=roles)
            role_dd.grid(row=row, column=1, padx=5, pady=2)

            nest_var = tk.StringVar()
            nest_dd = ttk.Combobox(self.parent, textvariable=nest_var, state="readonly", values=["root"])
            nest_dd.grid(row=row, column=2, padx=5, pady=2)

            part_entry = tk.Entry(self.parent, width=25)
            part_entry.grid(row=row, column=3, padx=5, pady=2)

            self.widgets[header] = {
                "header_entry": h_entry, "role_var": role_var,
                "nested_under_var": nest_var, "nested_under_dropdown": nest_dd,
                "part_name_entry": part_entry
            }

            def toggle(e, r_dd=role_dd, p_en=part_entry):
                p_en["state"] = "normal" if r_dd.get() in ["Hierarchical Key", "Key Name and Value"] else "disabled"
                if p_en["state"] == "disabled": p_en.delete(0, tk.END)
                self.update_dropdowns()
                self.on_change()

            role_dd.bind("<<ComboboxSelected>>", toggle)

    def update_dropdowns(self):
        parents = ["root"]
        for h, w in self.widgets.items():
            if w["role_var"].get() in ["Hierarchical Key", "Value as Key", "Key Name and Value"]:
                parents.append(h)
        for h, w in self.widgets.items():
            w["nested_under_dropdown"]["values"] = parents
            if w["nested_under_var"].get() not in parents: w["nested_under_var"].set("root")

    def get_config_map(self):
        h_map = {}
        for h, w in self.widgets.items():
            role = w["role_var"].get()
            h_map[h] = {
                "original_header": h,
                "json_key": w["header_entry"].get() if role != "Value as Key" else None,
                "role": role,
                "nested_under": w["nested_under_var"].get(),
                "part_name": w["part_name_entry"].get() or "parts"
            }
            if role == "Value as Key": h_map[h]["json_key"] = w["header_entry"].get()
        return h_map
