# -*- coding: utf-8 -*-
"""Fix the deep-chain test: the node must actually have its link at +0x18.

The segfault was the test's fault and the warning before it was a true positive that I did not read carefully enough. `linkAt` reads
at +0x18 because that is where the module's chain link is; my test used `struct Node { Node* link; int payload; }`, which is 0x10
bytes, so `linkAt` read past the array and the walk followed whatever was there. Two signals said so -- `-Warray-bounds` naming
"array subscript 7 outside array bounds of Node [3]" -- and both were dismissed as noise about the test's shape.

So the node now has its link AT +0x18, with the padding written out, and the test asserts the offset rather than assuming it. A test
for a routine whose whole content is an offset must place the field at that offset, or it is testing the wrong thing.
"""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

OLD_START = "    // ---------------------------------------------------------------- the deep chain release (RE 0x923110)"
OLD_END = '    return check::finish("test_recovered");'

NEW = '''    // ---------------------------------------------------------------- the deep chain release (RE 0x923110)
    //
    // Thirty-five functions in the module are byte-identical to this one apart from their own addresses. The walk follows a link at
    // +0x18, releases each node and stops at null, and the link is read BEFORE the release.
    //
    // THE NODE MUST HAVE ITS LINK AT +0x18. A first version of this test used `struct Node { Node* link; int payload; }`, which is
    // 0x10 bytes, so the walk read past the array -- and the compiler had said so with `-Warray-bounds`. A test for a routine whose
    // whole content is an offset must place the field at that offset.
    {
        struct alignas(8) Node {
            unsigned char reserved[0x18];        // the module's chain link is at +0x18, not at +0x00
            Node* link;
            int payload;
        };
        static_assert(offsetof(Node, link) == 0x18, "the link must be where RE 0x92313C reads it");
        CHECK(offsetof(Node, link) == lcns::kDeepChainLink);
        CHECK(lcns::kDeepChainLink == 0x18);
        CHECK(lcns::kDeepChainLink != 0x10);      // owned_chain.hpp's link is at +0x10

        Node chain[3];
        for (int i = 0; i < 3; ++i) {
            for (unsigned char& byte : chain[i].reserved) {
                byte = 0;
            }
            chain[i].payload = i;
        }
        chain[0].link = &chain[1];
        chain[1].link = &chain[2];
        chain[2].link = nullptr;

        // the link read, against a live chain
        CHECK(lcns::linkAt(&chain[0]) == &chain[1]);
        CHECK(lcns::linkAt(&chain[1]) == &chain[2]);
        CHECK(lcns::linkAt(&chain[2]) == nullptr);

        // the walk, on a chain the release function detaches as it goes -- which is what releasing a node means
        Node a, b, c;
        for (Node* node : {&a, &b, &c}) {
            for (unsigned char& byte : node->reserved) {
                byte = 0;
            }
        }
        a.link = &b; b.link = &c; c.link = nullptr;
        int released = 0;
        lcns::releaseDeepChain(&a, [&released](Node* node) {
            ++released;
            node->link = nullptr;
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
        for (unsigned char& byte : one.reserved) {
            byte = 0;
        }
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
    text = text[:start] + NEW + text[end:]
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("fixed the deep chain test; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
