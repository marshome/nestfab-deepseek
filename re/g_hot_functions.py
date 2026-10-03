# -*- coding: utf-8 -*-
"""The functions with the MOST CALLERS, read from the profile instead of rescanning the image.

**THE PROFILE ALREADY HAS `callers`, `callees` AND `strings` PER FUNCTION** -- and an earlier version of this tool scanned all 18614 functions with a disassembler to rebuild
what was already there, which is the same mistake as counting a pattern instead of reading the mechanism. **The keys are DECIMAL addresses**, which is why the numbers looked
like they were not in the image.

**A FUNCTION WITH MANY CALLERS IS A ROOT**: reading it explains every call site at once, and the string literals at those sites are the module's own words about itself.
"""
import io
import os
import sys

from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

from lib import load_prof  # noqa: E402


def main():
    top_n = int(sys.argv[1]) if len(sys.argv) > 1 else 26
    profile = load_prof()

    # **THE RANK COMES FROM `callers` AND NOT FROM WALKING `callees`.** `callees` holds CALL-SITE ADDRESSES -- several per call, and entries inside the function
    # itself -- **so counting it counts call sites and not callers**: it reported 10418 for `0x62F280` while that function's `callers` list holds 5209, **and a
    # count that differs from the mechanism by a factor of two is the wrong count even when the rank happens to survive.**
    incoming = Counter()
    for address, entry in profile.items():
        for caller in entry.get("callers") or []:
            incoming[address] += 1

    print("functions in the profile: %d" % len(profile))
    print("")
    print("%-11s %-8s %-7s %-6s %s" % ("address", "callers", "size", "insns", "a string it references"))
    for address, count in incoming.most_common(top_n):
        entry = profile.get(address)
        if entry is None:
            continue
        strings = entry.get("strings") or []
        sample = ""
        for text in strings[:2]:
            sample = text if isinstance(text, str) else str(text)
            break
        print("0x%09X %-8d %-7s %-6s %s"
              % (address, count, entry.get("size"), entry.get("nins"), sample[:58]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
