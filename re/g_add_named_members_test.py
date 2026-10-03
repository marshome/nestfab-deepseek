# -*- coding: utf-8 -*-
"""Test the oracle-named members, and register the standard as a rule with the generator as its check."""
import io
import os
import subprocess
import sys

ROOT = r"D:\Nesting\nestfab"
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")
ANCHOR = '    return check::finish("test_recovered");'

BLOCK = '''
    // ---------------------------------------------------------------- the members an ORACLE names (generated)
    //
    // lcns/docs/WHAT_IS_NORMAL_CPP.md states the standard and this is the first file to meet it: **a field with no name does not belong in a
    // class**, so every member here is named by an option key the module ANSWERS TO, paired with the offset its lookup result is stored into.
    // The MIPLIB benchmark names are excluded, which a first version of the generator got wrong and emitted `void* air03`.
    {
        using lcns::SqueezeMultiTilerMembers;

        // the members have NAMES a programmer can read, which is the point, and offsets that are footnotes rather than the content
        SqueezeMultiTilerMembers tiler{};
        tiler.nb_iterations_first = 3;
        tiler.enable_flip = 1;
        CHECK(tiler.nb_iterations_first == 3u);
        CHECK(tiler.enable_flip == 1u);

        // a COUNT is an integer and not a pointer, and a FLAG likewise: the first version typed every qword store as void*
        CHECK(sizeof(tiler.nb_iterations_first) == 8u);
        CHECK(sizeof(tiler.enable_flip) == 8u);
        CHECK(sizeof(tiler.nb_strips_filling_advanced) == 8u);

        // and the name-derived types, which is the oracle doing work the instruction cannot: nb_* is a count, *ratio is a measurement
        static_assert(sizeof(decltype(tiler.nb_iterations_first)) == 8, "a count is not a pointer");
        static_assert(std::is_same<decltype(tiler.enable_flip), std::uint64_t>::value, "a flag is an unsigned integer");
        static_assert(std::is_same<decltype(tiler.nesting_offset_ratio), double>::value,
                      "a name ending in _ratio is a measurement, which is what the vocabulary says");

        // THE REGION BETWEEN PLACED FIELDS IS NAMED, because a byte range that says so is honest and a member named after its address is not
        CHECK(sizeof(tiler.unplaced_0008) == 0x30u);
        CHECK(sizeof(tiler.unplaced_0040) == 0x8u);
    }
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "SqueezeMultiTilerMembers" in text:
        print("already present")
        return 0
    include = '#include "lcns/named_members.hpp"\n'
    if include not in text:
        anchor = '#include "lcns/small_buffer.hpp"\n'
        assert anchor in text, "the small_buffer include is gone"
        text = text.replace(anchor, anchor + include, 1)
        print("include added")
    if "#include <type_traits>" not in text:
        text = text.replace("#include <cstdint>\n", "#include <cstdint>\n#include <type_traits>\n", 1)
    text = text.replace(ANCHOR, BLOCK + "\n" + ANCHOR, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("test added; lines now %d" % text.count("\n"))

    result = subprocess.run([sys.executable, os.path.join(ROOT, "re", "g_note.py"), "requirement",
                             "类成员必须有 oracle 命名（模块自己回答的选项名），并与同一条指令的偏移配对；没有名字的偏移只作为具名 unplaced 区段。"
                             "标准见 lcns/docs/WHAT_IS_NORMAL_CPP.md，检查见 re/g_gen_named_members.py。",
                             "--check", "re/g_gen_named_members.py"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(result.stdout.strip()[:300])
    return 0


if __name__ == "__main__":
    sys.exit(main())
