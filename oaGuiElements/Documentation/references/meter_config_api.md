# 📚 Meter Config API Reference

## 🛠️ Classes

### `class MeterConfig`
Handles the parsing and retrieval of configuration data for meter widgets.

#### `__init__(self, config_data)`
Initializes the configuration object with raw data (typically a dictionary).

**Parameters:**
- `config_data`: Dictionary containing meter properties (colors, sizes, ranges).

#### 🎨 Visual Properties
- `label(self)`: Returns the primary text label for the meter.
- `show_label(self)`: Boolean flag to toggle label visibility.
- `font_size(self)`: Returns the font size for labels and scales.
- `custom_colour(self)`: Returns the primary accent color.
- `widget_label_color(self)`: Returns the color for the widget's label.
- `intended_bg(self)`: Returns the desired background color.
- `is_transparent(self)`: Boolean flag for background transparency.
- `faceplate_color(self)`: Returns the color of the card inside the bezel.
- `canvas_bg(self)`: Returns the base canvas background color.
- `fg_color(self)`: Returns the foreground/stroke color.
- `scale_label_color(self)`: Returns the color for scale numbers.
- `bezel_shape(self)`: Returns the shape definition for the meter bezel.
- `pointer_colour(self)`: Returns the primary needle color.
- `pointer_colour_2(self)`: Returns the secondary needle color.
- `pivot_colour(self)`: Returns the color of the needle pivot point.

#### 📐 Geometry & Scale
- `size(self)`: Returns a tuple of (width, height).
- `width(self)`: Returns the widget width.
- `height(self)`: Returns the widget height.
- `scale_padding(self)`: Returns the padding between the scale and bezel.
- `needle_scale(self)`: Returns the scaling factor for the needle length.
- `needle_thickness(self)`: Returns the thickness of the primary needle.
- `needle_thickness_2(self)`: Returns the thickness of the secondary needle.
- `min_val(self)`: Returns the minimum scale value.
- `max_val(self)`: Returns the maximum scale value.
- `red_zone_start(self)`: Returns the value where the 'red zone' begins.
- `mid_range_start(self)`: Returns the value where the 'middle range' begins.
- `anchor_point(self)`: Returns the zero-anchor point for the needle.
- `resting_point(self)`: Returns the needle's resting position.
- `meter_viewable_angle(self)`: Returns the total arc angle in degrees.
- `meter_center_angle(self)`: Returns the center offset angle in degrees.
- `pivot_size(self)`: Returns the diameter of the needle pivot.
- `pivot_crop(self)`: Boolean flag to crop the pivot area.
- `mask(self)`: Returns the path to an image mask for the meter.

#### 📈 Ballistics & Timing
- `meter_mode(self)`: Returns the ballistic mode (e.g., VU, PPM, RMS).
- `glide_time(self)`: Returns the time for the needle to reach a new value.
- `dwell_time(self)`: Returns the time the needle stays at a peak.
- `hold_time(self)`: Returns the duration of the peak hold.
- `fall_time(self)`: Returns the decay time for the needle.
- `peak_hold_ms(self)`: Returns the peak hold duration in milliseconds.
- `peak_flag(self)`: Boolean flag to enable/disable peak indicators.

#### 📏 Ticks & Labels
- `tick_step(self)`: Returns the interval between major ticks.
- `sub_ticks(self)`: Returns the number of sub-ticks between major ticks.
- `sub_tick_style(self)`: Returns the visual style for sub-ticks.
- `scale_numbers(self)`: Returns a list of numbers to display on the scale.
- `ticks_visible(self)`: Boolean flag to toggle all ticks.
- `custom_ticks(self)`: Returns a list of custom tick positions.
- `label_overrides(self)`: Returns a map of value-to-string label overrides.

#### 🛠️ Offsets & Overrides
- `pivot_offset_x(self)`, `pivot_offset_y(self)`: Offsets for the primary pivot.
- `pivot_offset_x_2(self)`, `pivot_offset_y_2(self)`: Offsets for the secondary pivot.
- `tick_length_override(self)`: Custom length for major ticks.
- `sub_tick_length_override(self)`: Custom length for sub-ticks.
- `arc_radius_offset(self)`: Radius offset for the scale arc.
- `tick_radius_offset(self)`: Radius offset for ticks.
- `label_radius_offset(self)`: Radius offset for scale labels.
- `needle_length_factor_override(self)`: Manual override for needle length.
