"""Per-device instrument panels — one control surface per discovered instrument.

The instrument panels used to be a fixed display: one hand-placed DMM tab in
`FrontEnd/Gui_Frames/1_Instruments/left_100/`, bound to no instrument in
particular, however many DMMs were actually on the bench. This bench has eight
34401As, two loads and several scopes; it had one of each on screen.

So the authored panels moved to `BackEnd/Instruments/Templates/` (see the README
there) and this stamps one instance per discovered device back into the frontend
tree — eight DMMs become eight tabs, each bound to its own VISA resource.

Called by build_discovered_gui.py after every scan; also runnable by hand:

    python3 Deployment/build_instrument_panels.py

Generated output is data: gitignored, and pruned when a device disappears.
"""
import json
import os
import re
import shutil

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_ROOT = os.path.join(REPO_ROOT, "BackEnd", "Instruments", "Templates")
# Back into the tab the templates were evacuated from, so the Instruments tab
# keeps its place in the UI — only its contents are now generated rather than
# authored. `left_100` (not `left_50`) because an instrument gets the FULL tab
# width: the right-hand half was retired, and a bench panel reads better across
# the whole window than squeezed into a column. See WindowManager.parseSplitName
# — /^(left|right|top|bottom)_(\d+)$/ , the number being percent of the parent.
OUT_ROOT = os.path.join(REPO_ROOT, "FrontEnd", "Gui_Frames", "1_Instruments", "left_100")

# Marker file identifying a generated device folder. Pruning only ever deletes
# directories carrying this, so a hand-authored panel dropped into the same tree
# survives — deleting someone's authored work because it sat in a generated
# directory is not a recoverable mistake.
STAMP = ".generated-by-openair"


def load_manifest():
    with open(os.path.join(TEMPLATE_ROOT, "manifest.json")) as f:
        return json.load(f)


def device_slug(model, resource):
    """Folder name for one device — this becomes its tab label.

    Model alone is not identity: this bench has eight 34401As reporting serial
    "0", so `34401A` would name all eight. The VISA resource is what actually
    distinguishes them (host + GPIB address), so the address tail rides along:
    `34401A_44-44-44-111_gpib7-4`. Ugly, and correct; a friendly name belongs in
    a user-editable alias map, not in the identity that panels are keyed on.
    """
    tail = resource or ""
    tail = tail.replace("TCPIP::", "").replace("::INSTR", "")
    tail = re.sub(r"[^A-Za-z0-9]+", "-", tail).strip("-")
    slug = f"{model}_{tail}" if tail else str(model)
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", slug)


def bind_node(node, write_topic, model):
    """Recursively stamp device binding onto every yak_handler in a panel.

    `target` is the topic the VISA daemon executes SCPI on; without it YAK
    publishes every command to its global pub topic, which nothing subscribes to
    — the reason the panels have never actually driven an instrument. `model`
    narrows YAK's SCPI lookup to this instrument's command table instead of
    "first command of that name found in any model".
    """
    stamped = 0
    if isinstance(node, dict):
        handler = node.get("yak_handler")
        if isinstance(handler, dict):
            handler["target"] = write_topic
            handler["model"] = model
            stamped += 1
        for value in node.values():
            stamped += bind_node(value, write_topic, model)
    elif isinstance(node, list):
        for item in node:
            stamped += bind_node(item, write_topic, model)
    return stamped


def instantiate(template_dir, out_dir, write_topic, model, exclude=()):
    """Copy one template subtree, binding every panel in it to one device.

    Only `.json` is copied: the WYSIWYG editor leaves `*.json.old` backups all
    over the authored tree (the Spectrum template has eight of them), and those
    are neither valid panels nor anything a device tab should show.
    """
    panels = handlers = 0
    for root, dirs, files in os.walk(template_dir):
        rel = os.path.relpath(root, template_dir)
        parts = [] if rel == "." else rel.split(os.sep)
        if parts and parts[0] in exclude:
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in exclude]
        for name in files:
            if not name.endswith(".json"):
                continue
            with open(os.path.join(root, name)) as f:
                try:
                    doc = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"[instrument-gui] skipping malformed {os.path.join(root, name)}: {e}")
                    continue
            handlers += bind_node(doc, write_topic, model)
            dest_dir = out_dir if rel == "." else os.path.join(out_dir, rel)
            os.makedirs(dest_dir, exist_ok=True)
            with open(os.path.join(dest_dir, name), "w") as f:
                json.dump(doc, f, indent=2)
            panels += 1
    return panels, handlers


def prune(wanted):
    """Delete generated device folders that no longer match a live device.

    `wanted` is {(tab, slug)}. Only stamped directories are removed, and an
    emptied tab folder goes with them so a device type that vanished does not
    leave an empty tab behind.
    """
    if not os.path.isdir(OUT_ROOT):
        return
    for tab in sorted(os.listdir(OUT_ROOT)):
        tab_path = os.path.join(OUT_ROOT, tab)
        if not os.path.isdir(tab_path):
            continue
        for slug in sorted(os.listdir(tab_path)):
            dev_path = os.path.join(tab_path, slug)
            if not os.path.isdir(dev_path):
                continue
            if (tab, slug) in wanted or not os.path.isfile(os.path.join(dev_path, STAMP)):
                continue
            shutil.rmtree(dev_path)
            print(f"[instrument-gui] pruned {tab}/{slug}")
        if os.path.isdir(tab_path) and not os.listdir(tab_path):
            os.rmdir(tab_path)


def build(devices):
    """devices: [{type, model, resource, write_topic}] — one panel each.

    Returns (panels_written, devices_built).
    """
    manifest = load_manifest()
    wanted = set()
    written = built = 0

    for dev in devices:
        spec = manifest.get(dev.get("type"))
        if not spec:
            # A discovered type with no authored template (VNA, Counter, DAQ,
            # SMU today). Silent skip would read as a broken build.
            print(f"[instrument-gui] no template for type {dev.get('type')!r} — {dev.get('model')} skipped")
            continue
        template_dir = os.path.join(TEMPLATE_ROOT, dev["type"], spec["panel"])
        if not os.path.isdir(template_dir):
            print(f"[instrument-gui] template missing: {template_dir}")
            continue

        slug = device_slug(dev.get("model", "unknown"), dev.get("resource", ""))
        out_dir = os.path.join(OUT_ROOT, spec["tab"], slug)
        # Rewrite rather than merge: a stale panel from a previous template is
        # worse than a missing one, and the folder is generated data.
        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)
        panels, handlers = instantiate(
            template_dir, out_dir, dev.get("write_topic", ""), dev.get("model", ""),
            exclude=set(spec.get("exclude", [])),
        )
        with open(os.path.join(out_dir, STAMP), "w") as f:
            json.dump({"type": dev.get("type"), "model": dev.get("model"),
                       "resource": dev.get("resource"),
                       "write_topic": dev.get("write_topic")}, f, indent=2)
        wanted.add((spec["tab"], slug))
        written += panels
        built += 1
        print(f"[instrument-gui] {spec['tab']}/{slug} — {panels} panel(s), {handlers} bound command(s)")

    prune(wanted)
    return written, built


def devices_from_collected(collected):
    """Adapt build_discovered_gui's `collected` map to build()'s device list.

    VISA categories ARE the knowledge-base type (DMM, Spectrum, …), so the
    category name selects the template. `_topic_prefix` is recorded by the
    collector because the device's Write topic cannot be reconstructed from the
    row fields alone.
    """
    manifest = load_manifest()
    devices = []
    for category, blocks in collected.items():
        if category not in manifest:
            continue
        for fields in blocks.values():
            prefix = fields.get("_topic_prefix")
            if not prefix:
                continue
            devices.append({
                "type": category,
                "model": fields.get("model", "unknown"),
                "resource": fields.get("resource", ""),
                "write_topic": f"{prefix}/Write",
            })
    return devices


def main():
    """Standalone run: read the retained VISA tree off the broker directly."""
    import build_discovered_gui as discovered  # same directory, same collector

    client = discovered.make_client()
    client.on_connect = discovered.on_connect
    client.on_message = discovered.on_message
    client.connect("127.0.0.1", 1883, 60)
    client.loop_start()
    import time
    time.sleep(discovered.COLLECT_SECONDS)
    client.loop_stop()

    written, built = build(devices_from_collected(discovered.collected))
    print(f"[instrument-gui] {built} device panel set(s), {written} panel file(s)")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
