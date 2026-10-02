# -*- coding: utf-8 -*-
"""Classify functions as library from the module's own labels, and name the domain ones.

Usage: python g_label_classify.py 51 [dry]

The module announces itself: functions hand literals to the logger, and the literals include the standard library's own
names -- basic_string::append, std::vector, __cxa_throw and the like. A function that says it is basic_string::append is
library code, and that judgement comes from the module's own words rather than from a guess about its shape.

The same pass prints the domain-looking labels of the remaining functions, which is how a nameless routine becomes a named
one without reading its body.
"""
import io
import json
import os
import re
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L          # noqa: E402
import g_toolchain as T         # noqa: E402
import lib as LIB               # noqa: E402
from lib import disasm, load_prof, rva2off  # noqa: E402

IMAGE = LIB.data if isinstance(LIB.data, (bytes, bytearray)) else LIB.data()
TOOLCHAIN = os.path.join(L.ROOT, "re", "g_toolchain.py")

LIBRARY_MARKERS = (
    "basic_string", "std::", "__cxa", "__gnu_cxx", "operator new", "operator delete", "allocator",
    "vector", "map<", "set<", "list<", "deque", "stringstream", "streambuf", "ios_base", "locale",
    "pthread", "mutex", "condition_variable", "chrono", "ratio", "codecvt", "num_put", "money_put",
    "terminate", "typeinfo", "dynamic_cast", "bad_alloc", "length_error", "out_of_range",
    "printf", "scanf", "malloc", "calloc", "realloc", "free(", "abort",
)


def printable(data):
    out = []
    for b in data:
        if b == 0:
            break
        if 32 <= b < 127:
            out.append(chr(b))
        else:
            break
    return "".join(out)


def string_at(rva):
    try:
        off = rva2off(rva)
    except Exception:
        return None
    if off is None or off < 0 or off >= len(IMAGE):
        return None
    text = printable(IMAGE[off:off + 120])
    return text if len(text) >= 3 else None


def labels_of(rva, size):
    out = []
    body = [i for i in disasm(rva) if not size or i.address < rva + size]
    for index, ins in enumerate(body):
        m = re.search(r"\[rip \+ 0x([0-9a-f]+)\]", ins.op_str)
        if not m:
            continue
        nxt = body[index + 1].address if index + 1 < len(body) else ins.address + 8
        text = string_at(nxt + int(m.group(1), 16))
        if text:
            out.append(text)
    return out


def main(argv):
    ordinal = int(argv[0])
    dry = len(argv) > 1 and argv[1] == "dry"
    profile = load_prof()
    kinds = {}

    def domain(addr):
        if addr in L.VERIFIED or addr in T.BOILERPLATE or addr in getattr(T, "IMPLEMENTED", ()):
            return False
        if addr not in profile:
            return False
        if addr not in kinds:
            k = T.kind(addr, profile)
            size = (profile.get(addr) or {}).get("size") or 0
            kinds[addr] = k if (k is not None and k != "domain" and size <= 64) else "domain"
        return kinds[addr] == "domain"

    def callees(addr):
        out = []
        size = (profile.get(addr) or {}).get("size")
        for i in disasm(addr):
            if size and i.address >= addr + size:
                break
            if i.mnemonic in ("call", "jmp"):
                m = re.search(r"0x([0-9a-f]+)", i.op_str)
                if m:
                    out.append(int(m.group(1), 16))
        return out

    table = json.loads(io.open(os.path.join(L.ROOT, "re", "exports_table.json"), encoding="utf-8").read())
    rva = None
    for e in table:
        if (e.get("ords") or [0])[0] == ordinal:
            rva = e["rva"]
            break
    assert rva is not None

    seen = {}
    q = deque((t, 1) for t in callees(rva) if domain(t))
    while q:
        a, d = q.popleft()
        if a in seen and seen[a] <= d:
            continue
        seen[a] = d
        for t in callees(a):
            if domain(t):
                q.append((t, d + 1))

    library = {}
    named = {}
    for a in sorted(seen):
        size = (profile.get(a) or {}).get("size")
        texts = labels_of(a, size)
        for text in texts:
            low = text.lower()
            if any(marker in text or marker in low for marker in LIBRARY_MARKERS):
                library[a] = text
                break
        if a not in library and texts:
            best = [t for t in texts if len(t) >= 4 and not t.startswith("//")]
            if best:
                named[a] = best[0]

    print("closure %d functions" % len(seen))
    print("  classified as library by their own labels: %d" % len(library))
    print("  carrying a domain looking label: %d" % len(named))
    print("")
    print("the library ones, first twenty:")
    for a, text in sorted(library.items(), key=lambda kv: (profile.get(kv[0]) or {}).get("size") or 0)[:20]:
        print("    0x%-8X %6s B  %r" % (a, (profile.get(a) or {}).get("size"), text))
    print("")
    print("domain labels, first thirty, which are names:")
    for a, text in sorted(named.items(), key=lambda kv: (profile.get(kv[0]) or {}).get("size") or 0)[:30]:
        print("    0x%-8X %6s B  %r" % (a, (profile.get(a) or {}).get("size"), text))

    if not dry and library:
        s = io.open(TOOLCHAIN, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        anchor = "    0xD59A0,  # xor eax, eax ; ret -- a default override returning zero"
        if anchor not in s:
            anchor = "    0x5C5270,  # mov rax, rcx ; ret -- returns its own argument"
        lines = [anchor]
        for a, text in sorted(library.items()):
            lines.append("    0x%X,  # library by its own label: %r" % (a, text[:60]))
        io.open(TOOLCHAIN, "w", encoding="utf-8", newline="\n").write(s.replace(anchor, "\n".join(lines), 1))
        print("")
        print("g_toolchain.py  %d functions classified as library" % len(library))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
