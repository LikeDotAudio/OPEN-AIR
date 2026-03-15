# workers/logic/state_mirror_engine.py
#
# Primary Purpose:
# The StateMirrorEngine facilitates seamless bidirectional synchronization
# between the local User Interface (Tkinter variables) and the distributed
# MQTT state tree. It ensures that local control changes are propagated to the
# network while maintaining local UI consistency when remote updates arrive.
#
# Responsibilities:
# - Synchronize GUI widget states with corresponding MQTT topics.
# - Implement high-performance throttling and change-only filtering to 
#   minimize network congestion.
# - Provide 'Interaction Locking' (Do Not Disturb) to prevent network updates
#   from interrupting active human manipulation of a widget.
# - Enforce loop prevention using 'origin_source' and Instance IDs to avoid
#   recursive feedback cycles.
# - Manage an asynchronous registration queue to offload widget initialization
#   from the primary UI thread.
#
# Constraints:
# - Requires a running Tkinter event loop ('root' must not be NULL).
# - Relies on 'orjson' for efficient serialization of telemetry payloads.
# - Assumes a thread-safe environment for registry access (uses RLock).
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260222.Optimized.2

import orjson
import inspect
import random
import time
import queue
import threading
import tkinter as tk
import contextlib
import os

# --- Standard Debug Logging Setup ---
# LOCAL_DEBUG: Toggles internal engine diagnostics for state synchronization.
LOCAL_DEBUG = True
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

# Specialized logger bound to the state engine subsystem.
state_logger = logger.bind(subsystem="STATE_ENGINE")

from managers.configini.config_reader import Config
from workers.Command_Router.mqtt.mqtt_message import MqttMessage

# Retrieve the global configuration singleton.
app_constants = Config.get_instance()

from workers.Command_Router.mqtt import mqtt_publisher_service
import workers.Command_Router.mqtt.mqtt_topic_utils as mqtt_topic_utils

class StateMirrorEngine:
    """
    Synchronizes GUI state with the MQTT broker with high-performance throttling.
    
    This engine acts as the 'glue' between the visual representation (widgets)
    and the digital state (MQTT). It utilizes a registration system to track
    which Tkinter variables correspond to which MQTT topics.
    """

    def __init__(self, base_topic, subscriber_router, root, state_cache_manager):
        """
        Initializes the StateMirrorEngine.

        Inputs:
            base_topic (str): The root MQTT topic prefix for all state traffic.
            subscriber_router (MqttSubscriberRouter): The router used for
                dispatching incoming MQTT messages.
            root (tk.Tk): The root Tkinter object for scheduling UI updates.
            state_cache_manager (StateCacheManager): The manager for local
                state persistence and Hub synchronization.

        Outputs:
            None.
        """
        self.base_topic = base_topic
        self.subscriber_router = subscriber_router
        self.root = root
        self.state_cache_manager = state_cache_manager
        
        # Internal registry protection. RLock allows recursive access within
        # the same thread during complex widget initialization.
        self._registry_lock = threading.RLock()
        self.registered_widgets = {}
        self.topic_to_widget_id = {}
        
        # Memoization cache for topic path calculations.
        self._topic_calc_cache = {}
        
        self._last_global_broadcast_ts = 0
        self._GLOBAL_THROTTLE_MS = 0.020 # 50Hz global cap to prevent floods.

        # Offload widget state initialization to a background worker.
        self._registration_queue = queue.Queue()
        self._reg_thread = threading.Thread(target=self._registration_worker, 
                                            daemon=True)
        self._reg_thread.start()

        self.is_inert = (root is None)
        self.GUID = app_constants.INSTANCE_GUID
        
        self._silent_update = False
        self._suppress_broadcast = False
        self._binding_suspended = False
        self.update_queue = queue.Queue()
        self._processing_scheduled = False
        self._schedule_lock = threading.Lock()
        
        self.broadcast_declarations_enabled = False

    def _registration_worker(self):
        """
        Background worker that processes the widget registration queue.
        
        This worker ensures that fetching the initial state from the cache 
        does not block the main UI thread during heavy GUI loads.
        """
        while True:
            try:
                widget_id = self._registration_queue.get(timeout=1.0)
                if widget_id is None:
                    break 
                self.initialize_widget_state(widget_id)
                self._registration_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                state_logger.error(f"Error in registration worker: {e}")

    def shutdown(self):
        """
        Signals the background registration worker to terminate.
        """
        self._registration_queue.put(None)
        if self._reg_thread.is_alive():
            self._reg_thread.join(timeout=2.0)

    @contextlib.contextmanager
    def suspend_bindings(self):
        """
        Context manager to temporarily disable all state synchronization.
        """
        self._binding_suspended = True
        try:
            yield
        finally:
            self._binding_suspended = False

    def start_queue_processing(self):
        """
        Manually triggers the processing of the UI update queue.
        """
        if self.is_inert:
            return
        self._schedule_queue_processing()

    def _schedule_queue_processing(self):
        """
        Schedules the update queue to be drained on the next UI idle cycle.
        """
        if self.is_inert:
            return
        with self._schedule_lock:
            if self._processing_scheduled:
                return
            self._processing_scheduled = True
        self.root.after(0, self._process_queue_wrapper)

    def _process_queue_wrapper(self):
        """
        Internal wrapper to reset the scheduling lock before processing.
        """
        with self._schedule_lock:
            self._processing_scheduled = False
        self._process_queue()

    def _process_queue(self):
        """
        Drains the UI update queue and applies values to Tkinter variables.

        Implementation:
            Processes up to 1000 messages in a single burst to maintain
            high throughput while preventing UI thread starvation.
        """
        if self.is_inert:
            return
        try:
            count = 0
            while count < 1000:
                try:
                    tk_var, value, widget_id = self.update_queue.get_nowait()
                    count += 1
                    
                    # Performance optimization: Skip updates if the variable
                    # already matches the target value.
                    try:
                        if isinstance(value, (int, float, bool)):
                            if tk_var.get() == value: continue
                        elif str(tk_var.get()) == str(value): continue
                    except:
                        continue

                    # Mark this as a 'silent' update to prevent the change 
                    # from being broadcast back to the network.
                    self._silent_update = True
                    try:
                        tk_var.set(value)
                    finally:
                        self._silent_update = False
                except queue.Empty:
                    break
        finally:
            # Re-schedule if there are still messages in the queue.
            try:
                lookahead = self.update_queue.get_nowait()
                self.update_queue.put(lookahead)
                self._schedule_queue_processing()
            except queue.Empty:
                pass

    def calculate_topic(self, widget_id, tab_name):
        """
        Generates the full MQTT topic path for a given widget ID and tab.

        Lead with action: Maps hierarchical widget identifiers to standard
        MQTT topic paths, using memoization to optimize recurring lookups.

        Inputs:
            widget_id (str): The unique identifier for the widget.
            tab_name (str): The name of the GUI tab/panel containing the widget.

        Outputs:
            str: The fully qualified MQTT topic path.
        """
        cache_key = (widget_id, tab_name)
        if cache_key in self._topic_calc_cache:
            return self._topic_calc_cache[cache_key]

        widget_id_str = str(widget_id).replace(".fields.", ".").replace(".", "/")
        
        if (widget_id_str.startswith(self.base_topic + "/") or 
            widget_id_str.startswith("/")):
            res = widget_id_str.lstrip("/")
        else:
            clean_tab = tab_name
            if (self.base_topic and clean_tab and 
                clean_tab.startswith(self.base_topic)):
                clean_tab = clean_tab[len(self.base_topic) :].strip("/")
            res = "/".join([p for p in [self.base_topic, clean_tab, 
                            widget_id_str.lstrip("/")] if p]).replace("//", "/")
        
        self._topic_calc_cache[cache_key] = res
        return res

    def register_widget(self, widget_id, tk_variable, tab_name, config, 
                        update_callback=None, instance=None):
        """
        Registers a widget for bidirectional state synchronization.

        Inputs:
            widget_id (str): The unique name of the control point.
            tk_variable (Variable): The Tkinter variable object to mirror.
            tab_name (str): The logical container name.
            config (dict): Configuration parameters (min/max, key mapping).
            update_callback (callable, optional): Function to execute when
                the state changes.
            instance (Widget, optional): The physical widget instance, used
                for interaction locking.

        Outputs:
            str: The calculated topic path for the widget.
        """
        if self.is_inert:
            return None
        
        dynamics = config.get("dynamics", {})
        topic_override = dynamics.get("path") or dynamics.get("sub")
        
        if topic_override and (str(topic_override).startswith(self.base_topic + "/") 
                               or str(topic_override).startswith("/")):
            full_topic = self.calculate_topic(topic_override, tab_name)
        else:
            full_topic = self.calculate_topic(widget_id, tab_name)

        with self._registry_lock:
            self.registered_widgets[widget_id] = {
                "var": tk_variable, "tab": tab_name, "id": widget_id,
                "config": config, "update_callback": update_callback,
                "topic": full_topic, "last_broadcast_ts": 0,
                "last_sent_val": None, 
                "instance": instance
            }
            self.topic_to_widget_id[full_topic] = widget_id
            
        if LOCAL_DEBUG:
            state_logger.debug(f"📝📝📝 [REGISTER] Widget '{widget_id}' registered on topic '{full_topic}' (Callback: {update_callback is not None})")

        # ⚡ AUTOMATIC BROADCAST: Attach a trace to ensure any change to this variable
        def _auto_broadcast(*args):
            if LOCAL_DEBUG:
                state_logger.trace(f"🔄🔄🔄 [TRACE] Auto-broadcast triggered for '{widget_id}' (Silent: {self._silent_update}, Suspended: {self._binding_suspended})")
            if not self._silent_update and not self._binding_suspended:
                 self.broadcast_gui_change_to_mqtt(widget_id)
        
        tk_variable.trace_add("write", _auto_broadcast)

        self._registration_queue.put(widget_id)
        return full_topic

    def initialize_widget_state(self, widget_id):
        """
        Populates a widget's initial value from the local state cache.

        Lead with action: Queries the StateCacheManager for the last known
        value of a registered topic and applies it to the widget's variable.
        """
        with self._registry_lock:
            widget_info = self.registered_widgets.get(widget_id)
        if not widget_info:
            return False
        
        full_topic = widget_info["topic"]
        prefix = f"{self.base_topic}/{widget_info['tab']}/"

        if self.state_cache_manager:
            if not self.state_cache_manager.check_prefix_exists(prefix):
                return False

        if (self.state_cache_manager and 
            full_topic in self.state_cache_manager.cache):
            cached = self.state_cache_manager.cache[full_topic]
            try:
                if isinstance(cached, (dict, list)): data = cached
                elif isinstance(cached, (int, float)): data = {"val": cached}
                else: data = orjson.loads(cached)

                tk_var = widget_info["var"]
                data_key = widget_info["config"].get("key")
                
                # Extract the value based on the configured key mapping.
                if data_key and isinstance(data, dict):
                    new_value = data.get(data_key)
                else:
                    new_value = data.get("val", data.get("pos", None))
                
                widget_type = widget_info["config"].get("type", "")
                if (widget_type in ["_GuiButtonToggle", "_WinkButton", 
                                    "_WinkButtonToggler"] or 
                    isinstance(tk_var, tk.BooleanVar)):
                    val_str = str(new_value).lower().strip()
                    final_value = (val_str in ("true", "1", "on") if not 
                                   isinstance(new_value, bool) else new_value)
                elif isinstance(tk_var, (tk.DoubleVar, tk.IntVar)):
                    try:
                        v_min = float(widget_info["config"].get("min", 
                                      widget_info["config"].get("value_min", 0.0)))
                        v_max = float(widget_info["config"].get("max", 
                                      widget_info["config"].get("value_max", 100.0)))
                        final_value = max(v_min, min(v_max, float(new_value)))
                    except:
                        return False
                else:
                    final_value = new_value

                if final_value is not None:
                    with self._registry_lock:
                        widget_info["last_sent_val"] = final_value
                        
                    self.update_queue.put((tk_var, final_value, widget_id))
                    self._schedule_queue_processing() 
                    if widget_info["update_callback"]:
                        cb = widget_info["update_callback"]
                        self.root.after(0, lambda: 
                                        self._safe_execute_callback(cb, data, 
                                                                    widget_id))
                return True
            except:
                return False
        return False

    def broadcast_gui_change_to_mqtt(self, widget_id, extra_payload=None):
        """
        Publishes a local GUI change to the MQTT broker.

        Inputs:
            widget_id (str): The ID of the widget that changed.
            extra_payload (dict, optional): Additional metadata to attach
                to the outgoing message.

        Constraints:
            - Aborts if the engine is 'silent', 'suppressed', or 'suspended'.
            - Implements a 20ms global throttle and 50ms per-widget throttle.
            - Performs a change-only check to prevent redundant updates.
        """
        if (not widget_id or self.is_inert or self._suppress_broadcast or 
            self._silent_update or self._binding_suspended):
            if LOCAL_DEBUG:
                state_logger.trace(f"🔇🔇🔇 [BROADCAST] Aborted for '{widget_id}' (Inert: {self.is_inert}, Suppress: {self._suppress_broadcast}, Silent: {self._silent_update}, Suspended: {self._binding_suspended})")
            return
            
        # Optimization: Ignore high-frequency internal metadata topics.
        if ("/visibility/" in widget_id or "/left_meter" in widget_id or 
            "/right_meter" in widget_id):
            return

        with self._registry_lock:
            widget_info = self.registered_widgets.get(widget_id)
        if not widget_info:
            return
        
        now = time.time()
        # Throttling Logic: Prevent flooding the broker with high-frequency 
        # control data (e.g. from a slider movement).
        if (now - self._last_global_broadcast_ts) < self._GLOBAL_THROTTLE_MS:
            if LOCAL_DEBUG: state_logger.trace(f"⚖️⚖️⚖️ [THROTTLE] Global drop for '{widget_id}'")
            return
        if (now - widget_info.get("last_broadcast_ts", 0)) < 0.050:
            if LOCAL_DEBUG: state_logger.trace(f"⚖️⚖️⚖️ [THROTTLE] Widget drop for '{widget_id}'")
            return
        
        try:
            current_val = widget_info["var"].get()
        except:
            return

        # Purity Check: Only broadcast if the value has actually changed.
        last_val = widget_info.get("last_sent_val")
        if current_val == last_val or str(current_val) == str(last_val):
            if LOCAL_DEBUG: state_logger.trace(f"🤷‍♂️🤷‍♂️🤷‍♂️ [PURITY] No change for '{widget_id}' (Val: {current_val})")
            return

        widget_info["last_sent_val"] = current_val
        widget_info["last_broadcast_ts"] = now
        self._last_global_broadcast_ts = now
        full_topic = widget_info["topic"]

        if self.state_cache_manager:
            self.state_cache_manager.handle_external_update(
                full_topic, 
                current_val, 
                source="GUI",
                metadata=extra_payload
            )
        else:
            from workers.logic.manifest.builder import create_manifest
            payload_data = create_manifest(current_val, full_topic, "GUI", extra_payload)
            mqtt_publisher_service.publish_payload(full_topic, 
                                                   orjson.dumps(payload_data).decode())

    def sync_incoming_mqtt_to_gui(self, msg: MqttMessage):
        """
        Applies a remote MQTT update to the local GUI.

        Lead with action: Parses an incoming MqttMessage and updates the
        corresponding Tkinter variable if the message passes all loop 
        prevention and interaction locking checks.

        Interaction Locking (The "Do Not Disturb" Pattern):
            If a widget's 'is_locked' attribute is True (meaning a human is 
            currently interacting with it), remote updates for that widget 
            are discarded to prevent the control from "jumping" under the
            user's cursor.

        Anti-Feedback (The Golden Rule):
            If 'origin_source' matches the local 'widget_id', we apply the
            value silently (tk_var.set) but do NOT trigger a new broadcast.
        """
        if self.is_inert or not msg.payload:
            return
            
        topic = msg.topic
        try:
            payload = msg.payload
            if isinstance(payload, (dict, list)): data = payload
            elif isinstance(payload, (int, float)): data = {"val": payload}
            else: data = orjson.loads(payload)
            
            if not isinstance(data, dict):
                return
            
            # ⚡ MODULAR ECHO CANCELLATION: Is this us?
            from workers.logic.manifest.echo_canceller import is_echo
            if is_echo(data):
                return

            with self._registry_lock:
                widget_id = self.topic_to_widget_id.get(topic)
                if not widget_id or widget_id not in self.registered_widgets:
                    return
                widget_info = self.registered_widgets[widget_id]
                tk_var = widget_info["var"]
                
                # ⚡ MODULAR GHOST LOCK: Should we let the network in?
                from workers.logic.manifest.ghost_lock import is_ghost_touch_locked
                if is_ghost_touch_locked(data, widget_info.get("instance")):
                    if LOCAL_DEBUG:
                        state_logger.trace(f"🔒 LOCK: Dropping network update "
                                           f"for {topic} - Human in control.")
                    return
                
            is_self_originated = (data.get("origin_source") == widget_id)
            
            try:
                tk_var.get()
            except:
                return

            data_key = widget_info["config"].get("key")
            if data_key and isinstance(data, dict):
                new_value = data.get(data_key)
            else:
                new_value = data.get("val", data.get("pos", None))
            
            if new_value is None:
                return

            # Normalization and type conversion.
            widget_type = widget_info["config"].get("type", "")
            if (widget_type in ["_GuiButtonToggle", "_WinkButton", 
                                "_WinkButtonToggler"] or 
                isinstance(tk_var, tk.BooleanVar)):
                val_str = str(new_value).lower().strip()
                final_value = (val_str in ("true", "1", "on") if not 
                               isinstance(new_value, bool) else new_value)
            elif isinstance(tk_var, (tk.DoubleVar, tk.IntVar)):
                try:
                    v_min = float(widget_info["config"].get("min", 
                                  widget_info["config"].get("value_min", 0.0)))
                    v_max = float(widget_info["config"].get("max", 
                                  widget_info["config"].get("value_max", 100.0)))
                    final_value = max(v_min, min(v_max, float(new_value)))
                except:
                    return
            else:
                final_value = new_value

            if final_value is not None:
                with self._registry_lock:
                    widget_info["last_sent_val"] = final_value
                
                if is_self_originated:
                    # Apply value without triggering outbound broadcast.
                    self._silent_update = True
                    try:
                        tk_var.set(final_value)
                    finally:
                        self._silent_update = False
                else:
                    self.update_queue.put((tk_var, final_value, widget_id))
                    self._schedule_queue_processing()
                
                if widget_info["update_callback"]:
                    cb = widget_info["update_callback"]
                    self.root.after(0, lambda: 
                                    self._safe_execute_callback(cb, data, 
                                                                widget_id))
        except:
            pass

    def _safe_execute_callback(self, callback, data, widget_id):
        """
        Executes a widget callback within a 'silent' context.
        """
        self._silent_update = True
        try:
            callback(data)
        except:
            pass
        finally:
            self._silent_update = False

    def publish_command(self, topic: str, payload: str):
        """
        Directly publishes a command string to a specific MQTT topic.
        """
        if not self.is_inert and not self._silent_update:
            mqtt_publisher_service.publish_payload(topic, payload)

    def initialize_widget_state_from_cache(self, widget_id):
        return self.initialize_widget_state(widget_id)
        
    def is_widget_registered(self, widget_id: str) -> bool:
        """Checks if a widget ID exists in the internal registry."""
        with self._registry_lock:
            return widget_id in self.registered_widgets
            
    def get_widget_topic(self, widget_id):
        """Retrieves the topic path mapped to a specific widget ID."""
        with self._registry_lock:
            if widget_id in self.registered_widgets:
                return self.registered_widgets[widget_id]["topic"]
            return None

