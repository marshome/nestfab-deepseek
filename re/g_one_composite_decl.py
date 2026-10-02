# -*- coding: utf-8 -*-
"""One declaration of CompositeEngine, in engines_composite.hpp, included by engines.hpp.

Both headers declared it, so the compiler saw two definitions. The one with the body of evidence is engines_composite.hpp -- it carries the
stride, the container offsets, the eight loops and the six engines NOT called -- so engines.hpp includes it and drops its own copy.
"""
import io
import os
import re

ROOT = r"D:\Nesting\nestfab"
ENGINES = os.path.join(ROOT, "lcns", "include", "lcns", "engines.hpp")
COMPOSITE = os.path.join(ROOT, "lcns", "include", "lcns", "engines_composite.hpp")


def main():
    text = io.open(ENGINES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    # drop the generated CompositeEngine declaration block
    pattern = re.compile(r"/\*\* Engine::CompositeEngine, Run at 0x759B70, vtable 0xA3D000\.\n(?: \*.*\n)* \*/\n"
                         r"class CompositeEngine : public EngineBase \{\npublic:\n"
                         r"    CompositeEngine\(\) = default;\n\n"
                         r"    void\* run\(const void\* problem, double timeLimit, void\* observer, void\* result\) override;\n\};\n\n")
    if pattern.search(text):
        text = pattern.sub("// CompositeEngine is declared in lcns/engines_composite.hpp, which carries the evidence for it.\n\n", text, 1)
        print("dropped the duplicate declaration from engines.hpp")
    else:
        print("the duplicate block was not found by pattern; leaving it")
    if '#include "lcns/engines_composite.hpp"' not in text:
        anchor = "#include <cstdint>\n"
        assert anchor in text, "the include anchor is gone"
        text = text.replace(anchor, anchor + '\n#include "lcns/engines_composite.hpp"\n', 1)
        print("engines.hpp now includes engines_composite.hpp")
    io.open(ENGINES, "w", encoding="utf-8", newline="\n").write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
