# -*- coding: utf-8 -*-
"""Declare `Utils::TimerWinImplementation`: a 0x10 byte class whose constructor and only method are both fully read.

**EVERYTHING BELOW IS ONE INSTRUCTION, AND THE TWO FUNCTIONS AGREE:**

    the CONSTRUCTOR is 0x5F47C0, 112 bytes (the only site that installs its vtable):
        5F47C6  mov ecx, 0x10                     ; THE OBJECT IS 0x10 BYTES
        5F47D8  lea rax, [rip + 0x4474e1]         ; 0x5F47DF + 0x4474E1 = 0xA3BCC0 = its own vtable
        5F47DF  mov qword [rbx], rax              ; +0x00 = the vptr
        5F47E2  call qword [rip + 0x534304]       ; an IMPORTED call -- the performance counter
        5F47ED  call qword [rip + 0x5342F1]       ; and the frequency
        5F47FB  cvtsi2sd xmm0, [rsp + 0x30]       ; the counter as a double
        5F4805  cvtsi2sd xmm1, [rsp + 0x20]       ; the frequency as a double
        5F480C  divsd xmm0, xmm1
        5F4810  movsd qword [rbx + 8], xmm0       ; +0x08 = COUNTER / FREQUENCY, i.e. seconds

    and the METHOD is slot 2, 0x6D5910, 67 bytes:
        6D591D  call qword [rip + 0x4531c9]       ; the same two imports
        6D5928  call qword [rip + 0x4531b6]
        6D5936  cvtsi2sd xmm0, [rsp + 0x30]
        6D593D  cvtsi2sd xmm1, [rsp + 0x20]
        6D5944  divsd xmm0, xmm1
        6D5948  subsd xmm0, qword [rbx + 8]       ; **MINUS the +0x08 the constructor stored**
        6D5952  ret                               ; returned in xmm0, a double

**SO `+0x08` IS A BASELINE AND THE METHOD IS "SECONDS SINCE THAT BASELINE"**, with the subtraction at 0x6D5948 being the whole point of the field. **The class's
name is `Utils::TimerWinImplementation`, which is the module's own string**, and the two imports are the only platform calls in it -- which is what "Win" in the
name says.
"""
import io
import sys

TARGET = r"D:\Nesting\nestfab\lcns\include\lcns\engine.hpp"

BLOCK = '''/** RE 0xA3BCB0, THREE SLOTS: 0x6D5970 and 0x6D5960 the destructor pair, and 0x6D5910 the ONE method. **The object is 0x10 bytes**, from the only site that
 *  installs this vtable, 0x5F47C0, whose `mov ecx, 0x10` at 0x5F47C6 is the allocation and whose store at 0x5F4810 is the field.
 *
 *  **AND THE TWO FUNCTIONS AGREE ON WHAT +0x08 MEANS.** The constructor stores `counter / frequency` there, and the method computes the same quotient and then
 *  **subtracts that field**:
 *
 *      5F4810  movsd qword [rbx + 8], xmm0        ; the constructor's baseline, in SECONDS
 *      6D5948  subsd xmm0, qword [rbx + 8]        ; and the method's `now - baseline`
 *      6D5952  ret                                ; returned in xmm0
 *
 *  so the method is **seconds elapsed since the object was built**, and the subtraction is the whole purpose of the field. **The only calls in either function are
 *  two imports at 0x534304 and 0x5342F1 through the IAT**, which is what `Win` in the class's own name says. `Utils::TimerWinImplementation` is the module's
 *  string for it, from the RTTI. */
class TimerWinImplementation {
public:
    virtual ~TimerWinImplementation() = default;

    /** RE 0x6D5910, 67 bytes: `counter / frequency - baseline`, returned in `xmm0` as a double. **The name says what it returns and not what the module calls
     *  it** -- the module has no string for this method, so it is named for its arithmetic rather than given a plausible one. */
    virtual double elapsedSeconds() const;       // RE 0x6D5952 returns in xmm0

    // +0x00  RE 0x5F47DF: mov qword [rbx], rax, where rax is 0xA3BCC0 -- this class's own vtable

    /** +0x08, RE 0x5F4810: `movsd qword [rbx + 8], xmm0`, where xmm0 is `counter / frequency` from the two imports at 0x5F47E2 and 0x5F47ED. **It is a baseline
     *  in seconds and the method subtracts it**, so the pair of instructions is what establishes the meaning rather than the field alone. */
    double baselineSeconds_ = 0.0;               // +0x08
};

'''

MARKER = "// RE Multi::Supervisor (vtable 0xA3B4D0), Run at 0x827F0"


def main():
    text = io.open(TARGET, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "class TimerWinImplementation" in text:
        print("the class is already declared")
        return 0
    if MARKER not in text:
        print("REFUSING: the Supervisor comment is not found as the anchor")
        return 2
    text = text.replace(MARKER, BLOCK + MARKER, 1)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(text)
    print("engine.hpp: declared Utils::TimerWinImplementation, 0x10 bytes with its baseline at +0x08")
    return 0


if __name__ == "__main__":
    sys.exit(main())
