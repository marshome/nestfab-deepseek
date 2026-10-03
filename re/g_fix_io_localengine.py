# -*- coding: utf-8 -*-
"""Point the io code at the FIELD THE MODULE HAS, now that `localEngine` is split into `engineLo`/`engineHi`.

**`SetLocalEngine` AT 0xD370 WRITES TWO BYTES AND `Order` DECLARED ONE BOOL**:

    0xD390  mov byte [rsi + 0x200], al    ; the complement of the argument's low bit
    0xD3A0  mov byte [rsi + 0x201], bl    ; the complement of bit one

**so the module's +0x200 is one byte and +0x201 is another**, and `io.cpp` serialises the range under the names `local_engine`, `local_max_threads` and
`local_max_iterations`. The scalar is kept for the FIRST of the two bytes -- `engineLo`, which is what +0x200 is -- and `engineHi` is not serialised because
the file format has no key for it and inventing one would be a second name for a field the module names by its offset.

**AND THE TYPES FOLLOW THE STORES**: `maxThreads` and `maxIterations` are `std::uint32_t`, because `mov dword [rsi], eax` at 0xD3D5 and 0xD3E7 is four bytes;
`engineLo` is one byte. **`asInt`/`asBool` return `int`/`bool`, so each assignment is narrowed explicitly rather than left to the compiler.**
"""
import io
import sys

IO = r"D:\Nesting\nestfab\lcns\src\io.cpp"
TEST = r"D:\Nesting\nestfab\lcns\tests\test_io.cpp"


def fix(path, pairs):
    text = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    changed = 0
    for old, new in pairs:
        if old in text:
            text = text.replace(old, new, 1)
            changed += 1
        else:
            print("   NOT FOUND in %s: %s" % (path.rsplit("\\", 1)[-1], old.strip()[:70]))
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)
    print("   %s: %d replaced" % (path.rsplit("\\", 1)[-1], changed))


def main():
    fix(IO, [
        ('root.set("local_engine", Value(order.localEngine));',
         '// RE 0xD390: the module stores ONE BYTE at +0x200, so this is the byte and not a bool\n'
         '    root.set("local_engine", Value(static_cast<unsigned int>(order.engineLo)));'),
        ('out.localEngine = root.get("local_engine").asBool(false);',
         'out.engineLo = static_cast<std::uint8_t>(root.get("local_engine").asInt(0) & 0xFFu);   // RE 0xD390, one byte at +0x200'),
        ('root.set("local_max_threads", Value(order.maxThreads));',
         'root.set("local_max_threads", Value(static_cast<unsigned int>(order.maxThreads)));   // RE 0xD3D5: mov dword [rsi], eax\n'
         '    root.set("local_engine_hi", Value(static_cast<unsigned int>(order.engineHi)));   // RE 0xD3A0: mov byte [rsi + 0x201], bl'),
    ])
    fix(TEST, [
        (".localEngine", ".engineLo"),
    ])
    return 0


if __name__ == "__main__":
    sys.exit(main())
