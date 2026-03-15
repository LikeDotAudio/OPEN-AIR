# Scale Handler

Linearly scales a numerical value from a defined source range to a target destination range.

## Parameters
- `source_min` (float): The minimum value of the source range. Defaults to `0`.
- `source_max` (float): The maximum value of the source range. Defaults to `100`.
- `dest_min` (float): The minimum value of the destination range. Defaults to `0`.
- `dest_max` (float): The maximum value of the destination range. Defaults to `255`.

## Execute Logic
1. Retrieves range parameters for both source and destination.
2. Clamps the incoming value within the `source_min` and `source_max` bounds.
3. Calculates the scale factor: `(dest_max - dest_min) / (source_max - source_min)`.
4. Applies the linear transformation: `dest_min + (clamped_value - source_min) * scale`.
5. Returns the scaled value. If both destination bounds are integers, the result is rounded and returned as an integer.
6. If the input is non-numeric, it is passed through unchanged.
