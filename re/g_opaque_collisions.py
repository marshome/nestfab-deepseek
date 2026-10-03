# -*- coding: utf-8 -*-
"""Which opaque handle names collide with a real class the port declares.

**`api.hpp` SAYS `LCNS_OPAQUE(Order)`, WHICH EXPANDS TO `struct Order_t; using Order = Order_t*`** -- so `Order` is a POINTER TO AN INCOMPLETE TYPE. And
`lcns/model.hpp` declares `struct Order`, which is the module's object with named fields. **One translation unit includes both, and a signature that says `Order*`
then means `Order_t**`**, which is exactly what the linker saw:

    defined:    lcns::dll::exports::impl::setLocalMaximumThreads(lcns::Order*, int)
    referenced: lcns::dll::exports::impl::setLocalMaximumThreads(lcns::dll::Order_t**, int)

**THE OPACITY IS THE ERASURE'S SOURCE.** The wrappers have always taken `void*` because the handle they were given was opaque by construction -- so naming the real
type is not a rename, it is the removal of a second declaration of the same class.
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
API_HPP = os.path.join(ROOT, "lcns", "include", "lcns", "api.hpp")


def declared_classes():
    """Every `struct`, `class` or `union` the port declares, and where."""
    found = {}
    for root, dirs, files in os.walk(os.path.join(ROOT, "lcns")):
        if "build" in root:
            continue
        for name in files:
            if not name.endswith((".hpp", ".h")):
                continue
            path = os.path.join(root, name)
            text = io.open(path, encoding="utf-8", errors="replace").read()
            for match in re.finditer(r"^\s*(?:struct|class|union)\s+(\w+)\b", text, re.M):
                found.setdefault(match.group(1), []).append(os.path.relpath(path, ROOT))
    return found


def main():
    text = io.open(API_HPP, encoding="utf-8", errors="replace").read()
    handles = re.findall(r"LCNS_OPAQUE\((\w+)\)", text)
    classes = declared_classes()
    print("%-16s %s" % ("opaque handle", "a real class of that name is declared in"))
    for handle in handles:
        where = classes.get(handle, [])
        print("%-16s %s" % (handle, ", ".join(sorted(set(where))) if where else "(nothing -- genuinely opaque)"))
    print("")
    collide = [h for h in handles if h in classes]
    print("**COLLIDING: %d of %d**" % (len(collide), len(handles)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
