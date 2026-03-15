# ScaleHandler.execute

The **ScaleHandler** is a linear scaling logic block used to map values from a source range to a destination range.

## Purpose
The primary purpose is to convert values between different hardware and software protocols. For example:
- Mapping a **MIDI** 0-127 value to a **GUI** 0-100% fader.
- Mapping a **Knob** 0-1.0 value to a **Frequency** 20Hz-20000Hz.

## Parameters
- `source_min`: The minimum value expected from the source.
- `source_max`: The maximum value expected from the source.
- `dest_min`: The minimum value to output to the destination.
- `dest_max`: The maximum value to output to the destination.

## Functionality
The `execute` method performs the following:
1.  Clamps the incoming value to the source range.
2.  Performs a linear interpolation calculation.
3.  Returns an integer if both destination parameters are integers, otherwise returns a float.
4.  If the incoming value is not a number, it passes through unchanged.
