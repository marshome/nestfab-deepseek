# -*- coding: utf-8 -*-
"""Rename the one generated namespace that collides, and point the test at the real locations.

TWO PROBLEMS FROM THE FIRST GENERATION, both about names rather than facts:

  * `Engine` in the RTTI is a NAMESPACE (`Engine::CompositeObserver`), while this repository already has `lcns::Engine` as a CLASS. A
    namespace and a class of one name cannot coexist, so the generated namespace is `EngineNS` with the original recorded in the table.
  * several classes the test named are declared BY HAND in `lcns` (nester.hpp has `class FlipNester`), not in a `Multi` namespace, so the
    test's `lcns::Multi::FlipNester` was wrong and `lcns::FlipNester` is right. The generator skipped them because a hand-written header
    declares them, which is correct behaviour and the test was what needed fixing.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
GEN = os.path.join(ROOT, "re", "g_gen_class_definitions.py")
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")


def fix_generator():
    text = io.open(GEN, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    marker = "    # the declarations, grouped by namespace, skipping anything a hand-written header already declares"
    assert marker in text, "the generator's marker moved"
    patch = '''    # ONE NAMESPACE COLLIDES AND IS RENAMED. `Engine` in the RTTI is a namespace; this repository already has `lcns::Engine` as a
    # class, and a namespace and a class cannot share a name. The generated namespace is `EngineNS` and the table keeps the RTTI's own
    # qualified name, so nothing is lost -- only the emitted identifier differs, and it says why.
    RENAME = {"Engine": "EngineNS"}

''' + marker
    text = text.replace(marker, patch, 1)
    text = text.replace('        by_namespace.setdefault(namespace, []).append((short, qualified, vtable, slots, first, size))',
                        '        by_namespace.setdefault(RENAME.get(namespace, namespace), []).append((short, qualified, vtable, slots, first, size))', 1)
    io.open(GEN, "w", encoding="utf-8", newline="\n").write(text)
    print("generator: the Engine namespace is emitted as EngineNS")


def fix_test():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    pairs = [
        ("lcns::Multi::FlipNester", "lcns::FlipNester"),
        ("lcns::Multi::FilterNester", "lcns::FilterNester"),
        ("lcns::Multi::NoFillNester", "lcns::NoFillNester"),
        ("lcns::Multi::TilingNester", "lcns::TilingNester"),
        ("lcns::Multi::DatabaseNester", "lcns::DatabaseNester"),
        ("lcns::Structure::Observer", "lcns::Structure::Observer"),
        ("lcns::Tiling::BoxMultiTiler", "lcns::Tiling::BoxMultiTiler"),
    ]
    for old, new in pairs:
        text = text.replace(old, new)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("test: names corrected to where the classes are actually declared")


if __name__ == "__main__":
    fix_generator()
    fix_test()
