"""Cross-reference instrument panel controls against YAK's SCPI vocabulary.

A generated per-device panel only drives its instrument where a widget carries a
`yak_handler`. Today the Spectrum and Router templates carry them and the rest
carry none — so eight bound DMM tabs still send nothing. Closing that gap means
answering, per instrument family, three questions:

  1. which controls are already wired            (BOUND)
  2. which controls have a command available     (MATCH — the work worth doing)
  3. which controls have no command at all       (CONTROL-ONLY — SCPI to author)
  4. which commands no control exposes           (COMMAND-ONLY — capability sitting
                                                  unused; candidate for new widgets)

This reads both sides from their sources of truth: the YAK tree using the SAME
extraction rules as repository.rs (model = grandparent directory, command = a key
whose node carries an `Execute Command` message), and the template library under
BackEnd/Instruments.

Matching is a SUGGESTION, not an authority. Name similarity cannot know that a
DMM's `Mode_FRES` means four-wire resistance; the curated ALIASES table carries
the domain knowledge, and everything else is scored so a human can judge it.
Nothing here writes a binding — see --emit for a handler stub.

    python3 BackEnd/openair-yak/tools/yak_crossref.py                 # summary for every type
    python3 BackEnd/openair-yak/tools/yak_crossref.py DMM --verbose   # full table for one type
    python3 BackEnd/openair-yak/tools/yak_crossref.py DMM --emit      # yak_handler stubs to paste
"""
import argparse
import difflib
import glob
import json
import os
import re

# BackEnd/openair-yak/tools/ -> repo root is three levels up.
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)
YAK_ROOT = os.path.join(REPO_ROOT, "BackEnd", "openair-yak", "Yak")
TEMPLATE_ROOT = os.path.join(REPO_ROOT, "BackEnd", "Instruments")

# Which models a type's panels should be cross-referenced against. A type can
# have several (the bench has two scope families and four PSU modules), and a
# control is considered covered if ANY of them offers the command — the panel is
# stamped per device, so each instance resolves against its own model.
TYPE_MODELS = {
    "DMM": ["34401A"],
    "Load": ["6060B"],
    "Power": ["66101A", "66102A", "66103A", "66104A"],
    "Generator": ["33210A", "33220A"],
    "Oscilloscope": ["54641D", "DS1104Z"],
    "Spectrum": ["N9340B", "N9342CN", "HPE4411A"],
    "Router": ["3235"],
    # LCR and Distortion have templates in the manifest and folders in the YAK
    # tree, but were absent here — so the audit reported nothing about them and
    # they read as "no problem" when in fact nobody had looked. Listed now even
    # though 4263A and HP_8903B currently yield zero commands: an explicit
    # all-controls-unbacked row is the finding, silence is not.
    "LCR": ["4263A"],
    "Distortion": ["Porta_one", "HP_8903B"],
}

# Every type in Templates/manifest.json must appear above, else it is silently
# skipped. This is checked at startup rather than trusted.

# Domain knowledge name similarity cannot supply. control name -> command name.
# Deliberately small: only pairs a technician would call obvious, where the
# words share no useful stem.
ALIASES = {
    "DMM": {
        "Mode_VDC": "Config_DC_Volts",
        "Mode_VAC": "Config_AC_Volts",
        "Mode_RES": "Measure_Resistance_2Wire",
        "Mode_FRES": "Config_Resistance_4Wire",
        "Mode_ADC": "Measure_DC_Current",
        "Primary_Readout": "Read_Next",
        "Trend_Graph": "Fetch_Existing",
        "DMM_MODEL": "Read_IDN",
    },
    "Load": {
        "Master_Input_Switch": "Input_ON",
        "Set_Current": "Set_Current_Level",
        "Meter_Volts": "Measure_All",
        "Meter_Amps": "Measure_All",
        "Meter_Watts": "Measure_All",
        "DC_LOAD_MODEL": "IDN",
    },
    "Power": {
        "Master_Output_Switch": "Output_ON",
        "Voltage_Fader": "Set_Voltage",
        "Current_Fader": "Set_Current",
    },
}

# Widget types that display rather than command. They can still carry a handler
# (a readout is a query), so they are reported — just never counted as missing.
READOUT_TYPES = {"_GuiLabel", "_NeedleVUMeter", "_GuiGraph", "_TextInput", "_GuiValue", "_Value"}

SKIP_KEYS = {"label", "style", "cosmetics", "layout", "domain", "options", "description",
             "message_details", "behavior", "geometry"}


def yak_vocabulary():
    """{model: {command: scpi}} from `Yak/<Family>/<Model>/commands.json`.

    A read, not a reconstruction. The tables used to be panel trees that a
    command table was pattern-matched out of, so this function mirrored
    YakRepository::extract_commands including its two failure modes: a widget's
    `fields` key counted as a command (555 of them), and the model taken from the
    file's grandparent directory, which filed 391 commands under folder names.
    Both went away with the shape.
    """
    models = {}
    for path in glob.glob(os.path.join(YAK_ROOT, "*", "*", "commands.json")):
        try:
            with open(path) as f:
                table = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"⚠️  unreadable {path}: {e}")
            continue
        commands = models.setdefault(table["model"], {})
        for verb in ("set", "do", "rig", "nab"):
            for name, entry in (table.get(verb) or {}).items():
                commands[name] = entry["scpi"]
    return models


def template_controls(type_name):
    """[(widget_name, widget_type, has_handler)] for a type's per-device panel.

    One file per type — `<Type>/<Type>.json` — since the templates flattened;
    see the README there. The `<Type>_N.json` beside it is deliberately not read:
    its widgets are the same controls again, repeated per member, and counting
    them would report a type's coverage twice.
    """
    found, seen = [], set()

    def walk(node, name):
        if isinstance(node, dict):
            wtype = node.get("type")
            if isinstance(wtype, str) and wtype.startswith("_") and name and name not in seen:
                seen.add(name)
                # A readout is bound too: `yak_readout` makes the builder point the
                # widget at the device's /Read topic, which is how a display widget
                # participates. Counting it as unbound would report finished work.
                bound = isinstance(node.get("yak_handler"), dict) or node.get("yak_readout") is True
                found.append((name, wtype, bound))
            for key, value in node.items():
                if key in SKIP_KEYS:
                    continue
                walk(value, key if isinstance(value, dict) else name)
        elif isinstance(node, list):
            for item in node:
                walk(item, name)

    path = os.path.join(TEMPLATE_ROOT, type_name, f"{type_name}.json")
    try:
        with open(path) as f:
            walk(json.load(f), None)
    except (OSError, json.JSONDecodeError):
        pass
    return found


def normalize(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def tokens(text):
    return {t for t in re.split(r"[^a-z0-9]+", text.lower()) if len(t) > 1}


def suggest(control, commands, type_name):
    """(command, score, why) or None. Score 100 = curated alias."""
    alias = ALIASES.get(type_name, {}).get(control)
    if alias and alias in commands:
        return alias, 100, "alias"

    control_tokens = tokens(control)
    best = (None, 0.0, "")
    for command in commands:
        overlap = control_tokens & tokens(command)
        # Token overlap carries the meaning ("Set_Current" vs "Set_Current_Level");
        # the sequence ratio breaks ties between equally-overlapping candidates.
        score = len(overlap) * 30 + difflib.SequenceMatcher(
            None, normalize(control), normalize(command)).ratio() * 40
        if score > best[1]:
            best = (command, score, "+".join(sorted(overlap)) or "similar")
    return best if best[1] >= 30 else None


def report(type_name, vocab, verbose=False):
    models = TYPE_MODELS.get(type_name, [])
    commands = {}
    for model in models:
        for command, scpi in vocab.get(model, {}).items():
            commands.setdefault(command, (scpi, model))

    controls = template_controls(type_name)
    bound = [c for c in controls if c[2]]
    unbound = [c for c in controls if not c[2]]

    matched, orphan_controls = [], []
    for name, wtype, _ in unbound:
        hit = suggest(name, commands, type_name)
        if hit:
            matched.append((name, wtype, hit[0], commands[hit[0]][0], hit[1], hit[2]))
        else:
            orphan_controls.append((name, wtype))

    used = {m[2] for m in matched}
    unused = sorted(set(commands) - used)

    print(f"\n{'=' * 78}\n{type_name}  —  models: {', '.join(models) or 'none'}  "
          f"({len(commands)} commands, {len(controls)} widgets)\n{'=' * 78}")
    print(f"  BOUND        {len(bound):3d}  already carry a yak_handler")
    print(f"  MATCH        {len(matched):3d}  control + command exist, binding missing  <- the work")
    print(f"  CONTROL-ONLY {len(orphan_controls):3d}  no command found (SCPI to author)")
    print(f"  COMMAND-ONLY {len(unused):3d}  command exists, no control exposes it")

    if verbose:
        print("\n  -- proposed bindings " + "-" * 55)
        for name, wtype, command, scpi, score, why in sorted(matched, key=lambda m: -m[4]):
            flag = "  " if score >= 100 else ("? " if score < 55 else "~ ")
            print(f"  {flag}{name[:30]:30s} -> {command[:32]:32s} {scpi[:38]}")
            if score < 100:
                print(f"      {'':30s}    (match: {why}, score {score:.0f})")
        if orphan_controls:
            print("\n  -- controls with no command " + "-" * 47)
            for name, wtype in orphan_controls:
                tag = "readout" if wtype in READOUT_TYPES else "CONTROL"
                print(f"    [{tag}] {name[:34]:34s} {wtype}")
        if unused:
            print("\n  -- unused commands " + "-" * 56)
            for command in unused:
                print(f"    {command[:34]:34s} {commands[command][0][:40]}")
    return matched


def emit_stubs(type_name, matched):
    """yak_handler blocks for the proposed bindings, ready to paste.

    `target` and `model` are deliberately absent: build_instrument_panels.py
    stamps those per device, and a hardcoded one in the template would point
    every instance at the same instrument.
    """
    print(f"\n// yak_handler stubs for {type_name} — verb/converter need a human pass")
    for name, wtype, command, scpi, _score, _why in sorted(matched):
        placeholder = re.search(r"<(\w+)>", scpi)
        verb = "nab" if scpi.rstrip().endswith("?") else ("set" if placeholder else "do")
        stub = {"enable": True, "yak_type": verb, "sub_path": type_name, "command": command}
        if placeholder:
            stub["input_name"] = placeholder.group(1)
            stub["converter"] = ""
        print(f'  "{name}": {{"yak_handler": {json.dumps(stub)}}},')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("type", nargs="?", help="instrument type (default: all)")
    ap.add_argument("--verbose", "-v", action="store_true", help="full per-control tables")
    ap.add_argument("--emit", action="store_true", help="print yak_handler stubs")
    args = ap.parse_args()

    vocab = yak_vocabulary()

    # A type present in the manifest but missing from TYPE_MODELS is not
    # "clean" — it is unexamined. Say so loudly rather than omitting the row.
    try:
        with open(os.path.join(TEMPLATE_ROOT, "manifest.json")) as f:
            unlisted = sorted(set(json.load(f)) - set(TYPE_MODELS))
        if unlisted:
            print(f"⚠️  manifest types with no models listed here (NOT analyzed): {', '.join(unlisted)}\n")
    except (OSError, json.JSONDecodeError):
        pass

    # Commands whose model key is not a real model: the grandparent-is-the-model
    # rule (repository.rs) mis-files anything nested deeper than
    # <model>/<section>/file.json. These are unreachable at runtime whenever YAK
    # narrows a lookup by model, so they are reported, not silently dropped.
    real_models = {m for ms in TYPE_MODELS.values() for m in ms}
    phantom = {m: len(c) for m, c in vocab.items() if m not in real_models}
    if phantom:
        total = sum(phantom.values())
        detail = ", ".join(f"{m} ({n})" for m, n in sorted(phantom.items(), key=lambda kv: -kv[1]))
        print(f"⚠️  {total} commands filed under non-model folders — unreachable by "
              f"model-narrowed lookup: {detail}\n")

    types = [args.type] if args.type else list(TYPE_MODELS)
    for type_name in types:
        matched = report(type_name, vocab, verbose=args.verbose or args.emit)
        if args.emit:
            emit_stubs(type_name, matched)


if __name__ == "__main__":
    main()
