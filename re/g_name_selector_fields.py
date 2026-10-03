# -*- coding: utf-8 -*-
"""Name the two `RandomSheetSelector` members by OFFSET, as the class next door already does.

**THE SAME OFFSET HAD TWO NAMES ACROSS TWO SIBLINGS:**

    RandomSheetSelector   +0x08 secondArg_   +0x10 thirdArg_   +0x14 byte14_
    NoMixSheetSelector    +0x08 firstArg_    +0x10 thirdArg_   +0x18 owned18_   +0x20 member20_

**and the cause is that one names by ARGUMENT POSITION and the other by OFFSET.** `RandomSheetSelector`'s constructor takes its destination in `rcx` and its vtable
object in `rdx`, so the pointer it stores at +0x08 is its **second** argument -- **while `NoMixSheetSelector` stores its FIRST parameter in the same place.** **So
`secondArg_` and `firstArg_` are the same field seen from two counting conventions, and a reader comparing the two classes sees a disagreement that is not there.**

**AND THE OFFSET IS THE ONLY CONVENTION THAT SURVIVES A CHANGE OF CALLING SHAPE**, which is why `NoMixSheetSelector` already uses it for the first two. So the
pointer becomes `at08_` and the byte becomes `at14_` -- **`at08_` rather than `firstArg_`, because that name would repeat the mistake in the other direction**:
`RandomSheetSelector`'s first argument is its destination, so calling this `firstArg_` would be wrong for THIS class. **`thirdArg_` stays, because both classes
agree it is their third argument and the same four bytes.** **Where a name is a fact about the field, keep it; where it is a fact about one call site, use the
offset.**
"""
import io
import os
import sys

ROOT = r"D:\Nesting\nestfab"
FILES = [os.path.join(ROOT, "lcns", "include", "lcns", "tiling.hpp"),
         os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")]

# only the first occurrence in tiling.hpp is RandomSheetSelector's -- NoMixSheetSelector has none of these names
REPLACEMENTS = [("secondArg_", "at08_"), ("byte14_", "at14_")]


def main(apply):
    for path in FILES:
        text = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        changed = 0
        for old, new in REPLACEMENTS:
            if old not in text:
                continue
            count = text.count(old)
            text = text.replace(old, new)
            changed += count
            print("   %-30s %s -> %s  x%d" % (os.path.basename(path), old, new, count))
        if apply and changed:
            io.open(path, "w", encoding="utf-8", newline="\n").write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
