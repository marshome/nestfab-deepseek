# -*- coding: utf-8 -*-
"""The round counter: how many rounds have passed since the human was last synced.

Usage:
    python g_rounds.py                 -> the count and whether a sync is due
    python g_rounds.py --done "what"   -> record a round and what it did
    python g_rounds.py --synced        -> mark a sync done, reset the counter

The human asked to be synced every thirty rounds instead of every round, and that instruction lives in re/RESUME.md as rule 7.
A rule in a document is exactly the thing a long session drops, so it is a program here: re/rounds.json holds the number of
rounds since the last sync, the driver increments it, and the driver refuses to start a fresh round once thirty have passed
without a sync. That converts "remember to report" into a condition that stops work, which is the only kind of instruction that
survives a conversation.
"""
import argparse
import io
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "rounds.json")
LIMIT = 30


def load():
    try:
        return json.load(io.open(STORE, encoding="utf-8"))
    except Exception:
        return {"rounds": 0, "since": None, "history": []}


def save(data):
    io.open(STORE, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=1, sort_keys=True))


def stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--done", default=None, help="record a round with this description")
    parser.add_argument("--synced", action="store_true", help="mark a sync and reset the counter")
    parser.add_argument("--check", action="store_true", help="exit 4 when a sync is due, without printing a plan")
    args = parser.parse_args(argv)
    data = load()

    if args.done is not None:
        data["rounds"] = data.get("rounds", 0) + 1
        data.setdefault("history", []).append({"round": data["rounds"], "at": stamp(), "did": args.done})
        data["history"] = data["history"][-200:]
        save(data)
        print("round %d recorded: %s" % (data["rounds"], args.done))
        if data["rounds"] >= LIMIT:
            print("")
            print("SYNC DUE: %d rounds since the last sync (the limit is %d)." % (data["rounds"], LIMIT))
            print("Write the summary before starting another round, then `python re/g_rounds.py --synced`.")
        return 0

    if args.synced:
        previous = data.get("rounds", 0)
        data["rounds"] = 0
        data["since"] = stamp()
        data.setdefault("history", []).append({"round": 0, "at": stamp(), "did": "SYNCED after %d rounds" % previous})
        save(data)
        print("sync recorded after %d rounds" % previous)
        return 0

    rounds = data.get("rounds", 0)
    if args.check:
        print("%d of %d rounds since the last sync" % (rounds, LIMIT))
        return 4 if rounds >= LIMIT else 0
    print("rounds since the last sync: %d of %d" % (rounds, LIMIT))
    if data.get("since"):
        print("last sync: %s" % data["since"])
    recent = data.get("history", [])[-6:]
    if recent:
        print("")
        print("the last rounds:")
        for row in recent:
            print("    %-4s %s  %s" % (row.get("round"), row.get("at"), row.get("did", "")[:80]))
    if rounds >= LIMIT:
        print("")
        print("SYNC DUE")
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
