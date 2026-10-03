# -*- coding: utf-8 -*-
"""Every ad-hoc "carrier" struct in the port, and which offsets of the module's object each one re-describes.

**THIS IS THE OBJECTIVE'S "SECOND DESCRIPTION OF A CLASS", MEASURED.** The module has ONE object, and `lcns/include/lcns/model.hpp`'s `Order` describes it with
names taken from the exports. Beside it sit `OptionFlagCarrier`, `IntFieldCarrier`, `LocalEngineCarrier`, `UnknownFlagCarrier`, `SolverOptionCarrier` and more --
each declaring the same offsets again, often with a name that is its position (`field44`, `field1FC`) or a guess (`UnknownFlagCarrier`).

**AND THEY ARE NOT ALL ALIKE**, which is why this measures before proposing anything: a carrier whose fields are NAMED and whose offsets match `Order`'s is a
duplicate; one that describes bytes `Order` does not carry is a gap that `Order` should absorb.
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


def main():
    layout = io.open(os.path.join(ROOT, "lcns", "include", "lcns", "dll_layout.hpp"), encoding="utf-8", errors="replace").read()
    model = io.open(os.path.join(ROOT, "lcns", "include", "lcns", "model.hpp"), encoding="utf-8", errors="replace").read()

    # every `struct X { ... };` in dll_layout.hpp
    carriers = []
    for match in re.finditer(r"struct\s+(\w+)\s*\{(.*?)\n\};", layout, re.S):
        name, body = match.group(1), match.group(2)
        offsets = []
        cursor = 0
        for line in body.split("\n"):
            field = re.match(r"\s*[\w:<>,\s\*&]+?\s+(\w+)\s*(?:\[([^\]]*)\])?\s*;", line)
            if not field:
                continue
            array = field.group(2)
            comment = re.search(r"\+0x([0-9A-Fa-f]+)", line)
            if comment:
                cursor = int(comment.group(1), 16)
            offsets.append((cursor, field.group(1), array))
            size = None
            if array:
                size = int(array, 16) if array.startswith("0x") else int(array)
            cursor += 8 if size is None else size
        carriers.append((name, offsets))

    # Order's named offsets
    order_offsets = {}
    for line in model.split("\n"):
        found = re.search(r"\+0x([0-9A-Fa-f]+)", line)
        if not found:
            continue
        field = re.match(r"\s*[\w:<>,\s\*&]+?\s+(\w+)\s*(?:\[[^\]]*\])?\s*[;=]", line)
        if field:
            order_offsets[int(found.group(1), 16)] = field.group(1)

    print("carrier structs in dll_layout.hpp: %d" % len(carriers))
    print("named offsets in Order:            %d" % len(order_offsets))
    print("")
    for name, offsets in carriers:
        if not offsets:
            continue
        shared = [o for o, _f, _a in offsets if o in order_offsets]
        positional = [f for _o, f, _a in offsets if re.match(r"^(field|opaque|unnamed|unknown)[0-9A-Fa-f]*$", f)]
        print("%-26s %2d field(s), %2d offset(s) that Order also names%s"
              % (name, len(offsets), len(shared),
                 ",  %d position-named field(s)" % len(positional) if positional else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
