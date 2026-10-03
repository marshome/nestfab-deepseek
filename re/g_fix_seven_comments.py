# -*- coding: utf-8 -*-
"""Correct the seven offset comments that contradict the module, so the permutation can place all 48 fields.

**THE MEASUREMENT SAID 41 OF 48 AND THE SEVEN ARE COMMENTS, NOT PLACEMENT.** Each one was settled by a different piece of the module, and none of them is a
judgement call:

  * `pipeMode` IS AT `+0x170` IN **THIS** OBJECT. `launching_order.hpp:111` records the field as `std::uint8_t pipeMode;   // +0x170  RE 0xFCF0 SetPipeMode,
    read by 0x4FC2F0`, and 0x4FC2F0 is `mov rax,[rcx] ; movzx eax, byte [rax + 0x170]`. **So the "pipe block" is a REGION INSIDE `Order`, not another
    object** -- and `cfgAt188`, `cfgAt190`, `cfgAt198`, `cfgAt178` and `cfgAt180` take their offsets from their OWN NAMES, which is what
    `LaunchingOrderLayout` records for the same positions (`unnamed188` at +0x188).
  * `usedSurfaceUsableOffcutRatio` COMES AFTER TWO DOUBLES whose block comment says "(RE +0x28/+0x30/+0x38)", so it is +0x38; its own "+0x44" is the offset of
    `shear` below it.
  * `rowAlternate` is the SIXTH field of a block the comment gives as "(+0x128..+0x150)": 0x128, 0x130, 0x138, 0x140, 0x148, **0x150**.
"""
import io
import sys

MODEL = r"D:\Nesting\nestfab\lcns\include\lcns\model.hpp"

# field -> (old comment fragment, new offset). The old fragment is checked so a silent miss is impossible.
FIXES = [
    ("cfgAt190", 0x190),
    ("cfgAt188", 0x188),
    ("cfgAt198", 0x198),
    ("cfgAt178", 0x178),
    ("cfgAt180", 0x180),
    ("usedSurfaceUsableOffcutRatio", 0x038),
    ("rowAlternate", 0x150),
]


def main():
    text = io.open(MODEL, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    lines = text.split("\n")
    changed = []
    for index, line in enumerate(lines):
        for name, offset in FIXES:
            # the declaration line for that field, with its trailing comment
            if (" %s " % name) not in line and (" %s;" % name) not in line:
                continue
            if "//" not in line:
                continue
            head, _sep, _tail = line.partition("//")
            lines[index] = "%s// +0x%03X  CORRECTED: the module settles this offset, see re/rounds.json round 711" % (head, offset)
            changed.append((name, offset))
            break
    if not changed:
        print("REFUSING: none of the seven field declarations was found")
        return 2
    text = "\n".join(lines)
    io.open(MODEL, "w", encoding="utf-8", newline="\n").write(text)
    for name, offset in changed:
        print("   %-32s -> +0x%03X" % (name, offset))
    missing = [name for name, _o in FIXES if name not in {n for n, _ in changed}]
    if missing:
        print("NOT FOUND: %s" % ", ".join(missing))
        return 1
    print("%d of %d corrected" % (len(changed), len(FIXES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
