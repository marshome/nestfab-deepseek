# -*- coding: utf-8 -*-
"""Exclude the PADDING members from the union and the duplicate check -- they are not fields.

**WHAT THE MEASUREMENT ACTUALLY FOUND, WHICH THE TOOLS WERE HIDING.** `re/g_order_union.py` reported "15 offsets only `Order` has", and reading them settles
that **13 are `std::byte paddingNN` declarations the permutation inserted**, whose `+0xNNN` comments the field regex happily matched:

    +0x45  padding05    +0x49  padding06    +0x59  padding07    +0x64  padding08    +0x7C  padding09
    +0xA9  padding12    +0xC4  padding13    +0xE9  padding15    +0x199 padding19    +0x1A1 padding20
    +0x1B9 padding21    +0x201 padding23    +0x241 padding24

**and only TWO are real**: `maxIterations` at +0x1FC and `localEngine` at +0x200.

**SO THREE NUMBERS THIS PROJECT HAS BEEN QUOTING WERE INFLATED BY PADDING**, and the same omission explains `re/g_one_definition.py` reporting 68 shared
offsets where the union tool reports 67: it reads the layout the same way but `Order` differently, and padding counted on one side and not the other. **A
padding member is not a field**, and a tool that counts it is reporting the tool's own scaffolding as the module's structure.

    python -u g_exclude_padding.py
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

RULE = ('# **AND THE PADDING IS NOT A FIELD.** The permutation inserts `std::byte paddingNN[...]` members to force the next field onto its offset, and those\n'
        '# declarations carry a `+0xNNN` comment -- so a field regex matches them and counts the tool\'s own scaffolding as the module\'s structure. **Thirteen of\n'
        '# the "15 offsets only Order has" were padding**, and the same omission made `re/g_one_definition.py` report 68 shared offsets where this tool reports\n'
        '# 67. A member whose type is `std::byte`, whose name begins with `padding` and whose width is zero is not a field.\n'
        'NOT_A_FIELD = re.compile(r"^padding\\d*$")\n')


def patch(path, marker):
    text = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "NOT_A_FIELD" in text:
        print("   %s already excludes padding" % os.path.basename(path))
        return True
    if marker not in text:
        print("   REFUSING: the anchor is not in %s" % os.path.basename(path))
        return False
    text = text.replace(marker, RULE + marker, 1)
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)
    print("   %s now excludes padding" % os.path.basename(path))
    return True


def main():
    ok = patch(os.path.join(HERE, "g_order_union.py"), "FIELD = re.compile(")
    ok = patch(os.path.join(HERE, "g_one_definition.py"), "FIELD = re.compile(") and ok

    # and the filter itself, at the one place each tool builds its offset map
    for name, old, new in (
        ("g_order_union.py",
         '        for ftype, fname, array, offset in FIELD.findall(match.group("body")):\n',
         '        for ftype, fname, array, offset in FIELD.findall(match.group("body")):\n'
         '            if NOT_A_FIELD.match(fname):\n'
         '                continue          # **PADDING IS NOT A FIELD**, see the note at NOT_A_FIELD\n'),
        ("g_one_definition.py",
         '            for field, offset in found:\n',
         '            for field, offset in found:\n'
         '                if NOT_A_FIELD.match(field):\n'
         '                    continue      # **PADDING IS NOT A FIELD**, see the note at NOT_A_FIELD\n'),
    ):
        path = os.path.join(HERE, name)
        text = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        if "PADDING IS NOT A FIELD" in text:
            print("   %s already filters" % name)
            continue
        if old not in text:
            print("   REFUSING: the map site is not in %s" % name)
            ok = False
            continue
        text = text.replace(old, new, 1)
        io.open(path, "w", encoding="utf-8", newline="\n").write(text)
        print("   %s now filters the padding out" % name)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
