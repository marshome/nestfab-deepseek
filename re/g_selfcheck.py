# -*- coding: utf-8 -*-
"""The checks that catch the mistakes only the human was catching.

Usage: python g_selfcheck.py [--commits 40]

The human asked whether I can find these problems myself. The honest answer is "some, and the split is exact", so the split was
measured across this session's defects:

    BEHAVIOURAL   a double declared as uint64, a field silently dropped, three regex passes that left a block unbalanced, a
                  klass decoder that mislabelled fifty library classes, a width read as a scale factor
    JUDGEMENTAL   "the smallest remaining export needs 20740 BYTES read" (the unit measured how many exports a body is in, not
                  how much body there is), and 30 commits to tooling against 10 to the deliverable

and the pattern is that the behavioural ones were mostly caught by something ALREADY RUNNING -- the gate, the tests, the ledger,
a noisy output that forced a re-scoping -- while the judgemental ones were caught by the human, twice, both times answering a
question I had not asked myself. The reason is not carelessness: **no tool was asking whether the work was worth doing.**

So this file asks it. Three questions, each one a thing the human had to point out first:

  STALL      forwardedCount has not moved in N commits. The metric that matters is the deliverable, and a round that improves
             the tooling while the deliverable stands still is the drift the human noticed.
  TOOLING    more commits touch only re/ than touch lcns/. Same question, measured differently, and it is the one that produced
             "30 against 10".
  UNITS      a claim in the ledger whose number cannot be compared with the number beside it. The 20740 was recorded as BYTES
             when the same paragraph said 75 FUNCTIONS, and those two are not the same measurement -- the ledger holds both, and
             nothing noticed they were incommensurable.

Exit code 4 when the deliverable has stalled, which is the code re/g_round.py already treats as a stop.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


def run(command, cwd=ROOT):
    assert not (command[0] == "git" and "push" in command), "never push"
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.returncode, (result.stdout or "").strip(), (result.stderr or "").strip()


def forwarded_count_now():
    """The number in the forwarding table, which is the project's headline metric."""
    path = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")
    if not os.path.exists(path):
        return None
    text = open(path, encoding="utf-8", errors="replace").read()
    return len(re.findall(r"\{\s*\d+\s*,", text))


def commits(limit):
    _code, out, _err = run(["git", "log", "--format=%h|%s", "-%d" % limit])
    return [line.split("|", 1) for line in out.split("\n") if "|" in line]


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--commits", type=int, default=40)
    args = parser.parse_args(argv)

    problems = []
    rows = commits(args.commits)

    # STALL: when did the forwarding table last change, and how many commits ago was that
    _code, last, _err = run(["git", "log", "-1", "--format=%h", "--", "lcns/include/lcns/detail/exports_forwarding.inc"])
    since = 0
    for short, _subject in rows:
        if short == last:
            break
        since += 1
    count = forwarded_count_now()
    print("forwardedCount is %s; the forwarding table last changed %d commits ago (%s)" % (count, since, last or "never"))
    if since >= 12:
        problems.append("STALL: forwardedCount has not moved in %d commits. The deliverable is the implementation, and a round "
                        "that improves the tooling while the count stands still is the drift the human noticed." % since)

    # TOOLING: the ratio the human saw as "30 against 10"
    lcns = 0
    re_only = 0
    for short, _subject in rows:
        _c, files, _e = run(["git", "show", "--name-only", "--format=", short])
        names = [f for f in files.split("\n") if f.strip()]
        if any(f.startswith("lcns/") for f in names):
            lcns += 1
        elif names:
            re_only += 1
    print("in the last %d commits: %d touched lcns/, %d touched only re/" % (len(rows), lcns, re_only))
    if re_only > lcns * 2:
        problems.append("TOOLING: %d commits to re/ against %d to lcns/. Building apparatus is not the deliverable, and this "
                        "ratio was already pointed out once." % (re_only, lcns))

    # UNITS: a ledger claim whose numbers are incommensurable with its own witness
    import ledger
    data = ledger.load()
    for claim in data["claims"]:
        predicate = claim.get("predicate", "")
        witness = claim.get("witness", "")
        bytes_in_predicate = re.search(r"(\d{4,})\s*(?:bytes|B\b)", predicate)
        functions_in_witness = re.search(r"(\d+)\s+function", witness)
        if bytes_in_predicate and functions_in_witness:
            problems.append("UNITS: %s states %s bytes while its witness counts functions; the two units are not comparable "
                            "and the 20740 was exactly this mistake" % (claim["subject"], bytes_in_predicate.group(1)))

    print("")
    if problems:
        for problem in problems:
            print("PROBLEM: %s" % problem)
        print("")
        print("%d problems. The first two are the ones the human had to point out; the third is the one I wrote down myself and" % len(problems))
        print("then did not act on, which is why it is a check now.")
        return 4
    print("no stall, no tooling drift, and no incommensurable claim")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
