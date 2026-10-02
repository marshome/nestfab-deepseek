# -*- coding: utf-8 -*-
"""Verify the comparison-pair hypothesis: do the equal-size neighbours differ only in a negated tail?

The previous round identified four equal-size pairs with identical openings and called them `operator==` / `operator!=`. That is a
SHAPE, and this project does not accept a shape. What would make it a finding is that the two bodies are IDENTICAL except for the
last few instructions, because `!=` is defined as `!(==)` and a compiler emits exactly that.

This compares each pair instruction by instruction and reports:
  * how many instructions agree, from the START;
  * where they first differ;
  * what the differing tails are.

A pair whose bodies agree for all but a two or three instruction tail, where the tail is a comparison or a `xor`/`sete`/`setne`,
supports the hypothesis. A pair that diverges in the middle does not, and then the equal size is a coincidence of two different
functions that happen to be the same length.

A SELF-CHECK IS INCLUDED, per the rule this project adopted: one function compared against ITSELF must report "identical to the end",
and the tool refuses to report if it does not. That is the check whose absence let a broken parser print a confident zero two rounds
ago.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

PAIRS = [
    (0x87C960, 0x87C3C0),
    (0x87BA80, 0x87BF20),
    (0x87CC80, 0x87C6E0),
    (0x87BD10, 0x87C1B0),
    (0x929FA0, 0x9285E0),   # two of the eight identical teardown instantiations, as a control
]
SELF_CHECK = (0x87C960, 0x87C960)


def instructions(address, profile):
    size = (profile.get(address) or {}).get("size") or 0
    out = []
    for ins in disasm(address):
        if ins.address >= address + size:
            break
        out.append("%s %s" % (ins.mnemonic, ins.op_str.replace(" ", "")))
    return out


def compare(address_a, address_b, profile):
    left = instructions(address_a, profile)
    right = instructions(address_b, profile)
    common = 0
    for a, b in zip(left, right):
        if a != b:
            break
        common += 1
    return left, right, common


def main():
    profile = load_prof()

    # ---- the self-check: a function against itself must agree to the end -----------------------------------------------
    left, right, common = compare(SELF_CHECK[0], SELF_CHECK[1], profile)
    ok = common == len(left) == len(right) and left
    print("SELF-CHECK: 0x%X against itself agrees on %d of %d instructions?  %s"
          % (SELF_CHECK[0], common, len(left), ok))
    if not ok:
        print("REFUSING TO REPORT: the comparison cannot see a function agree with itself, so it measures nothing.")
        return 2
    print("")

    for address_a, address_b in PAIRS:
        left, right, common = compare(address_a, address_b, profile)
        total = min(len(left), len(right))
        print("=== 0x%X (%d instr) vs 0x%X (%d instr)" % (address_a, len(left), address_b, len(right)))
        print("    identical from the start for %d of %d instructions" % (common, total))
        if common == total and len(left) == len(right):
            print("    -> IDENTICAL to the end, so these are one function emitted twice, not a pair")
        else:
            print("    the first difference: %s" % ("-" if common >= len(left) else left[common]))
            print("                       vs %s" % ("-" if common >= len(right) else right[common]))
            tail_a = left[common:]
            tail_b = right[common:]
            print("    tail A: %s" % (tail_a[:4] if tail_a else "(none)"))
            print("    tail B: %s" % (tail_b[:4] if tail_b else "(none)"))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
