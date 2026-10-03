# -*- coding: utf-8 -*-
"""Re-run the gap tool's own loop and print the verdict for ordinal 84, so the discrepancy is in front of me rather than reasoned about."""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
api = io.open(os.path.join(ROOT, "lcns", "src", "api_exports.cpp"), encoding="utf-8", errors="replace").read()
forwarding = io.open(os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc"), encoding="utf-8", errors="replace").read()

entries = [(int(m.group(1)), m.group(2)) for m in
           re.finditer(r"^\s*\{(\d+),\s*reinterpret_cast<void\*>\(&([\w:]+)\)\}", forwarding, re.M)]
by_ordinal = {ordinal: symbol for ordinal, symbol in entries}
wrappers = {}
for match in re.finditer(r'extern "C"[^;{]*?\b(\w+)\s*\([^)]*\)\s*\{(.*?)\n\}', api, re.S):
    wrappers[match.group(1)] = " ".join(match.group(2).split())
rows = re.findall(r'\{"([^"]+)",\s*(\d+),\s*(\d+),', api)
name_of = {int(row[1]): row[0] for row in rows}

dispatching, stubbed = [], []
for ordinal, symbol in sorted(by_ordinal.items()):
    name = name_of.get(ordinal)
    body = wrappers.get(name or "", None)
    if body is None:
        stubbed.append((ordinal, name or "(no row)", symbol, "NO WRAPPER"))
    elif "impl::" in body:
        dispatching.append((ordinal, name, symbol))
    else:
        stubbed.append((ordinal, name, symbol, "the wrapper does not call impl::"))

print("dispatching: %d   stubbed: %d   total: %d" % (len(dispatching), len(stubbed), len(dispatching) + len(stubbed)))
print("ordinal 84 in dispatching: %s" % any(row[0] == 84 for row in dispatching))
print("ordinal 84 in stubbed:     %s" % any(row[0] == 84 for row in stubbed))
print("")
print("the dispatching ordinals: %s" % sorted(row[0] for row in dispatching))
