#!/usr/bin/env python3
"""Restructure labels in Gui_Frames: label_active / label_inactive become a single
`label` parent with `active` / `inactive` children. Applies at every level
(elements AND options). Idempotent.

Collision handling when a plain `label` co-exists:
  - no label_active           -> plain becomes label.active
  - plain == label_active     -> plain is redundant, dropped
  - plain != label_active     -> plain preserved as label.text (distinct title)

Run with --apply to write; default is a dry-run report.
"""
import json, glob, sys
from collections import OrderedDict, Counter

APPLY = "--apply" in sys.argv
stats = Counter()
touched = []

def is_pair(v):
    return isinstance(v, dict) and ("active" in v or "inactive" in v)

def build_label(o):
    """Return a new OrderedDict for `label`, or None if nothing to migrate."""
    if "label_active" not in o and "label_inactive" not in o:
        return None
    la = o.get("label_active")
    li = o.get("label_inactive")
    plain = o.get("label") if not is_pair(o.get("label")) else None
    plain_present = "label" in o and not is_pair(o.get("label"))

    label = OrderedDict()
    # text (distinct group title) only when plain differs from the active label
    if plain_present and la is not None and plain != la:
        label["text"] = plain
        stats["preserved_text"] += 1
    active = la if la is not None else (plain if plain_present else None)
    inactive = li if li is not None else None
    if active is not None:
        label["active"] = active
    if inactive is not None:
        label["inactive"] = inactive
    return label

def migrate_obj(o):
    label = build_label(o)
    if label is None:
        return o
    out = OrderedDict()
    placed = False
    for k, v in o.items():
        if k in ("label_active", "label_inactive"):
            if not placed:
                out["label"] = label; placed = True
            continue
        if k == "label":
            # replaced by the consolidated label parent (plain folded in already)
            if not placed:
                out["label"] = label; placed = True
            continue
        out[k] = v
    stats["nodes_migrated"] += 1
    return out

def walk(o):
    if isinstance(o, dict):
        o = migrate_obj(o)
        return OrderedDict((k, walk(v)) for k, v in o.items())
    if isinstance(o, list):
        return [walk(v) for v in o]
    return o

files = [f for f in glob.glob("Gui_Frames/**/*.json", recursive=True) if not f.endswith(".old")]
for f in files:
    try:
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh, object_pairs_hook=OrderedDict)
    except Exception as e:
        print("PARSE FAIL", f, e); continue
    before = json.dumps(data, ensure_ascii=False, sort_keys=True)
    new = walk(data)
    after = json.dumps(new, ensure_ascii=False, sort_keys=True)
    if before != after:
        touched.append(f)
        if APPLY:
            with open(f, "w", encoding="utf-8") as fh:
                json.dump(new, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

print("MODE:", "APPLY" if APPLY else "DRY-RUN")
print("files scanned:", len(files))
print("files changed:", len(touched))
print("nodes migrated:", stats["nodes_migrated"])
print("distinct titles preserved as label.text:", stats["preserved_text"])
