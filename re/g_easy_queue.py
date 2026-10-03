# -*- coding: utf-8 -*-
"""Where the remaining work is EASY, measured rather than guessed.

**THE HUMAN'S METHOD: take the easy ones first, because each one becomes a clue for the next.** So this ranks the 168 exports by how little has to be read to finish
them -- and the smallest functions in a module of this kind are almost always single-field accessors, which is the easiest thing there is and the most useful to have
first.

**AND IT SEPARATES THE TWO KINDS OF EASY:**

  * **NOT YET REVERSED AND SMALL** -- a body of under ~64 bytes that nothing implements yet. These are the queue.
  * **REVERSED BUT STILL AGAINST A CARRIER** -- the ones like the eight just done, where the work is mechanical because the offsets are already measured.
"""
import io
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
API = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")
IMPL = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")


def main():
    api = io.open(API, encoding="utf-8", errors="replace").read()
    impl = io.open(IMPL, encoding="utf-8", errors="replace").read()

    bodies = {}
    for match in re.finditer(r'^\s*\{"([^"]+)",\s*(\d+),\s*\d+,\s*0x([0-9A-Fa-f]+)u,\s*(\d+)u,\s*Status::(\w+)', api, re.M):
        bodies[match.group(1)] = (int(match.group(3), 16), int(match.group(4)), match.group(5))

    forwarding = io.open(os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc"),
                         encoding="utf-8", errors="replace").read()
    named = {m.group(1) for m in re.finditer(r"^\s*\{(\d+),", forwarding, re.M)}
    dispatching = {int(m.group(1)) for m in re.finditer(r"^\s*\{(\d+),", forwarding, re.M)}

    unreversed = [(name, rva, size) for name, (rva, size, status) in bodies.items() if status != "Forwarded"]
    small = sorted((row for row in unreversed if 0 < row[2] <= 64), key=lambda row: row[2])

    print("exports in the table:            %d" % len(bodies))
    print("  Status::Forwarded:             %d" % sum(1 for v in bodies.values() if v[2] == "Forwarded"))
    print("  Status::NotReversed:           %d" % len(unreversed))
    print("")
    print("**THE EASY QUEUE: not reversed, and a body of 64 bytes or less -- %d of them**" % len(small))
    print("%-6s %-40s %-8s %s" % ("rva", "export", "size", "what a body that small usually is"))
    for name, rva, size in small[:34]:
        print("0x%05X %-40s %-8d %s" % (rva, name[:40], size, "a single field" if size <= 40 else "two or three fields"))
    print("")
    print("and the carriers still reached through a `void*`:")
    for carrier in ("OptionFlagCarrier", "IntFieldCarrier", "SolverOptionCarrier", "UnknownFlagCarrier",
                    "LocalEngineCarrier", "HoleForceCarrier", "BadGeometryCarrier", "CachedBoxCarrier"):
        count = len(re.findall(r"static_cast<%s\*>" % carrier, impl))
        if count:
            print("   %-22s %d use(s)" % (carrier, count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
