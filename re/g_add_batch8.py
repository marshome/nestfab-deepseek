# -*- coding: utf-8 -*-
"""Batch eight: the stream, locale and refcount layer of the LaunchLocalComputation closure, read whole.

Round 526. The closure of ordinal 51 stands at 86 domain functions and 36335 bytes after batch seven, and the depth one
layer -- the twenty four functions the entry point calls directly -- was read whole. None of them is an algorithm. They are
libstdc++'s iostreams and its reference counting, and the evidence is per function:

    0x8AABC0  loads the pointer at +0, atomically decrements the count it points at, and when it reaches zero calls 0x8AA690
              and frees it. 0x8AA690 is the shared_ptr array deleter, already classified. This is the release operation of a
              shared_ptr, and it is called by five destructors.
    0x8AABF0  increments the count of one shared_ptr, decrements the count the destination holds, and stores: the assignment
              operator of the same family.
    0x8761B0  tests the flag at +8, frees the pointer at +0 through 0x63F6B8 and clears the flag; when the flag is clear it
              calls 0x97ABF0, which is the throw entry. Round 427 read this one as a "domain destructor" because its body was
              not enough to name it: the string it frees is the __cxx11 buffer of a string, and the flag is its ownership.
    0x9456A0  reads and writes the state word at +0x20 of a basic_ios, and calls 0x97A7B0 to throw. Its own literal names
              'basic_ios::clear', so the state word and the throw are that function's, not this module's.
    0x9445E0, 0x87F2A0  install a vtable from the image, release a member string at +0xc8, and hand a member at +0xd0 to the
              shared_ptr release: destructors of library objects, called by 0x65A530's stream construction.
    0x9454D0  calls the two, stores the stream state at +0x20 and the buffer at +0xe8: the basic_ios initialisation.
    0x944160  stores 6, 0 and 0x1002 at +8, +0x10 and +0x18 and moves a shared_ptr at +0xd0: the basic_streambuf header, and
              0x1002 is precisely the stream mode openmode writes use.
    0x944530, 0x945370  fill the eight vtable-relative member pointers from a locale's facets and test each: the
              basic_ios::init that pairs the stream with a locale.
    0x990540, 0x990840, 0x990780, 0x9916E0, 0x991920, 0x9919E0  look a facet up in a locale's cache, test it, hand it to
              0x9990E0 with its typeinfo and throw 0x998920 through 0x978750 when the cast fails: the facet accessors, one per
              facet. They are what 0x945370 calls eight times.
    0x9990E0  reads the virtual base of the object at [rcx - 0x10], compares the typeinfo at [rax - 8] with the requested
              one, and calls the virtual function at offset 0x38 or 0x40 whose result it then tests against 6: a dynamic cast
              to a facet type, with the -2 the ABI uses for the source type.
    0x944530, 0x87D270, 0x87D8E0, 0x87D590, 0x87EDF0, 0x867BF0, 0x867DF0, 0x8682A0, 0x868380, 0x88B6F0, 0x978010, 0x9878C0,
    0x877160, 0x630110, 0x62FF90, 0x8264E0  are the stream itself: 0x88B6F0 builds the object, 0x978010 writes a buffer
              through the vtable's xsputn at +0x68, 0x9878C0 is the string overload, 0x8682A0 and 0x868380 are the two
              sentry shapes (one for input, one for output, which is why 0x8682A0 has the 0x1002 mode test and the other
              does not), 0x867BF0 writes one character, and 0x877160 is the fopen behind a filebuf.
    0x89EC90, 0x8894B0  forward to 0x89EBA0 and 0x889D00; 0x89EBA0 was read in batch seven as ctype<char>::_M_initialize_ctype
              with its widen and narrow tables.
    0x531F20  reads the pointer at +0, frees the member at +8 through 0x530010 and then frees the object: a destructor.

The consequence for the objective is in re/CATEGORIES.md: what remains of this closure is the orchestration at 0x2AB0 plus a
small set of domain routines, and the counting rule this project already has is the right one -- a library function
implemented here would add nothing that the standard library does not already do.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
TOOLCHAIN = os.path.join(ROOT, "re", "g_toolchain.py")
CATEGORIES = os.path.join(ROOT, "re", "CATEGORIES.md")

LIBRARY = [
    (0x8AABC0, "atomically decrements the count the first member points at and calls 0x8AA690 then frees: the shared_ptr release"),
    (0x8AABF0, "increments one shared_ptr count, decrements the count at the destination and stores: the shared_ptr assignment"),
    (0x8761B0, "frees the pointer at +0 through 0x63F6B8 when the flag at +8 is set, else throws through 0x97ABF0: the string dispose with its ownership flag"),
    (0x9456A0, "reads and writes the basic_ios state word at +0x20 and throws through 0x97A7B0; its own literal names 'basic_ios::clear'"),
    (0x9445E0, "installs a vtable from the image, releases the member string at +0xc8 and hands +0xd0 to the shared_ptr release: a destructor"),
    (0x87F2A0, "installs a vtable, releases the members at +0x48 and +0x38 and hands +0xd0 to the shared_ptr release: the same destructor shape"),
    (0x9454D0, "calls 0x944160 and 0x945370 then stores the stream state at +0x20 and the buffer at +0xe8: the basic_ios initialisation"),
    (0x944160, "stores 6, 0 and 0x1002 at +8, +0x10 and +0x18 and moves a shared_ptr at +0xd0: the basic_streambuf header"),
    (0x944530, "fills the vtable-relative members and clears the two flags: part of the basic_ios construction"),
    (0x945370, "fills the eight facet pointers of a basic_ios from a locale and tests each: part of the same construction"),
    (0x990540, "looks a facet up in the locale cache, dynamic casts it through 0x9990E0 and throws when it fails: a facet accessor"),
    (0x990840, "the same facet accessor for another typeinfo"),
    (0x990780, "the same facet accessor for another typeinfo"),
    (0x9916E0, "the same facet accessor, throwing through 0x978750 and 0x998920"),
    (0x991920, "the same facet accessor for another typeinfo"),
    (0x9919E0, "the same facet accessor for another typeinfo"),
    (0x9990E0, "reads the virtual base at [rcx - 0x10], compares the typeinfo at [rax - 8] and calls the virtual function at 0x38 or 0x40: a dynamic cast to a facet type"),
    (0x88B6F0, "stores three vtable addresses from the image and calls 0x945370, 0x9454D0, 0x87EDF0 and 0x87D590: the stream object construction"),
    (0x978010, "reads the stream state, then calls the vtable entry at +0x68 or +0x60 and fills or pads the buffer: the ostream write"),
    (0x9878C0, "hands a pointer and a length to 0x978010: the ostream string overload"),
    (0x867BF0, "tests the sentry, writes one character through the buffer at +0xe8 and calls the vtable entry at +0x30: the single character write"),
    (0x8682A0, "tests the stream state against the 0x1002 write mode and sets the sentry result: the ostream sentry"),
    (0x868380, "the input sentry, the same shape without the write mode test"),
    (0x867DF0, "flushes the buffer when the state demands it: the stream flush"),
    (0x87D590, "calls 0x822590, 0x877160 and 0x822590 then sets the buffer pointers: the filebuf open"),
    (0x87D8E0, "calls 0x822590, 0x87D270 and 0x87D4E0 and clears the members: the filebuf close"),
    (0x87D270, "clears a member and returns whether a byte is available: the buffer underflow helper"),
    (0x87EDF0, "stores a vtable from the image, initialises the members and calls 0x8AAB00 and 0x8774E0: a constructor of the stream family"),
    (0x877160, "calls 0x65C810 for the mode string and 0x630FD0 to open, storing the handle at +0 and the flag at +8: the fopen wrapper"),
    (0x630110, "converts the character through 0x63F508 and 0x62FF90 with the default buffer: the widen-then-convert character path"),
    (0x8264E0, "zeroes 0x100 bytes on the stack, calls 0x63F2F8 and 0x63F300 on it and stores 1 then 2 at +0x38: the string comparison buffer"),
    (0x89EC90, "forwards to 0x89EBA0, the ctype<char> initialiser"),
    (0x8894B0, "forwards to 0x889D00, the member initialiser of the same family"),
    (0x531F20, "reads the pointer at +0, frees the member at +8 through 0x530010 and frees the object: a destructor"),
]

CATEGORY_NOTE = """
## What the LaunchLocalComputation closure actually contains, and the counting rule (round 526)

Batch eight read the twenty four functions the entry point calls directly. Not one of them is an algorithm: they are
libstdc++'s iostreams, its locale facet accessors, its shared_ptr reference counting and a handful of destructors. The
evidence is recorded next to each address in `re/g_toolchain.py`, and the shape of it is worth stating because it decides
how the rest of this objective should be counted:

* The whole `0x63xxxx` block of the closure is the numeric and locale layer, and the `0x8Axxxx`/`0x90Exxx`/`0x921xxx`/
  `0x922xxx`/`0x944xxx`/`0x945xxx` block is the iostreams and the locale's facet caches. `0x8A82F0` is
  `std::locale::_S_initialize`, which installs every facet there is, and that is why one call reaches twelve hundred
  functions: it is not a domain dependency chain, it is the standard library's own construction.
* `0x2AB0` itself is orchestration over those objects. It builds an input file stream over `c:\\Temp\\cns.pb.json` (the
  stream construction at 0x2BB6 to 0x2C92 calls exactly the four functions batch eight classified), writes '-> ' and
  'LaunchLocalComputation' into an output stream, writes the double argument, and at the end reads two configuration strings,
  `cns_force_cloud` and the server list `cns1.optalog.com;cns2.optalog.com`, plus the debug marker
  `// LaunchLocalComputation`.

So the honest way to finish this objective is NOT to write reimplementations of `basic_ios::clear` or a facet accessor:
those already exist in the standard library this project links against, and reimplementing them would add code without
adding recovered behaviour. `forwardedCount` is a count of *recovered domain behaviour*, and the rule that keeps it honest
is the one this project already uses for the platform-forwarding class: code whose work is done by the standard library or
by the platform is classified, recorded, and not counted as progress.

What is left of the closure after batch eight is the orchestration at 0x2AB0, the two wrappers, and the domain routines
that touch this module's own objects -- among them `0x1BF40` (the engine fetch, whose own literal is
`c:\\Temp\\debug_nest.txt`), `0x22A20`, `0x65A530` (which opens the three log files `log_nest.txt`, `cloud_nest.txt` and
`local_nest.txt` and records three success flags) and `0x7BB430` (whose literal is `CNS informations`). Those are the
functions the orchestration is about, and they are what the next batches read.
"""


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    s = read(TOOLCHAIN)
    a = "    0x63F170,  # word by word scan of a string, the strcmp family"
    assert a in s, "the g_toolchain anchor line is gone"
    added = []
    for rva, reason in LIBRARY:
        if "0x%X," % rva in s:
            print("    0x%X is already classified, skipped" % rva)
            continue
        added.append((rva, reason))
    lines = [a] + ["    0x%X,  # %s" % (rva, reason) for rva, reason in added]
    write(TOOLCHAIN, s.replace(a, "\n".join(lines), 1))
    print("g_toolchain.py  %d functions classified as library" % len(added))

    c = read(CATEGORIES)
    write(CATEGORIES, c.rstrip("\n") + "\n" + CATEGORY_NOTE)
    print("CATEGORIES.md   the round 526 section")
    print("done")


if __name__ == "__main__":
    main()
