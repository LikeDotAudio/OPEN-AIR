# active/active_marker_tune_and_collect.py
#
# Modularized Marker Go-Getter Worker.
# Version 20260315.Modular.1

import os
import orjson
import threading
import time
from loguru import logger

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    
from oaConfiguration.config_reader import Config
app_constants = Config.get_instance()

from oaComMQTT.mqtt_controller_util import MqttControllerUtility

# --- EXTRACTED CORE MODULES ---
from oaGuiTelemetry.core.instrument_controller import InstrumentController
from oaGuiTelemetry.core.marker_repository_watcher import MarkerRepositoryWatcher
from oaGuiTelemetry.core.tuning_helpers import Push_Marker_to_Center_Freq, Push_Marker_to_Start_Stop_Freq

# Constants
BUFFER_START_STOP_MHZ = 0.1
HZ_TO_MHZ = 1_000_000

# Topics
TOPIC_START_STOP = "OPEN-AIR/configuration/Start-Stop-Pause/Buttons/options/START/selected"
TOPIC_MARKERS_ROOT = "OPEN-AIR/repository/markers"
TOPIC_DEVICE_FREQ_WILDCARD = f"{TOPIC_MARKERS_ROOT}/+/IDENTITY/FREQ_MHZ"
TOPIC_MARKER_NAB_OUTPUT_WILDCARD = "OPEN-AIR/yak/Markers/nab/NAB_all_marker_settings/Outputs/Marker_*/value"

class MarkerGoGetterWorker:
    """
    Continuous peak retrieval worker for spectrum marker monitoring.
    """

    def __init__(self, mqtt_util: MqttControllerUtility):
        if LOCAL_DEBUG: logger.debug("🟢️️️🟢 Initializing the tireless Marker Go-Getter!")

        self.mqtt_util = mqtt_util
        self.stop_event = threading.Event()
        self.processing_thread = None
        
        # Modular Components
        self.instrument = InstrumentController(mqtt_util)
        self.repository = MarkerRepositoryWatcher()
        
        # State Tracking
        self.last_min_freq = None
        self.last_max_freq = None
        self.first_run = True
        self.peaks_received_event = threading.Event()

        self._setup_subscriptions()

    def _setup_subscriptions(self):
        """Sets up all required MQTT listeners."""
        self.mqtt_util.add_subscriber(TOPIC_START_STOP, self._handle_start_stop)
        self.mqtt_util.add_subscriber(f"{TOPIC_MARKERS_ROOT}/total_devices", self._on_marker_data_update)
        self.mqtt_util.add_subscriber(f"{TOPIC_MARKERS_ROOT}/min_frequency_mhz", self._on_marker_data_update)
        self.mqtt_util.add_subscriber(f"{TOPIC_MARKERS_ROOT}/max_frequency_mhz", self._on_marker_data_update)
        self.mqtt_util.add_subscriber(TOPIC_DEVICE_FREQ_WILDCARD, self._on_marker_data_update)
        self.mqtt_util.add_subscriber(TOPIC_MARKER_NAB_OUTPUT_WILDCARD, lambda t, p: self.peaks_received_event.set())

        logger.success("✅ Go-Getter is now listening for commands and marker data.")

    def _on_marker_data_update(self, topic, payload):
        self.repository.on_marker_update(topic, payload)

    def _handle_start_stop(self, topic, payload):
        try:
            try:
                is_start_command = str(orjson.loads(payload).get("value")).lower() == "true"
            except:
                is_start_command = str(payload).lower() == "true"

            if is_start_command and (self.processing_thread is None or not self.processing_thread.is_alive()):
                logger.debug("🟢 START command received. Beginning peak hunter loop.")
                self.stop_event.clear()
                self.first_run = True
                self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
                self.processing_thread.start()
            elif not is_start_command:
                logger.debug("🔴 STOP command received. Halting loop.")
                self.stop_event.set()
                if self.processing_thread: self.processing_thread.join(timeout=0.5)
                self.processing_thread = None
        except Exception as e:
            logger.error(f"❌ Error in start/stop handler: {e}")

    def _set_instrument_frequency_span(self):
        """Calculates and updates instrument span with buffer."""
        repo = self.repository
        if repo.min_frequency_mhz == self.last_min_freq and repo.max_frequency_mhz == self.last_max_freq and not self.first_run:
            return

        self.last_min_freq, self.last_max_freq = repo.min_frequency_mhz, repo.max_frequency_mhz
        new_min = max(0, repo.min_frequency_mhz - BUFFER_START_STOP_MHZ)
        new_max = repo.max_frequency_mhz + BUFFER_START_STOP_MHZ
        
        self.instrument.set_span(new_min, new_max)
        self.first_run = False

    def _processing_loop(self):
        """Orchestrates the batch marker query sequence."""
        if LOCAL_DEBUG: logger.success("✅ Peak Hunter loop started.")

        while not self.stop_event.is_set():
            self._set_instrument_frequency_span()
            device_ids = sorted(self.repository.marker_frequencies.keys())

            for i in range(0, len(device_ids), 6):
                if self.stop_event.is_set(): break
                batch_ids = device_ids[i : i + 6]
                batch_freqs = [self.repository.marker_frequencies[did] for did in batch_ids]
                
                # 1. Place Markers
                self.instrument.place_markers_batch(batch_freqs)
                time.sleep(0.3)
                
                # 2. Query NAB
                self.instrument.trigger_nab_query()
                logger.success(f"✅ Batch {i//6 + 1} processed.")

            if LOCAL_DEBUG: logger.success("✅ Full marker pass finished.")
            time.sleep(1.0)
