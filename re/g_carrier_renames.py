# -*- coding: utf-8 -*-
"""Which carrier fields sit on an offset `Order` ALREADY NAMES -- restricted to the carriers cast FROM `Order*`.

**THE FIRST VERSION OF THIS COMPARED EVERY STRUCT IN `dll_layout.hpp` AGAINST `Order` AND WAS WRONG IN BOTH DIRECTIONS.** `PartObject` is a PART and
`NestingOwner` is a wrapper around a part; comparing their offsets to `Order`'s produced `NestingOwner::nestings at +0x50 -> Order::shearGap`, **a coincidence of
position between two different objects**. A carrier only describes `Order` if it is CAST FROM it, so the cast is the filter and the offsets are the evidence.

**AND THE PORT'S OWN TOOLKIT SAYS WHICH CASTS ARE FROM `Order*`**: `order_fields(void*)` returns `LaunchingOrderLayout*`, and the others take the wrapper's
pointer directly, so `static_cast<T*>(order)` where `order` came from a wrapper is a description of the same object -- `static_cast<PartObject*>(part)` is not.
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
IMPL = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")


def order_names():
    text = io.open(os.path.join(ROOT, "lcns", "include", "lcns", "model.hpp"), encoding="utf-8", errors="replace").read()
    body = re.search(r"struct Order\s*\{(.*?)\n\};", text, re.S)
    out = {}
    for line in body.group(1).split("\n"):
        found = re.search(r"\+0x([0-9A-Fa-f]+)", line)
        field = re.match(r"\s*([\w:<>,\s\*&]+?)\s+(\w+)\s*(?:\[[^\]]*\])?\s*[;=]", line)
        if found and field:
            out[int(found.group(1), 16)] = (field.group(2), field.group(1).strip())
    return out


def carriers_used_as_order():
    """The carrier types the implementations cast a parameter named like the export's FIRST argument to."""
    text = io.open(IMPL, encoding="utf-8", errors="replace").read()
    # the parameter names the wrappers call the object: order, options, object, part, handle, owner ...
    used = {}
    for match in re.finditer(r"static_cast<([\w:]+)\*>\((\w+)\)", text):
        used.setdefault(match.group(1), set()).add(match.group(2))
    return used


def fields_of(name):
    text = io.open(os.path.join(ROOT, "lcns", "include", "lcns", "dll_layout.hpp"), encoding="utf-8", errors="replace").read()
    match = re.search(r"struct\s+%s\s*\{(.*?)\n\};" % re.escape(name), text, re.S)
    if not match:
        return []
    cursor = 0
    out = []
    for line in match.group(1).split("\n"):
        field = re.match(r"\s*([\w:<>,\s\*&]+?)\s+(\w+)\s*(?:\[([^\]]*)\])?\s*;", line)
        if not field:
            continue
        array = field.group(3)
        comment = re.search(r"\+0x([0-9A-Fa-f]+)", line)
        if comment:
            cursor = int(comment.group(1), 16)
        out.append((cursor, field.group(2)))
        cursor += (int(array, 16) if array and array.startswith("0x") else (int(array) if array and array.isdigit() else 8))
    return out


def main():
    names = order_names()
    used = carriers_used_as_order()
    print("Order names %d offset(s)" % len(names))
    print("")
    print("the parameter names the implementations cast from, which says which carriers describe the SAME object:")
    for carrier, arguments in sorted(used.items()):
        print("   %-30s from %s" % (carrier, ", ".join(sorted(arguments))))
    print("")
    # a carrier is a re-description of Order when it is cast from a parameter the WRAPPERS spell as the object
    SUSPECTS = ["IntFieldCarrier", "OptionFlagCarrier", "UnknownFlagCarrier", "SolverOptionCarrier",
                "LocalEngineCarrier", "HoleForceCarrier", "BadGeometryCarrier", "CachedBoxCarrier",
                "LaunchingOrderLayout"]
    for carrier in SUSPECTS:
        fields = fields_of(carrier)
        if not fields:
            continue
        hits = [(o, f, names[o][0]) for o, f in fields if o in names]
        print("%-24s %2d field(s), %2d on an offset Order names" % (carrier, len(fields), len(hits)))
        for offset, field, order_field in hits:
            marker = "  ** RENAME **" if field != order_field else ""
            print("   +0x%-4X %-36s Order::%s%s" % (offset, field, order_field, marker))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
