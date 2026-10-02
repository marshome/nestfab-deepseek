# -*- coding: utf-8 -*-
"""Complete the test's Sink for the six-slot interface, and correct the stale comment above it.

`Structure::Observer` gained a fourth pure virtual -- slot 4, which `BestObserver` does not forward -- so the test's concrete class must implement it.
**AND THE COMMENT ABOVE THE STRUCT IS NOW WRONG TWICE**: it says the vtable is at 0xA55FB0, and it says slots 0 and 1 are NULL. The measured table is
`Structure::Observer`'s own, derived from the three classes that implement it.
"""
import io
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

OLD = """        // the interface the forwarders reach, whose vtable at 0xA55FB0 has NULL in slots 0 and 1: a pure interface
        struct Sink : lcns::Structure_Observer {
            int offers = 0;
            bool finished = false;
            void offer(const lcns::Solution&, double) override { ++offers; }
            bool hasSolution() const override { return offers > 0; }
            void notify(bool done, int) override { finished = done; }
        } sink;"""

NEW = """        // **THE INTERFACE THE FORWARDERS REACH IS `Structure::Observer`**, whose chain is
        // `N6Engine12BestObserverE -> N9Structure8ObserverE` and whose three deriving classes each have SIX slots. Two of those slots are the base's
        // own placeholders -- `0x7C2460` and `0x7C2470` are `xor eax, eax; ret`, which is what a compiler emits for a pure virtual.
        struct Sink : lcns::Structure_Observer {
            int offers = 0;
            bool finished = false;
            int slot4Calls = 0;
            void offer(const lcns::Solution&, double) override { ++offers; }   // slot 2, RE 0x755A47: jmp [rax + 0x10]
            bool hasSolution() const override { return offers > 0; }           // slot 3, RE 0x755A57: jmp [rax + 0x18]
            void slot4() override { ++slot4Calls; }                            // slot 4, NOT forwarded by BestObserver
            void notify(bool done, int) override { finished = done; }          // slot 5, RE 0x755A6F: jmp [rax + 0x28]
        } sink;"""


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD not in text:
        print("REFUSING: the Sink struct is not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("completed the test's Sink for six slots and corrected the comment above it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
