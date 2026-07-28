"""Per-device instrument panels — one control surface per discovered instrument.

The instrument panels used to be a fixed display: one hand-placed DMM tab in
`FrontEnd/Gui_Frames/1_Instruments/left_100/`, bound to no instrument in
particular, however many DMMs were actually on the bench. This bench has eight
34401As, two loads and several scopes; it had one of each on screen.

So the authored panels moved to `BackEnd/Instruments/` (see the README
there) and this stamps one instance per discovered device back into the frontend
tree — eight DMMs become eight tabs, each bound to its own VISA resource.

Called by build_discovered_gui.py after every scan; also runnable by hand:

    python3 BackEnd/Core/orchestrator/gui/build_instrument_panels.py

Generated output is data: gitignored, and pruned when a device disappears.

An instrument type is TWO authored files and no folders:

    <Type>/<Type>.json     the instrument      — stamped once per device
    <Type>/<Type>_N.json   N of the instrument — the block that repeats

The sub-tab structure a device panel used to get from nested template folders
now comes from the instrument file's top-level keys, so the tree the author
edits is flat and the tree the UI renders is not.
"""
import glob
import json
import os
import re
import shutil

# BackEnd/Core/orchestrator/gui/ -> repo root is four levels up.
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")
)
TEMPLATE_ROOT = os.path.join(REPO_ROOT, "BackEnd", "Instruments")
YAK_ROOT = os.path.join(REPO_ROOT, "BackEnd", "openair-yak", "Yak")

# `${name}`, and deliberately not `<name>`: panel templates carry SCPI fragments
# (`"command_value": "VOLT <value>"`) and YAK's own command tables use `<chan>`,
# `<n>`, `<slot>`. Two substitution passes run over this data — this one at build
# time, YAK's at send time — and giving them the same delimiter is how a slot
# number ends up where a voltage belongs.
TOKEN = re.compile(r"\$\{(\w+)\}")
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


_CAPS = {}


def yak_capabilities(model):
    """What the model IS, from `BackEnd/openair-yak/Yak/**/<model>/model.json`.

    Channel counts and voltage/current ranges are properties of the instrument,
    so they live with the SCPI vocabulary rather than in the panel. Before this
    they lived nowhere machine-readable: the ranges were English in
    `knownDevices.json` ("Module 8V / 16A (128W)") and the scope's channel count
    was a description field reading "1, 2, 3, 4". Panels therefore shipped with
    no clamps at all, and the 8V module and the 60V module got the same widget.

    Looked up by model name, not by type — model names are unique across the YAK
    tree, and a second type→directory table is a second thing to keep in sync.
    """
    if model in _CAPS:
        return _CAPS[model]
    caps = {}
    for path in glob.glob(os.path.join(YAK_ROOT, "*", "*", "model.json")):
        if os.path.basename(os.path.dirname(path)).split("_", 1)[-1] == model:
            with open(path) as f:
                caps = json.load(f)
            break
    _CAPS[model] = caps
    return caps


def slot_of(resource):
    """Mainframe slot from a VISA resource, or None if the device isn't in one.

    `TCPIP::44.44.44.111::gpib7,30,4::INSTR` — board 7, primary 30, SECONDARY 4.
    The secondary address is the 66000A slot, and the only thing distinguishing
    the eight modules that all answer at primary 30.

    Three comma-parts is the test, and it has to be: the scope at
    `gpib7,6::INSTR` has two, where the `6` is its own primary address. Reading
    that as a slot would stamp `INST:NSEL 6` onto an instrument that has no
    slots.
    """
    m = re.search(r"gpib\d+,(\d+),(\d+)", resource or "", re.I)
    return int(m.group(2)) if m else None


def chassis_of(resource):
    """Key identifying the mainframe a device is plugged into.

    The resource with the secondary address removed, so all eight modules at
    `44.44.44.111::gpib7,30,*` share one key and group together, while a
    standalone supply is its own chassis of one.
    """
    return re.sub(r"(gpib\d+,\d+),\d+", r"\1", resource or "", flags=re.I)


def host_of(resource):
    """The instrument's host, for grouping things that share a bench but not a box.

    The eight 34401As are eight separate meters at eight GPIB primary addresses
    behind one gateway — no mainframe to group them by, yet a bank of eight is
    exactly the view that bench wants. `by: "host"` in the manifest selects this
    axis; `by: "chassis"` (the default) is for modules that really do plug into
    the same frame.
    """
    parts = (resource or "").split("::")
    return parts[1] if len(parts) > 1 else (resource or "")


def substitute(node, tokens):
    """Replace `${...}` through a copied template — in values AND in key names.

    Key names matter as much as values: a panel's identity in the frontend tree
    is its top-level key, so eight copies of one module template all named
    `Power_Module_1` would be eight panels claiming to be the same panel. That
    single differing line is the only thing the eight hand-maintained module
    files ever encoded.
    """
    if isinstance(node, dict):
        return {TOKEN.sub(lambda m: str(tokens.get(m.group(1), m.group(0))), k):
                substitute(v, tokens) for k, v in node.items()}
    if isinstance(node, list):
        return [substitute(v, tokens) for v in node]
    if isinstance(node, str):
        return TOKEN.sub(lambda m: str(tokens.get(m.group(1), m.group(0))), node)
    return node


def apply_domains(node, caps):
    """Resolve `"yak_domain": "volt"` against the model's capability sheet.

    The template names the quantity; the model supplies units and limits. A
    template cannot hardcode them and stay one template — this bench runs four
    module models spanning 8V/16A to 60V/2.5A off the same panel.
    """
    resolved = 0
    if isinstance(node, dict):
        key = node.get("yak_domain")
        if isinstance(key, str):
            spec = (caps.get("domains") or {}).get(key)
            if spec:
                node.setdefault("domain", {}).update(spec)
                resolved += 1
            else:
                # Silence here would look identical to a clamped widget.
                print(f"[instrument-gui] no '{key}' domain for model "
                      f"{caps.get('model', '?')} — widget left unclamped")
        for value in node.values():
            resolved += apply_domains(value, caps)
    elif isinstance(node, list):
        for item in node:
            resolved += apply_domains(item, caps)
    return resolved


def template(itype, suffix=""):
    """Path of one of an instrument's two authored files."""
    return os.path.join(TEMPLATE_ROOT, itype, f"{itype}{suffix}.json")


def unit_blocks(itype):
    """(repeating block, {deck name: deck block}) from `<Type>_N.json`.

    The N file is an ordinary panel — one OcaBin — so it opens in the WYSIWYG
    editor like anything else. Grouping unwraps it: the repeating block becomes
    one field of a generated station block, which is the shape the hand-authored
    `psu_four`/`psu_eight` had, only reached by composition instead of by
    copy-paste.

    The repeating block is the one carrying `${n}` in its name, because that is
    already what makes N copies of it N distinct panels rather than one panel
    claiming to exist N times. Every OTHER block in the file is a header deck —
    a strip that commands the whole group (`OUTP:ALL`) rather than one member —
    which a group spec asks for by name. Power keeps both of its decks that way:
    the bank of eight gets the logger, the quads get the master interlock, and
    neither needs a folder of its own to live in.
    """
    doc = read_panel(template(itype, "_N"))
    if doc is None:
        return None, {}
    for outer in doc.values():
        blocks = outer.get("blocks") or {}
        unit = next((b for name, b in blocks.items() if "${n}" in name), None)
        decks = {name: b for name, b in blocks.items() if "${n}" not in name}
        return unit, decks
    return None, {}


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


def bind_readout(node, read_topic):
    """Point display widgets at the device's SCPI reply topic.

    A query is only half a readout: YAK sends `:READ?` to the Write topic, the
    VISA daemon executes it and publishes the answer (retained) to `/Read`. A
    widget marked `"yak_readout": true` in the template gets `topic` set to that
    reply topic, so the meter actually shows what the instrument said instead of
    a dash. Without this the panel can command an instrument but never hear it.

    The template cannot hardcode the topic — it is per device — which is why
    this is a marker the builder resolves rather than a literal.
    """
    bound = 0
    if isinstance(node, dict):
        if node.get("yak_readout") is True:
            node["topic"] = read_topic
            bound += 1
        for value in node.values():
            bound += bind_readout(value, read_topic)
    elif isinstance(node, list):
        for item in node:
            bound += bind_readout(item, read_topic)
    return bound


def bind_node(node, write_topic, model, params=None):
    """Recursively stamp device binding onto every yak_handler in a panel.

    `target` is the topic the VISA daemon executes SCPI on; without it YAK
    publishes every command to its global pub topic, which nothing subscribes to
    — the reason the panels have never actually driven an instrument. `model`
    narrows YAK's SCPI lookup to this instrument's command table instead of
    "first command of that name found in any model".

    `params` are the constants this instance addresses itself with — `chan` for
    a mainframe slot or a scope channel. The command table is per model, and
    four of the eight modules here are 66104As, so the slot cannot live in the
    table: it read `INST:NSEL 1` for every one of them. YAK substitutes these
    before the widget value (openair-yak/src/verbs/mod.rs, apply_params).
    """
    stamped = 0
    if isinstance(node, dict):
        handler = node.get("yak_handler")
        if isinstance(handler, dict):
            handler["target"] = write_topic
            handler["model"] = model
            if params:
                handler["params"] = dict(params)
            stamped += 1
        for value in node.values():
            stamped += bind_node(value, write_topic, model, params)
    elif isinstance(node, list):
        for item in node:
            stamped += bind_node(item, write_topic, model, params)
    return stamped


def prepare(doc, dev, tokens=None):
    """Bind one panel document to one device: tokens, limits, topics, slot.

    Every panel goes through here, whether it was stamped on its own or nested
    into a group, so a module strip in the bank-of-8 is bound exactly as tightly
    as the same strip on its own tab.
    """
    model = dev.get("model", "")
    resource = dev.get("resource", "")
    slot = slot_of(resource)
    caps = yak_capabilities(model)

    marks = dict(tokens or {})
    marks.setdefault("model", model)
    marks.setdefault("resource", resource)
    marks.setdefault("slot", "-" if slot is None else slot)
    doc = substitute(doc, marks)

    apply_domains(doc, caps)

    write_topic = dev.get("write_topic", "")
    # SCPI channel numbering is 1-based; the GPIB secondary address is 0-based.
    params = {}
    if "chan" in marks:
        params["chan"] = str(marks["chan"])
    elif slot is not None:
        params["chan"] = str(slot + 1)
    handlers = bind_node(doc, write_topic, model, params)

    # `/Read` is where the VISA daemon publishes what the instrument answered;
    # the Write topic is where commands go.
    if write_topic.endswith("/Write"):
        bind_readout(doc, write_topic[:-len("/Write")] + "/Read")
    return doc, handlers


def read_panel(path):
    """Load one authored panel, or None if it isn't one.

    Only `.json` is read: the WYSIWYG editor leaves `*.json.old` backups all
    over the authored tree (the Spectrum template has eight of them), and those
    are neither valid panels nor anything a device tab should show.
    """
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[instrument-gui] skipping malformed {path}: {e}")
        return None


def write_panel(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(doc, f, indent=2)


def instantiate(itype, out_dir, dev):
    """Stamp `<Type>.json` for one device, exploding its top-level keys to tabs.

    A device panel's sub-tabs used to be authored as nested template folders —
    `Spectrum/Instrument/{amplitude,bandwidth,frequency,markers,traces}/`, one
    file each, five folders deep to hold five panels. The folders were the only
    thing the author got out of that depth, and the frontend builds tabs from
    folders anyway (WindowManager.TabContainer), so the keys can carry it:

        {"amplitude": {...}, "bandwidth": {...}}  ->  0_amplitude/, 1_bandwidth/

    Key order is tab order, which is why the `<i>_` prefix goes on: TabContainer
    sorts on it, and OaTopicMaker strips it back off, so the topic a widget
    publishes on is unchanged by the numbering.

    A key may instead hold a MAP of panels — the Router's `Coax` tab is two
    cards stacked in one pane — which is the same either-a-node-or-a-map test
    LoaderOrchestrator already makes on a file's own root. One key and one
    panel means no sub-tab at all: the file lands straight in the device folder,
    as the single-panel types (DMM, Load, LCR, …) have always rendered.
    """
    doc = read_panel(template(itype))
    if doc is None:
        print(f"[instrument-gui] template missing: {template(itype)}")
        return 0, 0

    entries = list(doc.items())
    if len(entries) == 1:
        bound_doc, handlers = prepare(dict(entries), dev)
        write_panel(os.path.join(out_dir, f"{itype}.json"), bound_doc)
        return 1, handlers

    panels = handlers = 0
    for i, (tab, node) in enumerate(entries):
        stack = {tab: node} if isinstance(node.get("type"), str) else node
        for j, (name, panel) in enumerate(stack.items()):
            bound_doc, bound = prepare({name: panel}, dev)
            write_panel(os.path.join(out_dir, f"{i}_{tab}", f"{j}_{name}.json"), bound_doc)
            handlers += bound
            panels += 1
    return panels, handlers


def repeat_unit(itype, spec, members, station_id, root):
    """Compose N bound copies of one unit template into a single group panel.

    This is the whole point of the exercise. `psu_eight.json` was 1183 lines of
    one module strip written out eight times; `psu_four.json` was the same strip
    four times with a different header. Neither could be right about limits,
    because a hand-authored file has one set of widgets and this chassis holds
    four different module models — the 8V strip and the 60V strip were the same
    strip. Composed here, each copy is bound to its own device, its own slot and
    its own model's ranges.

    `members` is [(tokens, device)] — the caller decides what repeats: sibling
    modules across a mainframe, or channels within one instrument.
    """
    unit, decks = unit_blocks(itype)
    if unit is None:
        print(f"[instrument-gui] {template(itype, '_N')} has no ${{n}} block to repeat")
        return None, 0

    fields, handlers = {}, 0
    wanted_deck = spec.get("header")
    if wanted_deck:
        block = decks.get(wanted_deck)
        if block is None:
            print(f"[instrument-gui] {itype}_N.json has no '{wanted_deck}' deck — "
                  f"{spec['name']} built without its header")
        else:
            # The header commands the whole group (`OUTP:ALL`), so it binds to
            # the first member — any of them reaches the mainframe.
            block, bound = prepare(json.loads(json.dumps(block)),
                                   members[0][1], members[0][0])
            handlers += bound
            fields[wanted_deck] = block

    for tokens, dev in members:
        copy, bound = prepare(json.loads(json.dumps(unit)), dev, tokens)
        handlers += bound
        fields[f"Unit_{tokens['n']}"] = copy

    station = {
        "type": "OcaBlock",
        "description": spec.get("description", {"En": spec["name"]}),
        "layout_columns": spec.get("columns", min(4, len(members))),
        "fields": fields,
    }
    return {root: {
        "type": "OcaBin",
        "id": station_id,
        "geometry": {"anchor": "NSEW"},
        "behavior": {"overflow_ns": "auto", "overflow_ew": "auto", "fluid_ew": True},
        "blocks": {spec.get("station", "Station"): station},
    }}, handlers


def chunk(items, size):
    """Split into groups of `size`; `"all"` means one group of everything."""
    if size == "all":
        return [items] if items else []
    return [items[i:i + size] for i in range(0, len(items), size)]


def build_group_panels(itype, spec, tab, devices):
    """Emit the group views declared for one instrument type.

    `over: "devices"` repeats across the instruments sharing a mainframe — the
    bank of 8, the quads, the pairs. `over: "channels"` repeats within a single
    instrument, once per channel its model declares, which is the same shape:
    two 54641Ds and a 4-channel Rigol are three devices whose panels differ only
    in how many identical channel strips they carry.
    """
    written = built = 0
    wanted = set()
    for group in spec.get("groups", []):
        instances = []
        if group.get("over") == "channels":
            for dev in devices:
                n = (yak_capabilities(dev.get("model", "")) or {}).get("channels")
                if not n:
                    print(f"[instrument-gui] {dev.get('model')} declares no channel "
                          f"count in its YAK model.json — {group['name']} skipped")
                    continue
                members = [({"n": i, "chan": i, "label": f"CH{i}"}, dev)
                           for i in range(1, n + 1)]
                instances.append((device_slug(dev.get("model"), dev.get("resource", "")),
                                  members))
        else:
            key_of = host_of if group.get("by") == "host" else chassis_of
            chassis = {}
            for dev in devices:
                chassis.setdefault(key_of(dev.get("resource", "")), []).append(dev)
            for key, members in sorted(chassis.items()):
                # Slot order where there are slots, address order otherwise, so a
                # bank reads left-to-right the way the rack is wired rather than
                # in whatever order discovery happened to answer.
                members.sort(key=lambda d: (slot_of(d.get("resource", "")) or 0,
                                            d.get("resource", "")))
                if len(members) < 2:
                    continue  # a "bank" of one is just the device's own panel
                for idx, part in enumerate(chunk(members, group.get("size", "all")), 1):
                    tagged = [({"n": i, "label": f"{d.get('model')}"}, d)
                              for i, d in enumerate(part, 1)]
                    slug = device_slug(group["name"], key)
                    instances.append((f"{slug}_{idx}" if group.get("size") != "all"
                                      else slug, tagged))

        for slug, members in instances:
            # Root key carries the slug: four pair-panels off one mainframe are
            # four panels, not one panel claiming to exist four times.
            doc, handlers = repeat_unit(itype, dict(group), members,
                                        group.get("id", "50.100.0.0"),
                                        re.sub(r"[^A-Za-z0-9]+", "_", slug))
            if doc is None:
                continue
            out_dir = os.path.join(OUT_ROOT, tab, group["name"], slug)
            if os.path.isdir(out_dir):
                shutil.rmtree(out_dir)
            write_panel(os.path.join(out_dir, "group.json"), doc)
            with open(os.path.join(out_dir, STAMP), "w") as f:
                json.dump({"group": group["name"], "members": len(members)}, f, indent=2)
            wanted.add(os.path.join(tab, group["name"], slug))
            written += 1
            built += 1
            print(f"[instrument-gui] {tab}/{group['name']}/{slug} — "
                  f"{len(members)} unit(s), {handlers} bound command(s)")
    return written, built, wanted


def prune(wanted):
    """Delete generated folders that no longer match a live device or group.

    `wanted` is a set of paths relative to OUT_ROOT. Matching on the stamp file
    rather than on a fixed depth, because a device panel sits at `<tab>/<slug>`
    and a group panel one level deeper at `<tab>/<group>/<slug>`. Only stamped
    directories are removed, so a hand-authored panel dropped into the same tree
    survives — deleting someone's authored work because it sat in a generated
    directory is not a recoverable mistake.
    """
    if not os.path.isdir(OUT_ROOT):
        return
    stale = []
    for root, dirs, files in os.walk(OUT_ROOT):
        if STAMP not in files:
            continue
        dirs[:] = []
        rel = os.path.relpath(root, OUT_ROOT)
        if rel not in wanted:
            stale.append((rel, root))
    for rel, path in stale:
        shutil.rmtree(path)
        print(f"[instrument-gui] pruned {rel}")
    # Empty tab/group folders go with them, so a type that vanished from the
    # bench does not leave a dead tab behind. Deepest-first, so a group folder
    # emptied by its own pruning is collected in the same pass.
    for root, dirs, files in sorted(os.walk(OUT_ROOT, topdown=False), reverse=False):
        if root != OUT_ROOT and not os.listdir(root):
            os.rmdir(root)


def build(devices):
    """devices: [{type, model, resource, write_topic}] — one panel each.

    Returns (panels_written, devices_built).
    """
    manifest = load_manifest()
    wanted = set()
    written = built = 0
    by_type = {}

    for dev in devices:
        spec = manifest.get(dev.get("type"))
        by_type.setdefault(dev.get("type"), []).append(dev)
        if not spec:
            # A discovered type with no authored template (VNA, Counter, DAQ,
            # SMU today). Silent skip would read as a broken build.
            print(f"[instrument-gui] no template for type {dev.get('type')!r} — {dev.get('model')} skipped")
            continue

        slug = device_slug(dev.get("model", "unknown"), dev.get("resource", ""))
        out_dir = os.path.join(OUT_ROOT, spec["tab"], slug)
        # Rewrite rather than merge: a stale panel from a previous template is
        # worse than a missing one, and the folder is generated data.
        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)
        panels, handlers = instantiate(dev["type"], out_dir, dev)
        if not panels:
            continue
        with open(os.path.join(out_dir, STAMP), "w") as f:
            json.dump({"type": dev.get("type"), "model": dev.get("model"),
                       "resource": dev.get("resource"),
                       "write_topic": dev.get("write_topic")}, f, indent=2)
        wanted.add(os.path.join(spec["tab"], slug))
        written += panels
        built += 1
        print(f"[instrument-gui] {spec['tab']}/{slug} — {panels} panel(s), {handlers} bound command(s)")

    # Group views come after the per-device pass because they are about the
    # bench rather than about one instrument — which modules share a mainframe,
    # how many channels a scope has. Nothing to build until every device is in.
    for dtype, group_devices in sorted(by_type.items()):
        spec = manifest.get(dtype)
        if not spec or not spec.get("groups"):
            continue
        gw, gb, gwanted = build_group_panels(dtype, spec, spec["tab"], group_devices)
        written += gw
        built += gb
        wanted |= gwanted

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
