// lcns/src/engines.cpp -- InfiniteEngine::run, and the six engines whose bodies have not been read.
#include "lcns/engines.hpp"

namespace lcns {

// RE 0x759A80, the whole 80 bytes. It is a DECISION and nothing else:
//
//     0x759A8D  mov rbx, rcx              ; `this`, and rbx is how the result comes back
//     0x759A85  ucomisd xmm3, [0x9AE740]  ; the time limit against -1.0
//     0x759A90  jp  0x759AB0              ; A NaN TAKES THE DELEGATING PATH
//     0x759A92  jne 0x759AB0              ; and so does any limit that is not exactly -1.0
//     0x759A94  mov r9, [rsp + 0x60]      ; the stack argument
//     0x759A99  call 0x757AE0             ; the NESTING ENGINE'S ENTRY, called directly rather than through a vtable
//     0x759A9E  mov rax, rbx / ret        ; the result
//     0x759AB0  mov rdx, [rdx + 0x10]     ; OTHERWISE: the engine found at +0x10 of THE PROBLEM -- **`rdx` is the SECOND argument, which this
//                                         ;   slot receives as `problem`, NOT as `this`**
//     0x759AB9  mov rax, [rdx]            ; that engine's vtable
//     0x759ABC  mov [rsp + 0x20], rcx     ; the stack argument again
//     0x759AC1  mov rcx, rbx              ; ITS `this` is the RESULT BUFFER, so the callee writes the result in place
//     0x759AC4  call qword ptr [rax + 0x10]   ; ITS Run, slot 2
//
// **THE EARLIER READING WAS WRONG AND THE CLASS CARRIED IT FOR SEVERAL ROUNDS.** `[rdx + 0x10]` was recorded as "the inner engine at
// this + 0x10", and in slot 2 `rdx` is the problem. That produced an `inner_` member and a `setInner` that no instruction supports, and a
// `dispatch` template whose delegate had to be passed in because there was nothing in the object to delegate to.
void* InfiniteEngine::run(const void* problem, double timeLimit, void*, void* result) {
    if (timeLimit == kUnlimitedTime) {
        // RE 0x759A99. 0x757AE0 is the nesting engine's entry and its body has not been read, so this arm is RECORDED and returns the buffer
        // rather than pretending to have nested anything.
        return result;
    }
    // RE 0x759AB0: the engine lives at +0x10 of the PROBLEM, and is called through its own vtable with the result buffer as its `this`.
    const auto* holder = static_cast<const ProblemView*>(problem);
    if (holder == nullptr || holder->engine == nullptr) {
        return result;
    }
    return holder->engine->run(problem, timeLimit, nullptr, result);
}

// The other six. Each is UNREAD beyond what its declaration records, and each says so at its own body rather than in a comment elsewhere
// -- a stub that returns nullptr silently would be indistinguishable from an engine that does nothing, which is the same class of
// mistake as a constant standing in for a class.

void* MultiEngine::run(const void*, double, void*, void* result) {
    return result;      // RE 0x755050 is 3795 bytes and NOT READ; the buffer is what every Run in this family returns
}

void* DelayedEngine::run(const void*, double, void*, void* result) {
    return result;      // RE 0x756EC0 is 750 bytes and NOT READ
}

void* NestingEngine::run(const void*, double, void*, void* result) {
    return result;      // RE 0x757250 is 1975 bytes and NOT READ; 0x757AE0 is a second entry to this class
}

void* CompositeEngine::run(const void*, double, void*, void* result) {
    // RE 0x759B70 is 8230 bytes and read far enough to establish what it does NOT do: it calls no other engine's Run, and it walks a
    // container of 16 byte records reached through its second argument's +0x10 and +0x18, accumulating into locals.
    return result;
}

void* EquivalentEngine::run(const void*, double, void*, void* result) {
    return result;      // RE 0x75BCC0 is 3569 bytes and NOT READ
}

void* CloudEngine::run(const void*, double, void*, void* result) {
    return result;      // RE 0x26A60 is 2284 bytes and NOT READ; the cloud gate is 0x2AB0, a different function
}

}  // namespace lcns
