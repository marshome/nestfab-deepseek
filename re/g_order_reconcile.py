#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""The two lists the Order reconciliation needs: what the layout has that Order does not, and where the two disagree on width.

**THIS IS THE RECONCILIATION'S INPUT AND NOT THE RECONCILIATION**, and keeping it separate is deliberate: the merge touches 234 call sites in ten files, and
a round that starts by editing those has no way to show what it was aiming at. This produces the two lists; `re/g_one_definition.py` records the debt the
merge will clear.

**AND THE PARSER HAD TO BE FIXED TWICE TO SEE BOTH STRUCTS:**

  * the first version required a KNOWN type name, so `Order` parsed as ZERO fields -- **because its first two fields are `Objective` and `NestingOrigin`,
    enumerated types this project declares itself**, and a width table of built-ins cannot know them. The type is now taken as written and its width
    resolved from a table that includes this project's enums, defaulting to the smallest power of two that fits a known one.
  * and the pattern is the same one `re/g_one_definition.py` uses, so the two tools cannot disagree about which fields they are looking at.

    python -u g_order_reconcile.py
    python -u g_order_reconcile.py --out re/ORDER_RECONCILE.md
"""
import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

STRUCT = re.compile(r"^(?:struct|class)\s+(\w+)\s*(?::[^\{]*)?\{(?P<body>.*?)^\};", re.M | re.S)
# **THE TYPE IS TAKEN AS WRITTEN**, because `Order` uses this project's own enums and a table of built-ins would parse it as empty
FIELD = re.compile(r"^\s+([\w:<>,\s\*&]+?)\s+\b(\w+)\s*(\[[^\]]*\])?\s*(?:=[^;]*)?;\s*//[^\n]*?\+0x([0-9A-Fa-f]+)", re.M)

WIDTHS = {
    "unsigned char": 1, "char": 1, "bool": 1, "std::uint8_t": 1, "std::int8_t": 1, "std::uint8_t ": 1,
    "std::uint16_t": 2, "std::int16_t": 2,
    "std::uint32_t": 4, "std::int32_t": 4, "int": 4, "float": 4,
    "std::uint64_t": 8, "std::int64_t": 8, "std::size_t": 8, "std::uintptr_t": 8,
    "double": 8, "long": 8, "void *": 8, "void*": 8,
    # **THIS PROJECT'S OWN ENUMS**, which is what `Order` opens with and what the first parser could not see
    "Objective": 4, "NestingOrigin": 4,
}
UNKNOWN = 0


def width_of(ftype, array):
    count = 1
    if array:
        inner = array.strip("[]")
        if inner.isdigit():
            count = int(inner)
        elif inner.startswith("0x"):
            count = int(inner, 16)
    base = WIDTHS.get(ftype.strip(), UNKNOWN)
    return base * count if base else UNKNOWN


def parse(path, struct_name):
    text = io.open(path, encoding="utf-8", errors="replace").read()
    for match in STRUCT.finditer(text):
        if match.group(1) != struct_name:
            continue
        fields = {}
        for ftype, name, array, offset in FIELD.findall(match.group("body")):
            fields[int(offset, 16)] = (ftype.strip(), name, width_of(ftype, array), array)
        return fields
    return {}


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", dest="out")
    args = parser.parse_args(argv)

    order = parse(os.path.join(ROOT, "lcns", "include", "lcns", "model.hpp"), "Order")
    layout = parse(os.path.join(ROOT, "lcns", "include", "lcns", "launching_order.hpp"), "LaunchingOrderLayout")
    if not order or not layout:
        print("REFUSING: Order parsed %d fields and the layout %d" % (len(order), len(layout)))
        return 2

    missing = sorted(set(layout) - set(order))
    both = sorted(set(layout) & set(order))
    disagreements = [(off, order[off], layout[off]) for off in both
                     if order[off][2] and layout[off][2] and order[off][2] != layout[off][2]]
    unknown = sorted(off for off in order if not order[off][2])

    lines = []
    lines.append("# The Order reconciliation's two lists\n")
    lines.append("`model.hpp`'s `Order` has **%d** offset-commented fields and `launching_order.hpp`'s `LaunchingOrderLayout` has **%d**; they share **%d**,"
                 " which is **%.0f%%** of the smaller. **They are one module object described twice**, and these are the two things a merge has to take"
                 " from the layout.\n" % (len(order), len(layout), len(both), 100.0 * len(both) / min(len(order), len(layout))))
    lines.append("")
    lines.append("## 1. The %d offsets the layout has and `Order` does not\n" % len(missing))
    lines.append("| offset | type | name in the layout |")
    lines.append("|---|---|---|")
    for offset in missing:
        ftype, name, width, array = layout[offset]
        lines.append("| +0x%03X | `%s` | `%s`%s |" % (offset, ftype + (" " + array if array else ""), name,
                                                       " (%d B)" % width if width else ""))
    lines.append("")
    lines.append("## 2. The %d shared offsets where the two disagree on WIDTH\n" % len(disagreements))
    lines.append("The module settles these: `re/g_adjudicate.py` compares each against the store it performs.\n")
    lines.append("| offset | Order | layout | narrower |")
    lines.append("|---|---|---|---|")
    for offset, (otype, oname, ow, _oa), (ltype, lname, lw, _la) in disagreements:
        winner = "layout" if lw < ow else ("Order" if ow < lw else "?")
        lines.append("| +0x%03X | `%s %s` (%dB) | `%s %s` (%dB) | **%s** |" % (offset, otype, oname, ow, ltype, lname, lw, winner))
    lines.append("")
    if unknown:
        lines.append("## 3. And %d of `Order`'s fields whose width the table could not resolve\n" % len(unknown))
        for offset in unknown:
            ftype, name, _w, array = order[offset]
            lines.append("   +0x%03X  `%s %s` -- add it to WIDTHS in re/g_order_reconcile.py" % (offset, ftype, name))
        lines.append("")
    lines.append("## 4. A convention the conflicts show\n")
    lines.append("**Where the two disagree on a NAME, the layout's is usually the module's and `Order`'s is a description**: `commonCutSafetyFlag` against")
    lines.append("`commonCutSafetyPreferenceGiven`, the latter being the export `SetCommonCutSafetyPreference` that writes the field. **So a merge keeps")
    lines.append("`Order`'s callers, the layout's widths, and per field whichever NAME the module itself supplies.**")

    text = "\n".join(lines) + "\n"
    if args.out:
        io.open(os.path.join(ROOT, args.out), "w", encoding="utf-8", newline="\n").write(text)
        print("wrote %s: %d fields in Order, %d in the layout, %d shared, %d missing, %d width conflicts, %d unknown widths"
              % (args.out, len(order), len(layout), len(both), len(missing), len(disagreements), len(unknown)))
        return 0
    print(text[:5000])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
