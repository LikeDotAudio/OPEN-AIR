# oaGui/Methods/deferred_task_handler.py
# Author: Anthony Peter Kuzub
# Version: 1.0.1
#
# Description: Mixin to safely manage deferred Tkinter events and prevent "invalid command name" errors.


class DeferredTaskHandler:
    """
    A handler for Tkinter widgets that tracks all scheduled deferred tasks 
    and ensures they are cancelled when the widget is destroyed.
    """

    def __init__(self, *args, **kwargs):
        self._init_deferred_handler()
        super().__init__(*args, **kwargs)

    def _init_deferred_handler(self):
        """Initializes the task tracking dictionary if not already present."""
        if not hasattr(self, "_scheduled_tasks"):
            self._scheduled_tasks = {}
            # Bind to the <Destroy> event to ensure cleanup
            try:
                self.bind("<Destroy>", self._cleanup_deferred_tasks, add="+")
            except Exception:
                # In case self is not a widget but a mixin on something that hasn't initialized yet
                pass

    def defer_execution(self, delay_ms, callback, *args):
        """
        Schedules a deferred task and tracks its ID.
        
        Args:
            delay_ms (int): Delay in milliseconds.
            callback (callable): The function to execute.
            *args: Arguments for the function.
            
        Returns:
            str: The task ID.
        """
        self._init_deferred_handler()

        task_id = None

        def wrapper(*f_args):
            if task_id in self._scheduled_tasks:
                del self._scheduled_tasks[task_id]
            if hasattr(self, "winfo_exists") and self.winfo_exists():
                callback(*f_args)

        task_id = self.after(delay_ms, wrapper, *args)
        self._scheduled_tasks[task_id] = callback
        return task_id

    def cancel_deferred(self, task_id):
        """Cancels a tracked deferred task."""
        if not task_id: return
        self._init_deferred_handler()
        if task_id in self._scheduled_tasks:
            try:
                self.after_cancel(task_id)
            except Exception:
                pass
            del self._scheduled_tasks[task_id]

    def _cleanup_deferred_tasks(self, event=None):
        """Cancels all pending deferred tasks. Triggered on <Destroy>."""
        if event and event.widget != self:
            return

        if hasattr(self, "_scheduled_tasks"):
            for task_id in list(self._scheduled_tasks.keys()):
                try:
                    self.after_cancel(task_id)
                except Exception:
                    pass
            self._scheduled_tasks.clear()

    # Legacy Aliases for Backward Compatibility
    def defer(self, ms, func, *args): return self.defer_execution(ms, func, *args)
    def safe_after(self, ms, func, *args): return self.defer_execution(ms, func, *args)
    def safe_after_cancel(self, task_id): return self.cancel_deferred(task_id)
    def _cleanup_safe_after(self): return self._cleanup_deferred_tasks()
    def _init_safe_after(self): return self._init_deferred_handler()
