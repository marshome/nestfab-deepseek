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

#include "lcns/engines_composite.hpp"
// **`recovery.hpp` IS INCLUDED SO THE RECOVERY MARKER CAN BE A REAL ONE.** `check_recovery.py` matches the literal shape `LCNS_*(id)`, so a comment is not a
// mark -- **and a decision recorded as a comment is invisible to the check that exists to keep decisions visible.**
#include "lcns/recovery.hpp"

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
 *
 * **AND THE SEVEN TABLES MEASURE THE BASE'S SURFACE: ONE VIRTUAL, AND IT IS `run`.** Every concrete engine has exactly three slots --
 *
 *      slot 0   70 to 137 bytes     the deleting destructor
 *      slot 1   71 to 129 bytes     the destructor
 *      slot 2   80 to 15430 bytes   `run`, and its ADDRESS DIFFERS IN ALL SEVEN
 *
 * -- and those counts are MEASURED rather than estimated: `CloudEngine` is 70, 71 and 15430, `InfiniteEngine` is 71, 76 and 80, and
 * `CompositeEngine` is 137, 129 and 8230. **So the base's whole surface is that one method**, and it is abstract because every derived class
 * implements it. There is no vtable for `Engine::Engine` ITSELF in re/vtables.json because an abstract base has no instantiated table, which is the
 * same reason the whole base layer was missing from this tree.
 */class EngineBase {
public:
    virtual ~EngineBase() = default;

    /** Slot 2, RE 0x2516E. The default is pure, so a subclass must say what it does rather than inherit silence. */
    virtual void* run(const void* problem, double timeLimit, void* observer, void* result) = 0;
};

/** RE vtable 0xA3CFD0, THREE slots. Slot 0 is the deleting destructor 0x759B20, slot 1 the destructor 0x759AD0, and slot 2 is `run` at 0x759A80, 80 bytes.
 *  **The slot-2 address DIFFERS IN ALL SEVEN ENGINES**, which is why slot 2 is the class's one virtual and the base is abstract. */
/** What RE 0x759AB0 reads out of the SECOND argument: the engine it delegates to sits at +0x10 of the problem. */
struct ProblemView {
    std::byte header[0x10]{};
    EngineBase* engine = nullptr;      // RE 0x759AB0: mov rdx, [rdx + 0x10]
};

class InfiniteEngine : public EngineBase {
public:
    InfiniteEngine() = default;

    /** **THE CLASS HAS NO MEMBER THAT AN INSTRUCTION SUPPORTS.** RE 0x759A80 reads `this` only in order to return it -- `mov rbx, rcx` at
     *  0x759A8D and `mov rax, rbx` at 0x759A9E -- and the engine it delegates to comes from the PROBLEM's +0x10, because in slot 2 `rdx` is
     *  the second argument and NOT `this`. An earlier `inner_` member at +0x10 was a misreading of that, and `setInner`, `inner` and the
     *  `dispatch` template existed only to serve it; they are deleted rather than left looking recovered.
     *
     *  The class's whole content is the DECISION: unlimited time enters the nesting engine at 0x757AE0 directly, and anything else -- a NaN
     *  included, because the branch is a `jp` -- goes through the engine the problem carries. */
    void* run(const void* problem, double timeLimit, void* observer, void* result) override;
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
// ------------------------------------------------------------------------------------------------
// THE OTHER SIX, DECLARED.
//
// Each is an Engine with the same three slots and the same Run signature, which is everything the RTTI and the call site
// establish. **Members are not invented**: the vtable says how many virtuals a class has and nothing about its data, so a
// declaration here carries what is known and the comment says which body remains unread.
//
// A constant named kCompositeEngineRun is NOT a class, and a header that gives six classes an address and declares none of
// them invites exactly that misreading -- which happened, and is why these exist.

/** Engine::MultiEngine, Run at 0x755050, vtable 0xA3CF00.
 *
 *  Not read.
 */
class MultiEngine : public EngineBase {
public:

    MultiEngine() = default;

    void* run(const void* problem, double timeLimit, void* observer, void* result) override;
};

/** Engine::DelayedEngine, Run at 0x756EC0, vtable 0xA3CF70.
 *
 *  Not read.
 */
class DelayedEngine : public EngineBase {
public:

    DelayedEngine() = default;

    void* run(const void* problem, double timeLimit, void* observer, void* result) override;
};

/** Engine::NestingEngine, Run at 0x757250, vtable 0xA3CFA0.
 *
 *  Not read.
 */
class NestingEngine : public EngineBase {
public:

    NestingEngine() = default;

    void* run(const void* problem, double timeLimit, void* observer, void* result) override;
};

// CompositeEngine is declared in lcns/engines_composite.hpp, which carries the evidence for it.

/** Engine::EquivalentEngine, Run at 0x75BCC0, vtable 0xA3D030.
 *
 *  Not read.
 */
class EquivalentEngine : public EngineBase {
public:

    EquivalentEngine() = default;

    void* run(const void* problem, double timeLimit, void* observer, void* result) override;
};

/** Engine::CloudEngine, Run at 0x26A60, vtable 0xA3CED0.
 *
 *  **EXEMPT FROM REVERSE ENGINEERING BY THE HUMAN'S INSTRUCTION AT ROUND 120: "CloudEngine 不需要逆向，其他的engine都需要".** So the `Not read` that stood here was a
 *  TODO and is now a DECISION, recorded as one -- **the difference matters, because a TODO invites a later round to spend effort on it and a decision does not.**
 *
 *  **AND THE EXEMPTION IS FOR THIS SHELL AND NOT FOR `lcns::CloudEngine`.** The cloud implementation in `lcns/cloud.hpp` is a different class in a different
 *  namespace: it wraps an `HttpClient` and a `Config` and returns a `CloudResult`, while this is the ABI shell with a `run` that matches `EngineBase`.
 *  **Two classes called `CloudEngine` is worth knowing when searching**, and `re/g_one_definition.py` reports them as two definitions rather than one.
 *
 *  `LCNS_NOT_REVERSED` records it in the same form as every other un-reversed subject, so `grep -rn LCNS_NOT_REVERSED` finds this one too.
 */
class CloudEngine : public EngineBase {
public:

    CloudEngine() = default;

    // NOT REVERSED BY DECISION -- the human's instruction at round 120: "CloudEngine 不需要逆向，其他的engine都需要".
    LCNS_NOT_REVERSED(engine.cloud);

    void* run(const void* problem, double timeLimit, void* observer, void* result) override;
};


static_assert(kEngineRunSlot == 0x10, "RE 0x2516E: call qword ptr [rax + 0x10]");
static_assert(kUnlimitedTime == -1.0, "the double at rva 0x9AE740");
static_assert(kInfiniteEngineRun == 0x759A80, "the slot this class implements");
static_assert(kNestingEngineRunDirect == 0x757AE0, "the routine the unlimited case calls DIRECTLY, not through a vtable");
static_assert(kNestingEngineRun == 0x757250 && kNestingEngineRunDirect == 0x757AE0,
              "NestingEngine has two entry points: its vtable slot and the direct one 0x757AE0");
static_assert(kMultiEngineRun != kNestingEngineRun && kNestingEngineRun != kInfiniteEngineRun,
              "the seven slots are seven addresses and must not be collapsed");

}  // namespace lcns
