import tkinter as tk
from tkinter import ttk
import datetime

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from loguru import logger

class Aes70Dashboard(tk.Frame):
    """
    AES70 (OCA) Status & Discovery.
    A pure observer that reflects state from the AES70Manager worker.
    """
    def __init__(self, parent, **kwargs):
        # Extract non-Tkinter arguments
        self.config_data = kwargs.pop("config", {})
        self.json_path = kwargs.pop("json_path", None)
        
        super().__init__(parent, **kwargs)
        self.aes_manager = self._find_aes_manager(parent)
        self._setup_ui()
        
        if self.aes_manager:
            self.aes_manager.add_monitor_callback(self.on_aes_activity)
            self._refresh_ui()

    def _find_aes_manager(self, widget):
        from oaGuiBuilder.builder import DynamicGuiBuilder
        curr = widget
        while curr:
            if isinstance(curr, DynamicGuiBuilder) and hasattr(curr, 'app_instance'):
                return getattr(curr.app_instance, 'aes70_manager', None)
            try: curr = curr.master
            except: break
        return None

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        self.configure(bg="#2b2b2b")

        # 1. Header
        header = tk.Frame(self, bg="#2b2b2b")
        header.pack(side=tk.TOP, fill=tk.X, pady=10)
        tk.Label(header, text="📻 AES70 / OCA DISCOVERY", font=("Helvetica", 14, "bold"), fg="#ffffff", bg="#2b2b2b").pack(side=tk.LEFT, padx=20)
        
        ttk.Button(header, text="Scan Network", command=self._trigger_scan).pack(side=tk.RIGHT, padx=20)

        # 2. Main Layout
        main_pane = tk.Frame(self, bg="#2b2b2b")
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10)

        # --- TOP: Device Monitor ---
        list_frame = tk.LabelFrame(main_pane, text="Discovered OCA Devices", bg="#2b2b2b", fg="#888888")
        list_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.device_tree = ttk.Treeview(list_frame, columns=("Status"), show="tree headings", height=8)
        self.device_tree.heading("#0", text="Device Name / UID")
        self.device_tree.heading("Status", text="Connection State")
        self.device_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- BOTTOM: Activity Monitor ---
        log_frame = tk.LabelFrame(main_pane, text="Protocol Activity Log", bg="#2b2b2b", fg="#888888")
        log_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = tk.Text(log_frame, bg="#000000", fg="#00ff00", font=("Courier", 10), height=8)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _trigger_scan(self):
        """Delegates the scan logic to the worker."""
        if self.aes_manager:
            self.aes_manager.trigger_scan()
            self._refresh_ui()

    def _refresh_ui(self):
        """Pure UI refresh. Pulls data from the manager."""
        if not self.aes_manager: return
        
        status = self.aes_manager.get_status()
        
        # We could update a general status label here if needed
        pass

    def on_aes_activity(self, event_type, details):
        """Called by the manager when events occur."""
        self.after(0, lambda: self._handle_event(event_type, details))

    def _handle_event(self, event_type, details):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        
        if event_type == "SCAN_COMPLETE":
            # Update Tree
            for item in self.device_tree.get_children():
                self.device_tree.delete(item)
            for dev in details:
                self.device_tree.insert("", "end", text=dev, values=("Online",))
            self.log_text.insert("1.0", f"[{ts}] 📻 SCAN COMPLETE: Found {len(details)} devices.\n")
        
        elif event_type == "STATE_SYNC":
            self.log_text.insert("1.0", f"[{ts}] 📻 SYNC >> {details}\n")

        # Truncate log
        if int(self.log_text.index('end-1c').split('.')[0]) > 50:
            self.log_text.delete('50.0', tk.END)

    def destroy(self):
        if self.aes_manager:
            try: self.aes_manager.remove_monitor_callback(self.on_aes_activity)
            except: pass
        super().destroy()

def get_gui_class():
    return Aes70Dashboard
