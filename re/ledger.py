# -*- coding: utf-8 -*-
"""The claim ledger: typed facts with provenance, and the rules that refuse a claim above its evidence.

Usage:
    python ledger.py add GRADE SUBJECT PREDICATE WITNESS [--round N]
    python ledger.py list [--grade GRADE] [--subject SUBJECT]
    python ledger.py promote SUBJECT --to GRADE --witness TEXT --round N
    python ledger.py check            (refuse anything used above its grade)
    python ledger.py report           (what the ledger believes, by grade)

Why this exists, in one paragraph. A reverse engineering session forgets, and a claim written down without its witness is
indistinguishable from a guess. This round alone lost time to six of those: an offset-frequency count that claimed an object
was a kilobyte, a naming tool that stamped one name on twenty fields, a mangled-name decoder that mislabelled fifty standard
library classes, a serialiser pairing that attached a key to the wrong accessor, a layout whose double was declared as an
integer, and a generator that dropped a field while reporting it as named. Every one was a CLAIM that no mechanism could
refuse. The ledger is that mechanism, and it is deliberately small:

    GUESS < SHAPE < ORACLE < INSTRUCTION < MEASURED < CONSTRUCTOR < DIFFERENTIAL

and the rules are the ones in re/LEDGER.md, enforced here rather than described:

  * a NAME needs ORACLE, or INSTRUCTION where the instruction is a setter whose own name is the field's;
  * a LAYOUT needs CONSTRUCTOR;
  * a BRANCH-equivalence needs DIFFERENTIAL;
  * a SHAPE may propose and may never conclude.

The store is re/ledger.json so a fresh session reads it instead of a conversation, and every claim records the file and line
its witness lives in as well as the address, because addresses move when a layout is regenerated and a quoted fragment does
not.
"""
import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "ledger.json")

GRADES = ["GUESS", "SHAPE", "ORACLE", "INSTRUCTION", "MEASURED", "CONSTRUCTOR", "DIFFERENTIAL"]
RANK = {grade: index for index, grade in enumerate(GRADES)}

# What each grade is allowed to conclude. A subject kind names the kind of claim, and the grade it needs.
NEEDS = {
    "name": "ORACLE",            # a field or function NAME
    "offset": "INSTRUCTION",     # a field's position
    "width": "INSTRUCTION",      # a field's width, from the store that writes it
    "layout": "CONSTRUCTOR",     # an object's size and complete field list
    "constant": "MEASURED",      # a value read out of the image
    "equivalence": "DIFFERENTIAL",   # behaviour that matches the original when both are run
    "shape": "SHAPE",            # a pattern that matches and nothing more
    "call": "INSTRUCTION",       # who calls whom
    "type": "CONSTRUCTOR",       # an object's type, from its constructor or its vtable
}


def load():
    try:
        return json.load(io.open(STORE, encoding="utf-8"))
    except Exception:
        return {"claims": []}


def save(data):
    io.open(STORE, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=1, sort_keys=True))


def add(data, grade, subject, predicate, witness, round_number=None):
    entry = {
        "grade": grade,
        "subject": subject,
        "predicate": predicate,
        "witness": witness,
        "round": round_number,
    }
    data["claims"].append(entry)
    return entry


def find(data, subject=None, grade=None):
    out = []
    for claim in data["claims"]:
        if subject and claim["subject"] != subject:
            continue
        if grade and claim["grade"] != grade:
            continue
        out.append(claim)
    return out


def strongest(data, subject):
    rows = find(data, subject=subject)
    if not rows:
        return None
    return max(rows, key=lambda c: RANK.get(c["grade"], -1))


def check(data):
    """Refuse any claim used above its grade.

    The rule that matters is the one an agent needs and a human does not: a claim of kind `name` whose best grade is SHAPE
    has no witness that can name anything, and using it anyway is how a session stamps a plausible word on a field and spends
    a round finding out.
    """
    problems = []
    for claim in data["claims"]:
        kind = claim.get("kind")
        if not kind:
            continue
        need = NEEDS.get(kind)
        if need is None:
            problems.append("unknown claim kind %r for %s" % (kind, claim["subject"]))
            continue
        have = claim["grade"]
        if RANK.get(have, -1) < RANK[need]:
            problems.append("%s: a %s claim needs %s but has %s -- %s"
                            % (claim["subject"], kind, need, have, claim["witness"][:60]))
    return problems


def main(argv):
    parser = argparse.ArgumentParser(description="the claim ledger")
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add")
    p_add.add_argument("grade", choices=GRADES)
    p_add.add_argument("subject")
    p_add.add_argument("predicate")
    p_add.add_argument("witness")
    p_add.add_argument("--kind", choices=sorted(NEEDS), default=None)
    p_add.add_argument("--round", type=int, default=None)

    p_list = sub.add_parser("list")
    p_list.add_argument("--grade", choices=GRADES, default=None)
    p_list.add_argument("--subject", default=None)

    p_pro = sub.add_parser("promote")
    p_pro.add_argument("subject")
    p_pro.add_argument("--to", choices=GRADES, required=True)
    p_pro.add_argument("--witness", required=True)
    p_pro.add_argument("--round", type=int, default=None)

    sub.add_parser("check")
    sub.add_parser("report")

    args = parser.parse_args(argv)
    data = load()

    if args.command == "add":
        entry = add(data, args.grade, args.subject, args.predicate, args.witness, args.round)
        if args.kind:
            entry["kind"] = args.kind
        save(data)
        print("added %s %s: %s" % (args.grade, args.subject, args.predicate))
        return 0

    if args.command == "list":
        for claim in find(data, args.subject, args.grade):
            print("%-13s %-28s %-46s %s" % (claim["grade"], claim["subject"], claim["predicate"], claim["witness"][:60]))
        return 0

    if args.command == "promote":
        current = strongest(data, args.subject)
        if current is None:
            print("no claim for %s" % args.subject)
            return 2
        if RANK[args.to] <= RANK[current["grade"]]:
            print("refusing: %s is already %s and %s is not higher" % (args.subject, current["grade"], args.to))
            return 3
        add(data, args.to, args.subject, current["predicate"], args.witness, args.round)
        save(data)
        print("promoted %s from %s to %s" % (args.subject, current["grade"], args.to))
        return 0

    if args.command == "check":
        problems = check(data)
        for problem in problems:
            print("PROBLEM: %s" % problem)
        print("%d claims, %d problems" % (len(data["claims"]), len(problems)))
        return 1 if problems else 0

    if args.command == "report":
        counts = {}
        for claim in data["claims"]:
            counts[claim["grade"]] = counts.get(claim["grade"], 0) + 1
        for grade in GRADES:
            print("%-13s %d" % (grade, counts.get(grade, 0)))
        print("")
        shapes = [c for c in data["claims"] if c["grade"] in ("GUESS", "SHAPE")]
        print("%d claims are proposals, not conclusions:" % len(shapes))
        for claim in shapes:
            print("    %-28s %s" % (claim["subject"], claim["predicate"][:70]))
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
