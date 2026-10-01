"""Resolve Coin::CoinLP's vtable slots, to identify the two methods BuildAndSolveLp calls.

BuildAndSolveLp does `mov rax,[coinlp]` then `call [rax+0x18]` and `call [rax+0x20]`.
The object's vptr points at the vtable address point (0xA3B280), so slot k sits at
0xA3B280 + 8*k. Print each slot's implementation, size, and first few instructions.
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()
ADDR_POINT = 0xA3B280


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


print("vtable header 0xA3B270, address point 0xA3B280")
for k in range(0, 13):
    slot_rva = ADDR_POINT + 8 * k
    off = rva2off(slot_rva)
    if off is None or off + 8 > len(data):
        print("  slot %-2d @0x%x : <unmapped>" % (k, slot_rva))
        continue
    fn = norm(u64(off))
    prof = PROF.get(fn) or {}
    print("  slot %-2d @0x%x (vptr+0x%02x) -> 0x%-8x %-22s size=%s nins=%s"
          % (k, slot_rva, 8 * k, fn, name_of(fn), prof.get("size"), prof.get("nins")))
    try:
        for i, ins in enumerate(disasm(fn, count=6)):
            print("        %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
            if i >= 5:
                break
    except Exception as exc:
        print("        <disasm failed: %s>" % exc)
