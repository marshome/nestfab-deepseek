// lcns/include/lcns/module_switch.hpp -- the module-wide (flag, object, gate) triple, RE from two independent closures.
//
// RE 0x9AF0 and RE 0x64B2C0 are 452 and 435 byte domain functions in different parts of the module, with one and three callers, and
// their prologues are the same:
//
//     0x9AF7  movzx eax, byte ptr [rip + 0xb15552]   -> rva 0xB1F050
//     0x9B09  lea   rcx, [rip + 0xb15548]            -> rva 0xB1F058
//     0x9B1A  call  0x63F6C0
//
//     0x64B2C7 movzx eax, byte ptr [rip + 0x4d3d82]  -> rva 0xB1F050   THE SAME
//     0x64B2DC lea   rcx, [rip + 0x4d3d75]           -> rva 0xB1F058   THE SAME
//     0x64B2ED call  0x63F6C0
//
// **Same flag, same object, same gate.** The displacements differ because the instructions are at different addresses, which is the
// fourth time this project has found two displacements resolving to one address -- and the reason a displacement must never be recorded
// as if it were an address.
//
// The pair is tested against the gate at 0x63F6C0, which the ledger already records as the logger's SECOND gate from 0x64AEA0's
// preamble. And 0xB1F050 is NOT the logger's own switch at 0xB1F018 -- it is 0x38 further on -- so this is a second, independent
// module-wide flag.
//
// WHY IT IS A HEADER. A global reached from two unrelated closures is shared state rather than a local convenience, and a C++
// reconstruction needs to name it exactly once rather than once per function. The shape -- test an enable flag, and if it is set hand a
// global object to a gate -- is what a lazily initialised singleton compiles to: the flag says whether the object has been built and
// the gate is what builds it.
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {

/** RE 0x9AF7 and 0x64B2C7: the module-wide enable flag. `movzx eax, byte ptr [rip + ...]`. */
constexpr std::uintptr_t kModuleSwitchFlag = 0xB1F050;

/** RE 0x9B09 and 0x64B2DC: the object the gate is handed. `lea rcx, [rip + ...]`. */
constexpr std::uintptr_t kModuleSwitchObject = 0xB1F058;

/** RE 0x9B1A and 0x64B2ED: the gate both call. The ledger records it as the logger's second gate. */
constexpr std::uintptr_t kModuleSwitchGate = 0x63F6C0;

/** RE 0x64AEA0's preamble: the logger's OWN switch, which is a different global 0x38 before this one. */
constexpr std::uintptr_t kLoggerSwitch = 0xB1F018;

static_assert(kModuleSwitchObject == kModuleSwitchFlag + 8, "the object is the flag's neighbour, 8 bytes on");
static_assert(kModuleSwitchFlag != kLoggerSwitch, "these are two different module-wide switches and must not be merged");
static_assert(kLoggerSwitch + 0x38 == kModuleSwitchFlag, "0xB1F018 + 0x38 is 0xB1F050, which is how they were told apart");

/** The two call sites that establish the pair, as constants so a test can assert them rather than a comment. */
constexpr std::uintptr_t kModuleSwitchSiteA = 0x9AF0;
constexpr std::uintptr_t kModuleSwitchSiteB = 0x64B2C0;
static_assert(kModuleSwitchSiteA != kModuleSwitchSiteB, "two independent closures, which is what makes the state shared");

/** RE the prologue both sites share: the enable flag is consulted first, and the gate only runs when it is set.
 *
 * `enabled` is the byte at kModuleSwitchFlag and `gate` is the function at kModuleSwitchGate. The two sites both store a zero byte and
 * the object's address to their own stack slots before the call, which is the setup the gate expects and not part of the test.
 */
inline bool moduleSwitchEnabled(unsigned char flag) {
    return flag != 0;                      // RE 0x9AFE and 0x64B2CE: `test al, al` then `je`
}

}  // namespace lcns
