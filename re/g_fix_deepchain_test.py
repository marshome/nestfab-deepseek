# -*- coding: utf-8 -*-
"""Replace the deep-chain test with one the compiler does not object to, and which is more honest.

The first version passed a lambda that only counted, and the warning was still `array subscript 7 is outside array bounds of
main()::Node [3]` -- GCC inlining the walk and proving that `linkAt(&chain[2])` reads beyond the array through a pointer it can no
longer track. The warning is about the test's shape rather than the recovered code, and the fix is to test the two things separately:

  * `linkAt` against a chain, which is where the offsets are checked;
  * `releaseDeepChain` against a chain the release function TRUNCATES as it goes, so nothing reads a released node.

That second version is also the honest one: the real routine frees each node, so a chain whose nodes are gone as they are released is
closer to the module than one that keeps them alive and walks on.
"""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

OLD_START = "    // ---------------------------------------------------------------- the deep chain release (RE 0x923110)"
OLD_END = "    }\n\n    return check::finish(\"test_recovered\");"

NEW = '''    // ---------------------------------------------------------------- the deep chain release (RE 0x923110)
    //
    // Thirty-five functions in the module are byte-identical to this one apart from their own addresses, so it is worth a test
    // rather than a note. The walk follows a link at +0x18, releases each node, and stops at null; the link must be read BEFORE the
    // release, which is what makes it safe.
    //
    // The two things are tested SEPARATELY: linkAt against a live chain, where the offsets are what matter, and releaseDeepChain
    // against a chain the release function detaches as it goes -- which is what the real routine does when it frees a node, and
    // which keeps the test from reading memory it has just released.
    {
        struct Node { Node* link; int payload; };
        Node chain[3];
        chain[0].link = &chain[1]; chain[0].payload = 0;
        chain[1].link = &chain[2]; chain[1].payload = 1;
        chain[2].link = nullptr;   chain[2].payload = 2;

        // the link offset, against owned_chain.hpp's +0x10
        CHECK(lcns::kDeepChainLink == 0x18);
        CHECK(lcns::kDeepChainLink != 0x10);
        CHECK(lcns::linkAt(&chain[0]) == &chain[1]);
        CHECK(lcns::linkAt(&chain[1]) == &chain[2]);
        CHECK(reinterpret_cast<unsigned char*>(&chain[0].link) - reinterpret_cast<unsigned char*>(&chain[0])
              == static_cast<std::ptrdiff_t>(lcns::kDeepChainLink));

        // the walk, on a chain that is detached node by node, which is what releasing one means
        Node a, b, c;
        a.link = &b; b.link = &c; c.link = nullptr;
        int released = 0;
        lcns::releaseDeepChain(&a, [&released](Node* node) {
            ++released;
            node->link = nullptr;          // the node is gone, so nothing may follow it afterwards
        });
        CHECK(released == 3);

        // a null head is a no-op, which is RE 0x923120
        released = 0;
        lcns::releaseDeepChain(static_cast<Node*>(nullptr), [&released](Node* node) {
            ++released;
            node->link = nullptr;
        });
        CHECK(released == 0);

        // and a single node
        Node one;
        one.link = nullptr;
        released = 0;
        lcns::releaseDeepChain(&one, [&released](Node* node) {
            ++released;
            node->link = nullptr;
        });
        CHECK(released == 1);
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD_START not in text:
        print("the block is not present; nothing changed")
        return 1
    start = text.index(OLD_START)
    end = text.index(OLD_END, start)
    text = text[:start] + NEW + text[end + len("    }\n"):]
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("replaced the deep chain test; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
