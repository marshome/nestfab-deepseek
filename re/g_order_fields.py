# -*- coding: utf-8 -*-
"""Every `order.<field>` an assertion string spells out, with the assertion's own text as the witness.

Usage: python g_order_fields.py [--all]

Found by reading the vocabulary of 0x1EE50, whose assertion strings contain the launch order's field names verbatim:

    0x21F81  boost.find(order.multitorch_cutting_preference) != boost.end()
    0x21F98  GetMultitorchProperties
    0x22603  all_settings.find(order.common_cut_safety_preference) != all_settings.end()
    0x2261A  GetCommonCutProperties

so `multitorch_cutting_preference` and `common_cut_safety_preference` are the module's OWN names for fields the ledger already
carries at +0x9C and +0x6C. This is the naming channel that the launch order's 70 unnamed offsets have been waiting for, and it is
different from the three channels already in use -- an assertion's second argument names a METHOD, a member expression names a
member with its receiver, and this names a FIELD as `order.<name>` in a condition.

It is also the strongest kind of field evidence this project has, because the assertion gives the name AND the map key it is looked
up in:

    order.multitorch_cutting_preference     looked up in `boost`, via GetMultitorchProperties
    order.common_cut_safety_preference      looked up in `all_settings`, via GetCommonCutProperties

which is a value flow rather than a label: the field's value is the KEY of a properties table, so the field's type is that table's
key type and its meaning is the table it indexes.

This prints every such name with the assertion text, the address, and the function that contains it.
"""
import argparse
import io
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib as LIB  # noqa: E402
from lib import disasm, load_prof, rva2off  # noqa: E402

PRINTABLE = re.compile(rb"[\x20-\x7e]{4,}")
FIELD = re.compile(r"\b(?:order|o|p_order)\s*(?:->|\.)\s*([a-z][a-z0-9_]{2,40})")
LEA = re.compile(r"^[a-z0-9]+, \[rip \+ 0x([0-9a-f]+)\]$")


def image():
    return LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data


def main(argv):
    show_all = "--all" in argv
    blob = image()
    profile = load_prof()

    # every string that names a field of the order, with where it sits
    hits = []
    for match in PRINTABLE.finditer(blob):
        text = match.group(0).decode("ascii", "replace")
        if "order" not in text:
            continue
        for name in FIELD.findall(text):
            hits.append((match.start(), name, text[:150]))

    by_name = defaultdict(list)
    for offset, name, text in hits:
        by_name[name].append((offset, text))
    order_names = sorted(by_name)
    print("strings naming an `order.<field>`: %d, over %d distinct field names" % (len(hits), len(order_names)))
    print("")

    # which function each string belongs to, by finding a lea that lands on it
    owners = defaultdict(set)
    wanted = {offset for offset, _n, _t in hits}
    for address, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        for ins in disasm(address):
            if ins.address >= address + size:
                break
            m = LEA.match(ins.op_str)
            if ins.mnemonic != "lea" or not m:
                continue
            target = ins.address + ins.size + int(m.group(1), 16)
            try:
                found = rva2off(target)
            except Exception:
                continue
            if found in wanted:
                owners[found].add(address)

    print("%-40s %-10s %s" % ("order field name", "string", "asserted in"))
    for name in order_names:
        offset, text = by_name[name][0]
        who = ", ".join("0x%X" % a for a in sorted(owners.get(offset, []))[:3])
        if not show_all and not who:
            continue
        print("%-40s 0x%-8X %s" % (name, offset, who))
    print("")
    print("Each name is the module's own word for a field of the launch order, and the assertion that contains it also names the")
    print("properties table the value indexes. That is a value flow: the field is a KEY, so its type is the table's key type.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
