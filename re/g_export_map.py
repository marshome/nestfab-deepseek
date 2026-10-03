# -*- coding: utf-8 -*-
"""Map the export layer: which file holds what, so the answer is a list of paths and not a guess."""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
FILES = [
    "lcns/src/api_exports.cpp",
    "lcns/src/exports.cpp",
    "lcns/src/exports_impl.cpp",
    "lcns/include/lcns/api.hpp",
    "lcns/include/lcns/exports.hpp",
    "lcns/include/lcns/exports_impl.hpp",
    "lcns/include/lcns/detail/exports_forwarding.inc",
    "lcns/include/lcns/dll_layout.hpp",
]

for name in FILES:
    path = os.path.join(ROOT, name)
    if not os.path.isfile(path):
        print("%-56s MISSING" % name)
        continue
    text = io.open(path, encoding="utf-8", errors="replace").read()
    marks = []
    if 'extern "C"' in text:
        marks.append('extern "C" x%d' % text.count('extern "C"'))
    if "entries()" in text or "kExportTable" in text:
        marks.append("the row table")
    if "kAddresses" in text:
        marks.append("kAddresses[168]")
    if "kForwarding[]" in text:
        marks.append("kForwarding[]")
    if re.search(r"^\s*(void|int|std::\w[\w:<>]*)\s+\w+\(void\*", text, re.M):
        marks.append("implementations (void* first parameter)")
    print("%-56s %5d lines  %s" % (name, len(text.split("\n")), ", ".join(marks)))
