# -*- coding: utf-8 -*-
"""Rewrite InfiniteEngine's declaration: no members, because no instruction supports one, and the run's real source of the engine is the problem.

THE MISREADING, and this is the fifth instance of the same failure in this session: `[rdx + 0x10]` at 0x759AB0 was recorded as an offset from
`this`. **In slot 2, `rdx` is the SECOND argument.** The consequence was an `inner_` member, a `setInner`/`inner` pair, and a `dispatch` template
whose delegate had to be supplied by the caller -- three pieces of API existing only to support a member that does not exist.
"""
import io
import os
import re
import sys

ENGINES = r"D:\Nesting\nestfab\lcns\include\lcns\engines.hpp"

OLD_START = "class InfiniteEngine : public EngineBase {"
OLD_END = "\n};\n"

NEW = '''/** What RE 0x759AB0 reads out of the SECOND argument: the engine it delegates to sits at +0x10 of the problem. */
struct ProblemView {
    std::byte header[0x10]{};
    EngineBase* engine = nullptr;      // RE 0x759AB0: mov rdx, [rdx + 0x10]
};

class InfiniteEngine : public EngineBase {
public:
    InfiniteEngine() = default;

    /** **THE CLASS HAS NO MEMBER THAT AN INSTRUCTION SUPPORTS.** RE 0x759A80 reads `this` only in order to return it -- `mov rbx, rcx` at
     *  0x759A8D and `mov rax, rbx` at 0x759A9E -- and the engine it delegates to comes from the PROBLEM's +0x10, because in slot 2 `rdx` is
     *  the second argument and NOT `this`. An earlier `inner_` member at +0x10 was a misreading of that, and `setInner`, `inner` and the
     *  `dispatch` template existed only to serve it; they are deleted rather than left looking recovered.
     *
     *  The class's whole content is the DECISION: unlimited time enters the nesting engine at 0x757AE0 directly, and anything else -- a NaN
     *  included, because the branch is a `jp` -- goes through the engine the problem carries. */
    void* run(const void* problem, double timeLimit, void* observer, void* result) override;
};
'''


def main():
    text = io.open(ENGINES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find(OLD_START)
    if start < 0:
        print("REFUSING: the InfiniteEngine declaration is not found")
        return 2
    end = text.find(OLD_END, start)
    if end < 0:
        print("REFUSING: the class's closing brace is not found")
        return 2
    # the doc comment immediately above the class belongs to it
    comment = text.rfind("/**", 0, start)
    if comment > 0 and text.count("*/", comment, start) == 1:
        start = comment
    text = text[:start] + NEW + text[end + len(OLD_END):]
    io.open(ENGINES, "w", encoding="utf-8", newline="\n").write(text)
    print("rewrote InfiniteEngine's declaration")
    print("  removed: inner_, setInner, inner, dispatch, the private section")
    print("  added:   ProblemView, and the run with no member to delegate to")
    return 0


if __name__ == "__main__":
    sys.exit(main())
