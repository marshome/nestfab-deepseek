# -*- coding: utf-8 -*-
"""Remove the opaque handles for the classes the port HAS recovered, and make every neutral return match its real type.

**THE HANDLES ARE A SECOND DECLARATION OF A CLASS THE PORT DECLARES.** `api.hpp` said `LCNS_OPAQUE(NestedPart)`, which is `struct NestedPart_t; using NestedPart =
NestedPart_t*` -- **a pointer to an incomplete type** -- while `lcns/model.hpp` declares `struct NestedPart` with seven fields. Same for `Order` (already renamed),
`Part`, `Sheet`, `Nesting`, `NestedPart` and `NoFitNesting`.

**AND THE NEUTRAL RETURN VALUES ARE WRONG FOR THE REAL TYPES.** The generated stubs say `return 0` 61 times and `return nullptr` 14 times, because a handle is a
pointer. **`NestedPart` is a value with `partIndex = 0` and `angle = 0.0`, so `return nullptr` cannot compile against it.** Each stub's neutral value has to be a
default-constructed object instead:

    a pointer handle   ->  nullptr     (no object)
    a recovered class  ->  Type{}      (an object whose every field is the default)

**AND THE SECOND IS THE HONEST ONE**: the module's function either produced a placement or it did not, and `NestedPart{}` is "a placement with no part and no
angle" -- an object that exists and is empty, rather than a null pointer that crashes whoever dereferences it.

**THE GENUINELY OPAQUE ONES STAY OPAQUE**: `NoFitContext` and `NoFitGeometry` have no recovered header.
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
HPP = os.path.join(ROOT, "lcns", "include", "lcns", "api.hpp")
CPP = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")
TYPED = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "api_typed.inc")

RECOVERED = {"Part": "model.hpp", "Sheet": "model.hpp", "Nesting": "model.hpp",
             "NestedPart": "model.hpp", "NoFitNesting": "nfp.hpp"}
STILL_OPAQUE = ["NoFitContext", "NoFitGeometry"]

HANDLE = re.compile(r"extern\s+\"C\"\s+(\w+)\s+(\w+)\s*\(([^)]*)\)\s*\{(.*?)\n\}", re.S)


def main(apply):
    hpp = io.open(HPP, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    cpp = io.open(CPP, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    typed = io.open(TYPED, encoding="utf-8", newline="").read().replace("\r\n", "\n")

    # 1. the header: a recovered class means there is no handle to declare
    removed = 0
    for name, where in RECOVERED.items():
        pattern = re.compile(r"LCNS_OPAQUE\(%s\);[^\n]*\n" % re.escape(name))
        if pattern.search(hpp):
            hpp = pattern.sub("// `%s` is a RECOVERED CLASS: lcns/%s declares it, so there is no handle to declare here.\n" % (name, where),
                              hpp, count=1)
            removed += 1
    print("   api.hpp: %d opaque handle(s) removed, %d left genuinely opaque (%s)"
          % (removed, len(STILL_OPAQUE), ", ".join(STILL_OPAQUE)))

    # 2. the ABI declaration's own comment, so it stops saying "opaque"
    hpp = hpp.replace("// Opaque handles. The real objects are internal C++ classes; only their field\n"
                      "// offsets were recovered (documented in re/REPORT.md section 3.2).",
                      "// Handles. **A RECOVERED CLASS IS NOT OPAQUE** -- where lcns/ declares the class, the ABI names it directly, because `using X = X_t*`\n"
                      "// beside `struct X` is two declarations of one name. Only the objects with no recovered header stay pointers to incomplete types.")

    # 3. the neutral returns: a recovered-class return gets a default-constructed object
    fixes = {}

    def fix(match):
        return_type, name, _params, body = match.groups()
        if return_type not in RECOVERED:
            return match.group(0)
        new_body = body
        if re.search(r"\breturn\s+nullptr\s*;", new_body):
            new_body = re.sub(r"\breturn\s+nullptr\s*;", "return %s{};" % return_type, new_body)
            fixes.setdefault(return_type, [0, 0])[0] += 1
        elif re.search(r"\breturn\s+0\s*;", new_body):
            new_body = re.sub(r"\breturn\s+0\s*;", "return %s{};" % return_type, new_body)
            fixes.setdefault(return_type, [0, 0])[1] += 1
        if new_body == body:
            return match.group(0)
        return 'extern "C" %s %s(%s) {%s\n}' % (return_type, name, _params, new_body)

    cpp = HANDLE.sub(fix, cpp)
    for return_type, (null_count, zero_count) in sorted(fixes.items()):
        print("   %-14s %d nullptr and %d zero return(s) became `%s{}`" % (return_type, null_count, zero_count, return_type))

    # 4. and the two generated files name the class rather than a handle -- which they already do, since the handle WAS the name.
    #    What must change is that `api_typed.inc`'s entries and the wrappers now refer to the class, so nothing to rewrite. This line is a check.
    for label, text in (("api_exports.cpp", cpp), ("api_typed.inc", typed)):
        for name in RECOVERED:
            if re.search(r"\b%s_t\b" % re.escape(name), text):
                print("   WARNING: %s still mentions %s_t" % (label, name))

    if apply:
        io.open(HPP, "w", encoding="utf-8", newline="\n").write(hpp)
        io.open(CPP, "w", encoding="utf-8", newline="\n").write(cpp)
        print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
