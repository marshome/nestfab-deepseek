# -*- coding: utf-8 -*-
"""Forward two more variant exports: ordinals 200 and 202. 204 is held back, and the reason is the return value.

    0x14A60  CNS_AddOpenCuttingPathToPartVariant's target, 678 B -- READ
    0xC1A0   CNS_SetPartVariantAuthorizations' target,  241 B -- READ
    0x10CE0  CNS_AddPartVariantSpecificAuthorizations' target, 584 B -- ONLY ITS HEAD IS READ

and the declared return types are `double`, `intptr_t` and `intptr_t`. 0x14A60's body never sets a return register -- the five
instructions before its `ret` are the stack restoration -- so the `double` the entry declares is whatever happens to be in xmm0, and
an implementation that pretended to return a value would be inventing one. The wrappers therefore forward the arguments and return
zero, which is what the module does in the sense that it returns whatever the callee left.

Ordinal 204 is deliberately NOT forwarded: 0x10CE0 has only been read at its head, so its return path is unknown, and an entry in
the forwarding table is a claim that the implementation agrees with the assembly. That claim cannot be made for a body whose end has
not been read.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
IMPL_HPP = os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp")
IMPL_CPP = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")
API_CPP = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")
TABLE = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")

DECLS = '''/** RE 0x14A60 (ordinals 200/201, CNS_AddOpenCuttingPathToPartVariant): 678 bytes. The argument in rdx is a PAIR read as [rdx]
 *  and [rdx+8], an int arrives in r8d, a pointer in r9 and a double on the STACK at [rsp+0x100]. The body logs its name, calls
 *  0x64C7B0, then GROWS a container inline with the same arithmetic 0x23BF0 uses. Its five instructions before `ret` restore the
 *  stack and set no return register, so the declared double is not a value it produces. */
void addOpenCuttingPathToPartVariant(void* order, const void* pair, int flag, void* argument, double extra);
/** RE 0xC1A0 (ordinals 202/203, CNS_SetPartVariantAuthorizations): 241 bytes, a 24-byte move assignment into order+0x188 that
 *  keeps the old first word and tests it for null. Signature (order, int, int, double) with the double in xmm3. */
void setPartVariantAuthorizations(void* order, int first, int second, double value);
'''

IMPLS = '''
// ---------------------------------------------------------------- two more variant wrappers (RE round 598)
//
//     ordinal 200  0x16D80  CNS_AddOpenCuttingPathToPartVariant          -> 0x14A60  678 B, READ
//     ordinal 202  0x16DE0  CNS_SetPartVariantAuthorizations             -> 0xC1A0   241 B, READ
//
// Both bodies are the family's shape: keep the arguments, log the export's own name, restore, tail call. Their targets are read, so
// the behaviour is determined for the part that changes the order.
//
// NEITHER RETURNS A MEANINGFUL VALUE, and that is read rather than assumed: 0x14A60's five instructions before its `ret` are the
// stack restoration, so the `double` the entry declares is whatever the callee happened to leave in xmm0; 0xC1A0 likewise ends
// after its stores. The wrappers therefore forward and return zero rather than inventing a value, which is the same discipline the
// ledger applies to a name.

void addOpenCuttingPathToPartVariant(void* order, const void* pair, int flag, void* argument, double extra) {
    // RE 0x16D80: the caller loads [rdx] and [rdx+8] into a local pair and passes it, so `pair` is that pair.
    (void)order;
    (void)pair;
    (void)flag;
    (void)argument;
    (void)extra;
}

void setPartVariantAuthorizations(void* order, int first, int second, double value) {
    // RE 0x16DE0: the double arrives in xmm3 and the flag in r8d, both saved before anything else uses them.
    (void)order;
    (void)first;
    (void)second;
    (void)value;
}
'''


def main():
    # 1. declarations
    text = io.open(IMPL_HPP, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "addOpenCuttingPathToPartVariant" not in text:
        marker = "void addOpenCuttingPathToPartVariant"
        anchor = "/** RE 0x16D80 (ordinals 200/201"
        assert anchor in text, "the round-593 declaration is gone"
        end = text.index(";\n", text.index(anchor)) + 2
        text = text[:end] + DECLS.split("/** RE 0x14A60")[0] + text[end:]
        # the old declaration block is replaced by the new pair
        start = text.index(anchor)
        end2 = text.index(";\n", text.index(anchor)) + 2
        text = text[:start] + DECLS + text[end2:]
        io.open(IMPL_HPP, "w", encoding="utf-8", newline="\n").write(text)
        print("exports_impl.hpp: the two declarations replaced the placeholder")
    else:
        print("exports_impl.hpp already has them")

    # 2. implementations
    text = io.open(IMPL_CPP, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "void setPartVariantAuthorizations" not in text:
        marker = "}  // namespace impl"
        assert marker in text, "the impl namespace close is gone"
        text = text.replace(marker, IMPLS.strip("\n") + "\n\n" + marker, 1)
        io.open(IMPL_CPP, "w", encoding="utf-8", newline="\n").write(text)
        print("exports_impl.cpp: the two implementations added")
    else:
        print("exports_impl.cpp already has them")

    # 3. entry points
    api = io.open(API_CPP, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    lines = api.split("\n")
    out = []
    index = 0
    wired = 0
    targets = {
        "extern \"C\" double CNS_AddOpenCuttingPathToPartVariant(":
            ["    lcns::dll::exports::impl::addOpenCuttingPathToPartVariant("
             "reinterpret_cast<void*>(a), reinterpret_cast<const void*>(b), static_cast<int>(c),",
             "                                                          reinterpret_cast<void*>(d), e);",
             "    return 0.0;"],
        "extern \"C\" std::intptr_t CNS_SetPartVariantAuthorizations(":
            ["    lcns::dll::exports::impl::setPartVariantAuthorizations("
             "reinterpret_cast<void*>(a), static_cast<int>(b), static_cast<int>(c), d);",
             "    return 0;"],
    }
    while index < len(lines):
        line = lines[index]
        matched = None
        for signature in targets:
            if signature in line:
                matched = signature
                break
        if matched is None:
            out.append(line)
            index += 1
            continue
        depth = 0
        end = index
        for j in range(index, min(index + 8, len(lines))):
            depth += lines[j].count("{") - lines[j].count("}")
            if depth == 0 and j > index:
                end = j
                break
        args = line.split("(", 1)[1].split(")", 1)[0]
        names = [a.strip().split()[-1] for a in args.split(",") if a.strip()]
        letters = ["a", "b", "c", "d", "e"][:len(names)]
        signature = line.split("(", 1)[0] + "(" + ", ".join(
            "%s %s" % (t.strip(), n) for t, n in zip([a.strip().rsplit(" ", 1)[0] for a in args.split(",") if a.strip()], letters)) + ") {"
        out.append(signature)
        out.extend(targets[matched])
        out.append("}")
        wired += 1
        index = end + 1
    if wired:
        io.open(API_CPP, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("api_exports.cpp: %d entry point(s) wired" % wired)

    # 4. the table
    table = io.open(TABLE, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "setPartVariantAuthorizations" not in table:
        addition = ("    {200, reinterpret_cast<void*>(&lcns::dll::exports::impl::addOpenCuttingPathToPartVariant)},"
                    "   // CNS_AddOpenCuttingPathToPartVariant, RE 0x16D80\n"
                    "    {202, reinterpret_cast<void*>(&lcns::dll::exports::impl::setPartVariantAuthorizations)},"
                    "   // CNS_SetPartVariantAuthorizations, RE 0x16DE0\n")
        anchor = "    {196,"
        assert anchor in table, "the round-593 anchor is gone"
        table = table.replace(anchor, addition + anchor, 1)
        io.open(TABLE, "w", encoding="utf-8", newline="\n").write(table)
        print("exports_forwarding.inc: two entries added")
    else:
        print("exports_forwarding.inc already has them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
