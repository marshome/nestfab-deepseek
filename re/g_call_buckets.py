# -*- coding: utf-8 -*-
"""Profile a function's calls by the SIZE of each callee, so a 15305 byte body becomes a few buckets.

Usage: python g_call_buckets.py 0x1EE50 [--top 10]

The idea is the one that has worked repeatedly in this session: a body's byte count says little, and what matters is how much of it is
its own logic and how much is handed to large routines. Bucketing the calls by callee size turns "15305 bytes, 3076 instructions" into
"this much geometry, this much boilerplate".

A SELF-CHECK IS BUILT IN, and this time against the defect that has now bitten FOUR times: a `$` anchor written through PowerShell's
quoting reaches Python as a literal backslash-dollar, the pattern matches nothing, and the tool reports zero. So the tool asserts that
it found at least one call whose target is in the profile, and REFUSES TO REPORT otherwise. A profile of a 3076-instruction function
that contains no call targets cannot be right, and the point is for the tool to say so rather than for a reader to notice.
"""
import argparse
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

DIRECT = re.compile(r"^0x([0-9a-f]+)$")


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("address")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args(argv)
    root = int(args.address, 16)
    profile = load_prof()

    size = (profile.get(root) or {}).get("size") or 0
    if size == 0:
        print("no profile entry for 0x%X" % root)
        return 2
    body = [i for i in disasm(root) if i.address < root + size]
    calls = []
    for ins in body:
        if ins.mnemonic != "call":
            continue
        match = DIRECT.match(ins.op_str.strip())
        if match:
            calls.append((ins.address, int(match.group(1), 16)))
    distinct = collections.Counter(target for _at, target in calls)

    # ---- the self-check, against the quoting defect that produced a false zero four times --------------------------------
    resolvable = [t for t in distinct if t in profile]
    print("0x%X  %d bytes  %d instructions  %d calls  %d distinct  %d resolvable in the profile"
          % (root, size, len(body), len(calls), len(distinct), len(resolvable)))
    if len(body) > 200 and not resolvable:
        print("REFUSING TO REPORT: this function has %d instructions and not one call target resolves, which cannot be right.")
        print("The likely cause is the pattern, not the code -- a `$` anchor through PowerShell quoting has done this four times.")
        return 2
    print("")

    buckets = collections.Counter()
    for target, count in distinct.items():
        callee_size = (profile.get(target) or {}).get("size") or 0
        if callee_size >= 3000:
            buckets["3000+ bytes"] += count
        elif callee_size >= 1000:
            buckets["1000-2999"] += count
        elif callee_size >= 300:
            buckets["300-999"] += count
        elif callee_size >= 50:
            buckets["50-299"] += count
        else:
            buckets["under 50 -- boilerplate or CRT"] += count
    print("the distinct calls bucketed by the size of the callee:")
    for name in ("3000+ bytes", "1000-2999", "300-999", "50-299", "under 50 -- boilerplate or CRT"):
        if buckets[name]:
            print("   %-34s %3d distinct, %3d calls" % (name, sum(1 for t in distinct
                  if bucket_of(profile, t) == name), buckets[name]))
    print("")
    print("the largest callees, which are where the work is:")
    for target, count in sorted(distinct.items(), key=lambda kv: -((profile.get(kv[0]) or {}).get("size") or 0))[:args.top]:
        print("   0x%-8X %6s B  x%d" % (target, (profile.get(target) or {}).get("size"), count))
    print("")
    return 0


def bucket_of(profile, target):
    size = (profile.get(target) or {}).get("size") or 0
    if size >= 3000:
        return "3000+ bytes"
    if size >= 1000:
        return "1000-2999"
    if size >= 300:
        return "300-999"
    if size >= 50:
        return "50-299"
    return "under 50 -- boilerplate or CRT"


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
