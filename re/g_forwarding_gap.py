# -*- coding: utf-8 -*-
"""Count how many `kForwarding` ordinals have a wrapper that ACTUALLY DISPATCHES, which is the real gap.

**THE TWO COUNTS THIS RECONCILES.** `kForwarding` lists 47 ordinals, and only 8 wrappers in `api_exports.cpp` mention `impl::`. **If a forwarded ordinal's wrapper
still calls `notReversed`, then the forwarding entry names an implementation that nothing calls** -- the list says one thing and the code does another.

**AND THIS CORRECTS A CLAIM I MADE TWICE.** I reported "**0 wrappers dispatch to a body**" from a grep for `exports_impl::`. The forwarders say `impl::`, in the
namespace `lcns::dll::exports::impl`, so the grep's answer was about a name and not about the mechanism. **A count produced by one pattern is a count of that
pattern.**
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
API = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")
FWD = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")


def main():
    api = io.open(API, encoding="utf-8", errors="replace").read()
    forwarding = io.open(FWD, encoding="utf-8", errors="replace").read()

    entries = [(int(m.group(1)), m.group(2)) for m in
               re.finditer(r"^\s*\{(\d+),\s*reinterpret_cast<void\*>\(&([\w:]+)\)\}", forwarding, re.M)]
    by_ordinal = {ordinal: symbol for ordinal, symbol in entries}

    # every extern "C" wrapper, its name and its body
    wrappers = {}
    for match in re.finditer(r'extern "C"[^;{]*?\b(\w+)\s*\([^)]*\)\s*\{(.*?)\n\}', api, re.S):
        wrappers[match.group(1)] = " ".join(match.group(2).split())

    # the table's rows, so an ordinal can be joined to a name
    rows = re.findall(r'\{"([^"]+)",\s*(\d+),\s*(\d+),', api)
    name_of = {int(row[1]): row[0] for row in rows}

    dispatching, stubbed = [], []
    for ordinal, symbol in sorted(by_ordinal.items()):
        name = name_of.get(ordinal)
        body = wrappers.get(name or "", None)
        if body is None:
            stubbed.append((ordinal, name or "(no row)", symbol, "NO WRAPPER"))
        elif "impl::" in body:
            dispatching.append((ordinal, name, symbol))
        else:
            stubbed.append((ordinal, name, symbol, "the wrapper does not call impl::"))

    print("kForwarding entries:                        %d" % len(entries))
    print("**of which the wrapper DISPATCHES:          %d**" % len(dispatching))
    print("  of which it does NOT:                     %d" % len(stubbed))
    print("")
    print("=== forwarded ordinals whose wrapper does NOT dispatch")
    for ordinal, name, symbol, why in stubbed:
        print("   ord %-4s %-30s -> %-46s %s" % (ordinal, name[:30], symbol.split("::")[-1][:46], why))
    return 0


if __name__ == "__main__":
    sys.exit(main())
