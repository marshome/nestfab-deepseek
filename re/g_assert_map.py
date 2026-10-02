# -*- coding: utf-8 -*-
"""Map every assertion site in the module: which function, which line.

RE 0x60A620 has 680 callers. Every one of them names a LINE of source, and this project had never used a single one until the previous
round. This builds the whole map and groups it by function, so a routine's assertion lines become a skeleton of where its decisions are.

Usage: python g_assert_map.py [--top 20] [--function 0x1EE50]
Output: re/assert_map.json, and a summary by function.

A SELF-CHECK, per the rule, and this one is strong because the expected answer is already in the ledger: 0x526160 must give LINE 154 and
its twin 0x5266A0 must give 176. Both were read by hand in an earlier round and both are on record. If either is wrong the tool refuses.

ONLY THE LINE IS INDEXED, NOT THE FILE. The file name is assembled differently at different sites -- 0x526160 builds it by immediate
stores, 0x1EE50 calls 0x1B130 -- and a decoder for the second form is a larger job than this round needs. The line is the part that is
uniform, and seven lines in one routine already turned out to be a usable skeleton.
"""
import argparse
import collections
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

REPORTER = 0x60A620
DIRECT = re.compile(r"^0x([0-9a-f]+)$")
MOVE_IMM = re.compile(r"^([a-z0-9]+), (0x[0-9a-f]+)$")
LINE_REGS = ("edx", "r8d", "ecx", "r9d", "esi", "edi")


def line_at(body, index):
    """The last value written to a line register before the call, scanning backwards."""
    for back in range(index - 1, max(-1, index - 60), -1):
        previous = body[back]
        if previous.mnemonic not in ("mov", "movabs"):
            continue
        moved = MOVE_IMM.match(previous.op_str.strip())
        if not moved:
            continue
        register, value = moved.group(1), int(moved.group(2), 16)
        if register in LINE_REGS and value < 100000:
            return value
    return None


def sites_in(address, profile):
    size = (profile.get(address) or {}).get("size") or 0
    body = [i for i in disasm(address) if i.address < address + size]
    out = []
    for index, ins in enumerate(body):
        if ins.mnemonic != "call":
            continue
        match = DIRECT.match(ins.op_str.strip())
        if match and int(match.group(1), 16) == REPORTER:
            out.append((ins.address, line_at(body, index)))
    return out


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--function")
    args = parser.parse_args(argv)
    profile = load_prof()

    # ---- the self-check against two lines already in the ledger ---------------------------------------------------------
    length_lines = [line for _at, line in sites_in(0x526160, profile) if line is not None]
    height_lines = [line for _at, line in sites_in(0x5266A0, profile) if line is not None]
    print("SELF-CHECK: 0x526160 gives %s (must contain 154) and 0x5266A0 gives %s (must contain 176)"
          % (length_lines, height_lines))
    if 154 not in length_lines or 176 not in height_lines:
        print("REFUSING TO REPORT: the two lines already on record are not reproduced, so this map would be worthless.")
        return 2
    print("")

    if args.function:
        root = int(args.function, 16)
        sites = sites_in(root, profile)
        print("0x%X: %d site(s)" % (root, len(sites)))
        for at, line in sites:
            print("   0x%-8X  line %s" % (at, line))
        return 0

    # ---- every function that calls the reporter --------------------------------------------------------------------------
    callers = sorted(set((profile.get(REPORTER) or {}).get("callers") or []))
    per_function = {}
    total = 0
    for address in callers:
        sites = sites_in(address, profile)
        if sites:
            per_function[address] = sites
            total += len(sites)

    payload = {("0x%X" % a): [{"site": "0x%X" % at, "line": line} for at, line in sites]
               for a, sites in per_function.items()}
    with io.open(os.path.join(HERE, "assert_map.json"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"sites": payload}, indent=1, sort_keys=True))

    print("functions that call the reporter: %d" % len(callers))
    print("assertion sites decoded: %d" % total)
    print("")
    ranked = sorted(per_function.items(), key=lambda kv: -len(kv[1]))
    print("%-9s %-7s %s" % ("function", "sites", "lines"))
    for address, sites in ranked[:args.top]:
        lines = " ".join(str(line) for _at, line in sites if line is not None)
        print("0x%-7X %-7d %s" % (address, len(sites), lines[:96]))
    print("")
    print("A function with many sites is one whose decisions are guarded, so its lines are a skeleton of its logic. The lines are")
    print("source POSITIONS and not offsets: they say where in the source a belief is checked and nothing about the object layout.")
    print("")
    print("wrote re/assert_map.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
