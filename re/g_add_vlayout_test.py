# -*- coding: utf-8 -*-
"""Add the vtable-layout test."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- the vtable layout (measured at 0xA3CFD0)
    //
    // Three attempts to reason this out produced three answers, and the memory dump settled it: the address point is NULL at +0, the
    // typeinfo is at +8, and the FIRST SLOT'S ADDRESS is at +0x10 -- which is what a vtable pointer holds and what a constructor installs.
    {
        CHECK(lcns::kVtableAddressPointOffset == 0x10u);
        CHECK(lcns::kVtableAddressPoint == 0x00u);
        CHECK(lcns::kVtableTypeInfo == 0x08u);

        // the arithmetic the tool keys on
        CHECK(lcns::vtableSlotAddress(0xA3CFD0u, 0u) == 0xA3CFE0u);
        CHECK(lcns::vtableSlotAddress(0xA3CFD0u, 1u) == 0xA3CFE8u);
        CHECK(lcns::vtableSlotAddress(0xA3CFD0u, 2u) == 0xA3CFF0u);

        // the base and the addresses, as the dump gives them
        CHECK(lcns::kInfiniteEngineVtableRva == 0xA3CFD0u);
        CHECK(lcns::kInfiniteEngineSlot0Address == 0xA3CFE0u);
        CHECK(lcns::kInfiniteEngineSlot1Address == 0xA3CFE8u);
        CHECK(lcns::kInfiniteEngineSlot2Address == 0xA3CFF0u);

        // and the VALUES at those addresses, which are code to call rather than data
        CHECK(lcns::kInfiniteEngineSlot0Value == 0x759B20u);   // deleting dtor
        CHECK(lcns::kInfiniteEngineSlot1Value == 0x759AD0u);   // dtor
        CHECK(lcns::kInfiniteEngineSlot2Value == 0x759A80u);   // Run
        // THE DISTINCTION THE TWO BUGS COLLAPSED: an address and a value are different numbers in different spaces
        CHECK(lcns::kInfiniteEngineSlot0Address != lcns::kInfiniteEngineSlot0Value);

        // the constructor found by the address it installs, and the field it writes
        CHECK(lcns::kInfiniteEngineCtorCandidate == 0x24FD0u);
        CHECK(lcns::kInfiniteEngineObjectBytes == 0x30u);      // RE 0x24FDA: mov ecx, 0x30
        CHECK(lcns::kInfiniteEngineFieldAt8 == 0x08u);         // RE 0x24FFC

        // and the OTHER class's constructor, which calls a base and then installs its vtable
        CHECK(lcns::kNestingNesterCtor == 0x342E0u);
        CHECK(lcns::kNestingNesterBaseCtor == 0xB4470u);       // RE 0x342F5
        CHECK(lcns::kNestingNesterVtableField == 0x00u);       // RE 0x34308: mov [rbx], rax
        // the two constructors are different functions for different classes
        CHECK(lcns::kNestingNesterCtor != lcns::kInfiniteEngineCtorCandidate);
        CHECK(lcns::kNestingNesterBaseCtor != lcns::kNestingNesterCtor);
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "vtableSlotAddress" in text:
        print("already present")
        return 0
    if '#include "lcns/vtable_layout.hpp"' not in text:
        anchor = '#include "lcns/class_definitions.hpp"\n'
        assert anchor in text, "the class_definitions include is gone"
        text = text.replace(anchor, anchor + '#include "lcns/vtable_layout.hpp"\n', 1)
        print("include added")
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("vtable-layout test added; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
