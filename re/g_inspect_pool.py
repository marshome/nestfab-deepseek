# -*- coding: utf-8 -*-
"""Inspect the typeinfo at 0xA18490 and the words at the table base 0xA3BCE0, without a shell quoting layer."""
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib  # noqa: E402

IMAGE = 0xB43000


def text_at(rva, limit=120):
    offset = lib.rva2off(rva) if 0 < rva < IMAGE else None
    if offset is None:
        return None
    return lib.pe.get_data(offset, limit).split(b"\x00", 1)[0].decode("utf-8", "replace")


def describe(word):
    if lib.IB <= word < lib.IB + IMAGE:
        rva = word - lib.IB
        return "a virtual address -> rva 0x%X   %r" % (rva, text_at(rva))
    if 0 < word < IMAGE:
        return "an rva 0x%X   %r" % (word, text_at(word))
    return "(not a pointer)"


def main():
    print("=== typeinfo at rva 0xA18490")
    for index in range(4):
        word = lib.u64(0xA18490 + index * 8)
        print("   +0x%02X = 0x%-14X %s" % (index * 8, word, describe(word)))

    print("")
    print("=== the words at the table base rva 0xA3BCE0")
    for index in range(10):
        word = lib.u64(0xA3BCE0 + index * 8)
        print("   +0x%02X = 0x%-14X %s" % (index * 8, word, describe(word)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
