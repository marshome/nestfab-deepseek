# -*- coding: utf-8 -*-
"""Remove the three generated-table test blocks BY BALANCED BRACES, which the previous attempt got wrong.

THE PREVIOUS ATTEMPT DELETED THE END OF THE FILE, and the reason is mechanical: it bounded each block by the NEXT comment header, so a block
whose following header was itself inside another replaced span took the tail with it. **A block boundary must be measured, not inferred from
the next heading** -- so this finds the block's opening brace and walks to its matching close.
"""
import io
import re
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TARGETS = ("every class the RTTI names", "the class registers, AS CLASS CONSTANTS", "every class's constructor",
           "the virtual method table", "the module's own classes (from its RTTI)")

REPLACEMENT = '''    // ---------------------------------------------------------------- the generated class tables, DELETED
    //
    // Blocks of assertions over generated tables stood here: the RTTI class list, the virtual slot list and the constructor table. **All
    // three are deleted, and so are the files they asserted against.** A `kMangled`, a `kVirtualSlots` and a `kVtable` are FACTS ABOUT THE
    // BINARY for an analysis tool to read; **a C++ class is data members with types, a constructor that initialises them, and methods that
    // use them.** Putting those constants inside a class is what the human objected to, four times.
    //
    // The facts are not lost: re/vtables.json holds every mangled name, slot count and vtable address, and the ledger cites the instructions
    // that establish them. What remains is the class work that was written BY HAND from constructors that were read.

'''


def block_span(lines, header_index):
    """(start, end) for the header at header_index: the comment lines, then the brace block that follows."""
    index = header_index
    # skip the comment lines of the block
    while index < len(lines) and (lines[index].strip().startswith("//") or not lines[index].strip()):
        index += 1
    if index >= len(lines) or lines[index].strip() != "{":
        return None
    depth = 0
    start = header_index
    while index < len(lines):
        depth += lines[index].count("{") - lines[index].count("}")
        if depth == 0:
            return (start, index + 1)
        index += 1
    return None


def main():
    lines = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n").split("\n")
    spans = []
    for index, line in enumerate(lines):
        if not re.match(r"^    // -{20,} ", line):
            continue
        if not any(target in line for target in TARGETS):
            continue
        span = block_span(lines, index)
        if span:
            spans.append(span)
            print("block at lines %d..%d: %s" % (span[0] + 1, span[1], line.strip()[:66]))
    if not spans:
        print("no target blocks found")
        return 2
    # merge overlapping spans, then replace from the last to the first
    spans.sort()
    merged = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    for start, end in sorted(merged, reverse=True):
        lines = lines[:start] + REPLACEMENT.split("\n") + lines[end:]
    text = "\n".join(lines)
    for include in ('#include "lcns/class_definitions.hpp"\n', '#include "lcns/classes.hpp"\n',
                    '#include "lcns/virtual_methods.hpp"\n'):
        text = text.replace(include, "")
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("")
    print("replaced %d span(s); lines now %d, brace balance %d"
          % (len(merged), text.count("\n") + 1, text.count("{") - text.count("}")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
