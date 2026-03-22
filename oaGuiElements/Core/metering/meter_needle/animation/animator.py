# animation/animator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import time

class MeterAnimator:
    def __init__(self, frame, config, canvas, draw_callback):
        self.frame = frame
        self.config = config
        self.canvas = canvas
        self.draw_callback = draw_callback
        
        # Initialize Frame State
        self.frame.anim_current_value = self.config.value_default
        self.frame.anim_target = self.config.value_default
        self.frame.anim_current_value_2 = self.config.value_default
        self.frame.anim_target_2 = self.config.value_default
        
        self.frame.anim_mode = "idle" # idle, tracking, holding, decaying
        self.frame.anim_hold_start = 0
        self.frame.anim_running = False
        self.frame.anim_peak_expiry = 0
        self.frame.anim_peak_on = False

    def start_animation(self):
        if not self.frame.anim_running:
            self.frame.anim_running = True
            self.animate()

    def update_target(self, new_value):
        self.frame.anim_target = new_value
        self.frame.anim_mode = "tracking"
        self.start_animation()

    def update_target_2(self, new_value):
        self.frame.anim_target_2 = new_value
        self.frame.anim_mode = "tracking"
        self.start_animation()

    def reset_peak(self, event=None):
        self.frame.anim_peak_expiry = 0
        self.frame.anim_peak_on = False
        self.draw_callback()

    def animate(self):
        dt = 20.0 # milliseconds per frame
        full_range = self.config.max_val - self.config.min_val
        if full_range <= 0: full_range = 1.0

        # --- State Machine Logic ---
        if self.frame.anim_mode == "holding":
            # Check if hold time expired
            if (time.time() * 1000) - self.frame.anim_hold_start >= self.config.hold_time:
                self.frame.anim_mode = "decaying"
            else:
                # Still holding, just wait
                self.canvas.after(int(dt), self.animate)
                return

        targets = [self.frame.anim_target]
        currents = [self.frame.anim_current_value]
        
        if self.config.meter_mode == "stereo":
            targets.append(self.frame.anim_target_2)
            currents.append(self.frame.anim_current_value_2)

        new_currents = []
        all_done = True

        for i, current in enumerate(currents):
            # Determine target based on mode
            if self.frame.anim_mode == "tracking":
                target = targets[i]
            elif self.frame.anim_mode == "decaying":
                target = self.config.resting_point
            else: # idle
                target = current 

            diff = target - current
            
            # Check for completion of current move
            if abs(diff) < 0.05: # Threshold
                new_currents.append(target)
            else:
                all_done = False
                step = 0.0
                time_param = 0.0
                
                if diff > 0: # Rising
                    time_param = self.config.glide_time
                else: # Falling
                    if self.frame.anim_mode == "tracking":
                        time_param = self.config.dwell_time
                    else:
                        time_param = self.config.fall_time
                
                if time_param <= 0:
                    step = diff # Instant
                else:
                    max_step = (full_range / time_param) * dt
                    # Clamp step to diff to avoid overshoot
                    if diff > 0:
                        step = min(diff, max_step)
                    else:
                        step = max(diff, -max_step)
                new_currents.append(current + step)

        self.frame.anim_current_value = new_currents[0]
        if self.config.meter_mode == "stereo":
            self.frame.anim_current_value_2 = new_currents[1]

        self.draw_callback()
        
        if all_done:
            if self.frame.anim_mode == "tracking":
                # Reached tracking target
                if self.config.hold_time > 0:
                    self.frame.anim_mode = "holding"
                    self.frame.anim_hold_start = time.time() * 1000
                else:
                    self.frame.anim_mode = "decaying"
                self.canvas.after(int(dt), self.animate)
            elif self.frame.anim_mode == "decaying":
                # Reached resting_point (decay complete)
                self.frame.anim_mode = "idle"
                self.frame.anim_running = False
        else:
            self.canvas.after(int(dt), self.animate)
