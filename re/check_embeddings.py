# -*- coding: utf-8 -*-
"""Verify every embedded block against libcns_dump_64.dll, byte for byte.

The point of embedding original code is that a gap in the reconstruction stays visible and honest. That only holds if
the embedded copy still IS the original, so this re-reads the DLL and fails on any difference: a byte, a length, or the
hash. It also checks that the generated C++ carries each block's hash, which ties the code in the project to the
registry rather than to a claim in a document.

Exit code 0 means every block matches. Anything else is a failure and prints what differs.
"""
import hashlib
import io
import json
import os
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *          # noqa: E402

ROOT = r"D:\Nesting\nestfab"
REGISTRY = os.path.join(ROOT, "re", "embedded_registry.json")
GEN_CPP = os.path.join(ROOT, "lcns", "src", "embedded", "gen_blobs.cpp")
GEN_S = os.path.join(ROOT, "lcns", "src", "embedded", "gen_orig.S")
GEN_TAB = os.path.join(ROOT, "lcns", "src", "embedded", "gen_table.cpp")


def main():
    if not os.path.exists(REGISTRY):
        print("FAIL: %s is missing -- run re/g_embed.py first" % REGISTRY)
        return 1
    registry = json.loads(io.open(REGISTRY, encoding="utf-8").read())
    cpp = io.open(GEN_CPP, encoding="utf-8").read()
    asm = io.open(GEN_S, encoding="utf-8").read() if os.path.exists(GEN_S) else ""
    tab = io.open(GEN_TAB, encoding="utf-8").read() if os.path.exists(GEN_TAB) else ""

    bad = 0
    callable_n = 0
    data_n = 0
    for e in registry:
        rva = e["rva"]
        size = e["size"]
        off = rva2off(rva)
        if off is None:
            print("FAIL 0x%x: the rva is outside the image" % rva)
            bad += 1
            continue
        actual = bytes(data[off:off + size])
        if len(actual) != size:
            print("FAIL 0x%x: only %d of %d bytes are inside the image" % (rva, len(actual), size))
            bad += 1
            continue
        digest = hashlib.sha256(actual).hexdigest()
        if digest != e["sha256"]:
            print("FAIL 0x%x: the DLL's bytes hash to %s, the registry says %s" % (rva, digest, e["sha256"]))
            bad += 1
            continue
        if e["sha256"] not in cpp:
            print("FAIL 0x%x: gen_blobs.cpp does not carry the hash %s" % (rva, e["sha256"]))
            bad += 1
        if e["status"] in ("callable", "callable_relocated"):
            callable_n += 1
            if e["symbol"] not in asm:
                print("FAIL 0x%x: %s is not defined in gen_orig.S" % (rva, e["symbol"]))
                bad += 1
            if e["symbol"] not in tab:
                print("FAIL 0x%x: %s is missing from the pointer table" % (rva, e["symbol"]))
                bad += 1
            # IN THIS BRANCH, not in an elif that can never run: a relocated copy must list what was rewritten, and the
            # generated assembly must carry a symbolic call for each of those sites.
            if e["status"] == "callable_relocated":
                relocs = e.get("relocations") or []
                if not relocs:
                    print("FAIL 0x%x: a relocated copy with no relocation list" % rva)
                    bad += 1
                if not e.get("reason"):
                    print("FAIL 0x%x: a relocated copy must record what was rewritten" % rva)
                    bad += 1
                for rel in relocs:
                    if rel.get("symbol") not in asm:
                        print("FAIL 0x%x: relocation to %s is not in gen_orig.S" % (rva, rel.get("symbol")))
                        bad += 1
            elif e.get("relocations"):
                print("FAIL 0x%x: a plain callable copy must not carry relocations" % rva)
                bad += 1
        elif e["status"] == "data":
            # Evidence carried as bytes: no symbol and no excuse, but the bytes and the hash are checked like any other.
            data_n += 1
            if e["symbol"]:
                print("FAIL 0x%x: a data block must not claim a symbol" % rva)
                bad += 1
        else:
            if not e["reason"]:
                print("FAIL 0x%x: comment-only without a reason" % rva)
                bad += 1

    total = sum(e["size"] for e in registry)
    print("embedded blocks: %d (%d callable, %d comment-only, %d data), %d bytes"
          % (len(registry), callable_n, len(registry) - callable_n - data_n, data_n, total))
    print("checked against libcns_dump_64.dll: %s" % ("all match" if bad == 0 else "%d MISMATCHES" % bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
