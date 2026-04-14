# /home/anthony/Documents/OPEN-AIR/oaComProtocols/oaComREST/Interface/gui_REST_tree.py
# Author: Anthony Peter Kuzub
# Version: 20260414.0015.1
#
# Description: REST API Tree Explorer with interactive testing capabilities.

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import threading
from pathlib import Path
import sys

import oaComProtocols.oaComREST.Entry as REST_MODULE

# --- GUI FALLBACKS (V3.2.1 Decoupling) ---
try:
    from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
except ImportError:
    class TransparencyMixin:
        """Fallback mixin for standalone execution without GUI manager."""
        def render(self): pass

class RestTreeImplementation(tk.Frame, TransparencyMixin):
    """
    Interactive API Tree Explorer.
    Allows manual testing of endpoints and full system state retrieval.
    """
    def __init__(self, parent, **kwargs):
        self.config_data = kwargs.pop("config", {})
        super().__init__(parent, **kwargs)
        
        # REST Server details
        from oaComProtocols.oaComREST.Constants.rest_constants import REST_BIND_HOST, REST_PORT
        self.base_url = f"http://{REST_BIND_HOST}:{REST_PORT}"
        
        self._setup_ui()
        self._refresh_tree()
        self._refresh_ui()
        self._schedule_refresh()

    def _schedule_refresh(self):
        """Schedules a periodic status check."""
        self._refresh_ui()
        if not getattr(self, '_destroyed', False):
            self.after(2000, self._schedule_refresh)

    def _refresh_ui(self):
        """Pulls status from the REST module's Entry point."""
        try:
            status = REST_MODULE.get_status()
            if status.get("running"):
                self.status_lbl.configure(text=f"🟢 ONLINE | PORT: {status['port']}", fg="#00ff00")
            else:
                self.status_lbl.configure(text="🔴 OFFLINE", fg="#ff4444")
        except Exception:
            pass

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        self.configure(bg="#2b2b2b")

        # 1. Top Control Bar
        ctrl_bar = tk.Frame(self, bg="#333333")
        ctrl_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Button(ctrl_bar, text="🔄 REFRESH TREE", bg="#444444", fg="#ffffff", font=("Helvetica", 9, "bold"),
                  command=self._refresh_tree, width=15).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(ctrl_bar, text="🚀 TEST FULLY (GET ALL)", bg="#f4902c", fg="#1a1a1a", font=("Helvetica", 9, "bold"),
                  command=self._test_fully, width=20).pack(side=tk.LEFT, padx=5, pady=5)

        self.status_lbl = tk.Label(ctrl_bar, text="Status: LOADING...", font=("Courier", 10, "bold"), fg="#ffff00", bg="#333333")
        self.status_lbl.pack(side=tk.RIGHT, padx=20)

        # 2. Main Body (Paned Window)
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- LEFT: Tree View ---
        tree_frame = tk.Frame(self.paned, bg="#2b2b2b")
        self.paned.add(tree_frame, weight=1)

        cols = ("Value")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="tree headings")
        self.tree.heading("#0", text="API Endpoints / Topics")
        self.tree.heading("Value", text="Live Value")
        self.tree.column("#0", width=350)
        self.tree.column("Value", width=150)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self._test_selected)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # --- RIGHT: Result & Interaction ---
        result_frame = tk.Frame(self.paned, bg="#1a1a1a", bd=1, relief="sunken")
        self.paned.add(result_frame, weight=1)

        header = tk.Frame(result_frame, bg="#333333")
        header.pack(side=tk.TOP, fill=tk.X)
        tk.Label(header, text="🧪 INTERACTIVE TESTER", font=("Helvetica", 10, "bold"), fg="#ffffff", bg="#333333").pack(side=tk.LEFT, padx=10, pady=5)
        
        self.btn_test = tk.Button(header, text="GET VALUE", bg="#33A1FD", fg="#ffffff", font=("Helvetica", 8, "bold"),
                                 command=self._test_selected, state="disabled")
        self.btn_test.pack(side=tk.RIGHT, padx=5, pady=2)

        self.result_text = tk.Text(result_frame, bg="#000000", fg="#00ff00", font=("Courier", 10), padx=10, pady=10)
        self.result_text.pack(fill=tk.BOTH, expand=True)

    def _on_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.btn_test.config(state="normal")
        else:
            self.btn_test.config(state="disabled")

    def _refresh_tree(self):
        """Fetches the tree keys from the server and rebuilds the view."""
        def worker():
            try:
                # We use the new tree endpoint to get keys
                response = requests.get(f"{self.base_url}/api/v1/system/tree", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    self.after(0, lambda: self._rebuild_tree_ui(data))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda: self.result_text.insert(tk.END, f"\n❌ Failed to sync tree: {err_msg}"))

        threading.Thread(target=worker, daemon=True).start()

    def _rebuild_tree_ui(self, data):
        """Reconstructs the hierarchical Treeview from a flat dict."""
        self.tree.delete(*self.tree.get_children())
        
        # Build node structure
        nodes = {} # path -> id
        
        # Sort topics to ensure parents are created before children
        topics = sorted(data.keys())
        
        for topic in topics:
            parts = topic.split('/')
            path = ""
            parent_id = ""
            
            for i, part in enumerate(parts):
                path = f"{path}/{part}" if path else part
                if path not in nodes:
                    # If it's the last part, show the value
                    val_str = str(data[topic]) if i == len(parts)-1 else ""
                    nodes[path] = self.tree.insert(parent_id, "end", text=part, values=(val_str,), open=True)
                parent_id = nodes[path]

    def _test_selected(self, event=None):
        selected = self.tree.selection()
        if not selected: return
        
        # Reconstruct path from tree hierarchy
        path_parts = []
        curr = selected[0]
        while curr:
            path_parts.insert(0, self.tree.item(curr)["text"])
            curr = self.tree.parent(curr)
        
        endpoint = "/".join(path_parts)
        self._run_test(endpoint)

    def _test_fully(self):
        """Tests the full tree endpoint."""
        self._run_test("api/v1/system/tree")

    def _run_test(self, endpoint):
        """Executes a GET request against an endpoint and displays the raw JSON result."""
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, f"📡 REQUEST: GET {self.base_url}/{endpoint}\n")
        self.result_text.insert(tk.END, "--------------------------------------------------\n\n")
        
        def worker():
            try:
                import time
                t0 = time.time()
                response = requests.get(f"{self.base_url}/{endpoint}", timeout=5)
                t1 = time.time()
                
                content = json.dumps(response.json(), indent=4)
                
                self.after(0, lambda: self._display_result(response.status_code, content, t1-t0))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda: self.result_text.insert(tk.END, f"❌ TEST FAILED: {err_msg}"))

        threading.Thread(target=worker, daemon=True).start()

    def _display_result(self, status, content, duration):
        self.result_text.insert(tk.END, f"✅ STATUS  : {status}\n")
        self.result_text.insert(tk.END, f"⏱️  LATENCY : {duration:.4f}s\n\n")
        self.result_text.insert(tk.END, "📦 RESPONSE BODY:\n")
        self.result_text.insert(tk.END, content)

    def render(self): pass
    def destroy(self):
        self._destroyed = True
        super().destroy()

__all__ = ["RestTreeImplementation"]
