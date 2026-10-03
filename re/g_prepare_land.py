# -*- coding: utf-8 -*-
"""Prepare the pair g_land.py needs from a block file and the finish marker."""
import io
import os
import sys

ROOT = r"D:\Nesting\nestfab"
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")
LANDINGS = os.path.join(ROOT, "re", "landings")
MARKER = '    return check::finish("test_recovered");'

name = sys.argv[1] if len(sys.argv) > 1 else None
if not name:
    print("REFUSING: give the block's stem, e.g. cancellers")
    sys.exit(2)

body = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
if body.count(MARKER) != 1:
    print("REFUSING: the finish marker appears %d time(s)" % body.count(MARKER))
    sys.exit(2)
if not os.path.isdir(LANDINGS):
    os.makedirs(LANDINGS)
io.open(os.path.join(LANDINGS, name + ".old"), "w", encoding="utf-8", newline="\n").write(MARKER)

block = io.open(os.path.join(LANDINGS, name + ".new"), encoding="utf-8", newline="").read().replace("\r\n", "\n")
if not block.endswith("\n"):
    block += "\n"
io.open(os.path.join(LANDINGS, name + ".new"), "w", encoding="utf-8", newline="\n").write(block + MARKER)
print("prepared %s: %d lines of assertions plus the finish marker" % (name, len(block.split("\n"))))
