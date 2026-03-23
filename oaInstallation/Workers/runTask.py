# Workers/runTask.py
# Author: Anthony Peter Kuzub
# Version: 20260323.2005.1
#
# Description: Background worker for executing installation and system tasks.

import asyncio
from typing import Callable, Coroutine, Any

class TaskWorker:
    """
    Orchestrates the execution of background tasks for the installation process.
    Ensures that tasks are run without blocking the UI thread.
    """
    def __init__(self, log_callback: Callable[[str], None]):
        self.log_callback = log_callback

    async def execute(self, task_coro: Coroutine[Any, Any, Any]) -> Any:
        """
        Executes a given coroutine task and handles standard logging or errors.
        """
        try:
            return await task_coro
        except Exception as e:
            self.log_callback(f"⚠️ [WORKER ERROR] Task failed: {e}")
            return False

def run_background_task(app: Any, coro: Coroutine[Any, Any, Any], group: str = "default") -> None:
    """
    Helper function to launch a coroutine as a Textual worker.
    """
    app.run_worker(coro, group=group, thread=False)
