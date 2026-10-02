# -*- coding: utf-8 -*-
"""Decode the file name and line number at every assertion site in a function.

RE 0x60A620 is the assertion reporter. Its METHOD argument is built in place a few bytes at a time before the call, and one of its
integer arguments is the LINE NUMBER -- a fact this project established at 0x526160, where the stores spelled
"../structure\\stat.cpp" and the line was 154. The ledger records 680 such call sites and has never used the line.

    python g_assert_sites.py 0x1EE50

THE DEFECT THE FIRST VERSION HAD, because it is instructive. It scanned backwards for the line number and took the FIRST immediate
assigned to `edx`, which at 0x526160 is `0x7070` -- the two bytes "pp" that go INTO THE STRING. The real line, `0x9A`, is assigned two
instructions before the call. So the tool reported no line numbers and its self-check caught it:

    SELF-CHECK: 0x526160's reporter sites give line numbers [] (an earlier round read 154 and 176 by hand)
    REFUSING TO REPORT

**The first value seen scanning backwards is the last value written going forwards**, which is the rule for a register that is reused:
the string construction clobbers `edx` on its way and the line number is what is left in it at the call. Taking the LAST assignment in
program order is correct; taking the first in scan order is not.

A SELF-CHECK, per the rule: the tool must reproduce 154 and 176 from 0x526160's two sites, which an earlier round read by hand, or it
refuses to report.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

REPORTER = 0x60A620
DIRECT = re.compile(r"^0x([0-9a-f]+)$")
STORE_MEM = re.compile(r"^(?:byte|word|dword|qword) ptr \[[^\]]+\], (0x[0-9a-f]+)$")
MOVE_IMM = re.compile(r"^([a-z0-9]+), (0x[0-9a-f]+)$")
LINE_REGS = ("edx", "r8d", "ecx", "r9d", "esi", "edi")


def decode_sites(address, profile):
    size = (profile.get(address) or {}).get("size") or 0
    body = [i for i in disasm(address) if i.address < address + size]
    sites = []
    for index, ins in enumerate(body):
        if ins.mnemonic != "call":
            continue
        match = DIRECT.match(ins.op_str.strip())
        if not match or int(match.group(1), 16) != REPORTER:
            continue
        bytes_in_order = []      # (index, value) so the string can be reassembled in program order
        line = None              # the LAST assignment wins, which is the value at the call
        for back in range(index - 1, max(-1, index - 60), -1):
            previous = body[back]
            if previous.mnemonic not in ("mov", "movabs"):
                continue
            text = previous.op_str.strip()
            stored = STORE_MEM.match(text)
            if stored:
                bytes_in_order.append((back, int(stored.group(1), 16)))
                continue
            moved = MOVE_IMM.match(text)
            if not moved:
                continue
            register, value = moved.group(1), int(moved.group(2), 16)
            if register in LINE_REGS:
                if line is None:
                    line = value          # the first seen backwards IS the last written forwards
                continue
            if register.startswith("r") and value > 0x100:
                bytes_in_order.append((back, value))
        bytes_in_order.sort()             # back into program order for the string
        raw = bytearray()
        for _back, value in bytes_in_order:
            width = 8 if value > 0xFFFFFFFF else (4 if value > 0xFFFF else 2)
            raw.extend(value.to_bytes(width, "little"))
        name = bytes(raw).split(b"\x00")[0]
        printable = "".join(chr(byte) if 32 <= byte < 127 else "." for byte in name)
        sites.append((ins.address, line, printable))
    return sites


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("address")
    args = parser.parse_args(argv)
    profile = load_prof()

    # THE SELF-CHECK'S PREMISE WAS WRONG AND THE CHECK CAUGHT IT, which is why it is written as a premise rather than as a hope.
    # An earlier round recorded "the assert argument edx is 0x9A then 0xB0" while reading the LENGTH and HEIGHT aggregators
    # together, and this tool's first self-check asked 0x526160 alone for BOTH numbers. 0x526160 has ONE reporter call, and 0xB0
    # belongs to its twin 0x5266A0. So the check now asks each function for its own line, which is what the evidence supports.
    lengths = [line for _at, line, _text in decode_sites(0x526160, profile) if line is not None]
    heights = [line for _at, line, _text in decode_sites(0x5266A0, profile) if line is not None]
    print("SELF-CHECK: 0x526160 gives %s (the length aggregator, read by hand as 154) and 0x5266A0 gives %s (height, 176)"
          % (lengths, heights))
    if 154 not in lengths or 176 not in heights:
        print("REFUSING TO REPORT: the decoder cannot reproduce the line numbers read by hand, so its output means nothing.")
        return 2
    print("")

    root = int(args.address, 16)
    sites = decode_sites(root, profile)
    size = (profile.get(root) or {}).get("size") or 0
    print("0x%X  %d bytes  %d assertion site(s)" % (root, size, len(sites)))
    print("")
    for at, line, text in sites:
        print("   0x%-8X  line %-6s  %r" % (at, line if line is not None else "?", text))
    print("")
    print("Each site is a file and a line the routine names about itself. The FILE comes from the byte stores before the call, which is")
    print("the channel this project found at 0x526160; the LINE is the last value left in one of the reporter's integer arguments.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
