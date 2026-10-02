# -*- coding: utf-8 -*-
"""Add the deep-chain release test, which check_recovery requires for a header that declares a name."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- the deep chain release (RE 0x923110)
    //
    // Thirty-five functions in the module are byte-identical to this one apart from their own addresses, so it is worth a test
    // rather than a note. The walk follows a link at +0x18, releases each node, and stops at null; the link must be read BEFORE the
    // release, which is what makes it safe.
    {
        struct Node { Node* link; int payload; };
        Node chain[3];
        chain[0].link = &chain[1]; chain[0].payload = 0;
        chain[1].link = &chain[2]; chain[1].payload = 1;
        chain[2].link = nullptr;   chain[2].payload = 2;

        int released = 0;
        lcns::releaseDeepChain(&chain[0], [&released](Node*) { ++released; });
        CHECK(released == 3);

        // a null head is a no-op, which is RE 0x923120
        released = 0;
        lcns::releaseDeepChain(static_cast<Node*>(nullptr), [&released](Node*) { ++released; });
        CHECK(released == 0);

        // a single node
        Node one;
        one.link = nullptr;
        released = 0;
        lcns::releaseDeepChain(&one, [&released](Node*) { ++released; });
        CHECK(released == 1);

        // the link offset, against owned_chain.hpp's +0x10
        CHECK(lcns::kDeepChainLink == 0x18);
        CHECK(lcns::kDeepChainLink != 0x10);
        // and linkAt reads exactly that offset
        CHECK(lcns::linkAt(&chain[0]) == &chain[1]);
        CHECK(lcns::linkAt(&chain[2]) == nullptr);
        CHECK(reinterpret_cast<unsigned char*>(&chain[0].link) - reinterpret_cast<unsigned char*>(&chain[0])
              == static_cast<std::ptrdiff_t>(lcns::kDeepChainLink));
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "releaseDeepChain" in text:
        print("already present")
        return 0
    if '#include "lcns/chain_release.hpp"' not in text:
        anchor = '#include "lcns/variant.hpp"\n'
        assert anchor in text, "the variant include is gone"
        text = text.replace(anchor, anchor + '#include "lcns/chain_release.hpp"\n', 1)
        print("added the include")
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("added the deep chain test; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
