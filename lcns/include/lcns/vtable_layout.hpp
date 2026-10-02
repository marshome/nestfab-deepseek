// lcns/include/lcns/vtable_layout.hpp -- where a class's vtable pointer points, and how its constructor is found.
//
// MEASURED BY DUMPING 0xA3CFC0, because three attempts to reason it out produced three different answers and the bytes settled it.
// re/vtables.json gives `vtable_rva` = 0xA3CFD0 for Engine::InfiniteEngine, and the memory there is:
//
//     0xA3CFD0: 0x0000000000000000     the ADDRESS POINT, NULL as this ABI leaves it
//     0xA3CFD8: 0x000000006BED90F0     the RTTI typeinfo, at +8
//     0xA3CFE0: 0x000000006BC19B20     SLOT 0, whose VALUE is 0x759B20
//     0xA3CFE8: 0x000000006BC19AD0     SLOT 1 = 0x759AD0
//     0xA3CFF0: 0x000000006BC19A80     SLOT 2 = 0x759A80
//
// **SO THE FIRST SLOT'S ADDRESS IS `vtable_rva + 0x10`**, and a function that installs the vtable loads THAT address and stores it into the
// object's first quadword. Engine::InfiniteEngine's destructor does exactly that:
//
//     0x759AD6  lea rax, [0xA3CFE0]     ; the first slot's ADDRESS, not its value and not the address point
//     0x759AE7  mov [rcx], rax          ; into the object
//
// WHICH IS WHY A CLASS'S CONSTRUCTOR CAN BE FOUND MECHANICALLY: a function that references that address is either the constructor, the
// destructor pair, or a factory -- and re/g_find_ctors.py counts 555 such references across 399 of the module's vtables.
//
// TWO BUGS MADE THE FIRST VERSION REPORT ZERO, and they were one mistake in two places: a dictionary keyed on the slots' VALUES
// (0x759B20) while the references are the slots' ADDRESSES (0xA3CFE0). **A vtable's values are code to call; its addresses are what a
// pointer holds.**
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {

/** RE the dump at 0xA3CFD0: the offset from `vtable_rva` to the first slot's address. */
constexpr std::size_t kVtableAddressPointOffset = 0x10;

/** RE the same dump: the NULL address point at +0 and the typeinfo at +8. */
constexpr std::size_t kVtableAddressPoint = 0x00;
constexpr std::size_t kVtableTypeInfo = 0x08;

/** The address of a class's slot N, which is what a vtable pointer holds. RE 0x759AD6 loads slot 0's. */
constexpr std::uintptr_t vtableSlotAddress(std::uintptr_t vtableRva, unsigned slot) {
    return vtableRva + kVtableAddressPointOffset + slot * 8u;
}

/** Engine::InfiniteEngine, as the dump gives it: the base, and the three slot addresses. */
constexpr std::uintptr_t kInfiniteEngineVtableRva = 0xA3CFD0;
constexpr std::uintptr_t kInfiniteEngineSlot0Address = kInfiniteEngineVtableRva + 0x10;   // 0xA3CFE0
constexpr std::uintptr_t kInfiniteEngineSlot1Address = kInfiniteEngineVtableRva + 0x18;   // 0xA3CFE8
constexpr std::uintptr_t kInfiniteEngineSlot2Address = kInfiniteEngineVtableRva + 0x20;   // 0xA3CFF0

/** And the VALUES at those addresses, which the dump also gives. */
constexpr std::uintptr_t kInfiniteEngineSlot0Value = 0x759B20;   // the deleting destructor
constexpr std::uintptr_t kInfiniteEngineSlot1Value = 0x759AD0;   // the destructor
constexpr std::uintptr_t kInfiniteEngineSlot2Value = 0x759A80;   // Run

/** A constructor is found by the address its `lea` installs, so the candidates for one class are the functions that reference this. */
constexpr std::uintptr_t kInfiniteEngineCtorCandidate = 0x24FD0;   // 209 bytes

/** RE 0x24FDA inside that candidate: `mov ecx, 0x30` before the allocator, so the class is 0x30 bytes. */
constexpr std::size_t kInfiniteEngineObjectBytes = 0x30;
/** RE 0x24FFC: `mov byte ptr [rax + 8], 0`, the first field the constructor writes. */
constexpr std::size_t kInfiniteEngineFieldAt8 = 0x08;

/** Multi::NestingNester: its constructor calls a base at 0xB4470 and then installs its vtable at +0. RE 0x342F5, 0x342FA, 0x34308. */
constexpr std::uintptr_t kNestingNesterCtor = 0x342E0;           // 422 bytes, 19 calls
constexpr std::uintptr_t kNestingNesterBaseCtor = 0xB4470;       // RE 0x342F5
constexpr std::size_t kNestingNesterVtableField = 0x00;          // RE 0x34308: mov [rbx], rax

static_assert(kVtableAddressPointOffset == 0x10, "the dump at 0xA3CFD0: the typeinfo is at +8 and slot 0 at +0x10");
static_assert(kInfiniteEngineSlot0Address == 0xA3CFE0, "the address RE 0x759AD6 loads");
static_assert(kInfiniteEngineSlot2Value == 0x759A80, "Run, which this project implements for that class");
static_assert(vtableSlotAddress(0xA3CFD0, 0) == 0xA3CFE0, "slot 0's address");
static_assert(vtableSlotAddress(0xA3CFD0, 2) == 0xA3CFF0, "slot 2's address");
static_assert(kInfiniteEngineObjectBytes == 0x30, "RE 0x24FDA: mov ecx, 0x30");

}  // namespace lcns
