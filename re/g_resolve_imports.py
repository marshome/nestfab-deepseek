#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Resolve the module's IMPORT TABLE by hand, so a thunk through the IAT can be named.

**WHY BY HAND.** `lib.pe` parses the EXPORT directory and not the imports -- the dump came out of UPX, and pefile's `DIRECTORY_ENTRY_IMPORT` is absent. But the
import DESCRIPTOR table is a plain array in the data directory, 20 bytes per entry:

    struct ImportDescriptor {
        DWORD OriginalFirstThunk;   // RVA to the hint/name table
        DWORD TimeDateStamp;
        DWORD ForwarderChain;
        DWORD Name;                 // RVA to the DLL name string
        DWORD FirstThunk;           // RVA to the IAT
    };

terminated by an all-zero entry, and each thunk is either a 1 bit set with the ordinal in the low 16 bits or an RVA to a `WORD hint; char name[]`.

**THE POINT IS TWO LEDGER CLAIMS THAT SAY THE CALLEE COULD NOT BE RESOLVED** -- `thunk.63F228` and `thunk.63F228-resolved` -- both about a `jmp qword ptr
[rip + ...]` at 0x63F228 whose IAT slot is 0xB28F1C.

    python -u g_resolve_imports.py
    python -u g_resolve_imports.py --slot 0xB28F1C
"""
import argparse
import io
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib  # noqa: E402

IMAGE_BASE = 0x6B4C0000


def read_c_string(rva, limit=256):
    offset = lib.rva2off(rva)
    end = lib.data.index(b"\x00", offset)
    return lib.data[offset:min(end, offset + limit)].decode("ascii", "replace")


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", dest="slot", help="an IAT RVA to name, e.g. 0xB28F1C")
    args = parser.parse_args(argv)

    # the import directory is entry 1 of the data directory
    directories = lib.pe.OPTIONAL_HEADER.DATA_DIRECTORY
    entry = directories[1]
    if entry.VirtualAddress == 0:
        print("no import directory")
        return 2
    table = {}
    print("import descriptors at RVA 0x%X, size %d:" % (entry.VirtualAddress, entry.Size))
    index = 0
    while True:
        offset = lib.rva2off(entry.VirtualAddress + index * 20)
        original, _stamp, _forward, name_rva, first_thunk = struct.unpack_from("<IIIII", lib.data, offset)
        if original == 0 and name_rva == 0 and first_thunk == 0:
            break
        dll = read_c_string(name_rva) if name_rva else "?"
        print("   %-24s OriginalFirstThunk 0x%-8X FirstThunk 0x%X" % (dll, original, first_thunk))
        walk = original or first_thunk
        slot = first_thunk
        position = 0
        while True:
            thunk = struct.unpack_from("<Q", lib.data, lib.rva2off(walk + position * 8))[0]
            if thunk == 0:
                break
            if thunk & (1 << 63):
                table[slot + position * 8] = "%s.#%d" % (dll, thunk & 0xFFFF)
            else:
                table[slot + position * 8] = "%s!%s" % (dll, read_c_string(thunk + 2))
            position += 1
            if position > 4096:
                break
        index += 1
        if index > 256:
            break

    print("")
    print("resolved %d import slot(s)" % len(table))
    if args.slot:
        wanted = int(args.slot, 16)
        print("   slot 0x%X -> %s" % (wanted, table.get(wanted, "NOT AN IMPORT SLOT IN THIS TABLE")))
        return 0
    for slot in sorted(table)[:30]:
        print("   0x%-8X %s" % (slot, table[slot]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
