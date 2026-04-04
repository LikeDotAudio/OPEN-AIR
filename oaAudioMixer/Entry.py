# oaAudioMixer/Entry.py
# Author: Gemini (Collaborator)
# Version: 20260403.2300.2
#
# Description: Entry point for the oaAudioMixer module.
# Discovers OS-specific audio backend and provides an interface.

import sys
import os
import json
from pathlib import Path

# Add the parent directory of oaAudioMixer to sys.path
script_dir = Path(__file__).parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Explicitly add the site-packages of the virtual environment
# This is where maturin develop usually installs editable packages.
venv_path = Path(sys.executable).parent.parent
site_packages_path = venv_path / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
if site_packages_path.exists() and str(site_packages_path) not in sys.path:
    sys.path.insert(0, str(site_packages_path))

# Ensure the Rust module is compiled and importable
try:
    # This might trigger a compilation if not already done
    from oaAudioMixer.Core.oaAudioMixer_rs.compiler_hook import ensure_compiled
    # maturin develop installs into the site-packages or directly next to the source
    # The ensure_compiled function handles adding the correct path for direct import.
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
        print(f"🔊 Master Volume: {volume:.2f}")
        output_data["master_volume"] = volume
    except Exception as e:
        print(f"❌ Failed to get master volume: {e}")
        output_data["master_volume_error"] = str(e)

    # Get Connected Software
    try:
        apps = mixer.get_connected_software()
        print("🎧 Connected Audio Applications:")
        output_data["connected_software"] = []
        for app in apps:
            print(f"  - Name: {app['name']}, Active: {app['is_active']}")
            output_data["connected_software"].append(app)
    except Exception as e:
        print(f"❌ Failed to get connected software: {e}")
        output_data["connected_software_error"] = str(e)

    # Save to JSON file
    output_dir = Path(os.path.dirname(__file__)) # Current directory of Entry.py
    json_file_path = output_dir / "oaAudioMixer_discovery.json"

    try:
        with open(json_file_path, 'w') as f:
            json.dump(output_data, f, indent=4)
        print(f"\n✅ Discovered audio devices saved to: {json_file_path}")
        print("\n--- Saved JSON Content ---")
        print(json.dumps(output_data, indent=4))
        print("--------------------------")
    except Exception as e:
        print(f"❌ Failed to save JSON output: {e}")

if __name__ == '__main__':
    main()
