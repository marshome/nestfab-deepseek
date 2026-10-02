# -*- coding: utf-8 -*-
"""The exports whose OWN bodies are small enough to read and write today, regardless of their closure.

Usage: python g_export_sizes.py [--top 20]

The self-check says forwardedCount has not moved in 26 commits, so this round is for the deliverable. The obstacle has been that
every unforwarded export's closure contains the same 75 functions, which made the whole set look blocked. But a closure is
REACHABILITY, not work: an export whose body is 40 bytes and which calls one small helper is finishable today even when some
distant branch of its closure is a 4479 byte global initialiser that only runs at load time.

So rank the unforwarded exports by their OWN body size and by how many of their callees are already verified, implemented or
classified. An export that is itself tiny, calls only known things, and has a trivial error path is next; the closure size is
reported beside it so the difference between "reachable" and "needed" stays visible.

`--walk ORDINAL` prints one export's body with its calls, so the smallest one can be read and written without the closure being
read first.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import g_leverage as L          # noqa: E402
import g_names as N             # noqa: E402
import g_toolchain as T         # noqa: E402
from lib import disasm, load_prof  # noqa: E402


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--walk", type=lambda v: int(v, 0), default=None)
    args = parser.parse_args(argv)
    profile = load_prof()
    table = json.loads(open(os.path.join(HERE, "exports_table.json"), encoding="utf-8").read())
    forwarded = L.forwarded_ordinals()

    rows = []
    for entry in table:
        ordinal = (entry.get("ords") or [0])[0]
        if ordinal in forwarded:
            continue
        root = entry["rva"]
        info = profile.get(root) or {}
        size = info.get("size") or 0
        callees = [c for c in (info.get("callees") or []) if c in profile]
        known = sum(1 for c in callees
                    if c in T.BOILERPLATE or c in getattr(T, "IMPLEMENTED", ()) or c in L.VERIFIED)
        # the closure, only to report it beside the body so reachability and work stay distinguishable
        seen = {root}
        queue = [root]
        while queue:
            a = queue.pop()
            for c in (profile.get(a) or {}).get("callees") or []:
                if c in profile and c not in seen:
                    seen.add(c)
                    queue.append(c)
        rows.append((size, len(callees) - known, len(callees), len(seen), ordinal, root))
    rows.sort()

    print("the unforwarded exports by their OWN body size:")
    print("")
    print("%-8s %-8s %-8s %-9s %-9s %s" % ("body", "unknown", "calls", "closure", "ordinal", "export"))
    for size, unknown, calls, closure, ordinal, root in rows[:args.top]:
        label = L.VERIFIED.get(root) or N.direct(root) or ""
        print("%-8d %-8d %-8d %-9d %-9d 0x%X %s" % (size, unknown, calls, closure, ordinal, root, label))
    print("")

    if args.walk is not None:
        for size, unknown, calls, closure, ordinal, root in rows:
            if ordinal != args.walk:
                continue
            info = profile.get(root) or {}
            body_size = info.get("size") or 0
            print("=== ordinal %d, export 0x%X, %d bytes, closure %d" % (ordinal, root, body_size, closure))
            for ins in disasm(root):
                if ins.address >= root + body_size:
                    break
                if ins.mnemonic == "call":
                    import re as _re
                    m = _re.search(r"0x([0-9a-f]+)", ins.op_str)
                    if m:
                        callee = int(m.group(1), 16)
                        label = N.direct(callee) or ""
                        mark = ("verified" if callee in L.VERIFIED else
                                "implemented" if callee in getattr(T, "IMPLEMENTED", ()) else
                                "library" if callee in T.BOILERPLATE else
                                "%d B" % ((profile.get(callee) or {}).get("size") or 0))
                        print("  0x%-8X call 0x%-8X  %-12s %s" % (ins.address, callee, mark, label))
                else:
                    print("  0x%-8X %-16s %s" % (ins.address, ins.mnemonic, ins.op_str))
            break
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
