# IS12/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2235.1
#
# Description: Gatekeeper for the IS12 module.

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel

# Add the project root to sys.path for absolute imports
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
    from oaComProtocols.oaComNmos.Core.IS12.Interface.schemas import (
        IS12BaseMessage,
        IS12CommandMessage,
        IS12CommandResponseMessage,
        IS12ErrorMessage,
        IS12NotificationMessage,
        IS12SubscriptionMessage,
    )
except ImportError:
    from Interface.schemas import (
        IS12BaseMessage,
        IS12CommandMessage,
        IS12CommandResponseMessage,
    )

class IS12Manager:
    """
    Manages IS-12 NMOS Control Protocol interactions.
    """
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        print(f"IS12Manager initialized with base URL: {self.base_url}")

    async def _send_message(self, endpoint: str, message: IS12BaseMessage) -> BaseModel | None:
        print(f"Attempting to send message to {self.base_url}{endpoint}")
        if isinstance(message, IS12CommandMessage):
            return IS12CommandResponseMessage(
                message_id=f"resp-{message.message_id}",
                timestamp="2026-04-05T15:47:01Z",
                version="1.0.1",
                command_result="Success",
                data={"status": "command_accepted"}
            )
        return None

    async def send_command(self, device_id: str, operation: str, parameters: dict[str, Any] | None = None) -> IS12CommandResponseMessage | None:
        command_message = IS12CommandMessage(
            message_id=f"cmd-{hash(device_id + operation + str(parameters))}",
            timestamp="2026-04-05T15:47:00Z",
            version="1.0.1",
            operation=operation,
            resource_id=device_id,
            parameters=parameters
        )
        response = await self._send_message("/api/v1/commands", command_message)
        if isinstance(response, IS12CommandResponseMessage):
            return response
        return None

    async def close(self):
        print("Closing IS12Manager connections.")

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

def start():
    """Start the module services."""
    print(f"🚀 [START] Starting {Path(__file__).parent.name} services...")

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
            try:
                while True: time.sleep(1)
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
        start()
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            stop()

__all__ = [
    "IS12Manager",
    "start",
    "stop",
    "status",
    "run_tests",
]
