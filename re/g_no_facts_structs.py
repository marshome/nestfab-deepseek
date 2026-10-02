#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A rule with a check: no type may be named `<AnExistingClass><ASuffixMeaningDescription>`.

THE HUMAN NAMED THE PATTERN, AND IT IS THE WHOLE SESSION: "Fields deleted, and then you made Members." Both were a type holding facts about a
class, written beside the class. The whole list from this repository:

    nesting_nester_fields.hpp   a FieldStore table for Multi::NestingNester      -- DELETED
    nesting_nester_layout.hpp   NestingNesterLayout for Multi::NestingNester     -- DELETED
    named_members.hpp           24 XxxMembers structs, 22 of them for classes that exist -- DELETED
    class_constructors.hpp      93 rows keyed by class name                      -- DELETED
    class_definitions.hpp       47 rows AND 46 placeholder classes
    classes.hpp                 96 rows: ClassInfo
    virtual_methods.hpp         384 rows: VirtualSlot

**AND THE FIRST ATTEMPT AT THIS CHECK WAS TOO BROAD**, which is worth recording: it flagged every type ending in `Record`, including
`RunRecord` and `PolymorphicRecord`, which ARE things rather than descriptions of things. **The defect is narrower: a type whose name is an
EXISTING CLASS followed by a suffix.** That is mechanical, and it is exactly the shape the human kept finding.

    python g_no_facts_structs.py [--list]
"""
import argparse
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INCLUDE = os.path.join(ROOT, "lcns", "include", "lcns")

# THE SUFFIXES THAT TURN A CLASS'S NAME INTO A DESCRIPTION OF IT
SUFFIXES = ("Members", "Layout", "Fields", "Info", "Facts", "Desc", "Descriptor", "Data", "Table", "Rows")
# A ROW OF A REGISTRY IS NOT A DESCRIPTION OF ONE CLASS. These registries ARE this project's deliverable: the module's own class list, its
# virtual slot list, its exports. Their row types are named here with the reason, so the exemption can be argued with.
REGISTRY_TYPES = {
    "ClassInfo": "a row of the RTTI class registry, which is the module's own list and a deliverable",
    "VirtualSlot": "a row of the virtual slot registry",
    "ClassFacts": "a row of the same registry",
    "ExportInfo": "a row of the export registry",
}


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)

    # every class and struct declared anywhere, with where
    declared = {}
    for path in sorted(glob.glob(os.path.join(INCLUDE, "**/*.hpp"), recursive=True)):
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for match in re.finditer(r"\b(?:struct|class)\s+(\w+)\b", text):
            declared.setdefault(match.group(1), os.path.basename(path))

    findings = []
    for path in sorted(glob.glob(os.path.join(INCLUDE, "**/*.hpp"), recursive=True)):
        name = os.path.basename(path)
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for match in re.finditer(r"\b(?:struct|class)\s+(\w+)\b", text):
            type_name = match.group(1)
            if type_name in REGISTRY_TYPES:
                continue
            for suffix in SUFFIXES:
                if not type_name.endswith(suffix) or len(type_name) <= len(suffix):
                    continue
                base = type_name[: -len(suffix)]
                if base in declared and not base.endswith(("Layer",)):
                    findings.append((name, type_name, base, declared[base]))
                break

    if args.list:
        for row in findings:
            print("   %-26s %-30s describes %s (in %s)" % row)
        return 0

    print("types named as a DESCRIPTION of a class declared elsewhere: %d" % len(findings))
    for file_name, type_name, base, where in findings:
        print("   %-26s %-30s describes %s (declared in %s)" % (file_name, type_name, base, where))
    print("")
    if findings:
        print("FAILING: a type named `<Class><Members|Layout|Fields|Info|Facts>` holds facts ABOUT that class, and the class is where they")
        print("belong -- as its own constants and members. **This is the defect the human found four times under four names**:")
        print("nesting_nester_fields.hpp, nesting_nester_layout.hpp, named_members.hpp and class_constructors.hpp were each a description of a")
        print("class that already existed. Put the facts in the class, or leave them in the table they came from, and do NOT generate a fifth")
        print("name for them.")
        return 1
    print("PASS: no type is named as a description of a class declared elsewhere.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
