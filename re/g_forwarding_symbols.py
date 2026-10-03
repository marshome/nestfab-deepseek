# -*- coding: utf-8 -*-
"""For the 39 forwarded ordinals whose wrapper does not dispatch, ask whether the named symbol EXISTS.

**TWO FAILURES LOOK THE SAME FROM THE LIST AND ARE DIFFERENT IN THE TREE:**

  * the symbol exists in `exports_impl.cpp` and nothing calls it -- **dead code behind a forwarding entry that claims it runs**;
  * the symbol does not exist at all -- **a forwarding entry naming an implementation that was never written**, which `exports.cpp`'s `forwards()` will still
    report as `Status::Forwarded`.

**AND `kForwarding` IS HAND-WRITTEN**, which its own header says first: "HAND-WRITTEN, not generated. ... Every line here is a claim that the named implementation
agrees with the assembly at the entry point." **So a line naming a missing symbol is a claim without a subject.**
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
API = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")
FWD = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")
IMPL = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")
HEADER = os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp")


def main():
    api = io.open(API, encoding="utf-8", errors="replace").read()
    forwarding = io.open(FWD, encoding="utf-8", errors="replace").read()
    impl = io.open(IMPL, encoding="utf-8", errors="replace").read()
    header = io.open(HEADER, encoding="utf-8", errors="replace").read()

    entries = [(int(m.group(1)), m.group(2)) for m in
               re.finditer(r"^\s*\{(\d+),\s*reinterpret_cast<void\*>\(&([\w:]+)\)\}", forwarding, re.M)]
    wrappers = {}
    for match in re.finditer(r'extern "C"[^;{]*?\b(\w+)\s*\([^)]*\)\s*\{(.*?)\n\}', api, re.S):
        wrappers[match.group(1)] = " ".join(match.group(2).split())
    rows = re.findall(r'\{"([^"]+)",\s*(\d+),\s*(\d+),', api)
    name_of = {int(row[1]): row[0] for row in rows}

    defined = set(re.findall(r"^(?:extern \"C\" )?[\w:<>*&\s]*?\b(\w+)\s*\([^;{]*\)\s*\{", impl, re.M))
    declared = set(re.findall(r"\b(\w+)\s*\([^;]*\)\s*;", header))

    rows_out = []
    for ordinal, symbol in sorted(entries):
        name = name_of.get(ordinal, "")
        body = wrappers.get(name, "")
        if "impl::" in body:
            continue
        short = symbol.split("::")[-1]
        rows_out.append((ordinal, name, short, short in defined, short in declared))

    exist = sum(1 for row in rows_out if row[3])
    print("forwarded ordinals whose wrapper does not dispatch: %d" % len(rows_out))
    print("   of which the named symbol IS defined in exports_impl.cpp: %d   <- DEAD CODE BEHIND A FORWARDING CLAIM" % exist)
    print("   of which it is NOT defined:                               %d   <- A CLAIM WITH NO SUBJECT" % (len(rows_out) - exist))
    print("")
    print("%-5s %-34s %-40s %-9s %s" % ("ord", "export", "named implementation", "defined", "declared"))
    for ordinal, name, short, is_defined, is_declared in rows_out:
        print("%-5d %-34s %-40s %-9s %s"
              % (ordinal, name[:34], short[:40], "yes" if is_defined else "**NO**", "yes" if is_declared else "no"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
