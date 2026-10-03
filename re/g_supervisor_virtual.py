# -*- coding: utf-8 -*-
"""Make `Supervisor` polymorphic, which its vtable says it is, and pin the two facts that follow.

**THE EVIDENCE:** `re/vtables.json` records `Multi::Supervisor` at base 0xA3B4D0 with two slots, 0x30B60 and 0x30EB0, both destructor pair; the class's own vtable
pointer **0xA3B4E0 = 0xA3B4D0 + 0x10** is what `lea rax, [rip + 0xa0a96f]` at 0x030B6A computes (`0x30B71 + 0xA0A96F`). **A class with a vptr whose
destructor is in the table has a virtual destructor, and the tree declares none.**

**AND THE ONE THING THAT MUST NOT CHANGE IS THE FIELD AT +8.** `mov rsi, qword [rcx + 8]` at 0x030B71 reads the state pointer, so adding a vptr must NOT move
it: with `virtual ~Supervisor()` the vptr takes +0x00 and `state_` stays at +0x08, **which is exactly the offset the destructor uses.** That is asserted below,
because it is the assertion that would catch the wrong fix.
"""
import io
import sys

HEADER = r"D:\Nesting\nestfab\lcns\include\lcns\engine.hpp"

OLD = """class Supervisor {
public:
    Supervisor(const Order& order, SolveContext& ctx, EngineParams params);"""

NEW = """class Supervisor {
public:
    /** **RE 0xA3B4D0, TWO SLOTS: 0x30B60 and 0x30EB0, both the destructor pair.** So the class HAS a vptr and its destructor IS virtual, and the construct is
     *  `lea rax, [rip + 0xa0a96f]` at 0x030B6A, whose target is 0x30B71 + 0xA0A96F = **0xA3B4E0 = 0xA3B4D0 + 0x10** -- the pointer a constructor installs.
     *
     *  **AND THE VPTR DOES NOT MOVE `state_`.** 0x030B71 reads `mov rsi, qword [rcx + 8]`, so the state pointer is at +0x08 in a class that already has a vptr
     *  at +0x00, and declaring this destructor virtual is what makes that arrangement expressible rather than accidental. */
    virtual ~Supervisor() = default;

    Supervisor(const Order& order, SolveContext& ctx, EngineParams params);"""


def main():
    text = io.open(HEADER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "virtual ~Supervisor() = default;" in text:
        print("the class is already polymorphic")
        return 0
    if OLD not in text:
        print("REFUSING: the Supervisor declaration is not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(HEADER, "w", encoding="utf-8", newline="\n").write(text)
    print("engine.hpp: Supervisor has a virtual destructor, from its two slot vtable at 0xA3B4D0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
