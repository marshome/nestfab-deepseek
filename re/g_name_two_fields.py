# -*- coding: utf-8 -*-
"""Make `Order` NAME the three offsets the carriers described, so the offset-named carriers can be replaced by it.

**THE MEASUREMENT, THREE INSTRUCTIONS AND THEIR FUNCTIONS:**

    SetSpecificSheetOrigin's neighbour 0xD310, 33 bytes   `mov dword [rsi + 0x18], ebx`  at 0xD327
    the next one                       0xD340, 33 bytes   `mov dword [rsi + 0x1c], ebx`  at 0xD357
    UnLockLaunchingOrder               0xD430, 36 bytes   `mov dword [rsi + 0x244], ebx` at 0xD447

**AND `Order` CALLS +0x18 AND +0x1C PADDING.** They fall inside `padding01[0x12]`, which runs +0x10..+0x21, **so the carriers were describing two real four-byte
fields that this project's own layout had written off as a gap.** `+0x244` is already named -- `unlockMode` -- and `IntFieldCarrier::field244` is a second name
for it.

**AND THE NAMES ARE POSITIONS, WHICH IS THE POINT.** The exports that write +0x18 and +0x1C are `SetSpecificSheetOrigin`'s neighbours at ordinals around 296-302,
and until those are read the fields have no oracle; **so they are named for the offset exactly as `IntFieldCarrier` named them, and the difference is that they
now live in the ONE structure that describes the module's object rather than in a second one beside it.**
"""
import io
import re
import sys

MODEL = r"D:\Nesting\nestfab\lcns\include\lcns\model.hpp"
LAYOUT = r"D:\Nesting\nestfab\lcns\include\lcns\dll_layout.hpp"

MODEL_OLD = "    std::byte padding01[0x12];   // +0x010..+0x021, no field here"
MODEL_NEW = ("    std::byte padding01a[0x8];   // +0x010..+0x017, no field here\n"
             "    /** +0x18, RE 0xD327: `mov dword [rsi + 0x18], ebx` in the 33-byte setter at 0xD310. **The module names no field here**, so this is the offset\n"
             "     *  as a name -- and it is the SAME name `IntFieldCarrier::field18` used, which is the point: the two structures became one. */\n"
             "    std::uint32_t field18 = 0;\n"
             "    /** +0x1C, RE 0xD357: `mov dword [rsi + 0x1c], ebx` in the 33-byte setter at 0xD340. The same, one field later. */\n"
             "    std::uint32_t field1C = 0;\n"
             "    std::byte padding01b[0x2];   // +0x020..+0x021, no field here")

LAYOUT_OLD = """    unsigned char opaque00[0x18];
    std::int32_t field18;      // RE 0x0D310
    std::int32_t field1C;      // RE 0x0D340
    unsigned char opaque20[0x24];
    std::int32_t field44;      // RE 0x0DDC0"""
LAYOUT_NEW = """    unsigned char opaque00[0x18];
    std::int32_t field18;      // +0x18, RE 0xD310: this carrier's name for Order::field18
    std::int32_t field1C;      // +0x1C, RE 0xD340: Order::field1C
    unsigned char opaque20[0x24];
    std::int32_t field44;      // +0x44, RE 0x0DDC0 -- **AND ORDER NAMES +0x44 `shear`**"""


def patch(path, old, new, label):
    text = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if new in text:
        print("   %-14s already patched" % label)
        return True
    if old not in text:
        print("   REFUSING: %-14s anchor not found" % label)
        return False
    io.open(path, "w", encoding="utf-8", newline="\n").write(text.replace(old, new, 1))
    print("   %-14s patched" % label)
    return True


def main():
    ok = patch(MODEL, MODEL_OLD, MODEL_NEW, "model.hpp")
    ok = patch(LAYOUT, LAYOUT_OLD, LAYOUT_NEW, "dll_layout.hpp") and ok
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
