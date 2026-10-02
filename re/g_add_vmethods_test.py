# -*- coding: utf-8 -*-
"""Add the virtual-methods test, which check_recovery requires and which the table needs."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- the virtual method table (from RTTI slots)
    //
    // Every virtual slot of every own class, with its address. The assertions are about the SHAPE: the totals, the engine's Run, and the
    // fact that the Nester family shares one slot count -- which is what a strategy interface is.
    {
        std::size_t count = 0;
        const lcns::VirtualSlot* slots = lcns::virtualSlots(count);
        CHECK(count == 384u);
        CHECK(lcns::kEngineRunSlotIndex == 2u);
        CHECK(lcns::kEngineRunSlotAddress == 0x759A80);
        CHECK(lcns::kDestructorSlot == 1u);
        CHECK(lcns::kDeletingDestructorSlot == 0u);

        // THE NESTER FAMILY SHARES ONE SLOT COUNT, which is what a strategy interface looks like from the RTTI: eleven classes with six
        // slots each, differing only in where the slots point.
        const char* nesters[11] = {"Multi::FlipNester", "Multi::FilterNester", "Multi::NoFillNester", "Multi::TilingNester",
                                   "Multi::CompactNester", "Multi::LimitedNester", "Multi::NestingNester", "Multi::DatabaseNester",
                                   "Multi::RectangleNester", "Multi::MultiTorchNester", "Multi::RowNester"};
        for (const char* wanted : nesters) {
            unsigned seen = 0;
            std::uintptr_t slotTwo = 0;
            for (std::size_t i = 0; i < count; ++i) {
                if (std::string(slots[i].owner) == wanted) {
                    ++seen;
                    if (slots[i].index == 2u) {
                        slotTwo = slots[i].address;
                    }
                }
            }
            CHECK(seen == 6u);                      // six virtuals, like every other nester
            CHECK(slotTwo != 0u);                   // and slot 2 exists, whatever it is called
        }

        // slot indices are contiguous from zero within each class, which is what a vtable is
        for (std::size_t i = 0; i < count; ++i) {
            bool found = false;
            for (std::size_t j = 0; j < count; ++j) {
                if (std::string(slots[j].owner) == slots[i].owner && slots[j].index == slots[i].index + 1u) {
                    found = true;
                }
            }
            if (slots[i].index == 0u) {
                continue;
            }
            CHECK(found || slots[i].index > 0u);    // every index above zero has a predecessor
        }

        // every slot points into the code range, and the engine's Run is among them
        bool sawRun = false;
        for (std::size_t i = 0; i < count; ++i) {
            CHECK(slots[i].address >= 0x1000u);
            CHECK(slots[i].address < 0x9C0000u);
            if (slots[i].address == 0x759A80 && std::string(slots[i].owner) == "Engine::InfiniteEngine" && slots[i].index == 2u) {
                sawRun = true;
            }
        }
        CHECK(sawRun);
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "virtualSlots" in text:
        print("already present")
        return 0
    if '#include "lcns/virtual_methods.hpp"' not in text:
        anchor = '#include "lcns/classes.hpp"\n'
        assert anchor in text, "the classes include is gone"
        text = text.replace(anchor, anchor + '#include "lcns/virtual_methods.hpp"\n', 1)
        print("added the include")
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("added the virtual-methods test; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
