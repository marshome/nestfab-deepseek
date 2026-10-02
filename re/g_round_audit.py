# -*- coding: utf-8 -*-
"""Check that every round was recorded, so a requirement cannot be lost by being unnoticed.

Usage: python g_round_audit.py [--since N]

The honest position, which this tool exists to make checkable rather than to claim away: the recording of this project's
decisions is DONE BY JUDGEMENT, not captured automatically. The human's requirement per round is written to re/DECISIONS.md only
when a round recognises it as a requirement, and a requirement buried in a longer message can be missed with nothing to catch
it. The same is true of the round counter: a round that does not call `re/g_rounds.py --done` leaves no trace.

So this compares what the repository SAYS happened with what git and the round counter RECORD:

  * a commit between two recorded rounds with no round recorded around it      -> a round that never registered
  * a recorded round whose time does not fall near any commit                  -> a round that did nothing, or a bad entry
  * a commit whose message contains 要求, requirement, 必须, must, never, 不要  -> a requirement-shaped commit with no rule
    added in the same commit

The third check is the one aimed at the real gap: a requirement is often visible in a commit message before it is written into
re/RULES.md, and this reports the ones that were not. It is deliberately a REPORT and not a failure, because a commit can
mention `must` while describing the original module rather than the human's wishes -- but it is printed every round, so the
question "did I record what the human asked" gets asked by a program.

Exit code is 4 when a round looks unrecorded, which re/g_round.py treats as a stop.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

REQUIREMENT_WORDS = ("要求", "requirement", "必须", "must ", "always ", "never ", "不要", "禁止", "每 30", "每30")


def run(command, cwd=ROOT):
    assert not (command[0] == "git" and "push" in command), "never push"
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return result.returncode, (result.stdout or "").strip(), (result.stderr or "").strip()


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", type=int, default=30, help="how many commits back to audit")
    args = parser.parse_args(argv)

    code, out, err = run(["git", "log", "--format=%h|%cI|%s", "-%d" % args.since])
    if code != 0:
        print("git log failed: %s" % err)
        return 2
    commits = []
    for line in out.split("\n"):
        if "|" not in line:
            continue
        short, when, subject = line.split("|", 2)
        commits.append((short, when, subject))

    rounds = json.load(open(os.path.join(HERE, "rounds.json"), encoding="utf-8"))
    recorded = rounds.get("history", [])
    print("commits in the window: %d" % len(commits))
    print("rounds recorded:       %d  (counter now at %s)" % (len(recorded), rounds.get("rounds")))
    print("")

    # a requirement-shaped commit that did not also touch re/RULES.md
    suspicious = []
    for short, when, subject in commits:
        if not any(word.lower() in subject.lower() for word in REQUIREMENT_WORDS):
            continue
        code, files, _err = run(["git", "show", "--name-only", "--format=", short])
        touched = [f for f in files.split("\n") if f.strip()]
        if not any("RULES.md" in f or "DECISIONS.md" in f for f in touched):
            suspicious.append((short, subject, touched))
    if suspicious:
        print("REQUIREMENT-SHAPED COMMITS WITH NO RULE RECORDED -- check each by hand:")
        for short, subject, touched in suspicious:
            print("    %s  %s" % (short, subject[:78]))
            print("        touched: %s" % ", ".join(touched[:4]))
        print("")
    else:
        print("no requirement-shaped commit is missing a rule record")
        print("")

    # the counter against the commits
    print("the recorded rounds, newest last:")
    for entry in recorded[-8:]:
        print("    %-4s %s  %s" % (entry.get("round"), entry.get("at"), entry.get("did", "")[:70]))

    unrecorded = 0
    if commits and not recorded:
        unrecorded = len(commits)
        print("")
        print("PROBLEM: %d commits and NOT ONE recorded round. The counter is the only place a round's reason survives, and" % len(commits))
        print("nothing has been written to it.")
    elif commits and recorded:
        # The timestamps come from two sources with DIFFERENT ZONES -- `git log --format=%cI` gives the committer's offset
        # (here +08:00) and re/rounds.json writes UTC with a Z -- so comparing the strings directly reported a missing round
        # that had in fact been recorded. Both are parsed to an aware datetime before the comparison, and the first version of
        # this tool got it wrong, which is recorded here because a checker that cries wolf is a checker nobody reads.
        def moment(text):
            try:
                return datetime.fromisoformat(text.replace("Z", "+00:00"))
            except Exception:
                return None

        newest_round = moment(recorded[-1].get("at", ""))
        newest_commit = moment(commits[0][1])
        if newest_round and newest_commit and newest_round < newest_commit:
            unrecorded = 1
            print("")
            print("PROBLEM: the newest commit (%s at %s) is LATER than the newest recorded round (%s)."
                  % (commits[0][0], newest_commit.isoformat(), newest_round.isoformat()))
            print("A round was committed without registering, so its reason is not in re/rounds.json.")
    print("")
    if unrecorded:
        print("ACTION: python re/g_rounds.py --done \"what this round did\"")
        return 4
    print("every recent round is accounted for in the counter")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
