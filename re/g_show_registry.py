# -*- coding: utf-8 -*-
"""Show the registry entries for the two existing NotReversed marks, so the new one matches their shape."""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
text = io.open(os.path.join(ROOT, "lcns", "include", "lcns", "recovery.hpp"), encoding="utf-8").read()
start = text.index("kGaps[]")
print("the registry starts at line %d" % (text[:start].count("\n") + 1))
for match in re.finditer(r'^\s*\{"[^"]+", Status::NotReversed.*$', text, re.M):
    print("   %s" % match.group(0).strip()[:120])
print("")
for name in ("search.beam_width", "row.135040"):
    index = text.find('"%s"' % name)
    if index < 0:
        print("   %s NOT REGISTERED" % name)
        continue
    end = text.find("\n", text.find('},', index))
    print("   %s:" % name)
    for line in text[index:end].split("\n"):
        print("      %s" % line.strip()[:110])
