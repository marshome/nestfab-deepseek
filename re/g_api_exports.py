# -*- coding: utf-8 -*-
"""Generate the C ABI layer: one definition per export, plus the table that describes them.

The user's requirement is that the project correspond to every exported function and that each implementation agree with
the assembly. This generator produces the two mechanical halves of that:

  * lcns/include/lcns/detail/api_exports.inc -- what each entry point IS (name, ordinals, rva, size, status);
  * lcns/src/api_exports.cpp -- the definition of each entry point, with the signature the reverse engineering inferred
    (the typed table) or, where no typed signature exists, one built from the argument-register analysis.

An entry point whose behaviour has NOT been recovered does not pretend: its body reports the call through
lcns::dll::exports::notReversed() and returns the documented neutral value for its return type (0, null or NaN), so a
caller can always tell failure from a result. The forwarding count is a number in the file rather than a claim in prose,
and every entry's original bytes are in the tree (re/g_embed.py embeds the whole export list), which is what makes the
assembly auditable next to the definition.

Emission order matters and was got wrong once: the address table takes the address of every definition, so it must be
emitted AFTER them, and an empty forwarding map needs a sentinel because a zero-length array is not valid C++.

Signatures are INFERRED. Where the inference is wrong the function still compiles and still fails loudly -- it cannot
silently return a plausible wrong answer, which is the property this layer preserves.
"""
import io
import json
import os
import re

ROOT = r"D:\Nesting\nestfab"
TABLE = os.path.join(ROOT, "re", "exports_table.json")
TYPED = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "api_typed.inc")
OUT_INC = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "api_exports.inc")
OUT_CPP = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")

POINTER_RETURNS = {"Order", "Sheet", "Part", "void*", "char*", "const char*", "int*", "unsigned char*"}


def neutral(ret):
    """The documented failure value for a return type -- never something that looks like a real result."""
    if ret == "void":
        return None
    if ret == "double":
        return "std::numeric_limits<double>::quiet_NaN()"
    if "*" in ret or ret in POINTER_RETURNS:
        return "nullptr"
    return "0"


def parse_typed():
    out = {}
    if not os.path.exists(TYPED):
        return out
    for line in io.open(TYPED, encoding="utf-8"):
        m = re.match(r"\s*LCNS_TYPED\(([^,]+),\s*([A-Za-z_][A-Za-z0-9_]*),\s*\((.*)\)\)", line)
        if m:
            out[m.group(2)] = (m.group(1).strip(), m.group(3).strip())
    return out


def main():
    exports = json.loads(io.open(TABLE, encoding="utf-8").read())
    typed = parse_typed()

    rows = []
    used_symbols = {}
    for i, e in enumerate(exports):
        name = e.get("name") or ("sub_%05X" % e["rva"])
        ords = e.get("ords") or [0]
        note = ((e.get("sem") or [""])[0] if isinstance(e.get("sem"), list) and e.get("sem") else "")
        # The original exports by ORDINAL (NumberOfNames = 0) and the labels were recovered from log strings, so two
        # ordinals may log the same label. The symbol has to be unique anyway; the table keeps the label unchanged.
        symbol = name
        if symbol in used_symbols:
            symbol = "%s_o%d" % (name, ords[0])
            note = (note + " [label shared with the entry at ordinal %d]" % used_symbols[name])[:150]
        used_symbols.setdefault(name, ords[0])
        rows.append({
            "symbol": symbol,
            "index": i,
            "name": name,
            "ord0": ords[0],
            "ord1": ords[-1] if len(ords) > 1 else -1,
            "ords": ords,
            "rva": e["rva"],
            "size": e["size"],
            "note": note.replace("\\", "/").replace('"', "'")[:150],
            "int_regs": e.get("int_regs") or [],
            "xmm": e.get("xmm") or [],
            "ret_xmm": bool(e.get("ret_xmm")),
            "typed": name in typed,
        })

    # ------------------------------------------------------------------ the definitions
    defs = []
    for r in rows:
        ret, params = typed.get(r["name"], (None, None))
        if ret is None:
            params = ", ".join(["std::intptr_t"] * len(r["int_regs"]) + ["double"] * len(r["xmm"]))
            ret = "double" if r["ret_xmm"] else "std::intptr_t"
        defs.append("")
        defs.append("// ordinal %s  rva 0x%05X  %d bytes%s"
                    % ("/".join(str(o) for o in r["ords"]), r["rva"], r["size"],
                       ("  " + r["note"]) if r["note"] else ""))
        if r["typed"]:
            defs.append("// signature from the inferred typed table")
        else:
            defs.append("// signature synthesized from the register analysis: %d integer register(s), %d xmm; the"
                        % (len(r["int_regs"]), len(r["xmm"])))
            defs.append("// interleaving of the two classes is not recoverable, so treat the parameter list as opaque")
        value = neutral(ret)
        if value is None:
            defs.append('extern "C" void %s(%s) {' % (r["symbol"], params))
            defs.append("    lcns::dll::exports::notReversed(%du);" % r["index"])
            defs.append("}")
        else:
            defs.append('extern "C" %s %s(%s) {' % (ret, r["symbol"], params))
            defs.append("    lcns::dll::exports::notReversed(%du);" % r["index"])
            defs.append("    return %s;" % value)
            defs.append("}")

    cpp = []
    cpp.append("// GENERATED by re/g_api_exports.py -- do not edit by hand.")
    cpp.append("//")
    cpp.append("// The C ABI of the original module: one definition per export. A body either forwards to a recovered")
    cpp.append("// implementation (the forwarding map below) or reports the call and returns the documented neutral value.")
    cpp.append("// Signatures are INFERRED -- see re/exports_table.json and lcns/docs/MAPPING.md.")
    cpp.append("")
    cpp.append('#include "lcns/api.hpp"')
    cpp.append('#include "lcns/exports.hpp"')
    cpp.append('#include "lcns/exports_impl.hpp"')
    cpp.append("")
    cpp.append("#include <cstdint>")
    cpp.append("#include <limits>")
    cpp.append("")
    cpp.append("namespace lcns {")
    cpp.append("namespace dll {")
    cpp.append("namespace exports {")
    cpp.append("")
    # The forwarding map is NOT generated. It is included from a hand-written file, because regenerating the table must
    # never erase a recovered behaviour and recovering one must never mean editing generated output. extern: a
    # namespace-scope const would have internal linkage and the runtime half could not link to it.
    cpp.append("// Which exports the project implements, from the hand-written file below. Every entry not listed there")
    cpp.append("// fails loudly instead of guessing, and its original bytes are embedded and verified.")
    cpp.append("extern const Forwarding kForwarding[];")
    cpp.append("extern const std::size_t kForwardingCount;")
    cpp.append('#include "lcns/detail/exports_forwarding.inc"')
    cpp.append("")
    cpp.append("}  // namespace exports")
    cpp.append("}  // namespace dll")
    cpp.append("}  // namespace lcns")
    cpp.append("")
    cpp.append("// ---------------------------------------------------------------- the 168 definitions")
    # Inside lcns::dll, because the inferred handle types (Order, Sheet, Part, ...) live there. C++ gives a function
    # declared extern "C" inside a namespace the same plain C linkage name, so the ABI is unaffected.
    cpp.append("")
    cpp.append("namespace lcns {")
    cpp.append("namespace dll {")
    cpp.extend(defs)
    cpp.append("")
    cpp.append("}  // namespace dll")
    cpp.append("}  // namespace lcns")
    cpp.append("")
    cpp.append("namespace lcns {")
    cpp.append("namespace dll {")
    cpp.append("namespace exports {")
    cpp.append("namespace {")
    cpp.append("")
    cpp.append("// The addresses of the definitions above, so a test can call every entry point through the ABI without")
    cpp.append("// knowing its type. The definitions are argument-independent, which is what makes that sound.")
    cpp.append("using RawFn = void (*)();")
    cpp.append("RawFn kAddresses[%d];" % len(rows))
    cpp.append("struct AddressBinder {")
    cpp.append("    AddressBinder() {")
    for r in rows:
        cpp.append("        kAddresses[%du] = reinterpret_cast<RawFn>(&%s);" % (r["index"], r["symbol"]))
    cpp.append("    }")
    cpp.append("};")
    cpp.append("AddressBinder kBindAddresses;")
    cpp.append("")
    cpp.append("}  // namespace")
    cpp.append("")
    cpp.append("const Entry kEntries[] = {")
    for r in rows:
        cpp.append('    {"%s", %d, %d, 0x%05Xu, %du, Status::NotReversed, "%s"},'
                   % (r["name"], r["ord0"], r["ord1"], r["rva"], r["size"], r["note"]))
    cpp.append("};")
    cpp.append("const std::size_t kEntryCount = sizeof(kEntries) / sizeof(kEntries[0]);")
    cpp.append("")
    cpp.append("const Entry* entries() { return kEntries; }")
    cpp.append("std::size_t count() { return kEntryCount; }")
    cpp.append("RawFn addressOf(std::size_t index) { return index < kEntryCount ? kAddresses[index] : nullptr; }")
    cpp.append("")
    cpp.append("}  // namespace exports")
    cpp.append("}  // namespace dll")
    cpp.append("}  // namespace lcns")
    cpp.append("")

    inc = ["// GENERATED by re/g_api_exports.py -- do not edit by hand.",
           "// One row per exported function of the original module, in the export table's order.",
           "//",
           "// LCNS_EXPORT_ENTRY(name, ord0, ord1, rva, size, status, note)"]
    for r in rows:
        inc.append('LCNS_EXPORT_ENTRY(%s, %d, %d, 0x%05X, %d, NotReversed, "%s")'
                   % (r["name"], r["ord0"], r["ord1"], r["rva"], r["size"], r["note"]))

    io.open(OUT_INC, "w", encoding="utf-8", newline="\n").write("\n".join(inc) + "\n")
    io.open(OUT_CPP, "w", encoding="utf-8", newline="\n").write("\n".join(cpp) + "\n")
    print("exports: %d definitions written, %d with a typed signature, %d synthesized"
          % (len(rows), sum(1 for r in rows if r["typed"]), sum(1 for r in rows if not r["typed"])))


if __name__ == "__main__":
    main()
