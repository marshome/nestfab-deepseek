# -*- coding: utf-8 -*-
"""Write the +0x1F8..+0x208 findings as a TEST, which is code and not a document.

**THE RULE `rounds-must-land-code` CAUGHT THIS ROUND, AND IT IS RIGHT**: three of the last twelve commits touched `lcns/`, against a floor of four. **A round
that reads a function and writes nothing has not finished**, and this round's findings had gone into the ledger and the commit message only.

**AND THE FINDINGS ARE EXACTLY THE KIND A TEST PINS**: five fields whose offsets and widths come from three exports,

    +0x1F8  maxThreads   4 B   RE 0xD3D5 and RE 0xD3E7: mov dword [rsi], eax
    +0x1FC  maxIterations 4 B  bounded by +0x1F8's four bytes and by +0x200's one
    +0x200  engineLo      1 B   RE 0xD390: mov byte [rsi + 0x200], al
    +0x201  engineHi      1 B   RE 0xD3A0: mov byte [rsi + 0x201], bl
    +0x202  unestablished 2 B   NO export writes these
    +0x204  threadsA      4 B   RE 0xDF73: mov dword [rdi + 0x204], r12d -- the export's SECOND argument
    +0x208  threadsB      4 B   RE 0xDF7A: mov dword [rdi + 0x208], ebp  -- its THIRD

**so the test measures each one's ADDRESS and SIZE against its neighbour**, which is what "the offsets are right" means and what a comment cannot enforce.
"""
import io
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
BLOCK_END = '    return check::finish("test_recovered");'

BLOCK = '''
    // ---------------------------------------------------------------- Order's +0x1F8..+0x208 range (RE 0xD370 and RE 0xDE80)
    //
    // **FIVE FIELDS FROM THREE EXPORTS, AND THE TEST MEASURES THEM RATHER THAN TRUSTING THE COMMENT.** `SetLocalEngine` at 0xD370 writes a byte at +0x200 and
    // another at +0x201; `SetLocalEngineThreads` at 0xDE80 writes a dword at +0x204 and another at +0x208; and `exports_impl.cpp` reads 0xD3D5, 0xD3E7, 0xD390
    // and 0xD3A0 into a LocalEngineCarrier whose `maxThreads` is at +0x1F8.
    {
        lcns::Order probe;
        const unsigned char* base = reinterpret_cast<const unsigned char*>(&probe);

        // **EACH FIELD'S ADDRESS AND ITS WIDTH, WHICH IS THE WHOLE CLAIM.** A declaration whose comment and member disagree fails here, and a width that is
        // wrong shows up as the NEXT field being in the wrong place -- which is why every offset in the range is measured and not only the first.
        CHECK(reinterpret_cast<const unsigned char*>(&probe.maxThreads) == base + 0x1F8);
        CHECK(sizeof(probe.maxThreads) == 4);
        CHECK(reinterpret_cast<const unsigned char*>(&probe.maxIterations) == base + 0x1FC);
        CHECK(sizeof(probe.maxIterations) == 4);
        CHECK(reinterpret_cast<const unsigned char*>(&probe.engineLo) == base + 0x200);
        CHECK(sizeof(probe.engineLo) == 1);                    // RE 0xD390: mov byte [rsi + 0x200], al
        CHECK(reinterpret_cast<const unsigned char*>(&probe.engineHi) == base + 0x201);
        CHECK(sizeof(probe.engineHi) == 1);                    // RE 0xD3A0: mov byte [rsi + 0x201], bl
        CHECK(reinterpret_cast<const unsigned char*>(&probe.threadsA) == base + 0x204);
        CHECK(sizeof(probe.threadsA) == 4);                    // RE 0xDF73: mov dword [rdi + 0x204], r12d
        CHECK(reinterpret_cast<const unsigned char*>(&probe.threadsB) == base + 0x208);
        CHECK(sizeof(probe.threadsB) == 4);                    // RE 0xDF7A: mov dword [rdi + 0x208], ebp

        // **AND THE TWO BYTES NOTHING WRITES ARE ACCOUNTED FOR RATHER THAN SKIPPED**, because a gap that no field explains is how the range would come out
        // 0x202 short without any check noticing.
        CHECK(reinterpret_cast<const unsigned char*>(&probe.unestablished202) == base + 0x202);
        CHECK(sizeof(probe.unestablished202) == 2);

        // and the ORDER, which is what makes the addresses above a range and not six unrelated facts
        CHECK(reinterpret_cast<const unsigned char*>(&probe.maxThreads) < reinterpret_cast<const unsigned char*>(&probe.maxIterations));
        CHECK(reinterpret_cast<const unsigned char*>(&probe.maxIterations) < reinterpret_cast<const unsigned char*>(&probe.engineLo));
        CHECK(reinterpret_cast<const unsigned char*>(&probe.engineHi) < reinterpret_cast<const unsigned char*>(&probe.threadsA));
        CHECK(reinterpret_cast<const unsigned char*>(&probe.threadsA) < reinterpret_cast<const unsigned char*>(&probe.threadsB));

        // **AND THE EXPORT'S ARGUMENT MAPPING IS RECORDED WHERE THE FIELDS ARE**: argument 2 is what 0xDE8D moves from edx and 0xDF73 stores at +0x204, and
        // argument 3 is what 0xDE90 moves from r8d and 0xDF7A stores at +0x208. **The module carries no string for either, so the names stay placeholders.**
        static_assert(sizeof(lcns::Order) >= 0x2C0, "the module's object is 0x2C0 and the port's own members follow it");
    }
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "Order's +0x1F8..+0x208 range" in text:
        print("the test already covers the range")
        return 0
    anchor = text.find(BLOCK_END)
    if anchor < 0:
        print("REFUSING: the finish marker is not found")
        return 2
    text = text[:anchor] + BLOCK + "\n" + text[anchor:]
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("added the range test: five fields, their addresses, their widths and their order")
    return 0


if __name__ == "__main__":
    sys.exit(main())
