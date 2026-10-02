# -*- coding: utf-8 -*-
"""A rule with a check: a round must land C++ under lcns/, measured over a window rather than per round.

WHY THIS EXISTS. The human observed that little C++ was coming out while the work continued, and the measurement agreed with them:

    rounds 500-549    27 ledger claims, and layout.hpp's 3744 lines were committed around round 141-173
    rounds 550-599    96 claims
    rounds 600+       87 claims, and about 1500 lines of C++

so the early rounds produced roughly 130 lines of C++ per round and the recent ones roughly 8, against a claim count that grew from 27 to
87 per fifty rounds. **The measurement infrastructure had grown until it consumed the product.** A rule is the response because that is
this project's only mechanism that works.

WHAT IT MEASURES, and why a window. A per-round check is impossible from here: this runs after a commit and cannot know whether the round
it belongs to changed lcns/. What it CAN measure is the ratio over a window of recent commits -- "in the last N commits, how many touched
lcns/" -- which is the quantity the human was actually asking about. The threshold is deliberately low, because a round that reads a
4000 byte function and writes three lines has done its job, and a round that writes nothing has not.

    python g_round_output.py [--commits 10] [--min 3]

A SELF-CHECK, per the rule: the window must contain at least one commit that touched lcns/, because this repository certainly has them;
if not, the tool is reading the wrong history.
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--commits", type=int, default=12)
    parser.add_argument("--min", type=int, default=4)
    args = parser.parse_args(argv)

    log = subprocess.run(["git", "log", "--format=%h %s", "-n", str(args.commits)],
                         cwd=ROOT, capture_output=True, text=True).stdout.strip().split("\n")
    log = [line for line in log if line]
    touched = 0
    rows = []
    for line in log:
        sha = line.split()[0]
        files = subprocess.run(["git", "show", "--name-only", "--format=", sha],
                               cwd=ROOT, capture_output=True, text=True).stdout
        hits = [f for f in files.split("\n") if f.startswith("lcns/") and
                (f.endswith(".hpp") or f.endswith(".cpp") or f.endswith(".inc"))]
        if hits:
            touched += 1
        rows.append((sha, line[len(sha):].strip()[:70], len(hits)))

    print("SELF-CHECK: commits in the window that touched lcns/: %d of %d" % (touched, len(log)))
    if touched == 0:
        print("REFUSING TO REPORT: no commit in the window touched lcns/, which cannot be right for this repository.")
        return 2
    print("")
    print("%-9s %-6s %s" % ("commit", "lcns", "subject"))
    for sha, subject, count in rows:
        print("%-9s %-6d %s" % (sha, count, subject))
    print("")
    print("commits that landed C++ under lcns/: %d of %d, against a floor of %d"
          % (touched, len(log), args.min))
    print("")
    if touched < args.min:
        print("FAILING: the recent rounds have produced analysis without producing code, which is the drift the human named.")
        print("A round that reads a function and writes nothing has not finished; a round that writes three lines has.")
        return 1
    print("The window is landing code. Note what this check CANNOT see: whether the code is any good, and whether a given round wrote")
    print("it -- only that the window as a whole is not all analysis.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
