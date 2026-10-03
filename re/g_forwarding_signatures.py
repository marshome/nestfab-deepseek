# -*- coding: utf-8 -*-
"""For the forwarded ordinals whose wrapper does not dispatch, print the MODULE's argument registers so the wrapper's signature can be derived.

**THE INFERRED TABLE'S SIGNATURES ARE THE THING THAT IS WRONG**, and two rounds have now shown the same failure: `(Order, int)` by value where the module writes
through `rcx`. This reads each function's first instructions and reports which of rcx, rdx, r8, r9 it actually USES, **which is the arity and the kind, and not a
guess about it.**

    python -u g_forwarding_signatures.py
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

API = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")
FWD = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")

ARGUMENTS = ("rcx", "rdx", "r8", "r9")
# the 32-bit halves, because a store or compare uses the half and that counts as using the whole
HALVES = {"ecx": "rcx", "edx": "rdx", "r8d": "r8", "r9d": "r9",
          "cx": "rcx", "dx": "rdx", "r8w": "r8", "r9w": "r9",
          "cl": "rcx", "dl": "rdx", "r8b": "r8", "r9b": "r9"}


def used_arguments(address, size, limit=40):
    """Which argument registers the function reads as a SOURCE, ignoring the ones it only writes."""
    seen = set()
    count = 0
    for instruction in disasm(address):
        if instruction.address >= address + size or count >= limit:
            break
        count += 1
        text = instruction.op_str
        if "," in text:
            destination, source = text.split(",", 1)
        else:
            destination, source = "", text
        # a register appears as a SOURCE -> it is an input. A `mov rsi, rcx` proves rcx is an input.
        first = destination.strip().split(" ")[-1]
        for name in ARGUMENTS:
            for form, whole in list(HALVES.items()) + [(name, name)]:
                if whole != name and form not in source:
                    continue
                if re.search(r"\b%s\b" % re.escape(form), source) and first not in (name, form):
                    seen.add(whole)
    return seen


def main():
    api = io.open(API, encoding="utf-8", errors="replace").read()
    forwarding = io.open(FWD, encoding="utf-8", errors="replace").read()
    profile = load_prof()

    entries = [(int(m.group(1)), m.group(2)) for m in
               re.finditer(r"^\s*\{(\d+),\s*reinterpret_cast<void\*>\(&([\w:]+)\)\}", forwarding, re.M)]
    rows = re.findall(r'\{"([^"]+)",\s*(\d+),\s*(\d+),\s*0x([0-9A-Fa-f]+)u,\s*(\d+)u,', api)
    info = {int(row[1]): (row[0], int(row[3], 16), int(row[4])) for row in rows}
    wrappers = {}
    for match in re.finditer(r'extern "C"[^;{]*?\b(\w+)\s*\([^)]*\)\s*\{(.*?)\n\}', api, re.S):
        wrappers[match.group(1)] = " ".join(match.group(2).split())

    print("%-5s %-34s %-9s %-9s %s" % ("ord", "export", "regs", "dispatches", "argument registers the module READS"))
    for ordinal, symbol in sorted(entries):
        name, rva, size = info.get(ordinal, ("(no row)", 0, 0))
        body = wrappers.get(name, "")
        if "impl::" in body:
            continue
        used = sorted(used_arguments(rva, size), key=ARGUMENTS.index) if rva else []
        print("%-5d %-34s %-9d %-9s %s"
              % (ordinal, name[:34], len(used), "no", ", ".join(used) or "(none read)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
