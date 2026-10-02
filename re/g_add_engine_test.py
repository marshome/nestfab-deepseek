# -*- coding: utf-8 -*-
"""Add the InfiniteEngine test, which check_recovery requires for a newly declared name and which the class needs anyway."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- InfiniteEngine (RE 0x759A80)
    //
    // The one Engine subclass whose body has been read. RE 0x759A80 is a DECORATOR with a sentinel: a time limit of exactly -1.0 means
    // nest until done, and any other limit goes to the inner engine at this+0x10.
    {
        lcns::InfiniteEngine engine;
        CHECK(engine.inner() == nullptr);
        CHECK(lcns::kRunInfiniteEngine == 0x759A80);
        CHECK(lcns::kNestingEngineRun == 0x757AE0);
        CHECK(lcns::kEngineRunSlot == 0x10);           // RE 0x2516E: call qword ptr [rax + 0x10]
        CHECK(lcns::kUnlimitedTime == -1.0);           // the double at rva 0x9AE740
        CHECK(lcns::kUnlimitedTimeConstant == 0x9AE740);

        // the seven slots are seven distinct addresses
        const std::uintptr_t slots[7] = {lcns::kRunMultiEngine, lcns::kRunDelayedEngine, lcns::kRunNestingEngine,
                                         lcns::kRunInfiniteEngine, lcns::kRunCompositeEngine, lcns::kRunEquivalentEngine,
                                         lcns::kRunCloudEngine};
        for (int i = 0; i < 7; ++i) {
            for (int j = i + 1; j < 7; ++j) {
                CHECK(slots[i] != slots[j]);
            }
        }

        // THE DECISION, driven with two markers so which arm ran is visible rather than assumed
        int unlimitedRan = 0;
        int delegatedRan = 0;
        void* result = reinterpret_cast<void*>(0x1234);

        void* out = engine.dispatch(lcns::kUnlimitedTime, result,
                                    [&](void*) -> void* { ++unlimitedRan; return result; },
                                    [&](lcns::EngineBase*, void* r) -> void* { ++delegatedRan; return r; });
        CHECK(unlimitedRan == 1);
        CHECK(delegatedRan == 0);
        CHECK(out == result);                          // RE 0x759A9E: mov rax, rbx

        // any other limit delegates
        unlimitedRan = delegatedRan = 0;
        out = engine.dispatch(10.0, result,
                              [&](void*) -> void* { ++unlimitedRan; return result; },
                              [&](lcns::EngineBase*, void* r) -> void* { ++delegatedRan; return r; });
        CHECK(unlimitedRan == 0);
        CHECK(delegatedRan == 1);
        CHECK(out == result);                          // RE 0x759AC7

        // AND A NaN DELEGATES, because 0x759A90 is `jp` -- so "unlimited" is exactly -1.0 and not "any special value"
        unlimitedRan = delegatedRan = 0;
        const double nan = std::numeric_limits<double>::quiet_NaN();
        out = engine.dispatch(nan, result,
                              [&](void*) -> void* { ++unlimitedRan; return result; },
                              [&](lcns::EngineBase*, void* r) -> void* { ++delegatedRan; return r; });
        CHECK(unlimitedRan == 0);
        CHECK(delegatedRan == 1);
        CHECK(out == result);

        // zero is a limit and not the sentinel, which is the distinction the comparison makes
        unlimitedRan = delegatedRan = 0;
        engine.dispatch(0.0, result,
                        [&](void*) -> void* { ++unlimitedRan; return result; },
                        [&](lcns::EngineBase*, void* r) -> void* { ++delegatedRan; return r; });
        CHECK(delegatedRan == 1 && unlimitedRan == 0);

        // the member at +0x10 is settable, which is the offset RE 0x759AB0 reads
        engine.setInner(nullptr);
        CHECK(engine.inner() == nullptr);
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "InfiniteEngine" in text:
        print("already present")
        return 0
    if '#include "lcns/engines.hpp"' not in text:
        anchor = '#include "lcns/miplib_names.hpp"\n'
        assert anchor in text, "the miplib_names include is gone"
        text = text.replace(anchor, anchor + '#include "lcns/engines.hpp"\n', 1)
        print("added the include")
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("added the InfiniteEngine test; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
