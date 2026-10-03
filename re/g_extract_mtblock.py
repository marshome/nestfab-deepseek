# -*- coding: utf-8 -*-
"""Extract the two test blocks and hand them to g_land.py, so the edit is recorded and matches exactly once."""
import io
import os
import sys

ROOT = r"D:\Nesting\nestfab"
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")
LANDINGS = os.path.join(ROOT, "re", "landings")

START = "    // ---------------------------------------------------------------- RandomSheetSelector embeds an MT19937 (RE 0xB0040)"
END = '    return check::finish("test_recovered");'

body = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
start = body.find(START)
end = body.find(END)
if start < 0 or end < 0 or end <= start:
    print("REFUSING: the two markers are not found in order")
    sys.exit(2)

if not os.path.isdir(LANDINGS):
    os.makedirs(LANDINGS)
old = body[start:end]
io.open(os.path.join(LANDINGS, "mtblock.old"), "w", encoding="utf-8", newline="\n").write(old)
print("the old block is %d lines, from %d to %d" % (len(old.split("\n")), start, end))
