# -*- coding: utf-8 -*-
"""Diagnose a tool that found nothing: print the operand strings so the parser can be checked.

Two patterns in re/g_vector_test.py matched ZERO instructions, including ones that certainly exist (0x23BF0 stores into the three
slots at rsp+0x30, +0x38 and +0x40). A search that finds nothing is either a true negative or a broken parser, and the way to tell
them apart is to look at the strings the parser was given.

This is the sixth "impossible number" of the session and the SECOND in one round: the first was the shell quoting in the previous
inline attempt, and this is the parser. Both are the same lesson at different depths -- a tool that reports nothing must be checked
before its finding is believed.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm  # noqa: E402


def main():
    print("=== every operand string of 0x23BF0 that mentions a bracket")
    count = 0
    for ins in disasm(0x23BF0):
        if "[" in ins.op_str:
            print("   %-12s %r" % (ins.mnemonic, ins.op_str))
            count += 1
            if count >= 14:
                break
    print("")
    print("=== and the same for 0x8C5090")
    count = 0
    for ins in disasm(0x8C5090):
        if "[" in ins.op_str:
            print("   %-12s %r" % (ins.mnemonic, ins.op_str))
            count += 1
            if count >= 10:
                break
    return 0


if __name__ == "__main__":
    sys.exit(main())
