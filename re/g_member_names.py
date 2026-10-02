# -*- coding: utf-8 -*-
"""Member names the module spells out inside its assertion and log strings.

Usage: python g_member_names.py [--pattern m_] [--context 60]

The naming channels this project has used read the function name out of `__PRETTY_FUNCTION__`-style strings and the method
name out of an assertion's second argument. Both give FUNCTIONS. A third channel was sitting in the same bytes and nobody read
it: an assertion that reaches a member writes the member expression into the condition string --

    part_index < nesting->nesting->multitorch_infos().m_infos.size()

so `multitorch_infos`, `m_infos`, `nesting` and `part_index` are names the MODULE gives to things, and two of them are members
(`m_infos` on the object `multitorch_infos()` returns, and `nesting` on the nesting). That is oracle-grade evidence for a FIELD,
which is exactly what the campaign to name the launch order's 70 unnamed offsets lacks.

This prints every such string with its file offset, and separates the three things one can carry:

    a MEMBER ACCESS     `x.m_foo` or `x->foo` -- a member name, and the receiver before the dot or arrow
    a LOCAL or PARAMETER   `part_index < ...` -- a name in a signature, useful for parameters
    a TYPE              `std::vector<...>` -- a library type, classified rather than named

A member name is evidence for a field only with its receiver, and the receiver is usually a call whose return type this project
may or may not know. So the output pairs each member with the expression before it, and nothing is promoted to a field name
without that pairing.
"""
import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib as LIB  # noqa: E402

MEMBER = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*(?:\.|->)\s*([A-Za-z_][A-Za-z0-9_]*)\s*(\(\))?")
CONDITION = re.compile(rb"[ -~]{12,}")


def strings(blob, minimum=24):
    for match in CONDITION.finditer(blob):
        text = match.group(0).decode("ascii", "replace")
        if len(text) >= minimum and ("->" in text or "." in text):
            yield match.start(), text


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", default=None, help="only strings containing this")
    parser.add_argument("--context", type=int, default=70)
    parser.add_argument("--limit", type=int, default=60)
    args = parser.parse_args(argv)

    blob = LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data
    found = []
    for offset, text in strings(blob):
        if args.pattern and args.pattern not in text:
            continue
        members = [(m.group(1), m.group(2), bool(m.group(3))) for m in MEMBER.finditer(text)]
        if not members:
            continue
        found.append((offset, text, members))

    print("strings that spell out a member expression: %d" % len(found))
    print("")
    receivers = {}
    for offset, text, members in found[:args.limit]:
        print("0x%06X  %s" % (offset, text[:110]))
        for receiver, member, is_call in members:
            print("            %s%s%s" % (receiver, "." if not is_call else "->", member))
            receivers.setdefault(member, set()).add(receiver)
        print("")
    print("the member names, and the receivers they appear on:")
    for member in sorted(receivers):
        print("    %-30s on %s" % (member, ", ".join(sorted(receivers[member])[:4])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
