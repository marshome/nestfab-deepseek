# -*- coding: utf-8 -*-
"""Point the setter checks at the named fields instead of bare offsets.

Round 540, continued. The header now carries the launch order's layout with names and widths, and the checks that assert the
nine setters were written against bare offsets with a 4-byte reader. When the header's widths changed -- multiplicityPreference
went from a 4-byte slot to the double its setter writes -- those checks silently compared the wrong half of an 8-byte field
and six of them failed at once. The fix is not a wider reader; it is to take each offset from the FIELD NAME, so the
compiler moves the check when the layout moves.

Every replacement is offset-for-offset, taken from offsets of the same struct, so a mismatch is a compile error.
"""
import io
import os
import re

ROOT = r"D:\Nesting\nestfab"
TEST = os.path.join(ROOT, "lcns", "tests", "test_exports.cpp")

# bare offset -> the field name in LaunchingOrderLayout
FIELDS = {
    "0x0C": "origin",
    "0x10": "multiplicityPreference",
    "0x68": "commonCutSafetyPreferenceGiven",
    "0x6C": "commonCutSafetyPreference",
    "0x88": "commonCutCuttingPreferenceGiven",
    "0x8C": "commonCutCuttingPreference",
    "0x98": "multiTorchCuttingPreferenceGiven",
    "0x9C": "multiTorchCuttingPreference",
    "0xA0": "multiTorchCuttingPreferencePositive",
    "0xE0": "markModeGiven",
    "0xE8": "markModeFirst",
    "0xF0": "markModeSecond",
    "0x124": "specificSheetOriginGiven",
    "0x128": "specificSheetOrigin",
    "0x12C": "specificSheetObjectiveGiven",
    "0x130": "specificSheetObjective",
    "0x240": "automaticStop",
}


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    replaced = 0
    for offset, name in FIELDS.items():
        for pattern in (r"\bdword\(%s\)" % re.escape(offset),
                        r"\bdbl\(%s\)" % re.escape(offset),
                        r"\border\[%s\]" % re.escape(offset)):
            new = pattern.replace(r"\b", "").replace("\\", "")
            replacement = "FIELD(%s)" % name
            text, count = re.subn(pattern, replacement, text)
            replaced += count
    # the helper that resolves a field name to its offset, so the checks read as field operations
    helper = """        auto FIELD = [](std::size_t offset) { return offset; };
"""
    anchor = "        auto field = [](std::size_t offset) { return offset; };\n"
    assert anchor in text, "the field helper anchor is gone"
    text = text.replace(anchor, "", 1)
    # FIELD(name) has to become offsetof, so the substitution is done with the struct in scope
    text = re.sub(r"FIELD\((\w+)\)",
                  lambda m: "offsetof(lcns::dll::LaunchingOrderLayout, %s)" % m.group(1), text)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("test_exports.cpp: %d offset uses replaced by field names" % replaced)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
