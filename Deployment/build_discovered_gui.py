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


def on_connect(client, userdata, flags, rc, properties=None):
    # `properties` is passed by paho 2.x (CallbackAPIVersion.VERSION2) and
    # absent under 1.x — defaulted so one signature serves both.
    print(f"[discovered-gui] connected rc={rc}")
    client.subscribe("OpenAir/System/Protocols/visa/Device/#")
    client.subscribe("OpenAir/System/Protocols/midi/Device/#")
    client.subscribe("OpenAir/System/Protocols/dnssd/Device/#")


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
        if key == "type":
            key = "direction"  # 'type' is widget vocabulary in panel JSON
        collected.setdefault("midi", {}).setdefault(block, {})[key] = value
        collected["midi"][block].setdefault("port", f"{direction} {dev_n}")
    elif proto == "dnssd":
        # {service_type}/{instance}/{key} — one Discovered category for all
        # DNS-SD/mDNS services, one block per instance, grouped by type.
        if len(rest) != 3 or not value:
            return
        service_type, instance, key = rest
        block = f"{instance} ({service_type})"
        collected.setdefault("dnssd", {}).setdefault(block, {})[key] = value


def label(text):
    return {"active": {"text": {"En": str(text)}}}


RESCAN_TOPIC = "OpenAir/System/Protocols/visa/Device/Rescan"


def write_scan_panel(device_count):
    """The Discovered tab's control panel: a RESCAN actuator wired (via
    explicit topic override) to the orchestrator's rescan listener, plus a
    scan-time stamp. Written on every run — 0_Scan sorts first in the tab."""
    scan_dir = os.path.join(OUT_DIR, "0_Scan")
    os.makedirs(scan_dir, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    doc = {
        "Device_Scan": {
            "type": "OcaBin",
            "description": {"En": "Device discovery controls"},
            "behavior": {"overflow_ns": "auto"},
            "blocks": {
                "Controls": {
                    "type": "OcaBlock",
                    "label": label("Device Discovery"),
                    "fields": {
                        "rescan": {
                            "type": "_GuiActuator",
                            "topic": RESCAN_TOPIC,
                            "label": {
                                "active": {"text": {"En": "RESCANNING..."}},
                                "inactive": {"text": {"En": "RESCAN DEVICES"}},
                            },
                            "layout": {"height": 50, "width": 250},
                        },
                        "last_scan": {
                            "type": "_GuiLabel",
                            "label": label(f"Last scan: {stamp} — {device_count} device(s). Reload the page after a rescan to see updated panels."),
                        },
                    },
                }
            },
        }
    }
    with open(os.path.join(scan_dir, "Scan.json"), "w") as f:
        json.dump(doc, f, indent=2)
    print(f"[discovered-gui] wrote scan control panel ({device_count} device(s) at {stamp})")


# Column order per protocol family; remaining keys append alphabetically.
PREFERRED_COLUMNS = {
    "visa": ["model", "manufacturer", "serial", "firmware", "resource", "status", "notes", "last_seen"],
    "midi": ["port", "name", "direction"],
    "dnssd": ["instance", "service_type", "hostname", "addresses", "port", "txt", "status", "last_seen"],
}
HIDDEN_COLUMNS = {"last_online", "connected", "raw_idn", "device_type", "_row_state"}

# How recently a device must have answered to count as ONLINE.
#
# Retained MQTT topics are the state store, so a device that was unplugged weeks
# ago still has retained state and still appears in this table. Without an age
# check every row looks equally current — which is how a table ends up showing a
# 2026-07-07 reading next to a live one with no visual difference.
ONLINE_WINDOW_SECONDS = 15 * 60


def row_state(row, now=None):
    """Classify a device row as 'online' | 'offline' | 'unknown'.

    Recency is the primary signal, because every agent publishes `last_online`.
    `connected` is only published by the VISA agent (it means "*IDN? answered"),
    so its ABSENCE must not count as offline — DNS-SD rows have no such field,
    and treating missing as false marked every live service red.

    An explicit `connected = 0` does override recency: a device that was probed
    seconds ago and failed to answer is not online, however fresh the timestamp.

    'unknown' is deliberate rather than folded into 'offline': a row with no
    timestamp at all (a probe that half-answered) is a different situation from
    one we know is stale, and colouring it red would assert more than we know.
    """
    now = time.time() if now is None else now

    # Explicit negative from an agent that actually measures it.
    raw_connected = str(row.get("connected", "")).strip()
    if raw_connected in ("0", "false", "False"):
        return "offline"

    raw = row.get("last_online")
    if raw in (None, ""):
        return "unknown"
    try:
        age = now - float(raw)
    except (TypeError, ValueError):
        return "unknown"

    return "online" if 0 <= age <= ONLINE_WINDOW_SECONDS else "offline"


def rows_for(category, blocks):
    """Device dict -> OcaTable rows; unix last_online becomes readable last_seen."""
    family = "visa" if category not in ("midi", "dnssd") else category
    rows = []
    for block_name, fields in sorted(blocks.items()):
        row = dict(fields)
        if "last_online" in row:
            try:
                row["last_seen"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(float(row["last_online"]))))
            except (ValueError, OverflowError):
                row["last_seen"] = row["last_online"]
        # Consumed by OcaTable for row colouring; hidden from the columns.
        row["_row_state"] = row_state(row)
        rows.append(row)
    keys = set().union(*[r.keys() for r in rows]) if rows else set()
    preferred = [k for k in PREFERRED_COLUMNS.get(family, []) if k in keys]
    rest = sorted(keys - set(preferred) - HIDDEN_COLUMNS)
    return preferred + rest, rows


def write_panels():
    # Prune category folders whose devices vanished (or re-categorized —
    # e.g. after a knowledge-base fix); 0_Scan is the permanent control panel.
    if os.path.isdir(OUT_DIR):
        for entry in os.listdir(OUT_DIR):
            if entry != "0_Scan" and entry not in collected:
                stale = os.path.join(OUT_DIR, entry)
                if os.path.isdir(stale):
                    import shutil
                    shutil.rmtree(stale)
                    print(f"[discovered-gui] pruned stale category {entry}/")
    written = 0
    for category, blocks in sorted(collected.items()):
        cat_dir = os.path.join(OUT_DIR, category)
        os.makedirs(cat_dir, exist_ok=True)
        headers, rows = rows_for(category, blocks)
        # The library OcaTable (libControl/text/OcaTable) — the component
        # built for exactly this ("Discovered Devices" in Sample.json):
        # sticky header, zebra rows, row-count footer, own scroll region.
        doc = {
            category: {
                "type": "OcaBin",
                "description": {"En": f"Discovered {category} devices (scan snapshot)"},
                "behavior": {"overflow_ns": "auto"},
                "blocks": {
                    "Devices": {
                        "type": "OcaTable",
                        "description": {"En": f"Discovered {category} devices"},
                        "headers": headers,
                        "data": rows,
                        "Sort": True,
                    }
                },
            }
        }
        out = os.path.join(cat_dir, f"{category}.json")
        with open(out, "w") as f:
            json.dump(doc, f, indent=2)
        written += 1
        print(f"[discovered-gui] wrote {out} ({len(rows)} device(s), {len(headers)} columns)")
    return written


def make_client():
    """paho-mqtt 2.x requires an explicit callback API version (and warns on
    VERSION1); 1.x has no such argument at all. requirements.txt allows
    either, so build whichever this environment supports — `on_connect`
    below takes the extra v2 `properties` argument optionally, which makes
    one callback signature valid under both APIs."""
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # paho >= 2.0
    except AttributeError:
        return mqtt.Client()  # paho 1.x


def main():
    client = make_client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("127.0.0.1", 1883, 60)
    client.loop_start()
    time.sleep(COLLECT_SECONDS)  # retained messages arrive immediately on subscribe
    client.loop_stop()
    n = write_panels()
    devices = sum(len(blocks) for blocks in collected.values())
    write_scan_panel(devices)
    if n == 0:
        print("[discovered-gui] no retained discovery topics found — only the scan panel written")


if __name__ == "__main__":
    main()
