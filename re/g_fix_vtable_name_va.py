# -*- coding: utf-8 -*-
"""Fix the probe: the pointers INSIDE the table are VIRTUAL ADDRESSES while the table's own base is given as an RVA.

**THE TWO CONVENTIONS MEET IN THIS ONE FUNCTION**, and mixing them is what the first version did:

  * `lib.u64(rva)` reads at an RVA, and `re/vtables.json` records `vtable_rva`, so **the table base is an RVA** -- that is why the first fix (subtracting
    `lib.IB`) made every target negative, and why the corrected one found the NULL at `+0x00`;
  * **but the words STORED IN the table are virtual addresses**, because the loader writes them after relocation -- the typeinfo pointers came out as
    `0x6BED7FE0` and `0x6BED8490`, which are `0x21...` past the image base `0x6B4C0000`.

**SO A STORED WORD MUST HAVE `lib.IB` SUBTRACTED BEFORE IT IS USED AS AN RVA**, which is the one step the first version omitted -- and that omission is why every
name came back "(the typeinfo did not resolve)" and every table reported zero slots.
"""
import io
import sys

TARGET = r"D:\Nesting\nestfab\re\g_vtable_name.py"

OLD = '''def describe(base_rva, recorded):
    if not (0 < base_rva < IMAGE_SIZE):
        return "0x%X is not an RVA in this image" % base_rva
    try:
        first = lib.u64(base_rva)
        typeinfo = lib.u64(base_rva + 8)
    except Exception as problem:                                   # noqa: BLE001 -- report, do not crash
        return "unreadable: %s" % problem
    lines = ["base 0x%X (rva 0x%X)" % (base_rva + lib.IB, base_rva),
             "   [base + 0x00] = 0x%X  %s" % (first, "NULL, as a base must be" if first == 0 else "**NOT NULL**")]
    if not typeinfo:
        lines.append("   [base + 0x08] = 0")
        return "\\n".join(lines)
    name = name_at(typeinfo)
    lines.append("   [base + 0x08] = 0x%X  ->  %s" % (typeinfo, name if name else "(the typeinfo did not resolve)"))
    slots = []
    for index in range(32):
        try:
            word = lib.u64(base_rva + 0x10 + index * 8)
        except Exception:                                          # noqa: BLE001
            break
        if not (0 < word < IMAGE_SIZE):
            break
        slots.append(word)
    lines.append("   %d slot(s), each an RVA: %s" % (len(slots), ", ".join("0x%X" % word for word in slots[:8])))
    known = recorded.get(base_rva + lib.IB)
    lines.append("   recorded in re/vtables.json as: %s" % (", ".join(known) if known else "NOT RECORDED"))
    return "\\n".join(lines)'''

NEW = '''def as_rva(stored_word):
    """**A WORD STORED IN A TABLE IS A VIRTUAL ADDRESS.** The loader writes absolute pointers after relocation, so a slot holds `IB + rva` and the image base
    comes off before the value can be read or looked up. Returning None keeps "not a pointer" distinct from "points at zero"."""
    if stored_word == 0:
        return 0
    if lib.IB <= stored_word < lib.IB + IMAGE_SIZE:
        return stored_word - lib.IB
    if 0 < stored_word < IMAGE_SIZE:
        return stored_word                     # already an RVA, which some tables hold before relocation
    return None


def describe(base_rva, recorded):
    if not (0 < base_rva < IMAGE_SIZE):
        return "0x%X is not an RVA in this image" % base_rva
    try:
        first = lib.u64(base_rva)
        raw_typeinfo = lib.u64(base_rva + 8)
    except Exception as problem:                                   # noqa: BLE001 -- report, do not crash
        return "unreadable: %s" % problem
    lines = ["base 0x%X (rva 0x%X)" % (base_rva + lib.IB, base_rva),
             "   [base + 0x00] = 0x%X  %s" % (first, "NULL, as a base must be" if first == 0 else "**NOT NULL**")]
    if not raw_typeinfo:
        lines.append("   [base + 0x08] = 0")
        return "\\n".join(lines)
    typeinfo_rva = as_rva(raw_typeinfo)
    if typeinfo_rva is None:
        lines.append("   [base + 0x08] = 0x%X, which is neither an RVA nor a virtual address in this image" % raw_typeinfo)
        return "\\n".join(lines)
    name = name_at(typeinfo_rva)
    lines.append("   [base + 0x08] = 0x%X (rva 0x%X)  ->  %s"
                 % (raw_typeinfo, typeinfo_rva, name if name else "(the typeinfo did not resolve)"))
    slots = []
    for index in range(48):
        try:
            word = lib.u64(base_rva + 0x10 + index * 8)
        except Exception:                                          # noqa: BLE001
            break
        rva = as_rva(word)
        if rva is None:
            break
        slots.append(rva)
    lines.append("   %d slot(s): %s" % (len(slots), ", ".join("0x%X" % word for word in slots[:8])))
    known = recorded.get(base_rva + lib.IB)
    lines.append("   recorded in re/vtables.json as: %s" % (", ".join(known) if known else "NOT RECORDED"))
    return "\\n".join(lines)'''


def main():
    text = io.open(TARGET, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "def as_rva" in text:
        print("the virtual-address step is already there")
        return 0
    if OLD not in text:
        print("REFUSING: the describe function is not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(text)
    print("g_vtable_name.py: stored words are now converted from virtual addresses to RVAs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
