# workers/builder/meter_bar/core/ballistics.py

import time

class BallisticsEngine:
    """Handles the physics math for meter movement, peak tracking, and auto-decay."""
    
    def __init__(self, config):
        self.cfg = config
        self.current_value = config.value_default
        self.target_value = config.value_default
        self.peak_value = config.value_default
        
        self.state = "idle" # idle, tracking, holding, decaying
        self.hold_start_time = 0
        self.peak_hold_start_time = 0
        
        self.overload_expiry = 0
        self.overload_fade_factor = 0.0
        
        self.is_running = False

    def set_target(self, value):
        self.target_value = value
        self.state = "tracking"
        self.is_running = True

    def update(self, dt_ms):
        """
        Updates the internal state based on elapsed time.
        Returns (current_val, peak_val, overload_fade_factor, is_running)
        """
        now_ms = time.time() * 1000
        full_range = self.cfg.max_val - self.cfg.min_val
        if full_range <= 0: full_range = 1.0

        # 1. State Transitions & Target Selection
        if self.state == "holding":
            # Check for transition to decay
            hold_dur = max(self.cfg.hold_time, self.cfg.dwell_time)
            if now_ms - self.hold_start_time >= hold_dur:
                self.state = "decaying"
        
        # Determine the "active" target based on state
        if self.state == "tracking":
            effective_target = self.target_value
        elif self.state == "decaying":
            effective_target = self.cfg.min_val
        else: # idle or holding
            effective_target = self.current_value

        # 2. Main Bar Movement
        diff = effective_target - self.current_value
        
        # Use a relative epsilon for completion check (0.1% of range)
        epsilon = full_range * 0.001
        reached_min = False
        
        if abs(diff) < epsilon:
            # Reached target for current state
            self.current_value = effective_target
            if self.state == "tracking":
                self.state = "holding"
                self.hold_start_time = now_ms
            elif self.state == "decaying":
                self.state = "idle"
                reached_min = True
        else:
            # Determine which time parameter to use
            if diff > 0:
                time_param = self.cfg.attack_ms
            else:
                if self.state == "tracking":
                    # We are tracking a signal that dropped
                    time_param = self.cfg.release_ms
                else:
                    # We are in the auto-decay phase
                    time_param = self.cfg.fall_time
            
            if time_param <= 0:
                self.current_value = effective_target
            else:
                # Calculate physics step
                # Full scale traversal in time_param ms
                step = (full_range / time_param) * dt_ms
                if diff > 0:
                    self.current_value = min(effective_target, self.current_value + step)
                else:
                    self.current_value = max(effective_target, self.current_value - step)

        # 3. Floating Peak Line
        if self.cfg.peak_display:
            if self.current_value > self.peak_value:
                self.peak_value = self.current_value
                self.peak_hold_start_time = now_ms
            else:
                # Decay after hold
                if now_ms - self.peak_hold_start_time >= self.cfg.peak_hold_time:
                    if self.cfg.peak_display_fall_time > 0:
                        p_step = (full_range / self.cfg.peak_display_fall_time) * dt_ms
                        self.peak_value = max(self.cfg.min_val, self.peak_value - p_step)
                    else:
                        self.peak_value = self.current_value

        # 4. Overload LED (Peak Hold Flag)
        if self.cfg.show_peak_hold:
            if self.current_value >= self.cfg.upper_range:
                self.overload_expiry = now_ms + self.cfg.peak_hold_time
                self.overload_fade_factor = 1.0
            else:
                if now_ms < self.overload_expiry:
                    self.overload_fade_factor = 1.0
                elif now_ms < self.overload_expiry + self.cfg.overload_fade_time:
                    if self.cfg.overload_fade_time > 0:
                        elapsed_fade = now_ms - self.overload_expiry
                        self.overload_fade_factor = max(0.0, 1.0 - (elapsed_fade / self.cfg.overload_fade_time))
                else:
                    self.overload_fade_factor = 0.0

        # 5. Activity Check
        is_active = (self.state != "idle")
        if self.cfg.peak_display and (self.peak_value > self.current_value + epsilon): 
            is_active = True
        if self.overload_fade_factor > 0: 
            is_active = True
            
        self.is_running = is_active
        return self.current_value, self.peak_value, self.overload_fade_factor, self.is_running, reached_min
