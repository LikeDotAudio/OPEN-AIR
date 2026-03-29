# .gemini/TempScripts/check_midi_state.py
import sys
import os
import pathlib

# Ensure root is in path
root = pathlib.Path('/home/anthony/Documents/OPEN-AIR')
sys.path.insert(0, str(root))

from oaConfiguration.FileReaders.config_reader import Config
from oaStateCache.Core.state_cache import StateRegistry
from oaComMQTT.Managers.mqtt_connection import MqttConnectionManager

def check():
    mqtt = MqttConnectionManager()
    cache = StateRegistry(mqtt)
    
    topics = [
        "OPEN-AIR/System/Status/MIDI/ActiveInputs",
        "OPEN-AIR/System/Status/MIDI/ActiveOutputs"
    ]
    
    print("--- MIDI STATE CHECK ---")
    for t in topics:
        val = cache.get_cached_value(t)
        print(f"{t}: {val}")
    
    # Check for any MIDI topics in cache
    print("\n--- RECENT MIDI TRAFFIC IN CACHE ---")
    found = False
    for t in cache.cache.keys():
        if "/MIDI/" in t:
            print(f"{t}: {cache.get_cached_value(t)}")
            found = True
    if not found:
        print("No MIDI topics found in cache.")

if __name__ == "__main__":
    check()
