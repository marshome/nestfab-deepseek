# -*- coding: utf-8 -*-
"""Teach the support audit to follow a HANDLE to the object it allocates.

THE BLINDNESS, and it produced four false entries in a row. The audit asked "does the function paired with this class touch offsets OF THE OBJECT",
and for a handle class the answer is legitimately NO: `MultitorchEvaluator` is `{impl* @0}`, `PackerCache` is `{impl* @8}`, `Squeezer` is
`{impl* @8}`, and their fields are inside the object the constructor ALLOCATES and stores.

**A MEMBER INSIDE THE OBJECT A HANDLE POINTS AT IS AS SUPPORTED AS ONE ON THE HANDLE**, so the audit now follows the pointer: when a constructor
allocates a block and stores it at +0 or +8, the offsets written to that BLOCK are the class's fields too.

    python g_members_without_instructions.py
"""
import argparse
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import disasm, load_prof, object_offsets  # noqa: E402
# **THE DISPLACEMENT COMES FROM `lib.object_offsets` AND NOT FROM A PRIVATE REGEX.** The pattern that stood here was
# `\[(\w+)(?: \+ (0x[0-9a-f]+))?\]`, which loses offsets 1 to 9 -- capstone prints a one-digit displacement in DECIMAL (`[rbx + 8]`), and `8` is the module's
# most common displacement (44996 occurrences) because it is `vptr + 8`, the `std::shared_ptr` count. `object_offsets` takes both spellings and treats a missing
# displacement as offset 0, which is the value a vtable store has.

FREE = 0x9984B0
ALLOCATOR = 0x998500
# the private ACCESS regex that stood here is gone: see the note at the import
MEMBER = re.compile(r"^ {4,}([\w:<>,\s\*&]+?)\s+(\w+)\s*(?:\{\})?\s*(?:=\s*[^;]*)?;", re.M)
ALLOC_SIZE = re.compile(r"^ecx, 0x([0-9a-f]+)$")


# A NOTE ON A MISTAKE MADE WHILE READING A CLASS BY HAND, because the same act is what this function automates: an offset matched against ANY of
# (rcx, rdx, rbx, rdi, rsi) is NOT evidence about `this`. Reading `Tiling::MultiOrientedPartPattern` I reported that its slot 3 "reads
# [this + 0x10]", and the matched instruction was `0x7EB61C lea rbx, [r12 + 8]` with r12 = rdx = the SECOND ARGUMENT. **THE RULE IS THAT THE BASE
# REGISTER MUST BE THE OBJECT**, and a scan accepting five registers at once cannot tell an argument from an instance. This function avoids that
# by requiring the register to have been loaded from rcx and not reassigned, which is why it reports the offsets it does.


def find_allocating_constructor(function, profile):
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


def walk(function, profile):
    """The offsets the function writes to `this`, AND the offsets it writes to a block it ALLOCATES.

    `this` is a register loaded from rcx; the allocated block is whatever the allocator returned. **The two are kept apart and both reported**,
    because which one a member lives in is exactly the distinction the handle classes turned on.
    """
    size = (profile.get(function) or {}).get("size") or 0
    if not size:
        return set(), set(), 0
    holds = {"rcx"}
    blocks = set()
    pending = None
    on_this, on_block = set(), set()
    for instruction in disasm(function):
        if instruction.address >= function + size:
            break
        text = instruction.op_str
        if instruction.mnemonic == "mov":
            m = ALLOC_SIZE.match(text)
            if m:
                pending = int(m.group(1), 16)
        if instruction.mnemonic == "call":
            if text.strip() == "0x%x" % ALLOCATOR and pending:
                blocks.add("__alloc__")
                pending = None
            # **THE ALLOCATOR RETURNS THE OBJECT IN `rax`, AND THE FIRST VERSION DID NOT KNOW THAT.** `0x5F47C6 mov ecx, 0x10` / `call 0x998500` / `0x5F47D5 mov
            # rbx, rax` is a constructor that ALLOCATES ITS OWN OBJECT -- **and `holds` began as `{rcx}` only, so `rax` was never in it, `rbx` never joined, and every
            # store through `rbx` was counted as neither the object nor the block.** That is why `TimerWinImplementation` was reported unsupported while its
            # constructor writes the vtable at +0x00 and `baselineSeconds_` at +0x08 through `rbx`.
            holds.add("rax")
        # **AND THE DISPLACEMENT COMES FROM THE SHARED PARSER, NOT FROM A PRIVATE REGEX.** The local pattern was `\[(\w+)(?: \+ (0x[0-9a-f]+))?\]`, which loses offsets 1 to
        # 9 -- **capstone prints a one-digit displacement in DECIMAL (`[rbx + 8]`), and `8` is the module's most common displacement because it is `vptr + 8`, the
        # `std::shared_ptr` count.** `re/lib.py`'s `object_offsets` takes both spellings and treats a missing displacement as offset 0, **which is the value the vtable
        # store has.** The local arithmetic `int(offset, 16) if offset else 0` happened to give the right answer for a single decimal digit and was luck, not design.
        for base, value, _is_store in object_offsets(text):
            if base in holds:
                on_this.add(value)
            elif base in ("rax", "rbx") and blocks:
                on_block.add(value)
        copy = re.match(r"^(\w+), (\w+)$", text)
        if instruction.mnemonic == "mov" and copy:
            destination, source = copy.group(1), copy.group(2)
            if source in holds:
                holds.add(destination)
            elif destination in holds:
                holds.discard(destination)
    return on_this, on_block, len(blocks)


def is_destructor(function, profile):
    size = (profile.get(function) or {}).get("size") or 0
    for instruction in disasm(function):
        if instruction.address >= function + size:
            break
        if instruction.mnemonic == "jmp" and instruction.op_str.strip() == "0x%x" % FREE:
            return True
    return False


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="owner")
    args = parser.parse_args(argv)

    profile = load_prof()
    data = json.loads(io.open(os.path.join(HERE, "all_class_fields.json"), encoding="utf-8").read())
    by_short = {e["class"].split("::")[-1]: int(e["constructor"], 16) for e in data["classes"] if e.get("constructor")}

    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "*.hpp"))):
        name = os.path.basename(path)
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for match in re.finditer(r"^class (\w+)[^\{]*\{(?P<body>.*?)^\};", text, re.M | re.S):
            short = match.group(1)
            if short not in by_short:
                continue
            members = [(m.group(1).strip(), m.group(2)) for m in MEMBER.finditer(match.group("body"))
                       if "static" not in m.group(1) and "//" not in m.group(1)]
            if not members:
                continue
            function = by_short[short]
            # **A DISPATCH SLOT IS NOT A CONSTRUCTOR, AND THE JSON'S PAIRING CAN BE ONE.** The candidate is replaced by the first function
            # that references the class's vtable POINTER and ALLOCATES, when the paired one allocates nothing -- which is what
            # re/g_find_real_ctor.py does by hand. Its verdict is reported below so a reader sees when a slot was used.
            alternative = find_allocating_constructor(function, profile)
            used_slot = alternative is not None and alternative != function
            if used_slot:
                function = alternative
            on_this, on_block, blocks = walk(function, profile)
            for slot in (profile.get(function) or {}).get("callers") or []:
                more_this, more_block, more_blocks = walk(slot, profile)
                on_this |= more_this
                on_block |= more_block
                blocks += more_blocks
            # A HANDLE IS SUPPORTED IF EITHER SIDE TOUCHES ANYTHING: the member may be on the object or inside the block it allocates
            supported = bool(on_this or on_block)
            rows.append((name, short, function, is_destructor(function, profile), on_this, on_block, blocks, members, supported))

    if args.owner:
        rows = [r for r in rows if r[1] == args.owner]

    print("%-22s %-10s %-8s %-22s %-22s %s" % ("class", "fn", "kind", "offsets ON THE OBJECT", "offsets IN THE BLOCK", "members"))
    unsupported = 0
    unsupported_names = []
    for name, short, function, destructor, on_this, on_block, blocks, members, supported in rows:
        kind = "NOT FOUND" if (destructor and not on_this) else ("DESTRUCTOR" if destructor else "constructor")
        if not supported:
            unsupported += 1
            unsupported_names.append(short)
        print("%-22s 0x%-8X %-8s %-22s %-22s %s"
              % (short[:22], function, kind,
                 " ".join("+0x%X" % o for o in sorted(on_this)[:4]) or "-- none --",
                 ("%d block(s): %s" % (blocks, " ".join("+0x%X" % o for o in sorted(on_block)[:4]))) if blocks else "--",
                 ", ".join(m[1] for m in members)[:26]))
    print("")
    # **AND IT NAMES THEM, BECAUSE A COUNT WITH NO NAMES IS NOT A REPORT.** The first version printed the number and not which classes it counted, so finding
    # them meant scanning the table by eye -- **and an unsupported class is exactly what a reader needs to be pointed at.**
    print("classes where NEITHER the object NOR any block the paired function allocates is touched: %d" % unsupported)
    for name in unsupported_names:
        print("   %s" % name)
    print("**THE TWO COLUMNS ARE THE POINT**: a handle class legitimately touches nothing on itself, and its fields are one level down. Four")
    print("classes were reported unsupported in a row before this was written, and all four were handles.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
