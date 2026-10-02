# -*- coding: utf-8 -*-
"""Supersede a claim whose GAP was closed by a different claim, not by a stronger version of itself.

re/g_supersede.py handles the common case: one predicate filed at two grades, where the weaker is superseded by the stronger. This
handles the other case, which is just as common and was not representable:

    SHAPE        r543  rcx.type  "the first argument's type is unknown per function, which is why the width check cannot conclude
                                 101, 2599, 315 and 9 functions write 1, 2, 4 and 16 bytes at +0x10 through rcx; only their types
                                 separate them"
    INSTRUCTION  r545  ...       "a callee's first-argument type is the caller's class when rcx carries it into the call"

The first is not a weaker version of the second -- it is a statement that a CHECK CANNOT CONCLUDE because a type is unknown, and the
second is the type propagation that makes it known. **The gap the first claim recorded was closed by a different claim**, so it should
be marked superseded with that claim named as the reason. Without this the ranking keeps offering to close a gap that is already closed,
which is what it did with the logger claim for many rounds.

    python g_supersede_by.py --subject rcx.type --grade SHAPE --by-round 545 --why "..."

It REFUSES when the named claim does not exist, when it is not stronger than the claim being superseded, or when the claim is already
superseded, so every refusal names a concrete mismatch.
"""
import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")
ORDER = ["GUESS", "SHAPE", "ORACLE", "INSTRUCTION", "MEASURED", "CONSTRUCTOR", "DIFFERENTIAL"]


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", required=True)
    parser.add_argument("--grade", required=True)
    parser.add_argument("--by-round", type=int, required=True)
    parser.add_argument("--why", required=True)
    args = parser.parse_args(argv)

    data = json.loads(io.open(LEDGER, encoding="utf-8").read())
    losers = [c for c in data["claims"] if c["subject"] == args.subject and c["grade"] == args.grade
              and not c.get("superseded_by")]
    if len(losers) != 1:
        print("REFUSING: expected exactly one live %s claim on %s, found %d." % (args.grade, args.subject, len(losers)))
        return 2
    loser = losers[0]

    winners = [c for c in data["claims"] if c["round"] == args.by_round and not c.get("superseded_by")]
    if not winners:
        print("REFUSING: no live claim was recorded in round %d." % args.by_round)
        return 2
    winner = max(winners, key=lambda c: ORDER.index(c["grade"]) if c["grade"] in ORDER else -1)

    if ORDER.index(winner["grade"]) <= ORDER.index(loser["grade"]):
        print("REFUSING: the claim from round %d is %s, which does not supersede %s." % (args.by_round, winner["grade"], loser["grade"]))
        return 2

    loser["superseded_by"] = {"grade": winner["grade"], "round": winner["round"], "subject": winner["subject"], "why": args.why}
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=1, sort_keys=True))
    print("marked the %s claim on %s (round %d) as superseded by the %s claim on %s (round %d)"
          % (loser["grade"], loser["subject"], loser["round"], winner["grade"], winner["subject"], winner["round"]))
    print("reason: %s" % args.why)
    print("")
    print("The two are NOT versions of one another; one recorded a gap and the other closed it. That is why this is a separate tool")
    print("from re/g_supersede.py, which chooses between two claims that share a predicate.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
