# oaStateCache/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2215.1
#
# Description: Gatekeeper for the oaStateCache module.
# The sole orchestrator for the State Cache Module.

import os
import sys
import subprocess
import time
from pathlib import Path

# Add the project root to sys.path for relative imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir
while project_root.parent != project_root:
    if (project_root / "GEMINI.md").exists():
        break
    project_root = project_root.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Absolute imports with fallback
try:
    from oaStateCache.Core.state_cache import StateRegistry
    from oaStateCache.Core.state_mirror_engine import StateMirrorEngine
except ImportError:
    from Core.state_cache import StateRegistry
    from Core.state_mirror_engine import StateMirrorEngine

_instance = None

def get_registry(mqtt_connection_manager=None, state_mirror_engine=None):
    """Returns the singleton StateRegistry instance."""
    global _instance
    if _instance is None:
        _instance = StateRegistry(mqtt_connection_manager, state_mirror_engine)
    return _instance

def start(mqtt_connection_manager=None, state_mirror_engine=None):
    """
    Initializes and starts the State Cache service.
    """
    print(f"🚀 [START] Starting {Path(__file__).parent.name} services...")
    
    # If no MQTT manager is provided and we are in standalone mode, 
    # we might need to initialize a default one or handle the lack thereof.
    # For now, we'll try to get the registry and then tell it to subscribe if possible.
    
    registry = get_registry(mqtt_connection_manager, state_mirror_engine)
    registry.initialize_state()
    
    # ⚡ V3.1.25 MQTT SYNC:
    # If we have an MQTT manager, ensure we subscribe to all topics to "get all the MQTT things".
    if registry.mqtt:
        print(f"📡 [MQTT] Synchronizing {Path(__file__).parent.name} with MQTT fabric...")
        registry.subscribe_to_all_topics()
    else:
        print(f"⚠️ [WARN] {Path(__file__).parent.name} started without MQTT manager. Network sync disabled.")
        
    return registry

def stop():
    """
    Shuts down the State Cache service.
    """
    global _instance
    if _instance:
        print(f"🛑 [STOP] Stopping {Path(__file__).parent.name} services...")
        _instance.shutdown()
        _instance = None

def status():
    """Returns the current status of the State Registry."""
    return "active" if _instance else "stopped"

def run_tests():
    """
    Discover and run tests in the local Tests/ directory using unittest via subprocess.
    Ensures isolation and proper sys.path handling.
    """
    print(f"📡📥📥 [TEST] {Path(__file__).parent.name}: Starting automated test discovery...")
    test_dir = current_dir / "Tests"
    
    if not test_dir.exists():
        print(f"⚠️ [TEST] {Path(__file__).parent.name}: No Tests/ directory found.")
        return True

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
        if result.returncode in [0, 5]:
            if result.returncode == 5:
                print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: No tests found, but discovery succeeded.")
            else:
                print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: All tests PASSED.")
            return True
        else:
            print(f"📡📤📤 [TEST] {Path(__file__).parent.name}: Tests FAILED.")
            return False
    except Exception as e:
        print(f"🛑 [ERROR] {Path(__file__).parent.name}: Test discovery failed: {e}")
        return False

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
            # Keep alive for standalone mode if started
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                stop()
        elif cmd == "--stop":
            stop()
        elif cmd == "--status":
            print(f"Status: {status()}")
        else:
            print(f"Unknown command: {cmd}")
    else:
        # Default standalone action if no args
        # In standalone mode, we might want to try and bootstrap a default MQTT manager
        # for testing purposes, but for now we follow the pattern.
        start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop()

__all__ = ["StateRegistry", "StateMirrorEngine", "get_registry", "start", "stop", "status", "run_tests"]
