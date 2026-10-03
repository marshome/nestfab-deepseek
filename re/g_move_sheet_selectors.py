# -*- coding: utf-8 -*-
"""Move the sheet-selector family OUT of `lcns::tiling` and into `lcns`, where its own name puts it.

**THE MODULE NAMES THE CLASS `Multi::SheetSelector`** -- `N5Multi13SheetSelectorE` -- **and a namespace in the port's headers is a naming decision that has to
follow the module's.** `Tiling::Pattern`, `Multi::Nester` and the rest follow theirs; this family is `Multi::`, so `lcns::tiling` was the wrong home and the
build said so: `'SheetSelector' is not a member of 'lcns'`.

**AND THE BLOCK WAS INSERTED BY ITS FIRST ANCHOR RATHER THAN BY ITS SEMANTICS** -- `g_declare_nomix_selector.py` put it before the second `class` it found, which
was inside the nested namespace. That is the same class of mistake as a regex that crosses a newline: **a rule applied without asking what the surrounding
thing is.**
"""
import io
import sys

TARGET = r"D:\Nesting\nestfab\lcns\include\lcns\tiling.hpp"

START = "// ---------------------------------------------------------------------------\n// The sheet-selector family -- RE: 0xAFD60"
END_MARK = "std::byte member38_[0x18];                        // NOT REVERSED: a sub-object constructed by 0xAFD7D0"


def main():
    text = io.open(TARGET, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find(START)
    if start < 0:
        print("REFUSING: the family's block is not found")
        return 2
    # the end of the block: the closing brace of NoMixSheetSelector
    tail = text.find("\n};\n", text.find("member38_", start))
    if tail < 0:
        print("REFUSING: the block's closing brace is not found")
        return 2
    block = text[start:tail + len("\n};\n")]
    text = text[:start] + text[tail + len("\n};\n"):]

    # **THE NEW HOME IS `lcns` ITSELF, AFTER THE NESTED NAMESPACES CLOSE.** The header's last `}` before EOF is `namespace lcns`'s, so the block goes just
    # before it -- and the marker is found from the END, because that is the one that closes `lcns`.
    close = text.rfind("\n}  // namespace lcns")
    if close < 0:
        close = text.rfind("\n}")
    if close < 0:
        print("REFUSING: the namespace's closing brace is not found")
        return 2
    text = text[:close] + "\n" + block + text[close:]
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(text)
    print("the sheet-selector family is now declared in lcns, before the namespace closes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
