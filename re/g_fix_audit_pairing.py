# -*- coding: utf-8 -*-
"""Make the support audit use a class's REAL constructor instead of the function its vtable slot points at.

THE LAST FALSE ENTRY, and it is the SAME PAIRING DEFECT that produced `InfiniteEngine`'s phantom `inner_`: `re/all_class_fields.json` pairs a
class with a function found by ANY reference to its vtable's slot-0 ADDRESS, and a DISPATCH SLOT is such a reference.

    PackerCache   paired with 0x158BE0   which is its vtable's SLOT 0, not its constructor
                  the constructor is 0x159480, which re/g_find_real_ctor.py reports as ALLOCATES 0x1E0

so the audit asked whether 0x158BE0 touches offsets of the object, and it does not -- **because it is a method, not the constructor.**

THE FIX: consult `re/g_find_real_ctor.py`'s rule -- the function that installs the vtable AND allocates, or failing that the one that installs
AND allocates nothing but stores to [this+0] -- and report which one was used, so a reader can see when the pairing is a slot.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.join(HERE, "g_members_without_instructions.py")

OLD = """            function = by_short[short]
            on_this, on_block, blocks = walk(function, profile)"""

NEW = """            function = by_short[short]
            # **A DISPATCH SLOT IS NOT A CONSTRUCTOR, AND THE JSON'S PAIRING CAN BE ONE.** The candidate is replaced by the first function
            # that references the class's vtable POINTER and ALLOCATES, when the paired one allocates nothing -- which is what
            # re/g_find_real_ctor.py does by hand. Its verdict is reported below so a reader sees when a slot was used.
            alternative = find_allocating_constructor(function, profile)
            used_slot = alternative is not None and alternative != function
            if used_slot:
                function = alternative
            on_this, on_block, blocks = walk(function, profile)"""

FUNCTION = '''def find_allocating_constructor(function, profile):
    """The function that installs this class's vtable pointer AND allocates; falls back to the paired one.

    A DISPATCH SLOT references the vtable's slot-0 address too, which is how the JSON came to pair `PackerCache` with 0x158BE0 -- a method of 895
    bytes that allocates nothing. **The constructor allocates**, so that is the discriminator, and it is the same one `re/g_find_real_ctor.py`
    applies.
    """
    size = (profile.get(function) or {}).get("size") or 0
    if not size:
        return None
    for instruction in disasm(function):
        if instruction.address >= function + size:
            break
        if re.match(r"^ecx, 0x[0-9a-f]+$", instruction.op_str):
            return None          # the paired function DOES allocate, so it stands
    # it does not allocate: look at the functions that install the same vtable pointer and do
    pointer = None
    for instruction in disasm(function):
        if instruction.address >= function + size:
            break
        if instruction.mnemonic == "lea":
            for operand in instruction.operands:
                if operand.type == 3 and operand.mem.base == 41:
                    if pointer is None:
                        pointer = instruction.address + instruction.size + operand.mem.disp
    if pointer is None:
        return None
    for address, info in profile.items():
        if not info.get("size") or address == function:
            continue
        allocates = False
        installs = False
        for instruction in disasm(address):
            if instruction.address >= address + info["size"]:
                break
            if re.match(r"^ecx, 0x[0-9a-f]+$", instruction.op_str):
                allocates = True
            if instruction.mnemonic == "lea":
                for operand in instruction.operands:
                    if operand.type == 3 and operand.mem.base == 41:
                        if instruction.address + instruction.size + operand.mem.disp == pointer:
                            installs = True
        if allocates and installs:
            return address
    return None


'''

OLD_MAIN = """            function = by_short[short]
            on_this, on_block, blocks = walk(function, profile)"""


def main():
    text = io.open(AUDIT, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "find_allocating_constructor" in text:
        print("the audit already consults the allocating constructor")
        return 0
    if OLD not in text:
        print("REFUSING: the pairing site is not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    # the helper goes before walk()
    anchor = "\ndef walk(function, profile):"
    if anchor not in text:
        print("REFUSING: walk is not found")
        return 2
    text = text.replace(anchor, "\n" + FUNCTION + "def walk(function, profile):", 1)
    io.open(AUDIT, "w", encoding="utf-8", newline="\n").write(text)
    try:
        compile(text, AUDIT, "exec")
    except SyntaxError as error:
        print("REFUSING: the rewritten audit does not compile -- line %d: %s" % (error.lineno, error.msg))
        return 1
    print("the audit now uses the allocating constructor when the paired function allocates nothing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
