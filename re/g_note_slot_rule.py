# -*- coding: utf-8 -*-
"""Register the vtable slot-offset relation as a rule, via re/g_note.py.

**THE RULE IS MECHANICAL AND I BROKE IT TWICE**: `re/vtables.json` records a class's `vtable_rva` -- the BASE of the table, with a NULL at +0 and the
typeinfo at +8 -- and its `slots`, whose first entry is at `base + 0x10`. **The address of a SLOT is not the base of anything**, and reading a slot's
VALUE as a table's base produced a false claim about `MultiOrientedPartPattern`'s slot count and a false reading of `BasicDistancer`'s entries.

re/g_note.py is used rather than editing re/RULES.md, because a rule added by hand would be a second place the rules live.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

RULE = ("vtable slot offset: vtable_rva is the table BASE (NULL at +0, typeinfo at +8) and slots[n] is the word at "
        "vtable_rva + 0x10 + n*8. The address of a slot is not the base of anything, and reading a slot VALUE as a table base "
        "produced a false slot-count claim and a false reading of a neighbouring table.")


def main():
    result = subprocess.run([sys.executable, os.path.join(HERE, "g_note.py"), "requirement", RULE,
                             "--check", "re/g_check_vtable_slots.py"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    print((result.stdout or "").strip()[:300])
    if result.returncode != 0:
        print((result.stderr or "").strip()[:300])
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
