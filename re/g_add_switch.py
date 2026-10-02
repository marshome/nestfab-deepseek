# -*- coding: utf-8 -*-
"""Land the global switch, and every ordinal that shares its address.

The whole closure is sixteen bytes across three functions, read in round 505:

    0xAFE0  test ecx, ecx ; setne cl ; movzx ecx, cl ; jmp 0x1B270
    0x1B270 movzx ecx, cl ; jmp 0x60A610
    0x60A610 mov byte ptr [rip + 0x518D3A], cl ; ret

so the export takes one integer, normalises it to zero or one, and stores that byte into a module global. The first
argument is the value, not an object: the test is on ecx, which is the first integer argument.

A module global is something a reimplementation can hold faithfully, unlike the version strings the original returns by
address, so this one is implemented rather than excused. The address of the global is not reproduced, and it does not need
to be: nothing outside the module can observe the original address, only the value's effect on behaviour.

Because two ordinals can share one address in this module, the script collects every ordinal whose rva is 0xAFE0 and
forwards all of them.
"""
import io
import json
import os

ROOT = r"D:\Nesting\nestfab"
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp")
SRC = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")
MAP = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")
TEST = os.path.join(ROOT, "lcns", "tests", "test_exports.cpp")

DECL = '''/** RE 0xAFE0 through 0x1B270: normalises the argument to zero or one. */
void setModuleSwitch(int value);
/** RE 0x60A610: reads back the byte the switch writes, so the behaviour can be checked. */
unsigned char moduleSwitch();

'''

BODY = '''namespace {
// RE 0x60A610 writes the byte at rip + 0x518D3A. The address is the original image's and cannot be reproduced, but the
// value can, and that is what any caller can observe.
unsigned char g_moduleSwitch = 0;
}  // namespace

void setModuleSwitch(int value) {
    // RE 0xAFE0: test, setne, movzx -- any non-zero becomes exactly one
    g_moduleSwitch = (value != 0) ? static_cast<unsigned char>(1) : static_cast<unsigned char>(0);
}

unsigned char moduleSwitch() {
    return g_moduleSwitch;
}

'''

TESTS = '''    // ------------------- the module switch, whose whole closure is sixteen bytes
    {
        lcns::dll::exports::impl::setModuleSwitch(0);
        CHECK(lcns::dll::exports::impl::moduleSwitch() == 0);
        lcns::dll::exports::impl::setModuleSwitch(7);
        CHECK(lcns::dll::exports::impl::moduleSwitch() == 1);    // any non-zero becomes exactly one (RE 0xAFE2)
        lcns::dll::exports::impl::setModuleSwitch(-1);
        CHECK(lcns::dll::exports::impl::moduleSwitch() == 1);
        lcns::dll::exports::impl::setModuleSwitch(0);
        CHECK(lcns::dll::exports::impl::moduleSwitch() == 0);
    }

    return check::finish("exports");'''


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    table = json.loads(io.open(os.path.join(ROOT, "re", "exports_table.json"), encoding="utf-8").read())
    ords = []
    for e in table:
        if e["rva"] == 0xAFE0:
            ords.append((e.get("ords") or [0])[0])   # primary ordinal only: the map contract requires ordinal0
    assert ords, "no ordinal maps to 0xAFE0"
    print("ordinals sharing 0xAFE0: %s" % sorted(ords))

    h = read(HDR)
    a = "void setShearMode(void* order, int value);"
    assert a in h, "setShearMode declaration not found"
    write(HDR, h.replace(a, DECL + a, 1))
    print("exports_impl.hpp  switch declared")

    s = read(SRC)
    b = "void setShearMode(void* order, int value)"
    assert b in s, "setShearMode body not found"
    write(SRC, s.replace(b, BODY + b, 1))
    print("exports_impl.cpp  switch and its reader")

    m = read(MAP)
    c = "    {33, reinterpret_cast<void*>(&lcns::dll::exports::impl::getSolutionIdentity)},  // GetSolution"
    assert c in m, "the GetSolution forwarding row was not found"
    rows = "\n".join("    {%d, reinterpret_cast<void*>(&lcns::dll::exports::impl::setModuleSwitch)},"
                     "  // shares RE 0xAFE0" % o for o in sorted(ords))
    write(MAP, m.replace(c, c + "\n" + rows, 1))
    print("exports_forwarding.inc  %d rows" % len(ords))

    e = read(TEST)
    f = '    return check::finish("exports");'
    assert f in e, "the exports finish anchor is missing"
    e = e.replace(f, TESTS, 1)
    start = e.find("const bool expected = ")
    assert start > 0
    end = e.find(";", start)
    extra = "".join(" || e->ordinal0 == %d" % o for o in sorted(ords))
    e = e[:end] + extra + e[end:]
    old = "CHECK(ex::forwardedCount() == 29u);"
    assert old in e, "the forwardedCount assertion was not found at 29"
    e = e.replace(old, "CHECK(ex::forwardedCount() == %du);" % (29 + len(ords)), 1)
    write(TEST, e)
    print("test_exports.cpp  switch checked, count 29 -> %d" % (29 + len(ords)))
    print("")
    print("done. Expected forwardedCount %d" % (29 + len(ords)))


if __name__ == "__main__":
    main()
