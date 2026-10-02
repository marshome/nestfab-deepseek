# -*- coding: utf-8 -*-
"""Give the model's part index an explicit setter, and record that the offset counting was too loose.

**A CORRECTION TO MY OWN READING, AND IT MATTERS FOR EVERY OFFSET COUNT IN THIS SESSION.** I reported that slot 3 at 0x7EB5E0 "reads [this + 0x10]"
by matching `\[(rcx|rdx|rbx|rdi|rsi) \+ 0x10\]` anywhere in the function -- and the matched instruction is

    0x7EB61C  lea rbx, [r12 + 8]      ; r12 = rdx = the SECOND ARGUMENT

so `+0x10` there belongs to an ARGUMENT and not to `this`. **AN OFFSET IS EVIDENCE ONLY IF THE BASE REGISTER IS THE OBJECT**, which is this
project's rule and which the loose scan violated. Slots 2 and 4 are sound -- they read `[this + 0x88]` and `[this + 0x80]` through rcx -- and
slot 3's offsets are not established by this reading.

AND THE FIX FOR THE MODEL: the part index the port uses is its own field, so it gets a setter rather than being smuggled through the
configuration bytes.
"""
import io
import sys

TILING = r"D:\Nesting\nestfab\lcns\include\lcns\tiling.hpp"
TEST = r"D:\Nesting\nestfab\lcns\tests\test_tiling.cpp"


def main():
    text = io.open(TILING, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    text = text.replace(
        "    void setSpacing(double spacing) { spacing_ = spacing; }",
        "    void setSpacing(double spacing) { spacing_ = spacing; }\n\n"
        "    /** **THE MODEL'S PART INDEX, NOT A MODULE FIELD.** The module's own part index is somewhere in the 0x70 bytes it copies; this is\n"
        "     *  what the port uses, so it is settable and named as the port's. */\n"
        "    void setPartIndex(int index) { partIndex_ = index; }", 1)
    io.open(TILING, "w", encoding="utf-8", newline="\n").write(text)
    print("added the model's setPartIndex")

    body = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "pat.setPartIndex(3)" not in body:
        body = body.replace("MultiOrientedPartPattern pat(config);",
                            "MultiOrientedPartPattern pat(config);\n        pat.setPartIndex(3);   // the MODEL's index; the module's is inside the 0x70 bytes it copies", 1)
        io.open(TEST, "w", encoding="utf-8", newline="\n").write(body)
        print("test_tiling.cpp: sets the model's part index explicitly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
