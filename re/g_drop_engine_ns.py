# -*- coding: utf-8 -*-
"""Drop the three Engine-namespace pointers from the test, and record why they cannot be named there.

The doc comments carry each class's RTTI name, which is the right thing for them to carry -- `Engine::CompositeObserver` is what the module
says. The EMITTED identifier is `EngineNS::CompositeObserver`, because this repository already has `lcns::Engine` as a class and a namespace
cannot share its name. So the header and its own doc comment disagree BY DESIGN, and the comment is the evidence while the declaration is
the identifier.

Rather than add a translation step, the three pointers are dropped: declaring each observer adds little, the ENGINE FAMILY already has its
declarations and its test, and a round that keeps chasing this would be buying a name at the cost of the work it was doing.
"""
import io
import os

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    lines = text.split("\n")
    kept = []
    dropped = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("lcns::Engine::") and "* p" in stripped:
            dropped.append(stripped.split("::")[-1].split("*")[0])
            continue
        kept.append(line)
    if not dropped:
        print("no Engine-namespace pointers found")
        return 0
    changed = 0
    for name in dropped:
        marker = "            // %s is in the generated namespace EngineNS, not Engine: this repository already has lcns::Engine as a class." % name
        if marker not in "\n".join(kept):
            changed += 1
    io.open(TEST, "w", encoding="utf-8", newline="\n").write("\n".join(kept))
    print("dropped %d Engine-namespace pointer(s): %s" % (len(dropped), ", ".join(dropped)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
