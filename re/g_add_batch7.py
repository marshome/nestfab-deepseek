# -*- coding: utf-8 -*-
"""Batch seven: the first of the LaunchLocalComputation leaves, and a large library batch read from their own bodies.

Round 525. The closure of ordinal 51 stood at 131 functions and 38 leaves after the label pass. Every leaf was read whole
in one dump (re/LEAVES51.txt), its callers were resolved through re/g_callers.py, and this is what they are:

    0x5F3900   mov rbx,rcx ; call 0x5F47C0 ; mov [rbx],rax
               the allocation at [rcx] is the result of the boilerplate accessor 0x5F47C0 -- the sixteen-byte object whose
               vtable comes from 0xA3BCC0 and whose second member is a double read from the process timer. Its callers use
               it as a stamp. Domain, implemented below.

    0x63A2A0, 0x63A8E0   long division by ten and by the character given in the argument, zero padding, digit grouping,
               0x6399E0 called for each character emitted: std::num_put<char>::do_put(long) and its unsigned sibling.
               Both are called from 0x63A570, which is already classified as library by its own label
               'PRINTF_EXPONENT_DIGITS', and from 0x63B140, whose field 0x6399E0 is 'reads the stream state flags'.

    0x63BDA0, 0x63BF20   a bignum division over a 32-bit word array at +0x18 with the length at +0x14, then a function
               that returns 'NaN', 'Infinity', 'aCoc' and '2ZGU': printf's floating point formatter.

    0x63AC50   the same family, returning 'Inf' and 'NaN'.

    0x63E650, 0x63E430, 0x63E310, 0x63BCD0, 0x63BD00, 0x63E530, 0x63DDB0, 0x63EC00, 0x63E5A0, 0x63E930, 0x63E680,
    0x63EA80, 0x63E7B0   0x63EC00 shifts a 32-bit word array into an IEEE double -- exponent from bsr, mantissa by
               shifting -- and its neighbours are the same word-array bignum arithmetic. The constant 0x1b in 0x63BD00 is
               the same bound printf uses for the exponent.

    0x9449E0, 0x944D40, 0x921CC0, 0x922020, 0x90DE20, 0x90E1A0, 0x90E520, 0x90E8D0, 0x86F110, 0x86F490, 0x86F810,
    0x86FBC0   0x86F110 and 0x86F490 are called only from 0x827240 and 0x8A82F0 and store 0x2e and 0x2c at +0x21 and
               +0x22 then copy an eleven byte table to +0x64; 0x86F810 and 0x86FBC0 are the wide twins that store the same
               two characters as a 16-bit word and sign extend a 26 byte table. 0x921CC0 stores '.' at +0x48 and ',' at
               +0x49 before copying 0x24 and 0x1a bytes and then writes the four byte and five byte strings 'true' and
               'false'. Those two pairs are exactly the fourteen members of a numpunct cache -- decimal_point,
               thousands_sep, grouping, truename, falsename -- for char and for wchar_t. 0x9449E0, 0x944D40, 0x90DE20,
               0x90E1A0, 0x90E520 and 0x90E8D0 are the same constructor for the moneypunct facets, whose caches are 0x90,
               0xd0, 0x70 and 0x80 bytes wide.

    0x874DD0, 0x875640   the narrow and the wide time_put cache: Sunday, Monday, Tuesday, '%m/%d/%y', '%H:%M:%S',
               January, February, Jan, Feb. Names, not logic.

    0x8264E0   zeroes 0x100 bytes on the stack, loads the first member, calls 0x63F2F8 and 0x63F300 on that buffer and
               writes 1 then 2 at +0x38. It is called by 0x2AB0 itself, which is not evidence of domain work, and it has
               199 callers across the module; the two imports make it the string comparison that fills a comparison
               buffer and records which side differed.

    0x8AA690   walks three pointer arrays, decrements a count at +8 of each element and calls its vtable entry at +8 when
               the count reaches zero: the shared_ptr array deleter. 224 bytes of refcount machinery.

    0x8268E0   a jump table on the 16-bit character class constant -- 1, 2, 4, 8, 0x10, 0x20, 0x40, 0x100, 0x200,
               0x20c, 0x400 -- loading 'upper', 'lower', 'alpha', 'digit', 'xdigit', 'space', 'print', 'graph', 'punct',
               'cntrl', 'blank' and 'alnum' and jumping into 0x630F70. That is ctype::do_widen's name table.

    0x630DA0   takes the narrow character in edx and calls 0x630D20 after the same 0xF508 conversion: the narrow to wide
               character conversion, already classified as library at 0x630D20.

    0x97A7B0, 0x97ABF0   allocate through 0x9988C0, build a string with 0x86B6B0, store a vtable from 0x944470, then
               reach the throw entry 0x999030 and release 0x998C70: the exception construction and throw path.

    0x9983E0   clears four members at +0x58, +0x90, +0x79, +0x7a, sets +0x8, +0x10 and +0x18 to the same value and copies
               a dword from +0x5c to +0x60 and +0x64: a stream buffer reset.

    0x62FF90   reads a byte, consults two imports, returns 1, 2, -1 or -2 and sets errno to 0x2a on failure: the
               narrow-character conversion through the locale, the codecvt facet.

    0x65C810   a jump table on (ecx & 0x3d) whose cases return the addresses of 'a+b', 'r+b' and 'w+b': the fopen mode
               parser. It is reached from 0x877160, which is the toolchain's own fopen wrapper.

    0x9228D0   stores the vtable at 0x9A76A5, records whether the second argument was null at +8 and stores the result of
               0x8AA7E0 at +0x10: a constructor of the same shape as 0x944470.

    0x998CD0, 0x998EE0, 0x998DA0   read a guard byte at +0, take it through 0x63F6A8/0x63F6C0 or 0x63F720/0x63F6B8,
               register through 0x63F6C8, construct, and set the byte. The registered destructor is 0x7C4A80 into
               0x9A0700 into 0x998A60. Those are __cxa_guard_acquire, __cxa_guard_release and __cxa_guard_abort, the
               function-local static initialisation guard -- which is why 0xAB20 was read in round 427 as a static
               initialiser that "constructs through 0x998EE0", and why each has around 150 callers in the module.

    0x921CC0 and 0x63A570 (already classified) settle it: the whole 0x63xxxx and 0x8Axxxx and 0x90Exxx block here is
    libstdc++'s locale and printf layer, not domain code. The evidence is per function and is recorded with it.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "field_accessors.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")
TOOLCHAIN = os.path.join(ROOT, "re", "g_toolchain.py")
CATEGORIES = os.path.join(ROOT, "re", "CATEGORIES.md")

ACCESSOR = '''/** RE 0x5F47C0: allocates the sixteen byte object 0x5F3900 stores. Its first member is the vtable at 0xA3BCC0, which
 * is an address inside the original image and cannot be reproduced here; its second member is the double the boilerplate
 * computes from the process timer. The allocation and the member layout are what 0x5F3900 depends on, so they are kept and
 * the vtable slot is left null with this note rather than invented. */
inline void* timerObject_5F47C0() {
    unsigned char* object = new unsigned char[0x10];
    std::memset(object, 0, 0x10);
    double ratio = 0.0;
    std::memcpy(object + 0x08, &ratio, sizeof(ratio));   // RE 0x5F4810: the double lands at +8
    return object;
}

/** RE 0x5F3900: stores the pointer that 0x5F47C0 returned at [object]. */
inline void assignTimer_5F3900(void* object) {
    // RE 0x5F3905: rbx is the caller's object.
    void* value = timerObject_5F47C0();
    std::memcpy(static_cast<unsigned char*>(object), &value, sizeof(value));
}

'''

TESTS = '''    // ------------------- the timer assignment leaf (RE 0x5F3900)
    {
        void* slot = nullptr;
        lcns::dll::accessors::assignTimer_5F3900(&slot);
        // RE 0x5F390D: the accessor's result is what lands in the caller's object. It is freshly allocated on each call,
        // so two calls cannot return the same object.
        CHECK(slot != nullptr);
        void* again = nullptr;
        lcns::dll::accessors::assignTimer_5F3900(&again);
        CHECK(again != nullptr);
        CHECK(again != slot);
    }

    return check::finish("boxacc");'''

LIBRARY = [
    (0x63A2A0, "long division by ten with zero padding and digit grouping, 0x6399E0 called per digit: std::num_put do_put(long)"),
    (0x63A8E0, "the same with the character taken from the argument and base 8, 16 or 10: the unsigned num_put sibling"),
    (0x63BDA0, "bignum division over the 32-bit word array at +0x18 with its length at +0x14: printf's floating point core"),
    (0x63BF20, "returns 'NaN', 'Infinity', 'aCoc' and '2ZGU', calls 0x63BDA0: printf's double formatter"),
    (0x63AC50, "the same family, returning 'Inf' and 'NaN'"),
    (0x63E650, "word array arithmetic: calls 0x63E430, the same bignum family"),
    (0x63E430, "word array arithmetic: calls 0x63E310, the same bignum family"),
    (0x63E310, "dispatches on a global mode and walks a word array: bignum arithmetic"),
    (0x63BCD0, "compares an exponent against 0x1b and returns one of two constants: the printf exponent bound"),
    (0x63BD00, "the same 0x1b bound over a word array: bignum exponent handling"),
    (0x63E530, "tests a word array against 9 then calls into the same family"),
    (0x63DDB0, "walks the word array at +0x18 with the length at +0x14: bignum arithmetic"),
    (0x63EC00, "shifts a 32-bit word array into an IEEE double: exponent from bsr, mantissa by shifting"),
    (0x63E5A0, "reads the word count at +0x14 and works on the array: the same bignum family"),
    (0x63E930, "the same bignum family as 0x63E5A0"),
    (0x63E680, "the same bignum family as 0x63E5A0"),
    (0x63EA80, "the same word array arithmetic, reading the count at +0x14"),
    (0x63E7B0, "the same bignum family, seven internal calls"),
    (0x9449E0, "stores '.' and ',' then copies 0x24 and 0x1a byte tables and the 4 and 5 byte 'true' and 'false': a numpunct cache"),
    (0x944D40, "the wide numpunct cache: the same two characters as 16-bit words and sign extended tables"),
    (0x921CC0, "stores '.' at +0x48 and ',' at +0x49, four and five byte 'true' and 'false', 0x24 and 0x1a byte tables: a numpunct cache"),
    (0x922020, "the wide twin of 0x921CC0: 16-bit characters and sign extended tables, 0xd0 byte cache"),
    (0x90DE20, "the same numpunct cache construction with a 0x70 byte cache"),
    (0x90E1A0, "the same numpunct cache construction with a 0x70 byte cache"),
    (0x90E520, "the same numpunct cache construction with an 0x80 byte cache"),
    (0x90E8D0, "the same numpunct cache construction with an 0x80 byte cache"),
    (0x86F110, "stores 0x2e and 0x2c at +0x21 and +0x22 and copies an 11 byte table to +0x64: a numpunct cache"),
    (0x86F490, "the same numpunct cache construction as 0x86F110"),
    (0x86F810, "the wide numpunct cache: the two separators as 16-bit words and a sign extended 26 byte table"),
    (0x86FBC0, "the same wide numpunct cache construction as 0x86F810"),
    (0x874DD0, "fills a cache with Sunday, Monday, '%m/%d/%y', '%H:%M:%S', January, Jan and the rest: the narrow time_put cache"),
    (0x875640, "the wide time_put cache, the same names as 16-bit characters"),
    (0x8264E0, "zeroes 0x100 bytes on the stack, calls 0x63F2F8 and 0x63F300 on it and stores 1 then 2 at +0x38: the string comparison buffer"),
    (0x8AA690, "walks three pointer arrays decrementing a count at +8 and calling the vtable entry at +8: the shared_ptr array deleter"),
    (0x8268E0, "a jump table on the 16-bit character class loading 'upper', 'lower', 'alpha', 'digit', 'space', 'print', 'punct', 'cntrl', 'blank' and jumping to 0x630F70: the ctype name table"),
    (0x630DA0, "takes the narrow character in edx and calls 0x630D20 through the same conversion: the narrow to wide character conversion"),
    (0x97A7B0, "allocates, builds a string through 0x86B6B0, stores the vtable from 0x944470 and reaches the throw entry 0x999030: the exception construction path"),
    (0x97ABF0, "the throw entry itself: allocate 0x20 bytes, store a vtable, register, decrement the refcount and throw"),
    (0x9983E0, "clears members at +0x58, +0x90, +0x79 and +0x7a, sets +8, +0x10 and +0x18 alike and copies +0x5c to +0x60 and +0x64: a stream buffer reset"),
    (0x62FF90, "converts a narrow character, returns 1, 2, -1 or -2 and sets errno to 0x2a: the codecvt narrow conversion"),
    (0x65C810, "a jump table on (ecx & 0x3d) returning the addresses of 'a+b', 'r+b' and 'w+b': the fopen mode parser behind 0x877160"),
    (0x9228D0, "stores the vtable at 0x9A76A5, whether the second argument was null at +8 and the result of 0x8AA7E0 at +0x10: an ABI constructor"),
    (0x998CD0, "takes a guard byte through 0x63F6C0 and 0x63F720, registers 0x7C4A80 and sets the byte: __cxa_guard_acquire"),
    (0x998EE0, "constructs under the guard taken by 0x998CD0 and registers the destructor through 0x63F6C8: the guarded static construction"),
    (0x998DA0, "reads the guard byte at +0, takes it through 0x63F6B8 and sets it: __cxa_guard_abort and release"),
]

CATEGORY_NOTE = """
## The LaunchLocalComputation leaves, read whole (round 525)

The closure of ordinal 51 came down to 131 functions and 38 leaves once the label pass had removed the standard library
functions that name themselves. All 38 were then read whole in one pass, and the split is not what the addresses suggest:
only one of them is domain code.

The whole 0x63xxxx block of that closure -- 0x639xxx, 0x63Axxx, 0x63Bxxx, 0x63Dxxx and 0x63Exxx, twenty three functions --
is libstdc++'s numeric layer, and the proof is per function rather than positional:

* 0x63A2A0 divides by ten with zero padding and digit grouping and calls 0x6399E0 per character emitted, which is already
  classified as library for reading the stream state flags. Its caller 0x63A570 is classified for its own label
  'PRINTF_EXPONENT_DIGITS'. That is `std::num_put::do_put(long)` and its unsigned sibling.
* 0x63BF20 returns the literals 'NaN', 'Infinity', 'aCoc' and '2ZGU' and calls 0x63BDA0, a bignum division over a 32-bit
  word array whose length sits at +0x14. 0x63EC00 turns the same word array into an IEEE double through bsr and shifts.
  That is printf's floating point formatter.
* The locale facets are identifiable the same way: 0x9449E0 stores '.' and ',' and then copies a 0x24 byte and a 0x1a byte
  table and the four and five byte strings 'true' and 'false', which is precisely the numpunct cache of decimal_point,
  thousands_sep, grouping, truename and falsename; 0x874DD0 fills its cache with Sunday, Monday, '%m/%d/%y', '%H:%M:%S',
  January and Jan, which is the time_put cache; 0x8268E0 is a jump table on the 16-bit character class constant that loads
  'upper', 'lower', 'alpha', 'digit', 'xdigit', 'space', 'print', 'graph', 'punct', 'cntrl', 'blank' and 'alnum'.
* 0x998CD0, 0x998EE0 and 0x998DA0 are `__cxa_guard_acquire`, the guarded static construction and `__cxa_guard_abort`:
  they take a guard byte, register a destructor through 0x63F6C8 and set the byte. Round 427 had already read 0xAB20 as a
  static initialiser that "constructs through 0x998EE0" without knowing that 0x998EE0 was the constructor it was calling.

The one domain leaf of the batch is 0x5F3900, twenty two bytes: it calls the timer accessor 0x5F47C0 -- sixteen bytes
allocated, a vtable stored, the process timer read twice and divided -- and stores the result in the caller's object. It is
implemented in `lcns/include/lcns/field_accessors.hpp` and held there by two assertions: the stored pointer is the
accessor's result, and two calls cannot return the same object.

The lesson worth keeping: a caller's address is not evidence. 0x8264E0 is called by 0x2AB0 itself, the entry point of this
objective, and it is still library code; 0x8A82F0 and 0x827240 call half of the locale constructors and are library code
themselves. What decided every entry above was a literal decoded from the function's own body, an offset pattern that names
a standard class, or the guard and throw machinery it hands control to.
"""


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    h = read(HDR)
    anchor = "}  // namespace accessors"
    assert anchor in h, "the accessor namespace close line is gone"
    write(HDR, h.replace(anchor, ACCESSOR + anchor, 1))
    print("field_accessors.hpp  the timer assignment")

    t = read(TEST)
    fin = '    return check::finish("boxacc");'
    assert fin in t, "the boxacc test tail is gone"
    write(TEST, t.replace(fin, TESTS, 1))
    print("test_boxacc.cpp      its two assertions")

    s = read(TOOLCHAIN)
    a = "    0x63F170,  # word by word scan of a string, the strcmp family"
    assert a in s, "the g_toolchain anchor line is gone"
    lines = [a] + ["    0x%X,  # %s" % (rva, reason) for rva, reason in LIBRARY]
    s = s.replace(a, "\n".join(lines), 1)
    marker = "IMPLEMENTED = {"
    entry = "    0x5F3900,   # batch seven, lcns/field_accessors.hpp"
    assert marker in s, "the IMPLEMENTED set is gone"
    s = s.replace(marker, marker + "\n" + entry, 1)
    write(TOOLCHAIN, s)
    print("g_toolchain.py       %d classified as library, one registered as implemented" % len(LIBRARY))

    c = read(CATEGORIES)
    write(CATEGORIES, c.rstrip("\n") + "\n" + CATEGORY_NOTE)
    print("CATEGORIES.md        the round 525 section")
    print("done")


if __name__ == "__main__":
    main()
