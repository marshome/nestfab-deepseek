// lcns/include/lcns/engine_defaults.hpp -- the values RE 0x4E5B0 installs, each with the instruction that writes it.
//
// RE 0x4E5B0 is 1574 bytes with two callers, and it is the initialiser of the object that RE 0x4EC00 then fills by name. It writes a
// fixed set of values, and every one below is the immediate of its instruction or the double its `movsd` loads -- so these are
// MEASURED, not inferred, and each carries the address that says so.
//
//     0x4E5FE  mov    byte  ptr [rcx], 1                  ; a flag at +0x00
//     0x4E5E0  movsd  qword ptr [rcx + 8], xmm2           ; 0.0001 from 0x9B1FB0
//     0x4E601  mov    dword ptr [rcx + 0x10], 0xa         ; 10
//     0x4E608  mov    dword ptr [rcx + 0x14], 5           ; 5
//     0x4E60F  mov    dword ptr [rcx + 0x18], 0xc         ; 12
//     0x4E616  mov    byte  ptr [rcx + 0x1c], 1
//     0x4E61A  mov    byte  ptr [rcx + 0x1d], 1
//     0x4E61E  mov    byte  ptr [rcx + 0x1e], 1
//     0x4E622  mov    dword ptr [rcx + 0x20], 8           ; 8
//     0x4E629  mov    dword ptr [rcx + 0x24], 0x1e        ; 30
//     0x4E5E5  movsd  qword ptr [rcx + 0x28], xmm5        ; 0.01
//     0x4E5EA  movsd  qword ptr [rcx + 0x30], xmm3        ; 0.1
//     0x4E5EF  movsd  qword ptr [rcx + 0x38], xmm4        ; 0.001
//     0x4E630  mov    dword ptr [rcx + 0x40], 8           ; 8
//     0x4E637  mov    dword ptr [rcx + 0x48], 5           ; 5
//     0x4E5F4  mov    dword ptr [rcx + 0x350], 0xf        ; 15, and see below
//     0x4E5D8  movsd  qword ptr [rcx + 0x358], xmm0       ; 0.5
//
// AND FIVE OF THESE OFFSETS MATCH NAMES FROM lcns/parameter_report.hpp, which is the check that the two readings are of one object:
//
//     +0x10  nb_iterations_before_postop?          no -- but +0x1C/0x1D/0x1E are enable_last_compaction / enable_last_postop and the
//            report lists only +0x1C, so two of the three bytes are unnamed in the report
//     +0x20  nb_iterations_first is at +0x48, and +0x20 is in the report's gap
//
// so the overlap is PARTIAL and the honest statement is that the two sets of offsets are consistent where they meet -- +0x1C is
// enable_last_compaction in both -- and that the initialiser writes values at offsets the report leaves as gaps. That is evidence the
// report is incomplete rather than wrong.
//
// THE 0x0F AT +0x350 is the value worth naming: 15 written into a dword immediately before the object's last double, in an initialiser
// that otherwise writes small counts and ratios. 15 is the kind of number a sentinel takes, and this project does not call it one without
// more evidence -- so it is recorded as a literal with its address and nothing more.
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {

/** One value RE 0x4E5B0 installs, with the instruction that installs it. */
struct EngineDefault {
    std::size_t offset;
    enum class Kind { Byte, Dword, Double } kind;
    double value;            // exact for Byte and Dword, since those are integers
    std::uintptr_t site;     // the instruction
};

inline const EngineDefault* engineDefaults(std::size_t& count) {
    static const EngineDefault table[] = {
        {0x000, EngineDefault::Kind::Byte,   1.0,    0x4E5FE},
        {0x008, EngineDefault::Kind::Double, 0.0001, 0x4E5E0},
        {0x010, EngineDefault::Kind::Dword,  10.0,   0x4E601},
        {0x014, EngineDefault::Kind::Dword,  5.0,    0x4E608},
        {0x018, EngineDefault::Kind::Dword,  12.0,   0x4E60F},
        {0x01C, EngineDefault::Kind::Byte,   1.0,    0x4E616},
        {0x01D, EngineDefault::Kind::Byte,   1.0,    0x4E61A},
        {0x01E, EngineDefault::Kind::Byte,   1.0,    0x4E61E},
        {0x020, EngineDefault::Kind::Dword,  8.0,    0x4E622},
        {0x024, EngineDefault::Kind::Dword,  30.0,   0x4E629},
        {0x028, EngineDefault::Kind::Double, 0.01,   0x4E5E5},
        {0x030, EngineDefault::Kind::Double, 0.1,    0x4E5EA},
        {0x038, EngineDefault::Kind::Double, 0.001,  0x4E5EF},
        {0x040, EngineDefault::Kind::Dword,  8.0,    0x4E630},
        {0x048, EngineDefault::Kind::Dword,  5.0,    0x4E637},
        {0x350, EngineDefault::Kind::Dword,  15.0,   0x4E5F4},
        {0x358, EngineDefault::Kind::Double, 0.5,    0x4E5D8},
    };
    count = sizeof(table) / sizeof(table[0]);
    return table;
}

/** The five doubles, named for what they are rather than for what they might mean. */
constexpr double kDefaultSmallRatio = 0.0001;   // RE 0x4E5E0, the value at +0x008
constexpr double kDefaultTinyRatio = 0.001;     // RE 0x4E5EF, +0x038
constexpr double kDefaultTenthRatio = 0.1;      // RE 0x4E5EA, +0x030
constexpr double kDefaultHundredthRatio = 0.01; // RE 0x4E5E5, +0x028
constexpr double kDefaultHalfRatio = 0.5;       // RE 0x4E5D8, +0x358

static_assert(sizeof(EngineDefault) == 32, "offset, kind, value and site");

}  // namespace lcns
