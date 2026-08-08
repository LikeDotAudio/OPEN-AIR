#!/usr/bin/env python3
"""Rewrite legacy browser-globals into ES modules, one file at a time.

`window.X = ...` is the de-facto export; `window.X` elsewhere is the import.
This builds the symbol table from the whole tree, then for the file(s) named
rewrites reads into imports and assignments into exports.

The window assignment is KEPT beside the new export on purpose: anything not yet
converted still reads the global, and removing it early breaks the file this
pass has not reached. Step 5 of the plan deletes them, once nothing reads them.
Browser/runtime globals are never touched — only symbols this tree defines.
"""
import re, os, sys, json, collections

ROOT = 'ui/src/legacy'
ASSIGN = re.compile(r'window\.([A-Za-z_$][\w$]*)\s*=(?!=)')
READ   = re.compile(r'window\.([A-Za-z_$][\w$]*)')

def files():
    for d, _, fs in os.walk(ROOT):
        for f in fs:
            if f.endswith(('.js', '.jsx')):
                yield os.path.join(d, f)

def symbol_table():
    """symbol -> defining file. A symbol defined twice is ambiguous and skipped."""
    owners = collections.defaultdict(set)
    for p in files():
        for m in ASSIGN.finditer(open(p, encoding='utf8', errors='replace').read()):
            owners[m.group(1)].add(p)
    return {s: next(iter(v)) for s, v in owners.items() if len(v) == 1}

def convert(path, table):
    src = open(path, encoding='utf8', errors='replace').read()
    mine = {m.group(1) for m in ASSIGN.finditer(src)}
    needs = {s for s in (m.group(1) for m in READ.finditer(src))
             if s in table and s not in mine and table[s] != path}

    imports = collections.defaultdict(set)
    for s in needs:
        rel = os.path.relpath(table[s], os.path.dirname(path)).replace(os.sep, '/')
        if not rel.startswith('.'):
            rel = './' + rel
        imports[rel].add(s)

    out = src
    for s in needs:                       # reads become bare identifiers
        out = re.sub(rf'window\.{re.escape(s)}\b', s, out)
    # ONLY top-level assignments become exports. An indented `window.X = …`
    # sits inside an IIFE or block, where `export` is a syntax error — that is
    # exactly what broke dsp.js:292 on the first pass. Those files keep the
    # global and are converted by hoisting the value out, which is a judgement
    # call per file, not a rewrite rule.
    exported = set()
    for s in sorted(mine):
        # Two shapes, and they need opposite treatment:
        #   const X = …; window.X = X   -> X already exists; re-declaring it is
        #                                  a duplicate-symbol error, so just
        #                                  append `export { X }`.
        #   window.X = …                -> the assignment IS the declaration, so
        #                                  it can carry the export inline.
        declared = re.search(rf'^\s*(?:const|let|var|function|class)\s+{re.escape(s)}\b', out, re.M)
        if declared:
            if not re.search(rf'^export\s*\{{[^}}]*\b{re.escape(s)}\b', out, re.M):
                out = out.rstrip('\n') + f'\n\nexport {{ {s} }}\n'
                exported.add(s)
            continue
        new, n = re.subn(rf'^window\.{re.escape(s)}\s*=(?!=)',
                         f'export const {s} = window.{s} =', out, count=1, flags=re.M)
        if n:
            out = new
            exported.add(s)

    header = ''.join(f"import {{ {', '.join(sorted(v))} }} from '{k}'\n"
                     for k, v in sorted(imports.items()))
    if header:
        out = header + '\n' + out
    open(path, 'w', encoding='utf8').write(out)
    return len(needs), len(exported)

if __name__ == '__main__':
    table = symbol_table()
    if sys.argv[1:2] == ['--table']:
        print(json.dumps({'symbols': len(table)}, indent=0))
        sys.exit(0)
    for target in sys.argv[1:]:
        r, w = convert(target, table)
        print(f"  {target}: {r} import(s), {w} export(s)")
