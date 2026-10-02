# -*- coding: utf-8 -*-
"""Which unimplemented exports still depend on REAL domain code, once the measured boilerplate is set aside.

The BOILERPLATE set below is not guessed. Every address in it was read whole and identified in an earlier round:

  0x9984B0  a five-byte jmp into the import stub bank, 5721 callers -- a deallocation wrapper
  0x998500  109 bytes, 2317 callers -- operator new, with the null-to-one fix and the new_handler retry
  0x62F280  171 bytes -- reaches the platform through the IAT; builds an "CCG " tagged argument block
  0x64AEA0  403 bytes -- the logger; round 369 showed it tests a global switch and returns when it is off
  0xAB20    98 bytes -- compiler-generated initialisation of a function-local static
  0x978750  51 bytes -- an allocation plus vtable store plus constructor call wrapper
  0x97ABF0  183 bytes -- the exception throw machinery: allocate, refcount, vtable, throw

Everything else that a function's own instructions show as toolchain, diagnostic or unknown is handled by kind() below.
An address in neither VERIFIED nor BOILERPLATE nor one of those kinds counts as domain, which is what must be read.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L  # noqa: E402
from lib import disasm, load_prof  # noqa: E402

BOILERPLATE = {
    0x9984B0,  # deallocation thunk into the import stub bank
    0x998500,  # operator new
    0x62F280,  # platform stub through the IAT
    0x64AEA0,  # the logger, no effect on its default path
    0xAB20,    # static initialisation boilerplate
    0x978750,  # allocation and constructor wrapper
    0x62F000,  # RE round 501: xor eax,eax; ret -- the default empty implementation
    0x62F010,  # two-level pointer fetch
    0x963560,  # global singleton accessor
    0x962F10,  # global singleton accessor
    0x998CB0,  # tail call into the runtime
    0x6562A0,  # throw helper
    0x990E80,  # fetch a global then call the throw helper
    0x62F380,  # virtual dispatch trampoline
    0x62F330,  # runtime initialisation guard
    0x656260,  # exception format and throw machinery
    0x998FE0,  # reference count and canary guard
    0x653130,  # virtual call with a stack cookie
    0x653300,  # same family as 0x653130
    0x653280,  # same family as 0x653130
    0x6530A0,  # same family as 0x653130
    0x998BC0,  # runtime string or exception helper
    0x9989A0,  # runtime string or exception helper
    0x999030,  # runtime throw entry
    0x89A730,  # eight bytes: lea rax,[rip+..] ; ret -- returns a static object address
    0x86A2C0,  # atomic decrement of [rcx+0x10] and delete when it reaches zero: refcount release
    0x877B20,  # installs a vtable taken from a global plus 0x10
    0x998C70,  # allocator size class dispatch between two globals
    0x875EB0,  # installs a vtable then initialises a member string
    0x86B6B0,  # std::string range constructor using the strlen stub
    0x9988C0,  # allocator with a 0xA0 byte header, zeroed, returns past the header
    0x97AB50,  # allocates, installs a vtable, throws, then releases
    0x998A60,  # runtime allocation family (restored: an earlier patch dropped the anchor line it replaced)
    0x7C4A80,  # allocates eight bytes, stores a vtable and calls the throw entry (restored for the same reason)
    0x910C20,  # std::string internal: data, length and small buffer, calls the growth routine
    0x62DBE0,  # four bytes: mov rax,rcx ; ret -- returns the first argument
    0x62DBF0,  # four bytes: mov rax,rcx ; ret -- the same identity
    0x62EFC0,  # vector subscript: base at [rdx+8] plus a 32-bit index taken through [rdx+0x10]
    0x86B750,  # shared_ptr copy: loads the control block and increments its count atomically
    0x86A370,  # container growth: base plus requested size, doubling policy
    0x86A3E0,  # container growth: clamps against 0x3FFFFFFFFFFFFFF9 and doubles
    0x653190,  # container helper built on the vector subscript above
    0x6533B0,  # jump table dispatch on a low nibble: a library character or format classifier
    0x97A6D0,  # reads a field of a runtime global and returns whether it is non zero
    0x62D860,  # calls 0x62D7B0 then returns minus one when the result is zero
    0x60C5A0,  # container size: distance from an inline buffer plus a stored count
    0x875F50,  # copy constructor: installs a vtable then copies a shared_ptr member
    0x877A20,  # derived copy constructor: vtable plus a string member
    0x875FD0,  # destructor: installs a vtable, decrements a refcount, releases when it reaches zero
    0x8760F0,  # destructor thunk: installs a vtable then jumps into the release path
    0x876040,  # derived copy constructor: calls 0x888F50 then installs a vtable
    0x877AD0,  # destructor thunk for the same family as 0x875FD0
    0xB5D60,  # xor eax, eax ; ret -- a default override returning zero
    0x6FC810,  # xor eax, eax ; ret -- a default override returning zero
    0xD5970,  # xor eax, eax ; ret -- a default override returning zero
    0xD59A0,  # xor eax, eax ; ret -- a default override returning zero
    0x5F3960,  # loads a member and makes a virtual call through its vtable: dispatch, not domain logic
    0x826C60,  # atomic increment of a global then stores the new value: an id or refcount generator
    0x8AA7E0,  # hands two rip literals to an import stub and returns a global: runtime initialisation
    0x63F170,  # word by word scan of a string, the strcmp family
    0x63A1C0,  # loads an 80-bit long double and reads a count from the second argument, then pads through 0x6399E0: a num_put overload
    0x63A6A0,  # the same prologue as 0x63A1C0: another num_put overload
    0x63A750,  # the same prologue as 0x63A1C0 at 390 bytes: the long double overload
    0x6398E0,  # reads the 0x7fff exponent mask of an 80-bit long double, classifies zero, infinity and NaN, and calls 0x63BF20
    0x639B50,  # pads and adjusts through 0x6399E0 using the stream width at +0xc: part of the num_put formatting
    0x639CA0,  # the same padding path, storing 0xffffffff as the width
    0x639C50,  # stores the '(null)' literal when the string argument is null: the num_put null string path
    0x639D40,  # the same family, emitting through 0x6399E0
    0x639A40,  # emits a wide character array through 0x630DA0 and 0x6399E0 with the same width padding
    0x639E30,  # reads the same stream fields and reaches three of the above: the same num_put layer
    0x63B140,  # reads the stream state words, dispatches on the format flags and reaches eleven num_put functions: the num_put entry point
    0x63BD80,  # shifts 1 left by the word count at [rcx - 4] and jumps to 0x63E530: the bignum normalisation
    0x8AABC0,  # atomically decrements the count the first member points at and calls 0x8AA690 then frees: the shared_ptr release
    0x8AABF0,  # increments one shared_ptr count, decrements the count at the destination and stores: the shared_ptr assignment
    0x8761B0,  # frees the pointer at +0 through 0x63F6B8 when the flag at +8 is set, else throws through 0x97ABF0: the string dispose with its ownership flag
    0x9456A0,  # reads and writes the basic_ios state word at +0x20 and throws through 0x97A7B0; its own literal names 'basic_ios::clear'
    0x9445E0,  # installs a vtable from the image, releases the member string at +0xc8 and hands +0xd0 to the shared_ptr release: a destructor
    0x87F2A0,  # installs a vtable, releases the members at +0x48 and +0x38 and hands +0xd0 to the shared_ptr release: the same destructor shape
    0x9454D0,  # calls 0x944160 and 0x945370 then stores the stream state at +0x20 and the buffer at +0xe8: the basic_ios initialisation
    0x944160,  # stores 6, 0 and 0x1002 at +8, +0x10 and +0x18 and moves a shared_ptr at +0xd0: the basic_streambuf header
    0x944530,  # fills the vtable-relative members and clears the two flags: part of the basic_ios construction
    0x945370,  # fills the eight facet pointers of a basic_ios from a locale and tests each: part of the same construction
    0x990540,  # looks a facet up in the locale cache, dynamic casts it through 0x9990E0 and throws when it fails: a facet accessor
    0x990840,  # the same facet accessor for another typeinfo
    0x990780,  # the same facet accessor for another typeinfo
    0x9916E0,  # the same facet accessor, throwing through 0x978750 and 0x998920
    0x991920,  # the same facet accessor for another typeinfo
    0x9919E0,  # the same facet accessor for another typeinfo
    0x9990E0,  # reads the virtual base at [rcx - 0x10], compares the typeinfo at [rax - 8] and calls the virtual function at 0x38 or 0x40: a dynamic cast to a facet type
    0x88B6F0,  # stores three vtable addresses from the image and calls 0x945370, 0x9454D0, 0x87EDF0 and 0x87D590: the stream object construction
    0x978010,  # reads the stream state, then calls the vtable entry at +0x68 or +0x60 and fills or pads the buffer: the ostream write
    0x9878C0,  # hands a pointer and a length to 0x978010: the ostream string overload
    0x867BF0,  # tests the sentry, writes one character through the buffer at +0xe8 and calls the vtable entry at +0x30: the single character write
    0x8682A0,  # tests the stream state against the 0x1002 write mode and sets the sentry result: the ostream sentry
    0x868380,  # the input sentry, the same shape without the write mode test
    0x867DF0,  # flushes the buffer when the state demands it: the stream flush
    0x87D590,  # calls 0x822590, 0x877160 and 0x822590 then sets the buffer pointers: the filebuf open
    0x87D8E0,  # calls 0x822590, 0x87D270 and 0x87D4E0 and clears the members: the filebuf close
    0x87D270,  # clears a member and returns whether a byte is available: the buffer underflow helper
    0x87EDF0,  # stores a vtable from the image, initialises the members and calls 0x8AAB00 and 0x8774E0: a constructor of the stream family
    0x877160,  # calls 0x65C810 for the mode string and 0x630FD0 to open, storing the handle at +0 and the flag at +8: the fopen wrapper
    0x630110,  # converts the character through 0x63F508 and 0x62FF90 with the default buffer: the widen-then-convert character path
    0x89EC90,  # forwards to 0x89EBA0, the ctype<char> initialiser
    0x8894B0,  # forwards to 0x889D00, the member initialiser of the same family
    0x531F20,  # reads the pointer at +0, frees the member at +8 through 0x530010 and frees the object: a destructor
    0x63A2A0,  # long division by ten with zero padding and digit grouping, 0x6399E0 called per digit: std::num_put do_put(long)
    0x63A8E0,  # the same with the character taken from the argument and base 8, 16 or 10: the unsigned num_put sibling
    0x63BDA0,  # bignum division over the 32-bit word array at +0x18 with its length at +0x14: printf's floating point core
    0x63BF20,  # returns 'NaN', 'Infinity', 'aCoc' and '2ZGU', calls 0x63BDA0: printf's double formatter
    0x63AC50,  # the same family, returning 'Inf' and 'NaN'
    0x63E650,  # word array arithmetic: calls 0x63E430, the same bignum family
    0x63E430,  # word array arithmetic: calls 0x63E310, the same bignum family
    0x63E310,  # dispatches on a global mode and walks a word array: bignum arithmetic
    0x63BCD0,  # compares an exponent against 0x1b and returns one of two constants: the printf exponent bound
    0x63BD00,  # the same 0x1b bound over a word array: bignum exponent handling
    0x63E530,  # tests a word array against 9 then calls into the same family
    0x63DDB0,  # walks the word array at +0x18 with the length at +0x14: bignum arithmetic
    0x63EC00,  # shifts a 32-bit word array into an IEEE double: exponent from bsr, mantissa by shifting
    0x63E5A0,  # reads the word count at +0x14 and works on the array: the same bignum family
    0x63E930,  # the same bignum family as 0x63E5A0
    0x63E680,  # the same bignum family as 0x63E5A0
    0x63EA80,  # the same word array arithmetic, reading the count at +0x14
    0x63E7B0,  # the same bignum family, seven internal calls
    0x9449E0,  # stores '.' and ',' then copies 0x24 and 0x1a byte tables and the 4 and 5 byte 'true' and 'false': a numpunct cache
    0x944D40,  # the wide numpunct cache: the same two characters as 16-bit words and sign extended tables
    0x921CC0,  # stores '.' at +0x48 and ',' at +0x49, four and five byte 'true' and 'false', 0x24 and 0x1a byte tables: a numpunct cache
    0x922020,  # the wide twin of 0x921CC0: 16-bit characters and sign extended tables, 0xd0 byte cache
    0x90DE20,  # the same numpunct cache construction with a 0x70 byte cache
    0x90E1A0,  # the same numpunct cache construction with a 0x70 byte cache
    0x90E520,  # the same numpunct cache construction with an 0x80 byte cache
    0x90E8D0,  # the same numpunct cache construction with an 0x80 byte cache
    0x86F110,  # stores 0x2e and 0x2c at +0x21 and +0x22 and copies an 11 byte table to +0x64: a numpunct cache
    0x86F490,  # the same numpunct cache construction as 0x86F110
    0x86F810,  # the wide numpunct cache: the two separators as 16-bit words and a sign extended 26 byte table
    0x86FBC0,  # the same wide numpunct cache construction as 0x86F810
    0x874DD0,  # fills a cache with Sunday, Monday, '%m/%d/%y', '%H:%M:%S', January, Jan and the rest: the narrow time_put cache
    0x875640,  # the wide time_put cache, the same names as 16-bit characters
    0x8264E0,  # zeroes 0x100 bytes on the stack, calls 0x63F2F8 and 0x63F300 on it and stores 1 then 2 at +0x38: the string comparison buffer
    0x8AA690,  # walks three pointer arrays decrementing a count at +8 and calling the vtable entry at +8: the shared_ptr array deleter
    0x8268E0,  # a jump table on the 16-bit character class loading 'upper', 'lower', 'alpha', 'digit', 'space', 'print', 'punct', 'cntrl', 'blank' and jumping to 0x630F70: the ctype name table
    0x630DA0,  # takes the narrow character in edx and calls 0x630D20 through the same conversion: the narrow to wide character conversion
    0x97A7B0,  # allocates, builds a string through 0x86B6B0, stores the vtable from 0x944470 and reaches the throw entry 0x999030: the exception construction path
    0x97ABF0,  # the throw entry itself: allocate 0x20 bytes, store a vtable, register, decrement the refcount and throw
    0x9983E0,  # clears members at +0x58, +0x90, +0x79 and +0x7a, sets +8, +0x10 and +0x18 alike and copies +0x5c to +0x60 and +0x64: a stream buffer reset
    0x62FF90,  # converts a narrow character, returns 1, 2, -1 or -2 and sets errno to 0x2a: the codecvt narrow conversion
    0x65C810,  # a jump table on (ecx & 0x3d) returning the addresses of 'a+b', 'r+b' and 'w+b': the fopen mode parser behind 0x877160
    0x9228D0,  # stores the vtable at 0x9A76A5, whether the second argument was null at +8 and the result of 0x8AA7E0 at +0x10: an ABI constructor
    0x998CD0,  # takes a guard byte through 0x63F6C0 and 0x63F720, registers 0x7C4A80 and sets the byte: __cxa_guard_acquire
    0x998EE0,  # constructs under the guard taken by 0x998CD0 and registers the destructor through 0x63F6C8: the guarded static construction
    0x998DA0,  # reads the guard byte at +0, takes it through 0x63F6B8 and sets it: __cxa_guard_abort and release
    0x65C940,  # loads a global and calls a library routine with the caller arguments
    0x87D4E0,  # frees the member at +0x68 when the flag at +0x78 is set: conditional destruction
    0x5F47C0,  # allocates sixteen bytes, stores a vtable, makes two import calls and divides: the ratio singleton read in round 447
    0x630EF0,  # builds a buffer on the stack and calls the import stub 0x63F508: library formatting
    0x89EA40,  # stores whether the argument was null, clears two members and loads a global: a constructor
    0x630D20,  # checks a bound against 0xff and stores one byte: narrow character conversion
    0x944470,  # installs a vtable from the image then copies a shared_ptr member: ABI and library
    0x943840,  # loads the member at +0x28 and decrements its refcount atomically: a release path
    0x9227C0,  # a constructor that also calls the runtime initialiser 0x8AA7E0 and stores its result
    0x9437A0,  # loads the member at +0x28 and works on its refcount: the same release family
    0x6399E0,  # reads the stream state flags and compares two counters: iostream internals
    0x630F70,  # walks a table of string pairs sixteen bytes apart: a locale or ctype table
    0x921970,  # installs a vtable from the image and stores whether the argument was null: ABI, and the vtable address cannot be reproduced
    0x921B40,  # the same constructor shape as 0x921970
    0x944690,  # the same constructor shape as 0x921970
    0x944860,  # the same constructor shape as 0x921970
    0x9A0700,  # takes a global, calls an import stub, allocates eight bytes, stores a vtable and throws
    0x62FF40,  # special cases minus one and builds six bytes on the stack for a library routine
    0x8771C0,  # tests the first member and a flag then clears: a release or reset path
    0xB81F0,  # returns the constant 100: a default override, not a computation
    0x877120,  # loads a member and calls the runtime stub 0x63F4B8
    0x63F140,  # a bounded byte scan, the strlen shape
    0x7C4AB0,  # allocates eight bytes, stores a vtable, calls the throw entry
    0x998920,  # the same exception object shape as 0x7C4AB0
    0x889010,  # stores a vtable then copies a shared_ptr member
    0x1B130,  # builds a string from a pointer and a length through the strlen stub
    0x63DEB0,  # walks a word array counting non zero entries: a bitset or vector internal
    0x63EA30,  # compares two word arrays element by element: the same family
    0x1E70,  # library by its own label: ' max iterations.'
    0x6100,  # library by its own label: 'basic_string::append'
    0x1B070,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x1D870,  # library by its own label: 'vector::reserve'
    0x1EE50,  # library by its own label: 'vector::_M_range_check: __n (which is %zu) >= this->size() ('
    0x23E70,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x24780,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x268A0,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x2A7E0,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x3B1F0,  # library by its own label: 'basic_string::_M_construct null not valid'
    0xB8210,  # library by its own label: 'basic_string::_M_construct null not valid'
    0xB8500,  # library by its own label: 'basic_string::_M_construct null not valid'
    0xB8890,  # library by its own label: 'basic_string::_M_construct null not valid'
    0xB9320,  # library by its own label: 'basic_string::_M_create'
    0xB9E50,  # library by its own label: 'basic_string::_M_replace'
    0xBA6F0,  # library by its own label: 'basic_string::_M_construct null not valid'
    0xC71D0,  # library by its own label: 'basic_string::_M_construct null not valid'
    0xCAAA0,  # library by its own label: 'basic_string::append'
    0xD05B0,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x1171F0,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x12ADB0,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x12B5F0,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x12BE80,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x12C1B0,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x12C980,  # library by its own label: 'basic_string::append'
    0x12CB40,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x12DA10,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x12F460,  # library by its own label: 'mutex'
    0x1F84C0,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x4CC640,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x4F7830,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x4FB020,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x4FBD80,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x4FD900,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x4FFF80,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x501B60,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x5070E0,  # library by its own label: 'used_surface_usable_offcut_ratio'
    0x520320,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x549110,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x5523B0,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x57F540,  # library by its own label: 'vector::reserve'
    0x582B40,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x592870,  # library by its own label: 'C:\\Users\\renaud\\nest\\external\\boost_1_63_0/boost/multiprecis'
    0x5B3500,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x5EFEA0,  # library by its own label: 'vector::reserve'
    0x5FD100,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x600770,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x600C40,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x602270,  # library by its own label: 'basic_string::append'
    0x602510,  # library by its own label: 'basic_string::append'
    0x602F00,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x603010,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x603740,  # library by its own label: 'basic_string::append'
    0x604020,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x605090,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x60A620,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x60D380,  # library by its own label: 'vector::_M_range_check: __n (which is %zu) >= this->size() ('
    0x63A570,  # library by its own label: 'PRINTF_EXPONENT_DIGITS'
    0x64E710,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x6F3500,  # library by its own label: 'mutex'
    0x6F8E10,  # library by its own label: 'mutex'
    0x74BB30,  # library by its own label: 'bad rational: zero denominator'
    0x74C440,  # library by its own label: 'bad rational: zero denominator'
    0x753000,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x776940,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x799BA0,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x7B1F70,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x81F210,  # library by its own label: 'basic_string::copy'
    0x8200F0,  # library by its own label: 'basic_string::copy'
    0x827240,  # library by its own label: 'cannot create shim for unknown locale::facet'
    0x827BF0,  # library by its own label: 'cannot create shim for unknown locale::facet'
    0x829FE0,  # library by its own label: 'basic_string::copy'
    0x82AD80,  # library by its own label: 'basic_string::copy'
    0x8C2E10,  # library by its own label: 'vector::_M_range_insert'
    0x8CA600,  # library by its own label: 'vector::_M_range_insert'
    0x8CCDC0,  # library by its own label: 'vector::_M_range_insert'
    0x8CE5B0,  # library by its own label: 'vector::_M_range_insert'
    0x8E8080,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x8EC3B0,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x8ECA70,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x8F2780,  # library by its own label: 'vector::reserve'
    0x90B0B0,  # library by its own label: 'vector::_M_default_append'
    0x90F310,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x90F5E0,  # library by its own label: 'basic_string::_M_replace_aux'
    0x910BA0,  # library by its own label: 'basic_string::_M_create'
    0x92AD10,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x92DEE0,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x9926B0,  # library by its own label: 'basic_string::append'
    0x992980,  # library by its own label: 'basic_string::_M_construct null not valid'
    0x9993F2,  # library by its own label: 'basic_string::append'
    0x8AA7D0,  # lea rax,[rip+..] ; ret -- the address of a global object
    0x9635E0,  # mov rax,[rip+..] ; ret -- loads a global pointer
    0x4F7030,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment
    0x5C61D0,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment
    0x5C5260,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment
    0x548630,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment
    0x5C61E0,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment
    0x548380,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment
    0x4F8350,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment
    0x547610,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment
    0x5C5F30,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment
    0x5C5F50,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment
    0x5C5270,  # mov rax, rcx ; ret -- returns its own argument
    0x90ECB0,  # std::string internal: same three words, clamps against max_size
}

# Entries whose value cannot be reproduced by any reimplementation, because it is an address inside the original image.
NOT_EQUIVALENT = {88, 90, 92}   # GetBuildVersion, GetBuildDate, GetMajorVersion


def kind(addr, profile):
    """One verdict per function, from its own instructions only. None if it is not a known function."""
    if addr not in profile:
        return None
    text = []
    size = (profile.get(addr) or {}).get("size")
    for ins in disasm(addr):
        if size and ins.address >= addr + size:
            break
        text.append(ins.mnemonic + " " + ins.op_str)
    if not text:
        return None
    if len(text) == 1:
        return "toolchain"
    for t in text:
        if "qword ptr [rip" in t and (t.startswith("jmp") or t.startswith("call")):
            return "toolchain"
        if t.startswith("call 0x63f3"):
            return "toolchain"
    for t in text:
        if t == "call 0x910ba0":
            return "diagnostic"
    return "domain"


def main():
    profile = load_prof()
    done = L.forwarded_ordinals()
    table = json.loads(io.open(os.path.join(L.ROOT, "re", "exports_table.json"), encoding="utf-8").read())

    verdicts = {}
    rows = []
    for e in table:
        ord0 = (e.get("ords") or [0])[0]
        if ord0 in done:
            continue
        name = e.get("name") or ("sub_%05X" % e["rva"])
        targets = L.external_targets(e["rva"], e["size"])
        rows.append((name, ord0, e["rva"], e["size"], targets))
        for t in targets:
            if t in L.VERIFIED or t in BOILERPLATE or t in verdicts:
                continue
            k = kind(t, profile)
            verdicts[t] = k if k is not None else "unknown"

    counts = {}
    for v in verdicts.values():
        counts[v] = counts.get(v, 0) + 1
    print("distinct blocker addresses judged: %d" % len(verdicts))
    for k in sorted(counts):
        print("    %-11s %d" % (k, counts[k]))
    print("    %-11s %d  (measured whole in earlier rounds)" % ("boilerplate", len(BOILERPLATE)))

    ready = []
    not_equivalent = []
    blocked = []
    for name, ord0, rva, size, targets in rows:
        bad = []
        for t in targets:
            if t in L.VERIFIED or t in BOILERPLATE:
                continue
            if verdicts.get(t) == "domain":
                bad.append(t)
        if not targets:
            ready.append((name, ord0, rva, size, "no external target at all"))
        elif not bad:
            if ord0 in NOT_EQUIVALENT:
                not_equivalent.append((name, ord0, rva, size, "returns an address inside the original image"))
            else:
                ready.append((name, ord0, rva, size, "only boilerplate, toolchain, diagnostic or verified"))
        else:
            blocked.append((name, ord0, rva, size, bad))

    print("")
    print("implementable now: %d" % len(ready))
    for name, ord0, rva, size, why in ready[:80]:
        print("    0x%-6X ord %-4d %-36s %5d bytes  (%s)" % (rva, ord0, name, size, why))
    print("")
    print("not equivalent by address, listed rather than counted as progress: %d" % len(not_equivalent))
    for name, ord0, rva, size, why in not_equivalent:
        print("    0x%-6X ord %-4d %-36s %5d bytes  (%s)" % (rva, ord0, name, size, why))
    print("")
    print("still blocked on real domain code: %d" % len(blocked))
    dom = {}
    for _n, _o, _r, _s, bad in blocked:
        for t in bad:
            dom[t] = dom.get(t, 0) + 1
    for t, c in sorted(dom.items(), key=lambda kv: -kv[1])[:14]:
        size = (profile.get(t) or {}).get("size")
        print("    0x%-8X blocks %3d exports, %s bytes" % (t, c, size))
    return 0


if __name__ == "__main__":
    sys.exit(main())


# Functions already implemented in lcns/src. The closure tools treat these as done, so the denominator falls as work
# lands instead of only when a function is classified as library. Each entry says where it lives.
IMPLEMENTED = {
    0x5F3900,   # batch seven, lcns/field_accessors.hpp
    0x51BFC0,   # batch six, lcns/field_accessors.hpp
    0x4FBE70, 0x822590,   # batch five, lcns/field_accessors.hpp
    0x8774E0,   # eaten by g_eat_leaves.py
    0x54CBC0, 0x4F7690, 0x4F7660, 0x4F7640, 0x4F7680,   # eaten by g_eat_leaves.py
    0x4FC240, 0x4FC250, 0x4FC2F0, 0x4FC300, 0x4FC260, 0x4FC2D0, 0x4FC320, 0x4FC340, 0x4FC290, 0x4FBE90, 0x4FBEA0, 0x4FC330,   # eaten by g_eat_leaves.py
    0x4F8D20, 0x4F8D10, 0x4F7600,   # eaten by g_eat_leaves.py
    0x52F8F0,   # eaten by g_eat_leaves.py
    0x4F8370, 0x4F8380, 0x4F8C80, 0x4F8C90, 0x4F8CA0, 0x4F8CB0, 0x4F9C30, 0x52F900, 0x52F910, 0x4F7330, 0x547650, 0x547630, 0x4F9C20, 0x4F7340, 0x52F8B0,   # eaten by g_eat_leaves.py
    0x4F8F80, 0x4F8F90, 0x4F73B0, 0x4F8540, 0x4F7390, 0x895F80, 0x5479B0, 0x4F77C0, 0x547670, 0x4F8FA0,   # eaten by g_eat_leaves.py
    0x52F930, 0x52F940, 0x4F7350, 0x4F7360, 0x4F73A0, 0x5FBC70, 0x5C4CE0, 0x4F73C0, 0x5C5F40, 0x54D120, 0x5C5F60, 0x5483B0, 0x5483A0, 0x54CE60, 0x52F8A0,   # batch four, lcns/field_accessors.hpp
    0x54D100, 0x5C4CD0, 0x4F7050, 0x4FC1D0, 0x5FC7E0, 0x4FC200, 0x4F8C70, 0x4F76B0, 0x548390,   # batch three, lcns/field_accessors.hpp
    0x4F7380, 0x4F8360, 0x4F8CD0, 0x4F7060, 0x4F76D0, 0x52F8D0, 0x52F8E0,   # batch two, lcns/field_accessors.hpp
    0x52F920, 0x54CE90, 0x54D110, 0x4F8C60, 0x4F8CC0, 0x4F76C0, 0x4F7270, 0x4F7290,   # lcns/field_accessors.hpp
}
