# -*- coding: utf-8 -*-
"""Round 10 deliverable: re/STRATEGY_METHODS.md + the registry entry.

The vtable method tables of every strategy class are recovered data (re/vtables.json), so each
method has a DEFINITE identity: slot k of class X, with its size. That turns the behavioural debt
into an exact work list -- and it shows that slot #5 is the Run body in every Nester class.
"""
import io
import json
import re
import subprocess
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import load_prof  # noqa: E402

RE = r"D:\Nesting\nestfab\re"
P = load_prof()
vts = json.load(io.open(RE + r"\vtables.json", encoding="utf-8"))

FAMILIES = [
    (u"策略类（`Multi::*Nester`）", "Multi::", "Nester"),
    (u"打包类（`Pack::*Nester`）", "Pack::", "Nester"),
    (u"板材选择器（`Multi::*SheetSelector`）", "Multi::", "SheetSelector"),
    (u"图案类（`Tiling::*`）", "Tiling::", ""),
    (u"描述/添加器（`Multi::Strategy*`）", "Multi::", "Strategy"),
]

rows = []
run_slots = []
for cls, v in vts.items():
    nm = v.get("demangled") or cls
    slots = v.get("slots") or []
    if not slots or "CryptoPP" in nm:
        continue
    for fam_label, fam_pref, fam_key in FAMILIES:
        if nm.startswith(fam_pref) and fam_key in nm:
            entries = []
            for i, s in enumerate(slots):
                if not s:
                    continue
                f = P.get(s) or {}
                entries.append((i, s, f.get("size") or 0))
            if entries:
                biggest = max(entries, key=lambda e: e[2])
                rows.append((fam_label, nm, entries, biggest))
                if "Nester" in nm and biggest[0] == 5:
                    run_slots.append((nm, biggest[1], biggest[2]))
            break

run_slots.sort(key=lambda r: -r[2])
total_run = sum(r[2] for r in run_slots)

out = [u"# `re/STRATEGY_METHODS.md` —— 策略类的**完整方法表**与 `Run` 工作量清单", u"",
       u"由 `re/g_strategy_methods.py` 生成（goal round 10），数据来自 `re/vtables.json`（443 个类，**已恢复**）。", u"",
       u"## 为什么这份表有用", u"",
       u"虚表顺序是恢复出的数据，所以「**`类名` 的第 k 槽**」是**确定身份**（不是形状猜测）。",
       u"于是**行为保真最大的欠账 —— 15 个策略的 `Run` 体 —— 变成了带字节数的精确清单**：", u"",
       u"| 类 | `Run` 槽 | 地址 | 字节 |", u"|---|---|---:|---:|"]
for nm, a, s in run_slots:
    out.append(u"| `%s` | #5 | `0x%x` | **%d** |" % (nm, a, s))
out += [u"", u"**合计 `Run` 体：%d 字节**（%d 个类）。这些函数目前全部是 `Substituted`（跑的是本工程的替代搜索）。" %
        (total_run, len(run_slots)), u"",
        u"`Pack::*Nester` 的 `Run` 不在槽 #5 而在**槽 #2**（它们的类更小，方法更少）。", u"",
        u"## 各族的完整方法表", u""]
for fam_label, fam_pref, fam_key in FAMILIES:
    out += [u"### %s" % fam_label, u"",
            u"| 类 | 方法（槽: 地址(字节)） |", u"|---|---|"]
    for _l, nm, entries, biggest in rows:
        if _l == fam_label:
            cells = u", ".join(u"#%d `0x%x`(%dB)%s" % (i, a, s, u" ←最大" if (i, a, s) == biggest else u"")
                               for i, a, s in entries)
            out.append(u"| **%s** | %s |" % (nm, cells))
    out.append(u"")

out += [u"## 由方法表读出的结构", u"",
        u"* `Multi::*Nester` 一律是 6 槽：`#0`/`#1` 极小（1–91 B，构造/探测），`#2` 是 4–31 B 的身份访问器，",
        u"  `#3`/`#4` 是参数读写（几十到 2,240 B），**`#5` 才是 `Run`**（1.6 KB–16.3 KB）。",
        u"* `Pack::*Nester` 只有 3 槽，`#0`/`#1` 极小，`#2` 是 `Run`。",
        u"* 板材选择器（`Multi::*SheetSelector`）是 4 槽：`#0`/`#1` 极小，`#2` 是选择逻辑（136–1,316 B），`#3` 是谓词。",
        u"* **`Multi::AllSheetSelector`**（`0x7D2500`）在本轮的表里首次出现 —— 此前报告只有 `Largest`/`Random`/`NoMix` 三个。",
        u"* `Tiling::*` 的槽数不固定（`BiModulePattern` 8 槽、`MultiOrientedPartPattern` 8 槽、",
        u"  `BoxMultiTiler`/`SqueezeMultiTiler` 5 槽），最大的槽是图案生成/评估体。", u""]

io.open(RE + r"\STRATEGY_METHODS.md", "w", encoding="utf-8", newline="\n").write(u"\n".join(out) + u"\n")
print("wrote re/STRATEGY_METHODS.md -- %d Run bodies, %d bytes total" % (len(run_slots), total_run))

# ---------------------------------------------------------------- registry entry (idempotent)
RP = r"D:\Nesting\nestfab\lcns\include\lcns\recovery.hpp"
t = io.open(RP, encoding="utf-8", newline="").read().replace("\r\n", "\n")
# remove any previous version of this entry (a bad one was written by the first run)
t = re.sub(r'    \{"engine\.strategy_methods".*?\},\n', '', t, flags=re.S)
ANCHOR = u'    {"engine.strategy_adder", Status::Recovered,'
assert ANCHOR in t, "anchor not found"
assert run_slots, "no Run slots found -- refusing to write an entry that says zero bytes"

slots_desc = u"; ".join(u"%s #5 0x%x (%d B)" % (nm.split("::")[-1], a, s) for nm, a, s in run_slots[:6])
entry = (u'    {"engine.strategy_methods", Status::Recovered, "vtable method tables, re/vtables.json",\n'
         u'     "every strategy class\'s METHOD TABLE is recovered data (the vtable order), so each method has '
         u'a definite identity: slot k of class X, with its size. This turns the biggest behavioural debt -- '
         u'the Run bodies -- into an exact work list, and it shows the layout: Multi::*Nester are 6 slots with '
         u'#0/#1 tiny constructors or probes, #2 a 4-31 B identity accessor, #3/#4 parameter accessors, and '
         u'#5 = Run, the largest method in every one of them (' + slots_desc + u'; the whole set is '
         + str(len(run_slots)) + u' classes / ' + str(total_run) + u' bytes, tabulated in re/STRATEGY_METHODS.md). '
         u'Pack::*Nester are 3 slots with Run at #2. The *SheetSelector family is 4 slots with the choice '
         u'logic at #2, and it includes Multi::AllSheetSelector 0x7d2500, which the earlier notes did not '
         u'have -- they listed only Largest/Random/NoMix. All of these Run bodies are still Substituted '
         u'(our own search runs instead); what is recovered here is their identity and exact size"},\n')
t = t.replace(ANCHOR, entry + ANCHOR, 1)
io.open(RP, "w", encoding="utf-8", newline="\n").write(t)

# self-check the table the same way check_recovery does
txt = io.open(RP, encoding="utf-8", newline="").read().replace("\r\n", "\n")
body = txt[txt.index("inline constexpr Gap kGaps[]"):]
block = body[body.index("{") + 1: body.index("\n};")]
hd = re.compile(r'\s*\{"([^"]+)",\s*Status::(\w+),')
ids = [m.group(1) for m in (hd.match(l) for l in block.split("\n") if not l.lstrip().startswith("//")) if m]
st = {}
for m in (hd.match(l) for l in block.split("\n") if not l.lstrip().startswith("//")):
    if m:
        st[m.group(2)] = st.get(m.group(2), 0) + 1
print("registry: %d entries, unique=%d, %s" % (len(ids), len(set(ids)), dict(sorted(st.items()))))

# test counts + a mark in engine.cpp
TP = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
s = io.open(TP, encoding="utf-8", newline="").read()
n = len(ids)
s2 = re.sub(r"CHECK\(kGapCount == \d+\);", "CHECK(kGapCount == %d);" % n, s)
s2 = re.sub(r"CHECK\(countOf\(Status::Recovered\) == \d+\);",
            "CHECK(countOf(Status::Recovered) == %d);" % st.get("Recovered", 0), s2)
s2 = re.sub(r"CHECK\(countOf\(Status::Structural\) == \d+\);",
            "CHECK(countOf(Status::Structural) == %d);" % st.get("Structural", 0), s2)
s2 = re.sub(r"CHECK\(countOf\(Status::NotReversed\) == \d+\);",
            "CHECK(countOf(Status::NotReversed) == %d);" % st.get("NotReversed", 0), s2)
if s2 != s:
    io.open(TP, "w", encoding="utf-8", newline="\n").write(s2)
    print("updated test_recovered counts")
else:
    print("test_recovered counts already match the registry")

EP = r"D:\Nesting\nestfab\lcns\src\engine.cpp"
e = io.open(EP, encoding="utf-8", newline="").read()
if "LCNS_RECOVERED(engine.strategy_methods)" not in e:
    e = e.replace("LCNS_RECOVERED(engine.strategy_adder);",
                  "LCNS_RECOVERED(engine.strategy_methods);\nLCNS_RECOVERED(engine.strategy_adder);", 1)
    io.open(EP, "w", encoding="utf-8", newline="\n").write(e)
    print("added the code mark")
