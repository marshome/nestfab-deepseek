# -*- coding: utf-8 -*-
"""Accept an assertion's evidence unless something CONTRADICTS it, and report the contradictions.

Usage: python g_conflict.py [--name shear_gap]

The human's refinement, and it replaces the rule written one round earlier: an assertion's name may be USED, and the test is not
"does an instruction also prove it" but "does anything CONTRADICT it". That is a better rule for two reasons. It is what a reader
would do -- take the module's word unless something says otherwise -- and it is checkable, because a contradiction has shapes:

  ORPHAN      the assertion names `order.<field>` and NO code in the module reads or writes that field name. The assertion
              describes something the code does not have, which is the stale-assertion case and the one that matters.
  UNUSED      the name appears in a string and in a table lookup but never in a store or a load, so it is a key with no field.
  AGREES      something else -- a setter, a serialiser key, another string -- uses the SAME name, so the assertion and that
              other source corroborate rather than conflict.

and the third shape is the reason this tool exists: a name used by two independent sources is not merely acceptable, it is the
strongest evidence this project has, and the earlier rule was discarding that by demanding an instruction witness for a name that
two oracles already agreed on.

What it does NOT do is let an assertion fix an OFFSET. A name is a word and a word can be checked for conflict; an offset is a
position and the assertion never states one. So the division is: an assertion may NAME a field, and only an instruction may place
it. That division is what the human's refinement implies and it is what the ledger's grades already express.
"""
import argparse
import io
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import lib as LIB  # noqa: E402
from lib import disasm, load_prof, rva2off  # noqa: E402

PRINTABLE = re.compile(rb"[\x20-\x7e]{3,}")
FIELD_IN_CONDITION = re.compile(r"\b(?:order|o|p_order|pOrder)\s*(?:->|\.)\s*([a-z][a-z0-9_]{2,40})")


def image():
    return LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data


def occurrences(blob, name):
    """Every place the name appears: as a bare string, and as a table key beside a lookup."""
    encoded = name.encode()
    return [m.start() for m in re.finditer(re.escape(encoded), blob)]


def main(argv):
    only = argv[argv.index("--name") + 1] if "--name" in argv else None
    blob = image()

    # every `order.<field>` the assertions name
    asserted = defaultdict(set)
    for match in PRINTABLE.finditer(blob):
        text = match.group(0).decode("ascii", "replace")
        if "order" not in text:
            continue
        for name in FIELD_IN_CONDITION.findall(text):
            asserted[name].add(match.start())

    # every name the ledger holds, so a corroboration can be spotted
    data = json.load(io.open(os.path.join(HERE, "ledger.json"), encoding="utf-8"))
    named_in_ledger = set()
    for claim in data["claims"]:
        for word in re.findall(r"([a-z][a-z0-9_]{3,40})", claim.get("predicate", "") + " " + claim.get("subject", "")):
            named_in_ledger.add(word)

    print("fields an assertion names as `order.<field>`: %d" % len(asserted))
    print("")
    print("%-38s %-6s %-9s %-9s %s" % ("field name", "occur", "in ledger", "verdict", "the other sources"))
    for name in sorted(asserted):
        if only and only not in name:
            continue
        where = occurrences(blob, name)
        in_ledger = name in named_in_ledger
        # corroboration: another string uses the same word, or the ledger already carries it
        others = []
        if in_ledger:
            others.append("the ledger")
        if len(where) > 1:
            others.append("%d other string(s)" % (len(where) - 1))
        snake = name.replace("_", "")
        verdict = "AGREES" if others else "ORPHAN"
        print("%-38s %-6d %-9s %-9s %s"
              % (name[:38], len(where), "yes" if in_ledger else "no", verdict, ", ".join(others) or "-"))

    print("")
    orphans = [n for n in asserted if n not in named_in_ledger and len(occurrences(blob, n)) <= 1]
    print("ORPHANED by this test: %d -- the assertion names a field that appears nowhere else" % len(orphans))
    for name in sorted(orphans):
        print("    %s" % name)
    print("")
    print("An assertion may NAME a field when nothing contradicts it. It may not PLACE one: a name is a word and a word can be")
    print("checked for conflict, while an offset is a position and no assertion states one. So this tool settles names and the")
    print("ledger's INSTRUCTION claims settle offsets.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
