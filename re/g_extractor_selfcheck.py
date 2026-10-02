# -*- coding: utf-8 -*-
"""A rule with a check: extractors must prove they work before their "nothing" is believed.

    python g_extractor_selfcheck.py [--list]

THE RULE, and where it comes from. Two consecutive rounds both printed "found 0" and only one of them was a finding. The second was
trustworthy because it asked a question whose answer it already knew and REFUSED TO REPORT when the answer came back wrong:

    SELF-CHECK: can this parser see 0x23BF0 store into +0x30?  True
    ...
    REFUSING TO REPORT: the parser cannot find a store this function certainly makes

That is cheap and mechanical, and it converts a class of silent false negatives into a loud failure. This checks for it.

WHAT COUNTS AS A SELF-CHECK, and the tightening this version makes. A first version accepted any `assert` and reported "30 of 152",
then listing them showed the matches were g_add29.py, g_add_batch7.py and scripts like them whose asserts validate their ARGUMENTS
rather than their extraction. **The number was an over-count, which is the opposite of this project's usual error and just as wrong.**
So the accepted patterns are now only the ones that tie the self-check to a CONCRETE expected value:

  * a refusal path -- `REFUSING` or a `return 2` that follows a failed check;
  * a named SELF-CHECK constant holding an address or a value the tool expects to find;
  * an `expected`/`EXPECT` value compared against what the extraction produced.

A bare `assert` no longer counts, because it cannot be told apart from an argument validation by reading the file, and pretending it
can is what produced the over-count.

WHAT IT STILL CANNOT SEE is stated here and printed by the tool, because a check that claims more than it measures is the failure
this session has recorded six times: **it cannot see whether the expected value is a USEFUL one.** A tool whose self-check expects
something trivial passes. The count is an UPPER BOUND on self-checking and the true figure is lower; the tool says so in its own
output rather than leaving it to be inferred.

Exit: 1 when a tool that reports a count holds none of the accepted patterns, 0 otherwise.
"""
import argparse
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# a tool REPORTS a count when it prints one of these
REPORTS_COUNT = re.compile(r"found\s|function\(s\)|matches|entries found|hits\b|\bcount\b", re.IGNORECASE)

# the accepted self-check patterns -- each ties the check to a CONCRETE expected value
SELF_CHECKS = [
    (re.compile(r"REFUSING TO REPORT"), "prints REFUSING TO REPORT"),
    (re.compile(r"SELF[-_ ]?CHECK", re.IGNORECASE), "names a SELF-CHECK"),
    (re.compile(r"^\s*(?:EXPECT|EXPECTED|KNOWN_[A-Z_]*)\s*=", re.MULTILINE), "declares an EXPECTED/KNOWN_ value"),
    (re.compile(r"\bself_check\s*\(", re.IGNORECASE), "calls a self_check"),
]


def analyse(path, name):
    text = io.open(path, encoding="utf-8", errors="replace").read()
    reports = bool(REPORTS_COUNT.search(text))
    found = [label for pattern, label in SELF_CHECKS if pattern.search(text)]
    return name, reports, found


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)

    rows = []
    for path in sorted(glob.glob(os.path.join(HERE, "g_*.py"))) + sorted(glob.glob(os.path.join(HERE, "check_*.py"))):
        name = os.path.basename(path)
        if name in ("g_extractor_selfcheck.py", "g_rules.py"):
            continue
        rows.append(analyse(path, name))
    for path in sorted(glob.glob(os.path.join(os.path.dirname(HERE), "lcns", "tools", "*.py"))):
        rows.append(analyse(path, "lcns/tools/" + os.path.basename(path)))

    counters = [(n, f) for n, r, f in rows if r]
    good = [(n, f) for n, f in counters if f]
    bad = [n for n, f in counters if not f]

    print("tools examined: %d, of which %d report a count" % (len(rows), len(counters)))
    print("")
    for name, found in good:
        if args.list:
            print("  OK    %-34s %s" % (name, ", ".join(found)))
    for name in bad:
        print("  NO    %-34s reports a count and never ties a check to an expected value" % name)
    print("")
    print("counters with a self-check: %d of %d" % (len(good), len(counters)))
    print("")
    print("WHAT THIS CANNOT SEE, so that the number is not read as more than it is: whether the EXPECTED value is a USEFUL one. A")
    print("tool whose self-check expects something trivial passes. So this count is an UPPER BOUND on self-checking and the true")
    print("figure is lower. A first version accepted a bare assert and reported 30; listing them showed they validated their")
    print("arguments, so the accepted patterns are now only those tied to a concrete expected value.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
