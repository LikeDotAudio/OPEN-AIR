# oaComProtocols.oaComMQTT/Interface/mqtt_explorer_impl.py
# Author: Anthony Peter Kuzub
# Version: 20260414.0045.1
#
# Description: MQTT Tree Explorer for the OPEN-AIR System.
# Pulls data from the State Cache and updates in real-time.

import tkinter as tk
from tkinter import ttk
import json
import time
from pathlib import Path
from oaLogging.Methods.matrix_gate import matrix_log
from oaComBroker.Core.event_bus import event_bus

try:
    from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
except ImportError:
    class TransparencyMixin:
        def render(self): pass

class MqttExplorerImplementation(tk.Frame, TransparencyMixin):
    """
    Hierarchical Tree Explorer for MQTT topics.
    Subscribes to EventBus for real-time updates from State Cache.
    """
    def __init__(self, parent, **kwargs):
        self.config_data = kwargs.pop("config", {})
        super().__init__(parent, **kwargs)
        
        self._nodes = {} # path -> item_id
        self._setup_ui()
        
        # Subscribe to state changes if available
        try:
            event_bus.subscribe("STATE_CHANGED", self._on_state_change)
            # Also subscribe to registry readiness to prime the tree
            event_bus.subscribe("REGISTRY_READY", self._prime_tree)
        except Exception:
            pass
            
        # Initial priming if state registry is already active
        self._prime_tree()

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        self.configure(bg="#2b2b2b")

        # Header
        header = tk.Frame(self, bg="#2b2b2b")
        header.pack(side=tk.TOP, fill=tk.X, pady=5)
        tk.Label(header, text="🌐 MQTT TREE EXPLORER", font=("Helvetica", 12, "bold"), fg="#ffffff", bg="#2b2b2b").pack(side=tk.LEFT, padx=10)
        
        btn_frame = tk.Frame(header, bg="#2b2b2b")
        btn_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Button(btn_frame, text="CLEAR", bg="#444444", fg="#ffffff", font=("Helvetica", 8), command=self._clear_tree).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="REFRESH", bg="#444444", fg="#ffffff", font=("Helvetica", 8), command=self._prime_tree).pack(side=tk.LEFT, padx=2)

        # Tree View
        tree_frame = tk.Frame(self, bg="#2b2b2b")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        cols = ("Value", "Timestamp")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="tree headings")
        self.tree.heading("#0", text="Topic Namespace")
        self.tree.heading("Value", text="Live Value")
        self.tree.heading("Timestamp", text="Last Updated")
        
        self.tree.column("#0", width=400)
        self.tree.column("Value", width=200)
        self.tree.column("Timestamp", width=150)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _clear_tree(self):
        self.tree.delete(*self.tree.get_children())
        self._nodes.clear()

    def _prime_tree(self, entries=None):
        """Primes the tree with initial state data."""
        # If no data provided, try to fetch from StateRegistry singleton
        if entries is None:
            try:
                # 1. Try from config first
                registry = self.config_data.get("state_cache_manager")
                
                # 2. Fallback to singleton if available
                if not registry:
                    from oaStateCache.Entry import get_registry
                    registry = get_registry()
                
                if registry and hasattr(registry, "rust_cache"):
                    # Use internal rust_cache items
                    for topic, data in registry.rust_cache.items():
                        val = data.get('value') if isinstance(data, dict) else data
                        ts = data.get('timestamp', time.time()) if isinstance(data, dict) else time.time()
                        self._update_node(topic, val, ts)
                    return
            except Exception as e:
                matrix_log("ui", "mqtt", "explorer", f"Failed to prime MQTT tree: {e}", "WARNING")
                return

        if not entries: return
        
        for topic, data in entries.items():
            val = data.get('value') if isinstance(data, dict) else data
            ts = data.get('timestamp', time.time()) if isinstance(data, dict) else time.time()
            self._update_node(topic, val, ts)

    def _on_state_change(self, topic, value, meta):
        """Real-time update from EventBus."""
        ts = meta.get('timestamp', time.time()) if isinstance(meta, dict) else time.time()
        self.after(0, lambda: self._update_node(topic, value, ts))

    def _update_node(self, topic, value, timestamp):
        """Inserts or updates a node in the hierarchical tree."""
        if not self.winfo_exists(): return
        
        parts = topic.split('/')
        path = ""
        parent_id = ""
        
        ts_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
        val_str = str(value)[:100] + ("..." if len(str(value)) > 100 else "")

        for i, part in enumerate(parts):
            path = f"{path}/{part}" if path else part
            if path not in self._nodes:
                # Create node
                is_last = (i == len(parts) - 1)
                v = val_str if is_last else ""
                t = ts_str if is_last else ""
                self._nodes[path] = self.tree.insert(parent_id, "end", text=part, values=(v, t), open=True)
            elif i == len(parts) - 1:
                # Update existing leaf
                self.tree.item(self._nodes[path], values=(val_str, ts_str))
            
            parent_id = self._nodes[path]

    def render(self): pass
    def destroy(self):
        super().destroy()

__all__ = ["MqttExplorerImplementation"]
