# -*- coding: utf-8 -*-
"""Give the two call sites the constructor's real arity: (int, double, double).

WHAT THE SECOND AND THIRD ARGUMENTS ARE IS ESTABLISHED, and this is what the call site at 0x766DBA through 0x766DCA shows: they are three
CONSECUTIVE fields of an option object, read at +0, +0x18 and +8 into the constructor's int and two doubles. **This project's Order already
carries the multitorch configuration**, so the values come from there; if the specific fields turn out to be different, the arity is still right
and the choice of fields is the part to revisit.
"""
import io
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_tiling.cpp"
SRC = r"D:\Nesting\nestfab\lcns\src\nester.cpp"


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "MultitorchEvaluator torch(4, " not in text:
        text = text.replace("MultitorchEvaluator torch(4);",
                            "// RE 0x4E8410: the constructor takes an int and TWO DOUBLES, all three written into the object it allocates\n"
                            "        MultitorchEvaluator torch(4, 1.0, 1.0);", 1)
        io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
        print("test_tiling.cpp: the constructor now takes three arguments")

    body = io.open(SRC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    old = "tiler.add(std::make_shared<tiling::MultitorchEvaluator>(order.multitorchNbTorches));"
    if old in body:
        body = body.replace(old,
                            "// RE 0x4E8410 takes (int, double, double); the call site at 0x766DBA reads all three out of one option object\n"
                            "    tiler.add(std::make_shared<tiling::MultitorchEvaluator>(order.multitorchNbTorches, order.multitorchCostRatio,\n"
                            "                                                            order.multitorchReconfig));", 1)
        io.open(SRC, "w", encoding="utf-8", newline="\n").write(body)
        print("nester.cpp: the construction now passes three arguments")
    return 0


if __name__ == "__main__":
    sys.exit(main())
