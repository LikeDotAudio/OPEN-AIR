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
hand: python3 BackEnd/Core/orchestrator/gui/build_discovered_gui.py
"""
import fcntl
import json
import os
import sys
import tempfile
import time

import paho.mqtt.client as mqtt

# BackEnd/Core/orchestrator/gui/ -> repo root is four levels up.
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")
)
OUT_DIR = os.path.join(REPO_ROOT, "FrontEnd", "Gui_Frames", "0_discovered")

# Where live table rows are published, one retained topic per category.
#
# The panel file carries a snapshot; this carries the truth. Columns still come
# from the file, so a NEW column needs a rebuild — but rows appearing,
# vanishing or changing state flow straight through.
LIVE_TABLE_PREFIX = "OpenAir/System/Gui/Discovered"
COLLECT_SECONDS = 5

# Narration for the browser's Discovery Activity feed.
#
# The VISA scan already narrates itself (visa/Scan/Log), but VISA is one agent
# out of a dozen: everything DNS-SD, Cast, Dante, PTP, RAVENNA, SAP and the
# printers find only ever appeared in the orchestrator's stdout. Whoever is
# actually using the UI cannot see stdout, so the page looked frozen while the
# terminal scrolled. This topic carries the same story onto the bus.
#
# Non-retained: it is an event stream. A page loaded an hour from now must not
# be shown a device appearing as though it were happening right then — the
# device records themselves are retained, the narration about them is not.
ACTIVITY_TOPIC = "OpenAir/System/Discovery/Activity"

# Above this many changes in one pass, narrate the count instead of every row.
# The first pass after a restart sees ~100 devices "appear" at once; a hundred
# lines of that buries the two changes that actually mattered.
ACTIVITY_DETAIL_LIMIT = 8

# {category: {block_name: {field_key: value}}}
collected = {}

# Retained `<category>/config` topics found under our own output prefix, left by
# an older OcaTable that published its node definition alongside the rows.
stale_gui_config = set()


def on_connect(client, userdata, flags, rc, properties=None):
    # `properties` is passed by paho 2.x (CallbackAPIVersion.VERSION2) and
    # absent under 1.x — defaulted so one signature serves both.
    print(f"[discovered-gui] connected rc={rc}")
    client.subscribe("OpenAir/System/Protocols/visa/Device/#")
    client.subscribe("OpenAir/System/Protocols/midi/Device/#")
    client.subscribe("OpenAir/System/Protocols/dnssd/Device/#")
    client.subscribe("OpenAir/System/Protocols/chromecast/Device/#")
    client.subscribe("OpenAir/System/Protocols/ravenna/Device/#")
    client.subscribe("OpenAir/System/Protocols/dante/#")
    client.subscribe("OpenAir/System/Protocols/printers/Device/#")
    client.subscribe("OpenAir/System/Protocols/appletv/Device/#")
    client.subscribe("OpenAir/System/Protocols/nmos/Device/#")
    client.subscribe("OpenAir/System/Protocols/sap/Device/#")
    client.subscribe("OpenAir/System/Protocols/avb/Device/#")
    client.subscribe("OpenAir/System/Protocols/ptp/Device/#")
    client.subscribe(SCAN_STATE_TOPIC)
    # Own output tree — read back only to find the retained `<category>/config`
    # topics an older OcaTable left behind (see stale_gui_config below).
    client.subscribe(f"{LIVE_TABLE_PREFIX}/#")


def on_message(client, userdata, msg):
    if msg.topic == SCAN_STATE_TOPIC:
        scan_state["value"] = msg.payload.decode(errors="replace").strip()
        return
    if msg.topic.startswith(f"{LIVE_TABLE_PREFIX}/"):
        # Rows we published ourselves; nothing to collect. The exception is the
        # `<category>/config` siblings: the table widget used to publish its own
        # node definition there (retained), which is dead weight on the broker
        # and, worse, sat one keystroke away from overwriting the row topic.
        if msg.topic.endswith("/config") and msg.payload:
            stale_gui_config.add(msg.topic)
        return
    parts = msg.topic.split("/")
    # OpenAir/System/Protocols/{proto}/Device/...
    if len(parts) < 6 or parts[4] not in ("Device", "Stream"):
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
        entry = collected.setdefault(dev_type, {}).setdefault(block, {})
        entry[key] = value
        # The device's own topic prefix, kept because the Write topic cannot be
        # rebuilt from the row fields (Dev index appears nowhere in them) and
        # per-device instrument panels are bound to exactly that topic.
        # Hidden from the table columns like the other underscore keys.
        entry["_topic_prefix"] = "/".join(parts[:4] + ["Device", dev_type, model, dev_n])
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
    elif proto == "chromecast":
        # {category}/{friendly_name}/{key} — the Cast agent has already decoded
        # the TXT record and chosen a category, so this is a straight passthrough.
        # One Discovered tab per category (Speaker, Video Cast, Smart Display …),
        # which is the point: 40 raw mDNS rows become a handful of meaningful ones.
        if len(rest) != 3 or not value:
            return
        category, friendly, key = rest
        block = friendly.replace("_", " ")
        collected.setdefault(f"cast_{category}", {}).setdefault(block, {})[key] = value
    elif proto in ("appletv", "nmos"):
        # Both already merged to one entry per thing by their agent
        # (Apple TV by hostname; NMOS by host+port), so straight passthrough.
        if len(rest) != 2 or not value:
            return
        name, key = rest
        collected.setdefault(proto, {}).setdefault(name.replace("_", " "), {})[key] = value
    elif proto == "printers":
        # Already merged to one entry per physical printer by the agent (keyed on
        # the Bonjour UUID), so this is a straight passthrough.
        if len(rest) != 2 or not value:
            return
        name, key = rest
        collected.setdefault("printers", {}).setdefault(name.replace("_", " "), {})[key] = value
    elif proto == "dante":
        # Two shapes under one protocol, matching Dante's split personality:
        #   Device/{name}/{key}          — native, found over mDNS
        #   Stream/{origin}/{name}/{key} — AES67, found over SAP
        # They get separate tabs because they answer different questions:
        # "what hardware is here" vs "what audio is being announced".
        # Native Dante only. AES67-over-SAP streams belong to openair-sap and
        # land in the `sap` tab — SAP is vendor-neutral, so filing it under
        # "Dante" would mislabel RAVENNA and translator traffic too.
        if parts[4] == "Device" and len(rest) == 2 and value:
            name, key = rest
            collected.setdefault("dante", {}).setdefault(name.replace("_", " "), {})[key] = value
        elif parts[4] == "Device" and len(rest) == 4 and rest[1] == "Channel" and value:
            # Device/{device}/Channel/{ch}/{key} — channels live under their
            # device, so a 16-channel interface is one device row plus 16
            # channel rows, not 16 devices.
            dev, _, ch, key = rest
            collected.setdefault("dante_channels", {}).setdefault(f"{ch} @ {dev}", {})[key] = value
    elif proto == "ravenna":
        # {host}/{stream}/{key} — one tab for all RAVENNA audio, one row per
        # stream, labelled with its host. A single node commonly publishes
        # several streams, so host is context rather than a separate tab.
        if len(rest) != 3 or not value:
            return
        host, stream_name, key = rest
        block = f"{stream_name.replace('_',' ')} @ {host}"
        collected.setdefault("ravenna", {}).setdefault(block, {})[key] = value
        collected["ravenna"][block].setdefault("host", host)
    elif proto == "sap":
        # {origin_ip}/{session}/{key} — SAP is the announcement mechanism Dante
        # uses in AES67 mode, so this is the same kind of audio stream RAVENNA
        # publishes, discovered by the opposite means (passive multicast push
        # rather than mDNS query). Kept as its own tab rather than merged into
        # RAVENNA's: a stream appearing in both is the useful signal, not noise.
        if len(rest) != 3 or not value:
            return
        origin, session_name, key = rest
        block = f"{session_name.replace('_',' ')} @ {origin}"
        collected.setdefault("sap", {}).setdefault(block, {})[key] = value
        collected["sap"][block].setdefault("source", origin)
    elif proto == "avb":
        # {entity_id}/{key} — AVDECC entities. Keyed by entity ID because ADP
        # carries no human-readable name at all; the name lives in the AEM
        # descriptor tree, which discovery does not fetch. One tab for AVB.
        if len(rest) != 2 or not value:
            return
        entity_id, key = rest
        collected.setdefault("avb", {}).setdefault(entity_id, {})[key] = value
    elif proto == "ptp":
        # {clock_id}-{port}-d{domain}/{key} — one row per PTP *port*, not per
        # device. A box can run several ports, several domains, and more than
        # one PTP flavour at once (v1, v2 and gPTP on one NIC is the case this
        # was built for), and each of those is an independent clock that can
        # disagree with the others. Merging them by device would hide exactly
        # the disagreement worth seeing.
        if len(rest) != 2 or not value:
            return
        segment, key = rest
        # Segment is "{id}-{port}-d{domain}"; the id itself is colon-separated,
        # so split from the right and keep whatever does not match as-is.
        parts_seg = segment.rsplit("-", 2)
        if len(parts_seg) == 3 and parts_seg[2].startswith("d"):
            clock, port_no, dom = parts_seg[0], parts_seg[1], parts_seg[2][1:]
            block = f"{clock} port {port_no} (domain {dom})"
        else:
            block = segment
        collected.setdefault("ptp", {}).setdefault(block, {})[key] = value
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


scan_state = {"value": "idle"}

RESCAN_TOPIC = "OpenAir/System/Protocols/visa/Device/Rescan"
CLEAR_TOPIC = "OpenAir/System/Protocols/visa/Device/Clear"
SCAN_STATE_TOPIC = "OpenAir/System/Protocols/visa/Scan/State"


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
                        "clear": {
                            "type": "_GuiActuator",
                            "topic": CLEAR_TOPIC,
                            "label": {
                                "active": {"text": {"En": "CLEARING..."}},
                                "inactive": {"text": {"En": "CLEAR ALL DEVICES"}},
                            },
                            "layout": {"height": 50, "width": 250},
                        },
                        "last_scan": {
                            "type": "_GuiLabel",
                            "label": label(
                                (f"⏳ SCAN IN PROGRESS — rows below are last scan's results and are shown amber until it finishes."
                                 if scan_state["value"] == "scanning" else
                                 f"Last scan: {stamp} — {device_count} device(s).")
                                + " Rows update live; reload only to pick up new tabs or columns."
                            ),
                        },
                        # The live feed. Everything the agents narrate on the bus
                        # — VISA's own scan log plus the watcher's device diffs —
                        # lands here, which is the whole point: a scan used to be
                        # visible only in the orchestrator's stdout, so pressing
                        # RESCAN from the browser looked like it did nothing.
                        "activity": {
                            "type": "_GuiScanActivity",
                            "description": {"En": "Discovery Activity"},
                            "layout": {"height": 340, "width": "100%"},
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
    # Cast devices: identity first, then what it can do, then where it lives.
    # RAVENNA: what the stream IS, then where it goes, then how it is clocked.
    "ravenna": ["stream", "host", "format", "sample_rate", "channels",
                "destination", "rtp_port", "ptime_ms", "clock_domain",
                "direction", "refclk", "status", "last_seen"],
    # SAP mirrors RAVENNA's column order — same stream facts, different
    # announcement path — with the SAP-specific origin and msg id at the end.
    "sap": ["stream", "source", "format", "sample_rate", "channels",
            "destination", "rtp_port", "ptime_ms", "clock_domain",
            "direction", "refclk", "announced_via", "msg_id", "status", "last_seen"],
    # Printers: identity, then capabilities (the questions people ask), then
    # how to reach it. Raw TXT is deliberately not a column — it is decoded.
    "appletv": ["device", "model", "model_id", "os_version", "airplay_version",
                "roles", "audio_codecs", "metadata", "features_raw", "addresses",
                "status", "last_seen"],
    "nmos": ["service", "role", "api_versions", "api_proto", "api_auth",
             "priority", "host", "port", "addresses", "last_seen"],
    "printers": ["printer", "manufacturer", "model", "color", "duplex", "scan",
                 "fax", "paper_max", "transports", "languages", "addresses",
                 "admin_url", "uuid", "status", "last_seen"],
    "dante_channels": ["channel", "device", "id", "sample_rate", "bit_depth",
                       "latency_ms", "frames_per_packet", "flow_channels",
                       "redundancy", "last_seen"],
    "dante": ["device", "manufacturer", "model", "discovery", "services",
              "addresses", "port", "hostname", "status", "last_seen"],
    "dante_aes67": ["stream", "discovery", "format", "sample_rate", "channels",
                    "destination", "rtp_port", "origin", "status", "last_seen"],
    # AVB: identity, then what it can carry, then the clock it follows —
    # grandmaster mismatch is the usual reason a discovered entity won't pass audio.
    "avb": ["entity_id", "mac", "oui", "interface", "talker_sources",
            "listener_sinks", "talker_capabilities", "listener_capabilities",
            "gptp_grandmaster", "gptp_domain", "milan", "entity_model_id",
            "configuration_index", "valid_time_s", "status", "last_seen"],
    # PTP: what kind of clock it is and who it follows, before the tuning
    # details. grandmaster + gm_class answer "is time healthy?", which is the
    # question a PTP tab exists for.
    # `messages` sits high on purpose: a port that only sends Pdelay_Req has no
    # Announce data, so every quality column is blank. The message mix is what
    # tells you that row is a peer-delay-only port rather than a parse failure.
    "ptp": ["clock_id", "port", "variant", "subdomain", "domain", "role",
            "messages", "grandmaster", "gm_class", "gm_class_meaning",
            "gm_accuracy", "time_source", "steps_removed", "priority1",
            "priority2", "sync_interval_s", "two_step", "status", "last_seen"],
    "chromecast": ["friendly_name", "model", "device_type", "capabilities",
                   "status_text", "addresses", "port", "hostname",
                   "protocol_version", "cast_id", "status", "last_seen"],
}
HIDDEN_COLUMNS = {"last_online", "connected", "raw_idn", "device_type", "_row_state",
                  "_topic_prefix", "reachable"}

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

    # The VISA heartbeat's verdict (orchestrator spawn_visa_heartbeat): the
    # instrument's transport stopped answering repeated probes. Distinct from
    # `connected`, which records whether *IDN? ever answered — an instrument can
    # be identified and later unplugged, and only this notices within 30s
    # instead of waiting out ONLINE_WINDOW_SECONDS.
    if str(row.get("reachable", "")).strip() in ("0", "false", "False"):
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
    if category.startswith("cast_"):
        family = "chromecast"
    elif category in ("midi", "dnssd", "ravenna", "sap", "avb", "ptp"):
        family = category
    else:
        family = "visa"
    rows = []
    for block_name, fields in sorted(blocks.items()):
        row = dict(fields)
        if "last_online" in row:
            try:
                row["last_seen"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(float(row["last_online"]))))
            except (ValueError, OverflowError):
                row["last_seen"] = row["last_online"]
        # Consumed by OcaTable for row colouring; hidden from the columns.
        # While a scan is running every row is provisional — the instrument may
        # be gone and we simply have not re-probed it yet. Showing last scan's
        # green during a live scan asserts something we do not currently know.
        row["_row_state"] = "unknown" if scan_state["value"] == "scanning" else row_state(row)
        rows.append(row)
    keys = set().union(*[r.keys() for r in rows]) if rows else set()
    preferred = [k for k in PREFERRED_COLUMNS.get(family, []) if k in keys]
    rest = sorted(keys - set(preferred) - HIDDEN_COLUMNS)
    return preferred + rest, rows


# ── Tab grouping ─────────────────────────────────────────────────────────────
#
# Folders make tabs, so nesting a category inside a group folder nests its tab.
# Without this every discovery lands in one flat row of ~18 tabs, which stops
# being navigable about half way along.
#
# The `N_` prefix orders the groups; the numbers are deliberately sparse so a
# new group can be slotted between two existing ones without renumbering (and
# renumbering is not free — the validator treats sibling prefix collisions as an
# error, and folder names are identity here).
GROUPS = {
    "1_Lab_Instruments": None,   # default for VISA/GPIB categories — see below
    # NMOS is here rather than in "Other" because it is media-over-IP
    # infrastructure, not a peripheral: an IS-04 registry is what AES67 senders
    # and receivers register WITH. It also carries video, so if this group is
    # ever renamed, rename it to something like "Media_Over_IP".
    "4_Audio_Over_IP": {"ravenna", "sap", "midi", "dante", "dante_channels",
                        "avb", "nmos"},
    "10_Google and Apple": {"appletv"},   # plus every cast_* category
    "12_Other": {"printers", "dnssd"},
}


# Categories promoted OUT of the group folders to sit as their own top-level
# tab, in the same shape as 0_Scan: `0_discovered/<folder>/<Name>.json` with no
# intermediate category directory.
#
# PTP earns this because it is not one more discovered device family — it is the
# clock every AES67 and AVB stream is disciplined to. When audio drops out, this
# is the first tab you open, and burying it one level inside Audio_Over_IP puts
# it at the same depth as the things it explains.
#
# The folder prefix orders it among the groups; 5 sits it directly after
# 4_Audio_Over_IP, which is where you look next.
TOP_LEVEL_TABS = {
    "ptp": ("5_PTP", "PTP"),
}


def group_for(category):
    """Which group folder a category's tab belongs in.

    Lab instruments are the DEFAULT rather than an explicit list, because VISA
    categories come from the instrument knowledge base at scan time — DMM,
    Oscilloscope, Generator, Spectrum, Load, LCR, Power… Listing them here would
    mean a newly-recognised instrument type silently landing in the wrong group
    (or worse, at the top level) until someone remembered to update this map.
    Everything discovered over the network is named explicitly; whatever is left
    came off the bench.
    """
    if category.startswith("cast_"):
        return "10_Google and Apple"
    for group, members in GROUPS.items():
        if members and category in members:
            return group
    return "1_Lab_Instruments"


def publish_live_tables(client) -> int:
    """Publish each category's rows to its live topic. Returns categories sent."""
    sent = 0
    for category, blocks in sorted(collected.items()):
        _headers, rows = rows_for(category, blocks)
        client.publish(
            f"{LIVE_TABLE_PREFIX}/{category}",
            json.dumps(rows),
            qos=1,
            retain=True,
        )
        sent += 1
    return sent


# One watcher per machine, enforced with a lock file.
#
# The orchestrator calls spawn_discovered_watcher() after EVERY scan, so without
# this each rescan left another watcher running: N copies republishing identical
# rows and narrating every change N times. The symptom in the browser is a feed
# that says everything twice, which reads as a bug in the diff rather than a
# process leak. flock is released automatically when the process dies, however it
# dies, so a crashed watcher never blocks its replacement.
WATCHER_LOCK_PATH = os.path.join(tempfile.gettempdir(), "openair-discovered-watcher.lock")
_watcher_lock = None  # module-level: the handle must outlive acquire_watcher_lock()


def acquire_watcher_lock():
    """True if this process may watch; False if another watcher already is."""
    global _watcher_lock
    handle = open(WATCHER_LOCK_PATH, "w")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return False
    handle.write(f"{os.getpid()}\n")
    handle.flush()
    _watcher_lock = handle
    return True


def publish_activity(client, level, message, source="discovery"):
    """Put one narration line on the bus for the browser's activity feed.

    QoS 0, non-retained — same reasoning as the orchestrator's scan_log: losing
    a line of commentary under load is preferable to slowing discovery for it.
    """
    payload = json.dumps({
        "level": level,          # "info" | "ok" | "warn" | "error"
        "message": message,
        "source": source,        # which agent family the line is about
        "ts": time.time(),
    })
    client.publish(ACTIVITY_TOPIC, payload, qos=0, retain=False)


def device_states():
    """{(category, block): row_state} for everything currently collected."""
    return {
        (category, name): row_state(fields)
        for category, blocks in collected.items()
        for name, fields in blocks.items()
    }


def narrate_changes(client, before, after):
    """Announce what changed between two device snapshots.

    Only appearances, disappearances and online/offline transitions are
    narrated. Field churn is deliberately silent: `last_online` moves on almost
    every pass, and a feed that says "something changed" twice a second says
    nothing at all.
    """
    added = [k for k in after if k not in before]
    removed = [k for k in before if k not in after]
    flipped = [k for k in after if k in before and before[k] != after[k]]

    def summarize(keys, verb, level):
        # Per-category counts read better than 53 individual lines the first
        # time a watcher sees a populated bus.
        counts = {}
        for category, _name in keys:
            counts[category] = counts.get(category, 0) + 1
        for category, n in sorted(counts.items()):
            publish_activity(client, level, f"{n} device(s) {verb}", source=category)

    for keys, verb, level in ((added, "appeared", "ok"), (removed, "vanished", "warn")):
        if not keys:
            continue
        if len(keys) > ACTIVITY_DETAIL_LIMIT:
            summarize(keys, verb, level)
        else:
            for category, name in sorted(keys):
                publish_activity(client, level, f"{name} {verb}", source=category)

    # Liveness flips summarize by DESTINATION STATE, not as one lump. They arrive
    # in waves: every device an agent last touched at the same moment crosses the
    # staleness window together, so an agent restart turns the whole table amber
    # in one pass. One line per device is then ~80 lines that say one thing.
    by_state = {}
    for key in flipped:
        by_state.setdefault(after[key], []).append(key)
    for state, keys in sorted(by_state.items()):
        level = {"online": "ok", "offline": "warn"}.get(state, "info")
        if len(keys) > ACTIVITY_DETAIL_LIMIT:
            summarize(keys, f"went {state}", level)
        else:
            for category, name in sorted(keys):
                publish_activity(client, level, f"{name} is now {state}", source=category)


def watch(client, interval: float = 2.0) -> None:
    """Stay connected and republish rows whenever the retained tree changes.

    Publish-only on purpose. The one-shot builder owns the panel FILES; two
    processes writing the same tree would race, and only a new category (or a
    new column) actually requires a file rewrite. Rows change constantly and
    are exactly what this keeps live.

    Republishing only on change keeps an idle bench quiet: PTP alone would
    otherwise put a full table on the bus every couple of seconds forever.

    Every pass also narrates itself to ACTIVITY_TOPIC, which is what makes
    discovery visible in the browser rather than only in this process's stdout.
    """
    print(f"[discovered-gui] watching — live rows -> {LIVE_TABLE_PREFIX}/<category>")
    devices = sum(len(b) for b in collected.values())
    publish_activity(
        client, "info",
        f"watching {len(collected)} categor(ies), {devices} device(s) — live rows are on the bus",
    )
    last = None
    seen = device_states()
    while True:
        time.sleep(interval)
        fingerprint = json.dumps(collected, sort_keys=True, default=str)
        if fingerprint == last:
            continue
        last = fingerprint
        n = publish_live_tables(client)
        current = device_states()
        narrate_changes(client, seen, current)
        seen = current
        print(f"[discovered-gui] live update: {n} table(s)")


def write_panels():
    # Prune categories whose devices vanished (or moved group after a
    # knowledge-base fix). Pruning has to walk INSIDE the group folders now:
    # a top-level sweep would see the group names, not find them in `collected`,
    # and delete every tab on each run.
    import shutil
    wanted = {(group_for(c), c) for c in collected if c not in TOP_LEVEL_TABS}
    # Folder -> category, for the promoted tabs. These live at the top level and
    # would otherwise be swept as "ungrouped leftovers" on the very next run —
    # which is exactly what happened to a hand-made 5_PTP/ directory.
    promoted = {folder: cat for cat, (folder, _) in TOP_LEVEL_TABS.items()}
    if os.path.isdir(OUT_DIR):
        for entry in sorted(os.listdir(OUT_DIR)):
            path = os.path.join(OUT_DIR, entry)
            if entry == "0_Scan" or not os.path.isdir(path):
                continue
            if entry in promoted:
                # Keep it while its category still has devices; drop the whole
                # folder when it does not, so an empty tab does not linger.
                if promoted[entry] not in collected:
                    shutil.rmtree(path)
                    print(f"[discovered-gui] pruned empty top-level tab {entry}/")
                continue
            if entry in GROUPS:
                for cat in sorted(os.listdir(path)):
                    cat_path = os.path.join(path, cat)
                    if os.path.isdir(cat_path) and (entry, cat) not in wanted:
                        shutil.rmtree(cat_path)
                        print(f"[discovered-gui] pruned stale category {entry}/{cat}/")
                # An empty group folder would render as an empty tab.
                if not os.listdir(path):
                    os.rmdir(path)
                    print(f"[discovered-gui] pruned empty group {entry}/")
            else:
                # A category left at the top level by an earlier, ungrouped
                # build. Remove it so it does not shadow the grouped copy.
                shutil.rmtree(path)
                print(f"[discovered-gui] pruned ungrouped leftover {entry}/")

    written = 0
    for category, blocks in sorted(collected.items()):
        if category in TOP_LEVEL_TABS:
            folder, doc_name = TOP_LEVEL_TABS[category]
            cat_dir = os.path.join(OUT_DIR, folder)
        else:
            folder, doc_name = group_for(category), category
            cat_dir = os.path.join(OUT_DIR, folder, category)
        os.makedirs(cat_dir, exist_ok=True)
        headers, rows = rows_for(category, blocks)
        # The library OcaTable (libControl/text/OcaTable) — the component
        # built for exactly this ("Discovered Devices" in Sample.json):
        # sticky header, zebra rows, row-count footer, own scroll region.
        doc = {
            doc_name: {
                "type": "OcaBin",
                "description": {"En": f"Discovered {category} devices (scan snapshot)"},
                "behavior": {"overflow_ns": "auto"},
                "blocks": {
                    "Devices": {
                        "type": "OcaTable",
                        "description": {"En": f"Discovered {category} devices"},
                        # Live rows. `data` below is the cold-start snapshot so
                        # the table is populated the moment the panel loads;
                        # this topic then replaces it as devices change, with no
                        # rebuild and no browser refresh. Kept fresh by the
                        # watcher (see --watch).
                        "topic": f"{LIVE_TABLE_PREFIX}/{category}",
                        "headers": headers,
                        "data": rows,
                        "Sort": True,
                    }
                },
            }
        }
        out = os.path.join(cat_dir, f"{doc_name}.json")
        with open(out, "w") as f:
            json.dump(doc, f, indent=2)
        written += 1
        print(f"[discovered-gui] wrote {folder}/{doc_name} ({len(rows)} device(s), {len(headers)} columns)")
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
    watching = "--watch" in sys.argv

    # Claim the watcher slot BEFORE connecting, so a redundant copy costs one
    # file open rather than a broker connection and five seconds of collection.
    if watching and not acquire_watcher_lock():
        print("[discovered-gui] another watcher holds the lock — exiting")
        return

    client = make_client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("127.0.0.1", 1883, 60)
    client.loop_start()
    time.sleep(COLLECT_SECONDS)  # retained messages arrive immediately on subscribe

    if watching:
        # Publish-only: never writes panel files, so it cannot race the
        # one-shot builder. Rows go live; columns and new categories still come
        # from a rebuild, which the orchestrator triggers on rescan.
        publish_live_tables(client)
        try:
            watch(client)
        except KeyboardInterrupt:
            pass
        finally:
            client.loop_stop()
        return

    client.loop_stop()
    n = write_panels()
    devices = sum(len(blocks) for blocks in collected.values())
    write_scan_panel(devices)

    # One control panel per discovered instrument, stamped from the backend
    # template library. Runs here rather than as its own spawned process
    # because it needs exactly the device map this collector just built, and
    # because two processes writing Gui_Frames would race.
    try:
        import build_instrument_panels
        panels, built = build_instrument_panels.build(
            build_instrument_panels.devices_from_collected(collected))
        print(f"[discovered-gui] instrument panels: {built} device(s), {panels} file(s)")
    except Exception as e:  # a panel-build failure must not lose the tables
        print(f"⚠️  [discovered-gui] instrument panel build failed: {e}")
    # Seed the live topics too, so a panel written now has rows the instant it
    # loads rather than waiting for the watcher's first change.
    client.loop_start()
    publish_live_tables(client)
    # Drop the retained `<category>/config` leftovers. MQTT deletes retained
    # state by publishing an empty payload to the exact topic.
    for topic in sorted(stale_gui_config):
        client.publish(topic, b"", qos=1, retain=True)
    if stale_gui_config:
        print(f"[discovered-gui] cleared {len(stale_gui_config)} stale /config topic(s)")
    # Tell the browser the tab structure changed — a rebuild is the one thing
    # live rows cannot deliver, so this is where "reload" is actually warranted.
    publish_activity(
        client, "info",
        f"panels rebuilt — {n} categor(ies), {devices} device(s); reload for new tabs or columns",
    )
    time.sleep(0.5)
    client.loop_stop()
    if n == 0:
        print("[discovered-gui] no retained discovery topics found — only the scan panel written")


if __name__ == "__main__":
    main()
