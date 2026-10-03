# -*- coding: utf-8 -*-
"""Wire every forwarded ordinal whose wrapper still reports its ordinal, one at a time and verifiably.

**THE SHAPE IS THE SAME FOR ALL OF THEM, WHICH IS WHY IT CAN BE DONE IN ONE PASS RATHER THAN THIRTY-EIGHT.** From the module's own first instructions:

  * **argument 1 is ALWAYS a pointer.** `rcx` is read as a source in every one of the 38, and in the two just wired it was `mov rsi, rcx` followed by a store or a
    load THROUGH it. So the wrapper takes `Order*` (or `Solution*`, whichever the inferred table named) and passes `static_cast<void*>`.
  * **argument 2, where the module reads `rdx`, is an int.**
  * **the implementation already has the right signature** -- `void*` plus `int`, returning what the module leaves in `rax` -- because that is how the earlier
    rounds wrote them.

**AND THE REPLACEMENT IS A TEXTUAL ONE ONLY BECAUSE IT WAS MEASURED FIRST.** `re/g_forwarding_signatures.py` reads each function's argument registers, so the
arity in every rewrite is the module's and not the table's. **The table's inferred signature is exactly what was wrong for ordinals 25 and 84.**
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
HALVES = {"ecx": "rcx", "edx": "rdx", "r8d": "r8", "r9d": "r9",
          "cx": "rcx", "dx": "rdx", "r8w": "r8", "r9w": "r9",
          "cl": "rcx", "dl": "rdx", "r8b": "r8", "r9b": "r9"}


def used_arguments(address, size, limit=40):
    seen = set()
    count = 0
    for instruction in disasm(address):
        if instruction.address >= address + size or count >= limit:
            break
        count += 1
        text = instruction.op_str
        destination, _sep, source = text.partition(",")
        first = destination.strip().split(" ")[-1]
        for whole in ARGUMENTS:
            for form in [whole] + [half for half, parent in HALVES.items() if parent == whole]:
                if re.search(r"\b%s\b" % re.escape(form), source) and first != form:
                    seen.add(whole)
    return seen


def main():
    api = io.open(API, encoding="utf-8", errors="replace").read()
    forwarding = io.open(FWD, encoding="utf-8", errors="replace").read()
    profile = load_prof()

    # the implementation's parameter count, from its declaration
    header = io.open(os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp"), encoding="utf-8",
                     errors="replace").read()

    entries = [(int(m.group(1)), m.group(2)) for m in
               re.finditer(r"^\s*\{(\d+),\s*reinterpret_cast<void\*>\(&([\w:]+)\)\}", forwarding, re.M)]
    rows = re.findall(r'\{"([^"]+)",\s*(\d+),\s*(\d+),\s*0x([0-9A-Fa-f]+)u,\s*(\d+)u,', api)
    info = {int(row[1]): (row[0], int(row[3], 16), int(row[4])) for row in rows}

    planned, refused = [], []
    for ordinal, symbol in sorted(entries):
        name, rva, size = info.get(ordinal, (None, 0, 0))
        if name is None or not rva:
            refused.append((ordinal, symbol, "no row or no rva"))
            continue
        wrapper = re.search(r'extern "C"[^;{]*?\b%s\s*\(([^)]*)\)\s*\{(.*?)\n\}' % re.escape(name), api, re.S)
        if not wrapper:
            refused.append((ordinal, name, "no wrapper found"))
            continue
        if "impl::" in wrapper.group(2):
            continue
        short = symbol.split("::")[-1]
        declaration = re.search(r"\b%s\s*\(([^;]*)\)\s*;" % re.escape(short), header)
        if not declaration:
            refused.append((ordinal, name, "no declaration for %s" % short))
            continue
        module_args = sorted(used_arguments(rva, size), key=ARGUMENTS.index)
        impl_args = [part for part in declaration.group(1).split(",") if part.strip()]
        if len(impl_args) != len(module_args):
            refused.append((ordinal, name, "the module reads %d argument(s) and %s takes %d"
                            % (len(module_args), short, len(impl_args))))
            continue
        planned.append((ordinal, name, short, len(module_args), declaration.group(1).strip()))

    print("wrappable now:  %d" % len(planned))
    print("refused:        %d" % len(refused))
    for ordinal, name, why in refused:
        print("   ord %-5s %-32s %s" % (ordinal, str(name)[:32], why))
    print("")
    for ordinal, name, short, count, signature in planned:
        print("   ord %-5d %-32s %s(%s)" % (ordinal, name[:32], short, signature))
    return 0


if __name__ == "__main__":
    sys.exit(main())
