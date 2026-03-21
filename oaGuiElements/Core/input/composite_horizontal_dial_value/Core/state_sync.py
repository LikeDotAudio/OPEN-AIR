import math
from loguru import logger

class CompositeStateSync:
    """Manages the synchronization math between the main value, fader (coarse), and dial (fine)."""

    @staticmethod
    def get_format_string(step):
        step = float(step)
        if step == 0: return "{}"
        if step == int(step): return "{:.0f}"
        try:
            decimal_places = len(str(float(step)).split('.')[-1])
        except Exception as e:
            logger.debug(f"Failed to calculate decimal places for step {step}: {e}")
            decimal_places = 2
        return f"{{:.{decimal_places}f}}"

    @staticmethod
    def calculate_initial_fine(initial_value, step_coarse, numerical_step):
        scaled_initial_fine = 0.0
        if numerical_step < step_coarse:
            fine_part = initial_value % step_coarse
            eff_range = step_coarse - numerical_step if (step_coarse - numerical_step) > 0 else step_coarse
            scaled_initial_fine = (fine_part / eff_range) * 999.0
        return round(scaled_initial_fine)

    @staticmethod
    def sync_from_main(main_val, step_coarse, numerical_step, format_string, entry_var, fader_var, dial_widget):
        try:
            entry_var.set(format_string.format(main_val))
            coarse_val = math.floor(main_val / step_coarse) * step_coarse
            fader_var.set(coarse_val)
            if numerical_step < step_coarse:
                fine_part = main_val % step_coarse
                eff_range = step_coarse - numerical_step if (step_coarse - numerical_step) > 0 else step_coarse
                dial_disp = (fine_part / eff_range) * 999.0
                dial_widget.variable.set(round(dial_disp))
                dial_widget._prev_dial_val_for_wrap_detection = round(dial_disp)
            else:
                dial_widget.variable.set(0)
        except Exception as e:
            logger.error(f"Error in sync_from_main: {e}")

    @staticmethod
    def calc_from_fader(fader_val, main_val, step_coarse, numerical_step, min_val, max_val):
        try:
            f_val = round(fader_val / step_coarse) * step_coarse
            fine = main_val % step_coarse if numerical_step < step_coarse else 0
            new_val = round((f_val + fine) / numerical_step) * numerical_step
            return max(min_val, min(max_val, new_val))
        except Exception as e:
            logger.error(f"Error in calc_from_fader: {e}")
            return main_val

    @staticmethod
    def calc_from_dial(ctx):
        """Calculates the new main value based on dial rotation, handling wraps."""
        try:
            # Unpack context for readability
            curr_dial = ctx['curr_dial']
            main_val = ctx['main_val']
            fader_var = ctx['fader_var']
            dial_widget = ctx['dial_widget']
            step_coarse = ctx['step_coarse']
            numerical_step = ctx['numerical_step']
            min_val = ctx['min_val']
            max_val = ctx['max_val']

            if numerical_step < step_coarse:
                if hasattr(dial_widget, '_prev_dial_val_for_wrap_detection'):
                    if dial_widget._prev_dial_val_for_wrap_detection == 999 and curr_dial == 0:
                        fader_var.set(fader_var.get() + step_coarse)
                    elif dial_widget._prev_dial_val_for_wrap_detection == 0 and curr_dial == 999:
                        fader_var.set(fader_var.get() - step_coarse)
                dial_widget._prev_dial_val_for_wrap_detection = curr_dial
                
                base = math.floor(main_val / step_coarse) * step_coarse
                eff_range = step_coarse - numerical_step if (step_coarse - numerical_step) > 0 else step_coarse
                new_fine = round(((curr_dial / 999.0) * eff_range) / numerical_step) * numerical_step
                return max(min_val, min(max_val, round((base + new_fine) / numerical_step) * numerical_step))
        except Exception as e:
            logger.error(f"Error in calc_from_dial: {e}")
        return main_val
