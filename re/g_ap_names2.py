"""Robustly resolve the RTTI name for a vtable address point.

Itanium ABI: vtable = [offset-to-top][typeinfo][funcs...] and the address point (the value
stored in a vptr) is vtable + 0x10. So the typeinfo pointer is normally at AP - 8, but this dump
is a memory image and some tables are viewed through a different window, so try several offsets
and report whichever yields a plausible typeinfo -> name chain.
"""
import struct
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402

IMAGE_BASE = 0x6B4C0000


def read_q(rva):
    off = rva2off(rva)
    return struct.unpack("<Q", data[off:off + 8])[0] if off is not None else None


def read_cstr(rva, n=160):
    off = rva2off(rva)
    if off is None:
        return None
    raw = data[off:off + n]
    i = raw.find(b"\x00")
    if i >= 0:
        raw = raw[:i]
    try:
        t = raw.decode("latin-1")
    except Exception:
        return None
    return t if t and all(32 <= ord(c) < 127 for c in t) else None


def name_for(ap):
    for delta in (8, 0x18, 0x10, 0x20):
        va = read_q(ap - delta)
        if not va:
            continue
        ti = va - IMAGE_BASE if va >= IMAGE_BASE else va
        nm_va = read_q(ti + 8)
        if not nm_va:
            continue
        nm = nm_va - IMAGE_BASE if nm_va >= IMAGE_BASE else nm_va
        s = read_cstr(nm)
        if s and (s.startswith("N") or s.startswith("St") or "Multi" in s or "Prc" in s
                  or "Row" in s or "Pack" in s or "Tiling" in s):
            return "typeinfo RVA 0x%x  name RVA 0x%x  = %r" % (ti, nm, s)
    return "unresolved"


APS = [0xA3BB40, 0xA3BB30, 0xA3BB10, 0xA3BAF0, 0xA3BB00, 0xA3BB70, 0xA3B180, 0xA3B140,
       0xA3B100, 0xA3B0C0]
for ap in APS:
    print("AP 0x%-8x : %s" % (ap, name_for(ap)))
