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
    # a constant returned straight away
    if len(ins) == 2 and ins[1][0] == "ret" and ins[0][0] == "mov" and re.match(r"eax,(0x[0-9a-f]+|\d+)$", ins[0][1]):
        return ("const", int(ins[0][1].split(",")[1], 0), None)
    # a global read through rip
    if len(ins) == 2 and ins[1][0] == "ret" and ins[0][0] == "mov" and ins[0][1].startswith("eax,dwordptr[rip+"):
        return ("global", None, None)
    # a two level pointer: load a member, then load through it at a fixed offset
    if len(ins) == 3 and ins[2][0] == "ret" and ins[0] == ("mov", "rax,qwordptr[rcx]"):
        mm = re.match(r"rax,qwordptr\[rax\+0x([0-9a-f]+)\]", ins[1][1])
        if mm:
            return ("twolvl", int(mm.group(1), 16), None)
        mm = re.match(r"add,?rax,0x([0-9a-f]+)", ins[1][0] + "," + ins[1][1]) or re.match(r"rax,0x([0-9a-f]+)", ins[1][1])
        if ins[1][0] == "add" and ins[1][1].startswith("rax,"):
            return ("ptradd", int(ins[1][1].split(",")[1], 16), None)
    # a null test on the first member
    if len(ins) == 3 and ins[2][0] == "ret" and ins[0][0] == "cmp" and ins[0][1] in ("qwordptr[rcx],0", "dwordptr[rcx],0") and ins[1][0] == "setne":
        return ("nullpred", None, None)
    # a two byte setter, adjacent offsets, second and third argument
    if len(ins) == 3 and ins[2][0] == "ret" and ins[0][0] == "mov" and ins[1][0] == "mov":
        m1 = re.match(r"byteptr\[rcx\+0x([0-9a-f]+)\],(dl|sil|r8b|r9b)", ins[0][1])
        m2 = re.match(r"byteptr\[rcx\+0x([0-9a-f]+)\],(dl|sil|r8b|r9b)", ins[1][1])
        if m1 and m2 and int(m2.group(1), 16) == int(m1.group(1), 16) + 1 and m1.group(2) == "dl" and m2.group(2) == "r8b":
            return ("twobytes", int(m1.group(1), 16), None)
    # a dword comparison between the two arguments
    if len(ins) == 3 and ins[2][0] == "ret" and ins[0][0] == "mov" and ins[0][1] in ("eax,dwordptr[rdx]", "eax,[rdx]") \
            and ins[1][0] == "cmp" and ins[1][1] in ("dwordptr[rcx],eax", "[rcx],eax") \
            and ins[2][0] == "ret" and False:
        pass
    if len(ins) == 4 and ins[3][0] == "ret" and ins[0][1] in ("eax,dwordptr[rdx]", "eax,[rdx]") \
            and ins[1] == ("cmp", "dwordptr[rcx],eax") and ins[2][0].startswith("set"):
        return ("dwordpred", ins[2][0], None)
    if len(ins) == 3 and ins[2][0] == "ret":
        a, b = ins[0], ins[1]
        if a[0] == "mov" and a[1] in ("eax,dwordptr[rdx]", "eax,[rdx]") and b[0] == "mov" and b[1] in ("dwordptr[rcx],eax", "[rcx],eax"):
            return ("copy", None, None)
    # a global object's address, or a global pointer loaded
    if len(ins) == 2 and ins[1][0] == "ret" and ins[0][0] == "lea" and ins[0][1].startswith("rax,[rip+"):
        return ("globaddr", None, None)
    if len(ins) == 2 and ins[1][0] == "ret" and ins[0][0] == "mov" and ins[0][1].startswith("rax,qwordptr[rip+"):
        return ("globptr", None, None)
    # one dword copied from the second argument into a field of the first
    if len(ins) == 3 and ins[2][0] == "ret" and ins[0][1] in ("eax,dwordptr[rdx]", "eax,[rdx]"):
        mm = re.match(r"dwordptr\[rcx\+0x([0-9a-f]+)\],eax", ins[1][1])
        if mm:
            return ("copyoff", int(mm.group(1), 16), None)
    # a member loaded and then handed to another function: a getter when that function is the identity
    # a field of the object the first member points at
    if len(ins) == 3 and ins[2][0] == "ret" and ins[0] == ("mov", "rax,qwordptr[rcx]"):
        mm = re.match(r"dwordptr\[rax\+0x([0-9a-f]+)\],edx", ins[1][1])
        if mm:
            return ("iset", int(mm.group(1), 16), 4)
        mm = re.match(r"byteptr\[rax\+0x([0-9a-f]+)\],dl", ins[1][1])
        if mm:
            return ("iset", int(mm.group(1), 16), 1)
        mm = re.match(r"eax,dwordptr\[rax\+0x([0-9a-f]+)\]", ins[1][1])
        if mm:
            return ("iget", int(mm.group(1), 16), 4)
        mm = re.match(r"eax,byteptr\[rax\+0x([0-9a-f]+)\]", ins[1][1])
        if mm:
            return ("iget", int(mm.group(1), 16), 1)
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

    books = {"identity": [], "zero": [], "get": [], "set": [], "addr": [], "copy": [], "getd": [], "setd": [],
             "const": [], "global": [], "twolvl": [], "ptradd": [], "nullpred": [], "twobytes": [], "dwordpred": [],
             "globaddr": [], "globptr": [], "copyoff": [], "memberget": [], "iget": [], "iset": [], "unknown": []}
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
    for a, off, _w in books["copyoff"][:limit]:
        name = "copyDwordTo%02X_%X" % (off, a)
        gen.append("/** RE 0x%X: copies one dword from the second argument into the field at +0x%02X. */" % (a, off))
        gen.append("inline void %s(void* destination, const void* source) {" % name)
        gen.append("    std::uint32_t value = 0;")
        gen.append("    std::memcpy(&value, source, sizeof(value));")
        gen.append("    std::memcpy(static_cast<unsigned char*>(destination) + 0x%02X, &value, sizeof(value));" % off)
        gen.append("}")
        gen.append("")
        implemented.append(a)
        tests.append("        { unsigned char s[8]; const std::uint32_t put = 0x0BADF00Du; std::memcpy(s, &put, sizeof(put));"
                     " lcns::dll::accessors::%s(object, s); std::uint32_t got = 0;"
                     " std::memcpy(&got, object + 0x%02X, sizeof(got)); CHECK(got == put); }   // RE 0x%X"
                     % (name, off, a))
    for a, off, target in books["memberget"][:limit]:
        if target not in (0x547610, 0x4F7030, 0x4F8350, 0x5C5F30, 0x5C5F50, 0x5C61D0, 0x5C5260, 0x548630, 0x5C61E0, 0x548380, 0x5C5270):
            continue   # only when the tail target is a known identity, otherwise this is a real wrapper
        name = "member%02X_%X" % (off, a)
        gen.append("/** RE 0x%X: returns the pointer held at +0x%02X, the tail call to 0x%X being the identity. */"
                   % (a, off, target))
        gen.append("inline void* %s(const void* object) {" % name)
        gen.append("    void* value = nullptr;")
        gen.append("    std::memcpy(&value, static_cast<const unsigned char*>(object) + 0x%02X, sizeof(value));" % off)
        gen.append("    return value;")
        gen.append("}")
        gen.append("")
        implemented.append(a)
        tests.append("        { const void* put = reinterpret_cast<const void*>(0x1234);"
                     " std::memcpy(object + 0x%02X, &put, sizeof(put));"
                     " CHECK(lcns::dll::accessors::%s(object) == put); }   // RE 0x%X" % (off, name, a))
    if books["globaddr"] or books["globptr"]:
        s_tmp = io.open(TOOLCHAIN, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        anchor3 = "    0xD59A0,  # xor eax, eax ; ret -- a default override returning zero"
        add = [anchor3]
        for a, _o, _w in books["globaddr"]:
            add.append("    0x%X,  # lea rax,[rip+..] ; ret -- the address of a global object" % a)
        for a, _o, _w in books["globptr"]:
            add.append("    0x%X,  # mov rax,[rip+..] ; ret -- loads a global pointer" % a)
        io.open(TOOLCHAIN, "w", encoding="utf-8", newline="\n").write(s_tmp.replace(anchor3, "\n".join(add), 1))
        print("g_toolchain.py       %d global accessors classified" % (len(books["globaddr"]) + len(books["globptr"])))
    for a, off, width in books["iget"][:limit]:
        bits = width * 8
        name = "iget%02X_%X" % (off, a)
        gen.append("/** RE 0x%X: reads the %d-bit field at +0x%02X of the object the first member points at. */"
                   % (a, bits, off))
        gen.append("inline std::uint%d_t %s(const void* object) {" % (bits, name))
        gen.append("    const unsigned char* inner = nullptr;")
        gen.append("    std::memcpy(&inner, object, sizeof(inner));")
        gen.append("    std::uint%d_t value = 0;" % bits)
        gen.append("    std::memcpy(&value, inner + 0x%02X, sizeof(value));" % off)
        gen.append("    return value;")
        gen.append("}")
        gen.append("")
        implemented.append(a)
        probe = {1: 0x5A, 4: 0x12345678}[width]
        tests.append("        { unsigned char inner[0x400]; std::memset(inner, 0, sizeof(inner));"
                     " const std::uint%d_t put = 0x%Xull; std::memcpy(inner + 0x%02X, &put, sizeof(put));"
                     " unsigned char outer[8]; unsigned char* p = inner; std::memcpy(outer, &p, sizeof(p));"
                     " CHECK(lcns::dll::accessors::%s(outer) == put); }   // RE 0x%X, read through the first member"
                     % (bits, probe, off, name, a))
    for a, off, width in books["iset"][:limit]:
        bits = width * 8
        name = "iset%02X_%X" % (off, a)
        gen.append("/** RE 0x%X: writes the %d-bit field at +0x%02X of the object the first member points at. */"
                   % (a, bits, off))
        gen.append("inline void %s(void* object, std::uint%d_t value) {" % (name, bits))
        gen.append("    unsigned char* inner = nullptr;")
        gen.append("    std::memcpy(&inner, object, sizeof(inner));")
        gen.append("    std::memcpy(inner + 0x%02X, &value, sizeof(value));" % off)
        gen.append("}")
        gen.append("")
        implemented.append(a)
        probe = {1: 0x5A, 4: 0x12345678}[width]
        tests.append("        { unsigned char inner[0x400]; std::memset(inner, 0, sizeof(inner));"
                     " unsigned char outer[8]; unsigned char* p = inner; std::memcpy(outer, &p, sizeof(p));"
                     " lcns::dll::accessors::%s(outer, 0x%Xull); std::uint%d_t got = 0;"
                     " std::memcpy(&got, inner + 0x%02X, sizeof(got)); CHECK(got == 0x%Xull); }   // RE 0x%X"
                     % (name, probe, bits, off, probe, a))
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
