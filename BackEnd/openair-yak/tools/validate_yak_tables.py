"""Check the YAK command tables against their own invariants.

    python3 BackEnd/openair-yak/tools/validate_yak_tables.py           # report
    python3 BackEnd/openair-yak/tools/validate_yak_tables.py --strict  # exit 1 on any finding

Written after a multi-step edit pass silently dropped ten hand-authored commands:
the tables are large enough now that a regression is invisible in a diff, and
"3646 loaded" reads the same whether or not the right 3646 are there. Run it
against git for the one check that needs a baseline:

    git stash && python3 … --snapshot /tmp/before.json && git stash pop
    python3 … --against /tmp/before.json
"""
import argparse
import collections
import glob
import json
import os
import re
import sys

# BackEnd/openair-yak/tools/ -> repo root is three levels up.
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)
YAK = os.path.join(REPO_ROOT, "BackEnd", "openair-yak", "Yak")
VERBS = ("set", "do", "rig", "nab")
VOWELS = set("AEIOU")


def short_keyword(word):
    """`VOLTage` -> `VOLT`, `LLINe1` -> `LLIN1`, `RESISTANCE` -> `RES`.

    The trailing index has to survive: `CALCulate:LLINe1` addresses limit line 1,
    and dropping the `1` turns it into a different command.
    """
    if any(c.islower() for c in word):
        caps = "".join(c for c in word if c.isupper() or c.isdigit())
        if caps:
            return caps
    letters = "".join(c for c in word if c.isalpha())
    trailing = word[len(letters):]
    if len(letters) <= 4:
        return letters + trailing
    base = letters[:3] if letters[3].upper() in VOWELS else letters[:4]
    return base + trailing


def tables():
    for path in sorted(glob.glob(os.path.join(YAK, "*", "*", "commands.json"))):
        with open(path) as f:
            yield path, json.load(f)


def check_known_devices(findings):
    """The `commands` links in knownDevices.json must resolve and be complete.

    A dangling link reads as coverage, and a model with a table but no entry is
    unreachable by discovery however complete its vocabulary is.
    """
    known_path = os.path.join(YAK, "knownDevices.json")
    try:
        with open(known_path) as f:
            known = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        findings.append(("knownDevices", known_path, f"unreadable: {e}"))
        return
    on_disk = {}
    for path in glob.glob(os.path.join(YAK, "*", "*", "commands.json")):
        with open(path) as f:
            on_disk[json.load(f).get("model")] = \
                os.path.relpath(path, YAK).replace(os.sep, "/")
    for model, rec in known.items():
        link = rec.get("commands")
        if link and not os.path.isfile(os.path.join(YAK, link)):
            findings.append((model, "knownDevices.commands",
                             f"link points at nothing: {link}"))
        elif link and on_disk.get(model) != link:
            findings.append((model, "knownDevices.commands",
                             f"link is {link}, table is at {on_disk.get(model)}"))
        elif not link and model in on_disk:
            findings.append((model, "knownDevices.commands",
                             f"has a table ({on_disk[model]}) but no link"))
    for model, rel in on_disk.items():
        if model not in known:
            findings.append((model, rel,
                             "command table with no knownDevices entry — "
                             "discovery cannot reach it"))


def check():
    findings = []
    counts = {}

    def bad(model, where, msg):
        findings.append((model, where, msg))

    for path, t in tables():
        model = t.get("model", "?")
        if model != os.path.basename(os.path.dirname(path)):
            bad(model, path, f"declared model does not match its folder "
                             f"{os.path.basename(os.path.dirname(path))!r}")
        seen_names = {}
        per_verb_scpi = collections.defaultdict(dict)
        n = 0
        for verb in VERBS:
            for name, e in (t.get(verb) or {}).items():
                n += 1
                where = f"{verb}/{name}"
                if name in seen_names:
                    bad(model, where, f"name also used in {seen_names[name]!r} — "
                                      f"repository.rs keeps the first and warns")
                seen_names[name] = verb

                scpi = e.get("scpi")
                if not isinstance(scpi, str) or not scpi.strip():
                    bad(model, where, "no scpi")
                    continue
                # `INST:NSEL <chan>;OUTP ON` — the node is every statement, not
                # the first. Cutting at the first space made every Power command
                # that selects a slot look like the same command.
                head = ";".join(re.split(r"[\s,]", st.strip(), 1)[0]
                                for st in scpi.split(";"))
                if head in per_verb_scpi[verb]:
                    bad(model, where, f"same SCPI node as "
                                      f"{per_verb_scpi[verb][head]!r} — one is an alias")
                per_verb_scpi[verb][head] = name

                if not (e.get("description") or "").strip():
                    bad(model, where, "no description")

                # A verb must match the shape of its template.
                q = "?" in scpi
                if verb == "nab" and not q:
                    bad(model, where, "in nab but asks nothing")
                if verb != "nab" and q:
                    bad(model, where, "carries a '?' but is not in nab")

                r = e.get("returns")
                if verb == "nab":
                    if not isinstance(r, dict):
                        bad(model, where, "nab with no returns block")
                    else:
                        want = scpi.count("?")
                        if r.get("count") != want:
                            bad(model, where, f"returns.count is {r.get('count')}, "
                                              f"but the template asks {want} question(s)")
                        if r.get("count", 0) > 1 and len(r.get("fields") or []) != want:
                            bad(model, where, "chained query without one field per answer")
                elif r is not None:
                    bad(model, where, f"{verb} should not carry a returns block")

                if verb in ("set", "rig"):
                    a = e.get("arg")
                    if not isinstance(a, dict):
                        bad(model, where, "set/rig with no arg block")
                    else:
                        if a.get("kind") == "enum" and not a.get("values"):
                            bad(model, where, "enum with no choice list — "
                                              "nothing can generate a legal value")
                        lo, hi = a.get("min"), a.get("max")
                        if lo is not None and hi is not None and lo >= hi:
                            bad(model, where, f"min {lo} is not below max {hi}")

                fast = e.get("scpiFast")
                if fast is not None:
                    if fast == scpi:
                        bad(model, where, "scpiFast repeats scpi — drop the field")
                    # Per STATEMENT: a chained template holds several, and
                    # checking only the first compared statement 1 against the
                    # whole chain.
                    for st in fast.split(";"):
                        got = re.split(r"[\s,]", st.strip(), 1)[0].lstrip(":")
                        expected = ":".join(
                            p if (not p or "<" in p) else short_keyword(p)
                            for p in got.split(":"))
                        if expected.rstrip("?") != got.rstrip("?"):
                            bad(model, where,
                                "scpiFast is not the short form of its keywords")
                            break
        counts[model] = n
    check_known_devices(findings)
    return findings, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--snapshot", metavar="FILE",
                    help="write {model: command count} and exit")
    ap.add_argument("--against", metavar="FILE",
                    help="fail if any model lost commands since that snapshot")
    args = ap.parse_args()

    findings, counts = check()

    if args.snapshot:
        with open(args.snapshot, "w") as f:
            json.dump(counts, f, indent=1)
        print(f"snapshot: {sum(counts.values())} commands across {len(counts)} models")
        return 0

    if args.against:
        before = json.load(open(args.against))
        lost = {m: (before[m], counts.get(m, 0)) for m in before
                if counts.get(m, 0) < before[m]}
        for m, (b, a) in sorted(lost.items()):
            print(f"❌ {m}: {b} -> {a} commands ({b - a} lost)")
        if lost:
            return 1
        print(f"no model lost commands ({sum(counts.values())} total)")

    by_model = collections.Counter(m for m, _w, _msg in findings)
    kinds = collections.Counter(msg.split(" —")[0].split(",")[0] for _m, _w, msg in findings)
    print(f"{sum(counts.values())} commands across {len(counts)} models, "
          f"{len(findings)} finding(s)")
    if findings:
        print("\nby kind:")
        for k, c in kinds.most_common():
            print(f"   {c:>5}  {k}")
        print("\nby model:", dict(by_model.most_common()))
        print("\nfirst 25:")
        for m, w, msg in findings[:25]:
            print(f"   {m:<10} {w:<44} {msg}")
    return 1 if (findings and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
