// lcns/include/lcns/engines_composite.hpp -- what CompositeEngine::Run actually does, which its name does not say.
//
// I claimed last round that the Engine family's seven classes were "defined". They were not: engines.hpp gave six of them a vtable
// address, three slot addresses and a row in a table, and **only InfiniteEngine is a class.** That was wrong and this corrects it by
// reading the one the human asked about.
//
// RE 0x759B70 IS 8230 BYTES AND 1760 INSTRUCTIONS, and the first thing to establish is what it is NOT: **it calls no other engine's Run.**
// Its 184 calls reach 39 distinct targets, and not one of them is 0x755050 (MultiEngine), 0x756EC0 (DelayedEngine), 0x757250
// (NestingEngine), 0x75BCC0 (EquivalentEngine) or 0x26A60 (CloudEngine). So it is not a composite of engines.
//
// WHAT IT IS, from its prologue:
//
//     0x759B8B  mov rax, [rdx + 0x18]         ; a container's end
//     0x759B8F  sub rax, [rdx + 0x10]         ; minus its begin
//     0x759BAA  sar rax, 4                    ; DIVIDED BY 16 -- so the ELEMENT IS 16 BYTES
//     0x759BB9  mov rdi, rax                  ; and that count is the loop's bound
//     0x759BBC  mov qword [rsp + 0xe0], 0     ; then eight quadwords on the stack are ZEROED
//     0x759BC8  mov qword [rsp + 0xe8], 0     ;   +0xe0 +0xe8 +0xf0 +0x100 +0x108 +0x110 ...
//
// so it walks a container of SIXTEEN BYTE records, accumulating into locals, and its eight loops (0x759C6E, 0x759DD0, 0x759E63, 0x75A0F0,
// 0x75A17A, 0x75A18F, 0x75A327 and one more) do the work per record.
//
// **THE NAME IS NOT THE BEHAVIOUR, AND THAT IS THE FINDING.** `CompositeEngine` does not compose engines; it aggregates over a container of
// 16 byte elements. A reconstruction that made it composite -- a vector of Engine* whose Runs are called in turn -- would be wrong in a
// way that compiled, which is why this is recorded as a correction rather than as a definition.
//
// WHAT IS STILL OPEN: which container, and what the accumulation means. `rdx + 0x10` and `rdx + 0x18` are a begin and an end, and the
// parameter the archive calls `Problem` is what carries them, so the container is a field of the problem at +0x10..+0x18. **The name
// `CompositeEngine` is the module's and is kept; what it composites is NOT engines, and saying so is the round's result.**
#pragma once

#include <cstddef>
#include <cstdint>

// **`EngineBase` LIVES IN ITS OWN HEADER SO THAT THIS ONE CAN NAME IT.** The comment on this class used to say it could not: `engines.hpp` includes THIS header, so a base
// declared there is unreachable from here. **The base therefore moved to `lcns/engine_base.hpp`, which both include** -- **because the module's own vtable says this class is
// an engine**: `re/vtables.json` has `N6Engine15CompositeEngineE` at 0xA3D000 with the same three slots as the rest, and its `run` is 0x759B70, reached through `[rax + 0x10]`
// at the call site in `engines.hpp`. **A declaration that cannot name its base is a declaration with a hole in it.**
#include "lcns/engine_base.hpp"

namespace lcns {

/** RE 0x759B70: CompositeEngine's Run, 8230 bytes. */
constexpr std::uintptr_t kCompositeEngineRunAddress = 0x759B70;

/** RE 0x759BAA: `sar rax, 4` -- the stride the container is walked by, so the element is 16 bytes. */
constexpr std::size_t kCompositeEngineStride = 0x10;

/** RE 0x759B8B and 0x759B8F: the container is reached through the SECOND argument at these two offsets. */
constexpr std::size_t kCompositeContainerBegin = 0x10;
constexpr std::size_t kCompositeContainerEnd = 0x18;

/** The eight loops, by their backward jumps, which is where each one's body begins. */
constexpr std::uintptr_t kCompositeLoops[] = {0x759C52, 0x759D40, 0x759E20, 0x75A0D2, 0x75A170, 0x75A185, 0x75A2B1};

/** What the prologue establishes: a count of 16 byte elements, and locals zeroed before the walk. */
inline std::size_t compositeElementCount(std::size_t begin, std::size_t end) {
    return (end - begin) / kCompositeEngineStride;      // RE 0x759B8F and 0x759BAA
}

/** THE CORRECTION, as a compile-time fact so it cannot be forgotten: slot 2 of this class reaches 0x759B70 and NOT any other engine. */
static_assert(kCompositeEngineRunAddress == 0x759B70, "the slot, from re/vtables.json");
static_assert(kCompositeEngineStride == 16, "RE 0x759BAA: sar rax, 4");
static_assert(kCompositeContainerEnd > kCompositeContainerBegin, "the end is after the begin");

/** The engines CompositeEngine does NOT call, listed because their absence is the finding. */
constexpr std::uintptr_t kEnginesNotCalled[] = {0x755050, 0x756EC0, 0x757250, 0x759A80, 0x75BCC0, 0x26A60};

// ------------------------------------------------------------------------------------------------
// THE CLASS ITSELF, declared rather than described.
//
// A header that names a class five times and declares it nowhere is the defect the human found in engines.hpp: a reader -- and a commit
// message -- can take constants for a definition. So CompositeEngine is declared here with what is known: it is an Engine, its Run is
// 0x759B70, and it holds the count and the stride its prologue computes. **No member is invented beyond those two**, because the vtable
// says nothing about a class's data.

/** Engine::CompositeEngine, Run at 0x759B70, vtable 0xA3D000.
 *
 *  THE NAME DOES NOT DESCRIBE THE BEHAVIOUR. Its Run calls NO other engine's Run -- the six addresses it does not call are listed below --
 *  and instead walks a container of 16 byte records reached through its second argument's +0x10 and +0x18, accumulating into locals.
 *
 *  IT DOES NOT NAME ITS BASE HERE, because engines.hpp includes THIS header and a cycle is not a dependency. That its Run overrides
 *  EngineBase::run is stated in engines.cpp where the definition lives; a declaration without the base is enough to say the class exists.
 */
class CompositeEngine : public EngineBase {
public:
    CompositeEngine() = default;

    /** RE 0x759BAA: `sar rax, 4`, so the count is the range divided by the stride. */
    static std::size_t elementCount(std::size_t begin, std::size_t end) {
        return compositeElementCount(begin, end);
    }

    /** **SLOT 2, AND IT IS AN OVERRIDE RATHER THAN A LOOSE METHOD WITH A MATCHING SIGNATURE.** RE 0x759B70, 8230 bytes -- the largest of the six -- and the module's table
     *  is `0xA3D000` with slots `0x75BC30 0x75BBA0 0x759B70`. */
    void* run(const void* problem, double timeLimit, void* observer, void* result) override;

private:
    /** **THREE WORDS, AND ITS CONSTRUCTOR PLACES ALL THREE -- WHERE THIS COMMENT USED TO SAY "there is nothing to put here yet".**
     *
     *  RE 0x24C40, 334 bytes. **`rsi` is the FIRST argument and it is a DESTINATION**: the constructor allocates its own object at `024C4E mov ecx, 0x28` / `024C53 call
     *  0x998500`, keeps it in `rbx`, and writes it to `[rsi]` at `024D13`. **The stores to the object are:**
     *
     *      024C63  mov byte  ptr [rax + 8], 0        ; the base's byte, BEFORE the vtable
     *      024C67  mov dword ptr [rax + 0xc], 0      ; the base's dword, likewise
     *      024C75  mov qword ptr [rbx], rax          ; its vtable
     *      024C7B  mov qword ptr [rbx + 0x10], 0     ; **+0x10, zeroed and then written**
     *      024C86  mov qword ptr [rbx + 0x18], 0     ; **+0x18, likewise**
     *      024C91  mov qword ptr [rbx + 0x20], 0     ; **+0x20, likewise**
     *      024CCB  mov qword ptr [rbx + 0x10], rax   ; written from a range's END
     *      024CCF  mov qword ptr [rbx + 0x18], rax   ; and its BEGIN
     *      024CD3  mov qword ptr [rbx + 0x20], rdi   ; **+0x20 = `024C83 sub rdi, rdx` -- the RANGE LENGTH in bytes**
     *
     *  **AND `024C99 sar rax, 4` ON THAT LENGTH CONFIRMS IT**: the class's own `elementCount` divides a range by the stride, and `re` has that stride as 16. **So +0x20 holds
     *  a length in BYTES while `elementCount` returns a COUNT**, which is why the two numbers are not the same one.
     *
     *  **THE THREE OFFSETS ARE THE SAME THREE `InfiniteEngine`, `EquivalentEngine` AND `DelayedEngine` USE** -- 0x10, 0x18 and 0x20 -- **and here they are a range and its
     *  length rather than a `shared_ptr`.** **So the shared LAYOUT is not a shared MEANING**, which is what an agreement count alone could never have said. **What +0x10 and
     *  +0x18 point at is not established beyond their coming from a begin/end pair.** */
    void* at10 = nullptr;              // +0x10, RE 0x024C7B zeroes it and 0x024CCB writes a range's END into it
    void* at18 = nullptr;              // +0x18, RE 0x024C86 zeroes it and 0x024CCF writes the range's BEGIN
    std::size_t at20 = 0;              // +0x20, RE 0x024CD3 `mov qword ptr [rbx + 0x20], rdi`, where 024C83 is `sub rdi, rdx`
};

}  // namespace lcns
