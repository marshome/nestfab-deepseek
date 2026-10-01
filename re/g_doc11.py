# -*- coding: utf-8 -*-
"""Round 11: append the Run-body reading plan + the LimitedNester first pass, then commit."""
import io
import subprocess

E = r"D:\Nesting\nestfab\re\findings_engine.md"
t = io.open(E, encoding="utf-8").read().rstrip() + "\n"
S = u"""
---

## 附 6：策略 `Run` 体的读法（goal round 10-11）

### 附 6.1 方法与顺序

`re/STRATEGY_METHODS.md` 给出每个策略类的**完整方法表**，`Run` 是 `Multi::*Nester` 的**槽 #5**
（`Pack::*` 是槽 #2）。因此每个 `Run` 都有**确定身份与确切字节数**，可以按从小到大逐个读：

`LimitedNester 1,650` → `FilterNester 2,254` → `FlipNester 3,496` → `DatabaseNester 4,495` →
`RectangleNester 5,261` → `NoFillNester 8,440` → `CompactNester 9,393` → `MultiTorchNester 12,232` →
`RowNester 12,380` → `NestingNester 14,374` → `TilingNester 16,258`（合计 **90,233 B**）。

### 附 6.2 第一遍：`Multi::LimitedNester::Run`（`0x4AB40`，1,650 B / **324 条指令**）**[已证实 + 未解]**

**已证实**：

| 项 | 值 |
|---|---|
| 被调用者（12 个） | `0xB44D0`(531 B，23 个调用者)、`0x92ECB0`(791)、`0x51CC90`(312)、`0x7C1CF0`(200)、`0x62F280`(171)、`0x910AF0`(168)、`0xB4D20`(69)、`0x5F3920`(54)、`0x5F3900`(22)、`0x5F3960`(17)、`0x5F3980`(10)、`0x9984B0`(5，`operator delete`) |
| 字符串 | **一个都没有**（纯算法体） |
| 浮点常量 | `0.0`（`0x9AF9E8`，`4ABBA ucomisd`）、**`0.01`**（`0x9AF9F0`，`4B131 addsd`） |
| 立即数 | `1`×2、`16`×1、**`120`×2**、**`400`×2** |
| 字段阶梯 | `+0x8…+0x200` 密集出现（`+0x8/0x10/0x18/0x20/0x28/0x30/0x38/0x40/0x50/0x58/0x68/0x78/0x80/0x90/0xA8/0xC8/0xD8/0xE0/0xF0/0x100/0x108/0x110/0x118/0x120/0x128/0x150/0x170/0x180/0x1F0/0x1F8/0x200`） |

**可以说的**：它是一个**包装型 `Run`**（与 `Modified`/`Limited` 的语义一致）：调用共享辅助 `0xB44D0`，
用 `0.0`/`0.01` 做一次容差比较，并在一段约 `0x200` 字节的状态上迭代，另有 `120`/`400` 两个计数型字面量。
`0x5F3900/0x5F3920/0x5F3960/0x5F3980` 这四个 10–54 B 的极小函数同批出现，像是**计数器/上报**家族。

**尚**未**解**（本档不声称）：`120`/`400` 的具体含义（尝试次数？上限？缓冲尺寸？）、
`0x200` 字段阶梯对应哪个结构（`LimitedNester` 自身还是它持有的问题对象）、
`0.01` 是步长还是容差、以及它如何"限制"内部搜索。

### 附 6.3 状态

`strategy.limited` 仍是 `Substituted`（lcns 跑的是自研替代搜索）。本轮把它的**调用面、常量与字段阶梯**
变成了可复核记录，**没有**把它改判为已恢复 —— 要改判必须先把上面"未解"的部分读完。
"""
io.open(E, "w", encoding="utf-8", newline="\n").write(t + S)
print("findings_engine.md appendix 6 appended")

subprocess.run(["git", "-C", r"D:\Nesting\nestfab", "add", "-A"])
r = subprocess.run(["git", "-C", r"D:\Nesting\nestfab", "commit", "-q", "-m",
                    "re: start reading the strategy Run bodies (LimitedNester first pass)"],
                   capture_output=True, text=True)
print((r.stdout or r.stderr).strip()[:200] or "committed")
