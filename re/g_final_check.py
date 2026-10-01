"""Final acceptance: cross-check the residual list against the code's recovered primitives.

(a) enumerate every residual marker in the re/ documents, so nothing is silently dropped;
(b) enumerate the recovered primitives that should exist in lcns/, with their RE addresses.
"""
import io
import os
import re

RE = r"D:\Nesting\nestfab\re"
LC = r"D:\Nesting\nestfab\lcns"


def read(p):
    try:
        return io.open(p, encoding="utf-8").read()
    except Exception:
        return ""


docs = {}
for name in ("REPORT.md", "findings_lp_use.md", "findings_lp.md", "findings_geometry.md",
             "findings_engine.md", "findings_features.md", "findings_cloud_lic.md"):
    docs[name] = read(os.path.join(RE, name))

print("=== (a) residual markers per document ===")
for name, t in docs.items():
    unc = t.count("\u672a\u786e\u8ba4")          # 未确认
    unre = t.count("\u4e0d\u53ef\u6062\u590d")     # 不可恢复
    infer = t.count("[\u63a8\u65ad]")              # [推断]
    print("   %-26s 未确认=%-4d 不可恢复=%-3d [推断]=%-4d  bytes=%d"
          % (name, unc, unre, infer, len(t)))

print()
print("=== (a2) the consolidated residual table (REPORT section 10.3) ===")
report = docs["REPORT.md"]
i = report.find("### 10.3")
j = report.find("### 10.4")
if i >= 0 and j > i:
    for line in report[i:j].split("\n"):
        if line.startswith("| ") and not line.startswith("| \u9879") and "---" not in line:
            print("   " + line[:150])
else:
    print("   (section 10.3 not found)")

print()
print("=== (b) recovered primitives present in the code ===")
code = {}
for root, _d, files in os.walk(LC):
    for f in files:
        if f.endswith((".hpp", ".cpp", ".inc")):
            p = os.path.join(root, f)
            code[os.path.relpath(p, LC)] = read(p)
allcode = "\n".join(code.values())

EXPECT = [
    ("0x5C22D0", "angleToFixedDegrees"), ("0x9BCFD8", "kSqueezeAlignmentTolerance"),
    ("0x9BCFC0", "kSqueezeParallelTolerance"), ("0x9BCEB0", "kCandidateHeightScale"),
    ("0x9BCF48", "kScoreUnset"), ("0x134F30", "nodeLength"),
    ("0x134F50", "nodeLengthY"), ("0x134F90", "nodeFlag40"),
    ("0x135010", "nodeFlag98"), ("0x136CB0", "candidateScore"),
    ("0x137800", "orderedAddElement"), ("0x5C2E40", "authorized"),
    ("0x5CEE50", "angleTransform"), ("0x5D38C0", "transformedHeight"),
    ("0x5D3BFF", "transformX"), ("0x5D3C17", "transformDet"),
    ("0x137FE0", "drainSources"), ("0x271000000000", "kSourceRecordCap"),
    ("0x1331A0", "itemContainerOffset"), ("0x136350", "kScoreNodeSize"),
    ("0x137C83", "elementScore"), ("0x1333D0", "kItemSize"),
]
bad = 0
for addr, sym in EXPECT:
    has_addr = addr in allcode
    has_sym = sym in allcode
    if not (has_addr and has_sym):
        bad += 1
    print("   %-16s %-30s addr:%-5s sym:%-5s" % (addr, sym, "OK" if has_addr else "MISS",
                                                 "OK" if has_sym else "MISS"))
print("   %d/%d primitives fully present in the code" % (len(EXPECT) - bad, len(EXPECT)))
print("   code files scanned: %d" % len(code))
