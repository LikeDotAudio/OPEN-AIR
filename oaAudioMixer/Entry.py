# oaAudioMixer/Entry.py
# Author: Gemini (Collaborator)
# Version: 20260403.2350.31
#
# Description: Entry point for the oaAudioMixer module.
# Discovers OS-specific audio backend and provides an interface.

import sys
import os
import json
import time
from pathlib import Path

# Add the parent directory of oaAudioMixer to sys.path
script_dir = Path(__file__).parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Ensure the Rust module is compiled and importable
try:
    from oaAudioMixer.Core.oaAudioMixer_rs.compiler_hook import ensure_compiled
    ensure_compiled()
    import oaaudiomixer_rs
except ImportError as e:
    print(f"🛑 [FATAL] Rust oaaudiomixer_rs module missing or failed to compile: {e}")
    sys.exit(1)

__all__ = ["main"]

def main():
    """
    Main entry point for the oaAudioMixer module.
    Discovers OS-specific audio backend and prints information.
    """
    print("📡 [AUDIO] Initializing OS-specific Audio Mixer...")
    mixer = oaaudiomixer_rs.AudioMixer()

    output_data = {}

    # Get Master Volume
    try:
        volume = mixer.get_master_volume()
        print(f"🔊 Current Master Volume: {volume:.2f}")
        output_data["master_volume"] = volume
    except Exception as e:
        print(f"❌ Failed to get master volume: {e}")
        output_data["master_volume_error"] = str(e)

    # Get Available Devices
    try:
        devices = mixer.get_available_devices()
        print("🔈 Available Audio Devices:")
        output_data["available_devices"] = []
        for dev in devices:
            default_str = " (DEFAULT)" if dev['is_default'] else ""
            print(f"  - {dev['description']} [{dev['sample_rate']}Hz, {dev['channels']}ch]{default_str}")
            print(f"    ID: {dev['name']}")
            print(f"    Volume: {dev['volume']:.2f}")
            output_data["available_devices"].append(dev)
            
            # TEST: Set volume of the first device (or default) to demonstrate ability
            # We'll set it to 0.45 and then back to its original volume
            # if dev['is_default']:
            #     print(f"🧪 [TEST] Setting volume of {dev['name']} to 0.45...")
            #     mixer.set_device_volume(dev['name'], 0.45)
            #     time.sleep(1)
            #     print(f"🧪 [TEST] Restoring volume of {dev['name']} to {dev['volume']:.2f}...")
            #     mixer.set_device_volume(dev['name'], dev['volume'])

    except Exception as e:
        print(f"❌ Failed to get available devices: {e}")
        output_data["available_devices_error"] = str(e)

    # Get Connected Software
    try:
        apps = mixer.get_connected_software()
        print("🎧 Connected Audio Applications:")
        output_data["connected_software"] = []
        for app in apps:
            print(f"  - Name: {app['name']}, PID: {app['pid']}, Driver: {app['driver']}, Active: {app['is_active']}")
            output_data["connected_software"].append(app)
    except Exception as e:
        print(f"❌ Failed to get connected software: {e}")
        output_data["connected_software_error"] = str(e)

    # Save to JSON file
    output_dir = Path(os.path.dirname(__file__))
    json_file_path = output_dir / "oaAudioMixer_discovery.json"

    try:
        with open(json_file_path, 'w') as f:
            json.dump(output_data, f, indent=4)
        print(f"\n✅ Discovered audio devices saved to: {json_file_path}")
    except Exception as e:
        print(f"❌ Failed to save JSON output: {e}")

def tui():
    """
    Launches the Textual TUI for the Audio Mixer.
    """
    from oaAudioMixer.Interface.MixerUI import MixerApp
    app = MixerApp()
    app.run()

if __name__ == '__main__':
    # Default to TUI unless --discovery is specified
    if "--discovery" in sys.argv:
        main()
    else:
        tui()
