# -*- coding: utf-8 -*-
"""Which declaration is right, decided by the module's own store instructions at each disputed offset.

Order and LaunchingOrderLayout declare the same object and disagree about 21 offsets' widths. A similarity score cannot say
which is right and neither can seniority, so this asks the only authority there is: the instruction that writes the field.

Two sources, in order of strength:

  the constructor  RE 0x14620 writes every field of the object, so its store widths are the object's true widths;
  the setters       the exports the ledger names, whose stores are quoted there.

For each disputed offset this prints the width the module uses, the address of the instruction, and what each declaration
claims. The verdict per row is mechanical: whichever declaration matches the module is right, and a declaration that is wider
than the module's store misplaces every field after it in a packed view.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

WIDTHS = {"byte": 1, "word": 2, "dword": 4, "qword": 8, "xmmword": 16}
STORE = re.compile(r"(byte|word|dword|qword|xmmword) ptr \[r[a-z0-9]+(?: \+ 0x([0-9a-f]+))?\]")

# The functions whose stores are this object's, with the evidence for each: the constructor and the nine setters the ledger
# carries at ORACLE or INSTRUCTION.
WRITERS = [
    (0x14620, "NewLaunchingOrder, the constructor"),
    (0xD050, "SetOrigin (86)"),
    (0xD1A0, "CNS_SetMultiplicityPreference (128)"),
    (0xE010, "SetAutomaticStop (140)"),
    (0xEC90, "SetCommonCutCuttingPreference (154)"),
    (0xE940, "SetCommonCutSafetyPreference (150)"),
    (0xF130, "SetMultiTorchCuttingPreference (176)"),
    (0x13E30, "SetSpecificSheetOrigin (298)"),
    (0x13FE0, "SetSpecificSheetObjective (300)"),
    (0x188D0, "SetMarkMode (246)"),
]

DISPUTED = [0x18, 0x20, 0x38, 0x44, 0x48, 0x58, 0x5C, 0x60, 0x68, 0x70, 0x84, 0x85, 0x88, 0x98,
            0xA8, 0xC0, 0xD0, 0xE8, 0x1A0, 0x1B8, 0x240]


def module_widths(profile):
    """offset -> (width, address, which writer)."""
    out = {}
    for address, label in WRITERS:
        size = (profile.get(address) or {}).get("size") or 0
        if size <= 0:
            continue
        for ins in disasm(address):
            if ins.address >= address + size:
                break
            m = STORE.search(ins.op_str)
            if not m:
                continue
            width = WIDTHS.get(m.group(1))
            offset = int(m.group(2), 16) if m.group(2) else 0
            if width and (offset not in out or width < out[offset][0]):
                # the NARROWEST store is the field's width: a wide store over a byte flag is the compiler writing a
                # neighbouring group, and the narrowest observation constrains the field hardest
                out[offset] = (width, ins.address, label)
    return out


def declarations(path, type_name):
    text = io.open(os.path.join(ROOT, path), encoding="utf-8", errors="replace").read()
    fields = {}
    current = None
    for number, line in enumerate(text.split("\n"), 1):
        m = re.match(r"\s*(?:struct|class)\s+(\w+)", line)
        if m:
            current = m.group(1)
            continue
        if current != type_name:
            continue
        f = re.match(r"\s*((?:std::)?(?:u?int\d+_t|int|long|short|char|float|double|bool|size_t|std::size_t|"
                     r"unsigned\s+char|unsigned\s+int|void\s*\*|[A-Z]\w*(?:::\w+)*)(?:\s*\*)?)\s+"
                     r"([A-Za-z_]\w*)\s*(?:\[\s*(\d+)\s*\])?\s*(?:=[^;]*)?;\s*(?://\s*(.*))?$", line)
        if not f:
            continue
        comment = f.group(4) or ""
        o = re.search(r"\+0x([0-9A-Fa-f]+)", comment)
        if not o:
            continue
        sizes = {"char": 1, "bool": 1, "unsigned char": 1, "std::uint8_t": 1, "uint8_t": 1, "short": 2,
                 "unsigned short": 2, "std::uint16_t": 2, "uint16_t": 2, "int": 4, "unsigned int": 4, "float": 4,
                 "std::uint32_t": 4, "uint32_t": 4, "double": 8, "long long": 8, "std::uint64_t": 8,
                 "uint64_t": 8, "size_t": 8, "std::size_t": 8, "long": 4}
        width = 8 if "*" in f.group(1) else sizes.get(f.group(1).strip())
        if f.group(3) and width:
            width *= int(f.group(3))
        fields[int(o.group(1), 16)] = (f.group(2), f.group(1).strip(), width, number)
    return fields


def main():
    profile = load_prof()
    widths = module_widths(profile)
    left = declarations("lcns/include/lcns/model.hpp", "Order")
    right = declarations("lcns/include/lcns/launching_order.hpp", "LaunchingOrderLayout")

    print("offset  the module    at         Order                          LaunchingOrderLayout            verdict")
    agree_right = agree_left = neither = no_evidence = 0
    for offset in DISPUTED:
        evidence = widths.get(offset)
        a = left.get(offset)
        b = right.get(offset)
        a_text = ("%s %s (%s)" % (a[1], a[0], a[2] or "?")) if a else "-"
        b_text = ("%s %s (%s)" % (b[1], b[0], b[2] or "?")) if b else "-"
        if evidence:
            module_text = "%d B" % evidence[0]
            at_text = "0x%X" % evidence[1]
            matched_right = b and b[2] == evidence[0]
            matched_left = a and a[2] == evidence[0]
            if matched_right and not matched_left:
                verdict = "Layout is right"
                agree_right += 1
            elif matched_left and not matched_right:
                verdict = "Order is right"
                agree_left += 1
            elif matched_left and matched_right:
                verdict = "both agree with the module"
            else:
                verdict = "NEITHER matches"
                neither += 1
        else:
            module_text = "-"
            at_text = "-"
            verdict = "no store found"
            no_evidence += 1
        print("+0x%-4X %-13s %-10s %-30s %-30s %s" % (offset, module_text, at_text, a_text, b_text, verdict))
    print("")
    print("the module settles it: LaunchingOrderLayout %d, Order %d, neither %d, and %d offsets have no store to consult"
          % (agree_right, agree_left, neither, no_evidence))
    return 0


if __name__ == "__main__":
    sys.exit(main())
