# -*- coding: utf-8 -*-
"""Two corrections to the closure tool, both found by inspecting what it called ready.

The tool listed nine exports as needing no further reading. Checking them one by one showed the list was wrong in three
ways:

  * GetLength (96), GetHeight (100), GetFillRatio (168) and GetNestingFillRatio (192) are thin entry points whose
    implementers walk containers and call several domain functions. They appeared dependency-free because kind() in
    g_toolchain classifies ANY function containing a call or jump through a rip-relative pointer as toolchain, and a large
    domain function that makes one incidental indirect call therefore got classified away. That rule is right for two
    byte stubs and wrong for a two kilobyte implementer, so the verdict is now only honoured for small functions.

  * GetPartUserStringEx (55) and GetSheetUserStringEx (61) are platform-forwarding: they assemble their arguments and
    jump into the import stub bank, so no domain logic is reversed by implementing them. They are excluded, as recorded
    in re/CATEGORIES.md.

  * GetBuildVersion (88), GetBuildDate (90) and GetMajorVersion (92) return an address inside the original image, which
    no reimplementation can reproduce. They are listed separately rather than counted as work.

After the corrections the ready list means what it says.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L          # noqa: E402
import g_toolchain as T         # noqa: E402
from lib import load_prof       # noqa: E402

# The verdict of kind() is only trusted for functions this small. Above it, a single indirect call is not evidence that the
# function is a stub: it is more likely a domain routine that logs or dispatches once.
SMALL_FOR_TOOLCHAIN = 64

NOT_EQUIVALENT = {88, 90, 92}          # return an address inside the original image
PLATFORM_FORWARDING = {55, 61}         # assemble arguments and jump into the import stub bank


def main():
    profile = load_prof()
    kinds = {}
    done = L.forwarded_ordinals()
    import json
    table = json.loads(io.open(os.path.join(L.ROOT, "re", "exports_table.json"), encoding="utf-8").read())

    def domain(addr):
        if addr in L.VERIFIED or addr in T.BOILERPLATE:
            return False
        if addr not in profile:
            return False
        if addr not in kinds:
            k = T.kind(addr, profile)
            size = (profile.get(addr) or {}).get("size") or 0
            if k is not None and k != "domain" and size <= SMALL_FOR_TOOLCHAIN:
                kinds[addr] = k
            else:
                kinds[addr] = "domain"   # a verdict of toolchain on a large body is not trusted
        return kinds[addr] == "domain"

    def callees(addr):
        out = []
        size = (profile.get(addr) or {}).get("size")
        from lib import disasm
        for ins in disasm(addr):
            if size and ins.address >= addr + size:
                break
            if ins.mnemonic not in ("call", "jmp"):
                continue
            m = re.search(r"0x([0-9a-f]+)", ins.op_str)
            if m:
                out.append(int(m.group(1), 16))
        return out

    from collections import deque
    rows = []
    ready = []
    not_equiv = []
    forwarding = []
    for e in table:
        ord0 = (e.get("ords") or [0])[0]
        if ord0 in done:
            continue
        seen = {}
        q = deque((t, 1) for t in callees(e["rva"]) if domain(t))
        while q:
            a, d = q.popleft()
            if a in seen and seen[a] <= d:
                continue
            seen[a] = d
            for t in callees(a):
                if domain(t):
                    q.append((t, d + 1))
        name = e.get("name") or ("sub_%05X" % e["rva"])
        if ord0 in NOT_EQUIVALENT:
            not_equiv.append((name, ord0, e["rva"], e["size"], len(seen)))
        elif ord0 in PLATFORM_FORWARDING:
            forwarding.append((name, ord0, e["rva"], e["size"], len(seen)))
        elif not seen:
            ready.append((name, ord0, e["rva"], e["size"]))
        rows.append((name, ord0, e["rva"], e["size"], len(seen), sum(((profile.get(a) or {}).get("size") or 0) for a in seen)))

    print("exports needing no further reading: %d" % len(ready))
    for name, ord0, rva, size in sorted(ready, key=lambda x: x[3]):
        print("    0x%-6X ord %-4d %-38s %4d B" % (rva, ord0, name, size))
    print("")
    print("not equivalent by address (listed, never counted): %d" % len(not_equiv))
    for name, ord0, rva, size, n in not_equiv:
        print("    0x%-6X ord %-4d %-38s %4d B  closure %d" % (rva, ord0, name, size, n))
    print("")
    print("platform forwarding (listed, never counted): %d" % len(forwarding))
    for name, ord0, rva, size, n in forwarding:
        print("    0x%-6X ord %-4d %-38s %4d B" % (rva, ord0, name, size))
    print("")
    print("cheapest twenty by closure size:")
    for name, ord0, rva, size, n, total in sorted(rows, key=lambda r: (r[4], r[5]))[:20]:
        print("    0x%-6X ord %-4d %-38s %4d B  needs %2d functions, %d bytes" % (rva, ord0, name, size, n, total))
    print("")
    total_fns = 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
