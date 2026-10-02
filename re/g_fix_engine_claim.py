# -*- coding: utf-8 -*-
"""Correct the claim that seven Engine classes were defined, and add the CompositeEngine test."""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")
TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

BLOCK = '''
    // ---------------------------------------------------------------- CompositeEngine::Run (RE 0x759B70)
    //
    // The class is named Composite and does not compose engines: its 184 calls reach 39 distinct targets and NOT ONE is another engine's
    // Run. What its prologue does is walk a container of SIXTEEN BYTE records and accumulate into locals.
    {
        CHECK(lcns::kCompositeEngineRunAddress == 0x759B70u);
        CHECK(lcns::kCompositeEngineStride == 0x10u);
        CHECK(lcns::kCompositeEngineStride == 16u);
        CHECK(lcns::kCompositeContainerBegin == 0x10u);
        CHECK(lcns::kCompositeContainerEnd == 0x18u);

        // the count a first element and an end give, which is `(end - begin) >> 4`
        CHECK(lcns::compositeElementCount(0x1000u, 0x1000u) == 0u);
        CHECK(lcns::compositeElementCount(0x1000u, 0x1010u) == 1u);
        CHECK(lcns::compositeElementCount(0x1000u, 0x1100u) == 16u);
        // a partial record is not counted, because the shift discards the remainder exactly as `sar` does
        CHECK(lcns::compositeElementCount(0x1000u, 0x100Fu) == 0u);

        // AND THE ENGINES IT DOES NOT CALL, which is the finding rather than an omission
        for (std::uintptr_t engine : lcns::kEnginesNotCalled) {
            CHECK(engine != lcns::kCompositeEngineRunAddress);
        }
        // the seven it might have called are seven distinct addresses
        for (int i = 0; i < 6; ++i) {
            for (int j = i + 1; j < 6; ++j) {
                CHECK(lcns::kEnginesNotCalled[i] != lcns::kEnginesNotCalled[j]);
            }
        }
        // and the eight loops are eight distinct bodies
        for (int i = 0; i < 7; ++i) {
            CHECK(lcns::kCompositeLoops[i] > 0x759B70u);
            CHECK(lcns::kCompositeLoops[i] < 0x759B70u + 8230u);
        }
    }
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "kCompositeEngineRunAddress" not in text:
        if '#include "lcns/engines_composite.hpp"' not in text:
            anchor = '#include "lcns/virtual_methods.hpp"\n'
            assert anchor in text, "the virtual_methods include is gone"
            text = text.replace(anchor, anchor + '#include "lcns/engines_composite.hpp"\n', 1)
            print("include added")
        marker = '    return check::finish("test_recovered");'
        assert marker in text, "the finish marker is gone"
        text = text.replace(marker, BLOCK + "\n" + marker, 1)
        io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
        print("CompositeEngine test added; lines now %d" % text.count("\n"))

    data = json.loads(io.open(LEDGER, encoding="utf-8").read())
    existing = {c["subject"] for c in data["claims"]}
    new = [
        {
            "grade": "INSTRUCTION",
            "kind": "offset",
            "subject": "CompositeEngine.does-not-compose",
            "predicate": ("CompositeEngine::Run calls NO other engine's Run, so the class does not compose engines; it walks a container "
                          "of 16 byte records and accumulates into locals"),
            "witness": ("RE 0x759B70's 184 calls reach 39 distinct targets and none is 0x755050, 0x756EC0, 0x757250, 0x759A80, 0x75BCC0 or "
                        "0x26A60; its prologue is 0x759B8B mov rax,[rdx+0x18], 0x759B8F sub rax,[rdx+0x10], 0x759BAA sar rax,4"),
            "round": 655,
        },
        {
            "grade": "INSTRUCTION",
            "kind": "offset",
            "subject": "Engine.family-not-defined",
            "predicate": ("the claim that seven Engine classes were defined was wrong: engines.hpp gives six of them a vtable address, "
                          "three slot addresses and a table row, and only InfiniteEngine is a class"),
            "witness": ("the human asked where CompositeEngine's implementation is; grepping engines.hpp finds class EngineBase, class "
                        "InfiniteEngine and struct EngineClass, and CompositeEngine appears only as four constexpr constants and a row"),
            "round": 655,
        },
    ]
    added = 0
    for claim in new:
        if claim["subject"] in existing:
            continue
        data["claims"].append(claim)
        added += 1
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=1, sort_keys=True))
    print("added %d claim(s), %d in the ledger" % (added, len(data["claims"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
