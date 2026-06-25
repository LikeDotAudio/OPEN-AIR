#!/usr/bin/env python3
"""Real MIDI tester: list ports, listen for input, or send a test note.
    python3 Validations/Protocols/midi/midi_tester.py ports
    python3 Validations/Protocols/midi/midi_tester.py listen [--port NAME] [--timeout S]
    python3 Validations/Protocols/midi/midi_tester.py send [--port NAME]
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import argparse, time
from _proto_util import config  # noqa: E402
import mido  # noqa: E402

def pick(names, want):
    if want and want != "auto":
        for n in names:
            if want in n: return n
    return names[0] if names else None

if __name__ == "__main__":
    cfg, _ = config("midi")
    ap = argparse.ArgumentParser(prog="midi_tester")
    ap.add_argument("action", nargs="?", default="listen", choices=["ports", "listen", "send"])
    ap.add_argument("--port", default=cfg.get("input_port", "auto"))
    ap.add_argument("--timeout", type=float, default=15.0)
    a = ap.parse_args()
    ins, outs = mido.get_input_names(), mido.get_output_names()
    if a.action == "ports":
        print("Inputs:"); [print(f"  • {n}") for n in ins] or print("  (none)")
        print("Outputs:"); [print(f"  • {n}") for n in outs] or print("  (none)")
        sys.exit(0)
    if a.action == "send":
        name = pick(outs, a.port)
        if not name: print("❌ no MIDI output port."); sys.exit(1)
        with mido.open_output(name) as out:
            out.send(mido.Message("note_on", note=60, velocity=100))
            time.sleep(0.3)
            out.send(mido.Message("note_off", note=60, velocity=0))
        print(f"  ⮞ sent note C4 to '{name}'"); sys.exit(0)
    name = pick(ins, a.port)
    if not name: print("❌ no MIDI input port (try )."); sys.exit(1)
    print(f"👂 [MIDI] listening on '{name}' for {a.timeout}s…")
    n = 0; end = time.time() + a.timeout
    with mido.open_input(name) as inp:
        while time.time() < end:
            for msg in inp.iter_pending():
                n += 1; print(f"  ⮜ {msg}")
            time.sleep(0.01)
    print(f"✅ [MIDI] received {n} message(s)."); sys.exit(0 if n else 2)
