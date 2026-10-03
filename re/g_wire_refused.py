# -*- coding: utf-8 -*-
"""Wire the refused entries ONE AT A TIME, with each one's evidence read rather than assumed.

**THE BULK PASS REFUSED SEVEN ON AN ARITY MISMATCH, AND THE SEVEN ARE NOT ONE KIND OF PROBLEM:**

  * **TWO OF THE REFUSALS WERE THE PROBE'S MISTAKE, NOT THE CODE'S.** `0xB190` (GetNumberOfNestedParts) reads `mov rbx, rcx` and then `mov rcx, qword [rbx + 8]`
    -- **the second `rcx` is a DESTINATION read from the object, not a second argument**, and `entries` counts a register as an argument when it appears as a
    source. So the module takes ONE argument and the implementation's `(void* order)` is right.
  * **`sub_0AFF0` (ordinal 288) is `test edx, edx` / `setne byte [rcx + 0xf8]` / `ret`** -- two arguments, and `setByteAtF8(void* object, int value)` matches.

**AND THE REMAINING FIVE ARE QUESTIONS I AM NOT GOING TO ANSWER BY GUESSING**, because each needs a function read in full: ord 176's module reads THREE
registers while its implementation takes two, ord 212's reads one while its implementation takes two, and ord 246's reads two while its implementation takes
four. **A mismatch that survives a correct probe means one of the two sides is wrong, and which one is a measurement.**
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
API = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")

# name -> (return type, parameters, the implementation call, the note)
WIRINGS = [
    ("GetNumberOfNestedParts", "std::size_t", "Solution* solution",
     "lcns::dll::exports::impl::getNumberOfNestedParts(static_cast<void*>(solution));",
     "**ONE ARGUMENT, AND THE PROBE SAID TWO.** 0xB195 is `mov rbx, rcx` and 0xB1A4 is `mov rcx, qword [rbx + 8]` -- the second rcx is a DESTINATION loaded "
     "from the object and not a second argument. The implementation's `(void* order)` was right and the refusal was the tool's."),
    ("sub_0AFF0", "void", "void* order, int value",
     "lcns::dll::exports::impl::setByteAtF8(order, value);",
     "**TWO ARGUMENTS AND THE PROBE SAID ZERO.** `test edx, edx` READS edx and writes no register, so a rule that looks at destinations saw nothing; the body is "
     "`setne byte [rcx + 0xf8]`, which uses rcx as the object and edx as the value. `setByteAtF8(void*, int)` matches exactly."),
]


def main():
    api = io.open(API, encoding="utf-8", errors="replace").read()
    done = 0
    for name, return_type, parameters, call, note in WIRINGS:
        # **`re.compile` TAKES A PATTERN AND FLAGS, AND `api` IS NEITHER.** The first version was
        # `re.compile(pattern % ..., api, re.S)` -- the source text in the flags position -- and the assignment that failed made `api` a LOCAL for the whole
        # function, so the next line's `pattern.search(api)` raised `cannot access local variable 'api' where it is not associated with a value`. **A wrong
        # argument in one line became an error about a different line's variable.**
        pattern = re.compile(r'extern\s+"C"\s+[^;{]*?\b%s\s*\(([^)]*)\)\s*\{(.*?)\n\}' % re.escape(name), re.S)
        match = pattern.search(api)
        if not match:
            print("   %-28s no wrapper found" % name)
            continue
        if "impl::" in match.group(2):
            print("   %-28s already dispatches" % name)
            continue
        replacement = ('extern "C" %s %s(%s) {\n    // %s\n    %s\n}'
                       % (return_type, name, parameters, note, call))
        api = api[:match.start()] + replacement + api[match.end():]
        api = re.sub(r'(\{"%s",\s*\d+,\s*\d+,\s*0x[0-9A-Fa-f]+u,\s*\d+u,\s*)Status::NotReversed,\s*""'
                     % re.escape(name), r'\1Status::Forwarded, "// wired after the arity was re-read"', api, count=1)
        print("   %-28s wired" % name)
        done += 1

    if done:
        io.open(API, "w", encoding="utf-8", newline="\n").write(api)
        print("%d wrapper(s) written" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main())
