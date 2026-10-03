# -*- coding: utf-8 -*-
"""Correct the four offset comments that were MISSING rather than wrong, so the permutation can place all 48 fields.

**THE FIRST VERSION OF THIS LOOKED FOR A TRAILING COMMA AND FOUND ONLY THREE OF SEVEN.** `cfgAt188`, `cfgAt190` and `cfgAt198` carry a comment and theirs was
corrected; **`cfgAt178`, `cfgAt180`, `usedSurfaceUsableOffcutRatio` and `rowAlternate` carry NONE**, so there was nothing to correct and they need one added.

**AND EACH OFFSET IS SETTLED RATHER THAN INFERRED:**

  * `cfgAt178` and `cfgAt180` take theirs from their names, which is the same convention `cfgAt188` follows and which `launching_order.hpp` records for
    those positions in `LaunchingOrderLayout`.
  * `usedSurfaceUsableOffcutRatio` is the THIRD of three doubles whose block comment says "(RE +0x28/+0x30/+0x38)", and the three declarations follow that
    comment in order: 0x28, 0x30, **0x38**.
  * `rowAlternate` is the SIXTH field of a block the comment gives as "(+0x128..+0x150)": 0x128, 0x130, 0x138, 0x140, 0x148, **0x150**.
"""
import io
import re
import sys

MODEL = r"D:\Nesting\nestfab\lcns\include\lcns\model.hpp"

ADD = [
    ("usedSurfaceUsableOffcutRatio", 0x038, "third of the three doubles the block comment gives as RE +0x28/+0x30/+0x38"),
    ("rowAlternate", 0x150, "sixth of the row block the comment gives as +0x128..+0x150"),
    ("cfgAt178", 0x178, "the offset is in the NAME, as for cfgAt188/cfgAt190"),
    ("cfgAt180", 0x180, "the offset is in the NAME, as for cfgAt188/cfgAt190"),
]


def main():
    text = io.open(MODEL, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    lines = text.split("\n")
    changed = []
    for index, line in enumerate(lines):
        for name, offset, why in ADD:
            if name in {n for n, _o, _w in changed}:
                continue
            # a declaration of that field, without a trailing comment
            if not re.match(r"^\s+[\w:<>,\s\*&]+?\s+%s\s*(=[^;]*)?;\s*$" % re.escape(name), line):
                continue
            lines[index] = "%s   // +0x%03X  ADDED: %s" % (line.rstrip(), offset, why)
            changed.append((name, offset, why))
            break
    if not changed:
        print("REFUSING: none of the four declarations was found without a comment")
        return 2
    io.open(MODEL, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    for name, offset, _why in changed:
        print("   %-32s -> +0x%03X (added)" % (name, offset))
    missing = [name for name, _o, _w in ADD if name not in {n for n, _o, _w in changed}]
    if missing:
        print("NOT FOUND: %s" % ", ".join(missing))
        return 1
    print("%d of %d added" % (len(changed), len(ADD)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
