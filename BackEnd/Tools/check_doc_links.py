#!/usr/bin/env python3
"""Fail if any Markdown file links to something that does not exist.

Milestone 1 was credited "all internal links programmatically verified to
resolve." That check ran once, by hand, over README.md — and five links were
dead by the next day: two pointed at `Documents/Audits/2_Architecture_Diagrams.md`
when the file lives in `Documents/notes/`, and three broke when the executive
reviews moved into their own folder. A claim that is only true on the day it is
made is not a check. This is the check.

Usage:
    python3 BackEnd/Tools/check_doc_links.py          # whole repo
    python3 BackEnd/Tools/check_doc_links.py Documents  # a subtree

Exits 1 with a report if anything is dead. Stdlib only, no third-party deps.
"""

from __future__ import annotations

import re
import sys
import urllib.parse
from pathlib import Path

# Directories that are not ours to police.
SKIP_DIRS = {
    ".git", "node_modules", ".crawler", "target", "dist", "build",
    "venv", ".venv", "__pycache__", ".pytest_cache", "site-packages",
}

# Vendored third-party sources. Their docs ship with dead links we did not
# write and will not maintain; linting them would make the gate permanently
# red and train everyone to ignore it. Matched against any path component.
VENDORED = (
    "nmos-cpp-master",
    "nmos-testing-tool-master",
    "nmos-device-control-mock-main-master",
    "nmos-control-rusty-device-master",
)

# [text](target) — captures the target, minus any #fragment.
LINK_RE = re.compile(r"\[[^\]]*\]\(\s*([^)\s]+?)(?:\s+\"[^\"]*\")?\s*\)")

# Links we intentionally do not resolve on disk.
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "#", "data:")


def is_external(target: str) -> bool:
    return target.startswith(EXTERNAL_PREFIXES)


def markdown_files(root: Path):
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if any(v in path.parts for v in VENDORED):
            continue
        yield path


def check(root: Path) -> list[tuple[Path, int, str]]:
    """Return [(file, line_number, dead_target)]."""
    dead: list[tuple[Path, int, str]] = []
    for md in markdown_files(root):
        try:
            lines = md.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError as exc:              # unreadable file is itself a problem
            print(f"  ! could not read {md}: {exc}", file=sys.stderr)
            continue

        in_fence = False
        for lineno, line in enumerate(lines, 1):
            # Don't lint links inside fenced code blocks — they are examples.
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            for match in LINK_RE.finditer(line):
                target = match.group(1).split("#", 1)[0].strip()
                if not target or is_external(target):
                    continue
                # %20 and friends: links are URL-encoded, paths are not.
                decoded = urllib.parse.unquote(target)
                resolved = (md.parent / decoded).resolve()
                if not resolved.exists():
                    dead.append((md, lineno, target))
    return dead


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    if not root.exists():
        print(f"error: {root} does not exist", file=sys.stderr)
        return 2

    total = sum(1 for _ in markdown_files(root))
    dead = check(root)

    if dead:
        print(f"\n✗ {len(dead)} dead link(s) across {total} Markdown file(s):\n")
        for md, lineno, target in dead:
            try:
                shown = md.relative_to(Path.cwd())
            except ValueError:
                shown = md
            print(f"  {shown}:{lineno}  ->  {target}")
        print(
            "\nFix the path, or delete the link. If a file moved, search for "
            "other references to it before assuming this is the only one.\n"
        )
        return 1

    print(f"✓ all internal Markdown links resolve ({total} files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
