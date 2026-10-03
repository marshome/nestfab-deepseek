# -*- coding: utf-8 -*-
"""For each unreversed export, the LARGEST function on its delegation chain -- the real work, not the entry point's size.

**THE SIZE-RANKED QUEUE WAS MISLEADING AND HERE IS WHY, THREE TIMES OVER:**

    GetLength              0xB130, 36 bytes   -> 0x526160, 757 bytes
    GetHeight              0xB160, 36 bytes   -> 0x5266a0, 759 bytes
    GetNestingFillRatio    0xB4E0, 38 bytes   -> 0x5257D0, and 0x5257D0 is not small either
    GetFillRatio           0xB4B0, 34 bytes   -> 0x5297C0, **881 bytes**

**SO THE ENTRY POINT'S SIZE SAYS NOTHING ABOUT THE WORK.** What matters is the biggest function the entry point reaches, because that is what has to be understood.

**AND A TAIL CALL TO A THUNK IS NOT A DELEGATION AT ALL.** `GetPartUserStringEx` ends `jmp 0x63f228` and 0x63f228 is `jmp qword ptr [rip + ...]` with `nop` padding --
**an unresolved IMPORT**, so that chain ends outside the module and cannot be reversed from this dump. The `jmp [rip+...]` shape is the test.
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

from lib import disasm, load_prof  # noqa: E402

API = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")


def is_thunk(address, profile):
    """A `jmp qword ptr [rip + ...]` with no prologue is an import thunk and not a function."""
    instructions = list(disasm(address, count=1))
    if not instructions:
        return False
    first = instructions[0]
    return first.mnemonic == "jmp" and first.op_str.startswith("qword ptr [rip")


def chain(address, size, profile, depth=0, seen=None):
    """The entry point's own size plus every function it delegates to."""
    seen = seen or set()
    if address in seen or depth > 3:
        return [(address, size)]
    seen.add(address)
    out = [(address, size)]
    n = 0
    for instruction in disasm(address):
        if instruction.address >= address + size or n > 60:
            break
        n += 1
        if instruction.mnemonic in ("jmp", "call"):
            target = instruction.op_str.strip()
            if not target.startswith("0x"):
                continue
            try:
                target_address = int(target, 16)
            except ValueError:
                continue
            entry = profile.get(target_address)
            if entry is None:
                continue
            if is_thunk(target_address, profile):
                out.append((target_address, 0))       # an import; the chain leaves the module
                continue
            out.extend(chain(target_address, entry.get("size") or 0, profile, depth + 1, seen))
    return out


def main():
    api = io.open(API, encoding="utf-8", errors="replace").read()
    profile = load_prof()
    rows = re.findall(r'^\s*\{"([^"]+)",\s*(\d+),\s*\d+,\s*0x([0-9A-Fa-f]+)u,\s*(\d+)u,\s*Status::(\w+)', api, re.M)

    print("%-40s %-7s %-7s %s" % ("export", "entry", "biggest", "what the chain reaches"))
    print("")
    easy, hard, imported = [], [], []
    for name, _ordinal, rva_text, size_text, status in rows:
        if status == "Forwarded":
            continue
        rva, size = int(rva_text, 16), int(size_text)
        links = chain(rva, size, profile)
        biggest = max((s for _a, s in links), default=0)
        thunked = any(s == 0 for _a, s in links)
        label = "** an IMPORT: the chain leaves the module **" if thunked and biggest <= size else ""
        if thunked and biggest <= size:
            imported.append(name)
        elif biggest <= 64:
            easy.append((name, rva, size, biggest))
        else:
            hard.append((name, size, biggest))
        if size <= 64 or thunked:
            print("%-40s %-7d %-7d %s" % (name[:40], size, biggest, label))
    print("")
    print("**REALLY EASY (nothing on the chain over 64 bytes): %d**" % len(easy))
    for name, rva, size, biggest in easy:
        print("   0x%05X %-40s entry %d, biggest %d" % (rva, name[:40], size, biggest))
    print("")
    print("ENDS AT AN IMPORT: %d -- %s" % (len(imported), ", ".join(imported[:8])))
    print("DELEGATES TO SOMETHING BIGGER: %d" % len(hard))
    return 0


if __name__ == "__main__":
    sys.exit(main())
