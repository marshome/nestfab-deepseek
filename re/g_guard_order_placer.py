# -*- coding: utf-8 -*-
"""Add a NON-DESTRUCTIVE guard to the Order placer, so the failure that destroyed the file cannot recur.

**WHAT HAPPENED, RECORDED BECAUSE THE GUARD IS THE FIX.** The first version of this tool rebuilt `struct Order` from the field lines it understood and wrote
the result in. `Order` is 335 lines carrying `std::vector<Part> parts`, `std::vector<Sheet> sheets`, accessor methods and private state with no offset
comment, **so all of it was dropped and four files stopped building.** The file was reverted with `git checkout` before anything else.

**THE GUARD IS A LINE COUNT, AND IT IS THE RIGHT ONE BECAUSE THE OPERATION IS ADDITIVE**: this tool only ever INSERTS padding, so the result must have MORE
lines than the original and must still contain every original line. Both are checked before the write, and a violation refuses.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLACER = os.path.join(HERE, "g_place_order_fields.py")

OLD = """    rebuilt = []
    for index, line in enumerate(lines):
        for filler in insertions.get(index, []):
            rebuilt.append(filler)
        rebuilt.append(line)
    text = text[:match.start()] + "\\n".join(rebuilt) + text[match.end():]
    io.open(MODEL, "w", encoding="utf-8", newline="\\n").write(text)
    print("inserted %d padding member(s); every original line is still in place" % pad)
    return 0"""

NEW = """    rebuilt = []
    for index, line in enumerate(lines):
        for filler in insertions.get(index, []):
            rebuilt.append(filler)
        rebuilt.append(line)

    # **THE GUARD, BECAUSE THIS OPERATION IS ADDITIVE AND A VERSION THAT WAS NOT DESTROYED THE FILE.** It only INSERTS padding, so the result must have
    # MORE lines than the original and must still contain every original line in order. Both are checked before the write.
    if len(rebuilt) <= len(lines):
        print("REFUSING: the rebuild has %d lines against the original %d, and an ADDITIVE edit must have more" % (len(rebuilt), len(lines)))
        return 2
    without_padding = [line for line in rebuilt if not line.lstrip().startswith("std::byte padding")]
    if without_padding != lines:
        first = next((i for i, (a, b) in enumerate(zip(without_padding, lines)) if a != b), min(len(without_padding), len(lines)))
        print("REFUSING: line %d differs from the original, so this edit is not additive and would drop what it does not understand" % first)
        return 2

    text = text[:match.start()] + "\\n".join(rebuilt) + text[match.end():]
    io.open(MODEL, "w", encoding="utf-8", newline="\\n").write(text)
    print("inserted %d padding member(s); %d line(s) before, %d after, and every original line is still in place" % (pad, len(lines), len(rebuilt)))
    return 0"""


def main():
    text = io.open(PLACER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "THE GUARD, BECAUSE THIS OPERATION IS ADDITIVE" in text:
        print("the guard is already present")
        return 0
    if OLD not in text:
        print("REFUSING: the write block is not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(PLACER, "w", encoding="utf-8", newline="\n").write(text)
    print("the placer now refuses any edit that is not provably additive")
    return 0


if __name__ == "__main__":
    sys.exit(main())
