# -*- coding: utf-8 -*-
"""Append library classifications to g_toolchain.py from the command line.

Usage: python g_classify.py 0x944470 "reason" 0x943840 "reason" ...

Reusable because every batch of leaves ends the same way: a handful of functions turn out to be ABI or library code, each
for a reason visible in its own body, and the reason has to be recorded next to the address rather than in a message that
scrolls away.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLCHAIN = os.path.join(HERE, "g_toolchain.py")
ANCHOR = "    0x63F170,  # word by word scan of a string, the strcmp family"


def main(argv):
    if len(argv) % 2 != 0:
        print("expected address and reason pairs")
        return 2
    text = io.open(TOOLCHAIN, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if ANCHOR not in text:
        print("the anchor line is gone; refusing to guess")
        return 3
    lines = [ANCHOR]
    added = []
    for index in range(0, len(argv), 2):
        rva = int(argv[index], 0)
        reason = argv[index + 1]
        if "0x%X," % rva in text:
            print("    0x%X is already classified, skipped" % rva)
            continue
        lines.append("    0x%X,  # %s" % (rva, reason))
        added.append(rva)
    io.open(TOOLCHAIN, "w", encoding="utf-8", newline="\n").write(text.replace(ANCHOR, "\n".join(lines), 1))
    print("classified %d functions: %s" % (len(added), ", ".join("0x%X" % a for a in added)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
