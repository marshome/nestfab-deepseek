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
 *
 * **AND THE BASE HAS DATA, WHICH THIS DECLARATION DID NOT.**
 *
 * Nothing in the image references an engine vtable, so there is no constructor to read the members off -- **but TWO engines' object registers read and write the SAME
 * ten offsets through registers that received `rcx`**:
 *
 *     DelayedEngine::run      through rdi (`756EEA mov rdi, rcx`)      +0x00 +0x10 +0x18 +0x20 +0x28 +0x30 +0x38 +0x40 +0x48 +0x50
 *     EquivalentEngine::run   through rsi (from the spill, `75BDD8`)   the same ten, and then +0x54 +0x58 +0x60
 *
 * **one contiguous range, 0x00 to 0x50**, with the widths the stores give: a dword at +0x00 and +0x30 and pointers elsewhere. **What each field MEANS is not
 * established**, so they are named by offset -- **and they live HERE rather than on a derived class, because the evidence that they exist is two derived classes agreeing
 * about them.** The initialisers are the values the bodies themselves write (0x756F1C, 0x756F27, 0x756F2F, 0x756F37, 0x756FCD, 0x756FD4, 0x756FDC).
 *
 * **AND WHAT IS *NOT* CLAIMED HERE MATTERS AS MUCH.** `+0x54`, `+0x58` and `+0x60` are `EquivalentEngine`'s alone in this measurement, **so they are not given to the
 * base**. **And an earlier version of this comment said FOUR engines agree on ELEVEN offsets, which was too strong**: `MultiEngine`'s extra offsets came from counting
 * EVERY register that ever received `rcx`, including `r15` after it took over from `r13`, so the count mixed registers. **Measured through the one register each prologue
 * establishes -- `r13` for `MultiEngine` and `r15` for `NestingEngine` -- each shows `+0x00` alone**, which is agreement and not contradiction, but it is much less than
 * was claimed. `re/g_engine_field_owners.py` is what does that one-register-at-a-time comparison, and `CompositeEngine` is left out of it because its prologue hands
 * `rcx` to several registers and then REUSES `rcx` as scratch, so a heuristic over "registers that ever received rcx" collects registers that received it and stopped
 * being it.
 */
class EngineBase {
public:
    virtual ~EngineBase() = default;

    /** Slot 2, RE 0x2516E. The default is pure, so a subclass must say what it does rather than inherit silence. */
    virtual void* run(const void* problem, double timeLimit, void* observer, void* result) = 0;

protected:
    /** **THE BASE IS A VPTR, A BYTE AND A DWORD -- AND THE ELEVEN MEMBERS THAT STOOD HERE WERE NOT THE BASE'S AT ALL.**
     *
     * **WHAT SETTLED IT WAS A CONSTRUCTOR PREAMBLE, WHICH IS THE EVIDENCE NINE ROUNDS OF READING `run` BODIES COULD NOT GIVE.** Two independent engine constructors
     * zero these two offsets **BEFORE** installing their vtable, which is what constructing a base sub-object looks like:
     *
     *      0x24AB0  EquivalentEngine     0x240D0  MultiEngine
     *      024ACA  byte  ptr [rax+8], 0          024100  byte  ptr [rax+8], 0
     *      024ACE  dword ptr [rax+0xc], 0        024104  dword ptr [rax+0xc], 0
     *      024ADC  qword ptr [rbx], rax          02411A  qword ptr [rbx], rax      ; the vtable, AFTER
     *      024AE2  qword ptr [rbx+0x10], rax     024116  dword ptr [rbx+0x10], r13d   ; **the first own member**
     *
     * **AND `0x23E70` (`NestingEngine`) WRITES THE SAME TWO OFFSETS WITH THE VALUE 1** -- `023F93 dword ptr [rax + 8], 1` and `023F9A dword ptr [rax + 0xc], 1` --
     * **which is why they are flags or counters and not a pointer.**
     *
     * **SO THE BASE ENDS AT 0x10 AND THE DERIVED CLASSES START THERE.** The declaration that stood here held eleven members from +0x00 to +0x50, **all of them eight bytes
     * lower than the instruction that uses each one**, and `static_assert(sizeof(EngineBase) == 0x60)` was pinning that wrong layout. **What that declaration actually
     * captured was an agreement between FOUR SIBLINGS about their OWN shared layout** -- `InfiniteEngine`, `MultiEngine`, `DelayedEngine`, `NestingEngine` and
     * `CompositeEngine` all touch +0x10 through +0x50 -- **and an agreement between siblings is not an inherited member.** Which class those offsets belong to is the next
     * question, and it is asked in the note on `EquivalentEngine` below rather than answered here. */
    std::uint8_t at08 = 0;         // +0x08, RE 0x024ACA `mov byte ptr [rax + 8], 0` and 0x023F93 `dword ptr [rax + 8], 1`
    std::uint32_t at0C = 0;        // +0x0C, RE 0x024ACE `mov dword ptr [rax + 0xc], 0` and 0x023F9A `dword ptr [rax + 0xc], 1`
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

    /** **"THE CLASS HAS NO MEMBER" WAS TRUE OF ITS `run` AND FALSE OF THE CLASS.** RE 0x24FD0, 209 bytes, and it ALLOCATES AND PLACES THREE:
     *
     *      024FD7  mov rsi, rcx                            ; **rcx is a DESTINATION for this constructor too**
     *      024FDA  mov ecx, 0x30 / 024FEE call 0x998500   ; **allocate 0x30**
     *      024FF9  mov rbx, rax                            ; the object is the allocation
     *      024FFC  mov byte  ptr [rax + 8], 0              ; the base's byte, BEFORE the vtable
     *      025006  mov dword ptr [rax + 0xc], 0            ; the base's dword, likewise
     *      025014  mov qword ptr [rbx], rax                ; its vtable
     *      02501A  mov qword ptr [rbx + 0x10], rax         ; **+0x10, a shared_ptr CONTROL BLOCK**
     *      025025  mov qword ptr [rbx + 0x18], rax         ; **+0x18, its pointer**
     *      02502B  lock add dword ptr [rax + 8], 1         ; **the use count, atomically**
     *      025030  movsd qword ptr [rbx + 0x20], xmm2      ; **+0x20, a DOUBLE -- the third argument**
     *
     *  **AND THE SAME THREE WORDS AT THE SAME THREE OFFSETS ARE WHAT `EquivalentEngine`'S CONSTRUCTOR BUILDS** (`0x24AB0`, allocation 0x30, `024AE2`, `024AED`, `024AF8`).
     *  **So `+0x10`, `+0x18` and `+0x20` are a SHARED THREE-WORD LAYOUT rather than one class's fields** -- and **this class's `run` (0x759A80, 80 bytes) never reads them
     *  while `EquivalentEngine`'s does.**
     *
     *  **WHAT THAT MEANS IS NOT DECIDED HERE**: it points at either a common base below `EngineBase` (0x10 through 0x28) or the two classes being instantiations of one
     *  template, **and the two candidates are told apart by reading `EquivalentEngine`'s `run` against this one rather than by guessing.**
     *
     *  **AND THE `run` NOTE THAT STOOD HERE WAS ABOUT THE BODY, WHICH IS STILL RIGHT**: RE 0x759A80 reads `this` only to return it, and the engine it delegates to comes
     *  from the problem's +0x10. **The mistake was concluding a fact about the CLASS from a fact about one METHOD.** */
    void* run(const void* problem, double timeLimit, void* observer, void* result) override;

private:
    void* control10 = nullptr;         // +0x10, RE 0x02501A -- a std::shared_ptr control block
    void* pointed18 = nullptr;         // +0x18, RE 0x025025 -- and 0x02502B increments its +0x08 atomically
    double at20 = 0.0;                 // +0x20, RE 0x025030 `movsd qword ptr [rbx + 0x20], xmm2`
};

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

    /** **ITS CONSTRUCTOR PLACES TEN OFFSETS AND THEY ARE THE CLASS'S OWN LAYOUT.** RE 0x240D0, 431 bytes, `0240E7 mov ecx, 0x48 / call 0x998500` -- **so the object is
     *  0x48 bytes: 0x10 of `EngineBase` and 0x38 of this class.**
     *
     *      024100  mov byte  ptr [rax + 8], 0     ; **the base's byte, BEFORE the vtable -- see `EngineBase`'s note**
     *      024104  mov dword ptr [rax + 0xc], 0   ; **the base's dword, likewise**
     *      02411A  mov qword ptr [rbx], rax       ; its own vtable
     *      024116  mov dword ptr [rbx + 0x10], r13d   ; **+0x10, the constructor's third argument, 32 bits**
     *      024124  mov byte  ptr [rbx + 0x14], r12b   ; **+0x14, its fourth argument, ONE BYTE**
     *      024226  mov qword ptr [rax + 0x18]         ; +0x18
     *      024128  mov dword ptr [rbx + 0x20], 0      ; +0x20
     *      02412F  mov qword ptr [rbx + 0x28], 0      ; +0x28
     *      02413F  mov qword ptr [rbx + 0x30], r8     ; +0x30 and +0x38 take the same register
     *      024143  mov qword ptr [rbx + 0x38], r8
     *      024137  mov qword ptr [rbx + 0x40], 0      ; +0x40
     *
     *  **AND `+0x10` AND `+0x18` ARE SHARED WITH `NestingEngine` AND `CloudEngine`, WHILE `+0x20` THROUGH `+0x50` ARE `CloudEngine`'S ALONE** (`re/g_engine_ctor_full.py`).
     *  **So `+0x10` and `+0x18` are declared on the base of this family or repeated in each; nothing above `+0x18` is shown to be shared by more than one class.** **What each
     *  field MEANS is not established**, so they carry their offsets -- **except the two the constructor's own arguments reach, which say so.** */
    void* run(const void* problem, double timeLimit, void* observer, void* result) override;

private:
    std::int32_t at10 = 0;             // +0x10, RE 0x024116 `mov dword ptr [rbx + 0x10], r13d` -- the third argument
    std::uint8_t at14 = 0;             // +0x14, RE 0x024124 `mov byte ptr [rbx + 0x14], r12b` -- the fourth argument, narrowed to a byte
    void* at18 = nullptr;              // +0x18, RE 0x024226 -- SHARED with NestingEngine and CloudEngine
    std::int32_t at20 = 0;             // +0x20, RE 0x024128 is a DWORD store
    void* at28 = nullptr;              // +0x28, RE 0x02412F
    void* at30 = nullptr;              // +0x30, RE 0x02413F
    void* at38 = nullptr;              // +0x38, RE 0x024143 -- the same register as +0x30
    void* at40 = nullptr;              // +0x40, RE 0x024137
};

/** Engine::DelayedEngine, Run at 0x756EC0, vtable 0xA3CF70.
 *
 *  Not read.
 */
class DelayedEngine : public EngineBase {
public:

    DelayedEngine() = default;

    /** **LIKE `NestingEngine`, ITS CONSTRUCTOR ALLOCATES THE OBJECT AND HANDS IT BACK THROUGH THE FIRST ARGUMENT.** RE 0x24B80, 192 bytes:
     *
     *      024B87  mov rsi, rcx                            ; **rcx is a DESTINATION, not `this`**
     *      024B8A  mov ecx, 0x28 / 024B98 call 0x998500   ; **allocate 0x28 -- the SMALLEST of the three engines**
     *      024BA3  mov rbx, rax                            ; the object is the allocation
     *      024BA6  mov byte  ptr [rax + 8], 0              ; the base's byte, BEFORE the vtable
     *      024BAA  mov dword ptr [rax + 0xc], 0            ; the base's dword, likewise
     *      024BB8  mov qword ptr [rbx], rax                ; its vtable
     *      024BBB  mov rax, qword ptr [rdi]
     *      024BBE  mov qword ptr [rbx + 0x10], rax         ; **+0x10, a shared_ptr CONTROL BLOCK**
     *      024BC9  mov qword ptr [rbx + 0x18], rax         ; **+0x18, its pointer**
     *      024BCF  lock add dword ptr [rax + 8], 1         ; **the use count, atomically**
     *      024BD4  movsd qword ptr [rbx + 0x20], xmm2      ; **+0x20, a DOUBLE -- the fifth argument**
     *      024BDE  mov qword ptr [rsi], rbx                ; **the object written to where rcx points**
     *      024C0A  mov qword ptr [rsi + 8], rax            ; and a second 0x18-byte object the constructor allocates at 0x24BD9
     *
     *  **AND `+0x20` IS A `double` HERE WHILE `MultiEngine` PUTS A DWORD IN ITS `+0x20`** -- so the two are not one layout, **which the allocations 0x28 and 0x48 already said
     *  and this confirms field by field.**
     *
     *  **THE DECLARATION THAT STOOD HERE WAS READ FROM `run` (0x756EC0, 750 bytes) AND GAVE THIS CLASS ELEVEN MEMBERS FROM A BODY WHOSE OBJECT REGISTER WAS NOT `this`.** The
     *  constructor gives three. **Reading a `run` body cannot separate a class's own members from a sub-object's, and the constructor can.** */
    void* run(const void* problem, double timeLimit, void* observer, void* result) override;

private:
    void* control10 = nullptr;         // +0x10, RE 0x024BBE -- a std::shared_ptr control block
    void* pointed18 = nullptr;         // +0x18, RE 0x024BC9 -- and 0x24BCF increments its +0x08 atomically
    double at20 = 0.0;                 // +0x20, RE 0x024BD4 `movsd qword ptr [rbx + 0x20], xmm2`
};

/** Engine::NestingEngine, Run at 0x757250, vtable 0xA3CFA0.
 *
 *  Not read.
 */
class NestingEngine : public EngineBase {
public:

    NestingEngine() = default;

    /** **ITS CONSTRUCTOR IS A FACTORY: it allocates the object itself and returns it through the FIRST ARGUMENT.** RE 0x23E70, 595 bytes:
     *
     *      023E84  mov rdi, rcx                  ; **rcx is a DESTINATION, not `this`**
     *      023E87  mov ecx, 0x78 / 023E94 call 0x998500   ; **allocate 0x78**
     *      023E9E  mov rbx, rax                  ; **the object is the allocation**
     *      023EA1  mov byte  ptr [rax + 8], 0    ; **the base's byte, before the vtable**
     *      023EA5  mov dword ptr [rax + 0xc], 0  ; **the base's dword, likewise**
     *      023EB8  mov qword ptr [rbx], rax      ; its vtable
     *      023EBD  mov dword ptr [rbx + 0x10], r12d   ; **+0x10 = the THIRD argument (r8d)**
     *      023ECB  mov dword ptr [rbx + 0x18], eax    ; +0x18 = a dword out of the source object
     *      023ED2  mov byte  ptr [rbx + 0x1c], al     ; +0x1C = [src + 4]
     *      023ED9  mov byte  ptr [rbx + 0x1d], al     ; +0x1D = [src + 5]
     *      023EC1  movlpd qword ptr [rbx + 0x28], xmm0  ; **+0x28 = a DOUBLE out of [src + 0x10]**
     *      023EC6  movhpd qword ptr [rbx + 0x30], xmm0  ; **+0x30 = a DOUBLE out of [src + 0x18]**
     *
     *  **AND `023E87 mov ecx, 0x78` IS THE OBJECT'S SIZE** -- 0x78, against `MultiEngine`'s 0x48 and `DelayedEngine`'s 0x28 -- **so these three classes are NOT one layout
     *  and the "shared range" reading was wrong in a way the sizes make obvious.**
     *
     *  **WHAT EACH FIELD MEANS IS NOT ESTABLISHED**, so they carry their offsets; **the two the source object feeds (+0x28 and +0x30) are doubles and the two bytes at +0x1C
     *  and +0x1D come from a packed struct of flags.** */
    void* run(const void* problem, double timeLimit, void* observer, void* result) override;

private:
    std::int32_t at10 = 0;             // +0x10, RE 0x023EBD -- the constructor's third argument
    std::int32_t at18 = 0;             // +0x18, RE 0x023ECB `mov dword ptr [rbx + 0x18], eax`
    std::uint8_t at1C = 0;             // +0x1C, RE 0x023ED2 -- a byte of a packed flag set
    std::uint8_t at1D = 0;             // +0x1D, RE 0x023ED9
    double at28 = 0.0;                 // +0x28, RE 0x023EC1 `movlpd qword ptr [rbx + 0x28], xmm0`
    double at30 = 0.0;                 // +0x30, RE 0x023EC6 `movhpd qword ptr [rbx + 0x30], xmm0`
};

// CompositeEngine is declared in lcns/engines_composite.hpp, which carries the evidence for it.

/** Engine::EquivalentEngine, Run at 0x75BCC0, vtable 0xA3D030.
 *
 *  Not read.
 */
class EquivalentEngine : public EngineBase {
public:

    EquivalentEngine() = default;

    /** **THIS IS THE ONLY ONE OF THE SIX THAT REACHES PAST THE BASE'S RANGE, AND THE THREE OFFSETS IT REACHES SETTLE WHERE THE BASE ENDS.**
     *
     *  Every engine's own object register was read to the end of its body for offsets above `+0x50` (`re/g_engine_derived_fields.py`), and the result is:
     *
     *      InfiniteEngine     -- none --        MultiEngine        -- none --        DelayedEngine      -- none --
     *      NestingEngine      -- none --        CompositeEngine    -- none --        **EquivalentEngine   +0x54 +0x58 +0x60**
     *
     *  **and `+0x58` is exactly the first eight-byte boundary after the base's nine pointers.** So the reading that fits all six is:
     *
     *      EngineBase        0x00 .. 0x53   the eleven members below, the last a DWORD at +0x54
     *                        -- padding to 0x58 --
     *      EquivalentEngine  0x58, 0x60     this class's own two pointers
     *
     *  **and that is why the two pointers here start at +0x58 and not at +0x50.** **The three reads with their instructions:**
     *
     *      75C71E  mov eax, dword ptr [rsi + 0x54]    ; the base's last member, read as a DWORD
     *      75C72C  mov r15, qword ptr [rsi + 0x58]    ; **this class's first own member**
     *      75C703  mov rdi, qword ptr [rsi + 0x60]
     *
     *  **and `rsi` is the object** -- `75BDD8 mov rsi, qword ptr [rsp + 0x210]`, which is where this function reloads the `rcx` it spilled at `75BCDB`. */
    void* run(const void* problem, double timeLimit, void* observer, void* result) override;

private:
    /** **THIS CLASS'S OWN AREA STARTS AT +0x10, AND IT HOLDS A `std::shared_ptr`.** RE 0x24AB0, 190 bytes, and its allocation is `024ABA mov ecx, 0x30` -- **so the whole
     *  object is 0x30 bytes: 0x10 of `EngineBase` and 0x20 of this class.**
     *
     *      024ADF  mov rax, qword ptr [rdi]        ; the source shared_ptr
     *      024AE2  mov qword ptr [rbx + 0x10], rax ; **+0x10, a CONTROL BLOCK**
     *      024AE6  mov rax, qword ptr [rdi + 8]
     *      024AED  mov qword ptr [rbx + 0x18], rax ; **+0x18, the pointer**
     *      024AF3  lock add dword ptr [rax + 8], 1 ; **an ATOMIC INCREMENT eight bytes into what +0x18 points at**
     *      024AF8  mov qword ptr [rbx + 0x20], 0   ; +0x20
     *
     *  **THE `lock add` IS WHAT IDENTIFIES IT**: a `std::shared_ptr` control block's use count, incremented atomically on copy. **And `RE 0x75C72C` and `0x75C703` read
     *  +0x58 and +0x60 as qwords, `RE 0x75C71E` reads +0x54 as a dword -- all three INSIDE this class's own area and none of them the base's.**
     *
     *  **AND WHAT +0x28 THROUGH +0x50 ARE IS NOT ESTABLISHED HERE.** `InfiniteEngine`, `MultiEngine`, `DelayedEngine`, `NestingEngine` and `CompositeEngine` all touch
     *  that range in their `run` bodies, **so it is a shared layout -- but the five constructors that would say WHOSE have not all been read**, and reading a `run` body
     *  cannot tell an inherited member from a sibling's identical own one. **This class declares only what its constructor places**, which is the three words above. */
    void* control10 = nullptr;         // +0x10, RE 0x24AE2 -- a std::shared_ptr control block
    void* pointed18 = nullptr;         // +0x18, RE 0x24AED -- and 0x24AF3 increments its +0x08 atomically
    void* at20 = nullptr;              // +0x20, RE 0x24AF8 zeroes it
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
