# -*- coding: utf-8 -*-
"""Why does the assertion-site decoder find no line numbers? Print what it actually sees."""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

REPORTER = 0x60A620
DIRECT = re.compile(r"^0x([0-9a-f]+)$")


def main():
    profile = load_prof()
    size = (profile.get(0x526160) or {}).get("size") or 0
    body = [i for i in disasm(0x526160) if i.address < 0x526160 + size]
    print("instructions: %d" % len(body))
    for index, ins in enumerate(body):
        if ins.mnemonic != "call":
            continue
        match = DIRECT.match(ins.op_str.strip())
        print("call at index %d, addr 0x%X, op %r, direct=%s, target=%s"
              % (index, ins.address, ins.op_str, bool(match),
                 match.group(1) if match else "-"))
        if match and int(match.group(1), 16) == REPORTER:
            print("   THE REPORTER. the 12 instructions before it:")
            for back in range(max(0, index - 12), index + 1):
                raw = body[back]
                print("      [%d] %08x %-12s %r" % (back, raw.address, raw.mnemonic, raw.op_str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
