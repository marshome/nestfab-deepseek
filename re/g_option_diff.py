# -*- coding: utf-8 -*-
"""Compare the archive's option-key table with the 175 names extracted from the lookup function.

The archive's appendix claims a "complete option key table" over rodata 0x9AF8F0-0x9AFF80, marked as proven. This project extracted 175
identifier-like names from the 259 call sites of RE 0x82A3E0. Two independent lists of the same thing, so comparing them either confirms
both or finds what one missed.

    python g_option_diff.py
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib as LIB           # noqa: E402
from lib import load_prof, rva2off  # noqa: E402

IDENT = re.compile(r"^[a-z][a-z0-9_]{4,}$")
BACKTICKED = re.compile(r"`([a-z][a-z0-9_]{4,})`")


def main():
    text = io.open(os.path.join(HERE, "findings_engine.md"), encoding="utf-8", errors="replace").read()
    marker = text.find("完整选项键表")
    print("the archive's option table section found at offset %d" % marker)
    if marker < 0:
        print("REFUSING: the section the archive claims is not present.")
        return 2
    # the table runs to the next top-level heading
    end = text.find("\n## ", marker + 10)
    chunk = text[marker:end if end > 0 else marker + 20000]
    archive = {name for name in BACKTICKED.findall(chunk) if IDENT.match(name)}
    print("names in the archive's table: %d" % len(archive))

    blob = LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data
    data = json.loads(io.open(os.path.join(HERE, "param_fields2.json"), encoding="utf-8").read())
    mine = set()
    for rows in data["sites"].values():
        for row in rows:
            if not row.get("name_rva"):
                continue
            offset = rva2off(int(row["name_rva"], 16))
            if offset is None:
                continue
            stop = blob.find(b"\x00", offset)
            if stop <= offset:
                continue
            name = blob[offset:stop].decode("ascii", "replace")
            if IDENT.match(name):
                mine.add(name)
    print("names extracted from the lookup's call sites: %d" % len(mine))
    print("")

    only_archive = sorted(archive - mine)
    only_mine = sorted(mine - archive)
    both = sorted(archive & mine)
    print("in BOTH: %d" % len(both))
    print("")
    print("in the ARCHIVE but not in my extraction: %d" % len(only_archive))
    for name in only_archive[:30]:
        print("   %s" % name)
    print("")
    print("in my extraction but not in the archive's table: %d" % len(only_mine))
    for name in only_mine[:30]:
        print("   %s" % name)
    print("")
    print("Two independent lists of one thing: agreement confirms both, and a difference is a lead rather than an error -- the archive's")
    print("table covers a rodata range while the extraction covers call sites, so a name in one and not the other says where to look.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
