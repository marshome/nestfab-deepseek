# -*- coding: utf-8 -*-
"""Append the rounds 525 to 529 reading of the LaunchLocalComputation orbit to re/EXPORT_BODIES.md.

The bodies themselves are in re/LEAVES51.txt and the classifications in re/g_toolchain.py; this records the three this
round actually read instruction by instruction -- the module's lazy static and its fast path, the diagnostic header they
build, and the two node routines -- so EXPORT_BODIES.md stays the place the read bodies live.
"""
import io

PATH = r"D:\Nesting\nestfab\re\EXPORT_BODIES.md"

NOTE = """

## The LaunchLocalComputation orbit read so far (rounds 525 to 529)

The closure of ordinal 51 was read whole in three passes and every entry has its evidence next to its address in
`re/g_toolchain.py`. What follows is the part that is a body rather than a classification.

### 0x1BF40, 0x1BF00 and 0x1BE70: the module's own lazy static

    1BE70  if ([rip + 0xB03514] != 0) return [rip + 0xB03511]    ; already built
           guard = __cxa_guard_acquire([rip + 0xB034F9])
           if (guard == 0) goto already
           if (guard) 0x65A530([rip + 0xB034DD])                  ; THE CONSTRUCTION
           __cxa_guard_release / register through 0x998EE0
           return [rip + 0xB034D9]

    1BF00  return [[1BE70()] + 1]        ; one byte of that static

    1BF40  static = 1BE70()
           if ([static + 0] == 0) return null                     ; the static says "off"
           if ([rip + 0xB0324A] != 0) goto done                   ; already made
           guard = __cxa_guard_acquire([rip + 0xB03219])
           if (guard) 0x7BB430([rip + 0xB03222])                  ; THE DIAGNOSTIC HEADER
           __cxa_guard_release / register through 0x998EE0
     done: if ([rip + 0xB03348] != 0) return null
           return [rip + 0xB03255]                                ; the ostringstream itself

So the entry point's first call, 0x1BF00, is one byte of a module-wide static, and its second, 0x1BF40, is that static's
diagnostic stream, built on first use. 0x2AB0 gets null from 0x1BF40 only when the static is off or its build id is zero,
and it writes into the stream otherwise.

### 0x7BB430: the diagnostic header, read whole

    88B6F0(stream, 0x30)                     ; the ostringstream constructor
    if ([order + 0xE8] != 0) return          ; already written
    978010 / 9878C0  'CNS informations'
    978010           [rip + 0xA07660]        ; the module's version object
    978010           the value at [rip + 0xA076A0], then ' '
    8693D0(stream, 0x40)                     ; a fill of 0x40
    cpuid leaf 0 -> eax = the highest leaf, then leaf 1:
        edx = (eax >> 0xC) & 0xF0 | (eax >> 4) & 0xF
    1B170('%d', that value)                  ; one number into a stack string
    978010 / 9878C0  the stack string        ; the CPU family and model
    B81F0() -> 869D00 -> 9878C0              ; the vendor string
    B8210() -> 978010 / 9878C0               ; the brand string, 727 bytes of it

That is a machine and build identification header: the product name, the module's version and build objects, one number
derived from CPUID leaf 1, the vendor string and the brand string. Its caller 0x1BF40 then appends two more numbers through
0x62D860. It is the same family as the `c:\\Temp\\*_nest.txt` logging the module does elsewhere, and its 0x40 byte fill and
0x30 constructor argument are the only reasons it sits inside this closure at all.

### 0x22A20: the object the orchestration builds

Its head and tail are implemented in `lcns/include/lcns/field_accessors.hpp`; the reading is in the round 529 section of
`re/CATEGORIES.md` and in `re/LAUNCH_LOCAL_COMPUTATION.md`. The one number worth repeating here is the mode: the constructor
branches on `[order + 0x240]` and configures an iteration cap of 500 with the pair 10.0 and 0.2 in mode 1, a cap of 10 with
3.0 in mode 2, and a cap of 10 with 4.0 and 0.1 otherwise. The five literal doubles decoded from the dump are 4.0 at
0x9AE1E8, 0.1 at 0x9AE1F0, 10.0 at 0x9AE1F8, 0.2 at 0x9AE200 and 3.0 at 0x9AE208.

### 0x9302C0 and 0x9308C0: an intrusive list of 0x48 byte nodes

Both recurse over a forward chain at +0x18 and both treat a doubly-linked list through +0x10 and +0x18:

    9302C0(base, src, 0x48):                 ; the copier, called once by 0x22A20
        node = new(0x48)
        node[0x20] = node + 0x30             ; the inline buffer of the string
        copy([src + 0x20] .. [src + 0x28], node[0x20])
        node[0x00] = src[0x00]               ; a type dword
        node[0x08] = the second argument
        node[0x10] = 0                       ; the back pointer is rewritten by the caller
        node[0x18] = (src[0x18] ? 9302C0(base, src[0x18], ..) : 0)
        node[0x40] = src[0x40]               ; the double
        for (p = src[0x10]; p; p = p[0x10]) { q = new(0x48); copy p into q; q[0x10] = previous; previous[0x18] = q; }
        return node

    9308C0(base, head):
        recurse into head[0x18]; free head[0x20] unless head[0x20] == head + 0x30; free head; free the node the second
        argument pointed at; then walk the list at head[0x10] freeing each node and its string.

The node is 0x48 bytes: a type dword at +0, an owner pointer at +8, a back pointer at +0x10, a forward pointer at +0x18, an
inline string at +0x20 with its length at +0x28, a double at +0x40. The two functions are read but not reimplemented: the
list's owner is not yet known, so what a node MEANS cannot be asserted yet, and writing a free routine whose ownership rule
is a guess would be worse than leaving it read.
"""


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "## The LaunchLocalComputation orbit read so far" in text:
        print("the note is already there; nothing written")
        return 0
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text.rstrip("\n") + "\n" + NOTE)
    print("appended %d characters to re/EXPORT_BODIES.md" % len(NOTE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
