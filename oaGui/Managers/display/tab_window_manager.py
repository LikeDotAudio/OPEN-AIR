# Managers/tab_window_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1001.1
#
# Description: Manages Toplevel windows for tear-off tabs.

from ..tabs.tab_re_attachment_service import re_attach_liberated_tab
from ..tabs.tab_tear_off_orchestrator import liberate_notebook_tab


class TabWindowManager:
    """Manages Toplevel windows for tear-off tabs using atomic services."""

    def __init__(self, application_instance):
        self.application = application_instance
        self.torn_off_windows = {}

    def tear_off_tab(self, event):
        """Liberates a tab via atomic service."""
        liberate_notebook_tab(self, event)

    def _on_tear_off_window_close(self, top_level_window):
        """Re-attaches a tab via atomic service."""
        re_attach_liberated_tab(self, top_level_window)

    def re_attach_tab(self, torn_off_window_id):
        """Placeholder for manual re-attachment logic."""
        pass
