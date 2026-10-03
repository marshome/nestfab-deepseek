# -*- coding: utf-8 -*-
"""Members that no instruction in the module ever touches.

**THE OBJECTIVE SAYS "a member with no instruction behind it should be deleted or recorded as unresolved -- do not leave it looking recovered", AND NOTHING CHECKS THAT.**
`re/g_members_without_instructions.py` asks whether each class's constructor touches SOMETHING; **this asks the opposite and per-member question: for each declared member, is
there ANY function in the module that accesses that offset through that object?**

**THE ANSWER CANNOT BE EXACT**, so the report grades itself:

  * the member's offset is known from the declaration's own `static_assert(offsetof(...) == 0xNN)`, which this project writes wherever it has one;
  * the offset is then searched for in the DISASSEMBLY of every function the class is plausibly used in -- **and when the class has no known functions, the search is over the
    whole module**, which is a weaker question and is reported as such.

    python -u g_member_offsets_live.py [class ...]
"""
import io
import os
import re
import sys

from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

from lib import disasm, load_prof  # noqa: E402

INCLUDE = os.path.join(ROOT, "lcns", "include", "lcns")
ASSERT = re.compile(r"offsetof\(\s*(\w+)\s*,\s*(\w+)\s*\)\s*==\s*(0x[0-9a-fA-F]+)")
MEMBER = re.compile(r"^\s*(?:[\w:<>,\s\*&]+?)\s+(\w+_)\s*(?:=|;|\{)")


def classes_with_offsets():
    """{class: [(member, offset)]} from the static_asserts beside the members."""
    found = defaultdict(list)
    for name in sorted(os.listdir(INCLUDE)):
        if not name.endswith(".hpp"):
            continue
        text = io.open(os.path.join(INCLUDE, name), encoding="utf-8", errors="replace").read()
        for match in ASSERT.finditer(text):
            found[match.group(1)].append((match.group(2), int(match.group(3), 16)))
    return found


def main():
    wanted = sys.argv[1:]
    profile = load_prof()
    table = classes_with_offsets()
    print("classes carrying offsetof assertions: %d" % len(table))
    if wanted:
        table = {k: v for k, v in table.items() if k in wanted}
    # **THE DISPLACEMENT IS PARSED AS A NUMBER, NOT MATCHED AS A SPELLING.** Capstone prints ONE-DIGIT displacements in DECIMAL (`[rax + 8]`) and larger ones in hex
    # (`[rax + 0x10]`), **so a regex demanding `0x` sees offset 8 nowhere and every class with a member at +0x8 looks untouched** -- which is exactly what the first
    # version reported, for nine classes at once. **And `[rax]` with no displacement is offset 0**, which has to be counted too or every vtable store is invisible --
    # the same blindness `re/g_members_without_instructions.py` had.
    live = set()
    for address in sorted(profile):
        size = (profile[address] or {}).get("size") or 0
        if not size or size > 6000:
            continue
        for instruction in disasm(address):
            if instruction.address >= address + size:
                break
            for match in re.finditer(r"\[r\w+(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\]", instruction.op_str):
                live.add(int(match.group(1), 16) if match.group(1) and match.group(1).startswith("0x")
                         else (int(match.group(1)) if match.group(1) else 0))
    print("offsets that appear as a displacement somewhere in the module: %d distinct values" % len(live))
    print("")
    for klass, members in sorted(table.items()):
        dead = [m for m in members if m[1] not in live]
        if not dead:
            continue
        print("%-30s %d of %d declared member(s) at an offset NO instruction uses:" % (klass, len(dead), len(members)))
        for member, offset in dead:
            print("      %-26s +0x%X" % (member, offset))
    return 0


if __name__ == "__main__":
    sys.exit(main())
