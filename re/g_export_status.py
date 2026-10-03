#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""How far the 168 exports are actually reversed, in the three senses that matter, because they do not agree.

**THE THREE COUNTS, AND THE THIRD IS THE ONE THAT ANSWERS THE QUESTION:**

  * **ROWS IN THE TABLE** -- `lcns/src/api_exports.cpp` has one row per export, so this is 168 by construction and says nothing about progress.
  * **BODIES IN `exports_impl.cpp`** -- functions with a real implementation, each carrying the RE addresses it was written from. **A body here is not an
    export that works.**
  * **WRAPPERS THAT DISPATCH TO A BODY** -- an `extern "C"` wrapper that CALLS one of those bodies, which is the only thing a caller of the DLL can reach.
    **A body with no wrapper is dead code, and this is the count the question is about.**

    python -u g_export_status.py            the three counts
    python -u g_export_status.py local      and every export whose name contains that string
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
API = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")
IMPL = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")
HEADER = os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp")


def main(argv):
    api = io.open(API, encoding="utf-8", errors="replace").read()
    impl = io.open(IMPL, encoding="utf-8", errors="replace").read()
    header = io.open(HEADER, encoding="utf-8", errors="replace").read()

    rows = re.findall(r'\{"([^"]+)",\s*\d+,\s*\d+,\s*0x([0-9A-Fa-f]+)u,\s*(\d+)u,\s*Status::(\w+)', api)
    stubs = len(re.findall(r"notReversed\(", api))
    dispatching = len(re.findall(r"exports_impl::", api))
    bodies = re.findall(r"^(?:extern \"C\" )?[\w:<>*&\s]*?\b(\w+)\s*\([^;{]*\)\s*\{", impl, re.M)
    declared = set(re.findall(r"\b(\w+)\s*\([^;]*\)\s*;", header))

    print("exports in the table:                     %d" % len(rows))
    print("  of which every row's Status:            %s" % (", ".join(sorted({row[3] for row in rows})) or "--"))
    print("")
    print("bodies implemented in exports_impl.cpp:   %d" % len(bodies))
    print("  declared in exports_impl.hpp:           %d" % len(declared))
    print("")
    print("**wrappers that DISPATCH to a body:        %d**" % dispatching)
    print("  wrappers that only call notReversed():  %d" % stubs)
    print("")
    print("**SO %d BODY/BODIES ARE IN THE TREE AND UNREACHABLE FROM THE EXPORT TABLE.**" % len(bodies))
    print("A body with no wrapper is dead code: a caller of the DLL cannot reach it, and no row moves out of NotReversed because of it.")

    print("")
    if argv:
        needle = argv[0].lower()
        print("=== every export whose name contains %r" % needle)
        for name, rva, size, status in rows:
            if needle in name.lower():
                print("   %-30s rva 0x%-8s %5s bytes  %-12s" % (name, rva, size, status))
    else:
        print("   (pass a substring, e.g. `local`, to list the matching exports)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
