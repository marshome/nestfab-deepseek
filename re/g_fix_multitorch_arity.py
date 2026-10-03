# -*- coding: utf-8 -*-
"""Give `setMultiTorchCuttingPreference_0F130` its THIRD parameter, which the module reads and the implementation did not have.

**THE BODY IS THREE STORES AND THEY USE ALL THREE REGISTERS:**

    00F13D  mov r12d, edx                 ; argument 2
    00F140  mov ebp, r8d                  ; **argument 3, which the implementation had no parameter for**
    00F223  test ebp, ebp
    00F225  mov byte [rsi + 0x98], 1      ; the "given" flag, unconditionally
    00F22C  setg byte [rsi + 0xa0]        ; the "positive" flag, FROM ARGUMENT 3
    00F233  mov dword [rsi + 0x9c], r12d  ; the value, from argument 2

**AND THE IMPLEMENTATION'S THREE FIELD OFFSETS ARE ALL CORRECT** -- `+0x98`, `+0xA0`, `+0x9C` -- so the only thing wrong is that it derived the positive flag
from `value > 0` instead of from a parameter of its own. **That is a real behavioural difference**: a caller passing `value = 5, flag = 0` gets `Positive = 0`
from the module and `Positive = 1` from this port.

**AND `ebp` IS NEVER STORED**, so the third argument is not a field: it is read, tested and discarded, which is why the offset-based reading of this function
looked complete.
"""
import io
import os
import sys

ROOT = r"D:\Nesting\nestfab"
HEADER = os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp")
IMPL = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")
API = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")

HEADER_OLD = "void setMultiTorchCuttingPreference_0F130(void* order, int value);"
HEADER_NEW = ("/** RE 0xF130, 388 bytes. **THE POSITIVE FLAG COMES FROM A THIRD PARAMETER, NOT FROM THE VALUE.** 0xF140 is `mov ebp, r8d` and 0xF22C is\n"
              " *  `setg byte [rsi + 0xa0]` -- so `flag > 0` is stored and `value > 0` is not. 0xF225 writes the \"given\" byte unconditionally and 0xF233 stores\n"
              " *  `edx` (argument 2) at +0x9C. **`ebp` is never stored**, so the third argument is read, tested and discarded. */\n"
              "void setMultiTorchCuttingPreference_0F130(void* order, int value, int flag);")

IMPL_OLD = """void setMultiTorchCuttingPreference_0F130(void* order, int value) {
    order_fields(order)->multiTorchCuttingPreferenceGiven = 1;                              // RE 0xF225
    order_fields(order)->multiTorchCuttingPreferencePositive = (value > 0) ? 1 : 0;         // RE 0xF22C
    order_fields(order)->multiTorchCuttingPreference = static_cast<std::uint32_t>(value);   // RE 0xF233
}"""
IMPL_NEW = """void setMultiTorchCuttingPreference_0F130(void* order, int value, int flag) {
    order_fields(order)->multiTorchCuttingPreferenceGiven = 1;                              // RE 0xF225: mov byte [rsi + 0x98], 1
    // **FROM THE THIRD ARGUMENT AND NOT FROM `value`.** 0xF140 is `mov ebp, r8d` and 0xF22C is `setg byte [rsi + 0xa0]`, so `flag > 0` is what is stored.
    order_fields(order)->multiTorchCuttingPreferencePositive = (flag > 0) ? 1 : 0;          // RE 0xF22C: setg
    order_fields(order)->multiTorchCuttingPreference = static_cast<std::uint32_t>(value);   // RE 0xF233: mov dword [rsi + 0x9c], r12d
}"""


def patch(path, old, new, label):
    text = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if new in text:
        print("   %-18s already patched" % label)
        return True
    if old not in text:
        print("   REFUSING: %-18s anchor not found" % label)
        return False
    io.open(path, "w", encoding="utf-8", newline="\n").write(text.replace(old, new, 1))
    print("   %-18s patched" % label)
    return True


def main():
    ok = patch(HEADER, HEADER_OLD, HEADER_NEW, "exports_impl.hpp")
    ok = patch(IMPL, IMPL_OLD, IMPL_NEW, "exports_impl.cpp") and ok
    # and the wrapper: three arguments, and it dispatches
    api = io.open(API, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    print("")
    print("the wrapper as it stands:")
    for line in api.split("\n"):
        if "SetMultiTorchCuttingPreference" in line:
            print("   %s" % line.strip()[:100])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
