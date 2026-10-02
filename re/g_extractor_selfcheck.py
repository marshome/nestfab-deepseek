# -*- coding: utf-8 -*-
"""A rule with a check: extractors must prove they work before their "nothing" is believed.

The rule comes from two consecutive rounds that both printed "found 0" and only one of which was a finding. The reason the second was
trustworthy is not care or intelligence: it asked a question whose answer it already knew and REFUSED TO REPORT when the answer came
back wrong. That is cheap, it is mechanical, and it converts a class of silent false negatives into a loud failure.

This is the check. It is honest about what it can and cannot enforce:

  * CAN: whether a tool contains a construct that would REFUSE on a failed expectation -- a `REFUSING`/`return 2` path, an
    `assert` on a self-check, or an explicit SELF_CHECK name. A tool with none of those cannot be refusing anything.
  * CANNOT: whether the self-check is asking a useful question. A tool can hold a vacuous self-check and pass this. That limit is
    printed rather than hidden, because a check that claims more than it measures is the failure this project keeps recording.

Usage: python g_extractor_selfcheck.py [--list]
Exit:  1 when a tool that reports "found N" has no self-check, 0 otherwise
"""
import argparse
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# a tool REPORTS a count when it prints something like "found %d" or "N function(s)" or "N of N"
REPORTS_COUNT = re.compile(r"found\s|function\(s\)|matches|hits|entries found|\bcount\b", re.IGNORECASE)
# and it SELF-CHECKS when it has one of these
SELF_CHECKS = [
    (re.compile(r"REFUSING TO REPORT"), "prints REFUSING TO REPORT"),
    (re.compile(r"SELF[-_ ]?CHECK", re.IGNORECASE), "names a SELF-CHECK"),
    (re.compile(r"^\s*assert\s", re.MULTILINE), "asserts something"),
    (re.compile(r"self_check|selfcheck", re.IGNORECASE), "has a self_check function"),
]

# tools whose output is prose rather than a count, and which therefore do not need this
NOT_A_COUNTER = set()


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)

    rows = []
    for path in sorted(glob.glob(os.path.join(HERE, "g_*.py"))) + sorted(glob.glob(os.path.join(HERE, "check_*.py"))):
        name = os.path.basename(path)
        if name in ("g_extractor_selfcheck.py", "g_rules.py"):
            continue
        text = io.open(path, encoding="utf-8", errors="replace").read()
        reports = bool(REPORTS_COUNT.search(text))
        found = [label for pattern, label in SELF_CHECKS if pattern.search(text)]
        rows.append((name, reports, found))

    # also the tools that live under lcns/tools, which are extractors too
    for path in sorted(glob.glob(os.path.join(os.path.dirname(HERE), "lcns", "tools", "*.py"))):
        name = "lcns/tools/" + os.path.basename(path)
        text = io.open(path, encoding="utf-8", errors="replace").read()
        rows.append((name, bool(REPORTS_COUNT.search(text)),
                     [label for pattern, label in SELF_CHECKS if pattern.search(text)]))

    counters = [(n, f) for n, r, f in rows if r]
    print("tools examined: %d, of which %d report a count" % (len(rows), len(counters)))
    print("")

    bad = []
    for name, found in counters:
        if found:
            if args.list:
                print("  OK    %-34s %s" % (name, ", ".join(found)))
        else:
            bad.append(name)
            print("  NO    %-34s reports a count and never refuses" % name)
    print("")
    print("counters with a self-check: %d of %d" % (len(counters) - len(bad), len(counters)))
    print("")
    print("WHAT THIS CANNOT SEE, stated so the check does not claim more than it measures: whether the self-check asks a USEFUL")
    print("question. A tool can hold a vacuous one and pass. What it can see is whether a tool has any construct that would refuse")
    print("when an expectation fails -- and a tool with none of those cannot be refusing anything.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
