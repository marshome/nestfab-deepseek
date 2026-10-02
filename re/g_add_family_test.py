# -*- coding: utf-8 -*-
"""Add the Engine family test."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- the Engine family (seven classes from RTTI)
    //
    // Each with its vtable and its three slots, of which slot 2 is Run. The seven Run addresses are the ones the archive verified and the
    // base class's comment listed; the slot addresses come from the RTTI.
    {
        std::size_t count = 0;
        const lcns::EngineClass* family = lcns::engineFamily(count);
        CHECK(count == lcns::kEngineFamilyCount);
        CHECK(count == 7u);

        // the seven Run addresses, which is what the base class's comment listed and what the archive verified
        struct Expected { const char* name; std::uintptr_t run; std::uintptr_t vtable; };
        const Expected expected[7] = {
            {"MultiEngine",      0x755050u, 0xA3CF00u},
            {"DelayedEngine",    0x756EC0u, 0xA3CF70u},
            {"NestingEngine",    0x757250u, 0xA3CFA0u},
            {"InfiniteEngine",   0x759A80u, 0xA3CFD0u},
            {"CompositeEngine",  0x759B70u, 0xA3D000u},
            {"EquivalentEngine", 0x75BCC0u, 0xA3D030u},
            {"CloudEngine",      0x26A60u,  0xA3CED0u},
        };
        for (const Expected& want : expected) {
            bool found = false;
            for (std::size_t i = 0; i < count; ++i) {
                if (std::string(family[i].name) == want.name) {
                    CHECK(family[i].run == want.run);
                    CHECK(family[i].vtable == want.vtable);
                    found = true;
                }
            }
            CHECK(found);
        }

        // the per-class slot constants agree with the table, which is the check that the two were generated from one source
        CHECK(lcns::kMultiEngineRun == 0x755050u);
        CHECK(lcns::kNestingEngineRun == 0x757250u);
        CHECK(lcns::kInfiniteEngineRun == 0x759A80u);
        CHECK(lcns::kCloudEngineRun == 0x26A60u);
        CHECK(lcns::kInfiniteEngineDtor == 0x759AD0u);
        CHECK(lcns::kInfiniteEngineDeletingDtor == 0x759B20u);
        CHECK(lcns::kMultiEngineDeletingDtor != lcns::kMultiEngineDtor);

        // and the seven vtables are distinct, which is what makes them identifiers
        for (std::size_t i = 0; i < count; ++i) {
            for (std::size_t j = i + 1; j < count; ++j) {
                CHECK(family[i].vtable != family[j].vtable);
                CHECK(family[i].run != family[j].run);
            }
        }
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "engineFamily" in text:
        print("already present")
        return 0
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("added the Engine family test; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
