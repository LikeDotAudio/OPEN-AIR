# Invert Handler

Inverts a numerical value within a specified range, or toggles a boolean value.

## Parameters
- `min_value` (float): The lower bound of the numerical range. Defaults to `0`.
- `max_value` (float): The upper bound of the numerical range. Defaults to `1`.

## Execute Logic
1. **Boolean Inversion**: If the value is a boolean, it returns the logical NOT of the value.
2. **Numerical Inversion**:
   - Retrieves `min_value` and `max_value` from parameters.
   - Calculates the inverted value using the formula: `(max_value + min_value) - current_value`.
   - Returns the result, attempting to preserve the original integer type if applicable.
3. **String Boolean Inversion**: If the value is a string matching "true"/"on"/"1" or "false"/"off"/"0", it returns the opposite string value.
4. If the value does not match these types, it is passed through unchanged.
