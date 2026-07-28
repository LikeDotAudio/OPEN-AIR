"""Point each known device at its command table, where one exists.

    python3 Deployment/build_known_device_links.py           # rewrite the links
    python3 Deployment/build_known_device_links.py --check    # exit 1 if stale

`Yak/knownDevices.json` says what an instrument IS — `*IDN?` gives a model, this
gives back a manufacturer, a type and a note. What it could not say is whether
YAK knows how to TALK to it, which is the next question anyone reading the file
has. So an entry with a table gains a path to it:

    "34401A": { "manufacturer": …, "type": "DMM", "notes": …,
                "commands": "DMM/34401A/commands.json" }

Paths are relative to the `Yak/` directory the file lives in, so the pair moves
together and neither has to know where the repo is checked out.

Generated, not maintained. A hand-kept index of 181 entries against a tree that
gains tables one instrument at a time is a list that is wrong by the second
commit — `--check` in a hook is the difference between a stale link and a lie.
Only the 16 populated models get the key; a `model.json`-only folder gets none,
because every one of the 181 has a `model.json` and a field that is always
present tells the reader nothing.
"""
import argparse
import glob
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YAK = os.path.join(REPO_ROOT, "BackEnd", "openair-yak", "Yak")
KNOWN = os.path.join(YAK, "knownDevices.json")
FIELD_ORDER = ("manufacturer", "type", "notes", "commands")


def tables_on_disk():
    """{model: path relative to Yak/} for every commands.json that exists.

    Keyed by the table's DECLARED model, not its folder name, so a folder renamed
    without its contents (or the other way round) shows up as a mismatch instead
    of silently linking the wrong instrument.
    """
    found = {}
    for path in sorted(glob.glob(os.path.join(YAK, "*", "*", "commands.json"))):
        rel = os.path.relpath(path, YAK)
        try:
            with open(path) as f:
                declared = json.load(f).get("model")
        except (OSError, json.JSONDecodeError) as e:
            print(f"   ⚠️  unreadable {rel}: {e}")
            continue
        folder = os.path.basename(os.path.dirname(path))
        if declared and declared != folder:
            print(f"   ⚠️  {rel} declares model {declared!r} but sits in {folder!r}")
        found[declared or folder] = rel.replace(os.sep, "/")
    return found


def rebuild():
    with open(KNOWN) as f:
        known = json.load(f)
    tables = tables_on_disk()

    linked, dropped, orphans = [], [], []
    for model, rec in known.items():
        rel = tables.get(model)
        if rel:
            if rec.get("commands") != rel:
                linked.append(model)
            rec["commands"] = rel
        elif "commands" in rec:
            # The table went away, or was never there. A link to nothing is worse
            # than no link: it reads as coverage.
            del rec["commands"]
            dropped.append(model)
        known[model] = {k: rec[k] for k in FIELD_ORDER if k in rec}

    for model in tables:
        if model not in known:
            orphans.append(model)

    return known, tables, linked, dropped, orphans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the file on disk is not what this would write")
    args = ap.parse_args()

    known, tables, linked, dropped, orphans = rebuild()
    rendered = json.dumps(dict(sorted(known.items())), indent=2, ensure_ascii=False) + "\n"

    if orphans:
        # A table nothing can be discovered into: the VISA scan yields a model
        # string, and a model absent from knownDevices answers "Unknown
        # Instrument" no matter how complete its vocabulary is.
        print(f"   ⚠️  {len(orphans)} command table(s) with no knownDevices entry — "
              f"unreachable by discovery: {', '.join(sorted(orphans))}")

    with open(KNOWN) as f:
        current = f.read()

    if args.check:
        if current != rendered:
            print(f"❌ knownDevices.json is stale — "
                  f"{len(linked)} link(s) to add, {len(dropped)} to drop")
            return 1
        print(f"✅ knownDevices.json is current "
              f"({sum(1 for r in known.values() if 'commands' in r)} of {len(known)} linked)")
        return 1 if orphans else 0

    with open(KNOWN, "w") as f:
        f.write(rendered)
    have = sum(1 for r in known.values() if "commands" in r)
    print(f"   ✅ {len(known)} known devices, {have} linked to a command table")
    if linked:
        print(f"      + {', '.join(sorted(linked))}")
    if dropped:
        print(f"      - dropped a dead link on {', '.join(sorted(dropped))}")
    return 1 if orphans else 0


if __name__ == "__main__":
    sys.exit(main())
