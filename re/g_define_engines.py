# -*- coding: utf-8 -*-
"""Define the six engines' run stubs, so the declarations link, and say at each one what is unread."""
import io

PATH = r"D:\Nesting\nestfab\lcns\src\engines.cpp"

STUBS = '''
// The other six. Each is UNREAD beyond what its declaration records, and each says so at its own body rather than in a comment elsewhere
// -- a stub that returns nullptr silently would be indistinguishable from an engine that does nothing, which is the same class of
// mistake as a constant standing in for a class.

void* MultiEngine::run(const void*, double, void*, void* result) {
    return result;      // RE 0x755050 is 3795 bytes and NOT READ; the buffer is what every Run in this family returns
}

void* DelayedEngine::run(const void*, double, void*, void* result) {
    return result;      // RE 0x756EC0 is 750 bytes and NOT READ
}

void* NestingEngine::run(const void*, double, void*, void* result) {
    return result;      // RE 0x757250 is 1975 bytes and NOT READ; 0x757AE0 is a second entry to this class
}

void* CompositeEngine::run(const void*, double, void*, void* result) {
    // RE 0x759B70 is 8230 bytes and read far enough to establish what it does NOT do: it calls no other engine's Run, and it walks a
    // container of 16 byte records reached through its second argument's +0x10 and +0x18, accumulating into locals.
    return result;
}

void* EquivalentEngine::run(const void*, double, void*, void* result) {
    return result;      // RE 0x75BCC0 is 3569 bytes and NOT READ
}

void* CloudEngine::run(const void*, double, void*, void* result) {
    return result;      // RE 0x26A60 is 2284 bytes and NOT READ; the cloud gate is 0x2AB0, a different function
}

'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "MultiEngine::run" in text:
        print("already defined")
        return 0
    marker = "}  // namespace lcns"
    assert marker in text, "the namespace close is gone"
    text = text.replace(marker, STUBS.strip("\n") + "\n\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("six stubs added, each naming what is unread")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
