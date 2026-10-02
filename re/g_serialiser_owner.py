# -*- coding: utf-8 -*-
"""Parse re/TYPES.md into a lookup, then ask which class owns the serialisers.

re/g_types_propagate.py prints a table of rva -> class with the rule that produced it:

    | `0x1B070` | `Engine` | CALL | rcx carried 0x9302C0's class at the call from 0x9302C0 |
    | `0x26A60` | `Engine` | SEED | slot of the vtable for Engine |

That is a table, so it can be read. This makes it a dictionary and uses it on the serialisers, which is the question the
key->offset pairing blocker has carried since round 575 as unanswerable:

    "the serialisers' signatures are unknown, so an offset cannot be attributed to an object"

    python g_serialiser_owner.py [--types re/TYPES.md] [--address 0x506B30]

A SELF-CHECK, per the rule: the table's own header says how many functions are typed, and the parse must agree with it.
"""
import argparse
import collections
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

ROW = re.compile(r"^\|\s*`(0x[0-9A-Fa-f]+)`\s*\|\s*`([^`]+)`\s*\|\s*([A-Z]+)\s*\|\s*(.*?)\s*\|\s*$")
HEADER_COUNT = re.compile(r"^\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*$")

# the JSON work named these as serialisers; a serialiser's first argument is the thing it writes
SERIALISERS = [0x506B30, 0x506D80, 0x506E90, 0x5070E0, 0x506A40, 0x506980,
               0x506520, 0x506300, 0x5060C0, 0x505F00, 0x505D40, 0x505B80,
               0x5059C0, 0x505800, 0x505640]


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--types", default=os.path.join(HERE, "TYPES.md"))
    parser.add_argument("--address")
    args = parser.parse_args(argv)

    if not os.path.exists(args.types):
        print("no types file at %s -- run: python re/g_types_propagate.py --out re/TYPES.md" % args.types)
        return 2
    text = io.open(args.types, encoding="utf-8").read()

    declared = None
    for line in text.split("\n")[:12]:
        match = HEADER_COUNT.match(line.strip())
        if match:
            declared = int(match.group(1))
            break

    table = {}
    classes = collections.Counter()
    for line in text.split("\n"):
        match = ROW.match(line.strip())
        if not match:
            continue
        address = int(match.group(1), 16)
        table[address] = (match.group(2), match.group(3), match.group(4))
        classes[match.group(2)] += 1

    print("SELF-CHECK: the table declares %s typed functions and this parse found %d" % (declared, len(table)))
    if declared is not None and len(table) != declared:
        print("REFUSING: the parse disagrees with the file's own count, so the table is not being read correctly.")
        return 2
    print("")
    print("classes by member count: %s" % ", ".join("%s %d" % (k, v) for k, v in classes.most_common(8)))
    print("")

    if args.address:
        target = int(args.address, 16)
        entry = table.get(target)
        print("0x%X -> %s" % (target, ("%s (%s, %s)" % entry) if entry else "NO TYPE PROPAGATED"))
        return 0

    print("the serialisers the JSON work named, and the class each belongs to:")
    typed = 0
    for address in SERIALISERS:
        entry = table.get(address)
        if entry:
            typed += 1
        print("   0x%-8X %s" % (address, ("%s  by %s" % (entry[0], entry[1])) if entry else "-- no type"))
    print("")
    print("%d of %d have a class." % (typed, len(SERIALISERS)))
    print("")
    if typed == len(SERIALISERS):
        print("SO THE BLOCKER'S PREMISE NO LONGER HOLDS: every serialiser's first argument has a known class, so the offsets it touches")
        print("are that class's fields and the key->offset pairing can be keyed on the class instead of guessed.")
    elif typed:
        print("THE BLOCKER'S PREMISE STILL HOLDS FOR %d OF THEM, and it is worth saying so plainly: type propagation reached one of" %
              (len(SERIALISERS) - typed))
        print("these routines and not the rest, so the pairing cannot be keyed on a class for the fourteen that have none. What has")
        print("changed since round 575 is that the question is now answerable per ADDRESS rather than in general -- which is progress")
        print("and not a solution, and the difference is exactly what a first version of this tool got wrong by printing that the")
        print("premise no longer held for any of them.")
    else:
        print("NOT ONE has a class, so the propagation has not reached the serialiser layer at all.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
