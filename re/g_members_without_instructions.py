# -*- coding: utf-8 -*-
"""Make the support audit count READS as well as writes, and treat a constructor that was NOT found as a separate verdict.

TWO DEFECTS IN THE AUDIT, both found by running it on a class that had just been corrected:

  1. IT ONLY COUNTED WRITES. `BestObserver::sink_` at +0x10 IS placed by an instruction -- `0x755A40 mov rcx, [rcx + 0x10]` READS it and jumps
     into its vtable -- and the audit called the class unsupported because its constructor is a destructor pair that only writes the vtable.
     **A member proven by a read is as supported as one proven by a write**, and the tool was reporting the class as one of the seven.
  2. IT DID NOT SEPARATE "the constructor was not found" FROM "the constructor does not place them". Those are different findings: the first is a
     gap in the scan, the second is a defect in the declaration. `re/g_find_real_ctor.py` decides which.

    python g_members_without_instructions.py [--class X]
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

from lib import disasm, load_prof  # noqa: E402

FREE = 0x9984B0
ACCESS = re.compile(r"\[(\w+)(?: \+ (0x[0-9a-f]+))?\]")
MEMBER = re.compile(r"^ {4,}([\w:<>,\s\*&]+?)\s+(\w+)\s*(?:\{\})?\s*(?:=\s*[^;]*)?;", re.M)


def is_destructor(function, profile):
    size = (profile.get(function) or {}).get("size") or 0
    for instruction in disasm(function):
        if instruction.address >= function + size:
            break
        if instruction.mnemonic == "jmp" and instruction.op_str.strip() == "0x%x" % FREE:
            return True
    return False


def accessed_offsets(function, profile):
    """Every offset touched through a register loaded from rcx, read OR written -- because a read places a member too."""
    size = (profile.get(function) or {}).get("size") or 0
    if not size:
        return set()
    holds = {"rcx"}
    offsets = set()
    for instruction in disasm(function):
        if instruction.address >= function + size:
            break
        for match in ACCESS.finditer(instruction.op_str):
            if match.group(1) in holds and match.group(2):
                offsets.add(int(match.group(2), 16))
        copy = re.match(r"^(\w+), (\w+)$", instruction.op_str)
        if instruction.mnemonic == "mov" and copy:
            destination, source = copy.group(1), copy.group(2)
            if source in holds:
                holds.add(destination)
            elif destination in holds:
                holds.discard(destination)
    return offsets


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
            members = [(m.group(1).strip(), m.group(2)) for m in MEMBER.finditer(match.group("body")) if "static" not in m.group(1)]
            if not members:
                continue
            function = by_short[short]
            offsets = accessed_offsets(function, profile)
            # AND THE CLASS'S OWN SLOTS, because a forwarder proves a member its constructor never touches
            for slot in (profile.get(function) or {}).get("callers") or []:
                offsets |= accessed_offsets(slot, profile)
            rows.append((name, short, function, is_destructor(function, profile), offsets, members))

    if args.owner:
        rows = [r for r in rows if r[1] == args.owner]

    print("%-22s %-16s %-10s %-9s %-12s %s" % ("class", "header", "fn", "kind", "offsets seen", "declared members"))
    unsupported = 0
    for name, short, function, destructor, offsets, members in rows:
        kind = "DESTRUCTOR" if destructor else "constructor"
        if not offsets and destructor:
            kind = "NOT FOUND"
        if not offsets:
            unsupported += 1
        print("%-22s %-16s 0x%-8X %-9s %-12s %s"
              % (short[:22], name[:16], function, kind,
                 " ".join("+0x%X" % o for o in sorted(offsets)[:4]) or "-- none --",
                 ", ".join(m[1] for m in members)[:36]))
    print("")
    print("classes where NO offset of the object is touched by the function the field scan paired with them, nor by its callers: %d" % unsupported)
    print("**AND `NOT FOUND` IS A DIFFERENT FINDING FROM AN UNSUPPORTED MEMBER**: it means the scan did not locate the class's constructor, so")
    print("nothing can be concluded about the members either way. re/g_find_real_ctor.py settles which case a class is in.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
