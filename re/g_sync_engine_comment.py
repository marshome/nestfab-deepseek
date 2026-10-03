# -*- coding: utf-8 -*-
"""Sync the engine-base comment with the corrected evidence: TWO named registers, TEN offsets."""
import io
import sys

PATH = r"D:\Nesting\nestfab\lcns\include\lcns\engines.hpp"

OLD = """ * Nothing in the image references an engine vtable, so there is no constructor to read the members off -- **but FOUR engines read and write the SAME offsets through
 * their object register**, and four classes agreeing on eleven offsets is a base and not a coincidence:
 *
 *     EquivalentEngine::run   through rsi, reloaded from the `rcx` spill at [rsp + 0x210] by 0x75BDD8 and 0x75BE6A
 *     CompositeEngine::run    through rdi, reloaded from [rsp + 0x410] by 0x75ABD1 and 0x75AD1D
 *     MultiEngine::run        reaches +0x00 +0x08 +0x18 +0x20 +0x28 +0x30 +0x38 +0x40
 *     DelayedEngine::run      reaches +0x00 +0x08 +0x10 +0x18 +0x20 +0x28 +0x30 +0x38 +0x40 +0x48 +0x50
 *
 * **the union is one contiguous range, 0x00 to 0x50**, with the widths the stores give: a dword at +0x00 and +0x30 and pointers elsewhere. **What each field MEANS is
 * not established**, so they are named by offset -- **and they live HERE rather than on a derived class, because the evidence that they exist is that four derived
 * classes agree about them.** The initialisers are the values the bodies themselves write (0x756F1C, 0x756F27, 0x756F2F, 0x756F37, 0x756FCD, 0x756FD4, 0x756FDC).
 */"""

NEW = """ * Nothing in the image references an engine vtable, so there is no constructor to read the members off -- **but TWO engines' object registers read and write the SAME
 * ten offsets through registers that received `rcx`**:
 *
 *     DelayedEngine::run      through rdi (`756EEA mov rdi, rcx`)      +0x00 +0x10 +0x18 +0x20 +0x28 +0x30 +0x38 +0x40 +0x48 +0x50
 *     EquivalentEngine::run   through rsi (from the spill, `75BDD8`)   the same ten, and then +0x54 +0x58 +0x60
 *
 * **one contiguous range, 0x00 to 0x50**, with the widths the stores give: a dword at +0x00 and +0x30 and pointers elsewhere. **What each field MEANS is not
 * established**, so they are named by offset -- **and they live HERE rather than on a derived class, because the evidence that they exist is two derived classes agreeing
 * about them.** The initialisers are the values the bodies themselves write (0x756F1C, 0x756F27, 0x756F2F, 0x756F37, 0x756FCD, 0x756FD4, 0x756FDC).
 *
 * **AND WHAT IS *NOT* CLAIMED HERE MATTERS AS MUCH.** `+0x54`, `+0x58` and `+0x60` are `EquivalentEngine`'s alone in this measurement, **so they are not given to the
 * base**. **And an earlier version of this comment said FOUR engines agree on ELEVEN offsets, which was too strong**: `MultiEngine`'s extra offsets came from counting
 * EVERY register that ever received `rcx`, including `r15` after it took over from `r13`, so the count mixed registers. **Measured through the one register each prologue
 * establishes -- `r13` for `MultiEngine` and `r15` for `NestingEngine` -- each shows `+0x00` alone**, which is agreement and not contradiction, but it is much less than
 * was claimed. `re/g_engine_field_owners.py` is what does that one-register-at-a-time comparison, and `CompositeEngine` is left out of it because its prologue hands
 * `rcx` to several registers and then REUSES `rcx` as scratch, so a heuristic over "registers that ever received rcx" collects registers that received it and stopped
 * being it.
 */"""


def main(apply):
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "AND WHAT IS *NOT* CLAIMED HERE MATTERS AS MUCH" in text:
        print("already synced")
        return 0
    if OLD not in text:
        print("REFUSING: the anchor is not where it is expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    if apply:
        io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
        print("synced the comment")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
