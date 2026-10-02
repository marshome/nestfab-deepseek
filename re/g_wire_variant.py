# -*- coding: utf-8 -*-
"""Wire the two variant entry points to their implementations, which the previous script did NOT do.

The script reported "api_exports.cpp: nothing to wire, or already wired" and that was wrong: the entry bodies still call
notReversed and return zero, because the detection looked for the target name inside a body that does not mention it. The result was
two forwarding-table entries claiming an implementation agrees with the assembly while the entry point still refused to run one --
which is precisely the false claim the table exists to prevent.

This replaces the two bodies by line, marks the parameters as used so the build stays at zero warnings, and prints the before and
after so the change is visible rather than asserted.
"""
import io
import os

PATH = r"D:\Nesting\nestfab\lcns\src\api_exports.cpp"

REPLACEMENTS = [
    (
        "extern \"C\" std::intptr_t AddHoleToPartVariant(std::intptr_t, std::intptr_t, std::intptr_t) {",
        ["extern \"C\" std::intptr_t AddHoleToPartVariant(std::intptr_t a, std::intptr_t b, std::intptr_t c) {",
         "    // RE 0x16D00, ordinal 196/197: eleven instructions that keep the three arguments, log the export's own name and tail",
         "    // call 0x132E0. The logger call is not reproduced; the rest is forwarded unchanged.",
         "    lcns::dll::exports::impl::addHoleToPartVariant(reinterpret_cast<void*>(a), static_cast<int>(b),",
         "                                                  reinterpret_cast<void*>(c));",
         "    return 0;",
         "}"],
    ),
    (
        "extern \"C\" std::intptr_t CNS_AddExternalBoundaryToPartVariant(std::intptr_t, std::intptr_t, std::intptr_t) {",
        ["extern \"C\" std::intptr_t CNS_AddExternalBoundaryToPartVariant(std::intptr_t a, std::intptr_t b, std::intptr_t c) {",
         "    // RE 0x16D40, ordinal 198/199: the SAME eleven instructions and the same tail target, so this delegates rather than",
         "    // repeating its twin. Kept as its own entry point because the module has two and the ordinals record the distinction.",
         "    lcns::dll::exports::impl::addExternalBoundaryToPartVariant(reinterpret_cast<void*>(a), static_cast<int>(b),",
         "                                                               reinterpret_cast<void*>(c));",
         "    return 0;",
         "}"],
    ),
]


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    lines = text.split("\n")
    out = []
    index = 0
    replaced = 0
    while index < len(lines):
        line = lines[index]
        matched = None
        for signature, _body in REPLACEMENTS:
            if signature in line:
                matched = signature
                break
        if matched is None:
            out.append(line)
            index += 1
            continue
        # find the end of the function: braces balance in the two lines that follow
        depth = 0
        end = index
        for j in range(index, min(index + 8, len(lines))):
            depth += lines[j].count("{") - lines[j].count("}")
            if depth == 0 and j > index:
                end = j
                break
        before = " | ".join(x.strip() for x in lines[index:end + 1])
        body = [b for sig, b in REPLACEMENTS if sig == matched][0]
        out.extend(body)
        print("replaced %s" % matched.split("(")[0].split()[-1])
        print("    before: %s" % before[:150])
        print("    after:  %s" % " ".join(x.strip() for x in body)[:150])
        replaced += 1
        index = end + 1
    if replaced:
        io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("%d entry point(s) wired" % replaced)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
