"""Discovered-device GUI builder — Phase 0 item 3 (transitional).

Collects the retained VISA/MIDI discovery topics off the broker and writes
one authored-shape panel per device category into Gui_Frames/0_discovered/,
so discovered devices show up in the Discovered tab TODAY.

Patched only enough to be useful meanwhile (this whole pipeline is replaced
by the Phase 4 Device Registry + live Discovered widget):
- subscribes to the topics the agents actually publish
  (OpenAir/System/Protocols/{visa,midi}/Device/#  — not the old bare
  visa/Device/#, which never received a single message)
- emits STRICT-VALID v41 layout JSON (OcaBin/OcaBlock/_GuiLabel with nested
  label pillars) instead of the dead _GuiValue+subscribe schema
- field values are baked as static text at scan time (the browser only
  subscribes to OpenAir/Gui/#, so live readouts of protocol topics are
  impossible until Phase 4 moves discovery onto OpenAir/Discovery)
- output dir is generated data: gitignored, excluded from openair-validate

Spawned by the orchestrator after the VISA scan completes; also runnable by
hand: python3 Deployment/build_discovered_gui.py
"""
import json
import os
import time

import paho.mqtt.client as mqtt

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO_ROOT, "FrontEnd", "Gui_Frames", "0_discovered")
COLLECT_SECONDS = 5

# {category: {block_name: {field_key: value}}}
collected = {}


def on_connect(client, userdata, flags, rc):
    print(f"[discovered-gui] connected rc={rc}")
    client.subscribe("OpenAir/System/Protocols/visa/Device/#")
    client.subscribe("OpenAir/System/Protocols/midi/Device/#")


def on_message(client, userdata, msg):
    parts = msg.topic.split("/")
    # OpenAir/System/Protocols/{proto}/Device/...
    if len(parts) < 6 or parts[4] != "Device":
        return
    proto = parts[3]
    rest = parts[5:]
    value = msg.payload.decode(errors="replace").strip()

    if proto == "visa":
        # {type}/{model}/Dev{n}/{key}
        if len(rest) != 4 or rest[3] in ("Write", "Read") or not value:
            return
        dev_type, model, dev_n, key = rest
        block = f"{model} ({dev_n})"
        collected.setdefault(dev_type, {}).setdefault(block, {})[key] = value
    elif proto == "midi":
        # {Input|Output}/Dev{n}/{key}
        if len(rest) != 3 or not value:
            return
        direction, dev_n, key = rest
        block = f"{direction} {dev_n}"
        collected.setdefault("midi", {}).setdefault(block, {})[key] = value


def label(text):
    return {"active": {"text": {"En": str(text)}}}


def write_panels():
    written = 0
    for category, blocks in sorted(collected.items()):
        cat_dir = os.path.join(OUT_DIR, category)
        os.makedirs(cat_dir, exist_ok=True)
        panel_blocks = {}
        for block_name, fields in sorted(blocks.items()):
            panel_blocks[block_name.replace(" ", "_")] = {
                "type": "OcaBlock",
                "label": label(block_name),
                "fields": {
                    key: {"type": "_GuiLabel", "label": label(f"{key}: {value}")}
                    for key, value in sorted(fields.items())
                },
            }
        doc = {
            category: {
                "type": "OcaBin",
                "description": {"En": f"Discovered {category} devices (scan snapshot)"},
                "blocks": panel_blocks,
            }
        }
        out = os.path.join(cat_dir, f"{category}.json")
        with open(out, "w") as f:
            json.dump(doc, f, indent=2)
        written += 1
        print(f"[discovered-gui] wrote {out} ({len(blocks)} device(s))")
    return written


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("127.0.0.1", 1883, 60)
    client.loop_start()
    time.sleep(COLLECT_SECONDS)  # retained messages arrive immediately on subscribe
    client.loop_stop()
    n = write_panels()
    if n == 0:
        print("[discovered-gui] no retained discovery topics found — nothing written")


if __name__ == "__main__":
    main()
