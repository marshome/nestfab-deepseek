#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Land an exact replacement into a source file, with the block RECORDED before and after and a refusal when it does not match.

**WHY ONE TOOL INSTEAD OF A SCRIPT PER EDIT.** The rule `no-regex-churn` exists because round 540's three regex passes over one test block left unbalanced
parentheses and the block had to be rewritten by hand, and it bounds how many scripts under `re/` write into `lcns/`. **A pile of one-off editors is the shape
that failed**; what the rule asks for is that a script rewriting a source **records the block it replaced** and **is not needed twice**. So this takes the
replacement from a JSON file, writes both sides to `re/landings/`, refuses unless the old text appears EXACTLY ONCE, and refuses unless the new text is there
afterwards.

**AND IT REFUSES TO DO TWO THINGS AT ONCE.** One landing is one file and one replacement, because a tool that applies several edits cannot tell which one moved a
line when the guard fails.

    python -u g_land.py --file lcns/include/lcns/tiling.hpp --old re/landings/x.old --new re/landings/x.new
    python -u g_land.py --show re/landings/x.json
"""
import argparse
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LANDINGS = os.path.join(HERE, "landings")


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", dest="target")
    parser.add_argument("--old", dest="old")
    parser.add_argument("--new", dest="new")
    parser.add_argument("--show", dest="show")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if args.show:
        spec = json.load(io.open(args.show, encoding="utf-8"))
        print(json.dumps(spec, indent=2, ensure_ascii=False))
        return 0

    if not (args.target and args.old and args.new):
        parser.error("give --file with --old and --new, or --show")

    target = args.target if os.path.isabs(args.target) else os.path.join(ROOT, args.target)
    for path in (target, args.old, args.new):
        if not os.path.isfile(path):
            print("REFUSING: %s is not a file" % path)
            return 2

    body = io.open(target, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    old = io.open(args.old, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    new = io.open(args.new, encoding="utf-8", newline="").read().replace("\r\n", "\n")

    # **THE EXACTLY-ONCE RULE.** An edit that matches nowhere is a drift, and one that matches twice is an edit that will change something the author did not
    # look at -- round 540's failure in one line.
    count = body.count(old)
    if count != 1:
        print("REFUSING: the old block appears %d time(s) in %s, and one landing replaces exactly one block" % (count, target))
        return 2
    if new in body:
        print("REFUSING: the new block is ALREADY in %s, so this landing has run" % target)
        return 2

    spec = {
        "target": os.path.relpath(target, ROOT).replace("\\", "/"),
        "old_sha": digest(old),
        "new_sha": digest(new),
        "old_lines": len(old.split("\n")),
        "new_lines": len(new.split("\n")),
        "old_preview": old.split("\n")[0][:110],
        "new_preview": new.split("\n")[0][:110],
    }
    print(json.dumps(spec, indent=2, ensure_ascii=False))
    if args.dry_run:
        print("(dry run: nothing written)")
        return 0

    # **THE RECORD GOES TO re/landings/ AND NOT INTO lcns/**, which is what keeps this tool's footprint off the tree it edits.
    if not os.path.isdir(LANDINGS):
        os.makedirs(LANDINGS)
    # **AND THE STEM CARRIES BOTH HASHES, BECAUSE ONE OF THEM COLLIDES.** The first version used only the OLD block's hash, and two landings that APPEND to the
    # same anchor share that block -- so the second overwrote the first's record, which is the opposite of what "records the block it replaced" is for. A landing
    # is identified by the PAIR it changes, so the pair is the name.
    stem = "%s-%s-%s" % (os.path.basename(target).replace(".", "_"), spec["old_sha"], spec["new_sha"])
    io.open(os.path.join(LANDINGS, stem + ".old"), "w", encoding="utf-8", newline="\n").write(old)
    io.open(os.path.join(LANDINGS, stem + ".new"), "w", encoding="utf-8", newline="\n").write(new)
    io.open(os.path.join(LANDINGS, stem + ".json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n")

    landed = body.replace(old, new, 1)
    if new not in landed:
        print("REFUSING: the replacement is not in the result, so nothing is written")
        return 2
    io.open(target, "w", encoding="utf-8", newline="\n").write(landed)
    print("landed into %s (%d line(s) -> %d); the record is re/landings/%s.{old,new,json}" % (target, spec["old_lines"], spec["new_lines"], stem))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
