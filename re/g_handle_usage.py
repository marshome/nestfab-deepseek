# -*- coding: utf-8 -*-
"""For each colliding handle: is it used as a parameter, as a return type, or both?

**THAT SPLIT IS THE WHOLE DECISION.** `Order` could be renamed because renaming a handle changes nothing about what a function does. **A handle used as a RETURN type
is different: the generated stubs say `return 0` and `return nullptr`, so turning those into real classes changes what 121 functions RETURN** -- and a rename that
also changes a return value is two changes pretending to be one.

**AND THE TWO KINDS NEED OPPOSITE TREATMENT:**

  * **parameter only** -> rename the handle, exactly as `Order` was renamed: the ABI is unchanged.
  * **return type** -> the stub has to gain a return value the class can produce, which is a recovered behaviour and not a rename.
"""
import io
import os
import re
import sys

from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
API = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")
TYPED = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "api_typed.inc")
HPP = os.path.join(ROOT, "lcns", "include", "lcns", "api.hpp")


def used_as():
    """kind -> set of handles, from the generated wrappers."""
    api = io.open(API, encoding="utf-8", errors="replace").read()
    out = defaultdict(set)
    for match in re.finditer(r'extern "C"\s+([\w:<>*&\s]+?)\s+(\w+)\s*\(([^)]*)\)', api):
        return_type, _name, parameters = match.group(1).strip(), match.group(2), match.group(3)
        for handle in ("OrderHandle", "Part", "Sheet", "Nesting", "NestedPart", "Solution", "NoFitNesting"):
            if re.search(r"\b%s\b" % re.escape(handle), return_type):
                out[handle].add("return")
            if re.search(r"\b%s\b" % re.escape(handle), parameters):
                out[handle].add("parameter")
    return out


def main():
    text = io.open(HPP, encoding="utf-8", errors="replace").read()
    handles = re.findall(r"LCNS_OPAQUE\((\w+)\)", text)
    typed = io.open(TYPED, encoding="utf-8", errors="replace").read()
    kinds = used_as()

    print("%-16s %-22s %-30s %s" % ("handle", "used as", "still LCNS_OPAQUE", "in the typed table"))
    for handle in handles:
        usage = kinds.get(handle, set())
        label = " and ".join(sorted(usage)) if usage else "(not in a wrapper signature)"
        print("%-16s %-22s %-30s %s"
              % (handle, label, "yes" if handle in handles else "no",
                 len(re.findall(r"\b%s\b" % re.escape(handle), typed))))
    print("")
    for handle in handles:
        usage = kinds.get(handle, set())
        if usage == {"parameter"}:
            print("   RENAMEABLE NOW: %s -- a parameter handle, so the ABI does not change" % handle)
        elif "return" in usage:
            print("   NEEDS A RETURN VALUE FIRST: %s -- %s" % (handle, " and ".join(sorted(usage))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
