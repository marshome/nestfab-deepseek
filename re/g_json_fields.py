# -*- coding: utf-8 -*-
"""Field names from the serialisers: key -> the accessor it is handed -> the offset that accessor reads.

Usage: python g_json_fields.py [--window 12]

`..\\structure\\text_io.cpp` is where this module writes and reads its JSON, and two of its functions are the whole
vocabulary:

    0x50DB70  ToJson      4607 bytes, 992 instructions, 217 calls, 20 keys (valid, version, number_of_nested_parts,
                          nestings, sheet_id, multiplicity, common_cut_evaluation, multitorch_infos, number_of_groups,
                          fill_ratio, min_x, min_y, ...)
    0x5091B0  LoadSheet   2187 bytes, 99 calls, 21 keys (geometry, quantity, dimension_x, dimension_y, left_gap,
                          right_gap, bottom_gap, top_gap, defect_gap, used_surface_evaluation, ...)

and both of them work the same way: load the key string, call a small accessor that reads the member, and hand the result to
the JSON writer or read it back. So the name is recoverable in three steps and none of them is a guess:

    the key literal        'dimension_x'
    -> the accessor        the call that follows it, for example 0x5FD060
    -> the offset          0x5FD060 reads [rcx + 0x18] on its first argument

This does that for every key in a serialiser, and prints the pairs it can complete. The accessors are the ones that touch
exactly one offset, so the mapping is one key to one field, which is what a declaration needs.
"""
import io
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_names as N             # noqa: E402
from lib import disasm, load_prof, rva2off  # noqa: E402
import lib as LIB               # noqa: E402

IMAGE = LIB.data if isinstance(LIB.data, (bytes, bytearray)) else LIB.data()
KEY = re.compile(r"^[a-z][a-z0-9_]{2,40}$")
ACCESS = re.compile(r"\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]")
SERIALISERS = (0x50DB70, 0x50EE50, 0x5091B0, 0x509A40, 0x50A550, 0x50B1D0, 0x505280, 0x5052C0, 0x506B30, 0x506D80,
               0x506E90, 0x506130, 0x506350)


def string_at(rva, limit=64):
    try:
        off = rva2off(rva)
    except Exception:
        return None
    if off is None or off < 0 or off >= len(IMAGE):
        return None
    out = []
    for b in IMAGE[off:off + limit]:
        if b == 0:
            break
        if 32 <= b < 127:
            out.append(chr(b))
        else:
            return None
    return "".join(out)


def accessor_offsets(addr, profile):
    """The offsets a small function reads or writes on its first argument. None when it is not an accessor."""
    size = (profile.get(addr) or {}).get("size") or 0
    if size == 0 or size > 0x200:
        return None
    body = [i for i in disasm(addr) if i.address < addr + size]
    offsets = set()
    for ins in body:
        for m in ACCESS.finditer(ins.op_str):
            if m.group(1) in ("rcx", "rdx", "r8", "r9") and m.group(2):
                offsets.add(int(m.group(2), 16))
    return offsets if len(offsets) == 1 else None


def main(argv):
    window = int(argv[argv.index("--window") + 1]) if "--window" in argv else 12
    profile = load_prof()

    # the offsets of every small accessor, computed once
    one_offset = {}
    for addr, info in profile.items():
        got = accessor_offsets(addr, profile)
        if got:
            one_offset[addr] = next(iter(got))

    table = defaultdict(list)
    for addr in SERIALISERS:
        size = (profile.get(addr) or {}).get("size") or 0
        body = [i for i in disasm(addr) if i.address < addr + size]
        for index, ins in enumerate(body):
            m = re.search(r"\[rip \+ 0x([0-9a-f]+)\]", ins.op_str)
            if not m:
                continue
            nxt = body[index + 1].address if index + 1 < len(body) else ins.address + 8
            text = string_at(nxt + int(m.group(1), 16))
            if not text or not KEY.match(text):
                continue
            # the accessor is the first call after the key that reads exactly one offset
            for k in range(index + 1, min(index + 1 + window, len(body))):
                if body[k].mnemonic != "call":
                    continue
                mm = re.search(r"0x([0-9a-f]+)", body[k].op_str)
                if not mm:
                    continue
                target = int(mm.group(1), 16)
                if target in one_offset:
                    table[one_offset[target]].append((text, target, addr, nxt + int(m.group(1), 16)))
                    break

    print("%d offsets paired with a key from a serialiser" % len(table))
    print("")
    name = {a: (N.direct(a) or "0x%X" % a) for a in SERIALISERS}
    for offset in sorted(table):
        entries = table[offset]
        keys = sorted(set(e[0] for e in entries))
        where = sorted(set(name.get(e[2], "0x%X" % e[2]) for e in entries))
        print("+0x%-6X  %-34s  %s" % (offset, ", ".join(keys[:4]), ", ".join(where[:3])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
