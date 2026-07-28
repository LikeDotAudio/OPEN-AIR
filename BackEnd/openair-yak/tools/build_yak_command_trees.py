"""Regenerate a `commands_tree.md` beside every `commands.json`.

One file per model, showing the SCPI vocabulary as the tree it actually is —
mnemonic by mnemonic, with the verb, arguments and reply shape on each leaf. The
tables are dicts of flat command names, which is what the runtime wants and the
wrong shape for a human deciding what a panel can address; this is the other view.

The generated part lives between markers. Anything already in the file is
preserved BELOW them, because the trees that exist were written by hand and carry
domain knowledge no generator can reproduce — that the 6060B is a power supply
running backwards, that a 66000A module is unreachable until you select its slot.
Regenerating replaces the block and leaves that prose alone.

    python3 BackEnd/openair-yak/tools/build_yak_command_trees.py           # rewrite every tree
    python3 BackEnd/openair-yak/tools/build_yak_command_trees.py --check    # exit 1 if stale
"""
import argparse
import glob
import json
import os
import re
import sys

# BackEnd/openair-yak/tools/ -> repo root is three levels up.
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)
YAK_ROOT = os.path.join(REPO_ROOT, "BackEnd", "openair-yak", "Yak")

BEGIN = "<!-- BEGIN GENERATED — BackEnd/openair-yak/tools/build_yak_command_trees.py -->"
# Trees generated before this tool moved out of Deployment/ carry the old
# marker. Recognised so a regeneration REPLACES that block, instead of failing
# to find it and burying the whole stale tree under "Notes carried over".
LEGACY_BEGIN = "<!-- BEGIN GENERATED — BackEnd/openair-yak/tools/build_yak_command_trees.py -->"
END = "<!-- END GENERATED -->"
CARRIED = "## Notes carried over"

VERBS = ("set", "rig", "nab", "do")
PLACEHOLDER = re.compile(r"<(\w+)>")


def split_header(statement):
    """`:SENSe:VOLTage:DC:RANGe <range>` -> (['SENSe','VOLTage','DC','RANGe'], '<range>').

    The header is everything up to the first space; whatever follows is the
    parameter, which may be a placeholder (`<range>`) or a literal the table
    baked in (`OFF`). Both are worth showing — a literal is why `Auto_Zero_OFF`
    and `Auto_Zero_ON` are two commands rather than one SET.
    """
    statement = statement.strip()
    head, _, param = statement.partition(" ")
    return [m for m in head.lstrip(":").split(":") if m], param.strip()


def annotate(name, verb, cmd, statement_param):
    """The one-line summary that hangs off a leaf."""
    bits = [f"**{verb.upper()}** `{name}`"]
    if statement_param:
        bits.append(f"`{statement_param}`")
    args = cmd.get("args") or []
    if args:
        bits.append("args: " + ", ".join(f"`{a}`" for a in args))
    # `arg` types the value the operator supplies — a bool is a toggle, an enum
    # is a selector and its `values` ARE the options, a numeric wants a domain.
    arg = cmd.get("arg") or {}
    if arg.get("values"):
        bits.append(f"{arg.get('kind', 'enum')}: "
                    + " | ".join(f"`{v}`" for v in arg["values"]))
    elif arg.get("kind") and arg["kind"] != "unknown":
        unit = arg.get("unit")
        bits.append(arg["kind"] + (f" ({unit})" if unit else ""))
    # Placeholders the operator does not supply are stamped per panel.
    stamped = [p for p in dict.fromkeys(PLACEHOLDER.findall(cmd.get("scpi", "")))
               if p not in args]
    if stamped:
        bits.append("per-instance: " + ", ".join(f"`{p}`" for p in stamped))
    returns = cmd.get("returns") or {}
    if returns:
        fields = returns.get("fields")
        if fields:
            bits.append("→ " + ", ".join(f.get("name", "?") for f in fields))
        else:
            rt = " ".join(x for x in (returns.get("type"), returns.get("unit")) if x)
            bits.append("→ " + (rt or f"{returns.get('count', 1)} value"))
    if cmd.get("unverified"):
        bits.append("†")
    line = " · ".join(bits)
    desc = (cmd.get("description") or "").strip()
    # The sweep gave whole subsystems the same description; it is noise once the
    # command name says the same thing.
    if desc and desc.lower().replace(" ", "_") != name.lower():
        line += f"<br>{desc}"
    return line


def build_tree(table):
    """Nest every single-statement command under its mnemonics.

    Returns (tree, common, compound). `common` holds the `*IDN?` family, which
    has no path to nest under. `compound` holds multi-statement commands, which
    belong to no single branch — a NAB spanning three subsystems is exactly the
    thing a tree cannot draw.
    """
    tree = {}
    common = []
    compound = []
    for verb in VERBS:
        for name, cmd in sorted((table.get(verb) or {}).items()):
            scpi = cmd.get("scpi", "")
            statements = [s for s in scpi.split(";") if s.strip()]
            if len(statements) > 1:
                compound.append((name, verb, cmd))
                continue
            path, param = split_header(scpi)
            if not path:
                continue
            if path[0].startswith("*"):
                common.append((name, verb, cmd, param))
                continue
            node = tree
            for mnemonic in path[:-1]:
                node = node.setdefault(mnemonic, {})
            node.setdefault("\0leaves", []).append((path[-1], name, verb, cmd, param))
    return tree, common, compound


def render_tree(node, depth=0):
    out = []
    pad = "  " * depth
    for leaf, name, verb, cmd, param in node.get("\0leaves", []):
        out.append(f"{pad}- `{leaf}` — {annotate(name, verb, cmd, param)}")
    for mnemonic in sorted(k for k in node if k != "\0leaves"):
        out.append(f"{pad}- **`{mnemonic}`**")
        out.extend(render_tree(node[mnemonic], depth + 1))
    return out


def family_notes(rel, model):
    """`<Family>/commands_tree.md` — prose written for a family, not a model.

    Linked only when it actually names the model it would be claiming to
    describe. `LCR/commands_tree.md` is byte-identical to `Load/commands_tree.md`
    and explains the 6060B electronic load, so the 4263A gets no link and the
    mis-file stays visible instead of being papered over by a pointer.
    """
    path = os.path.join(YAK_ROOT, rel.split("/")[0], "commands_tree.md")
    if not os.path.exists(path):
        return None
    text = open(path).read()
    # Prose about a module family names it once and wildcards the rest — the
    # Power notes cover 66103A as "6610xA" and never spell it out.
    wildcards = {model[:i] + "x" + model[i + 1:] for i in range(len(model))}
    if model in text or any(w in text for w in wildcards):
        return "../commands_tree.md"
    return None


def render(rel, table):
    family = table.get("family", rel.split("/")[0])
    model = table.get("model", rel.split("/")[1])
    counts = {v: len(table.get(v) or {}) for v in VERBS}
    total = sum(counts.values())
    unverified = sum(1 for v in VERBS for c in (table.get(v) or {}).values()
                     if c.get("unverified"))

    tree, common, compound = build_tree(table)

    out = [BEGIN, "",
           f"# {family}/{model} — command tree", "",
           f"Generated from `commands.json` by "
           f"`BackEnd/openair-yak/tools/build_yak_command_trees.py`. Edit the table, not this file.", "",
           f"**{total} commands** — SET {counts['set']} · RIG {counts['rig']} · "
           f"NAB {counts['nab']} · DO {counts['do']}"
           + (f" · {unverified} unverified ({unverified * 100 // total}%)"
              if total else ""), "",
           "`SET` one argument · `RIG` several applied together · `NAB` a query · "
           "`DO` a parameterless action. **†** marks a command swept out of a manual "
           "and never sent to the instrument.", ""]

    notes = family_notes(rel, model)
    if notes:
        out += [f"Written notes for this family: [`{family}/commands_tree.md`]({notes}).",
                ""]

    if compound:
        out += ["## Compound commands", "",
                "Several statements in one message, so they hang off no single "
                "branch. Every statement after the first carries a leading colon — "
                "without it the parser reads it relative to the previous header's "
                "path and the instrument answers `-113`.", ""]
        for name, verb, cmd in sorted(compound):
            out.append(f"- {annotate(name, verb, cmd, '')}")
            out.append(f"  - `{cmd.get('scpi', '')}`")
        out.append("")

    if tree:
        out += ["## Tree", ""] + render_tree(tree) + [""]

    if common:
        out += ["## Common commands (IEEE 488.2)", ""]
        for name, verb, cmd, param in sorted(common):
            out.append(f"- `{cmd.get('scpi', '')}` — {annotate(name, verb, cmd, param)}")
        out.append("")

    out.append(END)
    return "\n".join(out)


def merge(path, block):
    """Generated block on top, hand-written content preserved underneath."""
    if not os.path.exists(path):
        return block + "\n"
    existing = open(path).read()
    for marker in (BEGIN, LEGACY_BEGIN):
        if marker in existing and END in existing:
            head, _, rest = existing.partition(marker)
            _, _, tail = rest.partition(END)
            return head + block + tail
    # First run against a hand-written tree: keep every word of it.
    return f"{block}\n\n---\n\n{CARRIED}\n\n{existing.lstrip()}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="report drift without writing; exit 1 if stale")
    args = ap.parse_args()

    stale = []
    for table_path in sorted(glob.glob(os.path.join(YAK_ROOT, "*", "*", "commands.json"))):
        rel = os.path.relpath(table_path, YAK_ROOT).replace(os.sep, "/")
        with open(table_path) as f:
            table = json.load(f)
        tree_path = os.path.join(os.path.dirname(table_path), "commands_tree.md")
        merged = merge(tree_path, render(rel, table))
        current = open(tree_path).read() if os.path.exists(tree_path) else None
        if current == merged:
            continue
        stale.append(os.path.relpath(tree_path, REPO_ROOT))
        if not args.check:
            with open(tree_path, "w") as f:
                f.write(merged)

    if args.check:
        if stale:
            print(f"   ❌ {len(stale)} command trees are stale:")
            for s in stale:
                print(f"      {s}")
            return 1
        print("   ✅ every command tree is current")
        return 0

    if stale:
        print(f"   ✅ wrote {len(stale)} command trees")
        for s in stale:
            print(f"      {s}")
    else:
        print("   ✅ every command tree was already current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
