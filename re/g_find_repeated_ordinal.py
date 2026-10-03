# -*- coding: utf-8 -*-
"""Find which ordinal `kForwarding` repeats, because a dict keyed by ordinal silently drops one and that is what hid the wiring."""
import io
import os
import re
import sys

from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
forwarding = io.open(os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc"), encoding="utf-8").read()

entries = [(int(m.group(1)), m.group(2)) for m in
           re.finditer(r"^\s*\{(\d+),\s*reinterpret_cast<void\*>\(&([\w:]+)\)\}", forwarding, re.M)]
print("entries parsed: %d" % len(entries))
counts = Counter(ordinal for ordinal, _symbol in entries)
repeated = [(ordinal, count) for ordinal, count in counts.items() if count > 1]
print("distinct ordinals: %d" % len(counts))
print("repeated ordinals: %s" % (repeated or "none"))
for ordinal, count in repeated:
    for candidate, symbol in entries:
        if candidate == ordinal:
            print("   ord %d -> %s" % (ordinal, symbol))
print("")
print("by_ordinal would hold %d keys, and the join loses the difference" % len(counts))
