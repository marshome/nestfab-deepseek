# 数学优化子系统逆向报告 — LP / 列生成 (Dantzig–Wolfe) 机制

> ## ⚠️ 本文件 §0 与 §6 的"死代码"结论已作废
>
> **作废日期说明**：`§6` 用"vtable **头部**地址引用数 = 0"判定 `Lp::`/`Coin::CoinLP`/`Prc::`/`Row::`
> 整套为"已编译但未接线"。这个方法是错的：C++ 的 vptr 存的是 **vtable 地址点（`vtable+16`）**，
> 代码里只出现地址点。改用地址点重扫后结论反转为"**被构造**"（见 `REPORT.md` §7.3），
> 并已进一步证明 **`Coin::CoinLP` 被求解、且解被消费**。
>
> **权威版本**：`REPORT.md` §7.3 与新增的 [`findings_lp_use.md`](findings_lp_use.md)
> （"COIN-OR 的使用面"）。该文给出：`Coin::CoinLP` 的 13 个虚槽逐个定性、
> `BuildAndSolveLp`（`0x7D7200`，`..\multi\database.cpp`）的完整伪代码、
> **Clp 实际在解的 LP 的数学形式**（板材选择集合覆盖：`min Σ price(s)·x_s`,
> `s.t. Σ_s count(s,p)·x_s ≥ demand(p)`）、以及解被回映到板材的消费点。
>
> 下面保留原文以便追溯，但 **§0 表格中"没有/死代码/没有回流"三处与 §6 全节不可再引用**。

目标文件：`D:\Nesting\nestfab\libcns_dump_64.dll`（MD5 `01fea4b73a33dd233c66ca76235313fa`，内存 dump，ImageBase `0x6B4C0000`，非加载型）。
所有地址均为 **RVA**。文中标注 **[已证实]** / **[推断]** / **[未确认]**。

---

## 0. 结论速览（TL;DR）

| 问题 | 结论 |
|---|---|
| 列生成真的被用于排版吗？ | **列生成没有；但 LP 被真实使用。** `Prc::`/`Row::` 的定价/行去重仍只见构造与自洽接口；而 **`Coin::CoinLP`（Clp 包装）被 `BuildAndSolveLp`（`0x7D7200`，`..\multi\database.cpp`）驱动、求解，解由 slot 10 取回并回映到板材**。~~原文"整套是未实例化的死代码"~~ **已作废**。 **[已证实，见 [`findings_lp_use.md`](findings_lp_use.md)]** |
| 主问题是什么？ | **不是 Dantzig–Wolfe 主问题**，而是一条**板材选择集合覆盖 LP**：`min Σ_sheet price(s)·x_s`，`s.t. 对每个零件 p: Σ_sheet count(s,p)·x_s ≥ demand(p)`，`x ≥ 0`。由 `Coin::CoinLP`（Clp 1.15.3 封装，`vptr[+0]` + 求解器 `[+8]`，13 个虚槽）承载。 **[已证实]** |
| 定价子问题是什么？ | `Prc::PriceComputer` 族是 **beam search 候选（pattern/column）的定价器**，按部件的**几何量度**打分（Box 面积 / Hull / Alpha 面系数 / 线性组合）。它由 `..\nesting\algos\old_beam.cpp` 这条 beam 搜索路径**直接函数调用**（不经 vtable），不是 master problem 的对偶定价。 **[已证实（调用点）+ 推断（语义）]** |
| 默认定价变体？ | ~~**未确认**。四个定价器都没有构造函数被调用~~ **已结案：没有"默认变体"。** 构造是"`operator new` + 直接写 vtable"的**内联**形式，所以没有 C++ 构造函数 `call` 点（这正是旧结论的成因）。`0x4D64C0` 在 `0x4D6890` 起把 **Box + Hull + Alpha×2 四个子定价器全部构造**，交给 `Prc::LinearCombinationPricer` 按 **5 个权重**（`obj[+0x00/+0x08/+0x10/+0x18/+0x20]`）加权平均。六个构造点：`0x4D9AD0`=Box、`0x4D9B00`=Hull、`0x4D9B30`=Alpha、`0x4D9F80`=LinearCombination，另两个 LinearCombination 变体 `0x4D9CD0`/`0x4D9DE0` **无调用者**。 **[已证实，见 [`findings_lp_use.md`](findings_lp_use.md) §9]** |
| 结果如何回流？ | **LP 路径有回流**：`0x6A6AD0`（Database 族）在 `BuildAndSolveLp` 成功后 `call [vptr+0x50]`（slot 10 → 求解器 `vt+0x228`）取解向量，再回映到板材记录。~~原文"没有回流、没有任何调用者"~~ **已作废**。 beam 路径的定价结果则进入 `m_prices[]`，被 `Pack::KnapsackNester::Run`（`..\tiling\packer.cpp:410`）以断言 `prices.size() == m_problem.GetNumberOfParts()` 消费；两者**不是同一物**。 **[已证实]** |
| LSQR 终止串块 `0x9A74A0` | 与本优化栈**无关**，是**静态链接的 LSQR**（迭代最小二乘）残留；实现体已定位在 **`0x3B84E0`**。 **[已证实]** |

---

## 1. RTTI / vtable 事实（可复现）

### 1.1 类层次（typeinfo 链）

typeinfo 对象位于 `0xA17D40`–`0xA17EB8`，结构为 `{ &_ZTI<base>, &_ZTS<name> }`（SI 型）：

| typeinfo RVA | 名称字符串 RVA | mangled | 基类指针 |
|---|---|---|---|
| `0xA17D40` | `0xA22240` | `N2Lp13LinearProgramE` | `Prc::PriceComputer` (`0xA3ADA0`) |
| `0xA17D50` | `0xA22280` | `N3Prc13PriceComputerE` | `0xA3ADA0`（抽象基类根） |
| `0xA17D60` | `0xA222C0` | `N3Prc16BoxPriceComputerE` | `0xA17D50` |
| `0xA17D80` | `0xA222E0` | `N3Prc17HullPriceComputerE` | `0xA17D50` |
| `0xA17DA0` | `0xA22300` | `N3Prc18AlphaPriceComputerE` | `0xA17D50` |
| `0xA17DC0` | `0xA22320` | `N3Prc23LinearCombinationPricerE` | `0xA17D50` |
| `0xA17DE0` | `0xA22350` | `N3Row14BasicDistancerE` | `0xA17E20` (`Row::Distancer`) |
| `0xA17E00` | `0xA22370` | `N3Row8SqueezerE` | `0xA17E20` |
| `0xA17E20` | `0xA22380` | `N3Row9DistancerE` | `0xA3ADA0`（抽象基类根） |
| `0xA17EA0` | `0xA22410` | `N4Coin6CoinLPE` | `0xA17EB0` (`Lp::LinearProgram`) |

`Coin::CoinLP` **继承 `Lp::LinearProgram`**（typeinfo 基类指针 `0xA17EB0` 指向 `LinearProgram`；`0xA17EB0` 处的对象自身再以 `0xA3ADA0` 为其基类）⇒ 层次链为
`Prc::PriceComputer` ← `Lp::LinearProgram` ← `Coin::CoinLP`，`Prc::{Box,Hull,Alpha}PriceComputer` 与
`Prc::LinearCombinationPricer` 平级派生自 `PriceComputer`。**[已证实]**

- `Lp::LinearProgram` 是 `Prc::PriceComputer` 的**派生类**（不是独立根类）。**[已证实]**
- `Row::BasicDistancer` / `Row::Squeezer` 都是 `Row::Distancer` 的派生类。**[已证实]**
- **`Prc::BoostAlpha` (`0xA22260`)、`Prc::SurfaceCoeffs` (`0xA222A0`)、`Prc::DimAlpha` (`0xA22340`) 只有 typeinfo 名称字符串，在整份 dump 中没有任何 8 字节指针引用它们 ⇒ 它们是 Non-Polymorphic 型别（纯数据结构 / 无虚函数），编译器直接内联或按值使用，不可达导出。** **[已证实]**

### 1.2 vtable 清册（`vtable base +0x10` 才等于 slot 0；`+0x00` 是 offset-to-top，`+0x08` 是 typeinfo 指针）

```
Lp::LinearProgram         vtable 0xA3ADA0  （7 slots）
  +0x10 00861A20 (3B)   +0x18 00861A20   <- 两个相同的 trivial 虚函数（shared=15 个 vtable 共用）
  +0x20 007C4C70 (75B)  +0x28 007C4CF0 (89B)  +0x30 007C4CC0 (46B)
  +0x38 007C4D50 (123B) +0x40 007C4DD0 (15B)

Prc::PriceComputer        vtable 0xA3AED0   (= LinearProgram 的前 4 个 slot 完全相同)
  +0x10/+0x18 00861A20   +0x20 007C4C70   +0x28 007C4CF0
  +0x30 007C4F90 (79B)   +0x38 007C4FE0 (248B)  +0x40 007C50E0 (97B)

Prc::BoxPriceComputer     vtable 0xA3B0B0  （5 slots，GCC ABI：D1/D0 在 +0x10/+0x18）
  +0x10 00678D40 (1B)   +0x18 00678D30 (5B, 跳 9984B0 = operator delete)
  +0x20 007C9D90 (822B) +0x28 007CA100 (46B)  +0x30 007CA0D0 (40B)

Prc::HullPriceComputer    vtable 0xA3B0F0
  +0x20 007CA130 (6B)   +0x28 007CA170 (50B)  +0x30 007CA140 (40B)

Prc::AlphaPriceComputer   vtable 0xA3B130
  +0x20 007CA1B0 (6B)   +0x28 007CA200 (356B) +0x30 007CA1C0 (60B)

Prc::LinearCombinationPricer vtable 0xA3B170
  +0x10 00678DF0 (88B)  +0x18 00678D90 (88B)
  +0x20 007CA370 (578B) +0x28 007CA6C0 (323B) +0x30 007CA5C0 (256B)

Row::BasicDistancer       vtable 0xA3B1B0  （3 slots）
  +0x10 00679060 (1B)   +0x18 00679050 (5B)   +0x20 007CA810 (6B)

Row::Squeezer             vtable 0xA3B1E0  （3 slots）
  +0x10 00138BE0 (185B) +0x18 00138CA0 (191B) +0x20 0013A360 (221B)

Coin::CoinLP              vtable 0xA3B270  （13 slots）
  +0x10 00679E70 (198B) +0x18 00679DB0 (187B) +0x20 00679C20 (214B)
  +0x28 00679660 (4B)   +0x30 006792C0 (345B) +0x38 00679670 (715B)
  +0x40 00679940 (723B) +0x48 00679420 (575B) +0x50 00679D00 (168B)
  +0x58 007CB700 (14B)  +0x60 007CB710 (14B)  +0x68 007CB740 (14B)
  +0x70 007CB720 (18B)
```

---

## 2. `Lp::` / `Prc::PriceComputer` 接口层（base class）

`Prc::PriceComputer` 与 `Lp::LinearProgram` 共用同一套 slot 实现（`0x7C4C70 / 0x7C4CF0 / 0x7C4CC0`），说明 `LinearProgram` 只改写了 slot 4/5/6。**[已证实]**

### 2.1 `0x7C4C70` —— `price(_, priceable, out, unsigned idx)`
```
call 0x861A30                      ; 检查内部实现指针/有效性
test al,al ; jne ret
cmp edi, 3 ; jbe 0x7C4CA0          ; idx <= 3 才生效（≤4 个候选）
0x7C4CA0:  rax = [rbx]             ; vtable of *priceable
           rax = [rax+0x28]        ; 第 5 个虚槽
           jmp rax                 ; 尾调用 -> 内部对象
```
`0x861A30` 长 74 字节，被 100+ 处调用，是通用有效性/异常检查（`-fno-exceptions` 下的 throw stub）。

### 2.2 `0x7C4CF0` —— `try_price(priceable, out_double*)`
```
rax = [rcx] ; call [rax+0x30]      ; 转内部对象第 7 槽
取结果 flag dword[rsp+0x28]，and 6 == 6 才写入 *out，返回 1
```
### 2.3 `0x7C4CC0` —— 结果包装：`*r9 = r8 ; r9[8]=6 ; r9[0x10]=0x10`（标签 6 / 容量 0x10）

### 2.4 `0x7C4F90 / 0x7C4FE0 / 0x7C50E0`（`PriceComputer` 的 slot 4/5/6 = `LinearProgram` 覆写的那三个）
- `0x7C4F90`：先 `call 0x7C4CC0`，失败再 `rcx=[rbp+0x10]` 尾调用内部对象 `+0x30`。**即"委托给内部实现对象"模式**。
- `0x7C4FE0`：把区间端点 `[rsp+0x90..0xa8]`、`r14d` 打包进 `rsi`，并设置 `rsi[0x10] = 1 或 6`（`lea eax,[rax+rax*4+1]` ⇒ 1 (相等) 或 6 (内部)）；它是典型的 **区间/集合插入-合并** 例程。
- `0x7C50E0`：同样委托内部对象 `+0x40`。

**结论：[推断]** `PriceComputer` 是一个 **策略包装（Strategy/Decorator）**，真正的定价算法在被它持有的内部对象（很可能就是 `Prc::BoostAlpha` / `SurfaceCoeffs` / `DimAlpha` 这三个非多态型别的实例）里；`Lp::LinearProgram` 覆写其中三个槽以走 LP 路径。

---

## 3. `Prc::` 家族：到底在"定价"什么

### 3.1 源码路径证据（内联构造的字符串，非 rodata 常量，需按机器码还原）

| RVA | 内容 | 引用点 |
|---|---|---|
| `0x7C9FC8` | `..\rprice\price_computer.cpp` | `0x7C9D90` |
| `0x7CA4E0` | 同上 | `0x7CA370` |
| `0x9C1CC0` | `static_cast<long long>(pricer.m_prices[p]) >= 0` | `0x222200` |
| `0x9C1C96` | `AlphaSurfacePricer ` | `0x220ED0` |
| `0x9C1CAE` | `DimPricer ` | `0x220ED0` 邻近 |
| `0x9C242D` | `Pb pricing ` | `0x23B080` |
| `0x9C2449` | `..\nesting\algos\old_beam.cpp` | `0x23B080` |
| `0x9C15E0` | `..\nesting\algos\bucket_manager.hpp` | `0x81C690` 等 |

### 3.2 slot 实现语义

**`Prc::BoxPriceComputer`（vtable `0xA3B0B0`）**
- `slot 4 = 0x7CA0D0`：`operator new(8)`，写入 `lea rdx,[rip+0x270fd7]`（一个 vtable/函数指针常量），返回 `{ptr}`。**这是一个"创建内部实现"的工厂**。**[已证实]**
- `slot 3 = 0x7CA100`：在对象里内联构造 `"BoxSurface"`（`0x6166727553786f42` = `"BoxSurfa"`，`edx=0x6563` = `"ce"`，长度 0xa）。**类名 = `BoxSurface`**。**[已证实]**
- `slot 2 = 0x7C9D90`（822B，唯一的真算法）：
  ```
  0x7C9DCD  rdx = [rbx+0x50]                     ; 从 problem 取几何
  0x7C9DD4  call 0x5C31C0                        ; 取候选集合
  0x7C9DE9→ call 0x5EAD40 / 0x4DA280             ; 构造区间/包围盒容器
  0x7C9E30  loop: call 0x7CB750                  ; <-- area = (max_y-min_y)*(max_x-min_x)
  0x7C9E44  ucomisd / cmova                      ; 取"最大面积"的那个
  0x7C9E60  if (*p == 0)  return (p[3]-p[1])*(p[4]-p[2])
  ```
  其中 `0x7CB750`：
  ```
  xmm0 = [rcx+0x20] - [rcx+0x10]   ; (y1-y0)
  xmm1 = [rcx+0x18] - [rcx+0x08]   ; (x1-x0)
  xmm0 *= xmm1
  ```
  ⇒ **`0x7C9D90` 返回"面积最大的候选包围盒的面积"**。**[已证实（机器码）]**
  若候选为空集，则内联构造错误串 `"!orientation.empty()"` + `"..\rprice\price_computer.cpp"` + 行号 `0x2b`(=43)，调 `0x60A620` 抛出。**[已证实]**

**`Prc::HullPriceComputer`（vtable `0xA3B0F0`）**
- `slot 3 = 0x7CA170`：内联字符串 `"HullSurface"`（`0x667275536c6c7548` = `"HullSurf"`, `edx=0x6361`="ac", `[+0x1a]=0x65`="e"）。**类名 = `HullSurface`**。
- `slot 2 = 0x7CA130`：`movsd xmm0,[rdx+0x48]; ret` ⇒ **直接返回输入对象的第 0x48 偏移的 double**（预置的 hull 面系数）。**[已证实]**

**`Prc::AlphaPriceComputer`（vtable `0xA3B130`）**
- `slot 2 = 0x7CA1B0`：`movsd xmm0,[rdx+0x68]; ret` ⇒ **返回 `[+0x68]` 的 double（alpha 系数）**。**[已证实]**
- `slot 3 = 0x7CA200`：`r9 = <0x9D9D3A 附近的串池>`，`r8d = 0x148`(=328=行号)，`rdx = 0x4D96F0 的地址常量`，`xmm0 = [rdx+8]`；然后内联构造 `"AlphaPrice "`（`0x6972506168706c41`="AlphaPri", `eax=0x6563`="ce", `0x20`=空格）并 `append`。⇒ **它是"把 alpha 值格式化成名字"的 `name()`/`to_string()`**。**[已证实]**
- `slot 4 = 0x7CA1C0`：`operator new(0x10)`，写 `{vtable@0x...0x270f5d, [rdx+8]}` ⇒ 装箱一个 double。**[已证实]**

**`Prc::LinearCombinationPricer`（vtable `0xA3B170`）**
- `slot 2 = 0x7CA370`：
  ```
  for (auto& [pricer, w] : this->m_pricers) {      ; rbx 步长 0x10
      wsum += w;                                    ; xmm8
      wsum_price += w * pricer->vcall[+0x10](arg);  ; 对偶/权重加权
  }
  result = wsum_price / wsum;                       ; divsd
  if (!(wsum > 0)) -> 构造 "Combined pricers 0.0" 错误串 + 行号
  ```
  ⇒ **加权平均定价器（Composite）**：把多个子定价器的价格按权重线性组合。**[已证实]**
- `slot 3 = 0x7CA6C0`：内联构造 `"Combined("`（9 字符），遍历子定价器 `vcall[+0x20]` 取名，逐个 `append`，并以 `0x2c`(`,`) 分隔 ⇒ `"Combined(A,B,...)"`。**[已证实]**
- `slot 4 = 0x7CA5C0`：`operator new(0x20)`，逐个 `vcall[+0x20]` 装箱到新 vector ⇒ **clone/copy**。**[已证实]**

### 3.3 定价子问题的定义 **[推断，依据充分]**

`Prc::PriceComputer` 的 slot 4 接一个 `priceable`（`rdx`）并向下调用其 `vcall[+0x28]`；`idx <= 3` 的上限、返回 double、内部对象持有 `{min,max}` 包围盒（`[+0x08..+0x20]`）。

结合 `old_beam.cpp` / `bucket_manager.hpp` 的断言与 `"Pb pricing "` 日志，**子问题是**：给定一个 beam 节点前缀与一张候选放置（orientation / 区域包围盒），求该候选的**最大可用面（box area / hull surface / alpha 面系数）**作为"价格"，用于 beam 排序与剪枝。它**不是**"对偶价格 ≤ 0 的最优 pattern"式的 Dantzig–Wolfe 定价。**[推断]**

**未确认**：`Prc::SurfaceCoeffs`、`Prc::DimAlpha`、`Prc::BoostAlpha` 三个非多态类型的具体字段布局与在哪被使用（无 typeinfo 引用，只能靠内联构造的字符串在其它翻译单元里定位，本轮未完成）。

---

## 4. `Row::Distancer` / `BasicDistancer` / `Squeezer`

- `Row::Distancer`（`0xA17E20`）是抽象基类，`BasicDistancer`（`0xA3B1B0`）与 `Squeezer`（`0xA3B1E0`）实现它。
- **`Row::BasicDistancer::slot2 = 0x7CA810`** 与 **`Row::Squeezer::slot2 = 0x13A360`** 的函数体：
  - Squeezer 内部持有两棵 **区间 map**（`[rdi+0x240]` 与 `[rdi+0x248]`，节点步长 0x20/0x30，节点含 `{key, lo, hi, value, height}`）。
  - 查找逻辑：沿红黑树下降，若查询区间 `[rbx, rsi]` 被已有节点区间 `[node.lo, node.hi]` **包含** ⇒ 命中；否则 `call 0x1380D0`（未命中时的代价计算）后 `call 0x923990` 把结果**插回** `[rdi+0x240]`，返回 `node[+0x30]`。
  - `0x138BE0` / `0x138CA0` 是析构（清理两棵 map：`0x923B00` / `0x932E30` 销毁节点链，然后 `0x253140`、`0x5007C0` 销毁成员，最后 `operator delete`）。
  ⇒ **本质是"区间记忆化缓存（memoized interval cost）"**，成本函数 `0x1380D0` 未深入（本轮预算受限）。**[已证实结构 / 未确认成本函数语义]**
- **[推断]** `BasicDistancer`/`Squeezer` 是**行（row）生成的接受判据**：对将被加入 LP 的行，按 (lo,hi) 键缓存/复用其"距离/挤压量"，避免重复计算 —— 即 cutting-plane / row-generation 的**去重 + 剪枝**层（`Row::` 命名与"row == LP constraint"一致）。但**没有任何调用者**，因此只是一段未接线的实现。

---

## 5. `Coin::CoinLP` —— Clp 1.15.3 封装

### 5.1 布局与虚函数分派
- 对象布局：`[+0x00] = vptr`，`[+0x08] = ClpSimplex*`。
- 分派 thunk（**关键证据，已证实**）：
  ```
  0x7CB700:  rcx = [rcx+8] ; rax = [rcx] ; jmp [rax+0x248]
  0x7CB710:  rcx = [rcx+8] ; rax = [rcx] ; jmp [rax+0x228]
  0x7CB740:  rcx = [rcx+8] ; rax = [rcx] ; jmp [rax+0x230]
  0x7CB720:  r8d = 1 ; r9 = rdx ; rdx = [rcx+8] ; jmp 0x7CA830
  ```
  `ClpSimplex` 的 `dual()` / `primal()` / `solve()` 在 COIN-OR 1.15 的虚表里正落在 `+0x228 / +0x230 / +0x248`（与继承 `ClpModel` 的槽计数一致）⇒ **`Coin::CoinLP` 的末 4 个虚槽是"转发给内部 ClpSimplex"**。**[已证实结构 + 推断具体方法名]**
- `0x7C9A10`：`movsd xmm0,[rip...]`（读 `[rcx+8]` 及 `[rcx+8]+0x88`）⇒ 取 Clp 目标值的内联访问器。**[已证实]**

### 5.2 数据/常量证据
- `0x6792C0`（slot 4，345B，**全局构造器**，唯一 caller 是自己）其 `data_refs` 含 `0x9C2E18`、`0x9C2DF8`、`0x9C2E20`、`0x9C2E30`，这些地址是 **Clp 的边界常量**：`+inf = 0x7FEFFFFFFFFFFFFF`、`-inf = 0xFFEFFFFFFFFFFFFF`、`-1.0`、`1.0`、`0x7FFFFFFFFFFFFFFF`、DBL_MIN。⇒ **构造时把列的下界/上界设成 ±inf、目标设成 ±1.0**。**[已证实]**
- `0x6792C0..0x67A000` 的代码区紧邻 Clp 的 rodata（`0x9C2E40` 处有 `clp`、`OsiColCut`、`consistent`、`No ray?`），同一 `.pdata` 连续区间 ⇒ **这段是 Clp/CoinUtils 静态代码与 app 封装代码的交界**。**[已证实]**
- Clp 源码路径串：`0x9C9E1F` = `@C:\Users\renaud\nest\external\clp-1.15.3\Clp\src\ClpSimplexDual.cpp`；`0x9D2D30` = `C:\Users\renaud\nest\external\Clp-1.15.3\CoinUtils\src\CoinLpIO.cpp`；错误串 `0x9C8D20/0x9C8D80`（"ClpSimplexPrimal or ClpSimplexDual should have been called with correct startFinishOption"）、`0x9C94A8`（`ClpSimplex::readLp(): Unable to open file`）⇒ **Clp 1.15.3 静态链接确认**。**[已证实]**
- **`ClpSimplex` / `ClpModel` 没有出现在 RTTI 名称表里**（`0xA21120`–`0xA21ED0` 只有 `ClpMatrixBase / ClpPackedMatrix / ClpPresolve / ClpDualRowDantzig / ClpPrimalColumnSteepest / CoinModel …`，共 70 个 COIN 类名，**无 `ClpSimplex`/`ClpModel`**）⇒ 这两个类的 typeinfo 在编译/链接时被丢弃。**[已证实]**
- `ClpDualRowDantzig`(`0xA21680`)、`ClpPrimalColumnDantzig`(`0xA21AC0`)、`ClpPrimalColumnSteepest`(`0xA21BE0`)、`ClpDualRowSteepest`(`0xA21780`) 的存在 ⇒ **单纯形法主循环（Dantzig / Steepest 定价）来自 Clp 自身**。**[已证实]**

### 5.3 列/行的加入 **[推断]**
`0x7CA830`（3778B，被 `0x679D00`、`0x7CB720` 调用）对 `{double value, int a, int b}` 的 16 字节记录做**有序插入 / 去重 / 扩容**（`bsr`+`shr` 算容量、`0x267A30` memmove、`0x96D6E0` 走 `_M_fill_insert`），末尾再读回 `[+0x30]` 的 double。这是典型的 **`addColumn` / `addRow` 增量装配 + 稀疏矩阵插入**。**[推断：具体归列还是归行未确认]**
`0x679D00`（slot 8）→ `0x5F3900/0x5F3960/0x62F280` 后调 `0x7CA830` ⇒ **`CoinLP` 的"装配/提交"槽**。

---

## 6. 是否在主编排路径上？—— 决定性证据

对全文件 18,614 个函数做了 **RIP 相对寻址的精确重扫描**（脚本 `lp_s.py`，直接解码每条指令的 `[rip+disp]`，不依赖 `prof2.pkl` 的 `data_refs`），结果：

```
vtable 0xA3ADA0 (Lp::LinearProgram)        refs = 2  -> 0x656310, 0x656340
vtable 0xA3AED0 (Prc::PriceComputer)       refs = 2  -> 0x6563F0, 0x656420
vtable 0xA3B0B0 (Prc::BoxPriceComputer)    refs = 0
vtable 0xA3B0F0 (Prc::HullPriceComputer)   refs = 0
vtable 0xA3B130 (Prc::AlphaPriceComputer)  refs = 0
vtable 0xA3B170 (Prc::LinearCombination)   refs = 0
vtable 0xA3B1B0 (Row::BasicDistancer)      refs = 0
vtable 0xA3B1E0 (Row::Squeezer)            refs = 0
vtable 0xA3B270 (Coin::CoinLP)             refs = 0
```
- 两个仅有的引用就是**基类析构/构造**：`0x656340` 是 `Lp::LinearProgram::~LinearProgram`（`lea rax,[rip+0x3e4a59]` → 精确落在 `0xA3ADA0`，`mov [rcx],rax`，尾调 `0x946820`）；`0x656310` 是其变体；`0x6563F0/0x656420` 是 `Prc::PriceComputer` 的对应物。
- 更关键：**零个虚函数有外部调用者**。`prof2.pkl` 的 `callers` 全表显示，`0x7C4C70 / 0x7C4F90 / 0x7C9D90 / 0x7CA200 / 0x7CA370 / 0x7CA6C0 / 0x7CA5C0 / 0x7CA810 / 0x138BE0 / 0x138CA0` 的 `callers` **只有它们自己**；`0x13A360` 只被 `0x13A360` 调；`0x6792C0/0x679420/0x679670/0x679940/0x679D00` 同样只有自调用（即这些"自调用"是 `prof2.pkl` 对**同一函数内多层 thunk/未对齐解码**的伪影，实测无外部 xref）。
- 唯一的跨族调用是 4 个析构子→基类析构（`0x656340` 的 callers = `0x6563F0/0x656420/0x656430/0x656460`）。

⇒ ~~**结论：`Lp::` + `Coin::CoinLP` + `Prc::*PriceComputer` + `Row::*` 整套列生成 / 行生成机制，在本次 dump 的进程状态里是"已编译但未接线（dead code / 未实例化的库）"。**~~ **[已作废 —— 见文件头警示]**

> **上面这条结论是错的，已作废。** 本节的扫描用 vtable **头部**地址（`0xA3B270` 等），
> 而 C++ 的 vptr 指向 **地址点** `vtable+16`（`0xA3B280`），代码里只出现地址点。
> 用地址点重扫：`Coin::CoinLP` 在 `0x26777C` 被 `lea`（构造器 `0x267760` 内），
> 且在 `0x59AC0`（"linear"）与 `0x6A6AD0`（Database）两处被 `BuildAndSolveLp`（`0x7D7200`）
> 装配、求解，解再由 slot 10 取回。详见 [`findings_lp_use.md`](findings_lp_use.md)。

> 保留原文的方法学教训：`prof2.pkl` 的 `data_refs` 与 `lib.py` 的 `rip_targets()` 对
> **vtable 常量**不可靠，必须直接解码 `op.type==3 and op.mem.base==41`；而且**必须用地址点**。
（语义上完全自成闭环：主问题 `CoinLP` → 定价 `PriceComputer` 族 → 行去重 `Row::Squeezer`，接口齐备，唯独没有引擎侧入口。）

### 6.1 与引擎唯一的真实连接点：`Pack::KnapsackNester`
`0x770D10`（8230B，`name` 未恢复）在 `..\tiling\packer.cpp` 第 `0x19A` = **410** 行断言
`prices.size() == m_problem.GetNumberOfParts()`，其 `callers` 为 `0x1565C0 / 0x7705F0 / 0x770D10`。
但这里的 `m_prices` 是 **`Pack::KnapsackNester` 的按部件价格数组**（背包式打包器的权重），与 `Prc::` 定价器**不是同一物**：`Prc::` 侧的数组由 `0x9C1CC0` 的 `pricer.m_prices[p]` 断言与 `"Pb pricing "`（`0x23B080`）日志标识，位于 `old_beam.cpp`。**两者不可混淆。** **[已证实]**

---

## 7. LSQR 终止串块 @ `0x9A74A0`

- 该块依次含 `"The exact solution is x = 0"`、`"The residual Ax - b is small enough, given ATOL and BTOL"`、`"The least-squares solution is good enough, given ATOL"`、`"The residual Ax - b is small enough for this machine"`、`"The least-squares solution is good enough for this machine"`、`"Cond(Abar) seems to be too large for this machine"`、`"The iteration limit has been reached"` —— 这是 **`lsqr` 参考实现（Paige & Saunders）里 `istop` 的标准 1..7 消息表**。
- 该块位于 `BAB0` 段尾部 rodata（`0x9A74A0`），与 `Lp::`/`Prc::`/`Row::` 的任何函数**没有引用关系**；`Prc::AlphaPriceComputer::0x7CA200` 引用的是 `0x9D9D3A`、`Prc::BoxPriceComputer::0x7C9D90` 引用的是 `0x9D9D20`，与 `0x9A74A0` 无关。
- ⇒ **[已证实] 它属于静态链接进来的一个独立迭代最小二乘 / 稀疏求解器（LSQR），与本报告的 LP / 列生成栈无关。**
- **位置已结案**：全库只有两处引用该块，都在 **`0x3B84E0`** 内（`0x3BA0A4`、`0x3BA114`）
  ⇒ **LSQR 的实现体在 `0x3B84E0`**。**[已证实]**
- **仍未确认**：LSQR 是否是 Clp 的某个内部依赖（Clp 1.15 本身不含 LSQR），
  或来自另一个被静态链接的第三方库（Boost/其它）。

---

## 8. 未完成 / 未确认清单（**已按最新一轮更新**）

> 状态列反映 `findings_lp_use.md`（"COIN-OR 的使用面"）之后的实际情况；
> 已结案项保留原文以便追溯。

| # | 项 | 状态 |
|---|---|---|
| 1 | `Prc::BoostAlpha` / `SurfaceCoeffs` / `DimAlpha` 的字段布局与实际使用点 | **已收紧为"连 typeinfo 对象都不存在"**。用**绝对 VA**（`ImageBase 0x6B4C0000 + RVA`）重搜：`PriceComputer`/`BoxPriceComputer`/`LinearProgram`/`CoinLP` 的名字串各有 1 个指针（来自其 typeinfo 对象 `[+8]`），而这**三个各有 0 个** ⇒ 既无 vtable 也无 typeinfo，只剩编译器留下的孤立名字串。**字段布局仍[未确认]**，原因是无 RTTI 可依附、且其仅有的两个出现点（`0x220ED0` 的 `'AlphaSurfacePricer '`、`0x23B080` 的 `'Pb pricing '`）附近没有可反推布局的字段写入。详见 `findings_lp_use.md` §5.3。 |
| 2 | `Row::Squeezer` 的成本函数 `0x1380D0` 语义 | **大部分结案，见 [`findings_lp_use.md`](findings_lp_use.md) §8**。已完全译出三个组成原语：① 角度原语 `0x5C22D0`（157 B）= `round(atan2(y,x)/2π · 360e10)` 回绕到 `[0,360e10)`，常量 `0x9DE758=2π`、`0x9DE740=3.6e12`、`0x9DE750=0.5`；② `sin` 块 = `sin(2π·angleIndex/3.6e12)`，0/90/180/270 走精确分支（魔数 `0xD18C2E2800=9e11`、`0x1A3185C5000=1.8e12`、`0x274A48A7800=2.7e12`）；③ hypot `sqrt(a²+b²)`（`0x138210` 内联 `sqrtsd` + `0x62FE20` libm 兜底）。另定位 `0x134FA0` = `optional<Interval>`（值类型 **4×double**）、`0x134FF0` = 按 bool 在 `+0xA8`/`+0xC0` 间二选一。**仍缺**：把原语组合成成本值的算术次序与 `node[+0x30]` 的量纲。 |
| 3 | `0x7CA830` 归属 `addColumn` 还是 `addRow` | **已改判**：两者都不是。`0x7CA830`（3778 B）的真正形态是「**先 `call 0x267A30`（= `std::sort` 实例，把 16 字节 `{double,int,int}` 三元组按 (int@+0xC, int@+8, double@+0) 排序）**，再经 ostream 输出 3 空格分隔的数值表，输出写进调用者给的**临时 `std::string`**（`0x679D00` 传入，用完即析构）」。列/行的**追加**分别在 slot 4（`0x6792C0`）与 slot 5（`0x679670`）。**求解在 slot 8**：`call 0x7CA830(...)` 之后 `call [solver_vt+0x00]`、`call [solver_vt+0x100]`，返回值 `xor 1`。**未确认**：`0x7CA830` 是"装填进求解器"还是"格式化成文本"（两种读法都符合已观测证据）。 |
| 4 | `Coin::CoinLP` 是否在更早/更晚的构建中被引擎使用 | **结案**：**被使用**。构造点 4 处（`0x59AC0` "linear"、`0x24E2D0`、`0x25B040`、`0x6A6AD0` "Database"）；`BuildAndSolveLp` 装配求解；解由 slot 10 取回并回映。 |
| 5 | 四个定价变体的"默认值" | **仍[未确认]**（无构造函数调用、无配置读取点）。 |
| 6 | LSQR 块的所属库与函数位置 | **位置结案**：实现体在 **`0x3B84E0`**（见 §7）。所属第三方库仍[未确认]。 |
| 7 | **新增**：Clp 究竟在解什么 | **结案**：板材选择集合覆盖 LP（`min Σ price(s)·x_s`, `s.t. Σ_s count(s,p)·x_s ≥ demand(p)`），源文件 `..\multi\database.cpp`，驱动函数 `BuildAndSolveLp` `0x7D7200`。见 `findings_lp_use.md` §3。 |
| 8 | **新增**：OR-Tools 是否被使用 | **结案**：**没有**，13 个标记全文件 0 命中；静态链接的是 COIN-OR Clp 1.15.3（经 `OsiClpSolverInterface`）。 |

---

## 附：本轮使用的脚本（均在 `D:\Nesting\nestfab\re\`）

`lp_dis.py`（带字符串标注的反汇编）、`lp_ann.py`（同上，命令行传 RVA）、`lp_s.py`（全文件精确 RIP 目标扫描）、`lp_z.py`（vtable slot 清册 + 共享槽计数）、`lp_w.py` / `lp_x.py`（字符串→引用者反查）。
注意：`lib.py` 的 `rip_targets()` 与 `prof2.pkl` 的 `data_refs` 对本文件**不可靠**（对 `0xA3ADA0` 这类 vtable 常量返回 0 命中，实测 `lea` 存在），必须直接解码 `op.type==3 and op.mem.base==41`。
