# -*- coding: utf-8 -*-
"""Which unimplemented exports still depend on REAL domain code, once the measured boilerplate is set aside.

The BOILERPLATE set below is not guessed. Every address in it was read whole and identified in an earlier round:

  0x9984B0  a five-byte jmp into the import stub bank, 5721 callers -- a deallocation wrapper
  0x998500  109 bytes, 2317 callers -- operator new, with the null-to-one fix and the new_handler retry
  0x62F280  171 bytes -- reaches the platform through the IAT; builds an "CCG " tagged argument block
  0x64AEA0  403 bytes -- the logger; round 369 showed it tests a global switch and returns when it is off
  0xAB20    98 bytes -- compiler-generated initialisation of a function-local static
  0x978750  51 bytes -- an allocation plus vtable store plus constructor call wrapper
  0x97ABF0  183 bytes -- the exception throw machinery: allocate, refcount, vtable, throw

Everything else that a function's own instructions show as toolchain, diagnostic or unknown is handled by kind() below.
An address in neither VERIFIED nor BOILERPLATE nor one of those kinds counts as domain, which is what must be read.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L  # noqa: E402
from lib import disasm, load_prof  # noqa: E402

BOILERPLATE = {
    0x9984B0,  # deallocation thunk into the import stub bank
    0x998500,  # operator new
    0x62F280,  # platform stub through the IAT
    0x64AEA0,  # the logger, no effect on its default path
    0xAB20,    # static initialisation boilerplate
    0x978750,  # allocation and constructor wrapper
    0x62F000,  # RE round 501: xor eax,eax; ret -- the default empty implementation
    0x62F010,  # two-level pointer fetch
    0x963560,  # global singleton accessor
    0x962F10,  # global singleton accessor
    0x998CB0,  # tail call into the runtime
    0x6562A0,  # throw helper
    0x990E80,  # fetch a global then call the throw helper
    0x62F380,  # virtual dispatch trampoline
    0x62F330,  # runtime initialisation guard
    0x656260,  # exception format and throw machinery
    0x998FE0,  # reference count and canary guard
    0x653130,  # virtual call with a stack cookie
    0x653300,  # same family as 0x653130
    0x653280,  # same family as 0x653130
    0x6530A0,  # same family as 0x653130
    0x998BC0,  # runtime string or exception helper
    0x9989A0,  # runtime string or exception helper
    0x999030,  # runtime throw entry
    0x89A730,  # eight bytes: lea rax,[rip+..] ; ret -- returns a static object address
    0x86A2C0,  # atomic decrement of [rcx+0x10] and delete when it reaches zero: refcount release
    0x877B20,  # installs a vtable taken from a global plus 0x10
    0x998C70,  # allocator size class dispatch between two globals
    0x875EB0,  # installs a vtable then initialises a member string
    0x86B6B0,  # std::string range constructor using the strlen stub
    0x9988C0,  # allocator with a 0xA0 byte header, zeroed, returns past the header
    0x97AB50,  # allocates, installs a vtable, throws, then releases
    0x998A60,  # runtime allocation family (restored: an earlier patch dropped the anchor line it replaced)
    0x7C4A80,  # allocates eight bytes, stores a vtable and calls the throw entry (restored for the same reason)
    0x910C20,  # std::string internal: data, length and small buffer, calls the growth routine
    0x62DBE0,  # four bytes: mov rax,rcx ; ret -- returns the first argument
    0x62DBF0,  # four bytes: mov rax,rcx ; ret -- the same identity
    0x62EFC0,  # vector subscript: base at [rdx+8] plus a 32-bit index taken through [rdx+0x10]
    0x86B750,  # shared_ptr copy: loads the control block and increments its count atomically
    0x86A370,  # container growth: base plus requested size, doubling policy
    0x86A3E0,  # container growth: clamps against 0x3FFFFFFFFFFFFFF9 and doubles
    0x653190,  # container helper built on the vector subscript above
    0x6533B0,  # jump table dispatch on a low nibble: a library character or format classifier
    0x97A6D0,  # reads a field of a runtime global and returns whether it is non zero
    0x62D860,  # calls 0x62D7B0 then returns minus one when the result is zero
    0x60C5A0,  # container size: distance from an inline buffer plus a stored count
    0x875F50,  # copy constructor: installs a vtable then copies a shared_ptr member
    0x877A20,  # derived copy constructor: vtable plus a string member
    0x875FD0,  # destructor: installs a vtable, decrements a refcount, releases when it reaches zero
    0x8760F0,  # destructor thunk: installs a vtable then jumps into the release path
    0x876040,  # derived copy constructor: calls 0x888F50 then installs a vtable
    0x877AD0,  # destructor thunk for the same family as 0x875FD0
    0x90ECB0,  # std::string internal: same three words, clamps against max_size
}

# Entries whose value cannot be reproduced by any reimplementation, because it is an address inside the original image.
NOT_EQUIVALENT = {88, 90, 92}   # GetBuildVersion, GetBuildDate, GetMajorVersion


def kind(addr, profile):
    """One verdict per function, from its own instructions only. None if it is not a known function."""
    if addr not in profile:
        return None
    text = []
    size = (profile.get(addr) or {}).get("size")
    for ins in disasm(addr):
        if size and ins.address >= addr + size:
            break
        text.append(ins.mnemonic + " " + ins.op_str)
    if not text:
        return None
    if len(text) == 1:
        return "toolchain"
    for t in text:
        if "qword ptr [rip" in t and (t.startswith("jmp") or t.startswith("call")):
            return "toolchain"
        if t.startswith("call 0x63f3"):
            return "toolchain"
    for t in text:
        if t == "call 0x910ba0":
            return "diagnostic"
    return "domain"


def main():
    profile = load_prof()
    done = L.forwarded_ordinals()
    table = json.loads(io.open(os.path.join(L.ROOT, "re", "exports_table.json"), encoding="utf-8").read())

    verdicts = {}
    rows = []
    for e in table:
        ord0 = (e.get("ords") or [0])[0]
        if ord0 in done:
            continue
        name = e.get("name") or ("sub_%05X" % e["rva"])
        targets = L.external_targets(e["rva"], e["size"])
        rows.append((name, ord0, e["rva"], e["size"], targets))
        for t in targets:
            if t in L.VERIFIED or t in BOILERPLATE or t in verdicts:
                continue
            k = kind(t, profile)
            verdicts[t] = k if k is not None else "unknown"

    counts = {}
    for v in verdicts.values():
        counts[v] = counts.get(v, 0) + 1
    print("distinct blocker addresses judged: %d" % len(verdicts))
    for k in sorted(counts):
        print("    %-11s %d" % (k, counts[k]))
    print("    %-11s %d  (measured whole in earlier rounds)" % ("boilerplate", len(BOILERPLATE)))

    ready = []
    not_equivalent = []
    blocked = []
    for name, ord0, rva, size, targets in rows:
        bad = []
        for t in targets:
            if t in L.VERIFIED or t in BOILERPLATE:
                continue
            if verdicts.get(t) == "domain":
                bad.append(t)
        if not targets:
            ready.append((name, ord0, rva, size, "no external target at all"))
        elif not bad:
            if ord0 in NOT_EQUIVALENT:
                not_equivalent.append((name, ord0, rva, size, "returns an address inside the original image"))
            else:
                ready.append((name, ord0, rva, size, "only boilerplate, toolchain, diagnostic or verified"))
        else:
            blocked.append((name, ord0, rva, size, bad))

    print("")
    print("implementable now: %d" % len(ready))
    for name, ord0, rva, size, why in ready[:80]:
        print("    0x%-6X ord %-4d %-36s %5d bytes  (%s)" % (rva, ord0, name, size, why))
    print("")
    print("not equivalent by address, listed rather than counted as progress: %d" % len(not_equivalent))
    for name, ord0, rva, size, why in not_equivalent:
        print("    0x%-6X ord %-4d %-36s %5d bytes  (%s)" % (rva, ord0, name, size, why))
    print("")
    print("still blocked on real domain code: %d" % len(blocked))
    dom = {}
    for _n, _o, _r, _s, bad in blocked:
        for t in bad:
            dom[t] = dom.get(t, 0) + 1
    for t, c in sorted(dom.items(), key=lambda kv: -kv[1])[:14]:
        size = (profile.get(t) or {}).get("size")
        print("    0x%-8X blocks %3d exports, %s bytes" % (t, c, size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
