# -*- coding: utf-8 -*-
"""The function inventory: every function in the module, and how far its recovery has gone.

Usage:
    python g_inventory.py                -> the totals, by state
    python g_inventory.py --list STATE   -> the functions in one state, in work order
    python g_inventory.py --out re/INVENTORY.md

The requirement this answers is "持续从各个角度，寻找蛛丝马迹，不断推进函数，结构体，字段，变量，参数等的逆向". The obstacle to
sustained work is not a lack of leads, it is that progress is invisible: forwardedCount counts EXPORTS, the ledger counts
CLAIMS, and neither says how many of the module's functions have a name, a signature, a body, a test. So this builds the table
that does, one row per function, with the state it has reached:

    UNSEEN      nothing is known. The module has thousands.
    SEEN        its instructions have been read at least once by some tool: it appears in a closure, or it touches a named
                field, or a vtable holds it.
    NAMED       the module names it (re/name_registry.json, direct evidence only).
    CLASSED     it is a virtual method, so RTTI gives it a class and a slot (re/vtables.json).
    TYPED       its first argument's type is known, from the class it is a method of -- this is the state the width
                contradiction in re/LEDGER.md needs, and it is why the state exists.
    WRITTEN     the project has C++ for it, in lcns/.
    EQUIVALENT  a differential test runs the recovered code against the original bytes.

The states are CUMULATIVE and the table records the highest reached, so the totals are a progress bar rather than a checklist.
The point of printing them is that "which angle to work next" becomes a question about a distribution: if TYPED is small and
SEEN is large, type propagation is the bottleneck; if WRITTEN is small and NAMED is large, writing is.

This is deliberately a table of FACTS about coverage and not a quality judgement. A function can be unattempted and still be
perfectly understood by reading; it can be written and still be wrong. The counts exist so a round can see the shape of what is
left, which is the thing a conversation cannot show.
"""
import argparse
import glob
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import load_prof  # noqa: E402

STATES = ["UNSEEN", "SEEN", "NAMED", "CLASSED", "TYPED", "WRITTEN", "EQUIVALENT"]
RANK = {state: index for index, state in enumerate(STATES)}


def names():
    path = os.path.join(HERE, "name_registry.json")
    if not os.path.exists(path):
        return {}
    data = json.load(io.open(path, encoding="utf-8"))
    out = {}
    for key, value in data.items():
        direct = [v for v in (value.get("via") or []) if not v.startswith("via ")]
        if value.get("methods") and direct:
            out[int(key, 16)] = value["methods"][0]
    return out


def classes():
    """slot rva -> (class rva, decoded class name, slot position)."""
    path = os.path.join(HERE, "vtables.json")
    if not os.path.exists(path):
        return {}
    data = json.load(io.open(path, encoding="utf-8"))
    out = {}
    for mangled, info in data.items():
        if any(marker in mangled for marker in ("8CryptoPP", "NSt", "5boost", "6Json", "__cxxabiv1", "__gnu_cxx")):
            continue
        parts = []
        for match in re.finditer(r"(\d+)([A-Za-z0-9_]+)", mangled.lstrip("_Z").lstrip("N").rstrip("E")):
            word = match.group(2)[:int(match.group(1))]
            if not word.startswith("__cxx"):
                parts.append(word)
        name = "::".join(parts) or mangled
        for position, slot in enumerate(info.get("slots") or []):
            if slot:
                out.setdefault(slot, (info.get("vtable_rva") or 0, name, position))
    return out


def written():
    """Functions the project has C++ for, by the RE address its comments carry."""
    out = set()
    for pattern in ("lcns/src/*.cpp", "lcns/include/lcns/*.hpp", "lcns/include/lcns/**/*.hpp", "lcns/tests/*.cpp"):
        for path in glob.glob(os.path.join(ROOT, pattern), recursive=True):
            text = io.open(path, encoding="utf-8", errors="replace").read()
            for match in re.finditer(r"RE\s*0x([0-9A-Fa-f]{2,7})", text):
                address = int(match.group(1), 16)
                if address >= 0x1000:
                    out.add(address)
    return out


def exported():
    """The RVAs of the exported entry points, which are the module's surface."""
    table = os.path.join(HERE, "exports_table.json")
    if not os.path.exists(table):
        return set()
    data = json.loads(io.open(table, encoding="utf-8").read())
    return {entry["rva"] for entry in data if entry.get("rva")}


def state_of(address, profile, named, classed, recovered, exports):
    if address in exports:
        best = "SEEN"
    elif address in profile:
        best = "SEEN"
    else:
        best = "UNSEEN"
    if address in named:
        best = "NAMED"
    if address in classed:
        best = "CLASSED"
        # TYPED: a method's first argument is the class the vtable names
        best = "TYPED"
    if address in recovered:
        best = "WRITTEN"
    return best


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", default=None, choices=STATES)
    parser.add_argument("--out", default=None)
    parser.add_argument("--top", type=int, default=25)
    args = parser.parse_args(argv)

    profile = load_prof()
    named = names()
    classed = classes()
    recovered = written()
    exports = exported()

    rows = []
    for address in sorted(profile):
        size = (profile.get(address) or {}).get("size") or 0
        if size <= 0:
            continue
        state = state_of(address, profile, named, classed, recovered, exports)
        rows.append({
            "rva": address,
            "size": size,
            "state": state,
            "name": named.get(address, ""),
            "class": classed.get(address, (0, "", 0))[1],
            "slot": classed.get(address, (0, "", 0))[2],
            "export": address in exports,
        })
    totals = Counter(row["state"] for row in rows)

    print("functions with a size in the profile: %d" % len(rows))
    print("")
    for state in STATES:
        print("    %-11s %6d" % (state, totals.get(state, 0)))
    print("")
    unnamed = sum(1 for row in rows if not row["name"])
    print("named by the module:      %5d of %d" % (len(rows) - unnamed, len(rows)))
    print("with a class from RTTI:   %5d" % sum(1 for row in rows if row["class"]))
    print("with C++ in the project:  %5d" % totals.get("WRITTEN", 0))
    print("")

    if args.list:
        selected = [row for row in rows if row["state"] == args.list]
        selected.sort(key=lambda row: -row["size"])
        print("the %d %s functions, largest first:" % (len(selected), args.list))
        print("")
        for row in selected[:args.top]:
            print("    0x%-8X %7d B  %-28s %s" % (row["rva"], row["size"], row["name"][:28],
                                                   ("%s slot %d" % (row["class"], row["slot"])) if row["class"] else ""))

    if args.out:
        lines = ["# The function inventory",
                 "",
                 "Generated by `re/g_inventory.py`. One row per function, with the highest recovery state it has reached.",
                 "The states are cumulative: UNSEEN, SEEN, NAMED, CLASSED, TYPED, WRITTEN, EQUIVALENT.",
                 "",
                 "| state | functions |",
                 "|---|---:|"]
        for state in STATES:
            lines.append("| %s | %d |" % (state, totals.get(state, 0)))
        lines.append("| **total** | **%d** |" % len(rows))
        lines.append("")
        lines.append("## The named functions")
        lines.append("")
        lines.append("| rva | bytes | name | class |")
        lines.append("|---|---:|---|---|")
        for row in rows:
            if not row["name"]:
                continue
            lines.append("| `0x%X` | %d | `%s` | %s |"
                         % (row["rva"], row["size"], row["name"],
                            ("`%s` slot %d" % (row["class"], row["slot"])) if row["class"] else ""))
        io.open(os.path.join(ROOT, args.out.replace("/", os.sep)), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
        print("")
        print("wrote %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
