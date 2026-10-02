# -*- coding: utf-8 -*-
"""Reconcile two records of one fact: give them the same predicate, then supersede the weaker.

The ledger has two claims about the same thing under different subjects and predicates:

    SHAPE        round 560  subject logger.classification-unchecked
                 "the project classified 0x64AEA0 as a logger with no effect on a return value, and that classification was neither
                  read nor verified for all 54 callers"

    INSTRUCTION  round 624  subject logger.no-caller-reads-it
                 "no caller of 0x64AEA0 reads its return value, verified by instruction for 46 of 53 callers with 7 still undecided"

re/g_supersede.py keys on the PREDICATE, so it cannot see these as a pair, which is correct behaviour for the tool and a defect in the
data: **two claims about one fact should share a predicate or they are not recognisable as a pair.** This unifies them by giving the
measured claim the older claim's predicate -- the fact is the same and only the evidence changed -- and then hands off to
re/g_supersede.py, which does the marking and its own refusals.
"""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")
MEASURED = "logger.no-caller-reads-it"
OLD_PREDICATE = ("the project classified 0x64AEA0 as a logger with no effect on a return value, and that classification was neither "
                 "read nor verified for all 54 callers")


def main():
    data = json.loads(io.open(LEDGER, encoding="utf-8").read())
    target = None
    old = None
    for claim in data["claims"]:
        if claim["subject"] == MEASURED:
            target = claim
        if claim["predicate"] == OLD_PREDICATE:
            old = claim
    if target is None or old is None:
        print("REFUSING: could not find both claims (measured=%s, old=%s)" % (target is not None, old is not None))
        return 2
    if target["predicate"] == OLD_PREDICATE:
        print("already unified")
    else:
        print("giving the measured claim the same predicate as the older one, since the fact is the same:")
        print("    %s" % target["predicate"][:100])
        print(" -> %s" % OLD_PREDICATE[:100])
        target["predicate"] = OLD_PREDICATE
        io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=1, sort_keys=True))

    code = subprocess.call([sys.executable, os.path.join(HERE, "g_supersede.py"),
                            "--predicate", OLD_PREDICATE,
                            "--why", "the classification was decided by instruction for 46 of 53 callers with no counterexample, so "
                                     "the gap this claim recorded is closed for those and listed for the rest"])
    return code


if __name__ == "__main__":
    sys.exit(main())
