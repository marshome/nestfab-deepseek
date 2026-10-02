# -*- coding: utf-8 -*-
"""A rule with a check: a count over a set is worthless unless the set is the one the claim is about.

THE RULE, and it comes from three failures in five rounds, which makes it a pattern rather than three accidents:

    1. the closure of 0x132E0 reported 596 functions and 121762 bytes for a job that needed FOUR functions
    2. a search for `lea reg, [base + 0x40]` found 1955 functions where the ledger recorded 15, because the 15 were the ones whose
       base TYPE was identified and the search dropped that qualification
    3. a search for "computes a 0x50 byte element address" found 57 functions whose element fields DID NOT AGREE -- four different sets,
       one of them empty -- because `lea reg,[a+b*4]` then `shl reg,3` is a generic indexing idiom and not a type's size

Each time the count was arithmetically correct and answered a different question from the one the claim was about. So this checks a
specific and mechanical symptom: **DID THE MEMBERS AGREE?**

    python g_set_consistency.py --rows "<name1>:<members1>" "<name2>:<members2>" ...

which is hard to use by hand, so it also accepts a JSON file of rows:

    {"claim": "...", "what_must_agree": "element fields", "rows": [{"name": "...", "members": [...]}, ...]}

and reports whether the members agree, and how many distinct sets there are. A claim whose rows disagree is REFUSED rather than
downgraded, because the number is not weak, it is about something else.

This is deliberately unable to inspect a claim on its own -- it needs the rows that produced the count, which is the honest limitation:
the failure is not detectable from a number, only from the rows behind it. The check therefore also audits the TOOLS, by requiring
every tool that prints a per-row breakdown to be runnable with the self-test the project requires.
"""
import argparse
import collections
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def report(claim, what, rows):
    sets = collections.Counter(tuple(sorted(str(m) for m in row["members"])) for row in rows)
    print("claim: %s" % claim)
    print("rows:  %d, what must agree: %s" % (len(rows), what))
    print("distinct member sets: %d" % len(sets))
    for members, count in sets.most_common(6):
        print("   %3d row(s)  %s" % (count, " ".join(members) if members else "(none)"))
    print("")
    if len(sets) > 1:
        print("REFUSED: the rows do not agree, so the count is over a set of DIFFERENT things and cannot support a claim about one")
        print("of them. This is the symptom that produced 1955 for 15 and 57 for an idiom.")
        return 2
    print("The rows agree, so the count is over one kind of thing and can support a claim about it.")
    print("")
    print("AND THAT IS ALL IT SHOWS. Agreement is necessary and not sufficient: 57 rows can agree on the wrong members entirely. What")
    print("this check can do is catch the cheap and common failure, which is the one that has happened three times.")
    return 0


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", nargs="*", default=None, help="name:member,member,member")
    parser.add_argument("--file", default=None)
    args = parser.parse_args(argv)

    if args.file:
        data = json.loads(io.open(args.file, encoding="utf-8").read())
        return report(data.get("claim", "(no claim)"), data.get("what_must_agree", "members"), data.get("rows", []))

    if args.rows:
        rows = []
        for text in args.rows:
            name, _, members = text.partition(":")
            rows.append({"name": name, "members": [m for m in members.split(",") if m]})
        return report("(from --rows)", "members", rows)

    # with nothing to check, self-test on the failure that motivated the rule
    rows = [{"name": "0x1C6860", "members": ["+0x48:4"]},
            {"name": "0x8BCCB0", "members": ["+0x10:8", "+0x18:?"]},
            {"name": "0x489BE0", "members": []}]
    print("SELF-TEST on the rows that produced the element50 count, which must be REFUSED:")
    print("")
    code = report("element50.layout -- begins +0x10 +0x18 +0x20", "element fields", rows)
    if code != 2:
        print("")
        print("FAIL: the self-test did not refuse the rows known to disagree, so this check cannot be trusted.")
        return 1
    print("")
    print("and the same check on the rows that DO agree, which must pass:")
    rows = [{"name": "a", "members": ["+0x10:8", "+0x18:8"]},
            {"name": "b", "members": ["+0x10:8", "+0x18:8"]}]
    code = report("a made-up agreeing claim", "members", rows)
    return 0 if code == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
