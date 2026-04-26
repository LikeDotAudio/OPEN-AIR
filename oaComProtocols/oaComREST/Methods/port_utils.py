import os

# Methods/port_utils.py
# Author: Gemini (Collaborator)
# Version: 20260327.1700.1
#
# Description: Utilities for port monitoring and sibling-aware conflict resolution.
import psutil
from loguru import logger

from oaLogging.Methods.matrix_gate import matrix_log


def get_process_on_port(port):
    """Identifies the process currently listening on the specified port."""
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN' and conn.laddr.port == port:
                return psutil.Process(conn.pid)
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        pass
    return None

def is_friendly_process(proc):
    """
    Determines if a process is part of the SAME OPEN-AIR supervisor session.
    Checks PID, Parent PID, and the OPEN_AIR_INSTANCE_GUID environment variable.
    """
    current_pid = os.getpid()
    if proc.pid == current_pid:
        return True

    try:
        # 1. Check for shared parent (Supervisor)
        my_proc = psutil.Process(current_pid)
        my_parent = my_proc.parent()
        proc_parent = proc.parent()
        if my_parent and proc_parent and my_parent.pid == proc_parent.pid:
            return True

        # 2. Check for Session Identity GUID (Environment Injection)
        # This is the most reliable way to identify siblings from the same run.
        my_env = my_proc.environ()
        proc_env = proc.environ()

        my_guid = my_env.get("OPEN_AIR_INSTANCE_GUID")
        proc_guid = proc_env.get("OPEN_AIR_INSTANCE_GUID")

        if my_guid and proc_guid and my_guid == proc_guid:
            return True

        # ⚡ V3.1.28 STRICTNESS:
        # We NO LONGER consider any process with "openair" in the cmdline as friendly.
        # This allows a new supervisor run to "Zap" orphans from a previous crashed run.

    except (psutil.AccessDenied, psutil.NoSuchProcess):
        pass
    return False

def zap_port(port):
    """
    Attempts to terminate EXTERNAL processes found listening on the target port.
    Will NOT kill siblings, parents, or self.
    """
    proc = get_process_on_port(port)
    if not proc:
        return False

    if is_friendly_process(proc):
        matrix_log("comms", "rest", "zap_port", f"ℹ️ [PORT] Port {port} is held by a friendly/sibling process ({proc.pid}). Skipping zap.", "DEBUG")
        return False

    try:
        pid = proc.pid
        name = proc.name()
        logger.warning(f"⚡ [PORT] Zapping UNAUTHORIZED process {pid} ({name}) on port {port}...")

        proc.terminate()
        try:
            # ⚡ INCREASED TIMEOUT: Give process more time to close files/sockets
            proc.wait(timeout=3)
            return True
        except psutil.TimeoutExpired:
            logger.warning(f"⚠️ [PORT] Process {pid} did not terminate gracefully. Escalating to SIGKILL...")
            proc.kill()
            try:
                proc.wait(timeout=2)
                # Small sleep to allow OS to actually release the port binding
                import time
                time.sleep(0.5)
                return True
            except psutil.TimeoutExpired:
                logger.error(f"❌ [PORT] Failed to zap unauthorized process: timeout after wait (pid={pid}, name='{name}')")
                return False

    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        logger.error(f"❌ [PORT] Access denied or process vanished while zapping {port}: {e}")
    except Exception as e:
        logger.error(f"❌ [PORT] Unexpected failure zapping {port}: {e}")

    return False
