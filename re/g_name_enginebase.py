# -*- coding: utf-8 -*-
"""Name EngineBase in the test, now that the deleted members no longer reference it.

`EngineBase` is the interface the seven engines implement, and `check_recovery` requires every declared class to be named by a test. The
InfiniteEngine block used to name it through `setInner(EngineBase*)`; that member is deleted, so the interface has to be named for its own sake.
"""
import io
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
ANCHOR = '    return check::finish("test_recovered");'

BLOCK = '''
    // ---------------------------------------------------------------- the Engine interface (EngineBase)
    //
    // The pure virtual every engine in the family implements, and RE 0x2516E is what says its slot is 2 and its signature is
    // `(problem, timeLimit, observer, result)` returning the result buffer.
    {
        static_assert(std::is_abstract<lcns::EngineBase>::value, "EngineBase has a pure virtual run and cannot be instantiated");
        static_assert(std::is_base_of<lcns::EngineBase, lcns::InfiniteEngine>::value, "the seven engines implement it");
        static_assert(std::is_base_of<lcns::EngineBase, lcns::MultiEngine>::value, "and so does every other");
        static_assert(std::is_base_of<lcns::EngineBase, lcns::CloudEngine>::value, "including the cloud engine");

        // a pointer to the interface reaches the engine's own run, which is what the module's vtable does
        lcns::MultiEngine engine;
        lcns::EngineBase* asInterface = &engine;
        void* result = reinterpret_cast<void*>(0x55);
        CHECK(asInterface != nullptr);
        CHECK(asInterface->run(nullptr, 1.0, nullptr, result) == result);
    }
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "EngineBase" in text:
        print("the test already names EngineBase")
        return 0
    text = text.replace(ANCHOR, BLOCK + "\n" + ANCHOR, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("named EngineBase; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
