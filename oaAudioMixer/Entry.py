# oaAudioMixer/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2150.1
#
# Description: Gatekeeper for the oaAudioMixer module.


import sys
import os
from pathlib import Path
import json
import time

# Add the parent directory of oaAudioMixer to sys.path
script_dir = Path(__file__).parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Ensure the Rust module is compiled and importable
try:
    from oaRustCore import oa_audio_mixer_rs as oaaudiomixer_rs
except ImportError as e:
    print(f"🛑 [FATAL] Rust oaaudiomixer_rs module missing or failed to compile: {e}")
    sys.exit(1)


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


def run_tests():
    """
    Discover and run tests in the local Tests/ directory using unittest via subprocess.
    Ensures isolation and proper sys.path handling.
    """
    import subprocess
    import sys
    import os
    from pathlib import Path

    print(f"📡📥📥 [TEST] {Path(__file__).parent.name}: Starting automated test discovery...")
    current_dir = Path(__file__).parent.absolute()
    test_dir = current_dir / "Tests"
    
    if not test_dir.exists():
        return True

    project_root = current_dir
    while project_root.parent != project_root:
        if (project_root / "GEMINI.md").exists():
            break
        project_root = project_root.parent
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root) + os.pathsep + env.get("PYTHONPATH", "")
    
    try:
        rel_test_dir = os.path.relpath(test_dir, project_root)
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", rel_test_dir, "-p", "test_*.py"],
            cwd=str(project_root),
            env=env,
            capture_output=False
        )
        if result.returncode == 0:
            print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: All tests PASSED.")
            return True
        else:
            print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: Tests FAILED.")
            return False
    except Exception as e:
        print(f"🛑 [ERROR] {Path(__file__).parent.name}: Test discovery failed: {e}")
        return False

def start():
    """Start the module services."""
    print(f"🚀 [START] Starting {Path(__file__).parent.name} services...")
    main()

def stop():
    """Stop the module services."""
    print(f"🛑 [STOP] Stopping {Path(__file__).parent.name} services...")

def status():
    """Get the module status."""
    print(f"📊 [STATUS] Checking {Path(__file__).parent.name} status...")
    return "Running"

if __name__ == "__main__":
    # Absolute FIRST action: run tests
    if not run_tests():
        print("❌ [CRITICAL] Tests failed. Aborting execution.")
        sys.exit(1)
    
    # Standalone execution logic
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "--start":
            start()
        elif cmd == "--stop":
            stop()
        elif cmd == "--status":
            print(f"Status: {status()}")
        else:
            print(f"Unknown command: {cmd}")
    else:
        # Default standalone action if no args
        start()

    "start",
    "stop",
    "status",
    "run_tests",
__all__ = ["start", "stop", "status", "run_tests"]
