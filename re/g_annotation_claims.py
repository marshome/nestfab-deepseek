# -*- coding: utf-8 -*-
"""What each stack-citing annotation actually CLAIMS -- a width, a value, or a cross-reference.

**THE TWO KINDS ARE DIFFERENT AND ONLY ONE IS A DEFECT:**

    launching_order.hpp   `narrowest store is 1 byte(s) at RE 0xD062`        **a WIDTH claim** -- the store is the evidence for the member's SIZE
    row.hpp               `RE 0x5C4A45: a fixed-degree ANGLE (0x5C4CE0 value)`  **a VALUE claim** -- the address says where the number comes from

**A value claim does not place the member and does not size it**, so citing a stack store there is a cross-reference and not fabrication. **A width claim does place
it**, and a stack store cannot be the object. So the test is the annotation's own words, read rather than guessed.
"""
import glob
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

from lib import disasm  # noqa: E402

ANNOTATION = re.compile(r"^ {4,}(?P<member>[^;{}()]+?)\s*;\s*//(?P<comment>[^\n]*?)\bRE 0x(?P<address>[0-9A-Fa-f]{4,})", re.M)
STACK_WRITE = re.compile(r"\[(?:rsp|esp)(?:\s*[+-]\s*0x[0-9a-f]+)?\]")
# **THE WORDS THAT SAY "THIS STORE IS THE EVIDENCE FOR THE MEMBER'S SIZE".**
WIDTH_CLAIM = re.compile(r"narrowest store|written by|writes? (?:a |the )?\d+ ?byte|byte store|width", re.I)


def main():
    width_claims, value_claims = [], []
    for path in sorted(glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "*.hpp"))):
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for match in ANNOTATION.finditer(text):
            address = int(match.group("address"), 16)
            instructions = list(disasm(address, count=1))
            if not instructions:
                continue
            first = instructions[0]
            if not first.mnemonic.startswith("mov"):
                continue
            if not STACK_WRITE.search(first.op_str.split(",")[0]):
                continue
            entry = (os.path.basename(path), match.group("member").strip()[:30],
                     match.group("address"), first.mnemonic + " " + first.op_str, match.group("comment").strip()[:74])
            if WIDTH_CLAIM.search(match.group("comment")):
                width_claims.append(entry)
            else:
                value_claims.append(entry)

    print("**STACK-CITING ANNOTATIONS THAT CLAIM A WIDTH: %d**  <- these are the defect" % len(width_claims))
    for name, member, address, instruction, comment in width_claims:
        print("   %-22s %-30s RE 0x%-7s %-30s" % (name, member, address, instruction))
        print("      %s" % comment)
    print("")
    print("stack-citing annotations that claim a VALUE or a cross-reference: %d  <- not the defect" % len(value_claims))
    for name, member, address, instruction, comment in value_claims[:6]:
        print("   %-22s %-30s RE 0x%-7s %s" % (name, member, address, comment[:56]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
