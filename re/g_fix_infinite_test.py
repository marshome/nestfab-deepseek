# -*- coding: utf-8 -*-
"""Rewrite the InfiniteEngine test for the corrected class: the decision is exercised through run(), with a ProblemView.

The members the test called -- `inner()`, `dispatch()` -- are deleted because no instruction supports them, so the test now drives the DECISION
the module actually makes, on the object the module actually reads it from.
"""
import io
import re
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

BLOCK = '''    // ---------------------------------------------------------------- InfiniteEngine's decision (RE 0x759A80)
    //
    // **THE CLASS HAS NO MEMBERS**, because RE 0x759A80 reads `this` only to return it: `mov rbx, rcx` at 0x759A8D and `mov rax, rbx` at
    // 0x759A9E. The engine it delegates to comes from the SECOND argument's +0x10 -- in slot 2 `rdx` is the problem, not `this` -- which is
    // what an earlier `inner_` member at +0x10 misread. So the test drives `run` and the ProblemView, and there is nothing else to drive.
    {
        CHECK(lcns::kEngineRunSlot == 0x10u);
        CHECK(lcns::kUnlimitedTime == -1.0);
        CHECK(offsetof(lcns::ProblemView, engine) == 0x10u);      // RE 0x759AB0: mov rdx, [rdx + 0x10]

        lcns::InfiniteEngine engine;
        lcns::MultiEngine nested;
        lcns::ProblemView problem;
        problem.engine = &nested;

        void* result = reinterpret_cast<void*>(0x1234);

        // UNLIMITED: the nesting engine's own entry at 0x757AE0, whose body is NOT READ, so the arm is recorded and returns the buffer
        CHECK(engine.run(&problem, lcns::kUnlimitedTime, nullptr, result) == result);

        // ANY OTHER LIMIT delegates to the engine the problem carries, and the buffer comes back
        CHECK(engine.run(&problem, 10.0, nullptr, result) == result);

        // AND A NaN DELEGATES, because 0x759A90 is a `jp` -- "unlimited" is exactly -1.0 and not any special value
        const double nan = std::numeric_limits<double>::quiet_NaN();
        CHECK(engine.run(&problem, nan, nullptr, result) == result);

        // zero is a limit and not the sentinel, so it delegates too
        CHECK(engine.run(&problem, 0.0, nullptr, result) == result);

        // A PROBLEM WITH NO ENGINE IS HANDLED rather than dereferenced: 0x759AB9 loads the vtable from [rdx], and a null there would fault
        lcns::ProblemView empty;
        CHECK(engine.run(&empty, 10.0, nullptr, result) == result);
    }
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    lines = text.split("\n")
    headers = [(i, l) for i, l in enumerate(lines) if re.match(r"^    // -{20,} ", l)]
    start = end = None
    for position, (index, line) in enumerate(headers):
        if "InfiniteEngine" in line:
            start = index
            end = headers[position + 1][0] if position + 1 < len(headers) else len(lines)
            break
    if start is None:
        print("no InfiniteEngine block found")
        return 1
    print("replacing lines %d..%d" % (start + 1, end))
    out = lines[:start] + BLOCK.split("\n") + lines[end:]
    io.open(TEST, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("lines now %d" % len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
