# -*- coding: utf-8 -*-
"""Test ObserverSink, which is the interface BestObserver forwards to, and fix the BestObserver test block for the new shape."""
import io
import re
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

BLOCK = '''    // ---------------------------------------------------------------- BestObserver, which FORWARDS (RE 0x755A40)
    //
    // Three of its six slots are 11, 11 and 18 bytes and do nothing but read the object at +0x10 and jump into ITS vtable:
    //
    //     0x755A40  mov rcx, [rcx + 0x10] / mov rax, [rcx] / jmp [rax + 0x10]     ; slot 2
    //     0x755A50  mov rcx, [rcx + 0x10] / mov rax, [rcx] / jmp [rax + 0x18]     ; slot 3
    //     0x755A60  mov rcx, [rcx + 0x10] / movzx r8d, r8b / jmp [rax + 0x28]     ; slot 5
    //
    // **AND THE CLASS HAS NO OTHER EVIDENCE.** The declaration it replaced held a Solution, a double, a bool and an int, and no instruction
    // places any of them -- the two functions that could construct the object are the destructor pair and write only the vtable. A member
    // nothing places is not a member.
    {
        // the interface the forwarders reach, whose vtable at 0xA55FB0 has NULL in slots 0 and 1: a pure interface
        struct Sink : lcns::ObserverSink {
            int offers = 0;
            bool finished = false;
            void offer(const lcns::Solution&, double) override { ++offers; }
            bool hasSolution() const override { return offers > 0; }
            void notify(bool done, int) override { finished = done; }
        } sink;

        lcns::BestObserver observer;
        // with nothing to forward to, the calls are harmless -- which is what the module's forwarders would do only if the pointer were set,
        // and the class having no other state is exactly why that is the whole story
        observer.offer(lcns::Solution{}, 1.0);
        CHECK(observer.hasSolution() == false);

        // and through the interface the forwarders are FOR: a real sink receives both calls
        lcns::Solution solution;
        sink.offer(solution, 2.0);
        CHECK(sink.hasSolution());
        CHECK(sink.offers == 1);
        sink.notify(true, 3);
        CHECK(sink.finished);

        // ObserverSink is an interface: abstract, with the three methods the forwarders reach
        static_assert(std::is_abstract<lcns::ObserverSink>::value, "a pure interface");
        CHECK(sizeof(lcns::BestObserver) == sizeof(void*));      // RE 0x755A40: the class holds ONE pointer, at +0x10
    }
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    lines = text.split("\n")
    headers = [(i, l) for i, l in enumerate(lines) if re.match(r"^    // -{20,} ", l)]
    start = end = None
    for position, (index, line) in enumerate(headers):
        if "BestObserver" in line:
            start = index
            end = headers[position + 1][0] if position + 1 < len(headers) else len(lines)
            break
    if start is None:
        # no block: append before the finish marker
        anchor = '    return check::finish("test_recovered");'
        if anchor not in text:
            print("the finish marker is gone")
            return 1
        text = text.replace(anchor, BLOCK + "\n" + anchor, 1)
        io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
        print("added a BestObserver block; lines now %d" % text.count("\n"))
        return 0
    print("replacing lines %d..%d" % (start + 1, end))
    out = lines[:start] + BLOCK.split("\n") + lines[end:]
    io.open(TEST, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("lines now %d" % len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
