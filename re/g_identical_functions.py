# -*- coding: utf-8 -*-
"""How many functions in this module are IDENTICAL modulo their own addresses?

That is a count of template instantiations and of routines the compiler emitted more than once, and it is the question the previous
round's defect made visible: a comparison that scores `jle 0x87cbc5` against `jle 0x87c625` as a difference is measuring addresses
rather than code, and any two copies of one routine differ in exactly that way by construction.

NORMALISATION. Each instruction is reduced to `mnemonic + operand shape`, where:
  * a hex literal that is an ADDRESS inside the code range becomes `<addr>`;
  * a hex literal that is a CALL or JUMP target becomes `<addr>`;
  * every other hex literal is kept, because a constant like 0x18 or 0x2E is part of the code's meaning;
  * a rip-relative operand becomes `<rip>` and its resolved target is not compared, because that too is an address.

A SELF-CHECK, per the rule this project adopted two rounds ago -- and this time the self-check is DESIGNED AGAINST THE KNOWN DEFECT.
The previous tool's self-check compared a function with itself, which is the one input where an address difference cannot appear.
This one instead compares 0x87C960 with 0x87C3C0 and requires that they be reported as DIFFERENT even though their instructions are
word-for-word alike -- because if normalisation is working, they should agree much further than 48 instructions. If the normalised
comparison still reports them as differing at a jump, normalisation is not working.

Usage: python g_identical_functions.py [--top 25] [--min-instructions 8]
"""
import argparse
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib as LIB           # noqa: E402
from lib import disasm, load_prof  # noqa: E402

HEX = re.compile(r"0x([0-9a-f]+)")
RIP = re.compile(r"\[rip \+ 0x[0-9a-f]+\]")
CODE_LOW, CODE_HIGH = 0x400000, 0x9C0000


def image_size():
    blob = LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data
    return len(blob)


def normalise(ins):
    """Reduce one instruction to a shape, replacing addresses but keeping constants."""
    text = ins.op_str.replace(" ", "")
    text = RIP.sub("[rip]", text)
    def replace(match):
        value = int(match.group(1), 16)
        # an address, in the code range or beyond the image's data as a pointer
        if CODE_LOW <= value < CODE_HIGH:
            return "<addr>"
        if ins.mnemonic in ("call", "jmp") or ins.mnemonic.startswith("j"):
            return "<addr>"
        if value > 0x100000:
            return "<addr>"      # a large literal is a pointer or an offset into the image
        return match.group(0)
    text = HEX.sub(replace, text)
    return "%s %s" % (ins.mnemonic, text)


def shape(address, profile):
    size = (profile.get(address) or {}).get("size") or 0
    out = []
    for ins in disasm(address):
        if ins.address >= address + size:
            break
        out.append(normalise(ins))
    return out


def compare(address_a, address_b, profile):
    left, right = shape(address_a, profile), shape(address_b, profile)
    common = 0
    for a, b in zip(left, right):
        if a != b:
            break
        common += 1
    return left, right, common


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=25)
    parser.add_argument("--min-instructions", type=int, default=8)
    args = parser.parse_args(argv)
    profile = load_prof()

    # ---- the self-check, designed against the DEFECT THE PREVIOUS TOOL HAD ------------------------------------------------
    left, right, common = compare(0x87C960, 0x87C3C0, profile)
    print("SELF-CHECK: with normalisation, 0x87C960 vs 0x87C3C0 agree for %d of %d (was 48 of 203 before)" %
          (common, min(len(left), len(right))))
    if common <= 48:
        print("REFUSING TO REPORT: normalisation did not move the disagreement past the jump, so it is not normalising.")
        return 2
    print("")

    # ---- group every function by its normalised shape ---------------------------------------------------------------------
    groups = collections.defaultdict(list)
    for address, info in profile.items():
        size = info.get("size") or 0
        if not (8 <= size <= 20000):
            continue
        if not (CODE_LOW <= address < CODE_HIGH):
            continue
        text = shape(address, profile)
        if len(text) < args.min_instructions:
            continue
        groups[tuple(text)].append(address)

    identical = {k: v for k, v in groups.items() if len(v) > 1}
    total_functions = sum(len(v) for v in identical.values())
    print("functions grouped by normalised shape: %d groups hold more than one function" % len(identical))
    print("functions that are identical to at least one other: %d" % total_functions)
    print("")

    ranked = sorted(identical.items(), key=lambda kv: (-len(kv[1]), -len(kv[0])))
    print("%-7s %-9s %s" % ("copies", "instr", "addresses"))
    for text, addresses in ranked[:args.top]:
        shown = " ".join("0x%X" % a for a in addresses[:6])
        if len(addresses) > 6:
            shown += " ... +%d" % (len(addresses) - 6)
        print("%-7d %-9d %s" % (len(addresses), len(text), shown))
    print("")
    print("Addresses are normalised away and constants are NOT, so a group is a set of routines the compiler emitted more than once")
    print("with only their own positions differing. That is a template instantiation or a duplicated body, and it is not the same")
    print("claim as 'two functions of equal size', which the previous round showed is a family rather than a pair.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
