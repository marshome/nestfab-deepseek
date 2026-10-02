# -*- coding: utf-8 -*-
"""Count the rule ids in RULES.md and report duplicates. **TWO RULES FOR ONE REQUIREMENT IS THE DRIFT THIS PROJECT CHECKS FOR.**
"""
import collections
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
text = io.open(os.path.join(HERE, "RULES.md"), encoding="utf-8", errors="replace").read()

ids = re.findall(r'\{"id":\s*"([^"]+)"', text)
counts = collections.Counter(ids)
print("the %d markdown pseudo-ids in the file: %d" % (len(ids), len(counts)))
duplicates = [name for name, count in counts.items() if count > 1]
if duplicates:
    print("DUPLICATES: %s" % ", ".join(duplicates))
else:
    print("no duplicate ids")
print("")
for name in sorted(counts):
    print("   %-52s x%d" % (name[:52], counts[name]))
