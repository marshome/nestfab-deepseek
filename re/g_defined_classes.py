# -*- coding: utf-8 -*-
"""A rule with a check: a class the RTTI names must have a DEFINITION, and a claim about classes must be about definitions.

WHERE THIS COMES FROM. A round reported "seven Engine classes defined". Six of them had a vtable address, three slot addresses and a table
row, and one had a class. The human found it, and the question they asked -- "can you not find this yourself" -- has an uncomfortable
answer: **the mechanism was there and it was aimed at the wrong thing.**

    lcns/tools/check_recovery.py: "OK: every class in include/lcns is named by a test"

That is about names THIS PROJECT DECLARED. `class` did not appear in engines.hpp except twice, so there was nothing to check -- and the
classes the RTTI names, which is the list that matters, were never compared against what exists.

    the ledger: "the Engine family is seven classes" at ORACLE

That is true of the RTTI and false of the code, and the ledger had no way to tell "has an address" from "has a definition".

WHAT THIS CHECKS: for every own class in re/vtables.json, whether a hand-written header declares it as a class or a struct. It reports the
counts per namespace and FAILS when a class that a hand-written header CLAIMS -- one whose constants or table rows exist -- has no
definition. That is the precise defect: not "sixty classes are undefined", which is work remaining, but "the file that lists seven says
they are classes while defining one".

    python g_defined_classes.py [--todo]
"""
import argparse
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

FOREIGN = ("N8CryptoPP", "N5boost", "N6Json", "N9__gnu_cxx", "NSt7__cxx11", "N10__cxxabiv1", "N6Locale", "NSt6locale",
           "N5Clp", "N4Coin", "N8CoinUtils", "N3Osi", "N3Cbc", "N11CoinPresolve", "N6Ipopt", "N5Ipopt")

# generated tables are not definitions
GENERATED = {"classes.hpp", "virtual_methods.hpp", "parameter_report.hpp", "option_keys.hpp", "miplib_names.hpp",
             "engine_defaults.hpp", "detail"}


def load_classes():
    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    out = []
    for mangled, entry in data.items():
        if any(mangled.startswith(prefix) for prefix in FOREIGN):
            continue
        qualified = (entry.get("demangled") or "").strip()
        if qualified:
            out.append(qualified)
    return sorted(set(out))


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--todo", action="store_true")
    args = parser.parse_args(argv)

    headers = {}
    for path in glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "**", "*.hpp"), recursive=True):
        name = os.path.basename(path)
        if name in GENERATED:
            continue
        headers[path] = io.open(path, encoding="utf-8", errors="replace").read()

    classes = load_classes()
    defined = {}
    for qualified in classes:
        short = qualified.split("::")[-1]
        if short.startswith("<"):                      # a substituted template parameter is not a class of ours
            continue
        for path, text in headers.items():
            if re.search(r"\b(?:class|struct)\s+%s\b" % re.escape(short), text):
                defined[qualified] = os.path.basename(path)
                break

    total = len(classes)
    print("classes the RTTI names: %d" % total)
    print("declared as class/struct in a hand-written header: %d" % len(defined))
    print("")

    # WHICH OF THE HEADERS CLAIM A FAMILY THEY DO NOT DEFINE. A header claims a class when it gives it constants or a table row by name.
    overclaims = []
    for path, text in headers.items():
        name = os.path.basename(path)
        for qualified in classes:
            short = qualified.split("::")[-1]
            # A SUBSTITUTED TEMPLATE PARAMETER IS NOT A CLASS OF OURS, and the first version of this filter let several through because
            # the marker sits mid-name -- `<subst>::thread::_State_impl::<Engine...` -- so the test is for the marker ANYWHERE.
            if len(short) < 6 or "<" in qualified or "subst" in qualified:
                continue
            # a claim: the short name appears as an identifier with a Constant or a table row, but is never declared
            mentions = len(re.findall(r"\b%s\b" % re.escape(short), text))
            if mentions < 2:
                continue
            if re.search(r"\b(?:class|struct)\s+%s\b" % re.escape(short), text):
                continue
            overclaims.append((name, qualified, mentions))

    # A CROSS-REFERENCE IS NOT AN OVER-CLAIM. A header that names a class DECLARED IN ANOTHER header is doing what headers are for, so the
    # defect is narrower than "named more than once here and not declared here": it is "named more than once and declared NOWHERE", which is
    # what a reader can mistake for a definition. The first version conflated the two and flagged three correct cross-references.
    declared_somewhere = set()
    for path, text_of in headers.items():
        for match in re.finditer(r"\b(?:class|struct)\s+(\w+)", text_of):
            declared_somewhere.add(match.group(1))
    overclaims = [row for row in overclaims if row[1].split("::")[-1] not in declared_somewhere]

    print("HEADERS THAT NAME A CLASS MORE THAN ONCE WITHOUT DECLARING IT: %d" % len(overclaims))
    for name, qualified, mentions in sorted(overclaims, key=lambda row: -row[2])[:20]:
        print("   %-24s %-34s %d mentions" % (name, qualified[:34], mentions))
    print("")

    if args.todo:
        print("the classes with no definition at all:")
        for qualified in classes:
            if qualified in defined or qualified.split("::")[-1].startswith("<"):
                continue
            print("   %s" % qualified)
        print("")

    if overclaims:
        print("FAILING: a header names a class repeatedly and never declares it, so a reader -- and a commit message -- can call it")
        print("defined when it is a constant. That is the defect this rule exists for.")
        return 1
    print("PASS: every class a header names more than once is declared in a header.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
