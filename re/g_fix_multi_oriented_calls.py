# -*- coding: utf-8 -*-
"""Update MultiOrientedPartPattern's constructor, its two call sites, and the test."""
import io
import sys

SRC = r"D:\Nesting\nestfab\lcns\src\tiling.cpp"
NESTER = r"D:\Nesting\nestfab\lcns\src\nester.cpp"
TEST = r"D:\Nesting\nestfab\lcns\tests\test_tiling.cpp"

CTOR = '''// RE 0x4F2910: the class is the 0x90 byte object the routine allocates, its vtable is 0xA3D380 (base 0xA3D370), and it copies 0x70 bytes of
// the configuration into +8 through +0x78. **The `{object, control}` pair the caller receives is a reference-counted handle and is not part of
// this class**, which is why this constructor takes the configuration rather than an index.
MultiOrientedPartPattern::MultiOrientedPartPattern(const PatternConfig& config)
    : capacity_(4),                       // RE 0x4F2936: mov dword [rbx + 0x80], 4
      limit_(0xD18C2E2800ull) {           // RE 0x4F29C4: movabs rax, 0xD18C2E2800
    std::memcpy(inline_.bytes, config.bytes, sizeof(inline_.bytes));   // RE 0x4F2943 .. 0x4F29B6, 0x70 bytes
}'''


def main():
    text = io.open(SRC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    old = "MultiOrientedPartPattern::MultiOrientedPartPattern(int partIndex) : partIndex_(partIndex) {}"
    if old not in text:
        print("REFUSING: the old constructor is not found")
        return 2
    text = text.replace(old, CTOR, 1)
    io.open(SRC, "w", encoding="utf-8", newline="\n").write(text)
    print("rewrote the constructor")

    for path, old_call, new_call in (
            (NESTER, "tiling::MultiOrientedPartPattern pat(static_cast<int>(top));",
             "// RE 0x4F2910 takes a configuration and copies 0x70 bytes of it; `top` is what the model uses to fill one\n"
             "    tiling::MultiOrientedPartPattern::PatternConfig patternConfig;\n"
             "    std::memcpy(patternConfig.bytes, &top, std::min(sizeof(top), sizeof(patternConfig.bytes)));\n"
             "    tiling::MultiOrientedPartPattern pat(patternConfig);"),
            (TEST, "MultiOrientedPartPattern pat(3);",
             "MultiOrientedPartPattern::PatternConfig config;\n        MultiOrientedPartPattern pat(config);"),
            (TEST, "MultiOrientedPartPattern(0).layout(100.0, 100.0, 0)",
             "MultiOrientedPartPattern(MultiOrientedPartPattern::PatternConfig{}).layout(100.0, 100.0, 0)")):
        body = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        if old_call in body:
            body = body.replace(old_call, new_call, 1)
            io.open(path, "w", encoding="utf-8", newline="\n").write(body)
            print("%s: updated a call site" % path.rsplit("\\", 1)[-1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
