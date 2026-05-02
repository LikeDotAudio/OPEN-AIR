# Methods/horizontal_fader_renderer.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose
import math

from oaGui.Methods.formatting.i18n_utils import get_text
from oaGuiElements.Core.faders.fader_horizontal.Core.horizontal_fader_asset_generator import (
    HorizontalFaderAssetGenerator,
)
from oaStyle.Core.style import DEFAULT_THEME, THEMES


class HorizontalFaderRendererMixin:
    """Handles the rendering logic for the horizontal linear fader."""

    def render(self):
        if not self.winfo_exists(): return
        canvas_width, canvas_height = float(self.canvas.winfo_width()), float(self.canvas.winfo_height())

        MIN_RENDER_DIM = 1
        if canvas_width <= MIN_RENDER_DIM:
            canvas_width, canvas_height = self.width, self.height

        for item in self.canvas.find_all():
            if "panel_bg_slice" not in self.canvas.gettags(item):
                self.canvas.delete(item)

        if hasattr(self.canvas, 'panel_bg_image') and not self.canvas.find_withtag("panel_bg_slice"):
            self.canvas.create_image(0, 0, image=self.canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")

        center_y = canvas_height / 2.0
        theme_colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        accent_color = theme_colors.get("accent", "#f4902c")

        label_text = get_text(self.configuration.get("label_active"))
        if label_text:
            DEFAULT_LABEL_FONT_SIZE = 9
            font_size = int(float(self.configuration.get("layout", {}).get("font", DEFAULT_LABEL_FONT_SIZE)))
            LABEL_OFFSET_Y = 22
            self.canvas.create_text(canvas_width / 2.0, center_y - LABEL_OFFSET_Y, text=label_text, fill="white", font=("Arial", font_size, "bold"), anchor="s", tags="static")

        cap_scale = float(self.configuration.get("fader_cap_scale", 1.0))
        DEFAULT_CAP_WIDTH = 50
        DEFAULT_CAP_HEIGHT = 55
        cap_width = int(float(self.configuration.get("cap_width", DEFAULT_CAP_WIDTH)) * cap_scale)
        cap_height = int(float(self.configuration.get("cap_height", DEFAULT_CAP_HEIGHT)) * cap_scale)

        CAP_MARGIN_X = 10.0
        padding_x = cap_width / 2.0 + CAP_MARGIN_X

        TRACK_SLOT_OUTSET = 5
        TRACK_SLOT_HALF_HEIGHT = 4
        self.canvas.create_rectangle(padding_x - TRACK_SLOT_OUTSET, center_y - TRACK_SLOT_HALF_HEIGHT,
                                     canvas_width - padding_x + TRACK_SLOT_OUTSET, center_y + TRACK_SLOT_HALF_HEIGHT,
                                     fill="#050505", outline="#222", width=1, tags=("static", "track_slot"))

        TRACK_LINE_WIDTH = 2
        self.canvas.create_line(padding_x, center_y, canvas_width - padding_x, center_y, fill="#222", width=TRACK_LINE_WIDTH, tags="static")
        self.canvas.create_line(padding_x, center_y, padding_x, center_y, fill=self.configuration.get("value_highlight_color", accent_color), width=TRACK_LINE_WIDTH, tags="fill_line")

        self._draw_ticks(canvas_width, canvas_height, center_y, padding_x)

        self.cap_img = HorizontalFaderAssetGenerator.get_3d_cap(cap_width, cap_height, self.configuration.get("cap_color", "#dcdcdc"), "#111", highlight_color=self.configuration.get("cap_highlight_color"))
        self.canvas.create_image(padding_x, center_y, image=self.cap_img, tags="fader_cap")
        self.canvas.cap_img = self.cap_img

        FLOATING_VAL_OFFSET_Y = 25
        FLOATING_VAL_FONT_SIZE = 7
        self.canvas.create_text(padding_x, center_y - FLOATING_VAL_OFFSET_Y, text="", fill="white", font=("Arial", FLOATING_VAL_FONT_SIZE, "bold"), tags="floating_val", state="hidden")
        self._update_positions()

    def _draw_ticks(self, canvas_width, canvas_height, center_y, padding_x):
        value_range = self.max_val - self.min_val
        tick_interval = self.configuration.get("tick_interval")

        if tick_interval is None:
            if value_range > 0:
                TICKS_PER_SPAN = 10.0
                raw_interval = value_range / TICKS_PER_SPAN
                exponent = math.floor(math.log10(raw_interval))
                fractional_part = raw_interval / (10**exponent)

                # Snap to nice numbers
                if fractional_part < 1.5: snap_value = 1
                elif fractional_part < 3.5: snap_value = 2
                elif fractional_part < 7.5: snap_value = 5
                else: snap_value = 10

                tick_interval = snap_value * (10**exponent)
            else:
                DEFAULT_INTERVAL = 10
                tick_interval = DEFAULT_INTERVAL

        tick_values = []
        if float(tick_interval) > 0:
            current_tick = math.ceil(self.min_val / float(tick_interval)) * float(tick_interval)
            while current_tick <= self.max_val:
                tick_values.append(current_tick)
                current_tick += float(tick_interval)

        num_ticks = len(tick_values)
        # Determine label and sub-tick density
        if num_ticks > 5000: label_every = 500
        elif num_ticks > 1000: label_every = 200
        elif num_ticks > 500: label_every = 50
        elif num_ticks > 250: label_every = 20
        elif num_ticks > 100: label_every = 10
        elif num_ticks > 50: label_every = 5
        elif num_ticks > 20: label_every = 2
        else: label_every = 1

        if label_every >= 500: sub_tick_every = 100
        elif label_every >= 200: sub_tick_every = 50
        elif label_every >= 50: sub_tick_every = 10
        elif label_every >= 20: sub_tick_every = 5
        elif label_every >= 10: sub_tick_every = 2
        else: sub_tick_every = 1

        usable_width = canvas_width - (padding_x * 2.0)
        tick_color = self.configuration.get("tick_color", "light grey")
        sub_tick_color = self.configuration.get("sub_tick_color", "#555")

        for index, tick_value in enumerate(tick_values):
            norm_val = (tick_value - self.min_val) / value_range if value_range else 0
            tick_x = (usable_width * (max(0.0, min(1.0, norm_val))**(1.0 / self.log_exponent))) + padding_x

            if index % sub_tick_every == 0:
                TICK_START_Y = center_y + 8
                TICK_END_Y = center_y + 14 # Corrected line
                color = tick_color if index % label_every == 0 else sub_tick_color
                self.canvas.create_line(tick_x, TICK_START_Y, tick_x, TICK_END_Y, fill=color, tags="static")

            if index % label_every == 0:
                TEXT_OFFSET_Y = center_y + 20
                TICK_FONT_SIZE = 7
                display_text = f"{tick_value:.1f}" if tick_value != int(tick_value) else str(int(tick_value))
                self.canvas.create_text(tick_x, TEXT_OFFSET_Y, text=display_text, fill=tick_color, font=("Arial", TICK_FONT_SIZE), anchor="n", tags="static")

    def _update_positions(self, *args):
        if not self.winfo_exists() or not self.canvas.winfo_exists(): return
        try: current_value = self.variable.get()
        except: return

        canvas_width, canvas_height = float(self.canvas.winfo_width()), float(self.canvas.winfo_height())
        MIN_DIM = 1
        if canvas_width <= MIN_DIM: canvas_width, canvas_height = self.width, self.height

        cap_scale = float(self.configuration.get("fader_cap_scale", 1.0))
        DEFAULT_CAP_WIDTH = 50
        CAP_MARGIN_X = 10.0
        padding_x = (int(float(self.configuration.get("cap_width", DEFAULT_CAP_WIDTH)) * cap_scale)) / 2.0 + CAP_MARGIN_X

        val_range = self.max_val - self.min_val
        norm_val = (current_value - self.min_val) / val_range if val_range else 0
        handle_x = (canvas_width - (padding_x * 2.0)) * (max(0.0, min(1.0, norm_val))**(1.0 / self.log_exponent)) + padding_x

        center_y = canvas_height / 2.0
        self.canvas.coords("fader_cap", handle_x, center_y)
        self.canvas.coords("fill_line", padding_x, center_y, handle_x, center_y)

        if getattr(self, 'is_sliding', False):
            display_text = f"{current_value:.1f}" if current_value != int(current_value) else str(int(current_value))
            VAL_LABEL_OFFSET_Y = 25.0
            self.canvas.itemconfig("floating_val", text=display_text, state="normal")
            self.canvas.coords("floating_val", handle_x, center_y - VAL_LABEL_OFFSET_Y)
        else:
            self.canvas.itemconfig("floating_val", state="hidden")
