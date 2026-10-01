"""Read the doubles handed to the two AlphaPriceComputer instances and look for rodata strings
naming the three orphan Prc types."""
import struct
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


print("=== doubles passed to the two AlphaPriceComputer instances (0x4D68D3 / 0x4D68F5) ===")
for rva in (0x9D9C08, 0x9D9BE8, 0x9BCFC8, 0x9BCFD0, 0x9BCFA0, 0x9BCFB0, 0x9BCFC0, 0x9BCFD8,
            0x9B08B0, 0x9DE740, 0x9DE750, 0x9DE758):
    print("   0x%-8x = %-26r %s" % (rva, f64(rva), ("STR=%r" % STRS[rva][:50]) if rva in STRS else ""))

print()
print("=== rodata strings naming the three orphan types ===")
for rva, s in sorted(STRS.items()):
    if any(k in s for k in ("SurfaceCoeffs", "BoostAlpha", "DimAlpha", "SurfaceCoef", "BoostAlph")):
        print("   0x%-8x %r" % (rva, s[:70]))

print()
print("=== rodata strings in the pricer neighbourhood (0x9C1C00-0x9C1D20) ===")
for rva in sorted(STRS):
    if 0x9C1C00 <= rva <= 0x9C1D20:
        print("   0x%-8x %r" % (rva, STRS[rva][:80]))
