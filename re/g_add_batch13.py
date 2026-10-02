# -*- coding: utf-8 -*-
"""Batch thirteen: 0x1BF40 is the engine fetch, and 0x1BF00 is the module switch the entry point tests first.

Round 531. The entry point's first two calls are these, and they turned out to be the top of a chain the two wrappers and
the orchestration both depend on:

    2ACB  call 0x1BF00          ; if this returns 1, jump to 0x31C9 and read 'cns_force_cloud'
    2B0A  call 0x1BF40          ; the engine, or null

0x1BF00 is eighteen bytes and is fully determined:

    1BF00  sub rsp, 0x28
           call 0x1BE70          ; the module's lazy static, whose guard and constructor are library
           movzx eax, byte [rax + 1]
           ret

0x1BF40 is 149 bytes and is the same static, then three module flags:

    1BF40  static = 0x1BE70()
    1BF4A  if (static[0] == 0) return null                      ; the static says the engine is off
    1BF4F  if (module_flag_A[0] != 0) goto done                 ; the diagnostic stream was already built
    1BF80  guard = __cxa_guard_acquire(&guard_B)
    1BF90  if (guard) 0x7BB430(&the_stream)                      ; build the diagnostic header once
    1BFA3  __cxa_guard_release / register through 0x998EE0
    1BFAF  0x62D860()                                           ; the current thread id
    1BF5A  if (module_dword[0] != 0) return null                ; the build id is zero
    1BF64  return &the_stream                                   ; 0xB033C5

So what the entry point calls "the engine" is a stream, and the module's whole "engine or null" decision is: the static's
first byte says on or off, and a module dword says whether a build id was recorded. That is the shape of a diagnostics
guard rather than of an engine, and it is consistent with 0x7BB430, whose whole content is the product name, the version
and build objects, a CPUID-derived number and the CPU vendor and brand strings.

What is implemented here is the decision, with the two module fields and the three bytes of the static that the two
functions actually read, and the addresses they live at recorded as RE comments. The static itself and the guard are the
runtime's, the header is 0x7BB430, and the wrapper's own two offsets are what a caller sees.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "field_accessors.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")
TOOLCHAIN = os.path.join(ROOT, "re", "g_toolchain.py")

IMPLEMENTED = [
    (0x1BF00, "batch thirteen, lcns/field_accessors.hpp"),
    (0x1BF40, "batch thirteen, lcns/field_accessors.hpp -- the decision, with the module's data as arguments"),
]

ACCESSOR = '''/** RE 0x1BF00: the entry point's first test. It reads byte 1 of the module's lazy static, which is the switch that
 * decides whether LaunchLocalComputation does any work at all: the orchestration jumps to the 'cns_force_cloud' path when
 * this returns non-zero. moduleStatic_1BE70 is the caller's view of that static, because the static itself is built by the
 * runtime's guard and by 0x65A530. */
inline std::uint8_t moduleSwitch_1BF00(const void* moduleStatic_1BE70) {
    // RE 0x1BF09: movzx eax, byte ptr [rax + 1]
    std::uint8_t value = 0;
    std::memcpy(&value, static_cast<const unsigned char*>(moduleStatic_1BE70) + 1, sizeof(value));
    return value;
}

/** RE 0x1BF40: the engine fetch. It reads the static's first byte, the module flag that says the diagnostic header was
 * already built, and the module dword that holds the build id, and returns the header or null. The addresses are the
 * module's own: 0xB033C5 for the header, 0xB0324A for the flag, 0xB03348 for the dword and 0xB03217 for the guard. They
 * are reproduced as the arguments the test supplies, because a reimplementation does not own the module's data. */
inline void* engineFetch_1BF40(const void* moduleStatic_1BE70,
                               const std::uint8_t* headerBuiltFlag,
                               const std::uint32_t* buildId,
                               void* header) {
    // RE 0x1BF4A: the static's first byte, which is a different byte from the switch 0x1BF00 reads at +1.
    std::uint8_t on = 0;
    std::memcpy(&on, static_cast<const unsigned char*>(moduleStatic_1BE70), sizeof(on));
    if (on == 0) {
        return nullptr;
    }
    if (*headerBuiltFlag == 0) {
        // RE 0x1BF90: the header is built once, under the guard, by 0x7BB430. That function is read and classified, and
        // its effect is the header the caller passes in, so it is not run here.
    }
    if (*buildId != 0) {
        return nullptr;
    }
    return header;
}

'''

TESTS = '''    // ------------------- the module switch and the engine fetch (RE 0x1BF00 and 0x1BF40)
    {
        unsigned char module_static[0x10];
        std::memset(module_static, 0, sizeof(module_static));
        module_static[0] = 1;                       // RE 0x1BF4A: the static says the engine is on
        module_static[1] = 1;                       // RE 0x1BF09: the switch 0x1BF00 returns
        CHECK(lcns::dll::accessors::moduleSwitch_1BF00(module_static) == 1);
        module_static[1] = 0;
        CHECK(lcns::dll::accessors::moduleSwitch_1BF00(module_static) == 0);

        std::uint8_t header_flag = 1;               // RE 0x1BF4F: the header was already built
        std::uint32_t build_id = 0;                 // RE 0x1BF62: a zero build id is the one that lets the fetch through
        int header = 0;
        CHECK(lcns::dll::accessors::engineFetch_1BF40(module_static, &header_flag, &build_id, &header) == &header);
        // RE 0x1BF4D: the static's first byte is clear, so the fetch returns null whatever else says.
        module_static[0] = 0;
        CHECK(lcns::dll::accessors::engineFetch_1BF40(module_static, &header_flag, &build_id, &header) == nullptr);
        module_static[0] = 1;
        // RE 0x1BF62: a non-zero build id returns null, which is the case where the module recorded one.
        build_id = 7;
        CHECK(lcns::dll::accessors::engineFetch_1BF40(module_static, &header_flag, &build_id, &header) == nullptr);
        build_id = 0;
        // RE 0x1BF56 to 0x1BF90: the header is not built yet, which is the branch that calls 0x7BB430. It must not change
        // the result, because that call only writes the header the caller owns.
        header_flag = 0;
        CHECK(lcns::dll::accessors::engineFetch_1BF40(module_static, &header_flag, &build_id, &header) == &header);
    }

    return check::finish("boxacc");'''


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    h = read(HDR)
    anchor = "}  // namespace accessors"
    assert anchor in h, "the accessor namespace close line is gone"
    write(HDR, h.replace(anchor, ACCESSOR + anchor, 1))
    print("field_accessors.hpp  the module switch and the engine fetch")

    t = read(TEST)
    fin = '    return check::finish("boxacc");'
    assert fin in t, "the boxacc test tail is gone"
    write(TEST, t.replace(fin, TESTS, 1))
    print("test_boxacc.cpp      the five checks")

    s = read(TOOLCHAIN)
    marker = "IMPLEMENTED = {"
    assert marker in s, "the IMPLEMENTED set is gone"
    entries = [marker]
    for rva, why in IMPLEMENTED:
        if "0x%X," % rva not in s:
            entries.append("    0x%X,   # %s" % (rva, why))
    s = s.replace(marker, "\n".join(entries), 1)
    write(TOOLCHAIN, s)
    print("g_toolchain.py       %d registered as implemented" % (len(entries) - 1))
    print("done")


if __name__ == "__main__":
    main()
