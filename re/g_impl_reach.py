# -*- coding: utf-8 -*-
"""Which implemented functions no export reaches, and which named exports have no implementation at all.

**THE TWO GAPS ARE OPPOSITE AND BOTH ARE WORK:**

  * **A BODY WITH NO WRAPPER IS DEAD CODE.** It is written, it carries its RE addresses, it compiles, and no entry point dispatches to it -- which is what
    `InfiniteEngine` having only a comment amounted to, one layer up.
  * **A `kForwarding` ENTRY WHOSE SYMBOL DOES NOT EXIST IS A CLAIM WITH NO SUBJECT.** `forwards()` would return true and there would be nothing to call.

    python -u g_impl_reach.py
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

IMPL = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")
HEADER = os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp")
API = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")
FWD = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")


def main():
    impl = io.open(IMPL, encoding="utf-8", errors="replace").read()
    header = io.open(HEADER, encoding="utf-8", errors="replace").read()
    api = io.open(API, encoding="utf-8", errors="replace").read()
    forwarding = io.open(FWD, encoding="utf-8", errors="replace").read()

    defined = set(re.findall(r"^(?:extern \"C\" )?[\w:<>*&\s]*?\b(\w+)\s*\([^;{]*\)\s*\{", impl, re.M))
    declared = set(re.findall(r"\b(\w+)\s*\([^;]*\)\s*;", header))
    named = {m.group(2).split("::")[-1] for m in
             re.finditer(r"^\s*\{(\d+),\s*reinterpret_cast<void\*>\(&([\w:]+)\)\}", forwarding, re.M)}
    # every `impl::<name>` the wrappers call, and every one the forwarding list names
    called = set(re.findall(r"exports::impl::(\w+)\(", api))

    print("functions DEFINED in exports_impl.cpp:        %d" % len(defined))
    print("functions DECLARED in exports_impl.hpp:       %d" % len(declared))
    print("symbols named by kForwarding:                 %d" % len(named))
    print("symbols CALLED by a wrapper:                  %d" % len(called))
    print("")

    unreached = sorted(defined - called)
    print("**DEFINED BUT NOT CALLED BY ANY WRAPPER:        %d**" % len(unreached))
    for name in unreached:
        in_named = "  (named by kForwarding)" if name in named else ""
        in_declared = "" if name in declared else "  (NOT DECLARED)"
        print("   %-52s%s%s" % (name[:52], in_named, in_declared))
    print("")

    missing = sorted(named - defined)
    print("**NAMED BY kForwarding BUT NOT DEFINED:         %d**" % len(missing))
    for name in missing:
        print("   %s" % name)
    if not missing:
        print("   (none: every forwarding entry has a subject)")
    print("")

    undeclared = sorted(defined - declared)
    print("DEFINED BUT NOT DECLARED IN THE HEADER:        %d" % len(undeclared))
    for name in undeclared:
        print("   %s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
