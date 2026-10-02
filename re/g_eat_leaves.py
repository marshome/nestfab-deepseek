# -*- coding: utf-8 -*-
"""Eat the recognised leaves of a closure automatically, and print the ones that need reading.

Usage: python g_eat_leaves.py 51 [limit]

The deepest layers of these closures are overwhelmingly small functions in a handful of shapes. Recognising the shape
mechanically is safe here because each shape is checked instruction by instruction and the generated accessor carries the
RVA it came from, so nothing is inferred:

    mov rax, rcx ; ret                          -> a pointer adjustment, library
    xor eax, eax ; ret                          -> a default override returning zero, library
    mov r32, [rcx + off] ; ret                  -> a value getter, generated
    mov rax, [rcx + off] ; ret                  -> a pointer getter, generated
    movzx r32, byte [rcx + off] ; ret           -> a byte getter, generated
    mov [rcx + off], r32/r8 ; ret               -> a value setter, generated
    lea rax, [rcx + off] ; ret                  -> an address-of accessor, generated
    mov r32, [rdx] ; mov [rcx], r32 ; ret        -> a one dword copy, generated

Anything else is printed with its body, so the reading that needs a human stays a human's job. The script writes the
header, the tests and the registry, and it is idempotent in the sense that a shape already registered under the same RVA is
skipped.
"""
import io
import json
import os
import re
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L          # noqa: E402
import g_toolchain as T         # noqa: E402
from lib import disasm, load_prof  # noqa: E402

ROOT = L.ROOT
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "field_accessors.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")
TOOLCHAIN = os.path.join(ROOT, "re", "g_toolchain.py")


def norm(op_str):
    # offsets appear both as 0x10 and as 8, so decimal forms are canonicalised to hex before matching
    text = op_str.replace(" ", "")
    return re.sub(r"\[rcx\+(\d+)\]", lambda m: "[rcx+0x%X]" % int(m.group(1)), text)


def classify(body):
    """Return a descriptor for a recognised shape, or None."""
    ins = [(i.mnemonic, norm(i.op_str)) for i in body]
    if len(ins) == 2 and ins[0] == ("mov", "rax,rcx") and ins[1][0] == "ret":
        return ("identity", None, None)
    if len(ins) == 2 and ins[0] == ("xor", "eax,eax") and ins[1][0] == "ret":
        return ("zero", None, None)
    if len(ins) == 2 and ins[0][0] == "ret":
        return None
    if len(ins) == 2 and ins[1][0] == "ret":
        m, ops = ins[0]
        if m == "lea" and ops.startswith("rax,[rcx+0x") and ops.endswith("]"):
            return ("addr", int(ops[len("rax,[rcx+0x"):-1], 16), None)
        if m == "movsd" and ops.startswith("xmm0,qwordptr[rcx"):
            mm = re.match(r"xmm0,qwordptr\[rcx\+0x([0-9a-f]+)\]", ops)
            if mm:
                return ("getd", int(mm.group(1), 16), None)
            if ops == "xmm0,qwordptr[rcx]":
                return ("getd", 0, None)
        if m == "movsd" and ops.startswith("qwordptr[rcx"):
            mm = re.match(r"qwordptr\[rcx\+0x([0-9a-f]+)\],xmm1", ops)
            if mm:
                return ("setd", int(mm.group(1), 16), None)
            if ops == "qwordptr[rcx],xmm1":
                return ("setd", 0, None)
        if m in ("mov", "movzx") and ops.startswith(("eax,", "rax,", "eax,dword", "rax,qword")):
            src = ops.split(",", 1)[1]
            mm = re.match(r"(?:dword|qword)ptr\[rcx\+0x([0-9a-f]+)\]", src) or re.match(r"byteptr\[rcx\+0x([0-9a-f]+)\]", src) or re.match(r"\[rcx\+0x([0-9a-f]+)\]", src)
            if mm:
                width = 1 if "byteptr" in src else (8 if ("rax," in ops or "qword" in src) else 4)
                return ("get", int(mm.group(1), 16), width)
            mm = re.match(r"(?:dword|qword)ptr\[rcx\]", src) or re.match(r"byteptr\[rcx\]", src) or re.match(r"\[rcx\]", src)
            if mm:
                width = 1 if "byteptr" in src else (8 if ("rax," in ops or "qword" in src) else 4)
                return ("get", 0, width)
        if m == "mov" and ops.startswith(("dwordptr[rcx", "byteptr[rcx", "qwordptr[rcx")):
            dst, _src = ops.split(",", 1)
            width = 1 if dst.startswith("byteptr") else (8 if dst.startswith("qwordptr") else 4)
            mm = re.match(r"(?:dword|byte|qword)ptr\[rcx\+0x([0-9a-f]+)\]", dst)
            if mm:
                return ("set", int(mm.group(1), 16), width)
            if re.match(r"(?:dword|byte|qword)ptr\[rcx\]", dst):
                return ("set", 0, width)
    if len(ins) == 3 and ins[2][0] == "ret":
        a, b = ins[0], ins[1]
        if a[0] == "mov" and a[1] in ("eax,dwordptr[rdx]", "eax,[rdx]") and b[0] == "mov" and b[1] in ("dwordptr[rcx],eax", "[rcx],eax"):
            return ("copy", None, None)
    return None


def main(argv):
    ordinal = int(argv[0])
    limit = int(argv[1]) if len(argv) > 1 else 60
    profile = load_prof()
    kinds = {}

    def domain(addr):
        if addr in L.VERIFIED or addr in T.BOILERPLATE or addr in getattr(T, "IMPLEMENTED", ()):
            return False
        if addr not in profile:
            return False
        if addr not in kinds:
            k = T.kind(addr, profile)
            size = (profile.get(addr) or {}).get("size") or 0
            kinds[addr] = k if (k is not None and k != "domain" and size <= 64) else "domain"
        return kinds[addr] == "domain"

    def callees(addr):
        out = []
        size = (profile.get(addr) or {}).get("size")
        for i in disasm(addr):
            if size and i.address >= addr + size:
                break
            if i.mnemonic in ("call", "jmp"):
                m = re.search(r"0x([0-9a-f]+)", i.op_str)
                if m:
                    out.append(int(m.group(1), 16))
        return out

    table = json.loads(io.open(os.path.join(ROOT, "re", "exports_table.json"), encoding="utf-8").read())
    rva = None
    for e in table:
        if (e.get("ords") or [0])[0] == ordinal:
            rva = e["rva"]
            break
    assert rva is not None

    seen = {}
    q = deque((t, 1) for t in callees(rva) if domain(t))
    while q:
        a, d = q.popleft()
        if a in seen and seen[a] <= d:
            continue
        seen[a] = d
        for t in callees(a):
            if domain(t):
                q.append((t, d + 1))
    leaves = [a for a in seen if not [t for t in callees(a) if domain(t)]]
    leaves.sort(key=lambda a: (profile.get(a) or {}).get("size") or 0)

    books = {"identity": [], "zero": [], "get": [], "set": [], "addr": [], "copy": [], "getd": [], "setd": [], "unknown": []}
    for a in leaves:
        size = (profile.get(a) or {}).get("size") or 0
        body = [i for i in disasm(a) if i.address < a + size]
        d = classify(body)
        if d is None:
            books["unknown"].append((a, size, body))
        else:
            books[d[0]].append((a, d[1], d[2]))

    print("closure %d functions, %d leaves" % (len(seen), len(leaves)))
    print("  identity %d, zero %d, get %d, set %d, addr %d, copy %d, unknown %d"
          % (len(books["identity"]), len(books["zero"]), len(books["get"]), len(books["set"]),
             len(books["addr"]), len(books["copy"]), len(books["unknown"])))

    # the header
    h = io.open(HDR, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    anchor = "}  // namespace accessors"
    assert anchor in h
    gen = []
    tests = []
    implemented = []
    for a, off, width in books["get"][:limit]:
        bits = width * 8
        name = "get%02X_%X" % (off, a)
        gen.append("/** RE 0x%X: reads the %d-bit value at +0x%02X. */" % (a, bits, off))
        gen.append("inline std::uint%d_t %s(const void* object) {" % (bits, name))
        gen.append("    std::uint%d_t value = 0;" % bits)
        gen.append("    std::memcpy(&value, static_cast<const unsigned char*>(object) + 0x%02X, sizeof(value));" % off)
        gen.append("    return value;")
        gen.append("}")
        gen.append("")
        implemented.append(a)
        probe = {1: 0x5A, 4: 0x12345678, 8: 0x1122334455667788}[width]
        tests.append("        { const std::uint%d_t put = 0x%Xull; std::memcpy(object + 0x%02X, &put, sizeof(put));"
                     " CHECK(lcns::dll::accessors::%s(object) == put); }   // RE 0x%X" % (bits, probe, off, name, a))
    for a, off, width in books["set"][:limit]:
        bits = width * 8
        name = "set%02X_%X" % (off, a)
        gen.append("/** RE 0x%X: writes the %d-bit value at +0x%02X and nothing else. */" % (a, bits, off))
        gen.append("inline void %s(void* object, std::uint%d_t value) {" % (name, bits))
        gen.append("    std::memcpy(static_cast<unsigned char*>(object) + 0x%02X, &value, sizeof(value));" % off)
        gen.append("}")
        gen.append("")
        implemented.append(a)
        probe = {1: 0x5A, 4: 0x12345678, 8: 0x1122334455667788}[width]
        tests.append("        { lcns::dll::accessors::%s(object, 0x%Xull); std::uint%d_t got = 0;"
                     " std::memcpy(&got, object + 0x%02X, sizeof(got)); CHECK(got == 0x%Xull); }   // RE 0x%X"
                     % (name, probe, bits, off, probe, a))
    for a, off, _w in books["addr"][:limit]:
        name = "addr%02X_%X" % (off, a)
        gen.append("/** RE 0x%X: returns the address of the member at +0x%02X, not its value. */" % (a, off))
        gen.append("inline void* %s(void* object) {" % name)
        gen.append("    return static_cast<unsigned char*>(object) + 0x%02X;" % off)
        gen.append("}")
        gen.append("")
        implemented.append(a)
        tests.append("        CHECK(lcns::dll::accessors::%s(object) == object + 0x%02X);   // RE 0x%X" % (name, off, a))
    for a, off, _w in books["getd"][:limit]:
        name = "getDouble%02X_%X" % (off, a)
        gen.append("/** RE 0x%X: reads the double at +0x%02X, as movsd does. */" % (a, off))
        gen.append("inline double %s(const void* object) {" % name)
        gen.append("    double value = 0.0;")
        gen.append("    std::memcpy(&value, static_cast<const unsigned char*>(object) + 0x%02X, sizeof(value));" % off)
        gen.append("    return value;")
        gen.append("}")
        gen.append("")
        implemented.append(a)
        tests.append("        { const double put = -13.25; std::memcpy(object + 0x%02X, &put, sizeof(put));"
                     " CHECK(lcns::dll::accessors::%s(object) == put); }   // RE 0x%X" % (off, name, a))
    for a, off, _w in books["setd"][:limit]:
        name = "setDouble%02X_%X" % (off, a)
        gen.append("/** RE 0x%X: writes the double at +0x%02X and nothing else. */" % (a, off))
        gen.append("inline void %s(void* object, double value) {" % name)
        gen.append("    std::memcpy(static_cast<unsigned char*>(object) + 0x%02X, &value, sizeof(value));" % off)
        gen.append("}")
        gen.append("")
        implemented.append(a)
        tests.append("        { lcns::dll::accessors::%s(object, -13.25); double got = 0.0;"
                     " std::memcpy(&got, object + 0x%02X, sizeof(got)); CHECK(got == -13.25); }   // RE 0x%X"
                     % (name, off, a))
    for a, _o, _w in books["copy"][:limit]:
        name = "copyDword_%X" % a
        gen.append("/** RE 0x%X: copies one dword from the second argument to the first. */" % a)
        gen.append("inline void %s(void* destination, const void* source) {" % name)
        gen.append("    std::uint32_t value = 0;")
        gen.append("    std::memcpy(&value, source, sizeof(value));")
        gen.append("    std::memcpy(destination, &value, sizeof(value));")
        gen.append("}")
        gen.append("")
        implemented.append(a)
        tests.append("        { unsigned char s[8]; unsigned char d[8]; const std::uint32_t put = 0x0BADF00Du;"
                     " std::memcpy(s, &put, sizeof(put)); std::memset(d, 0, sizeof(d));"
                     " lcns::dll::accessors::%s(d, s); std::uint32_t got = 0; std::memcpy(&got, d, sizeof(got));"
                     " CHECK(got == put); }   // RE 0x%X" % (name, a))
    if gen:
        io.open(HDR, "w", encoding="utf-8", newline="\n").write(h.replace(anchor, "\n".join(gen) + anchor, 1))
        print("field_accessors.hpp  %d functions generated" % len(implemented))
    if tests:
        t = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        fin = '    return check::finish("boxacc");'
        assert fin in t
        block = ["    // ------------------- accessors eaten mechanically from the closure (g_eat_leaves.py)",
                 "    {", "        unsigned char object[0x800];   // the largest field offset an accessor touches",
                 "        std::memset(object, 0xA5, sizeof(object));"]
        block += tests
        block += ["    }", "", fin]
        io.open(TEST, "w", encoding="utf-8", newline="\n").write(t.replace(fin, "\n".join(block), 1))
        print("test_boxacc.cpp      %d checks generated" % len(tests))

    s = io.open(TOOLCHAIN, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if books["identity"] or books["zero"]:
        anchor2 = "    0x5C5270,  # mov rax, rcx ; ret -- returns its own argument"
        if anchor2 not in s:
            for cand in ("    0x5C5F50,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment",
                         "    0x4F7030,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment"):
                if cand in s:
                    anchor2 = cand
                    break
        lines = [anchor2]
        for a, _o, _w in books["identity"]:
            lines.append("    0x%X,  # mov rax, rcx ; ret -- returns its own argument" % a)
        for a, _o, _w in books["zero"]:
            lines.append("    0x%X,  # xor eax, eax ; ret -- a default override returning zero" % a)
        s = s.replace(anchor2, "\n".join(lines), 1)
    if implemented:
        marker = "IMPLEMENTED = {"
        entry = "    " + ", ".join("0x%X" % a for a in implemented) + ",   # eaten by g_eat_leaves.py"
        s = s.replace(marker, marker + "\n" + entry, 1)
    io.open(TOOLCHAIN, "w", encoding="utf-8", newline="\n").write(s)
    print("g_toolchain.py       %d registered as implemented, %d classified as library"
          % (len(implemented), len(books["identity"]) + len(books["zero"])))

    if books["unknown"]:
        print("")
        print("the first unknown leaves, for manual reading:")
        for a, size, body in books["unknown"][:12]:
            print("=== 0x%X (%d B)" % (a, size))
            for i in body[:12]:
                print("   %08x %-18s %s" % (i.address, i.mnemonic, i.op_str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
