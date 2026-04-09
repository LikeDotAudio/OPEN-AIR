# oaGui/Methods/safe_after_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Mixin to safely manage Tkinter .after() calls and prevent "invalid command name" errors.

import tkinter as tk
from loguru import logger

class SafeAfterMixin:
    """
    A mixin for Tkinter widgets that tracks all scheduled .after() tasks 
    and ensures they are cancelled when the widget is destroyed.
    """
    
    def __init__(self, *args, **kwargs):
        # Note: If this is used as a mixin, __init__ might not be called automatically 
        # depending on the MRO. We should ensure _init_safe_after is called.
        self._init_safe_after()
        super().__init__(*args, **kwargs)

    def _init_safe_after(self):
        """Initializes the task tracking dictionary if not already present."""
        if not hasattr(self, "_scheduled_tasks"):
            self._scheduled_tasks = {}
            # Bind to the <Destroy> event to ensure cleanup
            try:
                self.bind("<Destroy>", self._cleanup_safe_after, add="+")
            except Exception as e:
                # In case self is not a widget but a mixin on something that hasn't initialized yet
                pass

    def safe_after(self, ms, func, *args):
        """
        Schedules a task and tracks its ID.
        
        Args:
            ms (int): Delay in milliseconds.
            func (callable): The function to execute.
            *args: Arguments for the function.
            
        Returns:
            str: The after ID.
        """
        self._init_safe_after()
        
        task_id = None
        
        def wrapper(*f_args):
            if task_id in self._scheduled_tasks:
                del self._scheduled_tasks[task_id]
            if hasattr(self, "winfo_exists") and self.winfo_exists():
                func(*f_args)

        task_id = self.after(ms, wrapper, *args)
        self._scheduled_tasks[task_id] = func
        return task_id

    def safe_after_cancel(self, task_id):
        """Cancels a tracked task."""
        if not task_id: return
        self._init_safe_after()
        if task_id in self._scheduled_tasks:
            try:
                self.after_cancel(task_id)
            except Exception:
                pass
            del self._scheduled_tasks[task_id]

    def _cleanup_safe_after(self, event=None):
        """Cancels all pending tasks. Triggered on <Destroy>."""
        if event and event.widget != self:
            return
            
        if hasattr(self, "_scheduled_tasks"):
            for task_id in list(self._scheduled_tasks.keys()):
                try:
                    self.after_cancel(task_id)
                except Exception:
                    pass
            self._scheduled_tasks.clear()
