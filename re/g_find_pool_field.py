# -*- coding: utf-8 -*-
"""Find every store to `[reg + 8]` in the functions that can be building a `Utils::Pool`, so its field has an instruction.

**WHAT IS ALREADY CERTAIN, FROM THE TABLE AND TWO SIZES:**

    0xA3BCE0 is Utils::Pool<Multi::NestingContext>'s table base    [base] = NULL, [base + 8] = the typeinfo at 0xA18490
    its slots are TWO: 0x998FB0 at slot 0, which is the allocator-free thunk, and NULL at slot 1 -- A PURE VIRTUAL
    NestingContextPool is 0x10 bytes (0x32913 `mov ecx, 0x10`) and a `{vptr}` base is 8, so the base holds ONE more word
    measured: `{vptr, one pointer}` is 0x10, and `+0x478 + 0x10 = +0x488`, which is where the destructor's next interest starts

**so `Utils::Pool<T>` is `{vptr, T** items_}` and its constructor stores that pointer at +8.** This looks for the store, with the object register established
first: the functions are the ones that install the table, 0x30B60, 0x30EB0, 0x32700, 0x69A480, 0x69A500 and 0x871570.
"""
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

FUNCTIONS = [0x30B60, 0x30EB0, 0x32700, 0x69A480, 0x69A500, 0x871570]
STORE = re.compile(r"^(byte|word|dword|qword) ptr \[(\w+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\], ")


def main():
    profile = load_prof()
    for function in FUNCTIONS:
        size = (profile.get(function) or {}).get("size") or 0
        if not size:
            print("0x%X is not in the profile" % function)
            continue
        print("=== 0x%X (%d bytes)" % (function, size))
        for instruction in disasm(function):
            if instruction.address >= function + size:
                break
            found = STORE.match(instruction.op_str)
            if not found:
                continue
            offset = int(found.group(3), 16) if found.group(3) else 0
            print("   %06X  [%s + 0x%X]  %s" % (instruction.address, found.group(2), offset, instruction.op_str[:56]))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
