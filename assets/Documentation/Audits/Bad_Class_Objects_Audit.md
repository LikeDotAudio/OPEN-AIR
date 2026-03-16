# Clean Code Audit: Class & Object Structure Report

## Executive Summary
Analyzed codebase for God Classes, SRP violations, Low Cohesion, and Law of Demeter violations.
- **Files with Issues**: 89
- **Total Violations**: 172

## Top Offenders

### workers/builder/circular_motion_displacement_potentiometer/core/cmdp_tree_manager.py
#### SRP Violation (Naming)
- Line 4: Class 'CMDPTreeManager' uses noise word 'Manager' indicating mixed responsibilities.
  `class CMDPTreeManager:`
#### Law of Demeter (Train Wreck)
- Line 11: Chain of 3 calls/attributes violates encapsulation.
  `is_vis = not self.w.show_channels_var.get(); self.w.show_channels_var.set(is_vis)`
- Line 11: Chain of 3 calls/attributes violates encapsulation.
  `is_vis = not self.w.show_channels_var.get(); self.w.show_channels_var.set(is_vis)`
- Line 13: Chain of 3 calls/attributes violates encapsulation.
  `self.w.tree_window = tk.Toplevel(self.w); self.w.tree_window.title("Channel Tree"); self.w.tree_window.geometry("600x700")`
- Line 13: Chain of 3 calls/attributes violates encapsulation.
  `self.w.tree_window = tk.Toplevel(self.w); self.w.tree_window.title("Channel Tree"); self.w.tree_window.geometry("600x700")`
- Line 14: Chain of 3 calls/attributes violates encapsulation.
  `self.w.tree_window.protocol("WM_DELETE_WINDOW", self.toggle)`
- Line 19: Chain of 3 calls/attributes violates encapsulation.
  `self.w.pop_tree.heading("#0", text="Groups")`
- Line 20: Chain of 3 calls/attributes violates encapsulation.
  `for c in cols: self.w.pop_tree.heading(c, text=c); self.w.pop_tree.column(c, width=70, anchor="center")`
- Line 20: Chain of 3 calls/attributes violates encapsulation.
  `for c in cols: self.w.pop_tree.heading(c, text=c); self.w.pop_tree.column(c, width=70, anchor="center")`
- Line 21: Chain of 3 calls/attributes violates encapsulation.
  `self.w.pop_tree.pack(fill=tk.BOTH, expand=True)`
- Line 24: Chain of 3 calls/attributes violates encapsulation.
  `self.w.pop_tree.bind("<Button-1>", self._on_click)`
- ... and 20 more.

---
### workers/builder/data_graphing/core/view_controller.py
#### SRP Violation (Naming)
- Line 4: Class 'ViewController' uses noise word 'Controller' indicating mixed responsibilities.
  `class ViewController:`
#### Law of Demeter (Train Wreck)
- Line 26: Chain of 4 calls/attributes violates encapsulation.
  `self.ax.add_patch(self.rect); self.ax.figure.canvas.draw_idle()`
- Line 26: Chain of 3 calls/attributes violates encapsulation.
  `self.ax.add_patch(self.rect); self.ax.figure.canvas.draw_idle()`
- Line 30: Chain of 4 calls/attributes violates encapsulation.
  `if self.press and event.button == 2: self.press = None; self.ax.figure.canvas.draw(); self._trigger()`
- Line 30: Chain of 3 calls/attributes violates encapsulation.
  `if self.press and event.button == 2: self.press = None; self.ax.figure.canvas.draw(); self._trigger()`
- Line 36: Chain of 4 calls/attributes violates encapsulation.
  `self.ax.figure.canvas.draw_idle(); self._trigger()`
- Line 36: Chain of 3 calls/attributes violates encapsulation.
  `self.ax.figure.canvas.draw_idle(); self._trigger()`
- Line 41: Chain of 3 calls/attributes violates encapsulation.
  `x_start, y_start = self.press; w, h = self.ax.bbox.width, self.ax.bbox.height`
- Line 41: Chain of 3 calls/attributes violates encapsulation.
  `x_start, y_start = self.press; w, h = self.ax.bbox.width, self.ax.bbox.height`
- Line 48: Chain of 4 calls/attributes violates encapsulation.
  `self.ax.figure.canvas.draw_idle(); return`
- Line 48: Chain of 3 calls/attributes violates encapsulation.
  `self.ax.figure.canvas.draw_idle(); return`
- ... and 12 more.

---
### workers/builder/circular_motion_displacement_potentiometer/cmdp_group_handler.py
#### SRP Violation (Naming)
- Line 5: Class 'CMDPGroupHandler' uses noise word 'And' indicating mixed responsibilities.
  `class CMDPGroupHandler:`
#### Law of Demeter (Train Wreck)
- Line 51: Chain of 3 calls/attributes violates encapsulation.
  `if not self.w.mixin_ref.state_mirror_engine:`
- Line 54: Chain of 3 calls/attributes violates encapsulation.
  `sme = self.w.mixin_ref.state_mirror_engine`
- Line 73: Chain of 3 calls/attributes violates encapsulation.
  `if self.w.mixin_ref.subscriber_router and t:`
- Line 74: Chain of 4 calls/attributes violates encapsulation.
  `self.w.mixin_ref.subscriber_router.subscribe_to_topic(t, sme.sync_incoming_mqtt_to_gui)`
- Line 74: Chain of 3 calls/attributes violates encapsulation.
  `self.w.mixin_ref.subscriber_router.subscribe_to_topic(t, sme.sync_incoming_mqtt_to_gui)`
- Line 81: Chain of 3 calls/attributes violates encapsulation.
  `fr.config(bg=self.w.groups_container.cget("bg"))`
- Line 117: Chain of 3 calls/attributes violates encapsulation.
  `bg = self.w.groups_container.cget("bg")`
- Line 156: Chain of 3 calls/attributes violates encapsulation.
  `if self.w.mixin_ref.state_mirror_engine:`
- Line 157: Chain of 3 calls/attributes violates encapsulation.
  `idx = self.w.faders.index(f)`
- Line 158: Chain of 4 calls/attributes violates encapsulation.
  `self.w.mixin_ref.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{self.w.path}/ch{idx}/mute")`
- ... and 1 more.
#### God Class (Size)
- Line 5: Class 'CMDPGroupHandler' has 23 methods (Threshold: 15).
  `class CMDPGroupHandler:`

---
### workers/builder/data_graphing/core/graph_patina_mixin.py
#### Law of Demeter (Train Wreck)
- Line 28: Chain of 3 calls/attributes violates encapsulation.
  `self.fig.patch.set_facecolor(bg_hex)`
- Line 35: Chain of 3 calls/attributes violates encapsulation.
  `self.fig.patch.set_visible(visible)`
- Line 36: Chain of 3 calls/attributes violates encapsulation.
  `self.ax.patch.set_visible(visible)`
- Line 46: Chain of 3 calls/attributes violates encapsulation.
  `self.fig.images.clear()`
- Line 48: Chain of 3 calls/attributes violates encapsulation.
  `self.fig.patch.set_visible(False)`
- Line 49: Chain of 3 calls/attributes violates encapsulation.
  `self.ax.patch.set_visible(False)`

---
### workers/builder/circular_motion_displacement_potentiometer/cmdp_file_handler.py
#### SRP Violation (Naming)
- Line 13: Class 'CMDPFileHandler' uses noise word 'And' indicating mixed responsibilities.
  `class CMDPFileHandler:`
#### Law of Demeter (Train Wreck)
- Line 43: Chain of 3 calls/attributes violates encapsulation.
  `if self.w.mixin_ref.state_mirror_engine:`
- Line 44: Chain of 3 calls/attributes violates encapsulation.
  `sme = self.w.mixin_ref.state_mirror_engine`
- Line 82: Chain of 3 calls/attributes violates encapsulation.
  `inner = self.w.widget_config.copy()`

---
### workers/builder/data_graphing/core/annotation_manager.py
#### SRP Violation (Naming)
- Line 3: Class 'AnnotationManager' uses noise word 'Manager' indicating mixed responsibilities.
  `class AnnotationManager:`
#### Law of Demeter (Train Wreck)
- Line 43: Chain of 3 calls/attributes violates encapsulation.
  `ax.figure.canvas.draw_idle()`
- Line 48: Chain of 3 calls/attributes violates encapsulation.
  `ax.figure.canvas.draw_idle()`

---
### workers/Command_Router/protocol_router/router.py
#### Law of Demeter (Train Wreck)
- Line 68: Chain of 3 calls/attributes violates encapsulation.
  `old_observers = cls._instance.monitor._observers`
- Line 73: Chain of 3 calls/attributes violates encapsulation.
  `cls._instance.monitor._observers = old_observers`
#### God Class (Size)
- Line 19: Class 'ProtocolRouter' has 20 methods (Threshold: 15).
  `class ProtocolRouter:`

---
### display/right_50/bottom_90/3_Command_Router/gui_command_router.py
#### SRP Violation (Naming)
- Line 13: Class 'CommandRouter' uses noise word 'And' indicating mixed responsibilities.
  `class CommandRouter:`
#### Law of Demeter (Train Wreck)
- Line 305: Chain of 3 calls/attributes violates encapsulation.
  `self.router.firehose.clear()`
- Line 309: Chain of 3 calls/attributes violates encapsulation.
  `try: self.router._observers.remove(self.on_router_event)`

---
### assets/Stand Alone Utilities/Log Viewer/LogViewer.py
#### Law of Demeter (Train Wreck)
- Line 178: Chain of 3 calls/attributes violates encapsulation.
  `color_discrete_sequence=px.colors.qualitative.Pastel`
- Line 211: Chain of 3 calls/attributes violates encapsulation.
  `nbins=50, barmode="stack", color_discrete_sequence=px.colors.qualitative.Vivid`

---
### managers/Display/builder/core/layout_cache_manager.py
#### SRP Violation (Naming)
- Line 8: Class 'LayoutCacheManager' uses noise word 'Manager' indicating mixed responsibilities.
  `class LayoutCacheManager:`
#### Law of Demeter (Train Wreck)
- Line 32: Chain of 3 calls/attributes violates encapsulation.
  `self._cache_file.parent.mkdir(parents=True, exist_ok=True)`

---
### workers/builder/circular_motion_displacement_potentiometer/circular_motion_displacement_potentiometer.py
#### Law of Demeter (Train Wreck)
- Line 67: Chain of 3 calls/attributes violates encapsulation.
  `self.btn_toggle_groups.bind("<Button-3>", lambda e: self.gh.groups_menu.post(e.x_root, e.y_root))`
- Line 105: Chain of 3 calls/attributes violates encapsulation.
  `for p in ["val", "rot", "angle", "mute"]: self.mixin_ref.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{self.path}/ch{i}/{p}")`

---
### workers/Command_Router/mqtt/setup/config_reader.py
#### Law of Demeter (Train Wreck)
- Line 127: Chain of 4 calls/attributes violates encapsulation.
  `project_root = pathlib.Path(__file__).parent.parent.parent.parent`
- Line 127: Chain of 3 calls/attributes violates encapsulation.
  `project_root = pathlib.Path(__file__).parent.parent.parent.parent`

---
### workers/Command_Router/SNMP/snmp_manager.py
#### SRP Violation (Naming)
- Line 34: Class 'SNMPManager' uses noise word 'Manager' indicating mixed responsibilities.
  `class SNMPManager:`
#### God Class (Size)
- Line 34: Class 'SNMPManager' has 17 methods (Threshold: 15).
  `class SNMPManager:`

---
### audit_bad_tests.py
#### Law of Demeter (Train Wreck)
- Line 32: Chain of 3 calls/attributes violates encapsulation.
  `if isinstance(child.func, ast.Attribute) and child.func.attr.startswith("assert"):`

---
### assets/Stand Alone Utilities/OSC monitor/OSC monitor.py
#### SRP Violation (Naming)
- Line 14: Class 'StandaloneOscMonitor' uses noise word 'And' indicating mixed responsibilities.
  `class StandaloneOscMonitor:`

---
### assets/Stand Alone Utilities/Fluke Meter/flukeMeter.py
#### Law of Demeter (Train Wreck)
- Line 12: Chain of 3 calls/attributes violates encapsulation.
  `ports = list(serial.tools.list_ports.comports())`

---
### managers/Visa_Fleet_Manager/visa_fleet_manager.py
#### SRP Violation (Naming)
- Line 25: Class 'VisaFleetManager' uses noise word 'Manager' indicating mixed responsibilities.
  `class VisaFleetManager:`

---
### managers/Visa_Fleet_Manager/core/fleet_scan_mixin.py
#### Law of Demeter (Train Wreck)
- Line 37: Chain of 3 calls/attributes violates encapsulation.
  `self.mqtt_bridge.mqtt_manager.publish(topic, orjson.dumps(payload).decode())`

---
### managers/Visa_Fleet_Manager/core/fleet_command_queue_mixin.py
#### SRP Violation (Naming)
- Line 3: Class 'FleetCommandQueueMixin' uses noise word 'And' indicating mixed responsibilities.
  `class FleetCommandQueueMixin:`

---
### managers/configini/core/identity_manager.py
#### SRP Violation (Naming)
- Line 3: Class 'IdentityManager' uses noise word 'Manager' indicating mixed responsibilities.
  `class IdentityManager:`

---
### managers/Display/factory/asset_cache_manager.py
#### SRP Violation (Naming)
- Line 30: Class 'AssetCacheManager' uses noise word 'Manager' indicating mixed responsibilities.
  `class AssetCacheManager:`

---
### managers/Display/breakoff_manager/hidden_breakoff_manager.py
#### SRP Violation (Naming)
- Line 23: Class 'HiddenBreakoffManagerMixin' uses noise word 'Manager' indicating mixed responsibilities.
  `class HiddenBreakoffManagerMixin:`

---
### managers/Display/transparency/transparency_manager.py
#### SRP Violation (Naming)
- Line 9: Class 'TransparencyManager' uses noise word 'Manager' indicating mixed responsibilities.
  `class TransparencyManager:`

---
### managers/Display/parser/gui_smart_standardizer.py
#### SRP Violation (Naming)
- Line 5: Class 'SmartWidgetStandardizerMixin' uses noise word 'And' indicating mixed responsibilities.
  `class SmartWidgetStandardizerMixin:`

---
### managers/Display/parser/standardizers/lexicon_expander.py
#### SRP Violation (Naming)
- Line 1: Class 'LexiconExpander' uses noise word 'And' indicating mixed responsibilities.
  `class LexiconExpander:`

---
### managers/Display/telemetry/geometry_snitch/geometry_snitch.py
#### SRP Violation (Naming)
- Line 10: Class 'HiddenGeometryManagerMixin' uses noise word 'Manager' indicating mixed responsibilities.
  `class HiddenGeometryManagerMixin:`

---
### managers/Display/telemetry/visibility_snitch/visibility_snitch.py
#### SRP Violation (Naming)
- Line 10: Class 'HiddenVisibilityManagerMixin' uses noise word 'Manager' indicating mixed responsibilities.
  `class HiddenVisibilityManagerMixin:`

---
### managers/Display/array/array.py
#### SRP Violation (Naming)
- Line 17: Class 'ViewManager' uses noise word 'Manager' indicating mixed responsibilities.
  `class ViewManager:`

---
### managers/Display/builder/window_manager.py
#### SRP Violation (Naming)
- Line 32: Class 'WindowManager' uses noise word 'Manager' indicating mixed responsibilities.
  `class WindowManager:`

---
### managers/Display/builder/async_grid_renderer.py
#### Law of Demeter (Train Wreck)
- Line 100: Chain of 3 calls/attributes violates encapsulation.
  `state["pending"] += 1; creator = self.builder.widget_factory.get(w_type)`

---
