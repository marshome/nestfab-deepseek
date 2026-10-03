#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Find a class's REAL constructor: the function that installs its vtable AND allocates, or is called from a factory.

THE MISTAKE THIS CORRECTS, and it is the newest instance of the oldest one in this session: `re/g_all_class_fields.json` pairs a class with "the
candidate that writes the most fields", and the candidate is found by ANY function that references the vtable's slot-0 ADDRESS -- which a
destructor does too. **The pairing was never checked, and `Engine::InfiniteEngine` was paired with 0x24FD0, which is not its constructor at
all**: that function allocates a 0x30 byte object and a 0x18 byte object and stores them at its own +0 and +8, so it is a factory for some
OTHER class.

WHAT THIS DOES INSTEAD: for a given class, list every function that installs the class's vtable, with the EVIDENCE for each --
    * does it allocate (a `mov ecx, N` before a call to the allocator at 0x998500)?
    * does it store to [this + 0] where `this` came from rcx and never moved?
    * does it tail call the allocator (a destructor does)?
and the class's own vtable slots are read from re/vtables.json, so a slot's meaning is available where the slot's code says so.

    python -u g_find_real_ctor.py --class Engine::InfiniteEngine
"""
import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import disasm, load_prof, rip_targets  # noqa: E402

ALLOCATOR = 0x998500
FREE = 0x9984B0
STORE = re.compile(r"^(byte|word|dword|qword) ptr \[(\w+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\], (.+)$")


def evidence(function, profile):
    size = (profile.get(function) or {}).get("size") or 0
    if not size:
        return None
    holds = {"rcx"}
    out = {"allocates": [], "stores_to_this": [], "tails_to_free": None, "virtual_calls": 0, "size": size}
    pending_size = None
    for instruction in disasm(function):
        if instruction.address >= function + size:
            break
        text = instruction.op_str
        if instruction.mnemonic == "mov" and re.match(r"^ecx, 0x[0-9a-f]+$", text):
            pending_size = int(text.split(",")[1].strip(), 16)
        if instruction.mnemonic == "call":
            target = text.strip()
            if target == "0x%x" % ALLOCATOR and pending_size:
                out["allocates"].append((instruction.address, pending_size))
                pending_size = None
        if instruction.mnemonic == "jmp" and text.strip() == "0x%x" % FREE:
            out["tails_to_free"] = instruction.address
        if instruction.mnemonic == "call" and text.startswith("qword ptr [") and "+ 0x10]" in text:
            out["virtual_calls"] += 1
        match = STORE.match(text)
        if match:
            base, offset = match.group(2), match.group(3)
            if base in holds:
                out["stores_to_this"].append((instruction.address, int(offset, 16) if offset else 0, match.group(1)))
            continue
        copy = re.match(r"^(\w+), (\w+)$", text)
        if instruction.mnemonic == "mov" and copy:
            destination, source = copy.group(1), copy.group(2)
            if source in holds:
                holds.add(destination)
            elif destination in holds:
                holds.discard(destination)
    return out


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="owner", required=True)
    args = parser.parse_args(argv)

    profile = load_prof()
    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    entry = None
    for mangled, value in data.items():
        if (value.get("demangled") or "").strip() == args.owner:
            entry = value
            break
    if entry is None:
        print("no RTTI entry for %s" % args.owner)
        return 2

    base = int(entry["vtable_rva"])
    slot0 = base + 0x10
    print("%s, vtable 0x%X, %d slots" % (args.owner, base, len(entry["slots"])))
    for index, address in enumerate(entry["slots"]):
        info = profile.get(address) or {}
        print("   slot %d  0x%-8X %5s bytes  %d callers" % (index, address, info.get("size"), len(set(info.get("callers") or []))))
    print("")
    print("functions that reference the slot-0 ADDRESS 0x%X, with their evidence:" % slot0)
    found = []
    for address, info in profile.items():
        if not info.get("size"):
            continue
        if slot0 in rip_targets(address):
            found.append(address)
    for address in sorted(found):
        detail = evidence(address, profile)
        if detail is None:
            continue
        verdict = []
        if detail["allocates"]:
            verdict.append("ALLOCATES %s" % ", ".join("0x%X bytes at 0x%X" % (n, a) for a, n in detail["allocates"]))
        if detail["tails_to_free"]:
            verdict.append("TAIL CALLS free at 0x%X -> a DESTRUCTOR" % detail["tails_to_free"])
        if any(offset == 0 for _a, offset, _w in detail["stores_to_this"]):
            verdict.append("stores to [this+0]")
        if not verdict:
            verdict = ["no allocation, no free, no store to +0"]
        print("   0x%-8X %5d bytes  %s" % (address, detail["size"], "; ".join(verdict)))
        for site, offset, width in detail["stores_to_this"][:6]:
            print("        +0x%-4X %-6s at 0x%X" % (offset, width, site))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
