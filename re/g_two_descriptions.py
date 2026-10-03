# -*- coding: utf-8 -*-
"""How many implemented exports reach the module's object through `LaunchingOrderLayout` rather than through `Order`.

**THE TWO TYPES ARE THE SAME MODULE OBJECT DESCRIBED TWICE** -- `re/g_order_union.py` measured 54 shared offsets -- and this project's own adjudication says the
merge keeps `Order`'s names and the layout's widths. **So a setter written against `LaunchingOrderLayout` and a wrapper that now takes `Order*` are two
descriptions of one object inside one call path**, which is the "second description" the objective forbids.

**AND IT IS NOT ONLY COSMETIC**: the two types' fields have DIFFERENT NAMES for the same offsets, so a reader of `setShearMode` sees `layout->someName` while the
wrapper beside it says `Order*`, and nothing in the compiler relates them.
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
IMPL = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")


def main():
    text = io.open(IMPL, encoding="utf-8", errors="replace").read()
    layout = len(re.findall(r"order_fields\(", text))
    direct = len(re.findall(r"static_cast<LaunchingOrderLayout\*>", text))
    print("uses of `order_fields(`                     %d" % layout)
    print("casts to `LaunchingOrderLayout*`           %d" % direct)
    print("")
    print("=== the functions that use order_fields")
    for match in re.finditer(r"^[^\n]*\b(\w+)\s*\([^;{]*\)\s*\{(.*?)\n\}", text, re.S | re.M):
        if "order_fields(" not in match.group(2):
            continue
        print("   %-46s %s" % (match.group(1)[:46], " ".join(match.group(2).split())[:60]))
    print("")
    print("=== and every OTHER type the implementations cast their first argument to")
    types = re.findall(r"static_cast<([\w:]+)\*>\((\w+)\)", text)
    from collections import Counter
    for (type_name, _argument), count in Counter(types).most_common(14):
        print("   %-34s %d" % (type_name, count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
