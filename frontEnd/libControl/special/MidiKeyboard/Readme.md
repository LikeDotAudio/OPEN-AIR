# MidiKeyboard — on-screen keyboard

On-screen piano keyboard (6 octaves, 73 keys from C1) for note input.

- **Defines (global):** `MidiKeyboard`
- **Props:** `value`, `onChange`, `config` (`geometry.width/height`)
- **Loaded by:** the live app via `frontEnd/Core/Launch/index.html`.

<!-- wysiwyg:sample (auto-generated from oaGuiElements; edit here to drive the library) -->
## Sample (WYSIWYG library source)

The WYSIWYG editor builds this widget's **palette entry, live preview, and
property manipulators** from the JSON block below. The web server
(`frontEnd/Core/Launch/LauchWebserver.py` → `get_grab_bag()`) scans these
READMEs, extracts this block, and serves it at `/api/grabbag`. `_README`
documents the widget; every `_LEGEND` array becomes a dropdown of allowed values
in the property editor.

```json
{
  "midi_keyboard_Example": {
    "type": "_MidiKeyboard",
    "identity": {
      "label": "MIDI Keyboard",
      "id": "midi_kbd_01",
      "notes": "On-screen 6-octave (73-key) piano keyboard, C1 upward."
    },
    "geometry": {
      "width": 800,
      "height": 120,
      "anchor": "center"
    },
    "domain": {
      "primary": {
        "min": 36,
        "max": 108,
        "value_default": 60,
        "unit": "note",
        "step": 1
      }
    },
    "dynamics": {
      "path": "System/MIDI/Input"
    },
    "cosmetics": {
      "colors": {
        "primary": "#FFFFFF",
        "secondary": "#111111",
        "active": "#33A1FD",
        "background": "#1a1a1a"
      }
    },
    "interaction": {
      "is_read_only": false
    }
  },
  "_README": "On-screen MIDI keyboard. value = the active MIDI note number; min/max bound the visible range."
}
```
