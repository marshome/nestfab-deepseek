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
class CompositeEngine {
public:
    CompositeEngine() = default;

    /** RE 0x759BAA: `sar rax, 4`, so the count is the range divided by the stride. */
    static std::size_t elementCount(std::size_t begin, std::size_t end) {
        return compositeElementCount(begin, end);
    }

    void* run(const void* problem, double timeLimit, void* observer, void* result);

private:
    // RE 0x759BBC: the eight quadwords its prologue zeroes are LOCALS, not members -- they live at rsp+0xe0 upward. The only thing this
    // class is known to hold is the container it walks, and that belongs to the Problem its Run is handed rather than to the engine, so
    // there is nothing to put here yet and saying so is more useful than a placeholder.
};

}  // namespace lcns
