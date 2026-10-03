# -*- coding: utf-8 -*-
"""For ONE carrier, print each field with the offset, `Order`'s name there, and the export that writes it.

**THIS IS THE RENAME TABLE, AND THE THIRD COLUMN IS THE ORACLE.** A field renamed to `Order`'s name is renamed to what the module's OWN export names it -- `flag22`
becomes `reorganizeBiggestPartNearOrigin` because `SetReorganizeBiggestPartNearOrigin` writes it, and that is a witness and not a guess.

**AND A FIELD WHOSE OFFSET `Order` DOES NOT NAME IS THE OTHER KIND OF FINDING**: it is a byte the port has instructions for and no name for, so it goes into `Order`
with the offset as its name -- which is what `field18` and `field1C` already are.
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
LAYOUT = os.path.join(ROOT, "lcns", "include", "lcns", "dll_layout.hpp")
MODEL = os.path.join(ROOT, "lcns", "include", "lcns", "model.hpp")


def order_fields():
    text = io.open(MODEL, encoding="utf-8", errors="replace").read()
    body = re.search(r"struct Order\s*\{(.*?)\n\};", text, re.S).group(1)
    out = {}
    for line in body.split("\n"):
        found = re.search(r"\+0x([0-9A-Fa-f]+)", line)
        field = re.match(r"\s*([\w:<>,\s\*&]+?)\s+(\w+)\s*(?:\[[^\]]*\])?\s*[;=]", line)
        if found and field:
            out[int(found.group(1), 16)] = (field.group(2), field.group(1).strip())
    return out


def carrier_fields(name):
    text = io.open(LAYOUT, encoding="utf-8", errors="replace").read()
    match = re.search(r"struct\s+%s\s*\{(.*?)\n\};" % re.escape(name), text, re.S)
    if not match:
        return []
    cursor = 0
    out = []
    for line in match.group(1).split("\n"):
        field = re.match(r"\s*([\w:<>,\s\*&]+?)\s+(\w+)\s*(?:\[([^\]]*)\])?\s*;", line)
        if not field:
            continue
        array = field.group(3)
        comment = re.search(r"\+0x([0-9A-Fa-f]+)", line)
        if comment:
            cursor = int(comment.group(1), 16)
        out.append((cursor, field.group(1).strip(), field.group(2), array))
        if array:
            cursor += int(array, 16) if array.startswith("0x") else int(array)
        else:
            cursor += {"unsigned char": 1, "char": 1, "bool": 1, "std::uint8_t": 1,
                       "std::uint16_t": 2, "std::int16_t": 2,
                       "std::uint32_t": 4, "std::int32_t": 4, "int": 4, "unsigned": 4,
                       "double": 8, "std::uint64_t": 8, "void*": 8}.get(field.group(1).strip(), 8)
    return out


def main():
    names = order_fields()
    targets = sys.argv[1:] or ["OptionFlagCarrier"]
    for target in targets:
        fields = carrier_fields(target)
        if not fields:
            print("=== %s NOT FOUND" % target)
            continue
        print("=== %s -- %d field(s)" % (target, len(fields)))
        print("   %-8s %-12s %-26s %-30s %s" % ("offset", "type", "field", "Order's name there", "the export"))
        text = io.open(LAYOUT, encoding="utf-8", errors="replace").read()
        for offset, type_name, field, _array in fields:
            order_field, order_type = names.get(offset, ("(unnamed)", "?"))
            # the export name from the field's own comment, if it has one
            comment = re.search(r"^[^\n]*\b%s\b[^\n]*$" % re.escape(field), text, re.M)
            export = ""
            if comment:
                found = re.search(r"(Set\w+|CNS_\w+|Get\w+)", comment.group(0))
                export = found.group(1) if found else ""
            flag = "" if order_field in ("(unnamed)", field) else "   <- RENAME"
            print("   +0x%-5X %-12s %-26s %-30s %s%s"
                  % (offset, type_name[:12], field, "%s (%s)" % (order_field, order_type), export[:30], flag))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
