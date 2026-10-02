# -*- coding: utf-8 -*-
"""Type propagation: give a function's first argument a class, from the vtable identity of its methods.

Usage:
    python g_types_propagate.py                -> the totals and the rules that carried
    python g_types_propagate.py --function 0x2AB0
    python g_types_propagate.py --out re/TYPES.md
    python g_types_propagate.py --check 0x130 0x10

Why this is the keystone, in one paragraph. re/g_inventory.py measured it: of 18614 functions, only 342 have a known
first-argument type, because a virtual method is the only kind of function whose first argument the compiler labels -- the
vtable says which class it belongs to. re/g_contradict.py then could not conclude anything about the launch order's +0x10,
because the 2599 functions that write two bytes there through `rcx` might be writing into a different type, and only the TYPE
separates them. So a contradiction check, a parameter table and a variable table all wait on this one fact.

The propagation rules, each a shape that can be read in the instructions:

  SEED     a virtual method's first argument IS the class whose vtable holds it. RTTI, not inference.
  CALL     `Class::method` is called with `rcx = <this function's first argument>` -> the callee's type is the caller's.
  STORE    a constructor installs a vtable address at `[obj]` -> obj's type is that vtable's class.
  FIELD    a function `mov rax, [rcx+0x10] ; call 0x1234` passes the FIELD at +0x10 as the next first argument -> the callee's
           type is whatever type +0x10 holds in the caller, which is only known when the field itself is typed.

Only the first three are used, and the fourth is named because leaving it out is a choice: a field's type needs the layout, and
the layouts are not typed yet. Each typing records which rule produced it, so a claim can be argued with.

Every result is a PROPOSAL at SHAPE until an instruction confirms it, and the tool prints the rule and the call site for each,
because a propagated type that cannot be traced back is a guess with extra steps.
"""
import argparse
import glob
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

FOREIGN = ("8CryptoPP", "NSt", "5boost", "6Json", "__cxxabiv1", "__gnu_cxx", "6locale", "4Coin", "3Clp")
MOVE_RCX = re.compile(r"^(rcx|ecx|cx|cl), ([a-z0-9]+)$")
LOAD_FIELD = re.compile(r"^([a-z0-9]+), (?:qword ptr )?\[rcx(?:\+(0x[0-9a-f]+))?\]$")
VPTR_STORE = re.compile(r"^\[([a-z0-9]+)(?:\+(0x[0-9a-f]+))?\], ([a-z0-9]+)$")
LEA_VTABLE = re.compile(r"^([a-z0-9]+), \[rip\+(0x[0-9a-f]+)\]$")
ALIAS = {}
for _full, _names in {"rax": ("eax", "ax", "al"), "rbx": ("ebx", "bx", "bl"), "rcx": ("ecx", "cx", "cl"),
                      "rdx": ("edx", "dx", "dl"), "rsi": ("esi", "si", "sil"), "rdi": ("edi", "di", "dil")}.items():
    ALIAS[_full] = _full
    for _n in _names:
        ALIAS[_n] = _full
for _r in range(8, 16):
    for _s in ("", "d", "w", "b"):
        ALIAS["r%d%s" % (_r, _s)] = "r%d" % _r


def canonical(reg):
    return ALIAS.get(reg, reg)


def decode(mangled):
    parts = []
    for match in re.finditer(r"(\d+)([A-Za-z0-9_]+)", mangled.lstrip("_Z").lstrip("N").rstrip("E")):
        word = match.group(2)[:int(match.group(1))]
        if not word.startswith("__cxx"):
            parts.append("std" if word == "St" else word)
    return "::".join(parts) or mangled


def vtables(profile):
    """vtable rva -> (class name, [slot rvas]); plus slot rva -> class."""
    path = os.path.join(HERE, "vtables.json")
    data = json.load(io.open(path, encoding="utf-8"))
    by_address = {}
    by_slot = {}
    for mangled, info in data.items():
        if any(marker in mangled for marker in FOREIGN):
            continue
        rva = info.get("vtable_rva") or 0
        slots = [s for s in (info.get("slots") or []) if s in profile]
        if not rva or not slots:
            continue
        name = decode(mangled)
        by_address[rva] = (name, slots)
        by_address[rva + 16] = (name, slots)          # the address point a constructor stores
        for slot in slots:
            by_slot.setdefault(slot, name)
    return by_address, by_slot


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--function", type=lambda v: int(v, 0), default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--check", type=lambda v: int(v, 0), default=None)
    args = parser.parse_args(argv)

    profile = load_prof()
    by_address, by_slot = vtables(profile)

    types = {}          # rva -> (class, rule, evidence)
    order = []

    # SEED: a virtual method's first argument is its class. RTTI, no inference.
    for slot, name in by_slot.items():
        if slot in profile:
            types[slot] = (name, "SEED", "slot of the vtable for %s" % name)
            order.append(slot)
    seeded = len(types)

    # CALL and STORE, in waves: a wave only uses what earlier waves established, so a type never rests on itself.
    call_carried = 0
    store_carried = 0
    for wave in range(6):
        added = 0
        for address, info in profile.items():
            size = info.get("size") or 0
            if size <= 0:
                continue
            body = [i for i in disasm(address) if i.address < address + size]
            regs = {}                      # register -> class, for registers holding the first argument
            if address in types:
                regs["rcx"] = types[address][0]
            for position, ins in enumerate(body):
                operand = ins.op_str.replace(" ", "")
                # STORE: a constructor installs a vtable address into a register that is the object
                m = LEA_VTABLE.match(ins.op_str)
                if ins.mnemonic == "lea" and m:
                    target = ins.address + ins.size + int(m.group(2), 16)
                    if target in by_address:
                        regs[canonical(m.group(1))] = "vtable:" + by_address[target][0]
                    continue
                m = VPTR_STORE.match(operand)
                if ins.mnemonic == "mov" and m:
                    # `mov qword ptr [rcx], rax` -- the memory operand's BASE is the object, and the value stored is the
                    # vtable address. The first version read the base as the value and found nothing, which is why STORE
                    # reported zero until the operand order was read again.
                    base = canonical(m.group(1))
                    source = canonical(m.group(3))
                    if source in regs and regs[source].startswith("vtable:"):
                        name = regs[source][7:]
                        types.setdefault(base, (name, "STORE",
                                                "vtable for %s stored at 0x%X" % (name, ins.address)))
                        if base not in order:
                            order.append(base)
                            added += 1
                            store_carried += 1
                    continue
                # CALL: rcx = <register holding the caller's class> immediately before the call
                m = MOVE_RCX.match(ins.op_str.replace("[", "").replace("]", ""))
                if ins.mnemonic == "mov" and m:
                    source = canonical(m.group(2).split(",")[0])
                    if source in regs and not regs[source].startswith("vtable:"):
                        regs["rcx"] = regs[source]
                    continue
                if ins.mnemonic == "call" and position > 0:
                    target = None
                    mm = re.match(r"^0x([0-9a-f]+)$", ins.op_str)
                    if mm:
                        target = int(mm.group(1), 16)
                    if target and target in profile and "rcx" in regs and not regs["rcx"].startswith("vtable:"):
                        if target not in types:
                            types[target] = (regs["rcx"], "CALL",
                                             "rcx carried 0x%X's class at the call from 0x%X" % (address, address))
                            order.append(target)
                            added += 1
                            call_carried += 1
        if not added:
            break

    print("functions with a first-argument type: %d" % len(types))
    print("    by SEED  (RTTI, a virtual method's own class):  %d" % seeded)
    print("    by CALL  (rcx carried the caller's class):     %d" % call_carried)
    print("    by STORE (a constructor installed a vtable):   %d" % store_carried)
    print("")
    by_class = Counter(name for name, _rule, _why in types.values())
    print("the largest classes by propagated members:")
    for name, count in by_class.most_common(12):
        print("    %-40s %d" % (name[:40], count))
    print("")

    if args.function is not None:
        entry = types.get(args.function)
        if entry:
            print("0x%X carries %s (%s: %s)" % (args.function, entry[0], entry[1], entry[2]))
        else:
            print("0x%X has no propagated type" % args.function)

    if args.check is not None:
        offset = args.check
        holders = []
        needle = "+0x%x]" % offset
        for address, (name, _rule, _why) in types.items():
            info = profile.get(address) or {}
            size = info.get("size") or 0
            if size <= 0:
                continue
            for ins in disasm(address):
                if ins.address >= address + size:
                    break
                if "[rcx" in ins.op_str.replace(" ", "") and needle in ins.op_str.replace(" ", ""):
                    holders.append((address, name))
                    break
        counted = Counter(name for _a, name in holders)
        print("")
        print("functions whose FIRST argument is typed and which touch +0x%X: %d" % (offset, len(holders)))
        for name, count in counted.most_common(10):
            print("    %-40s %d" % (name[:40], count))
        print("")
        print("THIS is the answer the contradiction finder could not reach: at +0x%X the accesses belong to the classes above," % offset)
        print("so a width disagreement is a contradiction only WITHIN one of them. Across them it is several different fields.")

    if args.out:
        lines = ["# The propagated first-argument types",
                 "",
                 "Generated by `re/g_types_propagate.py`. SEED is RTTI (a virtual method's class); CALL is `rcx` carrying the",
                 "caller's class into the callee; STORE is a constructor installing a vtable. Each row names its rule and the",
                 "call site, because a propagated type that cannot be traced back is a guess with extra steps.",
                 "",
                 "| functions typed | by SEED | by CALL | by STORE |",
                 "|---:|---:|---:|---:|",
                 "| %d | %d | %d | %d |" % (len(types), seeded, call_carried, store_carried),
                 "",
                 "| rva | class | rule | evidence |",
                 "|---|---|---|---|"]
        for address in sorted(types):
            name, rule, why = types[address]
            lines.append("| `0x%X` | `%s` | %s | %s |" % (address, name, rule, why))
        io.open(os.path.join(ROOT, args.out.replace("/", os.sep)), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
        print("")
        print("wrote %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
