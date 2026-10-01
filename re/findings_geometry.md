# 几何子系统逆向报告 — `libcns_dump_64.dll` (Optalog CNS)

分析对象：`D:\Nesting\nestfab\libcns_dump_64.dll`（MD5 `01fea4b73a33dd233c66ca76235313fa`，ImageBase `0x6B4C0000`）。
所有地址均为 **RVA**（`BAB0` 段内 file offset == RVA；其余用 `rva2off()`）。
证据类型标注：**[证明]** = 反汇编直接可见；**[推断]** = 由调用关系/字符串/数据布局推断；**[未确认]** = 未验证。

---

## 0. TL;DR（最重要的结论）

1. **Clipper / ClipperLib 根本不存在**。全文件对 `Clipper` / `ClipperLib` / `PolyTree` / `IntPoint` / `JoinType` / `MiterLimit` 的搜索均为 0 命中。原 BRIEF 里"Clipper 静态链接"的说法在本文件上是错的。**[证明]**
2. 几何内核是 **自研的两套内核**：
   - `..\exact\*`：**定长整数"精确"内核**（点坐标 = `int64`，全局定标 **1e10**；行列式/叉积用 **128 位**中间量）。文件：`geom.cpp`、`convolution.cpp`、`nofit_map.cpp`、`boolean.cpp`、`path.cpp`、`geom_conversion.inl`、`relinker_internal.cpp`。
   - `..\geom\*`：**double 内核**（`ring.cpp`、`element_path.cpp`、`layered_multi_polygon.cpp`、`convexifier.*`、`svg_io.cpp`、`arcs_approximation.cpp`、`properties.cpp`、`authorization.cpp`）。
3. NFP（no-fit polygon）**不是** edge-merge+`atan2` 排序，而是 `exact::convolution`：把两条边序列按**方向象限（sign-based quadrant，1..4）**做极角归并（无 `atan2`），术语在源码里叫 **Convolution**（"卷积"=边界 Minkowski 和）。**[证明（结构）]**
4. 内偏移（interpart gap / inflate）走 `exact::geom.cpp::NewExternalOffset` 0x58B520 与 0x58A7E0，采用**分步多次偏移**：`N = floor(dist/step + 0.5)`，`N<=1` 直接返回。**[证明]**
5. `atan2` 只有一个实现 0x634C70（x87 `fpatan`），只被 `Geom::SignedAngleInRad` 0x5C5280 使用（`atan2(cross, dot)`）；NFP 主路径不用它。**[证明]**

---

## 1. 源文件 → 函数映射（由内联构造的 `__FILE__` 字面量反推）

代码里 `assert` 的 `__FILE__`/`__func__` 是**用 `movabs` 立即数逐块拼进栈缓冲**的，因此不在 rodata 里、`prof2.pkl` 的 `data_refs` 也看不到。我用一个"内联字符串重建器"（`re\g5_inline.py`）把它们还原出来。**[证明]**

| 源文件 | 函数 RVA（size） |
|---|---|
| `..\exact\path.cpp` | 0x57FDA0 (2005) `RemoveAlignedCollinearPoints` |
| `..\exact\geom.cpp` | 0x582C00 (2206)、0x583830 (2279)、0x584120 (2080)、**0x5867C0 (3089) `GetConvolutionLoops`**、**0x5873E0 (2784) `GetNoFitConvolutions`**、0x588A60 (2683)、**0x58B520 (563) `NewExternalOffset`** |
| `..\exact\geom_conversion.inl` | 0x584CC0 (2031)、0x5854B0 (2031)、0x685CD0 (1769)、**0x6863C0 (3262) `ToExactPerimeter`** |
| `..\exact\convolution.cpp` | **0x596F20 (924) `ConvolutionRaw`** |
| `..\exact\boolean.cpp` | 0x597BD0 (570) |
| `..\exact\nofit_map.cpp` | **0x59B3B0 (1408) `NoFitMapWithoutHolesChecked`**、0x59C560 (1961)、0x59CD10 (7356)、**0x59E9D0 (10198) `NoFitMapWithoutHoles`**、0x5A2690 (2286) |
| `..\geom\ring.cpp` | 0x5C5280 (665) `SignedAngleInRad`、0x5C5520 (1098) |
| `..\geom\convexifier.*` | 0x93FD50 (3461)、0x940AE0 (3516)（成员 `m_convexifier_points`） |
| `..\geom\layered_multi_polygon.cpp` | 0x5C73B0 / 0x5C75D0 / 0x5C77F0 (各 540)、0x5C7A10 (553) |
| `..\geom\element_path.cpp` | 0x5EFEA0 (1502) |
| `..\geom\svg_io.cpp` | 0x5DFF90 (643) |
| `..\tiling\nofit_mapper.cpp` | 0x7E6010 (7777) `NoFitMapper`（含 `m_canceller != nullptr`） |
| `cns_no_fit.cpp` | 0x7060/0x7100/0x71B0（assert 辅助）、**0x7270 `GetRing`**、0x74C0 `GetPart`、0x76D0、0x7CB0、0x8290、0x83E0、0x85B0、**0x85D0 `DrawSVG`**，以及全部 `NoFit*`/`CNS_NoFit*` 导出 |
| `cns.cpp` | 0x9F00 (1821)、以及 `SetInterpartGap`/`SetDefectGap`/`SetSheetGaps` 等设置类导出 |

`nofit_map.cpp` 的 `__FILE__` 是 `..\exact\nofit_map.cpp`；断言实例（`0x59B505`、`0x59B79F`、`0x5869DD` 等）：
```
(polygon1.m_internal_paths.size() == 0u) && "holes unsupported"   // nofit_map.cpp
(polygon2.m_internal_paths.size() == 0u) && "holes unsupported"
(polygon1.m_internal_paths.size() == 0u) && "hole not supported"  // geom.cpp 0x5867C0/0x5873E0
```
→ 说明 `Polygon` 的洞成员名就叫 `m_internal_paths`，且**卷积步骤不支持带洞多边形**。**[证明]**

`..\exact\convolution.cpp` 里的断言（0x5970B3 处内联构造）：
```
max_size >= union(size1,size2)          // convolution.cpp line 0x14B = 331
__func__ = "ConvolutionRaw"
```

---

## 2. 数据结构（NoFit / NFP）

### 2.1 基本类型 **[证明]**

```cpp
struct Point { double x, y; };              // sizeof = 16
using Ring  = std::vector<Point>;           // sizeof = 24
struct Polygon {                            // sizeof = 48 (0x30)
    Ring              m_external_path;      // +0x00
    std::vector<Ring> m_internal_paths;     // +0x18
};
struct NoFitGeometry {                      // 堆对象 sizeof = 24
    std::vector<Polygon> result;            // +0x00
};
```

证据：
- `NoFitGetNumberOfExternalPolygons` **0x89D0**：`([rcx+8]-[rcx])/48`（`sar rax,4` + magic `0xAAAAAAAAAAAAAAAB`）。返回值 = `result.size()`。
- `DeleteNoFitGeometry` **0x8A10**：以 0x30 步长遍历 `[rcx]..[rcx+8]`（= `result`），对每个 `Polygon` 先释放 `[rdi+0x18]..[rdi+0x20]` 内每个 `Ring`（步长 0x18）的数据指针 `[rbx]`，再释放 `[rdi+0x18]`（`m_internal_paths` 数组），最后释放 `[rdi]`（`m_external_path` 数据）；末尾 `jmp operator delete(0x9984B0)` 释放 handle 本身 → handle 就是 `{std::vector<Polygon> result;}`（24 字节）。
- `GetRing` **0x7270**：
  - 断言 `external_number < map->result.size()`（字符串 `0x9AC430`，`cns_no_fit.cpp` 行 `0x1E3`=483）；
  - `internal_number == 0` → 调 `sub_5C5F50`（就是 `mov rax,rcx; ret`，恒等）→ 返回 `&poly.m_external_path`；
  - 否则调 `sub_5C5F60`（`lea rax,[rcx+0x18]`）→ 得到 `&poly.m_internal_paths`，再做 `(end-begin)/24` 与 `internal_number-1` 比较（断言 `(internal_number - 1) < inners.size()`，字符串 `0x9AC468`，行 `0x1EA`=490），返回 `&inners[internal-1]`。
  - 返回类型是 `std::vector<Point> const*`；内层元素 24 字节 ⇒ `Ring`（`std::vector<Point>`）。
- `CNS_NoFitGetNumberOfHoles` **0x8E70**：断言 `external_number < n`（字符串 `0x9AC5BD`，行 `0x1DA`=474），返回 `m_internal_paths.size()`。
- `CNS_NoFitGetPoint` **0x91C0**：`GetRing(ctx, ext, internal)`，断言 `point_number < ring.size()`（`0x9AC5F6`，行 `0x202`=514），元素步长 16，读出 `x`、`y` 两个 `double`（`movsd [rax]` / `movsd [rax+8]`）。
- `NoFitGetNumberOfPoints` **0x8FC0**：TLS 保护（`0xB1F050`/`0xB1F058` + `0x63F6C0`）+ 日志，最后 `GetRing(...).size()`。

### 2.2 `NoFitContext` = 240 字节 **[证明（布局）/未确认（成员语义）]**

`NewNoFitContext` **0x9AF0**：
```
mov ecx, 0xF0 ; call operator new(0x998500) ; rcx=new ; rdx=arg ; call CNS_NoFitContext(0x668F20)
```
⇒ 上下文对象 **0xF0 = 240 字节**，构造函数就是 `CNS_NoFitContext` **0x668F20**（2631 字节，同一 TU）。函数名/断言用 tracer 日志 `NewNoFitContext` / `// NewNoFitContext`。

`DeleteNoFitContext` **0x9CC0** 揭示了成员偏移（按销毁顺序）：

| 偏移 | 内容 | 证据 |
|---|---|---|
| +0x08, +0x10 | 两个指针，先 `sub_5007C0(ptr)` 再 `operator delete` | **[证明]** 0x9E9D–0x9ECA |
| +0x18..+0x28 | 红黑树（`std::map`）头/节点，节点析构辅助 `0x931690` | **[证明]** 0x9E70 |
| +0x48..+0x58 | 另一个 `std::map`，节点析构辅助 `0x931C00` | **[证明]** 0x9E43 |
| **+0x78..+0x88** | `std::map<Key, std::vector<Polygon>>` ← **NFPMap 缓存**；节点 key 析构辅助 **0x7CB0**；value 是节点 +0x40 处的 `std::vector<Polygon>`（= §2.1 的 `NoFitGeometry`） | **[证明]** 0x9D93–0x9E3D |
| **+0xA8..+0xB8** | 同构的第二个 map（另一种 key），key 析构辅助 **0x76D0** | **[证明]** 0x9CEB–0x9D8D |
| **+0xD8** | `int64` 已缓存多边形**总数**；> `0x1312CFF`(=19,999,999) 时清空 +0x78 的缓存 | **[证明]** 0x665C06 / 0x665D92 / 0x665EF3 |
| **+0xE8** | `uint32 m_max_complexity`；`NoFitSetMaximumComplexity` 直接 `mov [rcx+0xE8], edx`；为 0 时用默认值 **0x61A8 = 25000** | **[证明]** 0x9A22 / 0x665DF8 |
| ctx+0xE8 之后的成员（+0xF0 已越界）不存在 | | |

`NoFitSetMaximumComplexity` **0x9930**：`(ctx, int n)` → `ctx->m_max_complexity = n`（含 tracer 日志与异常路径）。

### 2.3 `NoFitNesting` = 32 字节 **[证明]**

- `NewNoFitNesting` **0x9330**：`operator new(0x20)`，`[rax]=arg1`，`[rax+8]=[rax+0x10]=[rax+0x18]=0` → `{ void* ctx; std::vector<Placement> v; }`。
- `NoFitAddNestedPart` **0xA9D0**：`(nesting, Part* p, bool flip, double a, double b, double c)`（`xmm3` + 栈上两个 double）；往 `[nesting+8..+0x10]` 追加 **0x28 = 40 字节**的记录：
  `{ Part* part; bool flip; double; double; double; }`。
- `DeleteNoFitNesting` **0x9500**：只释放 `[n+8]`（元素无析构 ⇒ 元素是 POD）再 `delete n`。

### 2.4 `NoFitMap` / `NFPMap` 的缓存与惰性计算 **[证明]**

`0x665BF0`（840 字节，被 `GetNoFitMap` 0x8AC0 调用）是 **"取或算"缓存函数**：
1. 若 `ctx->[0xD8] > 0x1312CFF` → 清空 +0x78 的 map（调 0x7CB0）、重置树头、`[0xD8]=0`（0x665D92–0x665DD0）。
2. 在 +0x78 的 `std::map` 里按 **32 字节 key（4×int64）** 二分查找（比较函数 `sub_7060` + `sub_5C4D30`），命中则返回 `node+0x40`（`std::vector<Polygon>`，函数返回 `lea rax,[rsi+0x40]`）。
3. 未命中则计算：`GetPart(ctx,key)` → `0x4F7600(part)`（取 part 几何）→ `0x5D38C0` → **`0x585CA0`**（真正的 NFP 计算）→ `0x83E0` 插入 map；
   用 `0x5CDBD0` 取新 map 的多边形个数累加到 `[0xD8]`。
4. 传给 `0x585CA0` 的复杂度上限：`esi = ctx->[0xE8]; if(!esi) esi=25000;` 容差 = `1e-6`（rodata `0x9AC818`）。

`GetNoFitMap` 导出 **0x8AC0** 的入参处理（关键常量）：
```
xmm7 = 360.0 (0x9AC830)   xmm8 = 3.6e12 (0x9AC838)   xmm9 = 0.5 (0x9AC840)
arg4 → floor(arg4/360.0*3.6e12 + 0.5) → cvttsd2si  (等价于 round(arg4*1e10))
```
即把 **double 按 1e10 定标转成 int64**（对角度则是"整圆 = 360*1e10 = 3.6e12"）。同样的三元组被 `GetNoFitPlacementMap` 0xA620、`DrawSVG` 0x85D0、0x9F00、0x6673F0、0x7C80B0 使用。**[证明]**

`GetNoFitPlacementMap` **0xA620**：结构上与 `GetNoFitMap` 同类（同样 1e10 定标 + tracer 日志），走另一套 key/缓存（+0xA8 的 map）。**[推断]**

---

## 3. NFP / Minkowski（Convolution）算法

### 3.1 调用链 **[证明]**

```
GetNoFitMap(0x8AC0) / GetNoFitPlacementMap(0xA620)
  └─ 0x665BF0  缓存查找（map @ctx+0x78）
      └─ 0x585CA0 (526)                       ← double 层入口
          ├─ 0x6863C0 (3262) ×2  ToExactPerimeter(geom_conversion.inl, tol=1e-6)
          ├─ 0x5A2530 (349)
          │    └─ 0x5A11B0 (4990)
          │         ├─ 0x59E9D0 (10198) NoFitMapWithoutHoles   (nofit_map.cpp)
          │         │    └─ 0x59CD10 (7356)  ← 核心
          │         │         ├─ 0x59C560 (1961)  断言 IsValid(nofit_polygon)
          │         │         ├─ 0x59B080 / 0x5A2530
          │         ├─ 0x5A2690 (2286)  断言 IsValid(nofit_polygon)
          │         └─ 0x59AF50 / 0x598980 / 0x8CDDE0
          └─ 0x687080        精确结果 → double 多边形
0x5867C0 GetConvolutionLoops  → 0x597500 / 0x6863C0
0x5873E0 GetNoFitConvolutions → 0x6863C0 ×2 → 0x597500
0x596F20 ConvolutionRaw       → 0x596100 ×2
```

`0x585CA0` 的签名（由寄存器用法）：`(out, poly2, poly1, int max_complexity, bool, double tolerance)`，其中 `r9d = max_complexity`（来自 0x665BF0，默认 25000），`[stack+0x10] = tolerance = 1e-6`。

### 3.2 `ConvolutionRaw` + 核心 **[证明]**

- **`ConvolutionRaw` 0x596F20** `(out, polygon1, polygon2, int max_size)`：
  1. `0x596100(out=stack, rdx=poly1, r8=poly2, r9d=1)`；
  2. 若 `max_size != 0` 且 `max_size < size(第一趟)` → 构造断言 `max_size >= union(size1,size2)`（`..\exact\convolution.cpp` 行 331）；
  3. `0x596100(out=stack2, rdx=poly2, r8=poly1, r9d=0)`（**交换两个多边形**）；
  4. `ebx = !flag`（`xor ebx,1`）作为返回值。
  ⇒ 说明 NFP 需要对两个方向各做一次卷积再合并。
- **核心 0x596100（3605 字节）**：
  - `0x595A80(out, poly1, poly2)`：先把多边形点列（0x20 字节/边：`{x1,y1,x2,y2}`，由 `0x57D8D0` 生成）转成 **16 字节方向向量**表 `{dy, dx}`（`dx = x1-x2`，`dy = y2-y1`，见 0x595B13–0x595B2D），然后用 `0x58E450` 对**相邻两条边的方向做 128 位叉积**（`i % n` 取环），把结果写成 **40 字节有向边记录**：
    ```
    +0x00 3×qword（方向 dx/dy 等）
    +0x18 qword
    +0x20 byte  "凸/凹"标记（叉积符号）
    +0x21 byte  另一个标记
    ```
    步长 `add rax,0x28` 证实记录 = 40 字节。
  - `0x596000(out+0x18, poly2, bool)`：`([rdx+8]-[rdx])/16` = 点数，然后 `0x595D60` + 循环调 `0x595E50(out, p_i, p_{i+1}, ...)` 生成 **64 字节 Edge 记录**：
    ```
    +0x00/+0x08 = A.x/A.y      (上一个点)
    +0x10/+0x18 = B.x/B.y      (下一个点)
    +0x20..+0x38 = C.x/C.y + 两个 bool（由 0x58E450 的叉积/共线判定决定是否插入额外点）
    ```
    `0x595E50` 内部两次调用 `0x58E450`（128 位叉积），据其符号决定是否补一个点 —— 这是**共线/自交处理**。
  - 主循环（0x5965CA 起）：对 `[out+0x18]` 的每条 64 字节 Edge，读 `dx=[rdi+0x10]`、`dy=[rdi+0x18]`，**只用符号判断**把方向分到 **象限 1..4**（0x596231–0x59631F）：
    ```
    dx>0 && dy>0            -> 1
    dx>0 && dy<=0           -> 2
    dx<=0 && dy<0           -> 3
    dx<0 && dy>0, dx<=0,dy=0-> 4
    ```
    然后按这个极角键把方向事件写入结果序列 `[out+0x48]`（40 字节记录：`{tag(0/1/-1), quadrant(1..4), dy, dx, ±1, 2×flag, index}`）。
  ⇒ **这就是 Minkowski/convolution 的"按极角归并"**：两个多边形的边天然按极角有序，用象限 + 128 位叉积做比较，**全程不用 `atan2`**，从而保持精确性。**[证明（指令级）；"这是教科书 edge-merge" 属 [推断]]**
- **精确算术原语 `0x58E450`（417 字节）**：把两个有符号 64 位数相乘累加，产生 `{rax,rdx}` 128 位结果 + 符号字节（`imul`/`mul` + `adc`/`sbb` + `cmp sil,dil`），可见大量 `sar reg,0x3F`（符号扩展）与 `neg`。它就是**行列式/叉积的精确谓词**，被卷积、偏移、布尔操作全部复用。**[证明]**
- **`GetConvolutionLoops` 0x5867C0** / **`GetNoFitConvolutions` 0x5873E0**（`..\exact\geom.cpp`）：两者都先调 `0x6863C0(ToExactPerimeter)` 把两个多边形在给定**旋转角**下转成精确表示，断言 `hole not supported`，再调 `0x597500`；`GetNoFitConvolutions` 还保留 `GetNoFitH` 字面量（0x587636/0x587AF1，函数名被截断显示为 `GetNoFitH`）。**[证明]**

### 3.3 "Clipper 替代品"
- 布尔/裁剪：`..\exact\boolean.cpp` **0x597BD0**（570 字节）。**[证明（文件归属）；具体算法未展开]**
- 共线点清理：`..\exact\path.cpp` **0x57FDA0** `RemoveAlignedCollinearPoints`，断言 `"closed precondition" && (points.front() == points.back(...))`、`"no empty precondition" && !points.empty`。**[证明]**
- 凸化：`..\geom\convexifier.*` **0x93FD50 (3461) / 0x940AE0 (3516)**，成员 `m_convexifier_points`，断言 `(*m_convexifier_points).size() > std::max(i1, i2)`。**[证明]**
- `Geom::` 侧的 `PartPolygon` / `RealPolygon` / `PolygonProxy`（RTTI typeinfo 名在 0xA211B0 / 0xA211D0 / 0xA21260；`vtables.json` 中**没有**它们的 vtable ⇒ 非多态类）、`Geom::MultiPolygon`（`shared_ptr` 计数体 RTTI `St23_Sp_counted_ptr_inplaceIN4Geom12MultiPolygonE...` 在 0xA35060）、字符串 `HullSurf`(0x7CA181)、`tooling_geometry`(0x4DACA0)、`SetExtraGeometry`(0x547F80)。**[证明（存在）/未展开]**

### 3.4 角度与 atan2 **[证明]**
- **`Geom::SignedAngleInRad` 0x5C5280**（`..\geom\ring.cpp`）：
  ```
  cross = v2.y*v1.x - v1.y*v2.x      (xmm7)
  dot   = v2.x*v1.x + v1.y*v2.y      (xmm6)
  assert(cross != 0 && dot != 0)     // 字符串在 0x5C530B 内联构造，长度 0x1E
  return atan2(cross, dot)           // xmm0=cross, xmm1=dot  → call 0x634C70
  ```
- **`0x634C70`（41 字节）= `atan2`**：`fld x` / `fld y` / `fpatan` / `fstp`（x87 实现）。同簇还有 `cos` 0x634CA0、`exp` 0x634DC0、`pow` 0x6352F0、`sin` 0x635970、`sqrt` 0x62FE20 —— 说明 libm 是静态链接的（`.rsrc` 的导入表里只有 `acos` 一个数学函数）。
- **`0x5C22D0`（157 B）= 定点角度转换原语** **[已证实，逐指令译出]**（新增，见
  [`findings_lp_use.md`](findings_lp_use.md) §8.2）：
  ```c
  // rcx = 指向两个 double 的方向向量
  int64_t AngleToFixedDegrees(const double* v) {
      if (v[0] == 0.0 && v[1] == 0.0) return 0;      // 0x5C22E7 / 0x5C2336
      double a = atan2(v[1], v[0]);                  // 0x634C70（全库唯一 atan2）
      a = a / 6.283185307179586;                     // 0x9DE758 = 2π
      a = a * 3600000000000.0;                       // 0x9DE740 = 360e10
      a = a + 0.5;                                   // 0x9DE750
      int64_t r = (int64_t)round(a);                  // 0x62FA20 = libm 取整
      while (r < 0)               r += 3600000000000LL;   // 0x5C231F
      while (r > 3600000000000LL) r -= 3600000000000LL;   // 0x5C2360
      return r;                                       // ∈ [0, 360e10)
  }
  ```
  常量已逐个读出：`0x9DE758 = 6.283185307179586`、`0x9DE740 = 3.6e12`、`0x9DE750 = 0.5`；
  边界 `0x34630B8A000 = 360 × 1e10`。**单位是"度"，定标 1e10**（与 `kScale` 同源）。
  ⇒ 工程对应 `geom::angleToFixedDegrees` / `geom::kFullTurnFixedDegrees`（`test_exact` 覆盖
  0/45/90/180/270/315 度与回绕，并断言 0/90/180/270 的魔数 `0xD18C2E2800` / `0x1A3185C5000` /
  `0x274A48A7800`）。

### 3.5 关键常量汇总

| 常量 | rodata RVA | 用途 / 引用者 |
|---|---|---|
| `1e10` | 0x9AD708 | 精确内核长度定标 |
| `3.6e12` = 360×1e10 | 0x9AC838 / 0x9AD6F0 | 角度→int64 定标 |
| `360.0` | 0x9AC830 / 0x9AD6F8 | 同上（`x/360*3.6e12`） |
| `0.5` | 0x9AC840 / 0x9AD728 | round-half-up（后面接 `0x62FA20`=floor/round） |
| `1e-6` | 0x9AC818 / 0x9DCB20 | NFP 容差（0x665BF0、0x665F40、0x6673F0、0x674680） |
| `0.0`（及 -0.0） | 0x9DCB28 | `NewExternalOffset` 的 `radius >= 0` 前置断言 |
| `1.0` / `0.5` | 0x9DCB10 / 0x9DCB18 | 偏移步数 `N = floor(dist/step + 0.5)` |
| 0.05 / 0.001 / 1e9 / 1e10 / 1000.0 / 1e-4 / 359.9999 / 0.01 / 1e-6 | 0x9AD6E0 … 0x9AD738 | cns.cpp 常量池（gap、角度归一化） |
| `25000` (`0x61A8`) | 立即数 | `m_max_complexity` 未设时的默认值（0x665DF8） |
| `19999999` (`0x1312CFF`) | 立即数 | NFPMap 缓存清空阈值（0x665C06） |

---

## 4. 偏移 / inflate / gap

### 4.1 Part 侧的 inflate **[证明]**

`AddInflatedToolPathToPart` **0x12C60 (169 字节)** `(part, double inflate)`：
```
rbp = [part+0x58]; rbx = [part+0x50]      // 第一组环（步长 0x18）
loop: 0x128E0(elem, &part+0x98, &part+0xb0, xmm3 = inflate)
rbx = [part+0x60]; rbp = [part+0x70]      // 第二组环
btc rsi, 0x3F                             // 把 inflate 的符号位取反 → -inflate
loop: 0x128E0(elem, &part+0x98, &part+0xb0, xmm3 = -inflate)
```
⇒ **外轮廓 +gap、内孔 −gap**，这是标准的"带洞多边形膨胀"实现方式，无需 Clipper 的 `JoinType` 概念。**[证明]**

`0x128E0 (883)` → `0x12780` + **`0x58A7E0`**（`..\exact\geom.cpp` 邻域，3388 字节）+ `0x5C5970`(geom/ring.cpp) + `0x5C5BF0`；`0x58A7E0` 也被 `GetInflatedModulesGeometries`(0x4C2200)、`EquivalentSmallerDefects`(0x4BC9E0)、0x621EB0/0x6228D0/0x623360、0x7B7C00 调用。**[证明]**

### 4.2 偏移算法 = 分步多次偏移 **[证明]**

`0x58A7E0` 开头：
```
xmm6 = dist(参数2)   xmm7 = step(栈上 double)
ucomisd xmm6, 0 ; jbe 早退
xmm0 = xmm6 / xmm7 ; xmm0 += 0.5 ; call 0x62FA20 ; cvttsd2si rax
cmp rax, 1 ; jle 早退                  // N = round(dist/step)，N<=1 不偏移
... 之后是 N 次迭代的偏移环
```
`NewExternalOffset` **0x58B520** `(out, ring, double radius, double step, ...)`：
```
ucomisd xmm2, 0.0 (0x9DCB28) ; jb → 构造断言字符串（"radius > ..." "..\exact\geom.cpp"）并抛出
否则 call 0x58A7E0(out, ring, radius, step, ...)
```
⇒ **偏移不是"一次 Clipper Offset + JoinType/MiterLimit"，而是把 gap 切成 N 份逐步外扩**（`N = round(dist/step)`），这样每一小步都可以用精确谓词保持拓扑正确。**未发现任何 JoinType / MiterLimit / ArcTolerance 常量或字符串**。**[证明；"为什么这么设计"属推断]**

### 4.3 gap 的存储位置 **[证明]**

| API | RVA | 行为 |
|---|---|---|
| `SetExtraGapOnPart(part, double)` | 0x14450 | `part[+0x10] = gap` |
| `SetDefectGap(order, double)` | 0x109C0 | `order[+0x118] = gap` |
| `SetSheetGaps` | 0xCCB0 (527) | 未逐条展开（同族 setter） |
| `SetShearGap` | 0xCEF0 (45) | 极小的 setter |
| `SetInterpartGap` | **未定位到导出 RVA** | 字符串在 `cns.cpp` 池 `0x9ACC64`，同池有断言 `(gap >= 0.0) && "Negative part gap unsupported"`（`0x9ACC78`）；另有字符串 `CNS_SetInterpartGap`(0x9AD6B0)。**[未确认]** |

`OffsetManager` / `OffsetEvaluator` / `OffsetMultiEvaluator` / `NoFitStrips` 是 `shared_ptr` 管理的类（RTTI 计数体 `St23_Sp_counted_ptr_inplaceI13OffsetManager…` 0xA34D00、`…I15OffsetEvaluator…` 0xA34DC0、`…I11NoFitStrips…` 0xA34CA0），相关字符串：`parameters.m_offset_manager`(0x9BE7B3)、`nc.m_offset_manager`(0x9C0020)、`nesting_offset_ratio`(0x9AFBDF)、`Offsets computed`(0x9C1ECB)、`GetNestableOffset`(0x9BE8F0)、`CheckOffset`(0x9BFCC8)、`!detect_correct_invalid || IsGeometryValid(inflated)`(0x9D9528)、`GetInflatedModulesGeometries`(0x9D95D0)。**[证明（存在）；实现未展开]**

---

## 5. 干涉 / 点-多边形测试

- **`Verify::DetectOverlap` 0x99EAC0 (237 字节)**：只是**校验框架的钩子**——内联构造字符串 `"Verify::DetectOverlap"`（`0x764F746365746544`='DetectOv' + `0x3A3A796669726556`='Verify::' + `0x616C7265`='eral'），随后调 `0x5F3BC0`/`0x5F43D0`（Verify 注册/抛出）→ 它本身**不做几何判断**。**[证明]**
- 真正的几何谓词全部落在**128 位精确行列式** `0x58E450` 上，被 convolution（0x596100/0x595A80/0x595E50）与 offset（0x58A7E0）直接调用；`Geom::SignedAngleInRad` 0x5C5280 提供有符号角。**[证明]**
- `nofit_map.cpp` 内部大量使用 `IsValid(...)` 断言（`IsValid(nofit_polygon)` @0x59CB4E/0x59DC06/0x5A2B4A；`results.size() == 1u` @0x59E016；`IsValid(results)` @0x59E1BA；`IsValid(result.second)` @0x5A0610），说明**每个卷积结果都要过一遍几何有效性/重叠检查**。**[证明]**
- **具体的 point-in-polygon（射线法/绕数）例程未定位** → **未确认**。相关但未展开的备选：`0x576470 GetIntersectingIndex`（2141 字节，位于 `..\common_cut\matrix.cpp`；按 `r*c` 个 40 字节单元分配矩阵，与"行×列的多边形相交索引"相符）、`0x576470` 的调用者 `0x5744A0`、`0x573CD0 GetOffsetedGeometry`（2000 字节，也在 `..\common_cut\matrix.cpp`）。

---

## 6. 导出 NoFit API 逐个结论

| 导出 | RVA | 结论 |
|---|---|---|
| `NewNoFitContext` | 0x9AF0 | `new(0xF0)` + `CNS_NoFitContext(0x668F20)`；返回 240 字节上下文 |
| `DeleteNoFitContext` | 0x9CC0 | 按 §2.2 顺序销毁 6 个容器/指针，最后 `delete ctx` |
| `NewNoFitNesting` | 0x9330 | `new(0x20)`，`{ctx, vector<40B>}` |
| `DeleteNoFitNesting` | 0x9500 | `free([n+8]); delete n` |
| `NoFitAddNestedPart` | 0xA9D0 | push 40 字节 `{Part*, bool flip, double, double, double}` |
| `NoFitSetMaximumComplexity` | 0x9930 | `ctx[0xE8] = n`（默认 25000） |
| `GetNoFitMap` | 0x8AC0 | 角度→int64（×1e10）→ 0x665BF0 缓存/惰性计算 → 返回 `NoFitGeometry*` |
| `GetNoFitPlacementMap` | 0xA620 | 同类，走 ctx+0xA8 的缓存 |
| `DeleteNoFitGeometry` | 0x8A10 | 递归释放 `result[] → m_internal_paths[] → m_external_path` |
| `NoFitGetNumberOfExternalPolygons` | 0x89D0 | `result.size()`（元素 48 字节） |
| `NoFitGetNumberOfInternalHoles` | — | 断言字符串 `0x9AC59F` 存在；`CNS_NoFitGetNumberOfHoles` 0x8E70 为其实现 |
| `NoFitGetNumberOfPoints` | 0x8FC0 | `GetRing(...).size()`（Point = 16 字节） |
| `NoFitGetPoint` / `CNS_NoFitGetPoint` | 0x91C0 | 写回 `x`、`y` 两个 double |
| `CNS_NoFitGetNumberOfHoles` | 0x8E70 | `m_internal_paths.size()` |
| `NoFitGenerateSvgNesting` | 0x9550 | 无几何计算，只做参数校验/日志 + 生成 SVG（本文件未含对应 `..\geom\svg_io.cpp`? 实为 0x5DFF90） |
| `NoFitGenerateSvgGeometry` | 0x9790 | 同上 |
| `DrawSVG` | 0x85D0 | `cns_no_fit.cpp` 内的 SVG 输出，也用到 360/3.6e12/0.5 定标 |
| `ComputeNoFitSheetMap` | 0x665F40 (5289) | 按**板材**批量生成 NFP map（断言取自 `cns_no_fit.cpp` 池：`it != m_part_number.end()`、`n <= m_equivalent_problem->GetNumberOfParts()`）；`1e-6` 容差 |
| `CNS_NoFitContext` | 0x668F20 (2631) | 上下文构造函数 |
| `GetRing` | 0x7270 | 内部核心访问器（`cns_no_fit.cpp` 行 483/490） |
| `GetPart` | 0x74C0 | `(ctx, n)`，断言 `it != m_part_number.end()`(0x9AC48E) 与 `n <= m_equivalent_problem->GetNumberOfParts()`(0x9AC4A8) |

**未确认项**：`NoFitGenerateSvgNesting/Geometry` 的精确行为（只确认 0x9550/0x9790 无几何运算、只走 tracer+Svg 写出）；`SetInterpartGap` 的导出 RVA；`NoFitGetNumberOfInternalHoles` 是否有独立导出地址（导出表里 `0x9AC59F` 只作为 `CNS_NoFitGetNumberOfHoles` 的日志名出现）。

---

## 7. 取消 / 多线程（NFP 相关）

- `Multi::NoFitMapCanceller`：RTTI vtable `0xA3B8E0`（3 槽）。
- `NoFitMultiThreadComputer::RunAllComputations`：`std::thread::_State_impl<...>` RTTI `0xA54350`。
- `..\tiling\nofit_mapper.cpp` **0x7E6010 (7777 字节)** `NoFitMapper`，断言 `m_canceller != nullptr`（`0x9D...` 内联字符串）。**[证明]**

---

## 8. 复现用工具（本次新增，均在 `D:\Nesting\nestfab\re\`）

| 脚本 | 作用 |
|---|---|
| `g1_names.py` | 从 `prof2.pkl.own_plain` 还原 1738 个函数的 tracer 名；`nm(rva)` |
| `g2_rev.py` | 字符串 RVA → 引用它的函数（反查） |
| `g3_dis.py` | 带注解的反汇编（自动标注 call 目标名、rip 目标字符串/数据） |
| `g5_inline.py` | **重建内联构造的字符串字面量**（`__FILE__`/`__func__`/assert 文本），这是本次定位 `..\exact\*` 文件归属的关键 |
| `g6_region.py` | 按 RVA 区间批量重建字面量 |
| `g8_filemap.py` / `g9_allfiles.py` | 全库"源文件 → 函数"映射，输出 `out_g_filemap2.txt` |

---

## 附：点在多边形内 / 绕数例程的定位结果 —— **旧候选被否定，结论是"内联 + 断言"** **[本轮，已证实]**

§7.1 把"point-in-polygon / 绕数例程未定位"列为未确认，并给出候选
`0x576470 GetIntersectingIndex`、`0x573CD0 GetOffsetedGeometry`。
本轮用三条独立证据把这个问题收敛成一个**明确结论**。

### (a) 128 位精确谓词 `0x58E450` 的**全部**调用者只有 13 个 **[已证实]**

全代码段线性反汇编搜 `call 0x58E450`：

```
0x58C0C0 (73)   0x58C110 (82)   0x58C170 (65)   0x594CA0 (231)   0x594D90 (394)
0x594F20 (855)  0x595280 (1632) 0x595930 (82)    0x595990 (153)   0x595A80 (729)
0x595E50 (418)  0x596100 (3605) 0x5B36E0 (196)
```

**没有一个在 `0x57xxxx` 区** ⇒ 旧候选被否定：

* `0x576470`（2141 B）先用 `0x570050` 构造对象，再
  `imul eax,[rsp+0x1B0]` × `[rsp+0x1B8]`（**二维网格规模**）与
  `lea rcx,[rbx+rbx*4] ; shl rcx,3`（**每格 40 字节**），
  与 §7.4 记录的 `..\common_cut\matrix.cpp` 40 字节记录一致
  ⇒ 它是**共边矩阵构造器**，不是包含测试。
* `0x573CD0`（2000 B）同样不调用精确谓词。

其中三个小函数是**精确谓词的外壳**（不是包含测试）：

| 函数 | 大小 | 作用 |
|---|---|---|
| `0x58C0C0` | 73 B | `psubq` 组两个二维差分 → `0x58E450`；返回出参指针 |
| `0x58C110` | 82 B | 同上，但把结果里的**符号位**组合成 bool（`mov rax,[rsp+0x40] ; or rax,[rsp+0x48] ; setne`） |
| `0x58C170` | 65 B | 直接返回符号位（`movzx eax,byte [rsp+0x50]`） |
| `0x595930` / `0x595990` | 82 / 153 B | 两次调用精确谓词，用 `xor 1` / `and` 组合成**相对位置分类**（对象布局：`+0x20` 与 `+0x38` 两个标志、`+0x28..+0x30` 一个 pair） |

### (b) `Verify::DetectOverlap 0x99EAC0` 是**死代码** **[已证实]**

* 全库搜 `call 0x99EAC0` ⇒ **0 个调用者**。
* 它自身的指令说明了它在做什么：`0x99EAC0` 先 `lea rcx,[rip+0x18408B]` + `call 0x943890`，
  再用两个立即数拼串 —— `0x764F746365746544` = `"DetectOv"`、
  `0x3A3A796669726556` = `"Verify::"`，随后补 `"erlap"` ⇒
  它只是**断言消息 `"Verify::DetectOverlap"` 的构造器**，真正的检查内联在调用点，
  而这里**连调用点都没有**。

⇒ 该项从"只是抛异常的校验钩子"**升级为"零引用死代码"**，可彻底排除。

### (c) 包含测试**存在**，但它是**内联的**：只在断言里留下痕迹 **[已证实]**

| 字符串 | RVA | 说明 |
|---|---|---|
| `..\geom\` + `ring.cpp` | `0x5C58A5` / `0x5C5896` | 该串簇属 **`..\geom\ring.cpp`**；`'ContainsH'`(`0x5C5852`) 与 `'.size() H'`/`'points()H'` 一样，是**内联断言串的尾部碎片**（`movabs` 拼串的产物） |
| `..\nesti`+`ng\nesti`+`ng.c` | `0x16C5EB` / `0x16C602` / `0x16C61D` | 属 **`..\nesting\nesting.c…`**；同簇含 `'m_windowH'`、`'RestrictH'`、`'.ContainH'`、`'s(windowH'` |
| `old.Contains(nnp.m_window)` | `0x9BF9B8` | 完整断言表达式，被 **`0x1C1A60`（734 B）** 引用 |

而 `0x1C1A60` 又是**断言消息构造器**（`0x919EC0` 建串 → `0x978010` 追加 →
`0x8688E0` 以 `xmm1` 把 double 格式化后追加 → `0x1C1010`/`0x82B7B0` 小工具），
所以"包含测试"**没有独立的被调用函数**：检查内联在断言点。

### (d) `Contains(window)` 的判据已从 `0x1C1A60` 的指令读出 **[已证实]**

```
1C1AC2  xmm1 = [rbx + 0x60]                 ; 本对象的窗口下界（x 或 y）
1C1ABA  xmm0 = [rodata 0x9BFD30] = 0.001   ; 容差
1C1ACC  xmm1 += xmm0
1C1AC7  xmm6 = [rax + 0x60]                 ; 另一对象的同一字段
1C1AD5  ucomisd xmm1, xmm6 ; jae → 失败路径
```

⇒ **`Contains(window)` = 对对象 `+0x60` / `+0x68` 两个 double 的"带容差的窗口包含"测试**
（`+0x60`/`+0x68` 是该对象的窗口/包围盒对，容差常量在 `0x9BFD30` = 0.001）。
它**以内联 + 断言的形式存在**，所以"按函数找不到"是**结构性的**，不是遗漏。

### 结论（这一段替换 §7.1 的"未确认"）

| 原项 | 新状态 |
|---|---|
| point-in-polygon / 绕数例程未定位 | ✅ **结案为结构性结论**：精确谓词的 13 个调用者已穷举（全在 `..\exact\*`，均为线段/环的相对位置分类）；包含测试**内联**在 `..\geom\ring.cpp` 与 `..\nesting\nesting.c…` 的断言点，判据已读出（`+0x60`/`+0x68` + 容差 + `ucomisd`）；两个旧候选**被否定** |
| `Verify::DetectOverlap 0x99EAC0` | ✅ 升级为**零引用死代码** |
| `0x576470` / `0x573CD0` | ✅ 前者定性为 `..\common_cut\matrix.cpp` 的 **40 字节网格矩阵构造器**；后者不用精确谓词，与包含测试无关 |
