# Debounce Handler

Prevents rapid-fire messages by enforcing a minimum cooldown period between executions.

## Parameters
- `period_ms` (int): The minimum time in milliseconds that must elapse before another message is allowed through. Defaults to `50`.

## Execute Logic
1. Retrieves `period_ms` from parameters.
2. Retrieves `last_debounce_time` from the persistent pipeline state.
3. Gets the current system time in milliseconds.
4. Calculates the elapsed time since the last successful execution.
5. If the elapsed time is less than `period_ms`, it returns `None` to drop the message.
6. If the period has elapsed, it updates the state with the current time and returns the value.
