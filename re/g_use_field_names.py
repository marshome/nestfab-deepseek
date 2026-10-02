# -*- coding: utf-8 -*-
"""Point the readers and writers at the named fields instead of the raw offsets.

Round 540. The human's rule: where a structure has been identified, the code that reads and writes it must use the field
name, not a bare offset. Two places violate it and both are this project's own code, not the original's:

  * lcns/src/exports_impl.cpp -- the nine setters write +0x0C, +0x10, +0x68, +0x6C, +0x88, +0x8C, +0x98, +0x9C, +0xA0,
    +0xE0, +0xE8, +0xF0, +0x124, +0x128, +0x12C, +0x130, +0x240 through a local FieldWriter and integer literals. Those
    offsets all have names now, and `offsetof` on the named field is both clearer and checked by the compiler.
  * tests/test_exports.cpp asserts the same stores with `dword(0x8C)` and `order[0x68]`. A test that spells offsets is a test
    that has to be re-read after every layout edit, and it cannot catch the edit that moves a field, because it was written in
    the same units as the edit.

This rewrites both against lcns/launching_order.hpp. The offsets that do NOT have a name keep their integer form, and the
comment says which of the two it is -- that distinction is the whole point of the header's named/unnamed split.

The FieldWriter helper goes away with them: with named fields the setters are plain, checkable assignments through the
struct, which is what they always were.
"""
import io
import os
import re

ROOT = r"D:\Nesting\nestfab"
CPP = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_exports.cpp")

# offset -> (field name, kind). kind is 'dword', 'byte' or 'double'.
FIELDS = {
    0x00C: ("origin", "dword"),
    0x010: ("multiplicityPreference", "double"),
    0x068: ("commonCutSafetyPreferenceGiven", "byte"),
    0x06C: ("commonCutSafetyPreference", "dword"),
    0x088: ("commonCutCuttingPreferenceGiven", "byte"),
    0x08C: ("commonCutCuttingPreference", "dword"),
    0x098: ("multiTorchCuttingPreferenceGiven", "byte"),
    0x09C: ("multiTorchCuttingPreference", "dword"),
    0x0A0: ("multiTorchCuttingPreferencePositive", "byte"),
    0x0E0: ("markModeGiven", "byte"),
    0x0E8: ("markModeFirst", "double"),
    0x0F0: ("markModeSecond", "double"),
    0x124: ("specificSheetOriginGiven", "byte"),
    0x128: ("specificSheetOrigin", "dword"),
    0x12C: ("specificSheetObjectiveGiven", "byte"),
    0x130: ("specificSheetObjective", "dword"),
    0x240: ("automaticStop", "dword"),
    0x288: ("estimateLocalComputation", "dword"),
}


def main():
    text = io.open(CPP, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    changed = 0

    # the nine setters used a local FieldWriter; with named fields they are plain assignments through a typed pointer
    old_helper = """namespace {

/** A field and the "given" byte this module writes four bytes before it. RE 0xEA09/0xEA0D and its four siblings. */
struct FieldWriter {
    unsigned char* base;
    void writeByte(std::size_t offset, unsigned char value) const {
        std::memcpy(base + offset, &value, sizeof(value));
    }
    void writeDword(std::size_t offset, std::uint32_t value) const {
        std::memcpy(base + offset, &value, sizeof(value));
    }
    void writeDouble(std::size_t offset, double value) const {
        std::memcpy(base + offset, &value, sizeof(value));
    }
};

}  // namespace

"""
    new_helper = """namespace {

/** The order as the nine setters see it: the named layout, so a field is written by NAME.
 *
 * RE 0xEA09/0xEA0D and its four siblings established the shape these share -- a "given" byte four bytes before its value --
 * and lcns/launching_order.hpp now carries those offsets as named fields, so the setters below address them through
 * offsetof rather than through an integer. A layout edit that moves a field breaks the compile instead of silently writing
 * the wrong place.
 */
launchingOrder(void* order) {
    return static_cast<LaunchingOrderLayout*>(order);
}

}  // namespace

"""
    text = text.replace(old_helper, new_helper, 1)

    # rewrite each writer call into a named field assignment
    def writer(match):
        nonlocal changed
        offset = int(match.group(1), 16)
        method = match.group(2)
        value = match.group(3).strip()
        if offset not in FIELDS:
            return match.group(0)
        name, kind = FIELDS[offset]
        changed += 1
        return "launchingOrder(order)->%s = %s;" % (name, value)

    text = re.sub(r"FieldWriter\{static_cast<unsigned char\*>\(order\)\}\.write(Dword|Double|Byte)\((0x[0-9A-F]+), ([^;]+)\);",
                  lambda m: writer(re.match(r".*?\((0x[0-9A-F]+), ([^)]+)\)", m.group(0))), text)
    io.open(CPP, "w", encoding="utf-8", newline="\n").write(text)
    print("exports_impl.cpp: %d writer calls rewritten to named fields" % changed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
