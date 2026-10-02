# -*- coding: utf-8 -*-
"""Add the module-switch test, which check_recovery requires for a header that declares a name."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- the module switch pair (RE 0x9AF0 and 0x64B2C0)
    //
    // Two domain functions in different closures read the SAME flag and the SAME object and call the same gate, which is what makes
    // the state shared rather than local. The assertions are about the ARITHMETIC OF THE ADDRESSES, because that is the whole claim:
    // the object is the flag's neighbour, and the flag is not the logger's switch.
    {
        CHECK(lcns::kModuleSwitchFlag == 0xB1F050);
        CHECK(lcns::kModuleSwitchObject == 0xB1F058);
        CHECK(lcns::kModuleSwitchObject == lcns::kModuleSwitchFlag + 8);   // the 8 bytes between them
        CHECK(lcns::kModuleSwitchGate == 0x63F6C0);
        // and it is NOT the logger's own switch, which is 0x38 before it
        CHECK(lcns::kLoggerSwitch == 0xB1F018);
        CHECK(lcns::kLoggerSwitch != lcns::kModuleSwitchFlag);
        CHECK(lcns::kLoggerSwitch + 0x38 == lcns::kModuleSwitchFlag);
        // two independent sites, which is the evidence that the state is module-wide
        CHECK(lcns::kModuleSwitchSiteA == 0x9AF0);
        CHECK(lcns::kModuleSwitchSiteB == 0x64B2C0);
        CHECK(lcns::kModuleSwitchSiteA != lcns::kModuleSwitchSiteB);
        // the enable test, which is `test al, al` then `je` at both sites
        CHECK(lcns::moduleSwitchEnabled(0) == false);
        CHECK(lcns::moduleSwitchEnabled(1) == true);
        CHECK(lcns::moduleSwitchEnabled(0xFF) == true);
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "kModuleSwitchFlag" in text:
        print("already present")
        return 0
    if '#include "lcns/module_switch.hpp"' not in text:
        anchor = '#include "lcns/chain_release.hpp"\n'
        assert anchor in text, "the chain_release include is gone"
        text = text.replace(anchor, anchor + '#include "lcns/module_switch.hpp"\n', 1)
        print("added the include")
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("added the module switch test; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
