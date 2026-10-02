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
constexpr std::uintptr_t kRunMultiEngine = 0x755050;
constexpr std::uintptr_t kRunDelayedEngine = 0x756EC0;
constexpr std::uintptr_t kRunNestingEngine = 0x757250;
constexpr std::uintptr_t kRunInfiniteEngine = 0x759A80;
constexpr std::uintptr_t kRunCompositeEngine = 0x759B70;
constexpr std::uintptr_t kRunEquivalentEngine = 0x75BCC0;
constexpr std::uintptr_t kRunCloudEngine = 0x26A60;

/** RE 0x757AE0, the routine the unlimited case calls -- NestingEngine's Run slot, reached directly rather than through a vtable. */
constexpr std::uintptr_t kNestingEngineRun = 0x757AE0;

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

static_assert(kEngineRunSlot == 0x10, "RE 0x2516E: call qword ptr [rax + 0x10]");
static_assert(kUnlimitedTime == -1.0, "the double at rva 0x9AE740");
static_assert(kRunInfiniteEngine == 0x759A80, "the slot this class implements");
static_assert(kNestingEngineRun == 0x757AE0, "the routine the unlimited case calls");
static_assert(kRunMultiEngine != kRunNestingEngine && kRunNestingEngine != kRunInfiniteEngine,
              "the seven slots are seven addresses and must not be collapsed");

}  // namespace lcns
