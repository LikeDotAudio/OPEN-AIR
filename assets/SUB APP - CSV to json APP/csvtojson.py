import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import orjson
import os
import sys
import io
import re


class CSVToJSONApp(tk.Tk):
    """
    A Tkinter application to convert a CSV file to a nested JSON structure
    with dynamic grouping capabilities and a JSON preview feature.
    """

    def __init__(self):
        super().__init__()
        self.title("CSV to JSON Converter")
        self.geometry("1200x800")

        self.csv_filepath = ""
        self.headers = []
        self.header_widgets = {}

        self.setup_frames()
        self.create_widgets()

    def setup_frames(self):
        """Creates the main frames for organizing the UI."""
        self.top_frame = tk.Frame(self, padx=10, pady=10)
        self.top_frame.pack(fill=tk.X)

        self.main_content_frame = tk.Frame(self, padx=10, pady=10)
        self.main_content_frame.pack(fill=tk.BOTH, expand=True)

        self.header_config_frame = tk.LabelFrame(
            self.main_content_frame, text="Header Configuration", padx=10, pady=10
        )
        self.header_config_frame.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5
        )

        self.output_frame = tk.LabelFrame(
            self.main_content_frame, text="JSON Output", padx=10, pady=10
        )
        self.output_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.headers_canvas = tk.Canvas(self.header_config_frame)
        self.headers_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.headers_scrollbar = ttk.Scrollbar(
            self.header_config_frame,
            orient=tk.VERTICAL,
            command=self.headers_canvas.yview,
        )
        self.headers_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.headers_canvas.configure(yscrollcommand=self.headers_scrollbar.set)
        self.headers_frame = tk.Frame(self.headers_canvas)
        self.headers_canvas.create_window(
            (0, 0), window=self.headers_frame, anchor="nw"
        )

        self.headers_frame.bind(
            "<Configure>",
            lambda event: self.headers_canvas.configure(
                scrollregion=self.headers_canvas.bbox("all")
            ),
        )

        # Notebook for Treeview and Raw JSON view
        self.output_notebook = ttk.Notebook(self.output_frame)
        self.output_notebook.pack(fill=tk.BOTH, expand=True)

        # Treeview tab
        tree_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(tree_frame, text="Structured View")
        self.treeview = ttk.Treeview(
            tree_frame, columns=("Value"), show="tree headings"
        )
        self.treeview.heading("#0", text="Key")
        self.treeview.heading("Value", text="Value")
        self.treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.treeview_scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.treeview.yview
        )
        self.treeview.configure(yscrollcommand=self.treeview_scrollbar.set)
        self.treeview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Raw JSON tab
        raw_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(raw_frame, text="Raw JSON")
        self.raw_json_text = tk.Text(raw_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.raw_json_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.raw_json_scrollbar = ttk.Scrollbar(
            raw_frame, orient=tk.VERTICAL, command=self.raw_json_text.yview
        )
        self.raw_json_text.configure(yscrollcommand=self.raw_json_scrollbar.set)
        self.raw_json_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_widgets(self):
        """Creates and places all the widgets in the application window."""
        tk.Label(self.top_frame, text="Input CSV File:").grid(
            row=0, column=0, sticky="W", padx=5, pady=2
        )
        self.csv_path_entry = tk.Entry(self.top_frame, width=50)
        self.csv_path_entry.grid(row=0, column=1, padx=5, pady=2)
        self.csv_browse_button = tk.Button(
            self.top_frame, text="Browse...", command=self.load_csv_file
        )
        self.csv_browse_button.grid(row=0, column=2, padx=5, pady=2)

        tk.Label(self.top_frame, text="Output JSON File:").grid(
            row=1, column=0, sticky="W", padx=5, pady=2
        )
        self.json_path_entry = tk.Entry(self.top_frame, width=50)
        self.json_path_entry.grid(row=1, column=1, padx=5, pady=2)
        self.json_browse_button = tk.Button(
            self.top_frame, text="Browse...", command=self.save_json_file
        )
        self.json_browse_button.grid(row=1, column=2, padx=5, pady=2)

        tk.Label(self.top_frame, text="Root JSON Key Name:").grid(
            row=2, column=0, sticky="W", padx=5, pady=2
        )
        self.root_name_entry = tk.Entry(self.top_frame, width=20)
        self.root_name_entry.insert(0, "root")
        self.root_name_entry.grid(row=2, column=1, sticky="W", padx=5, pady=2)

        self.load_button = tk.Button(
            self.top_frame, text="Load Headers", command=self.load_headers
        )
        self.load_button.grid(row=3, column=0, pady=10)
        self.preview_button = tk.Button(
            self.top_frame, text="Preview JSON", command=self.preview_json
        )
        self.preview_button.grid(row=3, column=1, pady=10)
        self.convert_button = tk.Button(
            self.top_frame, text="Convert to JSON", command=self.convert_to_json
        )
        self.convert_button.grid(row=3, column=2, pady=10)

        self.headers_canvas.update_idletasks()
        self.headers_canvas.config(scrollregion=self.headers_canvas.bbox("all"))

    def load_csv_file(self):
        """Opens a file dialog to select the input CSV file."""
        filepath = filedialog.askopenfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
        )
        if filepath:
            self.csv_path_entry.delete(0, tk.END)
            self.csv_path_entry.insert(0, filepath)
            self.csv_filepath = filepath
            filename = os.path.basename(filepath)
            default_json_name = os.path.splitext(filename)[0] + ".json"
            self.json_path_entry.delete(0, tk.END)
            self.json_path_entry.insert(0, default_json_name)

    def save_json_file(self):
        """Opens a file dialog to specify the output JSON file path."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON files", "*.json")]
        )
        if filepath:
            self.json_path_entry.delete(0, tk.END)
            self.json_path_entry.insert(0, filepath)

    def load_headers(self):
        """
        Reads headers from the selected CSV and creates UI controls for each,
        including grouping options.
        """
        for widget in self.headers_frame.winfo_children():
            widget.destroy()

        self.headers.clear()
        self.header_widgets.clear()

        if not self.csv_filepath or not os.path.exists(self.csv_filepath):
            messagebox.showerror("🔴 ERROR", "Please select a valid CSV file.")
            return

        try:
            df = pd.read_csv(self.csv_filepath, nrows=1, keep_default_na=False)
            self.headers = list(df.columns)

            # Create a row of controls for each header
            tk.Label(
                self.headers_frame, text="JSON Key Name", font=("Arial", 10, "bold")
            ).grid(row=0, column=0, padx=5, pady=2)
            tk.Label(self.headers_frame, text="Role", font=("Arial", 10, "bold")).grid(
                row=0, column=1, padx=5, pady=2
            )
            tk.Label(
                self.headers_frame, text="Nested Under", font=("Arial", 10, "bold")
            ).grid(row=0, column=2, padx=5, pady=2)
            tk.Label(
                self.headers_frame,
                text="Part Name (e.g., 'contents')",
                font=("Arial", 10, "bold"),
            ).grid(row=0, column=3, padx=5, pady=2)

            for i, header in enumerate(self.headers):
                row_num = i + 1

                header_entry = tk.Entry(self.headers_frame, width=20)
                header_entry.insert(0, header)
                header_entry.grid(row=row_num, column=0, sticky="W", padx=5, pady=2)

                role_var = tk.StringVar()
                # ADDING THE NEW ROLE
                role_dropdown = ttk.Combobox(
                    self.headers_frame,
                    textvariable=role_var,
                    state="readonly",
                    values=[
                        "Hierarchical Key",
                        "Sub Key",
                        "Simple Value",
                        "Value as Key",
                        "Key Name and Value",
                        "Skip",
                    ],
                )
                role_dropdown.grid(row=row_num, column=1, padx=5, pady=2)

                nested_under_var = tk.StringVar()
                nested_under_dropdown = ttk.Combobox(
                    self.headers_frame,
                    textvariable=nested_under_var,
                    state="readonly",
                    values=["root"],
                )
                nested_under_dropdown.grid(row=row_num, column=2, padx=5, pady=2)

                part_name_entry = tk.Entry(self.headers_frame, width=25)
                part_name_entry.grid(row=row_num, column=3, padx=5, pady=2)

                self.header_widgets[header] = {
                    "header_entry": header_entry,
                    "role_var": role_var,
                    "nested_under_var": nested_under_var,
                    "nested_under_dropdown": nested_under_dropdown,
                    "part_name_entry": part_name_entry,
                }

                def toggle_widgets(event):
                    role = role_dropdown.get()
                    if role in ["Hierarchical Key", "Key Name and Value"]:
                        part_name_entry["state"] = "normal"
                    else:
                        part_name_entry.delete(0, tk.END)
                        part_name_entry["state"] = "disabled"

                    self.update_nested_under_dropdowns()
                    self.preview_json()

                role_dropdown.bind("<<ComboboxSelected>>", toggle_widgets)

            self.after(100, self.preview_json)

            self.headers_canvas.update_idletasks()
            self.headers_canvas.config(scrollregion=self.headers_canvas.bbox("all"))

        except Exception as e:
            messagebox.showerror("🔴 ERROR", f"Failed to read CSV headers: {e}")

    def update_nested_under_dropdowns(self):
        """Updates the options in the Nested Under dropdowns based on current roles."""
        parents = ["root"]
        for header, widgets in self.header_widgets.items():
            role = widgets["role_var"].get()
            # ADDING THE NEW ROLE TO THE PARENTS
            if role in ["Hierarchical Key", "Value as Key", "Key Name and Value"]:
                parents.append(header)

        for header, widgets in self.header_widgets.items():
            widgets["nested_under_dropdown"]["values"] = parents
            if widgets["nested_under_var"].get() not in parents:
                widgets["nested_under_var"].set("root")

    def generate_json_from_config(self):
        """
        Helper function to generate JSON data from the current UI configuration.
        """

        try:
            df = pd.read_csv(self.csv_filepath, keep_default_na=False)

            sort_by_columns = []
            header_map = {}
            for original_header, widgets in self.header_widgets.items():
                role = widgets["role_var"].get()
                json_key_name = widgets["header_entry"].get()
                nested_under = widgets["nested_under_var"].get()

                config = {
                    "original_header": original_header,
                    "json_key": json_key_name if role not in ["Value as Key"] else None,
                    "role": role,
                    "nested_under": nested_under,
                }
                if role in ["Hierarchical Key", "Key Name and Value"]:
                    config["part_name"] = widgets["part_name_entry"].get() or "parts"
                    sort_by_columns.append(original_header)
                elif role == "Value as Key":
                    config["json_key"] = json_key_name
                    sort_by_columns.append(original_header)

                header_map[original_header] = config

            df.sort_values(by=sort_by_columns, inplace=True, kind="stable")

            root_name = self.root_name_entry.get()
            final_json = {root_name: []}

            final_json[root_name] = self.build_json_hierarchy(df, header_map, "root")

            if final_json[root_name] == []:
                messagebox.showerror(
                    "🔴 ERROR",
                    "The root 'Hierarchical Key' or 'Value as Key' must be selected to form the root of the JSON structure.",
                )
                return {}

            return final_json

        except Exception as e:
            messagebox.showerror(
                "🔴 ERROR", f"An error occurred during generation: {e}"
            )

            return {}

    def preview_json(self):
        """Generates and displays a preview of the JSON output."""
        if not self.csv_filepath or not os.path.exists(self.csv_filepath):

            self.update_output_with_json({})
            return

        json_data = self.generate_json_from_config()
        # Only proceed if generation was successful and returned a non-empty dictionary
        if json_data:
            self.update_output_with_json(json_data)

    def convert_to_json(self):
        """Converts the CSV to JSON and saves the file."""
        json_filepath = self.json_path_entry.get()
        if not json_filepath:
            messagebox.showerror("🔴 ERROR", "Please specify an output JSON file name.")
            return

        json_data = self.generate_json_from_config()
        if not json_data:
            return

        try:
            with open(json_filepath, "w") as f:
                f.write(orjson.dumps(json_data).decode("utf-8"))

            self.update_output_with_json(json_data)
            messagebox.showinfo(
                "Success", f"Successfully converted and saved to {json_filepath}"
            )
        except Exception as e:
            messagebox.showerror("🔴 ERROR", f"Failed to save JSON file: {e}")

    def update_output_with_json(self, data):
        """
        Clears and populates the Treeview and Raw JSON viewer with JSON data.
        """
        # Update Treeview
        for item in self.treeview.get_children():
            self.treeview.delete(item)

        def insert_items(parent, dictionary):
            if isinstance(dictionary, dict):
                for key, value in dictionary.items():
                    if isinstance(value, (dict, list)):
                        node = self.treeview.insert(parent, "end", text=key, open=True)
                        insert_items(node, value)
                    else:
                        self.treeview.insert(parent, "end", text=key, values=(value,))
            elif isinstance(dictionary, list):
                for i, item in enumerate(dictionary):
                    if isinstance(item, (dict, list)):
                        node = self.treeview.insert(
                            parent, "end", text=f"[{i}]", open=True
                        )
                        insert_items(node, item)
                    else:
                        self.treeview.insert(
                            parent, "end", text=f"[{i}]", values=(item,)
                        )

        insert_items("", data)

        # Update Raw JSON viewer
        self.raw_json_text.delete(1.0, tk.END)
        try:
            formatted_json = orjson.dumps(data, indent=4)
            self.raw_json_text.insert(tk.END, formatted_json)
        except Exception as e:
            self.raw_json_text.insert(tk.END, f"🔴 ERROR formatting JSON: {e}")

    def build_json_hierarchy(self, df, header_map, parent_key):
        """
        Recursively builds the JSON structure from the grouped DataFrame.
        This version now correctly handles multiple grouping keys per level.
        """
        output_list = []

        # Get all headers nested under the current parent_key
        current_level_configs = sorted(
            [
                h
                for h in header_map.values()
                if h["nested_under"] == parent_key and h["role"] != "Skip"
            ],
            key=lambda x: self.headers.index(x["original_header"]),
        )

        # Find the first grouping key for this level
        first_grouping_key_config = next(
            (
                h
                for h in current_level_configs
                if h["role"]
                in ["Hierarchical Key", "Value as Key", "Key Name and Value"]
            ),
            None,
        )

        # Base case: No more grouping keys at this level
        if first_grouping_key_config is None:

            output_list = []
            if not df.empty:
                simple_configs = [
                    h
                    for h in current_level_configs
                    if h["role"] in ["Simple Value", "Sub Key"]
                ]

                for _, row in df.iterrows():
                    node = {}
                    for header_config in simple_configs:
                        original_header = header_config["original_header"]
                        json_key = header_config["json_key"]
                        value = row[original_header]

                        if pd.notna(value) and value != "":
                            if isinstance(value, bool):
                                value = str(value).lower()
                            node[json_key] = value
                    if node:
                        output_list.append(node)
            return output_list

        first_grouping_key = first_grouping_key_config["original_header"]
        grouped_df = df.groupby(first_grouping_key, sort=False)

        for key_value, group in grouped_df:
            node = {}

            # Build the current node based on the first grouping key
            if first_grouping_key_config["role"] == "Value as Key":
                children = self.build_json_hierarchy(
                    group, header_map, first_grouping_key
                )
                merged_children = {}
                if children and isinstance(children, list):
                    for child_dict in children:
                        merged_children.update(child_dict)
                elif children and isinstance(children, dict):
                    merged_children.update(children)

                node[key_value] = merged_children

            elif first_grouping_key_config["role"] == "Hierarchical Key":
                if isinstance(key_value, bool):
                    key_value = str(key_value).lower()

                node[first_grouping_key_config["json_key"]] = key_value
                node[first_grouping_key_config["part_name"]] = (
                    self.build_json_hierarchy(group, header_map, first_grouping_key)
                )

            # NEW LOGIC FOR "KEY NAME AND VALUE"
            elif first_grouping_key_config["role"] == "Key Name and Value":
                part_name = first_grouping_key_config["part_name"]
                # Create a key with the header's JSON Key Name
                # The value is a dictionary with the part_name holding the CSV value
                node[first_grouping_key_config["json_key"]] = {
                    part_name: key_value,
                    "parts": self.build_json_hierarchy(
                        group, header_map, first_grouping_key
                    ),
                }

            output_list.append(node)

        return output_list


if __name__ == "__main__":
    app = CSVToJSONApp()
    app.mainloop()
