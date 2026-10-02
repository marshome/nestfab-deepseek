# -*- coding: utf-8 -*-
"""Blockers: a registry of what is stuck, why, and what was already tried -- so a round can look elsewhere.

Usage:
    python g_blocked.py add "key->offset pairing" --reason "..." --tried "..." [--round N]
    python g_blocked.py list
    python g_blocked.py resolve "key->offset pairing" --how "..."

The human's instruction, and it is a working method rather than a preference: **when one place is stuck, try others broadly, and
come back to the stuck place when something has moved.** Every tool this project has ranks work by value, and none of them can
express "this is stuck, go elsewhere", so a round that hits a wall either keeps hammering or drifts. This is the missing state.

It is deliberately small: a blocker has an id, the round it appeared, what was TRIED (so the next attempt does not repeat it), and
the reason. `resolve` records how it came unstuck rather than deleting it, because "what unstuck this" is the most useful thing to
know the next time something similar is stuck.

The one rule that makes it work rather than becoming a list of excuses: **a blocker records what was TRIED, and a blocker with no
attempts is not a blocker, it is an intention.** The tool refuses to record one.
"""
import argparse
import io
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "blockers.json")


def load():
    try:
        return json.load(io.open(STORE, encoding="utf-8"))
    except Exception:
        return {"blockers": []}


def save(data):
    io.open(STORE, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=1, sort_keys=True))


def stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    p_add = sub.add_parser("add")
    p_add.add_argument("id")
    p_add.add_argument("--reason", required=True)
    p_add.add_argument("--tried", action="append", default=[])
    p_add.add_argument("--round", type=int, default=None)
    p_res = sub.add_parser("resolve")
    p_res.add_argument("id")
    p_res.add_argument("--how", required=True)
    sub.add_parser("list")
    args = parser.parse_args(argv)
    data = load()

    if args.command == "add":
        if not args.tried:
            print("REFUSING: a blocker with no attempts is an intention, not a blocker. Give --tried at least once.")
            return 2
        for entry in data["blockers"]:
            if entry["id"] == args.id and not entry.get("resolved"):
                entry.setdefault("tried", []).extend(args.tried)
                save(data)
                print("added %d attempt(s) to the existing blocker %r" % (len(args.tried), args.id))
                return 0
        data["blockers"].append({"id": args.id, "at": stamp(), "round": args.round,
                                 "reason": args.reason, "tried": args.tried, "resolved": None})
        save(data)
        print("recorded the blocker %r with %d attempt(s); a round may now work elsewhere" % (args.id, len(args.tried)))
        return 0

    if args.command == "resolve":
        for entry in data["blockers"]:
            if entry["id"] == args.id:
                entry["resolved"] = {"at": stamp(), "how": args.how}
                save(data)
                print("resolved %r: %s" % (args.id, args.how))
                return 0
        print("no blocker named %r" % args.id)
        return 2

    open_blockers = [b for b in data["blockers"] if not b.get("resolved")]
    print("blockers: %d open, %d resolved" % (len(open_blockers), len(data["blockers"]) - len(open_blockers)))
    print("")
    for entry in open_blockers:
        print("%s  round %s" % (entry["id"], entry.get("round")))
        print("    because: %s" % entry["reason"][:120])
        for attempt in entry["tried"]:
            print("    tried:   %s" % attempt[:120])
        print("")
    for entry in data["blockers"]:
        if entry.get("resolved"):
            print("%s  RESOLVED: %s" % (entry["id"], entry["resolved"]["how"][:100]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
