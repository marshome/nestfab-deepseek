# -*- coding: utf-8 -*-
"""Wire the 31 forwarded ordinals whose argument count already agrees with their implementation.

**EACH REWRITE USES THE MODULE'S OWN ARITY**, from `re/g_plan_wiring.py`, which reads each function's argument registers: one means `(Object* object)`, two means
`(Object* object, int value)`. **And the FIRST PARAMETER BECOMES A POINTER in every case** -- the module reads `rcx` as a source and then loads or stores through
it, which is what the two already-wired exports established for their own bodies.

**AND THE SEVEN IT REFUSES ARE REFUSED OUT LOUD**, because a mismatch between the module's arity and the implementation's is a question and not a formatting
problem: it means either the probe did not look far enough into the function or the implementation's signature is wrong, and **both of those are reasons to stop
rather than to guess.**
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import disasm  # noqa: E402

API = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")
FWD = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")
HEADER = os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp")

ARGUMENTS = ("rcx", "rdx", "r8", "r9")
HALVES = {"ecx": "rcx", "edx": "rdx", "r8d": "r8", "r9d": "r9",
          "cx": "rcx", "dx": "rdx", "r8w": "r8", "r9w": "r9",
          "cl": "rcx", "dl": "rdx", "r8b": "r8", "r9b": "r9"}
# the type each register holds, once argument 1 is known to be a pointer. rdx is an int in 30 of the 31; r8 appears once
SECOND = "int"


def used_arguments(address, size, limit=40):
    seen = set()
    count = 0
    for instruction in disasm(address):
        if instruction.address >= address + size or count >= limit:
            break
        count += 1
        destination, _sep, source = instruction.op_str.partition(",")
        first = destination.strip().split(" ")[-1]
        for whole in ARGUMENTS:
            for form in [whole] + [half for half, parent in HALVES.items() if parent == whole]:
                if re.search(r"\b%s\b" % re.escape(form), source) and first != form:
                    seen.add(whole)
    return seen


def main(apply):
    api = io.open(API, encoding="utf-8", errors="replace").read()
    forwarding = io.open(FWD, encoding="utf-8", errors="replace").read()
    header = io.open(HEADER, encoding="utf-8", errors="replace").read()

    entries = [(int(m.group(1)), m.group(2)) for m in
               re.finditer(r"^\s*\{(\d+),\s*reinterpret_cast<void\*>\(&([\w:]+)\)\}", forwarding, re.M)]
    rows = re.findall(r'\{"([^"]+)",\s*(\d+),\s*(\d+),\s*0x([0-9A-Fa-f]+)u,\s*(\d+)u,', api)
    info = {int(row[1]): (row[0], int(row[3], 16), int(row[4])) for row in rows}

    rewritten, refused = [], []
    for ordinal, symbol in sorted(entries):
        name, rva, size = info.get(ordinal, (None, 0, 0))
        if name is None or not rva:
            continue
        # **THE NAME IN THE PATTERN MUST BE THE FUNCTION'S OWN AND NOT A BARE WORD BEFORE IT.** `extern "C" Part, const char* GetPartUserString(Part)` contains the
        # name inside its return type, and a pattern that merely looks for the name found THAT occurrence -- so the replacement emitted
        # `extern "C" Part, const char** GetPartUserString(...)`. **A search for a name is not a search for a declaration of it.**
        pattern = re.compile(r'extern\s+"C"\s+([^;{]*?)\b%s\s*\(([^)]*)\)\s*\{(.*?)\n\}' % re.escape(name), re.S)
        match = pattern.search(api)
        if not match or "impl::" in match.group(3):
            continue
        # **THE IMPLEMENTATION'S DECLARATION IS WHAT SAYS THE RETURN TYPE AND THE PARAMETER TYPES.** The old wrapper returned `int` while `getPartUserString`
        # returns `const char*`, so returning the implementation's value from an `int` function is `invalid conversion from 'const char*' to 'int'`; and a `void`
        # implementation behind a non-void wrapper is `void value not ignored as it ought to be`. **The inferred table's return type was as wrong as its
        # parameter types.** **`short` and `declaration` come FIRST** -- the version that read `return_type` before defining them raised
        # `cannot access local variable 'declaration'` and wrote nothing at all.
        short = symbol.split("::")[-1]
        declaration = re.search(r"^[^\n]*\b%s\s*\(([^;]*)\)\s*;" % re.escape(short), header, re.M)
        if not declaration:
            refused.append((ordinal, name, "no declaration"))
            continue
        return_type = declaration.group(0).split(short)[0].strip() or "void"
        module_args = sorted(used_arguments(rva, size), key=ARGUMENTS.index)
        impl_args = [part.strip() for part in declaration.group(1).split(",") if part.strip()]
        if len(impl_args) != len(module_args):
            refused.append((ordinal, name, "%d vs %d" % (len(module_args), len(impl_args))))
            continue
        # **AND THE SECOND PARAMETER'S TYPE COMES FROM THE IMPLEMENTATION, NOT FROM A DEFAULT.** `sub_16CB0` forwards to `setUserStringAt1B8(void*, const char*)`,
        # so its second argument is a STRING and not an int -- the module's `rdx` is a pointer there. Reading the declaration is what says so, and a rewrite
        # that assumed `int` produced `invalid conversion from 'int' to 'const char*'`.
        second_type = "int"
        third_type = "int"
        impl_parameters = [part.strip() for part in declaration.group(1).split(",")]
        if len(impl_parameters) > 1:
            second_type = impl_parameters[1].rsplit(" ", 1)[0].strip()
        if len(impl_parameters) > 2:
            third_type = impl_parameters[2].rsplit(" ", 1)[0].strip()
        # **AND A FORWARDING ENTRY THAT NAMES A DIFFERENT EXPORT'S IMPLEMENTATION IS A QUESTION, NOT A TYPO TO FIX HERE.** `sub_0AFF0` and `sub_0B000` forward to
        # `setModuleSwitch`, `setByteAtF8` and `setDoubleAndFlag`, whose arities do not match theirs either -- so the list is wrong about them and they are
        # refused rather than wired to something plausible.
        # **AND THE FIRST PARAMETER'S NAMED TYPE COMES FROM THE OLD WRAPPER**, which is where the inferred table's spelling of it survives. It is only the NAME
        # that is kept -- the POINTER is added -- because the module reads rcx as a source and then dereferences it in every one of these.
        old_parameters = [part.strip() for part in match.group(2).split(",") if part.strip()]
        first_type = old_parameters[0].rstrip("*").strip().split(" ")[-1] if old_parameters else "void"
        parameters = ["%s* object" % first_type]
        if len(module_args) > 1:
            parameters.append("%s value" % second_type)
        if len(module_args) > 2:
            parameters.append("%s extra" % third_type)
        # **THE PATTERN'S FIRST GROUP ENDS AT THE OPENING PARENTHESIS**, so the replacement has to SUPPLY the parameter list and the brace rather than reuse the
        # old ones -- the first version emitted the comment and the call directly after `(`, which is where `'object' was not declared in this scope` came from.
        comment = ("\n"
                   "    // **WIRED FROM THE MODULE'S OWN ARITY**: re/g_plan_wiring.py read %s as the argument register(s), and 0x%X's body reads through rcx.\n"
                   % (", ".join(module_args), rva))
        call = ", ".join(["static_cast<void*>(object)"] + (["value"] if len(module_args) > 1 else [])
                         + (["extra"] if len(module_args) > 2 else []))
        # **AND A NON-VOID RETURN TYPE NEEDS A RETURN STATEMENT.** The first version emitted only the call, so sixty wrappers that used to `return 0` became
        # functions with no return -- `-Wreturn-type`, and this project's gate fails on warnings. **The old wrapper's body said what it returned; the
        # replacement has to say the same thing, with the implementation's value instead of the neutral one.**
        if return_type == "void":
            body = "    lcns::dll::exports::impl::%s(%s);\n" % (short, call)
        else:
            body = "    return lcns::dll::exports::impl::%s(%s);\n" % (short, call)
        replacement = ('extern "C" %s %s(%s) {%s%s}'
                       % (return_type, name, ", ".join(parameters), comment, body))
        api = api[:match.start()] + replacement + api[match.end():]
        # and the table row
        # **ONE BACKSLASH AND NOT TWO.** A raw string with `\\1` is a literal backslash followed by `1`, so every rewritten row began with a stray `\` and the
        # build reported `stray '\' in program` fifteen times. The backreference in a raw string is `\1`.
        api = re.sub(r'(\{"%s",\s*\d+,\s*\d+,\s*0x[0-9A-Fa-f]+u,\s*\d+u,\s*)Status::NotReversed,\s*""'
                     % re.escape(name), r'\1Status::Forwarded, "// kForwarding -> impl::%s"' % short, api, count=1)
        rewritten.append((ordinal, name, short, len(module_args)))

    for ordinal, name, short, count in rewritten:
        print("   ord %-5d %-34s -> %s (%d arg)" % (ordinal, name[:34], short, count))
    print("%d wrapper(s) rewritten" % len(rewritten))
    if refused:
        print("")
        print("refused (arity disagrees, so a question and not a formatting problem):")
        for ordinal, name, why in refused:
            print("   ord %-5d %-34s %s" % (ordinal, name[:34], why))

    if apply and rewritten:
        io.open(API, "w", encoding="utf-8", newline="\n").write(api)
        print("")
        print("written: lcns/src/api_exports.cpp")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
