import time
from workers.logger.logger import builder_logger
from workers.builder.widgets.graphing.graphing import graph_updater

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True

class GraphThrottleMixin:
    """Implements 30 FPS throttling and redundancy filtering for graph updates."""

    def _initialize_throttle(self):
        self._update_pending = False
        self._pending_data = {}
        self._last_draw_time = 0
        self._THROTTLE_MS = 33 
        self._last_csv_data = {}
        self._last_settings_vals = {}
        self._force_redraw = False

    def _schedule_update(self):
        if self._update_pending: return
        self._update_pending = True
        elapsed = (time.time() * 1000) - self._last_draw_time
        self.after(max(1, self._THROTTLE_MS - int(elapsed)), self._perform_scheduled_update)

    def _perform_scheduled_update(self):
        self._update_pending = False
        self._last_draw_time = time.time() * 1000
        has_changes = False
        
        for ds_id, (x_vals, y_vals) in list(self._pending_data.items()):
            if ds_id in self.lines:
                ds_config = self.datasets_config.get(ds_id, {})
                smoothing = int(ds_config.get("style", {}).get("smoothing", 0))
                graph_updater.load_initial_data(self.lines[ds_id], self.x_data[ds_id], self.y_data[ds_id], x_vals, y_vals, smoothing=smoothing)
                has_changes = True
        self._pending_data.clear()
        
        if has_changes or self._force_redraw:
            if not self._force_redraw:
                graph_updater.perform_fast_blit(self.ax, self.canvas, list(self.lines.values()))
            else:
                graph_updater.autoscale_and_redraw(self.ax, self.canvas)
            self._force_redraw = False
