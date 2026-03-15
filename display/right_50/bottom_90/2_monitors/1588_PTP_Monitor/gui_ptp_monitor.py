import tkinter as tk
from tkinter import ttk
import datetime
import orjson
import sys
import os
from pathlib import Path

# --- Path Guard: Ensure project root is in sys.path ---
current_path = Path(__file__).resolve()
root_path = current_path
for parent in current_path.parents:
    if (parent / "workers").exists() and (parent / "display").exists():
        root_path = parent
        break

if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from managers.PTP.ptp_manager import register_ptp_callback, unregister_ptp_callback

# --- Protocol: Integration Layer ---
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger
from managers.configini.config_reader import Config

from workers.styling.style import THEMES, DEFAULT_THEME
from managers.Display.transparency.transparency_mixin import TransparencyMixin

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file

app_constants = Config.get_instance()

class PtpMonitor(tk.Frame, TransparencyMixin):
    """
    A GUI monitor that displays a running list of PTP (IEEE 1588) packets
    with a detailed dissector for inspecting packet fields.
    Layout: Packet List (Top) -> Time Meters (Middle) -> Dissector (Bottom)
    """

    def __init__(self, parent, json_path=None, config=None, **kwargs):
        self.config_data = config if config else {}
        self.theme_colors = self.config_data.get("theme_colors", THEMES[DEFAULT_THEME])
        self.meters = {}
        
        # Set default background to match theme for non-transparent areas
        if "bg" not in kwargs and "background" not in kwargs:
            kwargs["bg"] = self.theme_colors.get("bg", "#2b2b2b")
            
        super().__init__(parent, **kwargs)
        
        self._setup_styles()
        self._setup_ui()
        
        # --- Transparency Integration ---
        # Note: ModuleLoader now wraps this in a DynamicGuiBuilder
        builder = self._find_builder_instance(self)
        if builder:
            self._apply_transparency(self, canvas=None, config_data={}, builder_instance=builder)
        
        # Register for updates
        register_ptp_callback(self.on_ptp_packet)
        
        if LOCAL_DEBUG: logger.debug("🖥️ PTP Monitor Initialized.")

    def _find_builder_instance(self, widget):
        """Recursively searches for a DynamicGuiBuilder in the parent hierarchy."""
        from workers.builder.builder import DynamicGuiBuilder
        curr = widget
        while curr:
            if isinstance(curr, DynamicGuiBuilder):
                return curr
            try:
                curr = curr.master
            except:
                break
        return None

    def _setup_styles(self):
        """Configures custom styles for the dark background."""
        self.style = ttk.Style()
        bg_color = self.theme_colors.get("bg", "#2b2b2b")
        
        self.style.configure("Dark.TFrame", background=bg_color)
        self.style.configure("Dark.TLabel", background=bg_color, foreground=self.theme_colors.get("fg", "#dcdcdc"))
        # Custom style for treeviews
        self.style.configure("Ptp.Treeview", 
                             background="#3c3f41", 
                             fieldbackground="#3c3f41", 
                             foreground="black")

    def _setup_ui(self):
        """Sets up the 3-pane vertical split UI."""
        self.pack(fill=tk.BOTH, expand=True)
        
        # Main vertical paned window
        self.v_paned = tk.PanedWindow(self, orient=tk.VERTICAL, bg=self.cget("bg"), bd=0, sashwidth=4)
        self.v_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 1. TOP PANE: Packet List
        self.list_container = tk.Frame(self.v_paned, bg=self.cget("bg"))
        self.v_paned.add(self.list_container, stretch="always", height=200)
        
        lbl_list = ttk.Label(self.list_container, text="PTP (Precision Time Protocol) Monitor", 
                             font=("Helvetica", 12, "bold"), style="Dark.TLabel")
        lbl_list.pack(side=tk.TOP, pady=(0, 5))
        
        cols = ("Time", "Source IP", "Type", "Domain", "Seq ID", "Clock Identity")
        self.packet_tree = ttk.Treeview(self.list_container, columns=cols, show="headings", style="Ptp.Treeview")
        
        for col in cols:
            self.packet_tree.heading(col, text=col)
            if col == "Time": self.packet_tree.column(col, width=150, anchor="w")
            elif col == "Clock Identity": self.packet_tree.column(col, width=250, anchor="w")
            else: self.packet_tree.column(col, width=100, anchor="w")
        
        self.packet_tree.tag_configure("Sync", foreground="#006400")      # Dark Green
        self.packet_tree.tag_configure("Announce", foreground="#4444ff")  # Blue
        self.packet_tree.tag_configure("Follow_Up", foreground="#000000") # Black
        
        scroll_y = ttk.Scrollbar(self.list_container, orient=tk.VERTICAL, command=self.packet_tree.yview)
        self.packet_tree.configure(yscrollcommand=scroll_y.set)
        self.packet_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.packet_tree.bind("<<TreeviewSelect>>", self.on_packet_select)

        # 2. MIDDLE PANE: Horizontal Meters
        self.meter_container = tk.Frame(self.v_paned, bg=self.cget("bg"))
        # Increased height slightly to accommodate labels
        self.v_paned.add(self.meter_container, stretch="never", height=180)
        self._setup_meters(self.meter_container)

        # 3. BOTTOM PANE: Dissector
        self.dissect_container = tk.Frame(self.v_paned, bg=self.cget("bg"))
        self.v_paned.add(self.dissect_container, stretch="always", height=300)
        
        lbl_dissect = ttk.Label(self.dissect_container, text="Packet Dissector", 
                                font=("Helvetica", 10, "bold"), style="Dark.TLabel")
        lbl_dissect.pack(side=tk.TOP, anchor="w", pady=(5, 0))

        self.dissector_tree = ttk.Treeview(self.dissect_container, columns=("Value"), show="tree headings", style="Ptp.Treeview")
        self.dissector_tree.heading("#0", text="Field")
        self.dissector_tree.heading("Value", text="Value")
        self.dissector_tree.column("#0", width=200, anchor="w")
        self.dissector_tree.column("Value", width=400, anchor="w")
        
        d_scroll_y = ttk.Scrollbar(self.dissect_container, orient=tk.VERTICAL, command=self.dissector_tree.yview)
        self.dissector_tree.configure(yscrollcommand=d_scroll_y.set)
        self.dissector_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        d_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 4. FOOTER: Controls
        self.controls_frame = tk.Frame(self, bg=self.cget("bg"))
        self.controls_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        self.btn_clear = ttk.Button(self.controls_frame, text="Clear Log", command=self.clear_log)
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        self.btn_copy_cmd = ttk.Button(self.controls_frame, text="COPY PTP SNIFFER COMMAND", command=self.copy_sniffer_command)
        self.btn_copy_cmd.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def _setup_meters(self, parent_frame):
        """Creates the 6 time analysis meters horizontally."""
        builder = self._find_builder_instance(self)
        if not builder: return

        meter_configs = [
            ("Month", 1, 12, "MONTH"),
            ("Day", 1, 31, "DAY"),
            ("Hour", 1, 24, "HOUR"),
            ("Minute", 0, 59, "MIN"),
            ("Second", 0, 59, "SEC"),
            ("Millisecond", 0, 999, "MS")
        ]
        
        # Center the meter stack horizontally
        self.meter_stack = tk.Frame(parent_frame, bg=self.cget("bg"))
        self.meter_stack.pack(expand=True)

        for label, v_min, v_max, short_label in meter_configs:
            cfg = {
                "type": "_NeedleVUMeter",
                "label": label,
                # Scaled down for horizontal fit
                "geometry": {"width": 140, "height": 140},
                "domain": {"primary": {"min": float(v_min), "max": float(v_max), "value_default": float(v_min)}},
                "cosmetics": {
                    "colors": {"foreground": "#000000", "bezel": "#000000", "scale_label": "#000000"},
                    "style_overrides": {
                        "bezel_shape": "squircle",
                        "bezel_width": 4,
                        "overlay_style": "aperture_mask",
                        "Pointer_Style": "knife-edge",
                        "sub_ticks": 2 if v_max < 100 else 4,
                        "tick_length": 5,
                        "label_radius_offset": 5
                    },
                    "labels": [
                        {"text": short_label, "x": 0, "y": -55, "size": 9, "font": "Arial", "weight": "bold"},
                        {"value_overlay": True, "x": 0, "y": -40, "size": 9, "weight": "bold", "color": "#000000", "sig_fig": 0}
                    ]
                }
            }
            meter_frame = builder.make_meter_needle(self.meter_stack, cfg)
            if meter_frame:
                meter_frame.pack(side=tk.LEFT, padx=2)
                self.meters[label] = meter_frame

    def _on_gui_visible(self, event=None):
        """Called when the tab becomes visible. Forces a reslice."""
        builder = self._find_builder_instance(self)
        if builder and hasattr(builder, "_trigger_reslice_all"):
            builder._trigger_reslice_all()

    def copy_sniffer_command(self):
        """Copies the sudo command to run the PTP tester to the clipboard."""
        script_path = root_path / "managers" / "PTP" / "PTPtester.py"
        
        # Get current broker config
        addr = app_constants.MQTT_BROKER_ADDRESS
        port = app_constants.MQTT_BROKER_PORT
        
        cmd = f"sudo PYTHONPATH=$(python3 -m site --user-site) python3 {script_path} --broker {addr} --port {port}"
        
        self.clipboard_clear()
        self.clipboard_append(cmd)
        original_text = self.btn_copy_cmd.cget("text")
        self.btn_copy_cmd.config(text="PASTE copied text into terminal")
        self.after(3000, lambda: self.btn_copy_cmd.config(text=original_text))
        if LOCAL_DEBUG: logger.debug(f"📋 PTP Sniffer command copied to clipboard: {cmd}")

    def on_ptp_packet(self, data):
        """Callback received from the PtpManager."""
        ts_raw = data["timestamp"]
        dt = datetime.datetime.fromtimestamp(ts_raw)
        ts_str = dt.strftime('%H:%M:%S.%f')[:-3]
        
        msg_type = data["message_type"]
        tag = ""
        if "Sync" in msg_type: tag = "Sync"
        elif "Announce" in msg_type: tag = "Announce"
        elif "Follow_Up" in msg_type: tag = "Follow_Up"

        # Add visual breakdown of timestamp for the dissector
        seconds = int(ts_raw)
        fraction = ts_raw - seconds
        ms = int(fraction * 1000)
        us = int((fraction * 1_000_000) % 1000)
        ns = int((fraction * 1_000_000_000) % 1000)

        breakdown = {
            "0_Raw_Unix_Float": f"{ts_raw:.9f}",
            "1_Epoch_Seconds": f"{seconds} (Seconds since Jan 1, 1970)",
            "2_Sub_Second_Remainder": f"{fraction:.9f}",
            "3_Calendar_Breakdown": {
                "Year": dt.year,
                "Month": f"{dt.month} ({dt.strftime('%B')})",
                "Day": dt.day,
                "Hour": dt.hour,
                "Minute": dt.minute,
                "Second": dt.second,
                "ISO_8601": dt.isoformat()
            },
            "4_Resolution_Breakdown": {
                "Milliseconds": f"{ms} ms",
                "Microseconds": f"{us} \u00b5s",
                "Nanoseconds": f"{ns} ns"
            }
        }
        
        ordered_data = {"Timestamp_Analysis": breakdown}
        ordered_data.update(data)

        # Insert at the top of the treeview
        item_id = self.packet_tree.insert("", 0, values=(
            ts_str, 
            data["source_ip"], 
            msg_type, 
            data["domain"], 
            data["sequence_id"], 
            data["clock_identity"]
        ), tags=(tag))
        
        if not hasattr(self, "_packet_data_cache"):
            self._packet_data_cache = {}
        self._packet_data_cache[item_id] = ordered_data

        # ⚡ AUTO-DISSECT: Always show the most recent packet
        self.packet_tree.selection_set(item_id)
        self.packet_tree.see(item_id)
        self.on_packet_select()

        if len(self.packet_tree.get_children()) > 100:
            last_item = self.packet_tree.get_children()[-1]
            self.packet_tree.delete(last_item)
            if last_item in self._packet_data_cache:
                del self._packet_data_cache[last_item]

    def _update_meters_from_timestamp(self, ts_raw):
        """Updates the visual meters from a unix float timestamp."""
        if not self.meters: return
        
        dt = datetime.datetime.fromtimestamp(ts_raw)
        ms_val = int(dt.microsecond / 1000)
        
        try:
            if "Month" in self.meters: self.meters["Month"].vu_value_var.set(dt.month)
            if "Day" in self.meters: self.meters["Day"].vu_value_var.set(dt.day)
            if "Hour" in self.meters: self.meters["Hour"].vu_value_var.set(dt.hour)
            if "Minute" in self.meters: self.meters["Minute"].vu_value_var.set(dt.minute)
            if "Second" in self.meters: self.meters["Second"].vu_value_var.set(dt.second)
            if "Millisecond" in self.meters: self.meters["Millisecond"].vu_value_var.set(ms_val)
        except Exception as e:
            logger.exception("⚠️ Failed to update PTP meters")

    def on_packet_select(self, event=None):
        """Handles selection in the packet list to populate the dissector and update meters."""
        selected_items = self.packet_tree.selection()
        if not selected_items: return
            
        for item in self.dissector_tree.get_children():
            self.dissector_tree.delete(item)
            
        item_id = selected_items[0]
        data = self._packet_data_cache.get(item_id)
        if data: 
            self._populate_dissector("", data)
            # Update meters from selected packet
            ts = data.get("timestamp")
            if ts is not None:
                self._update_meters_from_timestamp(ts)

    def _populate_dissector(self, parent, data):
        """Recursively populates the dissector tree."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    node = self.dissector_tree.insert(parent, "end", text=key, open=True)
                    self._populate_dissector(node, value)
                else:
                    self.dissector_tree.insert(parent, "end", text=key, values=(value))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    node = self.dissector_tree.insert(parent, "end", text=f"[{i}]", open=True)
                    self._populate_dissector(node, item)
                else:
                    self.dissector_tree.insert(parent, "end", text=f"[{i}]", values=(item))

    def clear_log(self):
        for item in self.packet_tree.get_children():
            self.packet_tree.delete(item)
        for item in self.dissector_tree.get_children():
            self.dissector_tree.delete(item)
        self._packet_data_cache = {}

    def render(self):
        """Required by TransparencyMixin to sync background colors of children."""
        if not hasattr(self, 'cget'): return
        bg = self.cget("bg")
        # Update style background for treeviews
        self.style.configure("Ptp.Treeview", background=bg, fieldbackground=bg)
        self.style.configure("Dark.TFrame", background=bg)
        self.style.configure("Dark.TLabel", background=bg)
        
        # Sync the manual frames
        self.v_paned.configure(bg=bg)
        self.list_container.configure(bg=bg)
        self.meter_container.configure(bg=bg)
        self.dissect_container.configure(bg=bg)
        self.meter_stack.configure(bg=bg)
        self.controls_frame.configure(bg=bg)

    def destroy(self):
        unregister_ptp_callback(self.on_ptp_packet)
        super().destroy()
