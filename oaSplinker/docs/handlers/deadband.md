# Deadband Handler

Drops messages if the value change is within a certain threshold. This is a stateful handler that remembers the last value that was passed through the pipeline.

## Parameters
- `threshold_percent` (float): The percentage of change required to allow the message through. Defaults to `1`.
- `max_value` (float): The maximum expected value used to calculate the percentage change. Defaults to `100`.

## Execute Logic
1. Retrieves `threshold_percent` and `max_value` from parameters.
2. Retrieves `last_deadband_value` from the persistent pipeline state.
3. If no previous value exists, it stores the current value and allows it through.
4. Calculates the percentage change between the current value and the last passed value.
5. If the change is less than `threshold_percent`, it returns `None` to drop the message.
6. If the change meets or exceeds the threshold, it updates the state with the current value and returns it.
7. If values are non-numeric, it drops the message only if the value is identical to the last one.
