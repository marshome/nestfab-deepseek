#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Compare the two placed layouts field by field, so the merge is decided on evidence rather than on which name is used more.

**BOTH ARE NOW PLACED AND BOTH DESCRIBE THE MODULE'S 0x2C0 OBJECT.** `model.hpp`'s `Order` has its offset-commented fields at their offsets (55 measured, 0
disagreements), and `launching_order.hpp`'s `LaunchingOrderLayout` was built from RE 0x14620 the same way. **Two placed layouts of one object is the second
description this project forbids**, and which survives is a question about what each one KNOWS:

  * `Order` carries the names taken from the exports -- `shear`, `commonCutSafetyFlag`, `multitorchModeTag` -- and 234 call sites;
  * `LaunchingOrderLayout` carries 99 `unnamedXXX` fields, **which its own header says are offset-derived because the module never names them**, and 28 call
    sites.

**SO NEITHER IS COMPLETE AND THE MERGE IS A UNION**: every offset the layout has and `Order` does not, added to `Order` with the layout's name and width. This
prints that union and the conflicts, and says how many fields each side is missing.

    python -u g_order_union.py
    python -u g_order_union.py --out re/ORDER_UNION.md
"""
import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

STRUCT = re.compile(r"^(?:struct|class)\s+(\w+)\s*(?::[^\{]*)?\{(?P<body>.*?)^\};", re.M | re.S)
# **THE COMMENT MUST BE ON THE SAME LINE** -- a pattern whose comment part can cross a newline matches the SECTION HEADER below a field that has none, which is
# how the measurement recorded a claim `commonCutObjectiveDen` never made.
# **AND THE PADDING IS NOT A FIELD.** The permutation inserts `std::byte paddingNN[...]` members to force the next field onto its offset, and those
# declarations carry a `+0xNNN` comment -- so a field regex matches them and counts the tool's own scaffolding as the module's structure. **Thirteen of
# the "15 offsets only Order has" were padding**, and the same omission made `re/g_one_definition.py` report 68 shared offsets where this tool reports
# 67. A member whose type is `std::byte`, whose name begins with `padding` and whose width is zero is not a field.
NOT_A_FIELD = re.compile(r"^padding\d*$")
FIELD = re.compile(r"^\s+([\w:<>,\s\*&]+?)\s+\b(\w+)\s*(\[[^\]]*\])?\s*(?:=[^;]*)?;[^\n]*?//[^\n]*?\+0x([0-9A-Fa-f]+)", re.M)

WIDTHS = {
    "unsigned char": 1, "char": 1, "bool": 1, "std::uint8_t": 1, "std::int8_t": 1,
    "std::uint16_t": 2, "std::int16_t": 2,
    "std::uint32_t": 4, "std::int32_t": 4, "int": 4, "float": 4,
    "std::uint64_t": 8, "std::int64_t": 8, "std::size_t": 8, "std::uintptr_t": 8,
    "double": 8, "long": 8, "std::string": 32, "Objective": 4, "NestingOrigin": 4,
}
MODULE_SIZE = 0x2C0


def parse(path, name):
    text = io.open(path, encoding="utf-8", errors="replace").read()
    for match in STRUCT.finditer(text):
        if match.group(1) != name:
            continue
        fields = {}
        for ftype, fname, array, offset in FIELD.findall(match.group("body")):
            if NOT_A_FIELD.match(fname):
                continue          # **PADDING IS NOT A FIELD**, see the note at NOT_A_FIELD
            count = 1
            if array:
                inner = array.strip("[]")
                count = int(inner, 16) if inner.startswith("0x") else (int(inner) if inner.isdigit() else 1)
            width = WIDTHS.get(ftype.strip(), 0) * count
            fields[int(offset, 16)] = (ftype.strip(), fname, width)
        return fields
    return {}


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", dest="out")
    args = parser.parse_args(argv)

    order = parse(os.path.join(ROOT, "lcns", "include", "lcns", "model.hpp"), "Order")
    layout = parse(os.path.join(ROOT, "lcns", "include", "lcns", "launching_order.hpp"), "LaunchingOrderLayout")
    if not order or not layout:
        print("REFUSING: Order parsed %d and the layout %d" % (len(order), len(layout)))
        return 2

    both = sorted(set(order) & set(layout))
    only_layout = sorted(set(layout) - set(order))
    only_order = sorted(set(order) - set(layout))
    # a field name that is `unnamedXXX` says the module never named it, so it is the one thing the merge should NOT take from the layout
    unnamed = [o for o in only_layout if re.match(r"unnamed[0-9A-Fa-f]+$", layout[o][1])]
    unknown_widths = sorted({order[o][0] for o in only_order if not order[o][2]} | {layout[o][0] for o in only_layout if not layout[o][2]})

    lines = ["# The two placed layouts of the module's 0x2C0 object\n"]
    lines.append("| | Order (model.hpp) | LaunchingOrderLayout (launching_order.hpp) |")
    lines.append("|---|---|---|")
    lines.append("| fields with an offset | %d | %d |" % (len(order), len(layout)))
    lines.append("| shared offsets | colspan=2 | **%d** |" % len(both))
    lines.append("| only here | %d | %d |" % (len(only_order), len(only_layout)))
    lines.append("")
    lines.append("**AND `LaunchingOrderLayout` HAS %d OFFSETS `Order` DOES NOT, OF WHICH %d CARRY AN `unnamedXXX` NAME** -- which that file's own header explains:"
                 " \"A field with an OFFSET-DERIVED name (unnamedXXX) is one the module never names anywhere this project [can see]\". **So the merge takes those"
                 " offsets and NOT their names**, and `Order`'s names stand where it has one.\n" % (len(only_layout), len(unnamed)))
    lines.append("")
    lines.append("## The %d offsets only the layout has\n" % len(only_layout))
    lines.append("| offset | the layout's type | its name | width |")
    lines.append("|---|---|---|---|")
    for offset in only_layout:
        ftype, fname, width = layout[offset]
        lines.append("| +0x%03X | `%s` | `%s` | %s |" % (offset, ftype, fname, ("%d B" % width) if width else "?"))
    lines.append("")
    if only_order:
        lines.append("## And the %d offsets only `Order` has\n" % len(only_order))
        lines.append("| offset | Order's type | its name |")
        lines.append("|---|---|---|")
        for offset in only_order:
            ftype, fname, _width = order[offset]
            lines.append("| +0x%03X | `%s` | `%s` |" % (offset, ftype, fname))
        lines.append("")
    if unknown_widths:
        lines.append("## And types whose width the table lacks, which the merge needs\n")
        for ftype in unknown_widths:
            lines.append("   `%s`" % ftype)
        lines.append("")

    text = "\n".join(lines) + "\n"
    if args.out:
        io.open(os.path.join(ROOT, args.out), "w", encoding="utf-8", newline="\n").write(text)
        print("wrote %s: %d shared, %d only in the layout (%d unnamed), %d only in Order"
              % (args.out, len(both), len(only_layout), len(unnamed), len(only_order)))
        return 0
    print(text[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
