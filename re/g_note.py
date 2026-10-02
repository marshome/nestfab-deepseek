# -*- coding: utf-8 -*-
"""Record a requirement or a decision, so the next session does not need to be told again.

Usage:
    python g_note.py requirement "每30轮和我同步一次" --round 538
    python g_note.py decision "a structure is found in its CONSTRUCTOR" --evidence "RE 0x14620" --round 533
    python g_note.py list

Why this exists: the human asked how to stop repeating themselves. A transcript is worth keeping, but a transcript is not what
stops the repetition -- a file a fresh session READS is, and the reading only happens if the file is short and dated. So this
appends one line to re/DECISIONS.md, and for a requirement it also appends the rule to re/RULES.md as a checked condition,
because a requirement that is only a sentence is a requirement that gets dropped by the next long session.

The append-only shape is deliberate. A decision that is revised gets a NEW line with a new round rather than an edit, so the
history of what was believed and when stays readable, which is the same reason this project commits per round with the
addresses in the message.
"""
import argparse
import io
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DECISIONS = os.path.join(HERE, "DECISIONS.md")
RULES = os.path.join(HERE, "RULES.md")


def today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def insert_row(path, heading, row):
    """Add a table row under the named heading, keeping the file's tables contiguous."""
    text = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.index(heading)
    end = text.find("\n\n", start)
    if end < 0:
        end = len(text)
    block = text[start:end]
    block = block.rstrip("\n") + "\n" + row + "\n"
    io.open(path, "w", encoding="utf-8", newline="\n").write(text[:start] + block + text[end:])


def main(argv):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    p_req = sub.add_parser("requirement")
    p_req.add_argument("text")
    p_req.add_argument("--round", default="now")
    p_req.add_argument("--check", default="no check yet, which is recorded rather than hidden")
    p_dec = sub.add_parser("decision")
    p_dec.add_argument("text")
    p_dec.add_argument("--evidence", required=True)
    p_dec.add_argument("--round", default="now")
    sub.add_parser("list")
    args = parser.parse_args(argv)

    if args.command == "requirement":
        insert_row(DECISIONS, "## The requirements, in the human's words",
                   "| %s | %s |" % (args.round, args.text))
        # a requirement also becomes a rule, with its check named even when the check does not exist yet
        text = io.open(RULES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        identifier = re.sub(r"[^a-z0-9]+", "-", args.text.lower())[:40].strip("-") or "requirement"
        addition = ('\n {"id": "%s",\n  "rule": "%s",\n  "check": "%s",\n  "where": "re/RULES.md, added %s",\n'
                    '  "since": "round %s"}\n' % (identifier, args.text, args.check, today(), args.round))
        marker = "## What is deliberately NOT a rule here"
        text = text.replace(marker, addition.strip() + "\n\n" + marker, 1)
        io.open(RULES, "w", encoding="utf-8", newline="\n").write(text)
        print("recorded the requirement and added it to re/RULES.md as %s" % identifier)
        print("    its check is: %s" % args.check)
        print("    a rule with no check is recorded as one rather than dressed up as enforced")
        return 0

    if args.command == "decision":
        insert_row(DECISIONS, "## The decisions, and the evidence for each",
                   "| %s | %s | %s |" % (args.round, args.text, args.evidence))
        print("recorded the decision with its evidence")
        return 0

    if args.command == "list":
        text = io.open(DECISIONS, encoding="utf-8", newline="").read()
        for line in text.split("\n"):
            if line.startswith("| ") and not line.startswith("| round") and "---" not in line:
                print(line)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
