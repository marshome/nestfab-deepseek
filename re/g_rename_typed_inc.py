# -*- coding: utf-8 -*-
"""The same handle rename in the typed API table, with comments and strings protected.

**`api_typed.inc` IS A SECOND PLACE THE HANDLE IS NAMED** -- 86 lines of inferred signatures that say `Order` -- and the first rename did not touch it, so the build
then reported `expected type-specifier before 'Order'`. **A rename that misses a file is not a rename**, and the fix is the same substitution applied where the name
also lives.
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TARGET = r"D:\Nesting\nestfab\lcns\include\lcns\detail\api_typed.inc"


def main(apply):
    text = io.open(TARGET, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    literals = []

    def stash(match):
        literals.append(match.group(0))
        return "\x00%d\x00" % (len(literals) - 1)

    text = re.sub(r'//[^\n]*|/\*.*?\*/|"(?:[^"\\]|\\.)*"', stash, text, flags=re.S)
    before = len(re.findall(r"\bOrder\b", text))
    text = re.sub(r"\bOrder\b(?!\w)", "OrderHandle", text)
    after = len(re.findall(r"\bOrderHandle\b", text))
    text = re.sub(r"\x00(\d+)\x00", lambda m: literals[int(m.group(1))], text)
    print("api_typed.inc: %d mention(s) in CODE before, %d OrderHandle now" % (before, after))
    if apply:
        io.open(TARGET, "w", encoding="utf-8", newline="\n").write(text)
        print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
