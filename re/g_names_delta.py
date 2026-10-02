# -*- coding: utf-8 -*-
"""How much of re/NAMES.md is new: which recovered functions are not cited anywhere yet.

Usage: python g_names_delta.py
"""
import glob
import io
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"


def main():
    names = io.open(os.path.join(ROOT, "re", "NAMES.md"), encoding="utf-8").read()
    pattern = re.compile(r"^\| `([^`]+)` \| `(0x[0-9A-F]+)`", re.M)
    pairs = pattern.findall(names)
    funcs = {}
    for method, addr in pairs:
        funcs.setdefault(int(addr, 16), set()).add(method)
    print("recovered method names: %d, for %d distinct functions" % (len(pairs), len(funcs)))

    skip = {"NAMES.md", "ASSERTIONS.md"}
    cited = set()
    files = glob.glob(os.path.join(ROOT, "re", "*.md")) + glob.glob(os.path.join(ROOT, "re", "*.py"))
    for root, _d, fs in os.walk(os.path.join(ROOT, "lcns")):
        if os.sep + "build" in root:
            continue
        for f in fs:
            if f.endswith((".cpp", ".hpp", ".md")):
                files.append(os.path.join(root, f))
    for fp in files:
        if os.path.basename(fp) in skip:
            continue
        try:
            text = io.open(fp, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for m in re.finditer(r"0x([0-9A-Fa-f]{3,8})", text):
            cited.add(int(m.group(1), 16))

    new = sorted(a for a in funcs if a not in cited)
    print("of those, not cited anywhere in re/ or lcns/ yet: %d" % len(new))
    by_file = {}
    for a in new[:40]:
        by_file[a] = sorted(funcs[a])[0]
    for a in sorted(by_file):
        print("    0x%-8X %s" % (a, ", ".join(sorted(funcs[a]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
