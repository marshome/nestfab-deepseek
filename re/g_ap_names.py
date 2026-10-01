"""RTTI names for the address points around 0xA3BB30-0xA3BB40.

A vtable's typeinfo pointer sits at (address_point - 0x18), and the typeinfo's name pointer at
its +8. Resolve the class names so the strategy wrapper and the 208 byte core can be identified.
Note the data-section trap: pointers in the dump's data are absolute VAs (ImageBase 0x6B4C0000 +
RVA), while RIP-relative targets are bare RVAs.
"""
import struct
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402

IMAGE_BASE = 0x6B4C0000


def read_q(rva):
    off = rva2off(rva)
    if off is None:
        return None
    return struct.unpack("<Q", data[off:off + 8])[0]


def read_cstr(rva, n=120):
    off = rva2off(rva)
    if off is None:
        return None
    raw = data[off:off + n]
    end = raw.find(b"\x00")
    if end >= 0:
        raw = raw[:end]
    return raw.decode("latin-1")


print("=== typeinfo chain for the address points of interest ===")
for ap in (0xA3BB30, 0xA3BB40, 0xA3BB10, 0xA3BB70, 0xA3BB00, 0xA3B280, 0xA3B1F0, 0xA3B0C0):
    # vptr points at the address point; the vtable base is address_point - 0x10, and the
    # typeinfo pointer lives at vtable_base - 8 = address_point - 0x18
    ti_va = read_q(ap - 0x18)
    out = ["AP 0x%x" % ap]
    if ti_va:
        # pointers in data are absolute VAs
        ti_rva = ti_va - IMAGE_BASE if ti_va >= IMAGE_BASE else ti_va
        name_va = read_q(ti_rva + 8)
        if name_va:
            name_rva = name_va - IMAGE_BASE if name_va >= IMAGE_BASE else name_va
            out.append("typeinfo VA 0x%x -> name RVA 0x%x = %r" % (ti_va, name_rva,
                                                                   read_cstr(name_rva)))
        else:
            out.append("typeinfo VA 0x%x (no name ptr)" % ti_va)
    else:
        out.append("no typeinfo pointer")
    print("   " + "  ".join(out))

print()
print("=== first 8 vtable slots of each address point (as absolute VAs -> RVA) ===")
for ap in (0xA3BB30, 0xA3BB40):
    print("   AP 0x%x:" % ap)
    for k in range(8):
        va = read_q(ap + 8 * k)
        if va:
            print("      slot %d: VA 0x%-12x RVA 0x%x" % (k, va, va - IMAGE_BASE if va >= IMAGE_BASE else va))
