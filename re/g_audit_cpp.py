#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Is this C++, or a description of C++? A corrected audit.

THE PATTERN THIS REPLACES WAS WRONG, AND ITS OWN SELF-CHECK FOUND IT. The first version counted members with
`^\\s{4,}[\\w:<>,\\s\\*&\\[\\]]+\\s+\\w+\\s*(?:=|;|\\{...)`, which reported ZERO members for lcns/records.hpp -- a file that plainly has
`void** vtable = nullptr;`, `std::uint32_t wordA = 0;` and `std::byte unplaced[0x60 - 0x10]{};`. The pattern could not match them. **A
measurement that reports zero for a file you can read is a broken measurement**, so the self-check below asserts a KNOWN file's contents before
any verdict is printed.

WHAT MAKES A FILE NOT C++, decided here so the criteria can be argued with:

  * PLACEHOLDER CLASSES: a class body whose only line is a destructor. That is a name, and it is the shape a generator emits when it knows a
    class exists and nothing about it.
  * NO STATE AND NO BEHAVIOUR: no member lines and no function bodies. A file like that holds only constants and tables.
  * DATA-TABLE CONTENT: a file whose substantive lines are `{...}` rows or `constexpr` declarations.

  * AND A FILE IS FINE WHEN it declares members, or defines function bodies, or is a REGISTRY whose subject is genuinely a list -- exports,
    option names, benchmark names -- which is stated with a reason rather than assumed.

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

# A MEMBER LINE: four or more spaces of indent, ending in `;` or `{}` or an initialiser, and not a statement. Deliberately loose, because the
# strict version missed `void**` and `std::uint32_t` -- and the self-check below is what makes loose acceptable.
MEMBER = re.compile(r"^ {4,}(?!return\b|if\b|for\b|while\b|switch\b|else\b|case\b|using\b|typedef\b)(\S.*?);\s*(?://.*)?$", re.M)
FUNCTION = re.compile(r"^[ \t]*(?:inline\s+|static\s+|virtual\s+)?[\w:<>,\s\*&~]+\s+\w+\s*\([^;{]*\)\s*(?:const\s*)?(?:noexcept\s*)?\{", re.M)
TYPES = re.compile(r"^\s*(?:class|struct|union|enum)\s+\w+", re.M)
PLACEHOLDER_BODY = re.compile(r"(?:class|struct)\s+(\w+)\s*\{(?P<body>[^}]*)\}", re.S)
ONLY_DESTRUCTOR = re.compile(r"^\s*(?:virtual\s+)?~\w+\s*\(\s*\)\s*=\s*default\s*;", re.M)
CONSTEXPR = re.compile(r"^\s*(?:inline\s+)?constexpr\b", re.M)
TABLE_ROW = re.compile(r"^\s*\{\s*[\"']?\w", re.M)

REGISTRY = {
    "exports_forwarding.inc": "the forwarding table, one row per ordinal -- the module's own interface",
    "exports_impl.hpp": "the export registry, one entry per ordinal",
    "option_keys.hpp": "the option NAMES the module answers to, a list by nature",
    "miplib_names.hpp": "the 49 benchmark instance names, strings the module contains",
    "parameter_report.hpp": "the option name to offset map, whose subject IS the mapping",
    "trace.hpp": "the log prefixes, strings the module emits",
    "text_tags.hpp": "the geometry tag vocabulary from rodata, strings",
    "units.hpp": "unit conversion factors, values rather than addresses",
    "enums.hpp": "enum values the module's switch tables imply",
    "recovery.hpp": "the port's status per registry entry, a report",
}

SCAFFOLDING = {
    "class_definitions.hpp": "classes declared with nothing but a destructor -- a name and a comment, no members",
    "class_constructors.hpp": "one row per class: name, address, vtable, field COUNT; the fields themselves are not declared",
    "classes.hpp": "one row per class: mangled name, vtable, slot count",
    "virtual_methods.hpp": "one row per virtual slot: owner, index, address",
}


def measure(path):
    text = io.open(path, encoding="utf-8", errors="replace").read()
    placeholders = []
    for match in PLACEHOLDER_BODY.finditer(text):
        body = match.group("body")
        if len(ONLY_DESTRUCTOR.findall(body)) != 1:
            continue
        substantive = [line for line in body.split("\n")
                       if line.strip() and not line.strip().startswith(("public:", "private:", "protected:", "//", "/*", "*"))]
        if len(substantive) <= 1:
            placeholders.append(match.group(1))
    return {
        "name": os.path.basename(path),
        "types": len(TYPES.findall(text)),
        "members": len(MEMBER.findall(text)),
        "functions": len(FUNCTION.findall(text)),
        "constexprs": len(CONSTEXPR.findall(text)),
        "rows": len(TABLE_ROW.findall(text)),
        "placeholders": placeholders,
        "lines": text.count("\n") + 1,
    }


def self_check():
    """EXERCISE THE MEASUREMENT ON A FILE WHOSE CONTENT IS KNOWN, before any verdict is printed."""
    known = os.path.join(ROOT, "lcns", "include", "lcns", "records.hpp")
    if not os.path.exists(known):
        print("SELF-CHECK SKIPPED: records.hpp is gone")
        return True
    result = measure(known)
    ok = result["types"] == 2 and result["members"] >= 6
    print("SELF-CHECK on records.hpp: %d types (expect 2), %d members (expect 6+)  -- %s"
          % (result["types"], result["members"], "OK" if ok else "THE MEASUREMENT IS BROKEN"))
    if not ok:
        print("  records.hpp contains `void** vtable = nullptr;`, `std::uint32_t wordA = 0;` and `std::byte unplaced[...]{};`,")
        print("  so a count of fewer than six members means the pattern cannot see them and no verdict below is trustworthy.")
    return ok


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", action="store_true")
    parser.add_argument("--json")
    args = parser.parse_args(argv)

    if not self_check():
        return 2
    print("")

    rows = [measure(path) for path in sorted(glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "**", "*.hpp"), recursive=True))]
    for row in rows:
        row["registry"] = REGISTRY.get(row["name"])
        row["scaffolding"] = SCAFFOLDING.get(row["name"])

    if args.files:
        print("%-32s %5s %7s %6s %8s %5s %6s" % ("file", "types", "members", "funcs", "constexpr", "rows", "phold"))
        for row in sorted(rows, key=lambda r: (r["members"] + r["functions"], -r["lines"])):
            print("%-32s %5d %7d %6d %8d %5d %6d" % (row["name"][:32], row["types"], row["members"], row["functions"],
                                                      row["constexprs"], row["rows"], len(row["placeholders"])))
        return 0

    total_placeholders = sum(len(r["placeholders"]) for r in rows)
    print("headers: %d" % len(rows))
    print("")
    print("A. PLACEHOLDER CLASSES -- a body whose only line is a destructor: %d, in %d file(s)"
          % (total_placeholders, sum(1 for r in rows if r["placeholders"])))
    for row in rows:
        if row["placeholders"]:
            print("   %-30s %3d  %s%s" % (row["name"], len(row["placeholders"]),
                                          ", ".join(row["placeholders"][:5]),
                                          " ..." if len(row["placeholders"]) > 5 else ""))
    print("")

    empty = [r for r in rows if r["members"] == 0 and r["functions"] == 0 and not r["registry"]]
    print("B. NO STATE AND NO BEHAVIOUR (and not a stated registry): %d" % len(empty))
    for row in sorted(empty, key=lambda r: -r["lines"]):
        print("   %-30s %4d lines, %4d constexpr, %4d rows, %2d types" % (row["name"], row["lines"], row["constexprs"],
                                                                          row["rows"], row["types"]))
    print("")

    print("C. REGISTRIES -- a list IS the right shape, with the reason: %d present" % sum(1 for r in rows if r["registry"]))
    for row in rows:
        if row["registry"]:
            print("   %-30s %s" % (row["name"], row["registry"]))
    print("")

    print("D. SCAFFOLDING -- generated as a name and an address: %d" % sum(1 for r in rows if r["scaffolding"]))
    for row in rows:
        if row["scaffolding"]:
            print("   %-30s %s" % (row["name"], row["scaffolding"]))
    print("")

    verdict = total_placeholders > 0 or empty or any(r["scaffolding"] for r in rows)
    if verdict:
        print("VERDICT: NOT a reconstruction. %d placeholder classes, %d files with neither state nor behaviour, %d scaffolding files."
              % (total_placeholders, len(empty), sum(1 for r in rows if r["scaffolding"])))
        print("The module's own content -- a class's members, its virtuals, its constructor -- is in tables and constants rather than in types.")
    else:
        print("VERDICT: every header declares members, defines behaviour, or is a registry with a stated reason.")
    print("")
    print("HOW TO CATCH THIS NEXT TIME: this script, and its SELF-CHECK. The check exercises the measurement on a file whose content is known")
    print("before printing any verdict, because the first version of this script reported zero members for a file full of them -- **a broken")
    print("measurement produces confident nonsense, and only a known input catches it.**")

    if args.json:
        io.open(args.json, "w", encoding="utf-8", newline="\n").write(json.dumps(rows, indent=1, sort_keys=True))
        print("wrote %s" % args.json)
    return 1 if verdict else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
