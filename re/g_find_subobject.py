# -*- coding: utf-8 -*-
"""Find the functions that derive the address of a sub-object at +0x40, and look for a constructor among them.

re/ledger.json carries a SHAPE claim: "parent+0x40.subobject -- a sub-object with fields +0x10..+0x38, 15 functions derive its address
with lea, no constructor read". To promote it to a layout this project needs a CONSTRUCTOR, and this finds the candidate set.

    python g_find_subobject.py 0x40

What it reports, per function that takes the address:
  * the size and caller count, which says whether it is big enough to be a constructor;
  * whether it STORES into +0x40's own fields, which a constructor does and a reader does not;
  * the offsets it touches inside the sub-object, so the two sets can be told apart.

A SELF-CHECK, per the rule: the ledger claims FIFTEEN functions derive the address. If this finds fewer than five, it says so and
refuses, because a search that cannot reproduce the number already on record is not a search to act on.
"""
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

EXPECTED_DERIVATIONS = 15
LEA = re.compile(r"^[a-z0-9]+, \[([a-z0-9]+) \+ (0x[0-9a-f]+)\]$")
ACCESS = re.compile(r"\[([a-z0-9]+)(?:\s*\+\s*(0x[0-9a-f]+))?\]")
STORE = re.compile(r"^\[([a-z0-9]+)(?:\s*\+\s*(0x[0-9a-f]+))?\], ")


def main(argv):
    sub_offset = int(argv[0], 0) if argv else 0x40
    profile = load_prof()

    derivations = collections.defaultdict(list)
    for address, info in profile.items():
        size = info.get("size") or 0
        if not (20 <= size <= 8000):
            continue
        try:
            body = [i for i in disasm(address) if i.address < address + size]
        except Exception:
            continue
        for index, ins in enumerate(body):
            if ins.mnemonic != "lea":
                continue
            match = LEA.match(ins.op_str.strip())
            if not match or int(match.group(2), 16) != sub_offset:
                continue
            base = match.group(1)
            # the destination register, and then the offsets reached through it
            destination = ins.op_str.strip().split(",")[0]
            reached = set()
            stores = set()
            for later in body[index + 1:index + 40]:
                text = later.op_str.replace(" ", "")
                for hit in ACCESS.finditer(later.op_str.replace(" ", "")):
                    if hit.group(1) == destination and hit.group(2):
                        reached.add(int(hit.group(2), 16))
                store = STORE.match(later.op_str.replace(" ", "") + ",") if False else None
                m = re.match(r"^\[([a-z0-9]+)(?:\+(0x[0-9a-f]+))?\],", later.op_str.replace(" ", ""))
                if later.mnemonic == "mov" and m and m.group(1) == destination and m.group(2):
                    stores.add(int(m.group(2), 16))
            derivations[address].append((ins.address, base, sorted(reached), sorted(stores)))

    print("the ledger records %d functions deriving the address; this found %d" % (EXPECTED_DERIVATIONS, len(derivations)))
    if len(derivations) < 5:
        print("REFUSING: fewer than five is not the fifteen on record, so this search is not reproducing the claim.")
        return 2
    print("")
    print("%-9s %-6s %-7s %-9s %s" % ("function", "bytes", "callers", "stores?", "offsets reached through the destination"))
    ranked = sorted(derivations.items(), key=lambda kv: -len(kv[1][0][3]))
    for address, hits in ranked[:16]:
        info = profile.get(address) or {}
        at, base, reached, stores = hits[0]
        print("0x%-7X %-6d %-7d %-9s %s"
              % (address, info.get("size") or 0, len(set(info.get("callers") or [])),
                 "YES" if stores else "no", " ".join("+0x%X" % o for o in reached[:10])))
    print("")
    print("A function that STORES into the sub-object's fields is a candidate constructor; one that only reads is a user. That is the")
    print("distinction this project needs, because a layout requires a constructor and not a shape that matches.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
