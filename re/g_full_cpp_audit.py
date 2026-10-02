#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A full audit of the C++ tree: which files hold CODE, which hold DATA ABOUT code, and which hold plausible-looking fabrications.

THE THREE VERDICTS, and every file gets exactly one:

  * CODE -- declares types with members, or defines behaviour. The class work that was read from a constructor and a run.
  * DATA -- a registry whose subject genuinely IS a list: the module's exports, its option names, its RTTI. Legitimate, and named with a reason.
  * FABRICATED -- members or offsets that no instruction supports. **This is the category the human has been pointing at**, and the tests for it
    are mechanical:

        an `at_XXXX` member          a position wearing a name-shaped label
        a store to [rsp + ...] used as a field   the STACK is not the object
        offset comments on every member          the evidence has become the content
        a placeholder class          a name and a destructor, no members

    python g_full_cpp_audit.py [--files] [--json re/full_cpp_audit.json]
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

# REGISTRIES -- a list IS the right shape, each with the reason it is not a fabrication.
REGISTRY = {
    "exports_forwarding.inc": "one row per exported ordinal -- the module's own interface",
    "exports_impl.hpp": "the export registry",
    "option_keys.hpp": "the option NAMES the module answers to",
    "miplib_names.hpp": "the benchmark instance names the module contains",
    "parameter_report.hpp": "the option name to offset map, whose subject IS the mapping",
    "trace.hpp": "the log prefixes the module emits",
    "text_tags.hpp": "the geometry tag vocabulary from rodata",
    "units.hpp": "unit conversion factors, values",
    "enums.hpp": "enum values the module's switch tables imply",
    "recovery.hpp": "the port's status per registry entry, a report",
}

# THE FABRICATED PATTERNS, each with the reason it is one.
#
# **THE FIRST VERSION OF THE STACK TEST WAS WRONG AND THE HUMAN'S REPOSITORY CAUGHT IT**: it flagged any line mentioning `mov [rsp + ...]`,
# which is how a COMMENT cites a stack store as evidence -- legitimate, and present in geom.hpp, variant.hpp and licensing.cpp. **A check that
# flags correct code gets switched off.** The fabricated form is narrower: a MEMBER DECLARATION (four or more spaces of indent, ending in a
# semicolon) whose trailing comment cites a stack store as the thing that places it. `void* at_0020 = {}; // +0x20, RE .. mov [rsp+0x20], rax`.
FABRICATED = [
    (re.compile(r"\bat_[0-9A-Fa-f]{4}\b"), "a member named after its own offset"),
    (re.compile(r"^ {4,}\S.*;\s*//[^\n]*mov\s+\w+\s+ptr\s+\[rsp\s*\+", re.M), "a MEMBER whose comment cites a STACK store"),
    (re.compile(r"unplaced_[0-9A-Fa-f]{4}"), "an unplaced byte region standing in for a type"),
]

PLACEHOLDER = re.compile(r"(?:class|struct)\s+(\w+)\s*\{(?P<body>[^}]*)\}", re.S)
ONLY_DESTRUCTOR = re.compile(r"^\s*(?:virtual\s+)?~\w+\s*\(\s*\)\s*=\s*default\s*;", re.M)
MEMBER = re.compile(r"^ {4,}(?!return\b|if\b|for\b|while\b|switch\b|else\b|case\b|using\b|typedef\b)(\S.*?);\s*(?://.*)?$", re.M)
FUNCTION = re.compile(r"^[ \t]*(?:inline\s+|static\s+|virtual\s+)[\w:<>,\s\*&~]*\s+\w+\s*\([^;{]*\)\s*(?:const\s*)?(?:noexcept\s*)?\{", re.M)
TYPES = re.compile(r"^\s*(?:class|struct|union|enum)\s+\w+", re.M)
ADDRESS = re.compile(r"0x[0-9A-Fa-f]{5,}")
# AN OFFSET COMMENT ON A MEMBER: `// +0x18` at the end of a line that declares something
OFFSET_COMMENT = re.compile(r";\s*//\s*\+0x[0-9A-Fa-f]+")


def audit(path):
    name = os.path.basename(path)
    text = io.open(path, encoding="utf-8", errors="replace").read()
    lines = text.count("\n") + 1
    member_lines = MEMBER.findall(text)

    fabricated_hits = []
    for pattern, reason in FABRICATED:
        hits = pattern.findall(text)
        if hits:
            fabricated_hits.append((reason, len(hits)))

    placeholders = []
    for match in PLACEHOLDER.finditer(text):
        body = match.group("body")
        if len(ONLY_DESTRUCTOR.findall(body)) == 1:
            substantive = [line for line in body.split("\n")
                           if line.strip() and not line.strip().startswith(("public:", "private:", "protected:", "//", "/*", "*"))]
            if len(substantive) <= 1:
                placeholders.append(match.group(1))

    offset_comments = len(OFFSET_COMMENT.findall(text))
    return {
        "name": name,
        "lines": lines,
        "types": len(TYPES.findall(text)),
        "members": len(member_lines),
        "functions": len(FUNCTION.findall(text)),
        "addresses": len(ADDRESS.findall(text)),
        "offset_comments": offset_comments,
        "placeholders": placeholders,
        "fabricated": fabricated_hits,
        "registry": REGISTRY.get(name),
    }


def verdict(row):
    if row["fabricated"]:
        return "FABRICATED"
    if row["placeholders"]:
        return "FABRICATED"
    if row["registry"]:
        return "DATA"
    if row["members"] == 0 and row["functions"] == 0:
        return "DATA" if row["addresses"] or row["types"] == 0 else "EMPTY"
    # MANY OFFSET COMMENTS PER MEMBER means the evidence became the content
    if row["members"] and row["offset_comments"] > row["members"]:
        return "OFFSET-HEAVY"
    return "CODE"


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", action="store_true")
    parser.add_argument("--json")
    args = parser.parse_args(argv)

    rows = []
    for pattern in ("**/*.hpp", "**/*.cpp"):
        for path in glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", pattern), recursive=True):
            rows.append(audit(path))
        for path in glob.glob(os.path.join(ROOT, "lcns", "src", "*.cpp")):
            rows.append(audit(path))
    for row in rows:
        row["verdict"] = verdict(row)

    if args.files:
        print("%-32s %-11s %5s %7s %6s %6s %8s" % ("file", "verdict", "types", "members", "funcs", "consts", "offset//"))
        for row in sorted(rows, key=lambda r: (r["verdict"], -r["lines"])):
            print("%-32s %-11s %5d %7d %6d %6d %8d" % (row["name"][:32], row["verdict"], row["types"], row["members"],
                                                       row["functions"], row["addresses"], row["offset_comments"]))
        return 0

    counts = {}
    for row in rows:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    print("files audited: %d" % len(rows))
    print("")
    for name in ("CODE", "DATA", "OFFSET-HEAVY", "EMPTY", "FABRICATED"):
        print("   %-14s %d" % (name, counts.get(name, 0)))
    print("")

    for name in ("FABRICATED", "OFFSET-HEAVY", "EMPTY"):
        group = [r for r in rows if r["verdict"] == name]
        if not group:
            continue
        print("%s:" % name)
        for row in sorted(group, key=lambda r: -r["lines"]):
            why = []
            for reason, count in row["fabricated"]:
                why.append("%d x %s" % (count, reason))
            if row["placeholders"]:
                why.append("%d placeholder class(es)" % len(row["placeholders"]))
            if row["verdict"] == "OFFSET-HEAVY":
                why.append("%d offset comments for %d members" % (row["offset_comments"], row["members"]))
            if row["verdict"] == "EMPTY":
                why.append("no members and no functions")
            print("   %-30s %s" % (row["name"][:30], "; ".join(why)))
        print("")

    print("CODE and DATA are as expected. **A FABRICATED file is one whose content no instruction supports**, and the tests for it are the")
    print("three patterns above -- which were each found in this repository by the human, not by a tool.")
    if args.json:
        io.open(args.json, "w", encoding="utf-8", newline="\n").write(json.dumps(rows, indent=1, sort_keys=True))
        print("wrote %s" % args.json)
    return 1 if counts.get("FABRICATED") else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
