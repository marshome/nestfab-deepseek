// lcns/src/engines.cpp -- InfiniteEngine::run, the one Engine subclass whose body has been read.
#include "lcns/engines.hpp"

namespace lcns {

void* InfiniteEngine::run(const void* /*problem*/, double timeLimit, void*, void* result) {
    // The routine's own content is the DECISION, and it lives in dispatch() so a test can drive both branches without an engine to call.
    // Here the two branches are the module's: the unlimited case enters the nesting engine at 0x757AE0, and the other delegates to the
    // inner engine's Run slot. Neither of those is implemented yet, so this says so rather than pretending.
    //
    // RE 0x759A80's two arms:
    //     0x759A94  mov r9, [rsp + 0x60] / 0x759A99 call 0x757AE0      ; unlimited
    //     0x759AB0  mov rdx, [rdx + 0x10] / 0x759AC4 call [rax + 0x10] ; otherwise, through the inner engine's vtable
    return dispatch(timeLimit, result,
                    [](void* r) -> void* {
                        (void)r;                      // the buffer would be filled by RE 0x757AE0, which has not been read
                        return nullptr;               // so the unlimited arm is RECORDED and not implemented, and returns nothing
                    },
                    [](EngineBase* inner, void* r) -> void* {
                        (void)inner;
                        return r;                    // the delegating arm returns the buffer, which is what 0x759AC7 does
                    });
}

}  // namespace lcns
