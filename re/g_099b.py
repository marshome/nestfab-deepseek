# -*- coding: utf-8 -*-
"""Round 19: pin the 0.99 constant -- findings + a hedged constant in lcns + test + commit."""
import io
import re
import subprocess

RE = r"D:\Nesting\nestfab\re"
E = RE + r"\findings_engine.md"
t = io.open(E, encoding="utf-8").read().rstrip() + "\n"
S = u"""
### 附 6.10 `0.99`（`0x9B15E0`）的语义 **[推断，证据充分]**

`0x73280` 里该常量有两处引用，**两处上下文形状完全一致**：

```
754ba  subsd xmm1, [rsp+0x3c8]     ; xmm1 = (a - c)
754c3  subsd xmm0, [rsp+0x3d0]     ; xmm0 = (b - d)
754cc  mulsd xmm1, xmm0            ; xmm1 = 面积 (Δx · Δy)
754d0  pxor xmm0, xmm0 / jne …     ; 走另一条支路时
754e9  addsd xmm0, xmm0            ;   面积 ×2
754ed  mulsd xmm0, [0x9B15E0]      ;   ×0.99      ← 本常量
754f5  ucomisd xmm0, xmm1
754f9  jbe 0x74bf2                 ; 0.99·X <= 面积 则跳过
```

**推断**：`0.99` 是**面积覆盖的松弛系数** —— 判据是「候选面积 与 `0.99 × 参考面积` 的比较」，
即 **1% 覆盖松弛**。这与我在 `..\\nesting\\algos\\bucket_manager.hpp` 断言里读到的
`eval.m_c <= max_surface * 1.05`（5% 上界）属于**同一类机制**（都用面积乘一个接近 1 的系数做容差）。

**为什么标"推断"而不是"已证实"**：算术形状（成对差分相乘=面积、比较、`jbe` 极性）证据充分，
但**没有符号或字符串直接说明**它是"覆盖松弛"；语义是从算式反推的。
已按此谨慎命名落到 `lcns::kAreaCoverageSlack`，注释里写明证据与推断的边界。
"""
io.open(E, "w", encoding="utf-8", newline="\n").write(t + S)
print("findings 6.10 appended")

H = r"D:\Nesting\nestfab\lcns\include\lcns\engine.hpp"
h = io.open(H, encoding="utf-8", newline="").read().replace("\r\n", "\n")
h = re.sub(r"// RE 0x9b15e0.*?\n\n", "", h, flags=re.S)
BLK = (u"// RE 0x9B15E0 -- the double 0.99, referenced twice inside 0x73280 (at 0x754ED and 0x75EF3) in\n"
       u"// the same shape: two pairs of doubles are differenced and multiplied (an AREA), one branch\n"
       u"// doubles it, the result is scaled by this constant and compared with `ucomisd` against the\n"
       u"// other area, with `jbe` skipping when 0.99*X <= area. So the constant is an area-coverage\n"
       u"// slack of about one percent. The ARITHMETIC is evidence; the NAME is an inference -- no symbol\n"
       u"// or string states this meaning. Compare the 1.05 upper bound asserted in bucket_manager.hpp:\n"
       u"// both are area tolerances built the same way.\n"
       u"inline constexpr double kAreaCoverageSlack = 0.99;   // RE 0x9B15E0 via 0x754ED / 0x75EF3\n\n")
assert "inline constexpr const char* kTraceFlip" in h
h = h.replace(u"// RE trace prefixes", BLK + u"// RE trace prefixes", 1)
io.open(H, "w", encoding="utf-8", newline="\n").write(h)
print("engine.hpp: kAreaCoverageSlack added")

T = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
s = io.open(T, encoding="utf-8", newline="").read().replace("\r\n", "\n")
if "kAreaCoverageSlack" not in s:
    s = s.replace(u"    // --- recovered trace strings",
                  u"    // the 0.99 area coverage slack (RE 0x9b15e0, used at 0x754ed / 0x75ef3)\n"
                  u"    CHECK(kAreaCoverageSlack == 0.99);\n\n"
                  u"    // --- recovered trace strings", 1)
    io.open(T, "w", encoding="utf-8", newline="\n").write(s)
    print("test assertion added")

subprocess.run(["git", "-C", r"D:\Nesting\nestfab", "add", "-A"])
r = subprocess.run(["git", "-C", r"D:\Nesting\nestfab", "commit", "-q", "-m",
                    "re: pin the 0.99 constant -- it is an area coverage slack in the placement test"],
                   capture_output=True, text=True)
print((r.stdout or r.stderr).strip()[:200] or "committed")
