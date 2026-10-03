# -*- coding: utf-8 -*-
"""Wire `SetLocalMaximumIterations` end to end: the body, the signature, the wrapper, and the table's status.

**THE READING WAS ALREADY DONE AND THIS IS THE WIRING**, which `re/g_forwarding_gap.py` says is missing for 39 of the 47 forwarded ordinals.

    SetLocalMaximumIterations   ordinal 84/85, rva 0x0D400, 36 bytes, **2 register arguments** (re/exports_table.md)
        0D400  push rsi / push rbx / sub rsp, 0x28
        0D406  mov rsi, rcx                  ; **ARGUMENT 1 IS A POINTER -- the Order's address**
        0D409  mov ebx, edx                  ; argument 2, the value
        0D417  mov dword [rsi + 0x1fc], ebx  ; **AND THAT IS THE WHOLE BODY**
        0D423  ret

**AND THE GENERATED WRAPPER TAKES `Order` BY VALUE.** `extern "C" void SetLocalMaximumIterations(Order, int)` cannot pass an address, so wiring it without
changing the signature would pass a COPY where the module writes through a pointer. **The inferred signature was the guess and `mov rsi, rcx` is the measurement.**

**AND THE BODY'S CONTRACT IS ONE STORE AND NO CLAMP.** `0xD3C7 test ebx, ebx` and `0xD3D2 cmova` belong to `SetLocalMaximumThreads` in the function next door;
this one is 36 bytes with nothing but the store, so the implementation must not add a clamp that the module does not have.
"""
import io
import sys

CARRIER = r"D:\Nesting\nestfab\lcns\include\lcns\dll_layout.hpp"
HEADER = r"D:\Nesting\nestfab\lcns\include\lcns\exports_impl.hpp"
IMPL = r"D:\Nesting\nestfab\lcns\src\exports_impl.cpp"
API = r"D:\Nesting\nestfab\lcns\src\api_exports.cpp"

PATCHES = [
    (CARRIER,
     "    std::uint32_t maxThreads;   // +0x1F8, RE 0xD3D5 and RE 0xD3E7\n    unsigned char opaque1FC[0x04];\n",
     "    std::uint32_t maxThreads;   // +0x1F8, RE 0xD3D5 and RE 0xD3E7: mov dword [rsi], eax\n"
     "    std::uint32_t maxIterations;  // +0x1FC, RE 0xD417: mov dword [rsi + 0x1fc], ebx -- SetLocalMaximumIterations\n",
     "dll_layout.hpp"),

    (HEADER,
     "void setLocalMaximumThreads(void* object, int value);\n",
     "void setLocalMaximumThreads(void* object, int value);\n"
     "/** RE 0x0D400, 36 bytes, and the body is one store: `mov dword [rsi + 0x1fc], ebx` at 0x0D417. **The export's own name is the oracle for the field** --\n"
     " *  the module calls it `SetLocalMaximumIterations` and it writes exactly one offset, which is `Order`'s `maxIterations`. **No clamp**: 0xD3C7's\n"
     " *  `test ebx, ebx` and 0xD3D2's `cmova` are in the function next door. */\n"
     "void setLocalMaximumIterations(void* object, int value);\n",
     "exports_impl.hpp"),

    (IMPL,
     "void setLocalMaximumThreads(void* object, int value) {\n"
     "    static_cast<LocalEngineCarrier*>(object)->maxThreads = clampMaximumThreads(platformConcurrency(), value);\n}",
     "void setLocalMaximumThreads(void* object, int value) {\n"
     "    static_cast<LocalEngineCarrier*>(object)->maxThreads = clampMaximumThreads(platformConcurrency(), value);\n}\n\n"
     "void setLocalMaximumIterations(void* object, int value) {\n"
     "    // RE 0x0D417: mov dword ptr [rsi + 0x1fc], ebx.\n"
     "    // **AND NOTHING ELSE**: 0x0D400 is 36 bytes and every other instruction in it is the prologue or the return, so a clamp here would be a behaviour the\n"
     "    // module does not have. The thread count beside it IS clamped, which is why the two are easy to confuse.\n"
     "    static_cast<LocalEngineCarrier*>(object)->maxIterations = static_cast<std::uint32_t>(value);\n}",
     "exports_impl.cpp"),

    (API,
     '// ordinal 84/85  rva 0x0D400  36 bytes\n'
     '// signature from the inferred typed table\n'
     'extern "C" void SetLocalMaximumIterations(Order, int) {\n'
     '    lcns::dll::exports::notReversed(40u);\n}',
     '// ordinal 84/85  rva 0x0D400  36 bytes\n'
     '// **AND THE FIRST PARAMETER IS A POINTER, NOT A VALUE.** The inferred typed table said `(Order, int)`, while 0x0D406 is `mov rsi, rcx` and 0x0D417 writes\n'
     '// `dword [rsi + 0x1fc]` THROUGH it -- so rcx holds the ADDRESS of the Order. re/exports_table.md counts 2 register arguments, which is rcx and edx.\n'
     '// **The inferred signature was the guess and the instruction is the measurement.**\n'
     '//\n'
     '// **AND THIS WRAPPER DISPATCHES**: it calls the implementation in exports_impl.cpp, and kForwarding already names it at ordinal 84. Before this change the\n'
     '// list claimed the forward and the wrapper reported the ordinal instead, which is the gap re/g_forwarding_gap.py counts for 39 of 47.\n'
     'extern "C" void SetLocalMaximumIterations(Order* order, int iterations) {\n'
     '    lcns::dll::exports::impl::setLocalMaximumIterations(static_cast<void*>(order), iterations);\n}',
     "api_exports.cpp"),
]


def main():
    ok = True
    for path, old, new, label in PATCHES:
        text = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        if new.split("\n")[0] in text and label != "exports_impl.cpp":
            print("   %-18s already patched" % label)
            continue
        if old not in text:
            print("   REFUSING: %-18s anchor not found" % label)
            ok = False
            continue
        io.open(path, "w", encoding="utf-8", newline="\n").write(text.replace(old, new, 1))
        print("   %-18s patched" % label)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
