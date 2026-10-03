# -*- coding: utf-8 -*-
"""Fix the SAME newline-crossing regex in g_one_definition.py that was already fixed in the measurement.

**THE DISCREPANCY BETWEEN TWO TOOLS WAS THE BUG ITSELF.** `re/g_order_union.py` counted `Order` at 56 fields and `re/g_one_definition.py` at 57, and the extra
one was `+0x170` -- a claim `incompatibleSheets` never makes:

    bool incompatibleSheets = false;
                                        <- no comment on this line
    // --- pipe mode / late common-cut block (+0x170, +0x1A0..+0x1C0) ---

**the field has no trailing comment, so the pattern's comment part reached the SECTION HEADER on the next line and read `+0x170` out of it.** The same bug was
found and fixed in `re/g_measure_order_run.py` one round ago; **this is the other copy of it**, and the fact that two tools disagreed is what made it visible --
which is an argument for having the second tool rather than against it.

**SO BOTH TOOLS NOW REQUIRE THE COMMENT ON THE SAME LINE**, and the numbers should agree.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "g_one_definition.py")

OLD = '''FIELD = re.compile(r"^\\s+[\\w:<>\\s\\*&\\[\\]]+?\\b(\\w+)\\s*(?:\\[[^\\]]*\\])?\\s*(?:=[^;]*)?;\\s*//.*?\\+0x([0-9A-Fa-f]+)", re.M)'''
NEW = '''# **AND THE COMMENT MUST BE ON THE SAME LINE, WHICH IS THE FIX FOR A BUG THAT WAS ALREADY FIXED ELSEWHERE.** The pattern this replaces let its `//...` part span a
# NEWLINE, so `incompatibleSheets` -- which has no comment of its own -- matched the SECTION HEADER below it, "// --- pipe mode / late common-cut block
# (+0x170, +0x1A0..+0x1C0) ---", and was recorded as claiming +0x170. **A regex that can cross a newline will find the next line's data**, and the reason it
# was caught here is that `re/g_order_union.py` read the same file with the same-line rule and reported one field fewer -- **two tools disagreeing is what makes
# a bug like this visible.**
FIELD = re.compile(r"^\\s+[\\w:<>\\s\\*&\\[\\]]+?\\b(\\w+)\\s*(?:\\[[^\\]]*\\])?\\s*(?:=[^;]*)?;[^\\n]*?//[^\\n]*?\\+0x([0-9A-Fa-f]+)", re.M)'''


def main():
    text = io.open(TARGET, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "AND THE COMMENT MUST BE ON THE SAME LINE" in text:
        print("the same-line rule is already there")
        return 0
    if OLD not in text:
        print("REFUSING: the FIELD pattern is not as expected")
        # show what is there, so the next attempt is not another guess
        for line in text.split("\n"):
            if "FIELD = re.compile" in line:
                print("   found: %s" % line[:160])
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(text)
    print("g_one_definition.py now requires the comment on the same line")
    return 0


if __name__ == "__main__":
    sys.exit(main())
