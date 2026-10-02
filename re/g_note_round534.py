# -*- coding: utf-8 -*-
"""Append the round 534 correction: the launch order is 0x2C0 bytes, and its layout is read out of NewLaunchingOrder.

Round 533 concluded that the offsets +0x1C8 to +0x800 belong to one object because their user sets overlap, and said the
object was "at least a kilobyte". That was wrong in a way worth recording: the offsets do form a grid, but a grid is not an
object, and the extent tool could not tell one object's members from another's on the same numbers.

Round 534 found the answer in the constructor instead of in the statistics:

    NewLaunchingOrder (0x14620)   mov ecx, 0x2C0 ; call operator new
                                  then one store per field, +0x00 to +0x2B8

So the launch order is exactly 0x2C0 bytes, and the constructor writes every field, which makes its layout evidence rather
than inference. The offsets above 0x2C0 that the extent tool reported belong to OTHER objects that happen to use the same
low numbers, which is precisely the confusion the tool could not resolve and a constructor resolves at once.

That also explains 0x5007C0, the destructor in this objective's closure: it receives the order, dereferences it, and walks
+0x1D0, +0x1F8, +0x208, +0x228, +0x230, +0x240, +0x250, +0x258, +0x268, +0x270, +0x280, +0x2A8 and +0x2B8 -- all inside
0x2C0. And it explains why 0x22A20 allocates 0x1C8 while 0x5007C0 walks to 0x2B8: 0x22A20 is not building the launch
order at all. Its 0x1C8 bytes have a vtable-like pointer at +0, a double at +0x40, a flag at +0x48, the constant 9 at
+0x4C, an empty container at +0x50 and three strings, and it reads its mode from [order + 0x240]. It is a candidate object
that REFERS to the order, which is why the two layouts only look alike in the low offsets.
"""
import io
import os

PATH = r"D:\Nesting\nestfab\re\findings_structures_shared.md"

NOTE = """

## Correction (round 534): the launch order is 0x2C0 bytes, and NewLaunchingOrder says so

Round 533 showed the offsets `+0x1C8`, `+0x208`, `+0x240` and `+0x2A8` belong to one object by the overlap of their user
sets, and then overreached: it reported that the object extends past `+0x800` because the offsets keep coming on the same
eight byte grid. A grid is not an object. The extent tool cannot tell one type's members from another type's on the same
numbers, and this is the case that shows it.

The constructor settles it:

    NewLaunchingOrder (0x14620)
        lea rcx, [rip + 0x99925E] ; call 0x64AEA0      ; its own name to the logger
        mov ecx, 0x2C0           ; call 0x998500      ; operator new, 0x2C0 bytes
        movsd [rax + 0x00], xmm0  dword [rax + 0x08] = 0   dword [rax + 0x0C] = 0
        movsd [rax + 0x10], xmm0  dword [rax + 0x18] = 0   dword [rax + 0x1C] = 0
        byte  [rax + 0x20] = 0 ... byte [rax + 0x23] = 0
        movsd [rax + 0x28], xmm0  [rax + 0x30] [rax + 0x38]  byte [rax + 0x40] [rax + 0x41]
        dword [rax + 0x44] [rax + 0x48]  movsd [rax + 0x50]  dword [rax + 0x58]  byte [rax + 0x5C]
        movsd [rax + 0x60]  byte [rax + 0x68] = 1  dword [rax + 0x6C] = 1  movsd [rax + 0x70]
        movsd [rax + 0x78], xmm1  dword [rax + 0x80] = 0  ... to +0x2B8

So the launch order is **exactly 0x2C0 bytes** and the constructor writes every field, which makes the layout evidence
rather than inference. The offsets the extent tool found above `0x2C0` belong to other objects that happen to use the same
low numbers -- the confusion a constructor resolves and a frequency count cannot.

Three things this corrects or confirms:

* `0x5007C0`, the destructor in this objective's closure, receives the order, dereferences it, and walks `+0x1D0`, `+0x1F8`,
  `+0x208`, `+0x228`, `+0x230`, `+0x240`, `+0x250`, `+0x258`, `+0x268`, `+0x270`, `+0x280`, `+0x2A8` and `+0x2B8`. Every one
  is inside 0x2C0, so the destructor is consistent with the constructor and the type is confirmed from both ends.
* `0x22A20` is NOT building the launch order. It allocates 0x1C8, its own field map runs +0 to +0x1C0, and it READS its mode
  from `[order + 0x240]`. It builds a candidate object that refers to the order.
* `0x2AB0` receives the order in rcx, dereferences it into rbp, and reads `[rbp + 0x240]` -- the mode -- which is a member of
  the 0x2C0 launch order, not of the candidate.

### The lesson, which cost two rounds

A structure is found in its CONSTRUCTOR, not in the frequency of its offsets. The frequency tools are useful for finding
candidates and for checking that a claimed member set is plausible, but the moment a constructor is available it is the
authority: one function that writes every field in order gives the size, the field boundaries and the widths at once. The
order to work in is therefore to look for the constructor FIRST -- `NewLaunchingOrder` was already in the recovered name list
from the assertion channel before either round began.
"""


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "Correction (round 534)" in text:
        print("already appended")
        return 0
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text.rstrip("\n") + "\n" + NOTE)
    print("appended %d characters" % len(NOTE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
