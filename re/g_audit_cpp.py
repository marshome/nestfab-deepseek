#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Is this file C++, or is it a description of C++? A measurable audit of every generated and hand-written header.

THE HUMAN ASKED THREE THINGS: are class_constructors.hpp and class_definitions.hpp reverse engineering, check the generated code all the way,
and how can this be caught automatically next time. This answers all three with one measurement, because **the first two questions are the same
question and the third is "run this measurement every time".**

WHAT MAKES A FILE NOT C++. Decided here, so it can be argued with rather than assumed:

  * A TYPE WITH NO MEMBERS AND NO BEHAVIOUR. `class Foo { public: virtual ~Foo() = default; };` is a declaration that a name exists, with a
    comment saying what its first virtual is. **It is a placeholder.** Real reverse engineering writes the class's members and its virtual
    methods, because those are what the vtable and the instructions give.
  * A FILE WHOSE CONTENT IS TABLES OF NUMBERS with no type that has members. A registry of exports is legitimate -- it IS the module's
    interface -- but a table of "class, address, slot count" is a data dump wearing a header's filename.

  * AND A FILE IS FINE WHEN: it declares types with members, or defines functions, or is a registry whose subject is genuinely a list
    (exports, strings, option names). **Behaviour and state are the test; a name and an address are not.**

    python g_audit_cpp.py [--files] [--json re/cpp_audit.json]
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

# A PLACEHOLDER CLASS: a class body whose only member is a destructor. Written as a pattern rather than a heuristic because the shape is
# exactly what a generator emits when it knows a class exists and nothing about it.
PLACEHOLDER = re.compile(
    r"class\s+(\w+)\s*\{(?P<body>[^}]*)\}",
    re.S)
DESTRUCTOR_ONLY = re.compile(r"^\s*(?:virtual\s+)?~\w+\s*\(\s*\)\s*=\s*default\s*;", re.M)

# A TYPE WITH REAL CONTENT: a class or struct with at least one data member, or a method with a body.
TYPES = re.compile(r"^\s*(?:class|struct)\s+(\w+)", re.M)
DATA_MEMBER = re.compile(r"^\s{4,}[\w:<>,\s\*&\[\]]+\s+\w+\s*(?:=|;|\{[^}]*\})\s*(?://.*)?$", re.M)
FUNCTION_BODY = re.compile(r"^\s*(?:inline\s+|static\s+)?[\w:<>,\s\*&]+\s+\w+\s*\([^;{]*\)\s*(?:const\s*)?\{", re.M)

# LEGITIMATE REGISTRIES: files whose subject IS a list. Named with the reason, because a reason is what separates a registry from a dump.
REGISTRY = {
    "exports_forwarding.inc": "the forwarding table, one row per ordinal",
    "option_keys.hpp": "the option NAMES the module answers to, which is a list by nature",
    "miplib_names.hpp": "the 49 benchmark instance names, which are strings the module contains",
    "parameter_report.hpp": "the option name to offset map, whose subject is the mapping",
    "trace.hpp": "the log prefixes, which are strings the module emits",
    "text_tags.hpp": "the geometry tag vocabulary read from rodata, which are strings",
    "units.hpp": "unit conversion factors, which are values",
}

# THE SCAFFOLDING, NAMED. Files that were generated as placeholders and need to become types or go.
SCAFFOLDING = {
    "class_definitions.hpp": "46 classes declared with nothing but a destructor -- a name and a slot-2 comment, no members",
    "class_constructors.hpp": "one row per class: name, constructor address, vtable, field COUNT -- the class's fields are not declared",
    "classes.hpp": "one row per class: mangled name, vtable, slot count",
    "virtual_methods.hpp": "one row per virtual slot: owner, index, address",
    "recovery.hpp": "the port's status per registry entry, which is a report rather than code",
}


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", action="store_true")
    parser.add_argument("--json")
    args = parser.parse_args(argv)

    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "**", "*.hpp"), recursive=True)):
        name = os.path.basename(path)
        text = io.open(path, encoding="utf-8", errors="replace").read()

        placeholders = []
        for match in PLACEHOLDER.finditer(text):
            body = match.group("body")
            if DESTRUCTOR_ONLY.search(body) and len(DESTRUCTOR_ONLY.findall(body)) == 1:
                # a body whose only member-looking line is the destructor
                stripped = [line for line in body.split("\n")
                            if line.strip() and not line.strip().startswith(("public:", "private:", "protected:", "//", "/*", "*"))]
                if len(stripped) <= 1:
                    placeholders.append(match.group(1))

        rows.append({
            "name": name,
            "types": len(TYPES.findall(text)),
            "members": len(DATA_MEMBER.findall(text)),
            "functions": len(FUNCTION_BODY.findall(text)),
            "placeholders": len(placeholders),
            "placeholder_names": placeholders,
            "lines": text.count("\n") + 1,
            "registry": REGISTRY.get(name),
            "scaffolding": SCAFFOLDING.get(name),
        })

    if args.files:
        print("%-36s %5s %7s %6s %6s %6s" % ("file", "types", "members", "funcs", "phold", "lines"))
        for row in sorted(rows, key=lambda r: -r["placeholders"]):
            print("%-36s %5d %7d %6d %6d %6d" % (row["name"][:36], row["types"], row["members"],
                                                 row["functions"], row["placeholders"], row["lines"]))
        return 0

    total_placeholders = sum(r["placeholders"] for r in rows)
    print("headers: %d" % len(rows))
    print("PLACEHOLDER CLASSES -- a name and a destructor, no members: %d, in %d file(s)"
          % (total_placeholders, sum(1 for r in rows if r["placeholders"])))
    print("")
    for row in sorted(rows, key=lambda r: -r["placeholders"]):
        if not row["placeholders"]:
            continue
        print("   %-30s %3d placeholder(s), %4d types, %4d members" % (row["name"], row["placeholders"],
                                                                       row["types"], row["members"]))
        if row["placeholder_names"]:
            print("        %s%s" % (", ".join(row["placeholder_names"][:6]),
                                    " ..." if len(row["placeholder_names"]) > 6 else ""))
    print("")

    print("SCAFFOLDING -- generated files that are a name and an address rather than a type: %d" % len(SCAFFOLDING))
    for name, why in sorted(SCAFFOLDING.items()):
        row = next((r for r in rows if r["name"] == name), None)
        state = "PRESENT" if row else "gone"
        print("   %-30s %-8s %s" % (name, state, why))
    print("")

    print("REGISTRIES -- a list is the right shape for these, with the reason: %d" % len(REGISTRY))
    for name, why in sorted(REGISTRY.items()):
        row = next((r for r in rows if r["name"] == name), None)
        print("   %-30s %-8s %s" % (name, "PRESENT" if row else "gone", why))
    print("")

    verdict = total_placeholders > 0 or any(r["scaffolding"] for r in rows)
    if verdict:
        print("VERDICT: **the generated code is NOT a reconstruction.** %d placeholder classes and %d scaffolding files describe the"
              % (total_placeholders, sum(1 for r in rows if r["scaffolding"])))
        print("module without implementing it. A class the RTTI names is a starting POINT: its members come from the instructions that write")
        print("them and its virtuals from the slots, which is what re/g_find_ctors.py and re/g_class_fields.py already compute.")
    else:
        print("VERDICT: every header either declares types with members, defines behaviour, or is a registry with a stated reason.")
    print("")
    print("**HOW TO CATCH THIS NEXT TIME**: this script. `placeholders` counts classes whose body is a destructor and nothing else, which is")
    print("the exact shape a generator emits when it knows a name and no content -- so a generator that produces one is caught by running it.")

    if args.json:
        io.open(args.json, "w", encoding="utf-8", newline="\n").write(json.dumps(rows, indent=1, sort_keys=True))
        print("wrote %s" % args.json)
    return 1 if verdict else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
