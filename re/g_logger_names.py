# -*- coding: utf-8 -*-
"""Every call to the logger at 0x64AEA0, with the string the caller passes it.

Usage: python g_logger_names.py [--export-only]

The human observed that every call to 0x64AEA0 passes a string, and that the strings look like exported function names. If that
holds it is the largest naming channel this project has, because a function that logs its own name is an ORACLE for that name --
the same evidence that named the nine setters and the three build-metadata exports.

The check is mechanical. The logger's first argument arrives in rcx, so the caller's body immediately before the call must have
loaded it:

    lea rcx, [rip + disp]     ; the name string
    call 0x64AEA0

and the string is read out of the image at that address. This walks every caller, extracts the string for each call, and then
classifies it three ways, because the interesting question is not what the strings ARE but what they NAME:

    the string resolves to an EXPORT's rva     -> the export is named, and the name is oracle evidence
    the string has a `//` prefix                -> a diagnostic label, which this project already records elsewhere
    neither                                     -> an internal label, still a name for the function that logs it

`--export-only` prints just the first class, which is the one that moves the deliverable.
"""
import argparse
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_names as N  # noqa: E402
import lib as LIB    # noqa: E402
from lib import disasm, load_prof, rva2off  # noqa: E402

LOG = 0x64AEA0
LEA_RCX = re.compile(r"^rcx, \[rip \+ 0x([0-9a-f]+)\]$")
PRINTABLE = re.compile(rb"[\x20-\x7e]{3,}")


def image():
    return LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data


def string_at(blob, rva, limit=120):
    try:
        offset = rva2off(rva)
    except Exception:
        return None
    if offset is None or not (0 <= offset < len(blob)):
        return None
    match = PRINTABLE.match(blob[offset:offset + limit])
    return match.group(0).decode("ascii", "replace") if match else None


def main(argv):
    only_exports = "--export-only" in argv
    blob = image()
    profile = load_prof()
    logger = profile.get(LOG) or {}
    callers = [c for c in (logger.get("callers") or []) if c in profile]
    print("0x%X is called by %d functions in the profile" % (LOG, len(callers)))
    print("")

    # rva -> export name, so a logged string can be matched to the export it names
    import json
    table = json.loads(open(os.path.join(HERE, "exports_table.json"), encoding="utf-8").read())
    by_name = {}
    for entry in table:
        if entry.get("name"):
            by_name[entry["name"]] = entry

    rows = []
    for caller in callers:
        size = (profile.get(caller) or {}).get("size") or 0
        body = [i for i in disasm(caller) if i.address < caller + size]
        for index, ins in enumerate(body):
            if ins.mnemonic != "call" or "0x%x" % LOG not in ins.op_str.lower():
                continue
            # the string is loaded in the few instructions before the call
            name = None
            for back in range(index - 1, max(-1, index - 6), -1):
                m = LEA_RCX.match(body[back].op_str)
                if body[back].mnemonic == "lea" and m:
                    target = body[back].address + body[back].size + int(m.group(1), 16)
                    name = string_at(blob, target)
                    break
            rows.append((caller, ins.address, name))

    def bare(text):
        """The name without its `// ` diagnostic prefix, so `// AddPolygonPart // AddPolygonPart` matches the export."""
        out = text.strip()
        while out.startswith("//"):
            out = out[2:].strip()
        if "//" in out:
            out = out.split("//")[0].strip()
        return out

    exports = [r for r in rows if r[2] and bare(r[2]) in by_name]
    diagnostics = [r for r in rows if r[2] and r[2].startswith("//") and r not in exports]
    others = [r for r in rows if r not in exports and r not in diagnostics]

    print("%d logger calls found" % len(rows))
    print("    naming an EXPORT:        %d" % len(exports))
    print("    a `//` diagnostic label: %d" % len(diagnostics))
    print("    an internal label:       %d" % len(others))
    print("")

    if only_exports:
        print("the exports named by their own logger call -- the string is the export's name, logged by the export itself:")
        print("")
        print("%-30s %-10s %-9s %s" % ("name", "ordinals", "rva", "logged by"))
        for caller, at, name in sorted(exports, key=lambda r: r[2]):
            entry = by_name[bare(name)]
            ordinals = ",".join(str(o) for o in (entry.get("ords") or []))
            print("%-30s %-10s 0x%-7X 0x%X" % (bare(name)[:30], ordinals, entry["rva"], caller))
        return 0

    print("every logger call, with its string and what it names:")
    print("")
    for caller, at, name in sorted(rows, key=lambda r: r[2] or ""):
        kind = ("EXPORT " + name) if name and name.lstrip("/ ") in by_name else ("diag" if name and name.startswith("//") else "internal")
        print("  0x%-8X call at 0x%-8X  %-12s %s" % (caller, at, kind, (name or "(no lea rcx found)")[:60]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
