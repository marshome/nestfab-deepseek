# -*- coding: utf-8 -*-
"""Resolve a duplicated predicate: mark one claim as SUPERSEDED by another rather than deleting it.

Usage:
    python g_supersede.py --predicate "<text>" --by <id-of-the-winner> --why "..."

THE CONTRADICTION THIS EXISTS FOR. re/g_prioritize.py ranked a CONTRADICT first: one predicate filed at two grades, SHAPE from round
544 and INSTRUCTION from round 545. The weaker one was not wrong when it was written -- it said "a callee's first argument is the
caller's class when the call is through a vtable; nothing propagates that yet", and the next round a tool DID propagate it and
measured 4486 functions typing that way. So the SHAPE claim was SUPERSEDED, not mistaken, and the difference matters: deleting it
would erase the record that the question was once open, and leaving it would keep a resolved item at the top of the ranking forever.

WHY NOT JUST DELETE. Because the ledger's value is that a belief carries its history. A superseded claim keeps its round and its
witness, and gains a pointer to the claim that replaced it plus the reason. `re/g_prioritize.py` then stops ranking it, and a reader
can still see that the question was asked and answered.

A claim is identified by its PREDICATE text because that is what the priorities key on; ids, where they exist, are not unique across
the file. The tool refuses when the predicate matches more or fewer than two claims, so a mismatch is loud.
"""
import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

# the grades, weakest first, so "the winner" can be checked rather than taken on trust
ORDER = ["GUESS", "SHAPE", "ORACLE", "INSTRUCTION", "MEASURED", "CONSTRUCTOR", "DIFFERENTIAL"]


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--predicate", required=True)
    parser.add_argument("--why", required=True)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)

    data = json.loads(io.open(LEDGER, encoding="utf-8").read())
    matches = [c for c in data["claims"] if c["predicate"] == args.predicate]
    print("claims with that predicate: %d" % len(matches))
    for claim in matches:
        print("   grade %-14s round %-5s superseded_by %s" % (claim["grade"], claim["round"], claim.get("superseded_by")))
    print("")

    if args.list:
        return 0
    live = [c for c in matches if not c.get("superseded_by")]
    if len(live) != 2:
        print("REFUSING: this expects exactly two LIVE claims to choose between, and found %d." % len(live))
        return 2

    live.sort(key=lambda c: ORDER.index(c["grade"]) if c["grade"] in ORDER else -1)
    loser, winner = live[0], live[-1]
    if loser["grade"] == winner["grade"]:
        print("REFUSING: the two claims share the grade %s, so neither supersedes the other and this is a real conflict." % loser["grade"])
        return 2

    loser["superseded_by"] = {"grade": winner["grade"], "round": winner["round"], "why": args.why}
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=1, sort_keys=True))
    print("marked the %s claim (round %s) as superseded by the %s claim (round %s)" % (loser["grade"], loser["round"],
                                                                                     winner["grade"], winner["round"]))
    print("reason: %s" % args.why)
    print("")
    print("Both are kept: the weaker one records that the question was once open, and the pointer records that it was answered.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
