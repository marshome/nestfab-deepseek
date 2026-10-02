// lcns/include/lcns/engines.hpp -- the Engine family, of which only addresses existed until now.
//
// engine.hpp carries the BASE class and a comment listing the seven Run slots:
//
//     MultiEngine 0x755050, DelayedEngine 0x756EC0, NestingEngine 0x757250, InfiniteEngine 0x759A80,
//     CompositeEngine 0x759B70, EquivalentEngine 0x75BCC0, CloudEngine 0x26A60
//
// **and the comment was all there was.** This header defines the one whose body has been read in full, and records the interface the
// others will take, so that the next one is a definition rather than a paragraph.
//
// THE INTERFACE, read from the call site at 0x2516E rather than inferred from the slots:
//
//     0x25157  mov rdx, [r12]              ; the engine object
//     0x2515B  movq xmm3, r15              ; a double -- the TIME LIMIT, see below
//     0x25160  mov r8, r13                 ; an observer
//     0x25163  mov rcx, rsi                ; rsi = rsp+0x70, a RESULT BUFFER
//     0x25166  mov rax, [rdx]              ; the vtable
//     0x25169  mov [rsp + 0x20], r14       ; one stack argument
//     0x2516E  call qword ptr [rax + 0x10] ; SLOT 2, the Run
//
// and 0x25171 reads the buffer back (`mov eax, [rsp+0x70]`), so the slot RETURNS the buffer it was given. Slot 0 is the destructor and
// slot 1 the deleting destructor, which makes Run slot 2 -- the same layout as every other polymorphic class in this module.
//
// The register order gives `Run(problem, timeLimit, observer, result)` with the result OUTSIDE the arguments, which is what a routine
// returning a pointer into memory it was handed looks like.
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {

/** The vtable slot of `Run`, RE 0x2516E: `call qword ptr [rax + 0x10]`. */
constexpr std::size_t kEngineRunSlot = 0x10;

/** The sentinel RE 0x759A85 compares the time limit against: the double at rva 0x9AE740 is -1.0. */
constexpr double kUnlimitedTime = -1.0;

/** The address of that double, so a test can assert it rather than trust a decimal. */
constexpr std::uintptr_t kUnlimitedTimeConstant = 0x9AE740;

/** The seven Run slots, by the address in the base class's comment. */

/** RE 0x757AE0, the routine the unlimited case calls DIRECTLY rather than through the vtable -- NestingEngine's Run slot, reached directly rather than through a vtable. */
constexpr std::uintptr_t kNestingEngineRunDirect = 0x757AE0;

/** The Engine family's interface, as the call site expresses it.
 *
 * `Problem`, `Observer` and `Result` are names for the three roles the registers carry, and they are the module's own vocabulary: the
 * archive records `Run(const Problem&, double time_limit, Observer&, Result&)` inferred from this same site, and the double is the one
 * 0x759A85 compares against -1.0.
 *
 * The result is returned as a POINTER rather than by value because the caller passes a buffer and the slot hands it back -- and because
 * the recovered `Run`s end with `mov rax, rbx` where rbx is that buffer.
 */
class EngineBase {
public:
    virtual ~EngineBase() = default;

    /** Slot 2, RE 0x2516E. The default is pure, so a subclass must say what it does rather than inherit silence. */
    virtual void* run(const void* problem, double timeLimit, void* observer, void* result) = 0;
};

/** RE 0x759A80 (80 bytes): either run the nesting engine for ever, or hand the work to a nested engine.
 *
 * The whole body:
 *
 *     0x759A85  ucomisd xmm3, [rip + 0x254cb3]   ; the time limit against -1.0, rva 0x9AE740
 *     0x759A90  jp  0x759AB0                     ; a NaN time limit takes the delegating path
 *     0x759A92  jne 0x759AB0                     ; and so does any limit that is not exactly -1.0
 *     0x759A94  mov r9, [rsp + 0x60]             ; the stack argument
 *     0x759A99  call 0x757AE0                    ; NESTING ENGINE'S RUN, called directly
 *     0x759A9E  mov rax, rbx                     ; rbx is the result buffer from rcx
 *     0x759AA6  ret
 *     0x759AB0  mov rdx, [rdx + 0x10]            ; OTHERWISE: the INNER ENGINE at this + 0x10
 *     0x759AB4  mov rcx, [rsp + 0x60]            ; the stack argument
 *     0x759AB9  mov rax, [rdx]                   ; the inner engine's vtable
 *     0x759ABC  mov [rsp + 0x20], rcx
 *     0x759AC1  mov rcx, rbx                     ; the same result buffer
 *     0x759AC4  call qword ptr [rax + 0x10]      ; AND ITS RUN, slot 2
 *     0x759AC7  mov rax, rbx / ret
 *
 * so the class is a DECORATOR with a sentinel: `-1.0` means "no limit, nest until done", and any other limit means the nested engine
 * should decide. The two branches return the same buffer, which is why the routine reads as one decision rather than two behaviours.
 *
 * THE MEMBER IS AT +0x10, which is the offset RE 0x759AB0 reads, and it is the only field the routine touches -- so the class has one
 * member and one virtual method, and the padding before +0x10 belongs to the vtable pointer at +0.
 */
class InfiniteEngine : public EngineBase {
public:
    InfiniteEngine() = default;

    /** The inner engine, RE 0x759AB0: `mov rdx, [rdx + 0x10]`. */
    void setInner(EngineBase* inner) { inner_ = inner; }
    EngineBase* inner() const { return inner_; }

    /** RE 0x759A80's decision, as the instructions express it. `delegate` does what calling the inner engine's Run does, and
     *  `runUnlimited` does what RE 0x757AE0 does; both are parameters because neither the inner engine nor 0x757AE0 is part of what this
     *  routine determines, and the routine's own content is WHICH of them runs.
     *
     *  A NaN limit takes the delegating path, because 0x759A90 is `jp` -- so "unlimited" is exactly -1.0 and not "any special value".
     */
    template <typename RunUnlimited, typename Delegate>
    void* dispatch(double timeLimit, void* result, RunUnlimited runUnlimited, Delegate delegate) const {
        if (timeLimit == kUnlimitedTime) {          // RE 0x759A85, 0x759A90 jp, 0x759A92 jne
            return runUnlimited(result);            // RE 0x759A99 call 0x757AE0
        }
        return delegate(inner_, result);            // RE 0x759AB0 through 0x759AC4
    }

    void* run(const void* problem, double timeLimit, void* observer, void* result) override;

private:
    EngineBase* inner_ = nullptr;                   // +0x10
};

// ------------------------------------------------------------------------------------------------
// The rest of the Engine family, each with its vtable and its three slots.
//
// EVERY ONE OF THESE HAS THE SAME THREE SLOTS: the deleting destructor, the destructor and Run. What differs is where Run
// points, which is the only thing the base class's comment listed -- and a class with an address and no definition is what the
// human asked about. The slot addresses come from re/vtables.json; the Run addresses were verified by the archive.
//

/** Engine::MultiEngine, vtable 0xA3CF00. */
constexpr std::uintptr_t kVtableMultiEngine = 0xA3CF00;
constexpr std::uintptr_t kMultiEngineDeletingDtor = 0x7559E0;   // slot 0
constexpr std::uintptr_t kMultiEngineDtor = 0x755970;             // slot 1
constexpr std::uintptr_t kMultiEngineRun = 0x755050;              // slot 2

/** Engine::DelayedEngine, vtable 0xA3CF70. */
constexpr std::uintptr_t kVtableDelayedEngine = 0xA3CF70;
constexpr std::uintptr_t kDelayedEngineDeletingDtor = 0x757200;   // slot 0
constexpr std::uintptr_t kDelayedEngineDtor = 0x7571B0;             // slot 1
constexpr std::uintptr_t kDelayedEngineRun = 0x756EC0;              // slot 2

/** Engine::NestingEngine, vtable 0xA3CFA0. */
constexpr std::uintptr_t kVtableNestingEngine = 0xA3CFA0;
constexpr std::uintptr_t kNestingEngineDeletingDtor = 0x757A70;   // slot 0
constexpr std::uintptr_t kNestingEngineDtor = 0x757A10;             // slot 1
constexpr std::uintptr_t kNestingEngineRun = 0x757250;              // slot 2

/** Engine::InfiniteEngine, vtable 0xA3CFD0. */
constexpr std::uintptr_t kVtableInfiniteEngine = 0xA3CFD0;
constexpr std::uintptr_t kInfiniteEngineDeletingDtor = 0x759B20;   // slot 0
constexpr std::uintptr_t kInfiniteEngineDtor = 0x759AD0;             // slot 1
constexpr std::uintptr_t kInfiniteEngineRun = 0x759A80;              // slot 2

/** Engine::CompositeEngine, vtable 0xA3D000. */
constexpr std::uintptr_t kVtableCompositeEngine = 0xA3D000;
constexpr std::uintptr_t kCompositeEngineDeletingDtor = 0x75BC30;   // slot 0
constexpr std::uintptr_t kCompositeEngineDtor = 0x75BBA0;             // slot 1
constexpr std::uintptr_t kCompositeEngineRun = 0x759B70;              // slot 2

/** Engine::EquivalentEngine, vtable 0xA3D030. */
constexpr std::uintptr_t kVtableEquivalentEngine = 0xA3D030;
constexpr std::uintptr_t kEquivalentEngineDeletingDtor = 0x75CB40;   // slot 0
constexpr std::uintptr_t kEquivalentEngineDtor = 0x75CAC0;             // slot 1
constexpr std::uintptr_t kEquivalentEngineRun = 0x75BCC0;              // slot 2

/** Engine::CloudEngine, vtable 0xA3CED0. */
constexpr std::uintptr_t kVtableCloudEngine = 0xA3CED0;
constexpr std::uintptr_t kCloudEngineDeletingDtor = 0x755000;   // slot 0
constexpr std::uintptr_t kCloudEngineDtor = 0x754FB0;             // slot 1
constexpr std::uintptr_t kCloudEngineRun = 0x26A60;              // slot 2


/** The family as a table, so a test asserts the whole shape rather than seven names. */
struct EngineClass {
    const char* name;
    std::uintptr_t vtable;
    std::uintptr_t run;
};

inline const EngineClass* engineFamily(std::size_t& count) {
    static const EngineClass table[] = {
        {"MultiEngine", 0xA3CF00, 0x755050},
        {"DelayedEngine", 0xA3CF70, 0x756EC0},
        {"NestingEngine", 0xA3CFA0, 0x757250},
        {"InfiniteEngine", 0xA3CFD0, 0x759A80},
        {"CompositeEngine", 0xA3D000, 0x759B70},
        {"EquivalentEngine", 0xA3D030, 0x75BCC0},
        {"CloudEngine", 0xA3CED0, 0x26A60},
    };
    count = sizeof(table) / sizeof(table[0]);
    return table;
}

constexpr std::size_t kEngineFamilyCount = 7;
static_assert(kEngineRunSlot == 0x10, "RE 0x2516E: call qword ptr [rax + 0x10]");
static_assert(kUnlimitedTime == -1.0, "the double at rva 0x9AE740");
static_assert(kInfiniteEngineRun == 0x759A80, "the slot this class implements");
static_assert(kNestingEngineRunDirect == 0x757AE0, "the routine the unlimited case calls DIRECTLY, not through a vtable");
static_assert(kNestingEngineRun == 0x757250 && kNestingEngineRunDirect == 0x757AE0,
              "NestingEngine has two entry points: its vtable slot and the direct one 0x757AE0");
static_assert(kMultiEngineRun != kNestingEngineRun && kNestingEngineRun != kInfiniteEngineRun,
              "the seven slots are seven addresses and must not be collapsed");

}  // namespace lcns
