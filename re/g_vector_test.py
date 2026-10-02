# -*- coding: utf-8 -*-
"""Is the 0x18 byte element a std::vector header? The test, with a parser that works and a self-check.

THE LESSON FROM THE PREVIOUS ROUND IS BUILT IN. A first version of this reported zero for every search, including for a function it
was handed as a known sighting -- which is the only reason the break was noticed, because a zero from a broken parser and a zero from
a real absence look identical. So this version:

  * strips the `qword ptr`/`dword ptr` size prefixes the operand strings carry, which the previous patterns did not allow for;
  * asserts up front that it can FIND the three-slot store in 0x23BF0, and REFUSES TO REPORT if it cannot. A tool that cannot find
    what it is looking at has nothing to say about what it is looking for.

The hypothesis: libstdc++'s std::vector is three pointers -- begin, end, capacity -- which is 0x18 on x86-64. The previous round
found that 0x23BF0's triple is {begin, end, end} instead, so the hypothesis is not supported there; this asks whether it is supported
ANYWHERE, which is a different question and the one that decides whether the 0x18 size has one meaning or several.
"""
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

# the operand strings carry a size prefix: 'mov qword ptr [rsp + 0x30], rax'
PREFIX = re.compile(r"\b(?:qword|dword|word|byte)\s+ptr\s+")
# a store of a register into [reg + off], with the source LAST
STORE = re.compile(r"^\[([a-z0-9]+)(?:\s*\+\s*(0x[0-9a-f]+))?\],\s*(r[a-z0-9]+)$")
# a load into a register from [reg + off], with the destination FIRST
LOAD = re.compile(r"^([a-z0-9]+),\s*\[([a-z0-9]+)(?:\+\s*(0x[0-9a-f]+))?\]$")
# a subtraction of two registers
SUB = re.compile(r"^([a-z0-9]+),\s*([a-z0-9]+)$")

SELF_CHECK_ADDRESS = 0x23BF0
SELF_CHECK_REQUIRED = 0x30      # the first slot the grow primitive writes


def normalise(op_str):
    text = PREFIX.sub("", op_str.strip())
    return re.sub(r"\s*\+\s*", "+", text)


def slots(address, size):
    """The offsets one function stores into and loads from, per base register."""
    stores = collections.defaultdict(set)
    loads = collections.defaultdict(set)
    subs = []
    for ins in disasm(address):
        if ins.address >= address + size:
            break
        text = normalise(ins.op_str)
        if ins.mnemonic == "mov":
            m = STORE.match(text)
            if m:
                offset = int(m.group(2), 16) if m.group(2) else 0
                stores[m.group(1)].add(offset)
            m = LOAD.match(text)
            if m:
                offset = int(m.group(3), 16) if m.group(3) else 0
                loads[m.group(2)].add(offset)
        elif ins.mnemonic == "sub":
            m = SUB.match(text)
            if m:
                subs.append((m.group(1), m.group(2)))
    return stores, loads, subs


def main():
    profile = load_prof()

    # ---- the self-check, which is the whole point of this version ------------------------------------------------------------
    size = (profile.get(SELF_CHECK_ADDRESS) or {}).get("size") or 0
    stores, _loads, _subs = slots(SELF_CHECK_ADDRESS, size)
    found = any(SELF_CHECK_REQUIRED in offsets for offsets in stores.values())
    print("SELF-CHECK: can this parser see 0x%X store into +0x%X?  %s" % (SELF_CHECK_ADDRESS, SELF_CHECK_REQUIRED, found))
    if not found:
        print("REFUSING TO REPORT: the parser cannot find a store this function certainly makes, so a zero from it would mean")
        print("nothing. Fix the parser before believing any count below.")
        return 2
    print("  the registers it stores through: %s" % {r: sorted(o) for r, o in stores.items()})
    print("")

    install = []
    count = []
    for address, info in sorted(profile.items()):
        size = info.get("size") or 0
        if not (40 <= size <= 1200) or address < 0x400000 or address > 0x9B0000:
            continue
        try:
            stores, loads, subs = slots(address, size)
        except Exception:
            continue
        for register, offsets in stores.items():
            # the vector INSTALL shape: all three of +0, +8, +0x10 written
            if {0x00, 0x08, 0x10} <= offsets:
                install.append((address, size, register, sorted(offsets)))
                break
        for register, offsets in loads.items():
            if {0x00, 0x08} <= offsets and any(register in pair for pair in subs):
                count.append((address, size, register, sorted(offsets)))
                break

    print("=== the INSTALL shape: stores to +0x00, +0x08 AND +0x10 of one register")
    print("found %d function(s)" % len(install))
    for address, size, register, offsets in install[:14]:
        callers = len(set((profile.get(address) or {}).get("callers") or []))
        print("   0x%-8X %4d B  reg %-4s offs %-24s callers %d" % (address, size, register, offsets, callers))
    print("")
    print("=== the COUNT shape: reads +0x00 and +0x08 then subtracts one from the other")
    print("found %d function(s)" % len(count))
    for address, size, register, offsets in count[:14]:
        callers = len(set((profile.get(address) or {}).get("callers") or []))
        print("   0x%-8X %4d B  reg %-4s offs %-24s callers %d" % (address, size, register, offsets, callers))
    print("")
    print("=== and the six known 0x18 sightings, asked which shape they are")
    known = {0x23BF0: "the grow primitive", 0x22E40: "the element walk", 0x5CD5C0: "the box filler",
             0xC1A0: "the 24-byte move into order+0x188", 0x14A60: "the inline grow", 0x8C5090: "the nested walk"}
    for address, label in known.items():
        size = (profile.get(address) or {}).get("size") or 0
        stores, loads, _subs = slots(address, size)
        is_install = any({0x00, 0x08, 0x10} <= o for o in stores.values())
        is_count = any({0x00, 0x08} <= o for o in loads.values())
        print("   0x%-8X %-34s install=%-5s count=%s" % (address, label, is_install, is_count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
