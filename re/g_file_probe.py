# -*- coding: utf-8 -*-
"""Why does the file-name decoder return a one-character name? Print what it collects, raw."""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

REPORTER = 0x60A620
DIRECT = re.compile(r"^0x([0-9a-f]+)$")
STORE_MEM = re.compile(r"^(byte|word|dword|qword) ptr \[[^\]]+\], (0x[0-9a-f]+)$")
MOVE_IMM = re.compile(r"^([a-z0-9]+), (0x[0-9a-f]+)$")
LINE_REGS = ("edx", "r8d", "ecx", "r9d", "esi", "edi")


def main():
    profile = load_prof()
    size = (profile.get(0x526160) or {}).get("size") or 0
    body = [i for i in disasm(0x526160) if i.address < 0x526160 + size]
    index = [k for k, i in enumerate(body) if i.mnemonic == "call" and i.op_str.strip() == "0x60a620"][0]
    print("reporter call at index %d" % index)
    print("the 20 instructions before it, with what each matcher says:")
    for back in range(index - 20, index):
        previous = body[back]
        text = previous.op_str.strip()
        stored = STORE_MEM.match(text)
        moved = MOVE_IMM.match(text)
        verdict = []
        if stored:
            verdict.append("STORE(%s, 0x%s)" % (stored.group(1), stored.group(2)))
        if moved:
            verdict.append("MOVE(%s, 0x%s)%s" % (moved.group(1), moved.group(2),
                                                 " [LINE REG]" if moved.group(1) in LINE_REGS else ""))
        print("   [%d] %08x %-10s %-46r %s" % (back, previous.address, previous.mnemonic, text, " ".join(verdict)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
