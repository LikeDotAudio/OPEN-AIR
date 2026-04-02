import os

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Methods/port_utils.py
# Author: Gemini (Collaborator)
# Version: 20260327.1700.1
#
# Description: Utilities for port monitoring and sibling-aware conflict resolution.

import psutil
from loguru import logger

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
    Determines if a process is part of the OPEN-AIR ecosystem.
    Checks PID, Parent PID, and Command Line strings.
    """
    current_pid = os.getpid()
    if proc.pid == current_pid:
        return True
        
    try:
        # Check for shared parent (Supervisor)
        my_parent = psutil.Process(current_pid).parent()
        if my_parent and proc.parent() and my_parent.pid == proc.parent().pid:
            return True
            
        # Check command line for project markers
        cmdline = " ".join(proc.cmdline()).lower()
        if "openair" in cmdline or "oa" in cmdline:
            return True
    except:
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
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"ℹ️ [PORT] Port {port} is held by a friendly/sibling process ({proc.pid}). Skipping zap.", "DEBUG")
        return False

    try:
        logger.warning(f"⚡ [PORT] Zapping UNAUTHORIZED process {proc.pid} ({proc.name()}) on port {port}...")
        proc.terminate()
        proc.wait(timeout=3)
        return True
    except Exception as e:
        logger.error(f"❌ [PORT] Failed to zap unauthorized process: {e}")
        try:
            proc.kill()
            return True
        except:
            pass
    return False