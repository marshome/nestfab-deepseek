# -*- coding: utf-8 -*-
"""Index the findings archive by ADDRESS, so the archive is reachable from an address.

The gap this closes: `re/findings_*.md` holds fourteen files and about 1064 KB of finished analysis, and NOTHING pointed at them -- no
ledger claim cites one, and neither re/RESUME.md nor re/AGENT.md mentioned that they exist. So a session following the loop's own rules
re-derives what is already written down, which is what this one did for many rounds.

    python g_archive_index.py                 build re/archive_index.json
    python g_archive_index.py 0x1EE50         what the archive says about one address
    python g_archive_index.py --top 20        the addresses the archive covers most

The index is address -> {file: [line numbers]}, which is enough to answer "has anyone looked at this" in one command. It does NOT judge
whether the archived conclusion is correct: a finding is a lead like any other and its evidence must be checked, which is what the
round that hits it does.

A SELF-CHECK, per the rule: the archive certainly mentions 0x1EE50 -- an earlier command found 72 hits across the findings files -- so
the index must have it, and the tool refuses to write if it does not.
"""
import argparse
import collections
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "archive_index.json")
ADDRESS = re.compile(r"0x([0-9A-Fa-f]{4,7})\b")
SELF_CHECK_ADDRESS = 0x1EE50


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("address", nargs="?", default=None)
    parser.add_argument("--top", type=int, default=0)
    args = parser.parse_args(argv)

    paths = sorted(glob.glob(os.path.join(HERE, "findings_*.md")))
    if not paths:
        print("no findings files found")
        return 2

    index = collections.defaultdict(lambda: collections.defaultdict(list))
    for path in paths:
        name = os.path.basename(path)
        for number, line in enumerate(io.open(path, encoding="utf-8", errors="replace"), 1):
            for match in ADDRESS.finditer(line):
                index[int(match.group(1), 16)][name].append(number)

    # ---- the self-check ----------------------------------------------------------------------------------------------------
    hits = index.get(SELF_CHECK_ADDRESS)
    print("SELF-CHECK: the archive mentions 0x%X in %d file(s)?  %s"
          % (SELF_CHECK_ADDRESS, len(hits) if hits else 0, bool(hits)))
    if not hits:
        print("REFUSING TO WRITE: an address known to appear 72 times across the findings files is not in the index.")
        return 2
    print("")

    if args.address:
        target = int(args.address, 16)
        entry = index.get(target)
        if not entry:
            print("0x%X: the archive does NOT mention it" % target)
            return 0
        total = sum(len(v) for v in entry.values())
        print("0x%X: %d mention(s) across %d file(s)" % (target, total, len(entry)))
        for name, lines in sorted(entry.items(), key=lambda kv: -len(kv[1])):
            shown = ", ".join(str(n) for n in lines[:12])
            print("   %-34s %3d  line(s) %s%s" % (name, len(lines), shown, " ..." if len(lines) > 12 else ""))
        return 0

    if args.top:
        print("the addresses the archive covers most:")
        for address, entry in sorted(index.items(), key=lambda kv: -sum(len(v) for v in kv[1].values()))[:args.top]:
            total = sum(len(v) for v in entry.values())
            print("   0x%-8X %4d mention(s) in %d file(s)" % (address, total, len(entry)))
        print("")

    payload = {"0x%X" % address: {name: lines for name, lines in entry.items()} for address, entry in index.items()}
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps({"addresses": payload}, indent=1, sort_keys=True))
    print("files indexed: %d" % len(paths))
    print("distinct addresses: %d" % len(index))
    print("total mentions: %d" % sum(len(v) for entry in index.values() for v in entry.values()))
    print("")
    print("wrote %s" % OUT)
    print("")
    print("THE INDEX SAYS WHAT HAS BEEN LOOKED AT, NOT WHAT IS TRUE. A finding in the archive is a lead whose evidence still has to be")
    print("checked, exactly as a claim in the ledger does -- and the round that uses one says which it verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
