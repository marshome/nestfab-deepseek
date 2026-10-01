# COIN-OR 的使用面逆向报告 — `Lp::LinearProgram` / `Coin::CoinLP` / `BuildAndSolveLp`

目标文件：`D:\Nesting\nestfab\libcns_dump_64.dll`（MD5 `01fea4b73a33dd233c66ca76235313fa`，
内存 dump，ImageBase `0x6B4C0000`，非加载型）。所有地址均为 **RVA**。
标注约定：**[已证实]** / **[推断]** / **[未确认]**。

本报告补的是 [`findings_lp.md`](findings_lp.md) 与 [`REPORT.md`](REPORT.md) §7.3 里
**"Clp 究竟在解什么"** 这一个未确定项，并且**纠正** `findings_lp.md` §6 的过时结论。

---

## 0. 结论速览

| 问题 | 结论 |
|---|---|
| 二进制里有 OR-Tools 吗？ | **没有。** 13 个 OR-Tools 标记（`ortools` / `OR-Tools` / `operations_research` / `GlopParameters` / `glop` / `MPSolver` / `linear_solver` / `SatParameters` / `BopParameters` / `RoutingModel` / `cp_model` …）在 11.8 MB 全文件扫描中 **0 命中**。 **[已证实]** |
| 用的是哪个求解器？ | **COIN-OR Clp 1.15.3**，静态链接，经 `OsiClpSolverInterface`；构建路径串 `C:\Users\renaud\nest\external\Clp-1.15.3\Clp\src\ClpSimplexDual.cpp`、`…\Clp-1.15.3\CoinUtils\src\CoinLpIO.cpp`。 **[已证实]** |
| `Coin::CoinLP` 是死代码吗？ | **不是。** `findings_lp.md` §6 的"引用数 = 0 ⇒ 死代码"是方法学误判（搜了 vtable 头部而非地址点）。它被构造，且**被使用**。 **[已证实]** |
| Clp 在解什么？ | **板材选择集合覆盖 LP**：变量 = 候选板材，目标 = Σ `sheet.price() · x_s`，约束 = 每个零件一条 `Σ_s count[s][p] · x_s ≥ demand(p)`。**不是** Dantzig–Wolfe 主问题。 **[已证实]** |
| 解出来用了吗？ | **用了。** Database 侧解完后读 `CoinLP` slot 10（原始解向量）并回映到板材记录上。 **[已证实]** |

---

## 1. 求解器归属：OR-Tools vs COIN-OR

脚本 `g_solver_probe.py` 对全文件做大小写不敏感正则扫描：

```
--- OR-Tools ---
   ortools 0    OR-Tools 0    operations_research 0    GlopParameters 0    glop 0
   MPSolver 0   linear_solver 0   sat_parameters 0   SatParameters 0   BopParameters 0
   operations-research 0   RoutingModel 0   cp_model 0

--- COIN-OR ---
   ClpSimplex 6      OsiClp 48      ClpModel 94      CoinLpIO 20      CoinPackedMatrix 7
   CoinBuild 2       CoinUtils 1    CoinMessageHandler 1    Idiot 3
```

假阳性已排除：`Xpress` 那 1 处是 Clp 自带的玩笑串（`you really need Xpress from Dash
Associates :-)`）；`Cbc` 13 处是 base64 数据与 OpenSSL 的 `CBC` 分组模式串；`GLPK is not
available` 也是 CoinUtils 的消息。 **[已证实]**

静态链接的旁证（findings_lp.md §5.2 已记录，本报告复核）：`ClpDualRowDantzig`、
`ClpPrimalColumnDantzig`、`ClpPrimalColumnSteepest`、`ClpDualRowSteepest` 在 RTTI 名表里
（`0xA21120`–`0xA21ED0`，共 70 个 COIN 类名）⇒ **单纯形主循环来自 Clp 自身**，不是 app 自己写的。

---

## 2. `Coin::CoinLP`：对象布局与虚表

### 2.1 布局 **[已证实]**

| 偏移 | 内容 |
|---|---|
| `+0x00` | vptr（指向地址点 `0xA3B280`） |
| `+0x08` | 求解器对象指针（`ClpSimplex*` 角色） |
| `+0x10` | 一个字节标志（slot 3 写它） |
| `+0x18` / `+0x30` / `+0x48` | 三个并行 `std::vector<double>`（各占 0x18：begin/end/cap） |
| `+0x60` … `+0xE8` | 更多成员（构造时全部清零；成对的 `[+X] → [+X+8]` 平移是空 vector 的平凡搬移） |

实例大小 **0xF0 = 240 字节**（构造器 `0x26776A` 的 `mov ecx, 0xf0`）。 **[已证实]**

### 2.2 构造器 `0x267760`（719 B / 139 条指令） **[已证实]**

```
0x267760  CoinLP* make()
  0x26776A  ecx = 0xF0 ; call operator new          ; 240 B 的 CoinLP
  0x26777C  lea rax,[rip+…] = 0xA3B280 ; mov [rbx],rax   ; 装 vptr（地址点）
  0x267786  ecx = 0x418 ; call operator new         ; 1048 B 的求解器对象
  0x267791  call 0x281BA0                           ; 构造它
  0x26779B  mov [rbx+8], rsi                        ; this->m_solver = 它
  …        清 +0x18 … +0xE8
  0x2678BE  call [solver_vt + 0xC0](0, 0x2710)      ; 配置：0, 10000
  0x2678CD  xmm1 = [0x9C2E18] = 0.5 ; call 0x2B1720 ; 设 0.5
  0x2678E6  mov dword [solver + 0x2E8], 3           ; 模式 3
0x267730    (22 B 的转发构造 thunk：mov rbx,rcx; call 0x267760; mov rax,rbx; ret)
```

`0x281BA0`（693 B）是被包装的求解器对象的构造器。 **[已证实结构]**

### 2.3 虚表 13 个槽逐个定性 **[已证实]**

vptr 指向**地址点**（vtable 头 `0xA3B270` + 0x10 = `0xA3B280`），因此槽 k 在 `vptr + 8k`。

| 槽 | vptr 偏移 | 实现 | 大小 | 语义 |
|---|---|---|---|---|
| 0 | `+0x00` | `0x679E70` | 198 B | 析构（完整对象，装 vtable） |
| 1 | `+0x08` | `0x679DB0` | 187 B | 析构（删除版） |
| 2 | `+0x10` | `0x679C20` | 214 B | **init/重置**：调求解器 `vt+0x498`、`vt+0xC0(0,10000)`、设 `0.5`、写模式 `3` 到 `+0x2E8`（与构造器同序） |
| 3 | `+0x18` | `0x679660` | **4 B** | `mov byte [rcx+0x10], dl; ret` —— 标志位设置器 |
| 4 | `+0x20` | `0x6792C0` | 345 B | **追加一列**：往 `+0x18` / `+0x30` / `+0x48` 三个并行 double 向量各 push 一个值；用 `±DBL_MAX`（`0x9C2E20`/`0x9C2DF8`）作边界；经求解器 `vt+0x220` 读一个值，`dl==0` 时还会 `xorpd` 取负 |
| 5 | `+0x28` | `0x679670` | 715 B | **追加一行**：只调 `operator new`/`delete`/vector 增长（`0x998500`/`0x9984B0`/`0x90BEF0`），把 `(n, 下标, 系数, 右端)` 存进成员向量，**不碰求解器** |
| 6 | `+0x30` | `0x679940` | 723 B | 同样的追加型例程（第二族行/列） |
| 7 | `+0x38` | `0x679420` | 575 B | 同样的追加型例程 + 取值 |
| 8 | `+0x40` | `0x679D00` | 168 B | **提交 + 求解**：调 `0x7CA830` 装配，再两次虚调用（求解器 `vt+0x00`、`vt+0x100`），返回状态 |
| 9 | `+0x48` | `0x7CB700` | 14 B | 转发 → 求解器 `vt+0x248` |
| 10 | `+0x50` | `0x7CB710` | 14 B | 转发 → 求解器 `vt+0x228`（**解向量**） |
| 11 | `+0x58` | `0x7CB740` | 14 B | 转发 → 求解器 `vt+0x230` |
| 12 | `+0x60` | `0x7CB720` | 18 B | `r8d=1` 后 `jmp 0x7CA830`（带标志的重复装配） |

`0x7CA830`（3778 B）的字符串只有 `'   '`（`0x9C2DF2`，出现 8 次），并调用
**`0x267A30`（532 B）**（紧邻构造器之后，属于同一族）⇒ 它是"把累积的列/行装进求解器"的装配例程，
带表格化输出。 **[已证实结构 / 输出格式未展开]**

> 关于 `ClpSimplex` 的具体方法名：findings_lp.md 依据 COIN-OR 1.15 的 `ClpSimplex` 槽位
> 把 `+0x228/+0x230/+0x248` 分别对应 `primal()` / `dual()` / `solve()`。这一点是
> **[推断]**（槽位数与继承 `ClpModel` 的布局吻合），本报告沿用。槽 10 被实测用于取解（见 §4），
> 与该推断一致。

---

## 3. `BuildAndSolveLp`（`0x7D7200`，1520 B / 330 条指令） **[已证实]**

### 3.1 身份

函数内部的三个字符串：

```
'biggest_sheet->price()'     断言表达式        @0x9B0776
'BuildAndSolveLp'            它自己的 symlog 标签 @0x9B0810
'..\multi\database.cpp'      源文件            @0x9B0710
```

断言掷出时传的行号是 **`0x1C2` = 450**（`0x7D76FA` 的 `mov edx, 0x1c2`，随后 `call 0x60A620`）
⇒ **`assert(biggest_sheet->price())` @ `..\multi\database.cpp:450`**。 **[已证实]**

### 3.2 逆出的伪代码

```cpp
// rcx = problem/context, rdx = &CoinLP
bool BuildAndSolveLp(Problem* problem, CoinLP** lpp) {
    CoinLP* lp = *lpp;
    {/* 0x5F4310 构造一个 RAII 作用域对象（vtable 在 RVA 0xB1F5C0） */}

    lp->vcall_slot3(0);                       // 0x7D7257 / 0x7D752C：清 +0x10 的标志

    // 第一趟：遍历整张 problem 的板材记录，每张板材加一列
    for (Record* r = problem->begin; r != problem->end; r += 0x1A8) {   // 步长 0x1A8 = 424
        double price = /* 0x51D2F0(r) → 0x4F8550(..) */;                 // 取该板材的 price
        lp->vcall_slot4(/*isMin*/1, /*coef*/0.0, /*hasUpper*/false,
                        /*upper*/0.0, /*cost*/price);
    }

    const int nParts = problem->NumberOfParts();          // 0x4FC5A0（8 B 的访问器）
    const double biggest = priceOfBiggestSheet();          // 0x523050 → 0x4F8550
    if (biggest == 0.0) assert("biggest_sheet->price()");  // database.cpp:450

    for (int p = 0; p < nParts; ++p) {
        std::vector<int>    idx;
        std::vector<double> val;
        for (Record* r = problem->begin; r != problem->end; r += 0x1A8) {
            const double c = (double)r->counts[p];   // r[0x138] 是 int 数组，按零件索引
            if (c != 0.0) { idx.push_back(recordIndex); val.push_back(c); }
        }
        if (idx.empty()) {                            // 该零件在任何板材里都不出现
            idx.push_back(<被乘数 0x8C13521D 混合出的下标>);
            val.push_back(1.0);                       // ← 常量 @0x9B08B0 = 1.0：单位系数松弛列
        }
        const int demand = partDemand(problem->GetPart(p));   // 0x4FC5B0 GetPart → 0x4F7050
        lp->vcall_slot5(idx.size(), idx.data(), val.data(), (double)demand);
    }

    const int rc = lp->vcall_slot8();                 // 0x7D752C：装配 + 求解
    return rc == 0;                                   // 0x7D752F：test eax,eax; sete bl
}
```

### 3.3 用到的常量

| RVA | 值 | 用途 |
|---|---|---|
| `0x9B08B0` | `1.0` | 松弛列的系数（不是罚因子） |
| `0x9C2E18` | `0.5` | 构造器/slot 2 配置求解器时用 |
| `0x9C2DF8` | `+DBL_MAX` | 求解器的 +∞ 边界 |
| `0x9C2E20` | `−DBL_MAX` | 求解器的 −∞ 边界 |
| `0x9C2E30` | `−0.0` | `xorpd` 取负用 |
| `0x7C9A10` | 函数地址 | 求解器 `vt+0x220` 的"平凡实现"哨兵，用于跳过虚调用 |

### 3.4 所以 Clp 在解什么 **[已证实]**

```
变量：x_s   ，每张候选板材一个（slot 4 一趟加完）
目标：min  Σ_s  price(s) · x_s
约束：对每个零件 p ：  Σ_s  count(s, p) · x_s  ≥  demand(p)     （slot 5 一趟加完）
      x_s ≥ 0
```

这是一条**集合覆盖 / 下料（cutting-stock）型的"板材选择"LP**：列是**板材**，不是 pattern。
`findings_lp.md` §3.3 对 `Prc::` 的"面量打分/候选评分"判断与之自洽——真正的 LP 只负责
**在已有候选板材里挑一组最省的来覆盖零件需求**。 **[已证实]**

因此 `REPORT.md` §7.3 的未确定项 1「`Clp` 究竟在解什么」**结案**：
不是 Dantzig–Wolfe 主问题，而是上述覆盖 LP。

---

## 4. 使用点：谁构造、谁求解、解怎么用 **[已证实]**

| 位置 | 角色 |
|---|---|
| `0x267760` | `CoinLP` 构造/工厂（vtable 地址点 `0xA3B280` 在 `0x26777C` 被 `lea`） |
| `0x24E2D0`（154 B） | 构造 CoinLP 并存进一个持有者对象（`[+0]=CoinLP*`、`[+8]=−1`、`[+0x10..+0x20]` 清零），随后调 slot 3 清标志 ⇒ 持有者类的构造器（对应 RTTI 里的 `Lp::LinearProgram` 层） |
| `0x25B040`（4303 B） | 构造 CoinLP，随后调 `0x266D50`，把 `[+0x88]/[+0x8C]/[+0x90]` 置 `0xFFFFFFFF` ⇒ 另一条装配入口 |
| `0x59AC0`（624 B，含串 `linear`） | `CoinLP lp; if (BuildAndSolveLp(ctx, &lp)) { … 生成名为 "linear" 的结果（0x4D3C00） }` |
| `0x6A6AD0`（3369 B，`Database` 族） | `CoinLP lp; if (BuildAndSolveLp(db, &lp)) { x = lp.slot10(); n = 板材数; 0x5238B0(out, problem, n) … }` |

**`0x6A6AD0` 的解消费路径**（`0x6A6B7E` 起）：

```
0x6A6B7E  call BuildAndSolveLp
0x6A6B8F  and dl, al                     ; 与一个外部标志合取
0x6A6B95  je  …                          ; 失败则跳过
0x6A6BA3  call [vptr + 0x50]             ; = slot 10 → 求解器 vt+0x228  ← 取原始解向量
0x6A6BC9  sar rbx, 3 ; imul rbx, 0x21CFB2B78C13521D   ; 记录数/散列混合
0x6A6BD1  call 0x5238B0                  ; 把解回映到板材
```

⇒ **解被真实消费**（读解向量 → 选板）。这是判定"活代码"的决定性证据。 **[已证实]**

### 4.1 纠正 `findings_lp.md` §6

`findings_lp.md` §6 对整个 `Lp::`/`Coin::CoinLP`/`Prc::`/`Row::` 族给出"已编译但未接线（dead
code）"的结论，依据是"vtable 引用数 = 0"。该方法搜的是 **vtable 头部地址**
（`0xA3ADA0` / `0xA3B270` 等），而 C++ 的 vptr 存的是**地址点**（`vtable+16`），代码里只出现地址点。

用地址点重扫（`REPORT.md` §7.3 已纠正为"被构造"），本报告进一步证明：`Coin::CoinLP` 不只是
被构造，还**被求解并被消费**。`findings_lp.md` §6 的那张表与结论**应整体作废**，
`§0` 表格里"没有/死代码"三处、"§6.1"末尾的旁注也需相应修订。 **[已证实]**

---

## 5. `Prc::` / `Row::` 侧：本轮补上的与仍缺的

### 5.1 LSQR 归属（原 §7 未确认项） **[已证实]**

`0x9A74A0` 那组 LSQR 的 `istop` 消息（`The exact solution is x = 0` …）在全库只有两处引用，
都在 **`0x3B84E0`** 内（`0x3BA0A4`、`0x3BA114`）⇒ **LSQR 的实现体在 `0x3B84E0`**，
与 `Lp::`/`Prc::`/`Row::` 无引用关系，属独立静态链接库。原 §7 的"函数体位置未定位"**结案**。

### 5.2 `Row::Squeezer` 的成本函数 `0x1380D0` **[部分证实]**

- 大小 **2375 B / 476 条指令**（远大于一个"成本公式"）。
- 入口：`cmp byte [rdx+8], 0` → 为 0 时**提前返回**；`mov byte [rcx], 0` 先把输出字节清 0。
- 参数形态 `(rcx = 输出字节, rdx = 带标志的状态对象, r8, r9)` ⇒ 它是**区间记忆化缓存的
  "未命中则计算"入口**，返回的是**状态字节**；double 值由调用方从缓存节点 `node[+0x30]` 读
  （findings_lp.md §4 已证）。
- **[未确认]**：它内部那 476 条指令对应的**成本公式**（量纲、是否含距离/挤压量加权）本轮未逐条译出。
  这一项保持未确认，未做近似。

### 5.3 `Prc::BoostAlpha` / `SurfaceCoeffs` / `DimAlpha` **[已证实：连 typeinfo 对象都不存在]**

findings_lp.md 原话是"只有 RTTI 名字串、全库零指针引用 ⇒ 非多态型别"。本轮把这条**收紧**并纠正方法：

- **指针编码陷阱**：内存 dump 的**数据段**里存的是**运行时绝对 VA**（`ImageBase + RVA`，
  `ImageBase = 0x6B4C0000`），不是裸 RVA。用裸 RVA 搜 typeinfo 名字串会得到 0 命中。
- 用绝对 VA 重搜（已用已知 typeinfo 自检）：

  | 名字串 | 指向它的指针数 | 结论 |
  |---|---|---|
  | `N3Prc13PriceComputerE` `0xA22280` | 1（`0xA17D50` 的 `[+8]`） | 正常 typeinfo |
  | `N3Prc16BoxPriceComputerE` `0xA222C0` | 1（`0xA17D60` 的 `[+8]`） | 正常 typeinfo |
  | `N2Lp13LinearProgramE` `0xA22240` | 1（`0xA17D40`） | 正常 typeinfo |
  | `N4Coin6CoinLPE` `0xA22410` | 1（`0xA17EA0`） | 正常 typeinfo |
  | **`N3Prc10BoostAlphaE` `0xA22260`** | **0** | **孤立的名字串，无 typeinfo 对象** |
  | **`N3Prc13SurfaceCoeffsE` `0xA222A0`** | **0** | 同上 |
  | **`N3Prc8DimAlphaE` `0xA22340`** | **0** | 同上 |

  ⇒ 这三个**不是"非多态的类"，而是连 RTTI 对象都没生成**（既无 vtable 也无 typeinfo），
  只剩编译器留下的名字串。 **[已证实]**
- **字段布局 [未确认]**，且现在能说清为什么不可达：没有 typeinfo 可依附；它们仅有的两个
  出现点是**日志/断言标签**（`0x220ED0` 用 `'AP '`、`'AlphaSurfacePricer '`；`0x23B080` 用
  `'Pb pricing '`），附近**没有可反推布局的字段写入**。
- **顺带确认的一个具体事实**：`0x23B080`（`..\nesting\algos\old_beam.cpp`）通过
  `AssertCoherency` 断言 `m_eval.m_c == c` 与 `m_eval.m_v == v`，比较是**值级**
  `ucomisd xmm6, xmm0` ⇒ beam 节点的 `m_eval` 缓存里有标量 `m_c`、`m_v`；
  其**结构体偏移**需要断言点上方的寄存器装填，本轮未取。 **[已证实（断言文本与比较形式）/ 偏移未确认]**

---

## 6. 对 `lcns` 工程的后果

原库的 LP 层是：

```
Prc::PriceComputer (抽象)
  └─ Lp::LinearProgram
       └─ Coin::CoinLP        // vptr[+0] + 求解器*[+8]，13 个虚槽
            ↑ 由 BuildAndSolveLp（..\multi\database.cpp）驱动：
              一列/板材（cost = price()）、一行/零件（Σcount ≥ demand）、slot 8 提交求解、
              slot 10 取解
```

工程里此前的 `lcns::lp::Simplex` + 自定 `MasterProblem`/`columnGeneration` 是**替代品**，
不是还原：它把"手写单纯形"和"我自己的主问题"缝在一起，而原库是"Clp 后端 + 集合覆盖装配器"。
`lp_model.hpp` / `buildAndSolveLp` 因此按上表补出（见 `lcns/include/lcns/lp.hpp` 的
`LinearProgram` / `SimplexLinearProgram` / `buildAndSolveLp`），后端可换；手写单纯形保留为
零依赖默认后端。
## 7. 复现脚本（均在 `D:\Nesting\nestfab\re\`）

| 脚本 | 作用 | 输出 |
|---|---|---|
| `g_solver_probe.py` | 全文件扫 OR-Tools / COIN-OR / 其它求解器标记 | 控制台 |
| `g_clp_use.py` | 找 Clp 转发 thunk、装配例程、构造器的调用点；解析 CoinLP 地址点引用 | 控制台 |
| `g_coinlp_sites.py` | 4 个构造点各自的上下文 | 控制台 |
| `g_buildandsolve.py` | `BuildAndSolveLp` 全反汇编 + 字符串 + 调用者 | `out_g_buildandsolvelp.txt` |
| `g_coinlp_vtable.py` | 13 个虚槽逐个解析 + 首几条指令 | 控制台 |
| `g_lp_sweep.py` | 批量：常量、槽体、`0x7CA830`、helper、构造点、§8 遗留项 | `out_g_lp_use_sweep.txt` |
| `g_close_unknowns.py` | 四个收口目标的整函数反汇编 | `out_g_1380d0.txt` / `out_g_267a30.txt` / `out_g_7ca830.txt` / `out_g_factory.txt` |
| `g_lp_dump.py` | 找 LP/MPS 转储路径 + 流辅助函数识别 | 控制台 |
| `g_angle_and_sin.py` | 角度原语常量与 `sin` 块的反汇编窗口 | 控制台 |
| `g_prc_types2.py` / `g_prc_layout.py` | Prc 三个数据型别的 typeinfo 探测与布局尝试 | `out_g_prc_layout.txt` |
| `g_chain.py` / `g_nofit_dis.py` / `g_conv_callers.py` | 非凸 NFP 与 NFP 适配器链（见同一轮的 NFP 报告修订） | `out_g_nofit_dis.txt` 等 |

---

## 8. `Row::Squeezer` 的成本原语（**本轮新挖**）

### 8.1 修正一处此前的误标 **[已证实]**

`findings_lp.md` §5.3 把 `0x7CA830`（3778 B）描述为"addColumn / addRow 装配"。本轮读出它的**调用形态**：

* 唯一直接调用者是 `CoinLP` **slot 8 = `0x679D00`**，调用形式为
  `call 0x7CA830(rdx = 求解器对象, r8d = 0, r9 = &局部 std::string)`；该 string 是
  **{ptr@+0, size@+8, SSO buf@+0x10}** 的标准 libstdc++ 布局（`0x679D1A` 后 size=0、
  `0x679D23` 取 `rbx+0x10` 作数据指针），用完立刻析构 ⇒ 它是**临时缓冲**。
* `0x7CA830` 内部：先 `call 0x267A30`，再两次 `_M_fill_insert`（`0x96D6E0`），
  然后 **18 次 `0x978010`（ostream 数值插入）**，每次都紧跟 `'   '`（`0x9C2DF2`）分隔串，
  期间 `basic_ios::clear`（`0x9456A0`）出现在**异常清理路径**上 ⇒ 它**通过 ostream 格式化输出**。
* **`0x267A30` 不是"Clp 装配"，而是 `std::sort` 实例** **[已证实]**：`cmp rax,0x10f` 阈值 +
  三点取中 + `__unguarded_partition` 风格循环 + **对自身递归**（`0x267B51` 的 `call 0x267A30`）
  + 循环调 `0x95A5F0`（插入排序）。比较键是 16 字节记录的
  **(int@+0xC, int@+8, double@+0)** 字典序 —— 即把 `{double,int,int}` 三元组**按 (行,列) 排序**，
  这正是 COO 三元组交给求解器前的标准动作。

⇒ `0x7CA830` 的准确定性：**把累积的三元组排序后格式化/装填，并用一个临时 string 作缓冲**；
其中"装填进求解器"与"格式化成文本"两种读法在本轮证据下**尚未最终区分**（两者都符合已观测的
调用形态与指令特征）。**求解动作本身在 slot 8 里**：

```
0x679D2F  call 0x7CA830(solver, 0, 0, &scratch)
0x679D56  call [solver_vt + 0x00]      ; 求解器虚槽 0
0x679D5F  call [solver_vt + 0x100]     ; 求解器虚槽 +0x100
0x679D6F  xor esi, 1                   ; 返回值取反
```

### 8.2 角度原语 `0x5C22D0`（157 B）—— **完全译出** **[已证实]**

```c
// rcx = 指向两个 double 的方向向量 {x, y}
int64_t AngleToFixedDegrees(const double* v) {
    if (v[0] == 0.0 && v[1] == 0.0) return 0;          // 0x5C22E7/0x5C2336
    double a = atan2(v[1], v[0]);                       // 0x634C70 = x87 fpatan（全库唯一 atan2）
    a = a / 6.283185307179586;                          // 0x9DE758 = 2π
    a = a * 3600000000000.0;                            // 0x9DE740 = 360e10
    a = a + 0.5;                                        // 0x9DE750  → 四舍五入
    int64_t r = (int64_t)round(a);                      // 0x62FA20
    while (r < 0)          r += 3600000000000LL;         // 0x5C231F 回绕
    while (r > 3600000000000LL) r -= 3600000000000LL;    // 0x5C2360 回绕
    return r;                                            // ∈ [0, 360e10)
}
```

三个常量已逐个读出：`0x9DE758 = 6.283185307179586`、`0x9DE740 = 3.6e12`、
`0x9DE750 = 0.5`；边界 `0x34630B8A000 = 3.6e12 = 360 × 1e10`。

### 8.3 `0x1380D0` 的 `sin` 块 —— **完全译出** **[已证实]**

```
0x1386F8  call 0x5C22D0            ; rax = 定点角度 index ∈ [0, 360e10)
0x13870A  imul 0x9C5FFF26ED75ED55  ; 除以 3.6e12 的魔数（高半在 rdx）
0x13871C  rax -= (rcx >> 63)       ; 商取整
0x138729  rax *= 3.6e12
0x138730  rdx = rcx - rax          ; angleIndex mod 360e10
0x138736  rax == 0        → sin = 0    （精确）
0x138746  rax == 0xD18C2E2800 (=90e10)  → sin = +1（精确，跳过 libm）
0x138755  rax == 0x1A3185C5000 (=180e10) → sin = 0
0x138768  rax == 0x274A48A7800 (=270e10) → sin = −1
otherwise:
0x13877A  xmm0 = (double)angleIndex / 3.6e12     ; ∈ [0,1)
0x138782  xmm0 *= 6.283185307179586               ; → 弧度 ∈ [0, 2π)
0x13878A  call sin                                ; 0x635970（x87/静态 libm）
```

⇒ 该块算的是 **`sin(2π · angleIndex / 360e10)`**，即**方向角的弧度正弦**，
并对 0°/90°/180°/270° 走精确分支（避开 libm 误差）。四个魔数已逐个核对：
`0xD18C2E2800 = 9e11`、`0x1A3185C5000 = 1.8e12`、`0x274A48A7800 = 2.7e12`。

### 8.4 相邻距离与区间访问器 **[已证实]**

```
0x1381EB  xmm6 -= [rsp+0xD8]
0x1381FA  xmm1 *= xmm1
0x1381FE  xmm8 -= [rsp+0xE0]
0x138208  xmm0 += xmm1              ; a² + b²
0x138210  sqrtsd xmm9, xmm0         ; 内联 sqrt
0x138217  call sqrt                 ; 0x62FE20：xmm7 > xmm0 时走 libm（负/NaN 等边界）
```
⇒ **`sqrt(a² + b²)`**（hypot 形式的距离），并与 `xmm7` 比较（阈值分支）。
`xmm7` 全程被当作 0 使用（`pxor`/`ucomisd` 比较），故阈值为 0。

两个小助手：

| 地址 | 大小 | 语义 **[已证实]** |
|---|---|---|
| `0x134FA0` | 68 B | `optional<Interval>` 取用：`(out, src, bool)`，按 bool 选 `src+0x48` 或 `src+0x70`；被选项首字节为 0 则 `*out = 0`（空），否则 `*out = 1` 并 **拷贝 4 个 double（0x20 字节）** 到 `out+8..+0x20` ⇒ **区间值类型 = 4×double（很可能是 2D 盒 xmin/ymin/xmax/ymax）** |
| `0x134FF0` | 21 B | `(obj, bool) -> obj+0xA8` 或 `obj+0xC0`：**按 bool 在 +0xA8 / +0xC0 两个成员间二选一** |

### 8.5 成本公式本体 —— **已译出主表达式** **[已证实]**

`0x1380D0` 的签名由调用点 `0x13A360`（`Row::Squeezer` 的 slot 2）定出：

```
0x13A360  Row::Squeezer::slot2(this, rdx, r8)
    rdi = [this+8]                     ; 内部对象：两棵区间 map 在 +0x240 / +0x248
    在 +0x248 的红黑树上按键 (lo,hi) 下降：命中条件  lo <= node.lo  且  node.hi <= hi
    未命中：
0x13A3C0  r9 = rsi(hi) ; r8 = rbx(lo) ; rdx = rdi(obj) ; rcx = rbp(&result)
0x13A3CC  call 0x1380D0                ; 0x1380D0(&result, obj, lo, hi)
0x13A3D1  if (result.present == 0) goto 未定义
0x13A3D8  xmm0 = result.value
0x13A3FD  call 0x923990                ; 插回 +0x240 的 map（key={lo,hi}, value=cost）
0x13A407  xmm0 = [node+0x30]           ; 返回节点里的 double
```

⇒ `bool cost(Result* out, const Obj* obj, const Row* lo, const Row* hi)`，
其中 `out[0] = present`、`out[8] = double`；`lo`/`hi` 是**对象指针**（不是整数）——
体内两次 `0x134FA0` 分别在 `lo` 上按 bool=1 取 `+0x48`、在 `hi` 上按 bool=0 取 `+0x70`，
每次拷贝 **4 个 double**，即 **`lo`/`hi` 各带两份区间候选，由 `obj[+8]` 这个标志选择**。

主表达式（`0x13879E`–`0x1387E9`，逐指令）：

```c
A = opt(lo, +0x48);  B = opt(hi, +0x70);            // 5.4 节的 0x134FA0
dA = (A.v2 - A.v0, A.v3 - A.v1);  lenA = sqrt(dA.x² + dA.y²);   // 0x1381A6..0x138210
assert(lenA != 0);                                             // 0x13821C，失败即抛（串含 "distance"）
uA = dA / lenA;                                                // 0x1387EE 的 1/lenA + mulpd
dB = (B.v2 - B.v0, B.v3 - B.v1);  lenB = sqrt(...);  assert(lenB != 0);
uB = dB / lenB;                                                // 0x13880F
s  = sin(angleToFixedDegrees(uA));                              // 0x1386F8 → 8.3 节的 sin 块
cost = obj[+0x10] / s  -  max(|A.v0 - A.v2|, |B.v0 - B.v2|);    // 0x1387D6 / 0x1387DB
out[8] = cost;  out[0] = 1;                                     // 0x1387E4 / 0x1387E9
```

即：**`cost = 阈值 / sin(行方向角) − max(A 的 x 跨度, B 的 x 跨度)`**，
阈值取自 `obj[+0x10]`。数学上 `sin(angleToFixedDegrees(uA)) == uA.y`，原库仍绕定点角度
走一遍（在 0/90/180/270 度取精确值，见 8.3）。

另有若干 **0.005 容差闸**（常量 `0x9BCFD8 = 0.005`）在 `0x13864E`–`0x138694`：
对若干坐标差取 `fabs` 后若 `> 0.005` 就跳到 `*out = 0`（放弃，不记缓存）。
断言串的碎片已读到：`0x138842` 的 `0x203E2073` = `"s > "`、`0x1388D4` 的
`0x636E6174` + `0x65` = `"tance"` ⇒ 含 **"distance"** 字样。

### 8.5b 两条前置条件 —— **本轮新增确认** **[已证实]**

**(a) 平行性闸（`1e-6`）**。`0x1385A1`–`0x1385C9`：

```
1385A1  xmm6 = uB.x * uA.y
1385A7  xmm0 = uB.y * uA.x
1385B5  xmm0 -= xmm6                 ; = uA.x*uB.y - uA.y*uB.x = cross(uA,uB)
1385C1  fabs
1385B..  xmm1 = 1e-06 (0x9BCFC0)
1385C5  ucomisd xmm1, xmm0
1385C9  ja 0x1386F3                  ; 1e-6 > |cross|  ⇒ 平行 ⇒ 走角度路径
```

**陡转**：`ja` 的方向说明当 `1e-6 > |cross|`（**平行**）时才跳到 `0x1386F3`
（即 `call 0x5C22D0` 的角度路径）；**不平行**则顺序落到 `0x1385D0` 的闸块，
该闸块所有失败分支都归到 `0x1386EE jmp 0x138121`（`*out = 0`）。
⇒ **`Row::Squeezer` 的成本只对平行的两行适用**；不平行即"不适用"。

**(b) 区间表逐元素对齐闸（`0.005`）**。`0x1385E3`–`0x1386C3`：

```
1385E3  rcx = lo ; edx = 1 ; call 0x134FF0    ; → lo + 0xA8   （bool=1 → +0xA8）
1385F0  edx = 0  ; rcx = hi ; call 0x134FF0    ; → hi + 0xC0   （bool=0 → +0xC0）
1385FD  r10 = ([lo+0xA8].end - [lo+0xA8].begin) >> 5   ; 元素 = 32 字节
138618  rax = ([hi+0xC0].end - [hi+0xC0].begin) >> 5
13861C  sete al                                 ; 长度必须相等
13863B  fabs(lo.list[0].v0 - hi.list[0].v0)     ; 元素 +8  = 第 2 个 double
138664  fabs(lo.list[i].v2 - hi.list[i].v2)     ; 元素 +0x18 = 第 4 个 double
        …… 两两循环比较，任一超过 0.005 即 `*out = 0`
```

⇒ `lo` 在 `+0xA8`、`hi` 在 `+0xC0` 各带一个 **`vector<Interval>`（元素 32 字节 = 4 个 double）**；
**两者长度必须相等**，且**逐元素的 `v0` 与 `v2` 必须在 0.005 内**，否则成本不适用。
（`0x134FF0` 的 bool 语义：`test dl,dl; cmove rax,rcx` ⇒ `dl!=0 → +0xA8`，`dl==0 → +0xC0`。）

**[未确认]**：上述 0.005 闸所比较的**具体字段对**（`[obj+0x18]`/`[obj+0x8]` 等）与
`obj[+0x10]` 的量纲命名；这两点需要把 `0x1380D0` 剩余的入口基本块读完。

### 8.6 仍然未译出的部分 **[未确认]**

`0x1380D0` 共 476 条指令：**主成本表达式已逐指令译出**（8.5）、
**两条前置条件已译出**（8.5b）、**组成原语已全部译出**（8.2–8.4）。
仍未逐条确认的只剩**命名性细节**：`obj[+0x10]` 阈值与 `out`/节点 value 的量纲命名、
以及 `0x1386D0`–`0x1386EE` 那条把 `[rsi+0x10]` 写进 `[rbx+8]` 的支路所对应的语义条件。
它们不影响主表达式的忠实移植。

### 8.7 已并入工程 **[已证实]**

| RE 地址 | 工程对应 | 测试 |
|---|---|---|
| `0x5C22D0` 定点角度 | `geom::angleToFixedDegrees` / `geom::kFullTurnFixedDegrees` | `test_exact`（0/45/90/180/270/315 度、回绕、0/90/180/270 的魔数） |
| `0x1380D0` 成本 | `row::squeezeCost` + `row::SqueezeContext` / `Interval` / `Slot` / `IntervalList` | `test_row`（公式、0.005 闸、1e-6 平行闸、零长度、各 bail 分支） |
| `0x134FA0` / `0x134FF0` | `row::Slot`（presence + 4 double）与 `row::IntervalList` 的选取语义 | `test_row` |
| `0x13A360` 记忆化 | `row::Squeezer::cost`（按 (lo,hi) 地址键、命中判据 `lo<=keyLo && hi<=keyHi`、未命中才求值并插回） | `test_row`（命中/未命中/不缓存"不适用"） |

> 结构替代（已明示）：原库用红黑树索引，本工程用同判据的线性扫描——树只是索引，
> 命中/未命中的判定不变。零长度方向在原库是 `assert(distance != 0)`（**中止**），
> 重建里改为 `present = false`（不中止），断言原文已记录于 8.5。

---

## 9. `Prc::` 定价器族：构造点与“默认变体” —— **本轮结案**

### 9.1 六个构造函数（**纠正一处旧标注**）**[已证实]**

`REPORT.md` §7.3 曾把 `0x4D64C0` 称做"定价器工厂"。实际读下来：

* `0x4D64C0`（2257 B）**主要是一段断言串构造器**（内部两次 `basic_string::_M_create`，
  拼出 `parts.size() == m_specifics.m_prices.size()` 之类的文本），它**同时**是组合定价器的装配点。
* 那 6 个 `lea` 到价目器 vtable **地址点**的位置**不在 `0x4D64C0` 内**
  （`0x4D64C0` 只到 `0x4D6D91`），而是分属**六个各自独立的小构造函数**：

| 函数 | 大小 | 装载的地址点 | 类 |
|---|---|---|---|
| `0x4D9AD0` | 40 B | `0xA3B0C0` | `Prc::BoxPriceComputer` |
| `0x4D9B00` | 40 B | `0xA3B100` | `Prc::HullPriceComputer` |
| `0x4D9B30` | 57 B | `0xA3B140` | `Prc::AlphaPriceComputer` |
| `0x4D9CD0` | 258 B | `0xA3B180` | `Prc::LinearCombinationPricer`（**无调用者**） |
| `0x4D9DE0` | 406 B | `0xA3B180` | `Prc::LinearCombinationPricer`（**无调用者**） |
| `0x4D9F80` | 757 B | `0xA3B180` | `Prc::LinearCombinationPricer`（被 `0x4D693D` 调用） |

每个都是 `operator new(N)` + 写 vtable + 填参数的内联构造，**因此不存在"C++ 构造函数被调用"的
`call` 点** —— 这正是 `findings_lp.md` §0 得出"四个定价器都没有构造函数被调用"的原因，
该行结论作废。 **[已证实]**

### 9.2 **没有"默认变体"：四个子定价器被同时构造并加权组合** **[已证实]**

`0x4D6890` 起是装配序列（逐指令）：

```
0x4D6898  xmm9 = obj[0x00]                       ; 权重 w0
0x4D68A8  call 0x4D9AD0            ; → BoxPriceComputer        (r15)
0x4D68B8  xmm8 = obj[0x08]                       ; 权重 w1
0x4D68BE  call 0x4D9B00            ; → HullPriceComputer       (r14)
0x4D68D3  xmm1 = [0x9D9C08]                      ; Alpha 参数 a1
0x4D68DE  xmm7 = obj[0x10]                       ; 权重 w2
0x4D68E3  call 0x4D9B30            ; → AlphaPriceComputer #1
0x4D68F5  xmm1 = [0x9D9BE8]                      ; Alpha 参数 a2
0x4D68FD  xmm6 = obj[0x18]                       ; 权重 w3
0x4D6907  call 0x4D9B30            ; → AlphaPriceComputer #2
0x4D6916..0x4D6937  把 (w2, #1, w1, Box, w0) 依次压栈，xmm2 = w3
0x4D693D  call 0x4D9F80            ; → LinearCombinationPricer(Box, Hull, Alpha1, Alpha2, w0..w3)
0x4D6942..0x4D6988  释放四个子定价器（虚调用 [vptr+8] = 删除型析构）
0x4D698B  xmm1 = obj[0x20]                       ; 权重 w4
0x4D6993  call 0x4D9B70
0x4D69A6  call 0x4DA720                          ; 汇总进结果对象
```

结合 `0x7CA370` 已证语义（`Σ wᵢ·priceᵢ / Σ wᵢ`，加权平均），结论是：

> **原库不"选一个默认定价器"，而是把 Box + Hull + Alpha×2 全部构造出来，
> 交给 `Prc::LinearCombinationPricer` 按权重加权平均；权重取自 `obj[+0] [+8] [+0x10] [+0x18]`
> （另有 `[+0x20]` 用于后续一步）。**

`obj` 是一个**5 个 double 的权重/系数结构**（`+0x00/+0x08/+0x10/+0x18/+0x20`，共 0x28 字节），
字段本身是 **[已证实]**。**[推断，依据充分]**：RTTI 里那三个"只有名字、无 typeinfo 对象"的
非多态型别 `Prc::SurfaceCoeffs` / `Prc::BoostAlpha` / `Prc::DimAlpha` 很可能就是这类系数结构
（名字与"面量系数 / alpha 权重"吻合，且"无 vtable"正好符合纯数据）。
**但把 `obj` 具体归到哪一个名字上尚无直接证据**，故该归属标 **[推断]**。

`0x9D9C08` / `0x9D9BE8` 两个 double 参数（传给两个 Alpha 实例）**未读出数值**（属 `rprice`
翻译单元的 rodata），标 **[未确认]**。

---

---

## 10. `CoinLP` 内部布局、slot 5/6/7 与 `0x7CA830` 的最终定性 **[已证实]**

### 10.1 成员布局：3 个并行 `vector<double>` + COO 三元组累加器

用"每个虚槽写入的成员偏移"作签名（脚本 `g_slot_offsets.py`）：

| 槽 | 函数 | 写入的成员偏移 | 含义 |
|---|---|---|---|
| 4 | `0x6792C0` | `[this+0x20]` `[this+0x38]` `[this+0x50]`（三个 vector 的 **end**） | 三个并行 `vector<double>`，begin 在 `+0x18` / `+0x30` / `+0x48` ⇒ **每列 3 个属性**（cost / lower / upper） |
| 5 | `0x679670` | end 在 `+0x68` `+0x80` `+0x98` | 另三个 vector，begin 在 `+0x60` / `+0x78` / `+0x90` |
| 6 | `0x679940` | 同上 | 同上 |
| 7 | `0x679420` | 同上 | 同上 |
| 3 | `0x679660` | `[this+0x10]` 一个字节 | 标志位 |
| 8 | `0x679D00` | 无（只读） | 提交 + 求解 |

### 10.2 `0x7CA830` 的最终定性：**先就地排序三元组，再渲染成文本** —— 两件事都做

```
7CA843  r15 = [rcx+0x98]        ; vector(+0x90) 的 end
7CA84A  rdi = [rcx+0x90]        ; ... 的 begin
7CA851  rbp = rdx               ; arg2
7CA857  r14d = r8d              ; arg3（0 或 1）
7CA85A  [rsp+0x2d8] = r9        ; arg4 = 输出 std::string
7CA894  call 0x267A30           ; = std::sort（introsort：0x10f 阈值 + 取中 + 自递归）
7CA8C0..7CA908                  ; 插入排序收尾，比较键 [rec+0xc] → [rec+8] → [rec]
7CA918  r15 = [rbx+0x90] ; rdx = [rbx+0x98]     ; 重新读回同一 vector
7CA926  rax = [rbx+0xa8]                        ; 下一个 vector(+0xa0) 的 end
……
7CAC6B 起：18 次 ostream 数值插入 + '   '（0x9C2DF2）分隔，写进 arg4 的 string
```

关键点：

* `std::sort` 作用在 **`this` 自己的成员 vector（`+0x90`）** 上 ⇒ **就地排序，是功能性副作用**，
  与输出 string 无关。元素 16 字节 `{double@+0, int@+8, int@+0xc}`，
  排序键 **(int@+0xc, int@+8, double@+0)** ⇒ 生成**按列优先的 COO 三元组**，
  正是 Clp `CoinPackedMatrix` 默认消费的顺序。
* 同一个函数**又**把数值以 3 空格分隔格式化进调用者给的 `std::string`（`slot 8` 传入后立即析构）。
* ⇒ 此前"装填进求解器 **还是** 格式化成文本"的二选一是**假二分**：它两者都做
  ——**把累加器规范化（排序）**＋**渲染成文本**。求解动作在 `slot 8`：
  `call 0x7CA830` → `call [solver_vt+0x00]` → `call [solver_vt+0x100]` → `xor esi,1`。

### 10.3 `slot 5/6/7`：同一个"追加三元组"例程的三个变体 **[已证实结构 / 参数含义 [推断]]**

规范化指令流比对（`g_slot_diff.py`，把寄存器抽象成 R、只保留助记符+操作数种类+显式位移）：

* **slot 5 vs slot 6：只有 4 处差异**（27 行 diff）
  1. 一个 `lea R,[RIP+...]` 常量（vtable/typeinfo 指针）不同；
  2. 一个 `movsd R,[RIP+...]` double 常量不同；
  3. 一个 `lea R,[RIP-0x2a5]` / `[RIP-0x575]` 不同 —— 两处都**指回 slot 7 那个函数体**，
     即作为断言的 `__func__` 之名 ⇒ **slot 7 是被共享的核心**；
  4. slot 6 比 slot 5 多**一条 `xorpd R,M[RIP+...]`**（对一个值取负）。
* **slot 5 vs slot 7**：slot 7 **缺少整个前导块**（`movaps [R+0x60]`、`lea` 指针常量、
  读 `[solver+0x220]`、两次 compare/jne 断言检查、两个 `movsd` 存储），并且
  **没有任何间接调用**；slot 5/6 各有两次间接调用（`call rax`、`call rbx`）。

⇒ 定性：**slot 7 = 裸的"追加一条三元组"核心；slot 5/6 = 核心 + 求解器配置前导 + 两次虚分派**；
**slot 6 = slot 5 再加一次取负**（与 `slot 4` 在 `dl==0` 时"读 `[solver+0x220]` 再 `xorpd` 取负"
是同一种模式）。
**[推断]**：这一对很可能就是"下界/上界"或"最小化/最大化"两个方向的同一操作（取负是符号翻转），
但**没有直接证据把 5/6 分配到具体语义**，故不写死。

### 10.4 已并入工程

| RE | 工程 |
|---|---|
| `slot 4` 写三个并行 `vector<double>` | `SimplexLinearProgram::columnCost_ / columnLower_ / columnUpper_`（注释标注 `+0x18/+0x30/+0x48`） |
| `slot 5/6/7` 写 `+0x60`/`+0x78`/`+0x90`；元素 16 字节 `{double,int,int}` | `rowRhs_`（`+0x60`）+ `coefficients_`（`+0x90`，`Triplet{value,row,column}`，注释解释 a/b 归属的依据） |
| `0x7CA830` 就地排序（键 `(int@+0xc, int@+8, double@+0)`） | `SimplexLinearProgram::canonicalise()`，在 `solve()` 一开始调用（`std::stable_sort`，键 `(column,row,value)`） |
| `slot 8` = 规范化 → 求解 → 取反返回 | `solve()` 先 `canonicalise()` 再建 `Simplex` |

---

## 11. 翻译单元归属、反射注册表、Alpha 常量与 `Row::` 接线 **[本轮新增]**

### 11.1 内联断言串的**正确**还原法（并撤销一种错误方法）**[已证实]**

`..\pricer\*` 与 `..\rprice\*` 的断言串是**内联构造**的（无 rodata 锚点），因此
**在 `.text` 段里用字符串表命中的"标识符"绝大多数是伪影**（代码字节里恰好出现的可打印串，
尾部常带半个操作码，如 `'coeffs >E1'`、`'boost >=H'`）。本轮据此**撤销**了所有基于
`.text` 内字符串命中的结论。

可靠做法：模拟 `movabs reg,imm` + `mov [mem],reg` 的**轻型数据流**，把立即数按写入偏移拼回。
用该方法解出的真实串：

| 函数 | 还原出的串 | 结论 |
|---|---|---|
| `0x4D64C0` | `..\pricer\prices_generator.c…` + `…rices.m_prices.size()` | 源文件 **`..\pricer\prices_generator.cpp`**；断言涉及 `m_prices.size()` |
| `0x4D97B0` | `..\pricer\price_computer.cpp` + `rface` | 源文件 **`..\pricer\price_computer.cpp`**，提到 "Surface" |
| `0x7CA370` | `..\pricer\price_computer.cpp`、`rice`、` 0.0` | `LinearCombinationPricer::slot2` 的 `> 0.0` 断言（与已证的 `Σwᵢpᵢ/Σwᵢ` 一致） |
| `0x4F0D00` | `..\tiling\torch_tools.cpp` | 该处的 `'oost < 1'` 属**割炬**代码，与定价器无关（避免误归属） |

### 11.2 三个"孤儿"类型名**并非无引用**：反射注册表 `0x6CC9D0` **[已证实]**

对 rodata 串（可靠）做引用扫描：

| 串 | 引用者 |
|---|---|
| `'AP '`（`0x9C1C92`） | **`0x220ED0`**（563 B） |
| `'AlphaSurfacePricer '`（`0x9C1C96`） | **`0x220ED0`** |
| `'DP '`（`0x9C1CAA`） | **`0x221110`**（579 B） |
| `'DimPricer '`（`0x9C1CAE`） | **`0x221110`** |
| `'static_cast<long long>(pricer.m_prices[p]) >= 0'`（`0x9C1CC0`） | **`0x222200`**（8173 B） |
| `N3Prc10BoostAlphaE`（`0xA22260`） | **`0x6CC9D0`**（18272 B） |
| `N3Prc13SurfaceCoeffsE`（`0xA222A0`） | **`0x6CC9D0`** |
| `N3Prc8DimAlphaE`（`0xA22340`） | **`0x6CC9D0`** |

⇒ 三个类型名**由 `0x6CC9D0` 引用**（三处：`0x6CCB6E` / `0x6CD080` / `0x6CD631`，每处都是
"`lea rdx,[名字串]` → `call 0x608E40` 建 string → `call 0x829B70(rcx,rdx,r8=-1,r9=1)`" 的同一模式）
⇒ 该函数是**名称注册/描述表**（反射式），这也正是"名字串存在却没有 typeinfo 对象"的原因。
**这推翻了此前"零引用"的说法**——那次搜的是"指向名字串的指针"，而这里是代码直接 `lea` 名字串本身。

**字段布局仍 [未确认]**：注册调用传入的 `rdx`（`0x9D9B66`）落在 `basic_string::substr`
断言串的中间，不是可读注解；无 typeinfo、无 vtable、无成员名字串。

### 11.3 Alpha 常量 **[数值已证实 / 归属 [推断]]**

`0x4D68D3` 与 `0x4D68F5` 把两个 rodata double 传给两个 `AlphaPriceComputer` 实例：

* `0x9D9C08` = **0.5**
* `0x9D9BE8` = **0.1**

**[推断，依据充分]**：这两个值就是 `Prc::BoostAlpha` 与 `Prc::DimAlpha`（两个单 double 参数，
分别对应两个 alpha 定价变体；`'AP '`/`'DP '` 是它们的日志短标签）。**具体哪一个对应 0.5、
哪一个对应 0.1 无直接证据，不写死。**
**[推断]**：5 个 double 的系数块（`obj[+0x00..+0x20]`，见 §9.2）最可能是 `Prc::SurfaceCoeffs`，
同样无 typeinfo 可证。

### 11.4 `Row::` 的接线：`Squeezer` **可达**，`BasicDistancer` **未构造** **[已证实]**

```
多态虚表的装载点：
  BasicDistancer: 0x136AE0 (57 B)                        <- 无任何调用者
  Squeezer      : 0x138A20 (446 B) / 0x138D60 (437 B)     构造
                  0x138BE0 (185 B) / 0x138CA0 (191 B)     D1/D0 析构

可达链（自引擎向下）：
  AdvancedStrategist::operator()  0x2DF60 (481 B)
    -> 级联 0x2CCF0 (264 B)  -> 0x2D220 (264 B)
    -> StrategyAdder::Add 0x2C4D0 (2072 B)
       -> 0x8F210 (116 B)
          -> 0x6AABC0 (5763 B)                 ; 策略体（0x6Axxxx = 数据库/策略层）
             -> 0x13C380 (416 B)   @0x6AC10C
             -> 0x134470 (572 B)   @0x6AB72E
                -> 0x133DE0 (1458 B) @0x133EF7
             -> 0x136B80 (99 B)                   ; 真正的构造函数
                -> Row::Squeezer
```

⇒ **`Row::Squeezer`（行挤压代价 + 区间记忆化）在引擎的策略分派链上是活的**；
**`Row::BasicDistancer` 是死代码**（构造器无调用者）。

> 与 `findings_lp.md` §6"整套 `Row::` 未接线"的说法**部分矛盾**：那次的"0 引用"来自按
> **vtable 头部**地址扫描（应为地址点）；纠正后必须分开说 —— `Squeezer` 可达、
> `BasicDistancer` 不可达。

---

## 12. `Row::` 对象图与挤压器的构造路径 **[本轮新增，已证实]**

### 12.1 `Row::Squeezer` 的构造器 `0x138A20`（446 B / 97 条）逐指令

```
138A20  Row::Squeezer**(out = rcx, xmm1, xmm2, xmm3)
138A34  lea rax,[rip+0x9027B5] -> 0xA3B1F0 ; 装入 vtable 地址点
138A3B  [rcx] = rax                        ; 外层对象的 +0
138A41  ecx = 0x270 ; call operator new    ; inner = 624 字节
138A6B  inner[+8]    = 1                   ; ★ 这就是 0x1380D0 里 `cmp byte [rdx+8],0` 测的标志
138A72  inner[+0x00] = xmm2
138A79  inner[+0x10] = xmm3                ; ★ 这就是成本公式里的阈值 obj[+0x10]
138A7E  call 0x500710(inner+0x20)          ; 构造子对象 A
138A8F  xmm7 = xmm1 + xmm1                 ; = 2 * xmm1
138A9A  call 0x2530D0(inner+0x28, xmm7, xmm2)   ; 构造子对象 B（+0x28..+0x20F，0x1E8 字节）
138AAF  inner[+0x18] = <由 1 字符串 "s" 经 0x4FFC10 得到>
138AC4  inner[+0x228] = inner+0x218 ; inner[+0x230] = inner+0x218   ; 树 A 头（自指哨兵）
138ADA  inner[+0x258] = inner+0x248 ; inner[+0x260] = inner+0x248   ; 树 B 头（自指哨兵）
        inner[+0x218]=0 [+0x220]=0 [+0x238]=0  [+0x248]=0 [+0x250]=0 [+0x268]=0
138B5C  [out+8] = inner                     ; 外层 = {vptr@0, inner*@8}
        （异常路径 0x923B00 析构 `+0x210` 的树 —— 与 0x13A360 的 `[rdi+0x240]` 插入点对应）
```

⇒ **对象图**：

```
Row::Squeezer 外层 (16 B):  [+0x00] vptr = 0xA3B1F0   [+0x08] inner*
inner (0x270 = 624 B):
    [+0x00] double (xmm2, 传给 0x2530D0)
    [+0x08] bool = 1              ← 0x1380D0 的开关
    [+0x10] double = xmm3         ← 成本公式的阈值
    [+0x18] void*（由 "s" 构造）
    [+0x20] 子对象 A（0x500710 构造）
    [+0x28] 子对象 B（0x2530D0 构造，含 +0x48/+0x70 两个槽与 +0xA8/+0xC0 两个区间表）
    [+0x210]/[+0x240] 两棵红黑树头
```

**构造器签名**：`Squeezer**(out, double xmm1, double xmm2, double xmm3)`。

### 12.2 `0x13C380`（416 B / 101 条）：行集 → 挤压器 **[已证实]**

```
13C380(rcx = out, rdx = rbp = 行容器 {begin@+0, end@+8}, r8 = rdi = 配置对象)
13C3A9  ecx = 0xA10 ; call operator new        ; 外层 2576 字节
13C3BF  wrapper[+0x00] = rbp                   ; 存行容器
13C3C5..13C406  从 rdi 逐 8 字节拷贝 9 个 qword 到 wrapper[+8 .. +0x38]（0x48 字节配置）
13C3B9  xmm9 = [rdi+0x10]                      ; → 稍后作 xmm3
13C3C8  xmm8 = [rdi+0x18]                      ; → 稍后作 xmm2
13C413  xmm7 = 0 ; 13C41C xmm6 = xmm7          ; 累值初值 0
循环（13C420 起，13C473 `jne` 回跳）:
13C420  rcx = [rdi] ; call 0x133190
13C42E  call 0x5CD800(rcx = r12, rdx = rax)    ; 产出 [rsp+0x20] 一个 bool +
                                               ;     [rsp+0x28] [rsp+0x30] [rsp+0x38] [rsp+0x40] 四个 double
13C433  cmp byte [rsp+0x20], 0
13C438  xmm1 = 0                               ; ★ 先把本轮贡献置 0（在分支之前）
13C43C  jne 0x13C464                           ; 有效行 → 跳过算术，贡献保持 0
13C43E  xmm1 = [rsp+0x40] ; 13C44A xmm1 -= [rsp+0x30]     ; d0 = v3 - v1
13C444  xmm0 = [rsp+0x38] ; 13C450 xmm0 -= [rsp+0x28]     ; d1 = v2 - v0
13C456  ucomisd xmm1, xmm0
13C45A  jbe 0x13C4FF → 13C4FF addsd xmm0,xmm0 ; 13C503 xmm1 = xmm0
13C460  （否则）addsd xmm1, xmm1
13C46F  movapd xmm6, xmm1                      ; ★ 赋值，不是取最大！
13C479  xmm3 = xmm9 ; 13C47E xmm2 = xmm8
13C483  call 0x136B80(&squeezer, xmm6, xmm8, xmm9)
13C488  wrapper[+0x48] = 1
13C4A0..13C4B8  循环 rdx = 1..0x26F：wrapper[rdx*4 + 0x48] = 1   ; int[0x270] 全填 1
13C4C1  [rsi] = wrapper
```

**三处容易想当然、必须按指令写的地方**：

1. `xmm6 = xmm1` 是**赋值**，不是取最大 ⇒ 最终值等于**最后一行**的贡献；
2. "有效"行（`[rsp+0x20] != 0`）的贡献是 **0**（因为 `13C438` 在分支前就把 `xmm1` 置 0），
   而不是"保持上一轮的值"；
3. 差值**不取绝对值**：`13C456` 之后就是 `addsd` 加倍，全程没有 `andpd`/`fabs`
   ⇒ 是**带符号的 max**，负值会原样翻倍。

### 12.3 已并入工程 **[已证实]**

| RE | 工程 |
|---|---|
| `0x138A20` 的三处标量存储（`+8`=1、`+0`=xmm2、`+0x10`=xmm3）与 `2*xmm1` | `row::Squeezer(double twiceMaxExtent, double coeffAt0x18, double thresholdAt0x10)` + `enabled()/coeff()/threshold()/twiceMaxExtent()` |
| `0x13C380` 的循环、置 0、带符号 max、`addsd` 加倍、`call 0x136B80` | `row::buildSqueezer(rows, configAt0x10, configAt0x18)`（`RowView{valid, v[4]}` 对应 `0x5CD800` 的产出形状） |
| 上述三条易错语义 | `test_row` 各有一条断言专门钉住（赋值不是最大、有效行归 0、负值不取绝对值） |

### 12.4 仍未确认

* `0x5CD800` 的**内部语义**（它产出「1 个 bool + 4 个 double」——本工程按 `RowView` 建模形状，
  未译其算法）。
* 行容器元素的**型别**与 `0x133190` 的作用。
* 策略体 `0x6AABC0` 里对 `0x13C380` / `0x134470` 的**调用位置**（两者相隔 0x9DE 字节，
  且 `0x134470` 走的是 `0x8BEFC0`/`0x5EC370` 一套，与 `0x13C380` 不同）——
  **因此尚未把 `row::Squeezer` 接到 nester 的某个具体策略上**；原库的接线点是策略体内部，
  其策略**身份（对应哪个导出）未确认**。

---

## 13. 策略身份与 `row::Squeezer` 的**接线点** **[本轮新增，已证实]**

### 13.1 用内联串还原定出三个翻译单元

沿用 §11.1 的可靠方法（模拟 `movabs reg,imm` + `mov [mem],reg`）：

| 函数 | 还原出的串 | 结论 |
|---|---|---|
| `0x6AABC0`（5763 B / 1218 条） | `..\multi\row_nester.sh…` + `…pet.nesting_origin…` + `…&& "incompatible origin` | 源文件 **`..\multi\row_nester.cpp`** ⇒ 策略体身份 = **行排样器**（断言涉 `nesting_origin`） |
| `0x1380D0`（成本例程） | `..\row\squeezer.t…` | 源文件 **`..\row\squeezer.cpp`**（`Row::` 层在**自己的目录** `..\row\` 下） |
| `0x5CD800`（610 B / 145 条） | `..\geom\properties.c…` | 源文件 **`..\geom\properties.cpp`** ⇒ 它是**几何属性访问器**（产出 1 个 bool + 4 个 double） |

`0x5CD800` 的"bool + 四个 double"与"极值"语义、以及 `0x13C380` 对它取的
`2·max(v3−v1, v2−v0)`（两倍较大边长）合起来，最合理的读法是**包围盒 + 一个可用性/轴对齐标志**；
**[未确认]** 的是该标志的确切含义（未译 `0x5CD800` 内部）。

### 13.2 接线点：Squeezer 存在 `RowNester::this+0xC0` **[已证实]**

`0x6AABC0` 内 `0x6AC10C` 那次调用的实参：

```
6AC0F3  ecx = 8 ; call operator new        ; 8 字节持有器
6AC0FD  rdx = [rsp+0x58]                   ; 行容器
6AC102  r8  = rbp + 8                      ; ★ 配置对象 = this + 8（0x48 字节）
6AC106  rcx = rax                          ; out
6AC10C  call 0x13C380                      ; 构造 Row::Squeezer
6AC111  rbx = [rbp+0xC0]                   ; 旧挤压器
6AC118  [rbp+0xC0] = rsi                   ; ★ 新的存到 this+0xC0
6AC124  call 0x13C520 ; call operator delete   ; 析构旧挤压器
```

以及 `0x6AB72E` 对 `0x134470` 的调用同样把 `r9 = rbp + 8`（`0x134470` 是**另一套**下游：
`0x8BEFC0`/`0x5EC370`，并按 `[rbp+0x40]` 的 0/1/3 分派）。

`0x6AABC0` 内的模型访问也印证了它是排样器：`0x4FC940 GetSheet`、`0x4FC5A0`、
`0x4FC5B0 GetPart`、`0x4F7690`。

**由配置块在 `this+8` 推出字段映射**（这是 `0x13C380` 里
`xmm9 = cfg[+0x10]`、`xmm8 = cfg[+0x18]` 的直接后果）：

| `0x13C380` 读的 | 即 `RowNester` 的 | 用途 |
|---|---|---|
| `cfg[+0x10]` (xmm9) | **`this+0x18`** | `Row::Squeezer` 构造器的第 3 参 ⇒ inner`[+0x10]` = **成本公式的阈值** |
| `cfg[+0x18]` (xmm8) | **`this+0x20`** | 构造器第 2 参 ⇒ inner`[+0]` = 系数 |

### 13.3 已并入工程 **[已证实]**

| RE | 工程 |
|---|---|
| `0x6AABC0` = `..\multi\row_nester.cpp` 的策略体 | `RowNester::run`（`lcns/src/nester.cpp`），注释引用 `0x6AABC0` 与整个调用窗口 |
| Squeezer 存于 `this+0xC0`，旧对象析构 | `RowNester::squeezer_` + `hasSqueezer()` |
| 配置块 `this+8`，`this+0x18`/`this+0x20` 两个标量 | `RowNester::setRowConfig(at0x18, at0x20)` / `cfg18()` / `cfg20()`；**不编造默认常量**，默认 0 并注明来源未追 |
| 行元素来自 `..\geom\properties.cpp` 的 `0x5CD800` | 以 `placedShape(...)` + `geom::bounds(...)` 取每个已放零件的包围盒填入 `row::RowView` |
| `0x13C380(rows, this+8)` → `buildSqueezer` | `squeezer_ = row::buildSqueezer(rows, cfg18_, cfg20_)` |
| 上述映射 | `test_nester` 断言 `hasSqueezer()`、`enabled()`、`threshold()==cfg18_`、`coeff()==cfg20_` |

### 13.4 仍未确认

1. `RowNester::this+0x18` / `this+0x20` 这两个 double 的**来源**（哪个配置项或哪个 `SetXxx`
   导出写入）—— 工程里作为参数暴露，**不填造常量**。
2. `0x5CD800` 的**内部算法**与其 bool 标志的含义（工程按"每个元素都走 `2·max` 那条分支"接线，
   已在代码注释中标明）。
3. 行容器的**元素型别**（`0x13C380` 用 `13C420 rcx = [rdi]` + `call 0x133190`（5 字节，仅 2 条指令）
   取元素）。
4. `0x134470` 那一路（另一套下游）的用途。

### 13.5 **更正 §13.2/§13.3：上轮把接线放错了类** **[本轮，已证实]**

上一轮据 `0x6AC118 [rbp+0xC0] = rsi` 判定"Squeezer 存在 `RowNester::this+0xC0`"，
并据此把 `buildSqueezer` 放进了 `RowNester::run`。本轮把**地址点的 RTTI 名字**解出来后发现
该判定是错的。

**(a) 地址点的 RTTI 名字**（Itanium ABI：`vtable = AP - 0x10`，typeinfo 指针在 `AP - 8`：

| 地址点 | typeinfo RVA | 名字 RVA | 解出的类名 |
|---|---|---|---|
| `0xA3BB40` | `0xA18390` | `0xA22940` | **`N5Multi9RowNesterE`** = `Multi::RowNester` |
| `0xA3BB10` / `0xA3BB00` | `0xA18380` | `0xA22930` | `N5Multi6NesterE` = `Multi::Nester`（基类） |
| `0xA3B0C0` | `0xA17D60` | `0xA222C0` | `N3Prc16BoxPriceComputerE` |
| `0xA3B100` | `0xA17D80` | `0xA222E0` | `N3Prc17HullPriceComputerE` |
| `0xA3B140` | `0xA17DA0` | `0xA22300` | `N3Prc18AlphaPriceComputerE` |
| `0xA3B180` | `0xA17DC0` | `0xA22320` | `N3Prc23LinearCombinationPricerE` |

（后四个**独立印证了** §9.1 的四个定价器归属；`Row::Squeezer` `0xA3B1F0` 与 `Coin::CoinLP`
`0xA3B280` 在该偏移下解不出，属"表窗口不同"，不影响已知结论。）

**(b) `0x8F210` 是 `Multi::RowNester` 的构造函数，不是策略体**：

```
8F210(rcx = out, rdx, r8d = pipe)
8F221  call 0xB4470                     ; 基类 Multi::Nester 构造
8F226  lea rax,[rip+0x9AC913] -> 0xA3BB40
8F230  [rbx] = rax                      ; 装入 Multi::RowNester 的 vtable
8F238  ecx = 0xD0 ; call operator new   ; ★ 208 字节的 core
8F252  call 0x6AABC0(core, rdx, r8d=pipe)   ; ★ 填充 core
8F257  [rbx+0x18] = rsi                 ; ★ Multi::RowNester::+0x18 = core*
```

`0x6AABC0` 的**唯一调用者就是这个构造函数**；而 `Multi::RowNester::Run`
（vtable 槽 5 = `0x913E0`，12380 B）的直接被调表里**没有** `0x6AABC0`
（它调的是 `0x13C560`/`0x13EB20`/`0x679070`/`0x7C1CF0`/`0x63F2F0`/`0x63F2F8` 等）。

⇒ `0x6AABC0` = **208 字节 core 对象的构造函数/初始化**，其 `this` 是 core，**不是** `Multi::RowNester`。
所以 §13.2 表格里那三个偏移的正确归属是：

| 偏移 | 归属 |
|---|---|
| `+0x08 .. +0x50` | **core 的配置块**（作为第三参交给 `0x13C380`） |
| `+0x18` | core 的 double == `cfg[+0x10]` ⇒ Squeezer 的**成本阈值** |
| `+0x20` | core 的 double == `cfg[+0x18]` ⇒ 系数 |
| `+0x40` | core 的 mode（`0x6AB6B5`/`0x6AB6C0`/`0x6AB6C9` 与 0/1/3 比较） |
| `+0xC0` | core 的 `Row::Squeezer*`（`0x6AC118` 写入，旧对象 `0x6AC124` 析构） |

**(c) 工程已按此更正**（`lcns`）：

* 新增 `RowNestCore`（对应那个 208 字节 core，构造点 `0x6AABC0`）：持有
  `threshold_`(`+0x18`)、`coeff_`(`+0x20`)、`mode_`(`+0x40`)、`squeezer_`(`+0xC0`)，
  构造时按 `0x13C380` 的路径 `row::buildSqueezer(rows, threshold_, coeff_)`。
* `RowNester` 改为持有 `std::unique_ptr<RowNestCore> core_`（对应 `this+0x18`），
  `squeezer`/`cfg` 的直接成员**已移除**。
* **已知偏离（明示）**：二进制在 `Multi::RowNester` **构造函数**里就把 core 建好
  （因为它的构造函数已经拿到问题对象）；本工程的 `makeStrategy()` 此时还没有 `Order`，
  故 core 在**首次 `run()`** 时构建。**结构（`RowNester` 持 `+0x18` 的 core、core 持 `+0xC0`
  的挤压器）保持不变**，只有构建时机不同。
* 行元素取自 `Part::rawShape` 的包围盒（`0x6AABC0` 调 `0x4FC5B0 GetPart` 表明它用的是
  **问题几何**，不是已放零件）；**[未确认]** 它到底取哪些零件、以及 `0x5CD800` 的标志含义。
* `test_nester` 断言：`core()` 首次为 `nullptr`、`run()` 后非空且**只建一次**、
  `threshold()==cfg18_`、`coeff()==cfg20_`、`squeezer().threshold()==cfg18_`、
  `coloeff` 对应、`mode()==0`、`rowCount()==order.parts.size()`。

---

## 14. core 配置的来源与 `0x5CD800` 的产出结构 **[本轮新增，已证实]**

### 14.1 两个配置 double 的来源 —— **结案**

`0x6AABC0`（core 的初始化函数）开头**先把 core 的字段写成 rodata 常量**：

```
6AABDB  pxor xmm6, xmm6
6AABDF  xmm2 = [0x9B1A40] = 10.0
6AABE7  xmm3 = [0x9B1A48] =  4.0
6AABEF  xmm4 = [0x9B1A50] = 20.0
6AAC05  core[+0x00] = pipe          (byte)
6AAC09  core[+0x08] = xmm2          = 10.0
6AAC0E  core[+0x10] = xmm6          = 0
6AAC13  core[+0x18] = xmm3          =  4.0   ★ 阈值默认值
6AAC18  core[+0x20] = xmm4          = 20.0   ★ 系数默认值
6AAC1D  core[+0x28] = 0 ; 6AAC21 core[+0x30] = 0 ; 6AAC26 core[+0x38] = 0
6AAC8E  core[+0x40] = 0             (mode)
```

随后**可能被问题对象覆盖**：

```
6AAC2A  call 0x4FC2F0(arg)   ; = `mov rax,[rcx] ; movzx eax,byte [rax+0x170]`
6AAC3A  test al,al ; jne 0x6AC20A          ; 该位置位则跳到另一条路径
6AAC42  call 0x4FC300(arg)   ; = `mov rax,[rcx] ; movzx eax,byte [rax+0x1A0]`
6AAC49  je 0x6AAC82                        ; 未置位则保留默认值
6AAC53  call 0x4FC3C0(arg)   ; = `mov rax,[rcx] ; add rax,0x1A0`
6AAC5D  core[+0x20] = [rax+0x08]           ; == problem + 0x1A8
6AAC6B  core[+0x18] = [rax+0x10]           ; == problem + 0x1B0   ★ 覆盖后的阈值
6AAC62  core[+0x28] = (byte)[rax+0x18]     ; == problem + 0x1B8
6AAC75  core[+0x30] = [rax+0x20]           ; == problem + 0x1C0
```

（`arg` 由 `0x8F210` 给出：`0x8F233 call 0x30260`，而
`0x30260 = mov rax,[rcx+8] ; mov rax,[rax+0x18] ; ret`，即 `ctorArg2[+8][+0x18]`。）

⇒ **默认值 = `0x9B1A48 = 4.0`（阈值）、`0x9B1A50 = 20.0`（系数）、`0x9B1A40 = 10.0`（`core+8`）；
覆盖来源 = 问题对象的 `+0x1B0` / `+0x1A8`，gate 为 `+0x170` 与 `+0x1A0` 两个字节。**
（另有 `0x9B1A58 = 4.9999999999999996e-06` ≈ 5e-6，同簇常量。）

### 14.2 `0x5CD800` 的产出结构 = **包围盒**，且元素步长为 0x30 **[已证实]**

`0x5CD800` 的**签名与形状**（不是"逐元素返回 bool + 4 double"）：

```
5CD80D  rdi = rcx                  ; arg1 = out
5CD810  rcx = rdx ; rbx = rdx      ; arg2 = 容器
5CD816  call 0x5C61D0(arg2)        ; -> {begin@+0, end@+8}
5CD81F  if (begin == end) -> 0x5CD8A0   ; 空容器 -> 内联断言串路径
5CD824  ... 遍历：
5CD831  rcx = [rax]                            ; 取首元素
5CD834  call 0x5C5F30 = `mov rax,rcx ; ret`    ; 恒等
5CD83C  call 0x5C5260 = `mov rax,rcx ; ret`    ; 恒等
5CD847  call 0x5CD360(out, that)               ; 把该元素的盒并入 out
5CD863  add rbx, 0x30                          ; ★ 元素步长 = 0x30 = 48 字节
5CD87F  call 0x5C8C50(out, rsp+0x70)           ; 再并入一个盒
5CD88F  rax = rdi ; ret                        ; ★ 返回 out
```

`0x5C8C50` 暴露了 out 的**字段语义**：

```
5C8C50  cmp byte [rdx],0 ; je 0x5C8C60 ; ret   ; 源盒的标志非 0 ⇒ 直接返回（跳过）
5C8C69  xmm0 = [rdx+8] ; xmm1 = [rcx+8] ; if (xmm1 > xmm0) [rcx+8] = xmm0
5C8C88  if ([rcx+0x18] < xmm0) [rcx+0x18] = xmm0
5C8C94  xmm0 = [rdx+0x10] ; ...
```

⇒ out = `{ bool @+0 ; minX @+8 ; minY @+0x10 ; maxX @+0x18 ; maxY @+0x20 }`，
共 **0x28 = 40 字节**，正是 `0x13C380` 在 `[rsp+0x20]` 读的那个对象
（`r12 = rsp+0x20`，与 `0x5CD800` 的 `rax = rdi` 返回值一致）。

于是 `0x13C380` 的算术语义完全落地：

```
13C43E  xmm1 = [rsp+0x40] - [rsp+0x30]   = maxY - minY = 高
13C444  xmm0 = [rsp+0x38] - [rsp+0x28]   = maxX - minX = 宽
13C460  把较大者 `addsd` 加倍            = 2 * max(宽, 高)
```

**标志的极性**：两处使用都是"**非 0 即跳过**"（`0x5C8C50` 的提前返回；`0x13C380` 的
`jne 0x13C464`）。所以工程里该字段的正确命名是"**skip**"而不是"valid"
（我上一轮叫它 `valid` 并把语义写成"是可测量的"——极性是反的，本轮已改名 `skipExtent`）。

其它小助手：`0x133190 = lea rax,[rcx+8] ; ret`（取元素的 `+8` 子对象）；
`0x5C5F30` 与 `0x5C5260` 都是恒等 `mov rax,rcx; ret`。

**另注**：core 自己也调了一次 `0x5CD800`（`0x6ABBE3`），与 `0x13C380` 那次（`0x6AC10C` 内部）
是两处独立使用。

### 14.3 已并入工程 **[已证实]**

| RE | 工程 |
|---|---|
| rodata 默认值 `0x9B1A40/48/50` | `kRowCoreAt0x08 = 10.0` / `kRowCoreAt0x18 = 4.0` / `kRowCoreAt0x20 = 20.0`，`RowNester::cfg18_/cfg20_` 的默认值改为这两个**真常量**（不再是 0.0 占位） |
| 覆盖路径 `problem+0x1B0` / `+0x1A8` | **未建模**（本工程的 `Order` 没有 `Pb+0x1A8/+0x1B0` 对应字段）；两个值仍作为参数暴露，注释写明来源与 gate |
| out = `{bool, minX, minY, maxX, maxY}` | `row::RowView` 字段顺序与语义已按 `0x5C8C50` 校正；`v = [minX, minY, maxX, maxY]` |
| 标志极性"非 0 即跳过" | `RowView::skipExtent`（由 `valid` 改名，注释给出两处证据） |
| 元素步长 `0x30` | 记录（工程不建该容器；见 §14.4） |

### 14.4 仍未确认

* 容器的**元素型别**（只知道步长 `0x30 = 48` 字节，且元素 `+8` 处是一个子对象）。
* `0x5C61D0` / `0x5CD360` 的内部（后者是把一个盒并入累加器的 552 字节例程）。
* gate `problem+0x170` 置位时跳去的 `0x6AC20A` 那条路径。
* `0x134470` 那一路的用途。

---

## 15. 配置字段的**写入者**：两个命名导出 **[本轮新增，已证实]**

### 15.1 `Pb+0x170` ← 导出 **`SetPipeMode`**（`0xFCF0`，568 B）

```
FCF0   SetPipeMode(...)
FD25   rsi = rcx                    ; Pb*
FD28   ebp = edx                    ; the mode argument
...
FEBB   rax = [rsp+0x68] ; FEC0 [rsi+0x160] = rax
FEC7   rax = [rsp+0x70] ; FECC [rsi+0x168] = rax
FED3   rax = [rsp+0x78] ; FED8 [rsi+0x170] = rax      ★ 本行正是那个 gate 字节所在的 qword
FEDF   rax = [rsp+0x80] ; ...        [rsi+0x178] = rax
```

**宽度看似不符**（写 qword、`0x4FC2F0` 读 byte）的原因查清了：该导出是**整块结构拷贝**
（把栈上 `[rsp+0x68]` 起的连续 qword 拷进 `Pb+0x160…`），所以 `+0x170` 处的**字节**就是
被拷贝字段的低字节 —— 与 `0x4FC2F0` 的 `movzx eax, byte [rax+0x170]` 相容。

⇒ **`0x6AAC2A` 的那个 gate 就是 pipe mode**；这也解释了 `Multi::RowNester(pipe)` 的语义
（`0x8F210` 的 `r8d` 与 core 的 `core[+0] = pipe` 同源）。

### 15.2 `Pb+0x1A0 … +0x1C0` ← 导出 **`SetCommonCutParameters`**（`0x3C3F0`，1517 B）

```
3C3F0   SetCommonCutParameters(...)
3C40B   rbx = rcx                   ; Pb*
3C41A   call 0x4FC380
3C513   [rbx+0x190] = rax ; 3C522 [rbx+0x198] = rax
3C531   [rbx+0x1a0] = rax            ★ gate 字节（0x4FC300 / 0x4FC3C0 的基址）
3C540   [rbx+0x1a8] = rax            ★ → core+0x20（系数）
3C54F   [rbx+0x1b0] = rax            ★ → core+0x18（阈值）
3C55E   [rbx+0x1b8] = rax            ★ → core+0x28
3C56D   [rbx+0x1c0] = rax            ★ → core+0x30
```

同样是整块拷贝，因此"byte 读 / qword 写"相容。

**结论**：`Multi::RowNester` 那个 core 的配置来源是
**pipe 模式**（`SetPipeMode`）与**共边切割参数块**（`SetCommonCutParameters`），
两者都是**命名导出**。

### 15.3 已并入工程：把这条优先级真正实现 **[已证实]**

`Order`（`lcns/include/lcns/model.hpp`）新增字段并标注偏移：
`commonCutBlockSet`(`+0x1A0`)、`commonCutAt1A8`、`commonCutAt1B0`、`commonCutAt1B8`、
`commonCutAt1C0`；`pipeMode` 字段**工程里原本就有**（`+0x158..+0x178` 块），
本轮补注了"`0x4FC2F0` 读的就是 `Pb+0x170`"这条证据 —— 这也是对该字段归属的**独立印证**。

`RowNestCore` 的构造函数按 `0x6AABC0` 的**真实次序**实现优先级：

```cpp
threshold_ = configAt0x18;   // rodata 默认 4.0
coeff_     = configAt0x20;   // rodata 默认 20.0
if (!(pipe || order.pipeMode) && order.commonCutBlockSet) {   // RE: 0x6AAC3A 先于 0x6AAC42
    coeff_     = order.commonCutAt1A8;   // RE: 0x6AAC5D
    threshold_ = order.commonCutAt1B0;   // RE: 0x6AAC6B
}
```

`test_nester` 用三条用例分别钉住：**默认值**、**共边块存在时被覆盖**、
**pipe 模式开启时跳过覆盖**（`pipe` 参数与 `order.pipeMode` 两种入口都测）。

### 15.4 仍未确认

* `SetPipeMode` / `SetCommonCutParameters` 各自参数块里**哪一个 qword** 对应哪个语义
  （本轮只确定了"字节位置与读者相容"，未逐一配对）。
* `core+0x28`（`Pb+0x1B8`）与 `core+0x30`（`Pb+0x1C0`）的用途（已建模为字段，
  但**未接进任何算法**）。
* gate `problem+0x170` 置位时跳去的 `0x6AC20A` 路径做了什么。
* 容器元素型别、`0x5C61D0`/`0x5CD360` 内部、`0x134470` 那一路。

---

## 16. pipe 分支的实体、容器身份 **[本轮新增，已证实]**，并**更正 §15.3 的一处实现**

### 16.1 **更正**：pipe 模式不是"保留默认值"，而是**另一个配置来源**

上一轮我把 `0x6AAC3A` 的 `jne 0x6AC20A` 读成"pipe 模式 => 保留 rodata 默认、跳过覆盖"。
本轮把 `0x6AC20A` 读出来，事实是**它自己就是一条覆盖路径**：

```
6AC20A  call 0x4FC3A0(arg)                    ; = `mov rax,[rcx] ; add rax,0x170`（已核实：3 条指令）
6AC20F  xmm0 = [rax+0x08] ; core[+0x08] = xmm0    == Pb+0x178
6AC219  xmm0 = [rax+0x10] ; core[+0x10] = xmm0    == Pb+0x180
6AC223  xmm0 = [rax+0x18] ; core[+0x20] = xmm0    == Pb+0x188   ★ 系数
6AC22D  xmm0 = [rax+0x20] ; core[+0x18] = xmm0    == Pb+0x190   ★ 阈值
6AC232  al   = byte [rax+0x28]
6AC236  core[+0x18] = xmm0 ; 6AC23B core[+0x38] = al   == Pb+0x198
6AC23E  jmp 0x6AAC82
```

⇒ **两条互斥来源**：

| 条件 | 阈值 `core+0x18` | 系数 `core+0x20` |
|---|---|---|
| pipe 闸（`Pb+0x170`）置位 | **`Pb+0x190`**（`0x6AC22D`） | **`Pb+0x188`**（`0x6AC223`） |
| pipe 闸清零 且 共边闸（`Pb+0x1A0`）置位 | `Pb+0x1B0`（`0x6AAC6B`） | `Pb+0x1A8`（`0x6AAC5D`） |
| 两个闸都不满足 | rodata `0x9B1A48 = 4.0` | rodata `0x9B1A50 = 20.0` |

工程已按此改正（`RowNestCore` 的 `if (pipe) {...} else if (commonCutBlockSet) {...}`），
`Order` 补 `pipeAt178/pipeAt180/pipeAt188/pipeAt190/pipeAt198`，
`test_nester` 相应改为断言**两条来源各自的取值** + "pipe 优先于共边块"（`0x6AAC3A` 在 `0x6AAC42` 之前）。

### 16.2 相邻函数 `0x6AC250` 属**另一个类**，不是 core

`0x6AC250` 的 `lea rax,[rip+0x38F921]` → 地址点 `0xA3BB80`，RTTI 解出
**`N5Multi9SplitNodeE`** = `Multi::SplitNode`（`0xA3BB90` 同）。
它是在 `[rcx+0x38]..[rcx+0x40]` 上做引用计数释放（`lock sub dword [rbx+8],1` + 虚调用
`[rax+0x10]`/`[rax+0x18]`）的析构例程。**因此 208 字节的 core 自己没有 vtable**
（带 vtable 的是外层 `Multi::RowNester`，地址点 `0xA3BB40`）。

### 16.3 那个"行容器"就是 **core 自己的 `std::vector`（`core+0x48`）** **[已证实]**

`0x6AABC0` 在调 `0x13C380` 之前把容器地址存进 `[rsp+0x58]`：

```
6AAC82  rax = rbp + 0x48
6AAC95  [rsp + 0x58] = rax          ★ 容器 = core + 0x48
6AAC9A  rax = rbp + 0x60 ; 6AAC9E [rsp+0x68] = rax
6AACA3  rax = rbp + 0x78 ; 6AACA7 [rsp+0x70] = rax
6AACAC  rax = rbp + 0x98
6AACB3  qword [rbp+0x48] = 0 ; 6AACBB [rbp+0x50] = 0 ; 6AACC3 [rbp+0x58] = 0
```

`begin/end/cap` 三连清零 ⇒ **`core+0x48` 是一个空的 `std::vector`**，正是
`0x13C380` 的 `rdx`（其 `{begin@+0, end@+8}` 由 `0x5C61D0` 取出）。

**元素形状**：步长 **0x30 = 48 字节**（`0x13C380` 的 `add rbx,0x30`）。
元素被取用时是 `rcx = [rdi]`（元素的**第一个 qword = 一个指针**），
再 `0x133190 = lea rax,[rcx+8] ; ret` 得到 `ptr+8`，然后 `0x5CD800(out, ptr+8)`。
⇒ 元素 = `{ void* p ; 其余 40 字节 }`，且 `p+8` 处又是一个容器（`0x5CD800` 走的就是它）。
**[未确认]**：`p` 指向的型别、元素其余 40 字节的内容、以及填充该 vector 的那个循环
（在 `0x6AB394`/`0x6AB3E8` 一带，那里调 `0x4FC5A0 GetNumberOfParts` / `0x4FC5B0 GetPart`）。

### 16.4 仍未确认

* `core+0x28` / `core+0x30`（`Pb+0x1B8` / `Pb+0x1C0`）的用途（已建模为字段，未接算法）；
  同理 `core+0x38`（`Pb+0x198`，pipe 路径）。
* 两个参数块内"哪个 qword 对哪个语义"的逐一配对。
* 填充 `core+0x48` 那个 vector 的循环。
* `0x5C61D0` / `0x5CD360` 内部、`0x134470` 那一路。

---

## 17. **更正 §16.3**：行容器是 `vector<指针>`，0x30 步长属于嵌套容器 **[本轮，已证实]**

上一轮我据 `0x13C380` 的 `add rbx, 0x30` 判定"行容器元素 48 字节"。本轮读到 `0x6AABC0`
**真正把元素推进 `core+0x48`** 的那几行，结论不同：

```
6AB6A0  rcx = [rsp+0x78]                  ; the Part*
6AB6AD  call 0x4F7690(part)               ; -> 一个对象（rsi）
6AB6B5  eax = core[+0x40]                 ; ★ 那个 mode
6AB6BA  cmp eax, 0   ; 6AB6C0 cmp eax,1   ; 6AB6C9 cmp eax,3
6AB6CC  movabs rax, 0x1A3185C5000         ; ★ = 1.8e12 = 180 度（定点度，与 sin 块同源）
6AB6F6  call 0x5C4C50(...)                ; -> r15
6AB711  call 0x5C4950(rsp+0x1d0, r15, rsi)
6AB72E  call 0x134470(rcx=r15, rdx=rsp+0x1b0, r8=rsp+0x1d0, r9=core+8)   ; ★ r9 = core+8（配置块）
6AB738  new(0x90)                         ; ★ 144 字节的对象
6AB757  call 0x1333D0(newObj, rsp+0x1b0, edx=partIndex, r8, r9=r15, ...)
6AB75C  rax = core[+0x50]                 ; 向量的 end
6AB768  cmp rax, core[+0x58]              ; end vs cap
6AB76C  je 0x6AB8DD                       ; 需要扩容
6AB777  qword ptr [rax] = rdi             ; ★ 存一个**指针**
6AB77A  add rax, 8                        ; ★★ 元素步长 = 8，不是 0x30
6AB77E  core[+0x50] = rax
...
6AB7A9..6AB7FB  尾部清理：对 [rsi+0x18]..[rsi+0x20] 以 **0x18** 步长逐个 `operator delete [rbx]`
6AB7F4  add rsi, 0x30                     ; 以 0x30 步长走过临时缓冲
6AB812  add dword [rsp+0x50], 1 ; jmp 0x6AB3E0    ; 下一个零件
```

⇒ **`core+0x48` 是 `std::vector<Item*>`（元素 8 字节 = 指针）**，`Item` 是
`0x1333D0(...)` 造出的 **0x90 = 144 字节**对象。

**那 0x30 是从哪来的？** 是 `0x13C380` 的**第二个**循环。`0x13C380` 有两个循环：

* 循环 A（`0x13C420`）：`rcx = [rdi]`（取容器里的**指针**）→ `0x133190 = lea rax,[rcx+8]`
  ⇒ 取 `Item+8` 处的**嵌套容器** → `0x5CD800(out, Item+8)` 求包围盒。
* 循环 B（`0x13C854` 起）：`rbp = [rax+8] ; rbx = [rax]`（`rax = 0x5C61D0(嵌套容器)`）
  然后 `add rbx, 0x30` ⇒ **步长 0x30 属于那个嵌套容器**，
  用 `0x5CD360` 与 `0x5C8C50` 并盒。

所以 §16.3 里"元素步长 48 字节"的说法对**外层行容器是错的**，对**嵌套容器/临时缓冲是对的**。
`0x133190` 返回 `ptr+8` 也正好解释了两层结构。

**附带新增的两条事实**：

1. `core+0x40` 的 mode 在 `0x6AB6B5` 分派，其中一条分支把
   **`0x1A3185C5000 = 1.8e12`（= 180 度，定点度）** 作为角度参数（`0x6AB6CC` 存到 `[rsp+0xa0]`）。
   这与我此前译出的 `0x1380D0` sin 块里的 180 度魔数**是同一个常量**。
2. `0x134470` 是**逐零件**调用的（每个 `Part` 一次），且 `r9 = core+8`（配置块）
   —— 说明它是另一条与 `0x13C380` 平行、但**每次一块几何**的构造/计算路径。

### 17.1 仍未确认

* `Item`（0x90 字节）的**字段布局**（只知道 `+8` 是嵌套容器；构造者 `0x1333D0` 未译）。
* 嵌套容器的**元素型别**（步长 0x30、`[+0x18]`/`[+0x20]` 还有一层以 0x18 步长的指针表）。
* `0x4F7690` / `0x5C4C50` / `0x5C4950` 的作用；`0x134470` 那一路的具体算法。
* `core+0x28` / `core+0x30` / `core+0x38` 的用途。

---

## 18. `Item` / 嵌套容器的三层结构 **[本轮新增，已证实：偏移与步长]**

### 18.1 `Item`（0x90 = 144 字节）的构造者 `0x1333D0`（2408 B / 540 条）

调用点（`0x6AABC0`）：`call 0x1333D0(newObj, rsp+0x1b0, edx=partIndex, r8, r9=r15,
[rsp+0x20]=r15, [rsp+0x28]=core+8)`；返回指针后被存进 `core+0x48` 的 `vector`。

`r14 = this`，其写入即布局：

```
1333EA  dword [r14 + 0x00] = edx          ; ★ partIndex（32 位）
13340B  qword [r14 + 0x08] = 0            ; ┐
133417  qword [r14 + 0x10] = 0            ; ├ 一个 vector 的 begin/end/cap（+8/+0x10/+0x18）
13341F  qword [r14 + 0x18] = 0            ; ┘
133453  qword [r14 + 0x08] = <new ptr>    ; 分配后回填 begin
13345A  qword [r14 + 0x10] = <new ptr>    ; end = begin（空）
13345E  qword [r14 + 0x18] = ptr + size   ; cap
1334F0..13351B  逐元素拷贝：源 [r15]..[r15+8]，**步长 0x10（16 字节）**
133520  ... 继续处理 [r15+0x18]..[r15+0x20]，**步长 0x18**
其余写入：+0x20 +0x28 +0x30 +0x38 +0x40 +0x48 +0x50 +0x58 +0x60(×5)
          +0x68 +0x70 +0x78(×5) +0x80 +0x88
```

⇒ **`Item` = `{ int partIndex @+0x00 ; std::vector<Elem48> @+0x08 ; 其后 +0x20…+0x88 多组字段 }`**。

**这正好印证 §17**：`0x133190 = lea rax,[rcx+8]` 取的 `Item+8` 就是那个嵌套 `vector<Elem48>`，
`0x13C380` 循环 A 交给 `0x5CD800` 求包围盒的就是它。**三层结构**：

```
core+0x48 : std::vector<Item*>          元素 8 字节（指针）
   Item   : 0x90 = 144 字节             +0x00 int partIndex ; +0x08 vector<Elem48> ; …
   Elem48 : 0x30 = 48 字节              +0x00 vector<Elem16>(16 字节元素)
                                        +0x18 vector<0x18 字节记录>(每条拥有一个指针)
   Elem16 : 16 字节
```

步长证据：外层 `0x6AB77A add rax,8`；`Elem48` 由 `0xAAAAAAAAAAAAAAAB` + `sar 4`（÷48，
见 `0x1333F2`/`0x133407`/`0x133413` 与 `0x6AB41C`/`0x6AB450`/`0x6AB454`）；
`Elem16` 由 `0x1334B2 sar rax,4` + 拷贝循环 `0x133503 add rdx,0x10`（16 字节）；
`0x18` 那一层见 `0x6AB7A9..0x6AB7FB` 的清理循环（`add rbx, 0x18`，逐条 `operator delete [rbx]`）。

### 18.2 仍未确认

* `Item` 的 `+0x20…+0x88` 各字段的**语义**（只知有若干组 begin/end/cap 与计数，
  其中 `+0x60` 与 `+0x78` 各被写 5 次）。
* `Elem48` / `Elem16` 的几何含义（是点？线段？环？——只能确定互相嵌套与尺寸）。
* `0x4F7690`（`Part` → 那个 48 字节元素容器）、`0x5C4C50`、`0x5C4950` 的作用。
* `0x134470` 的算法（它是**逐零件**调用、`r9 = core+8` 配置块的另一条路径）。
* `core+0x28` / `core+0x30` / `core+0x38` 的用途。
* 两个 setter 参数块内 qword 与语义的逐一配对。

> 说明：以上都属于**本栈深层细节**，不是本报告任何主结论的前提；
> 它们已在文档中逐条列出并标明"未确认"，没有任何一处用近似值顶替。

### 18.3 本轮另收两项 **[已证实]**

**(a) `0x4F7690` 是 Part 的一个尾调访问器**

```
4F7690  mov rcx, qword ptr [rcx + 0x70]      ; ★ Part + 0x70
4F7694  jmp 0x547670                          ; 尾调
```

⇒ `0x6AABC0` 里那串"取 48 字节元素容器"的入口是 **`Part+0x70`**（经 `0x547670`）。
`0x6AB6AD` 的 `rsi` 随后被用作 `[rsi]`/`[rsi+8]`（容器），与 §18.1 的 `Elem48` 层对上。

**(b) core 的 `+0x28` / `+0x30` / `+0x38` 在 `0x6AABC0` 内没有任何读者**

对 `0x6AABC0` 内以 `rbp`（= core）为基址的读/写做了计数：

| 字段 | 读 | 写 | 在 `0x6AABC0` 内的首次读 |
|---|---|---|---|
| `+0x00`（pipe 字节） | 0 | 1 | — |
| `+0x08` | **3** | 2 | `0x6AB716`（`r9 = core+8` 交给 `0x134470`） |
| `+0x10` | 0 | 1 | — |
| `+0x18`（阈值） | 0 | 2 | — |
| `+0x20`（系数） | 0 | 2 | — |
| `+0x28` | **0** | 1 | — |
| `+0x30` | **0** | 1 | — |
| `+0x38` | **0** | 1 | — |
| `+0x40`（mode） | **2** | 2 | `0x6AB162` |
| `+0xC0`（Squeezer*） | **2** | 2 | `0x6AB864`（析构路径） |

⇒ `+0x18` / `+0x20` 虽然在本函数内不被读，但**确实被消费**：`0x6AABC0` 把 `core+8`
作为 `r8` 交给 `0x13C380`，而 `0x13C380` 只读 `cfg[+0x10]`（= `core+0x18`，阈值）与
`cfg[+0x18]`（= `core+0x20`，系数）—— 这正好闭合了 §12/§14 的链路。
**`+0x28` / `+0x30` / `+0x38` 则在整条已追踪的路径上找不到读者**
（`0x13C380` 不读它们，`0x6AABC0` 也不读）。
⇒ 它们**要么由 core 的其它成员函数读取（未追踪），要么是死字段**；
本轮**不下结论**，只把"已追踪范围内零读者"这一事实写明。

---

## 19. `0x134470` 的算法与 core 配置的第二个消费者 **[本轮新增，已证实]**

### 19.1 `0x134470`（572 B / 146 条）= **逐零件的"候选取最小"**

调用点：`0x6AABC0` 内 `0x6AB72E call 0x134470(rcx=r15, rdx=rsp+0x1b0, r8=rsp+0x1d0, r9=r12=core+8)`，
**每个零件一次**。逐指令：

```
134492  dword [rsp+0x28] = 0x14 = 20                      ; 一个初始容量/计数
1344B8  call 0x5EC370(...)                                 ; 在 rsp+0x50 造容器
1344C5  [rsp+0x70]=0 [+0x78]=0 [+0x80]=0                   ; 另一个 vector（begin/end/cap）
1344FC  call 0x8BEFC0(rcx=rsp+0x70, rdx=rsp+0x3f, r8=rsp+0x40)   ; 填充它
13450B  movabs rax, 0xD18C2E2800                           ; ★ = 9e11 = **90 度（定点度）**
13451D  [rsp+0x40] = rax
134515  if ([rsp+0x78] == [rsp+0x80]) goto 0x13466F
134573  add rbx, 0x38                                      ; ★ 内层元素步长 0x38 = 56 字节
1345B0  call 0x5C4C40(rbp)
1345B8  rcx = [rsp+0x70] ; r13 = [rsp+0x78]                ; 外层 vector 的 begin/end
1345E9  rdx = rbx ; rcx = rsi ; call 0x5C2E40(rsi, rbx)     ; 谓词，返回 al
1345F4  if (!al) → add rbx, 0x10（★ 外层步长 0x10 = 16 字节）→ 继续
1345F8  r9 = r12(= core+8 配置) ; r8 = rbx ; rdx = rsi ; rcx = rdi
134604  call 0x133DE0(rcx, rdx, r8, r9 = core+8)            ; ★ 逐元素的代价计算
134609  if (first) goto 0x134614
13460E  ucomisd xmm6, xmm0 ; jbe → 下一个                 ; ★ **保留更小的那个**
134614  rax = [rbx] ; rdx = [rbx+8]
13461E  xmm6 = xmm0                                         ; best = 当前
134629  qword [rbp] = rax ; qword [rbp+8] = rdx             ; ★ 把最优的 16 字节条目写进 *out
```

⇒ **`0x134470` 的语义**：扫描一个 **16 字节条目**的容器，对每个通过谓词 `0x5C2E40` 的条目调用
`0x133DE0(..., core+8)` 求代价，**保留最小值**，并把**最优条目**（16 字节）写进 `*out`。
两个常量/尺寸：`0x14 = 20`（初始容量）、`0x38 = 56`（内层元素步长）、
**`0xD18C2E2800 = 9e11 = 90 度**（与 §8.3 的 sin 块 90 度魔数**同一个**，与 §17 的 180 度同族）。

### 19.2 **core 的 `+0x18` / `+0x20` 有第二个消费者**

`0x134470` 把 `r9 = core+8`（配置块）交给 `0x133DE0`，而 `0x133DE0` 正是
§13 里那个"真正的 Row 构造函数调用者"（`0x133DE0` ← `0x134470 @0x134604`）。
⇒ `cfg[+0x10] = core+0x18`（阈值）与 `cfg[+0x18] = core+0x20`（系数）**除了 `0x13C380`，
还被 `0x133DE0` 这条逐零件路径消费**。这补完了 §18.3(b) 的结论。

### 19.3 **明确声明：`core+0x28` / `+0x30` / `+0x38` 用本方法不可恢复** **[不可恢复 + 原因]**

为找它们的读者，做了两轮定向检索：

1. **数据库 TU（`0x4F0000`–`0x500000`）里的大小 ≤40 字节的访问器**中，命中这些
   `Pb` 偏移的**只有两个**：`0x4FC2F0`（`Pb+0x170`）与 `0x4FC300`（`Pb+0x1A0`）。
   `+0x198` / `+0x1B8` / `+0x1C0` **没有对应的 getter**。
2. **全局按偏移扫描读者**会把它们与 130–220 个**无关类型**的同偏移访问混在一起
   （例如 `Pb+0x1B8` 有 131 个函数在读，其中含 `GetPartUserStringEx`、`CNS_GetSheet`、
   `SetPartUserString` 等，显然分属不同类），**无法据此判定归属**。

⇒ 结论：在**不建立跨函数指针等值分析**的前提下，
**`core+0x28` / `+0x30` / `+0x38` 是否被别处读取无法判定**。
已知的确切事实只有两条：它们**由两个配置块写入**（`Pb+0x198`=pipe 路径的字节、
`Pb+0x1B8`、`Pb+0x1C0`），且**在 `0x6AABC0` 与 `0x13C380` 内都没有读者**。
工程里它们被建模为字段（`pipeAt198`、`commonCutAt1B8`、`commonCutAt1C0`）
但**未接任何算法** —— 这是**明说的缺口，不是近似**。

---

## 20. 配置参数块的**确切边界**：原样结构拷贝 **[本轮新增，已证实]**

### 20.1 `SetCommonCutParameters` 写入的是一整段**连续块**

```
3C4DC  rbp = rsp + 0xF0
3C4ED  call 0x185A40(rbp, rsi = arg2, r12)         ; ★ 在 rsp+0xF0 生成参数块
3C4F2  [Pb+0x188] = [rsp+0xF0]
3C508  [Pb+0x190] = [rsp+0xF8]
3C51A  [Pb+0x198] = [rsp+0x100]
3C529  [Pb+0x1A0] = [rsp+0x108]
3C538  [Pb+0x1A8] = [rsp+0x110]
3C547  [Pb+0x1B0] = [rsp+0x118]
3C556  [Pb+0x1B8] = [rsp+0x120]
3C565  [Pb+0x1C0] = [rsp+0x128]
3C574  dword [Pb+0x1C8] = [rsp+0x130]
3C581  word  [Pb+0x1CC] = [rsp+0x134]
3C590  [Pb+0x...] = [rsp+0x138] ...
```

### 20.2 `0x185A40`（736 B / 173 条）= **原样结构拷贝**

```
185A48  rax = [rdx]        ; 185A53 [rcx] = rax
185A56  rax = [rdx+0x08]   ; 185A63 [rcx+0x08] = rax
185A67  [rdx+0x10] → [rcx+0x10]
185A6F  [rdx+0x18] → [rcx+0x18]
185A77  [rdx+0x20] → [rcx+0x20]
185A7F  [rdx+0x28] → [rcx+0x28]
185A87  [rdx+0x30] → [rcx+0x30]
185A8F  [rdx+0x38] → [rcx+0x38]
185A97  [rdx+0x40] → [rcx+0x40]        ; 共 **9 个 qword** 原样搬
185A9B  [rcx+0x48]=0 [rcx+0x50]=0 [rcx+0x58]=0
185AB7  rax = ([rdx+0x50] - [rdx+0x48]) ; 185ABA sar rax,3   ; ★ 8 字节元素的 vector
185AD9  operator new(rbp)
185AE1  [rcx+0x48]=ptr [rcx+0x50]=ptr [rcx+0x58]=ptr+size
185AED  r9 = [rsi+0x50] ...            ; 继续按 8 字节元素拷贝
```

⇒ **`Pb+0x188` 起的那一段，就是 `SetCommonCutParameters` 的 `arg2` 所指数组的
"偏移 0x00 起 9 个 qword" 的原样拷贝**，再加一个 `vector<8 字节元素>` 在 `+0x48`。
所以映射是**逐偏移一一对应**的：

| Pb 偏移 | = `arg2` 的偏移 |
|---|---|
| `+0x188` | `+0x00` |
| `+0x190` | `+0x08` |
| `+0x198` | `+0x10` |
| `+0x1A0` | `+0x18` |
| `+0x1A8` | `+0x20` |
| `+0x1B0` | `+0x28` |
| `+0x1B8` | `+0x30` |
| `+0x1C0` | `+0x38` |
| `+0x1C8`/`+0x1CC` | `+0x40`（dword + word） |
| `+0x1D0`… | `+0x48`（vector 的 begin/end/cap） |

### 20.3 **明确声明：块的"语义命名"不可恢复** **[不可恢复 + 原因]**

由上表，配对问题已被**化简到不能再化简**：要说出 `Pb+0x1B0` 是"什么"，
等价于说出 **`SetCommonCutParameters` 的调用方结构体（导出的参数类型）在偏移 0x28 处是什么**。
而该结构体是**调用者分配、由导出签名约定**的：
二进制里**没有它的定义、没有 typeinfo、没有成员名字串**（与 §11.2 的三个 Prc 型别同一处境）。
⇒ **本方法无法给出这些字段的语义名**；能给出且已给出的，是**精确的偏移对应**与
**每个偏移由哪个导出写入**（`+0x178/+0x180` ← `SetPipeMode`；`+0x188..` ← `SetCommonCutParameters`）。

### 20.4 工程侧命名更正 **[已证实]**

原先 `Order` 里的 `pipeAt178/180/188/190/198` 命名**名不副实**（`+0x188/+0x190/+0x198`
其实来自 `SetCommonCutParameters`，只有 `+0x178/+0x180` 来自 `SetPipeMode`）。
已统一改为**按偏移命名**的 `cfgAt178 / cfgAt180 / cfgAt188 / cfgAt190 / cfgAt198`，
并在 `model.hpp` 注释中写明：名称是**按偏移**而非按角色，且逐个列出两个导出的写入范围。
（行为不变，仅命名与注释；`RowNestCore` 与 `test_nester` 同步更新。）

---

## 21. 逐零件路径的依赖：谓词 `0x5C2E40` 与取价例程 `0x133DE0` **[本轮新增]**

### 21.1 谓词 `0x5C2E40`（138 B / 53 条）—— **完全译出** **[已证实]**

```
5C2E47  rdi = [rcx+8]                        ; 容器的 end
5C2E4B  rbx = [rcx]                          ; 容器的 begin
5C2E51  if (begin == end) → return 0
循环（★ 步长 0x18 = 24 字节）：
5C2E69  rcx = rsi ; call 0x5C4CD0(rsi)       ; → al（一个 tag 字节）
5C2E71  cmp al, byte [rbx]                   ; 与该记录的首字节比较
5C2E73  jne → 下一个
5C2E75  rcx = rsi ; call 0x5C4CE0(rsi)       ; → rax（一个整数）
5C2E7D  rcx = [rbx+8] ; r8 = [rbx+0x10]      ; 该记录的两个 qword
5C2E85  if (rcx > r8) goto 5C2EA2
5C2E8A  al = (rax >= rcx) & (rax <= r8)      ; ★ 落在 [rcx, r8] 内
5C2EA2  al = (rax <= r8) | (rax >= rcx)      ; ★ 或落在反向区间 [r8, rcx] 内
```

⇒ **`0x5C2E40(container, x)` = "容器里是否存在一条记录，其 `tag` 等于 `x` 的 tag，
且区间 `[rec+8, rec+0x10]` 包含 `x` 的整数值"** —— 一个**区间归属测试**。

记录形状（**新事实**）：**24 字节 `{ u8 tag @0 ; int64 lo @+8 ; int64 hi @+0x10 }`**，
步长 `0x18` —— 与 §18.1 里 `Elem48+0x18` 那个"0x18 字节记录"的清理循环**完全对上**，
所以谓词走的就是 **`Elem48` 的第二层容器**。

### 21.2 取价例程 `0x133DE0`（1458 B / 331 条）的入口 **[已证实]**

```
133E20  call 0x5CEE50(rsp+0x170, r8)                  ; 建中间对象
133E2E  call 0x5D38C0(rsp+0x40, rbx, rdi)
133E3E  call 0x5CD800(rsp+0xE0, rbp = rsp+0x40)       ; ★ 候选的包围盒
133E43  if (byte [rsp+0xE0] != 0) goto 0x133E81       ; 标志置位 ⇒ 高度/宽度都留 0
133E55  xmm6 = [rsp+0xF8] - [rsp+0xE8]                ; = maxY - minY = 高
133E67  xmm6 *= [0x9BCEB0] = 20.0                     ; ★★ 高 × 20
133E6F  xmm7 = [rsp+0x100] - [rsp+0xF0]               ; = maxX - minX = 宽
133E81  call 0x1333D0(rcx = rdi, edx = 0, r8 = rbx, r9 = r13,
                      [rsp+0x20] = r12, [rsp+0x28] = rsi)   ; ★ 造 Item（partIndex = 0）
133E90  new(0x10) ; [rax] = rdi ; [rax+8] = 0x271000000000  ; 16 字节临时记录
133EC0  xmm3 = [rsi+0x10]                             ; cfg[+0x10] = core+0x18 = 阈值
133ED0  xmm2 = [rsi+0x18]                             ; cfg[+0x18] = core+0x20 = 系数
133EF7  call 0x136B80(&squeezer@rsp+0x30, xmm1 = 高×20, xmm2, xmm3)   ; ★ 造 Row::Squeezer
```

⇒ **同一个 `Row::Squeezer` 构造器在两个调用点的第一实参含义不同**：

| 调用点 | `xmm1`（构造器第一实参） |
|---|---|
| `0x13C380`（行容器路径） | `2 × max(高, 宽)`（`13C456`/`13C460`） |
| **`0x133DE0`（逐候选路径）** | **`20.0 × 高`**（`133E55`–`133E67`，常量 `0x9BCEB0`） |

构造器内部再把 `xmm1` 加倍（`0x138A8F xmm7 = xmm1 + xmm1`）交给 `0x2530D0`。

**已并入工程**（`lcns`）：新增常量 `row::kCandidateHeightScale = 20.0`（RE `0x9BCEB0`）
与 `row::candidateSqueezerArg(height) = 20 * height`（RE `0x133E55..0x133E67`），
并由验收测试 `test_recovered` 断言（`candidateSqueezerArg(3.0) == 60.0`）。

### 21.3 `0x136Cxx` / `0x137FE0` 家族作用于**另一个对象**，不是 Squeezer **[已证实 + 边界]**

`0x133DE0` 里 `rbx = rsp+0x110`，而 Squeezer 的 out 槽是 **`rsp+0x30`**（`0x133EF7`）。
所以下面这些方法**不是** Squeezer 的方法，而是 `rsp+0x110` 处那个对象的：

| 函数 | 大小 | 逐指令结论 |
|---|---|---|
| `0x136CA0` | 13 B | `([rcx+0x20] − [rcx+0x18]) >> 4` ⇒ **容器元素个数**（16 字节元素），返回整数，**不碰 xmm0** |
| `0x136CB0` | 78 B | **带缓存的惰性求值**：先读 `[rcx+0x50]` 与常量 `0x9BCF48` 比较（相等才计算）；若容器空则置 0，否则取**末元素** `[rax-0x10]`（首 qword）与 `[rax-8]`（double），`call 0x134F30(首 qword)` 后 `xmm0 += xmm6`，并**回写 `[rcx+0x50]`** |
| `0x136D30` | 13 B | `al = [rcx+0x10] ; if (al) al = [rcx+0x11] ; return al` ⇒ 两级标志读取 |
| `0x137FE0` | 177 B | 遍历一个 **16 字节记录**的容器（`add rbx,0x10`）：读 `esi = [rbx+0xc]`（计数）与 `edx = byte [rbx+8]`，循环 `call 0x137A90([rbx], edx, rbp, ...)` 直到计数耗尽 |

⇒ `0x133DE0` 在**构造 Squeezer 之后**又构造/使用了一个"带缓存分值的容器对象"，
其缓存字段在 `+0x50`（守卫常量 `0x9BCF48`），容器在 `+0x18`/`+0x20`（16 字节元素），
标志在 `+0x10`/`+0x11`。

**`0x133DE0` 的返回值**：`0x133F47 call 0x136CB0` 把计算结果留在 **`xmm0`**，
随后 `0x133F53 call 0x136CA0`（整数、不碰 xmm0）与其后的一串 `operator delete` 清理
（只写 `rax`/指针）**都不会破坏 xmm0** ⇒ 函数经 `0x1342D4 ret` 返回的就是
**`0x136CB0` 算出的那个 double**（即 `+0x50` 的缓存值）。`0x134470` 正是用它做
`ucomisd xmm6, xmm0` **取最小**。
**[推断]**（标注）：该结论依赖"`xmm0` 在清理路径中不被破坏"，我已逐条核对
`0x134060`–`0x1342D4` 的指令均为整数/指针操作，故证据充分，但仍是**推断**而非直接读到 `movsd`。

### 21.4 仍未确认

* `rsp+0x110` 那个对象的**类名与完整布局**（`0x136C00` 是它的初始化函数，未译）。
* `0x134F30`（对末元素首 qword 做什么）、`0x137A90`（记录合并）、`0x136C00`、
  `0x5CEE50`、`0x5D38C0`、`0x5C4CD0`/`0x5C4CE0`（tag / 整数取值器）均未译。
* `0x133EDF` 的立即数 `0x271000000000`（16 字节临时记录的第二 qword；按字节看
  `0x2710 = 10000` 落在 `+0xd`）的**字段切分**未定。
* §21.1 的 `0x5C2E40` 返回 `1` 之后 `0x134470` 如何用它（`0x1345F4 test al,al` 跳过不匹配项）——
  这一条**已清楚**：谓词用来说"这个候选可接受"。

---

## 22. 逐候选的**分值公式** —— 取价链闭合 **[本轮新增，已证实]**

### 22.1 `0x136C00`（75 B）= `rsp+0x110` 那个对象的初始化器，**布局全给出**

```
136C00  xmm0 = [0x9BCF48] = -1.0        ; ★★ 缓存哨兵是 **-1.0**（不是 NaN！）
136C08  rax = rcx + 0x40
136C0C  [this+0x00] = xmm1              ; double
136C10  [this+0x08] = xmm2              ; double
136C15  byte [this+0x10] = 1            ; 标志 A（0x136D30 读它）
136C19  byte [this+0x11] = 1            ; 标志 B（0x136D30 的次级读取）
136C1D  [this+0x18] = 0                 ; ┐
136C25  [this+0x20] = 0                 ; ├ vector（**16 字节元素**，0x136CA0 用它算个数）
136C2D  [this+0x28] = 0                 ; ┘
136C35  [this+0x30] = this + 0x40       ; 一个自指的链表/哨兵头
136C39  [this+0x38] = 0
136C41  byte [this+0x40] = 0
136C45  [this+0x50] = xmm0 = -1.0       ; ★ 分值缓存，初值 -1.0
```

⇒ **对象布局**：`{ double@0 ; double@8 ; u8@0x10 ; u8@0x11 ; vector<16B>@0x18/0x20/0x28 ;
node*@0x30(=this+0x40) ; u64@0x38 ; u8@0x40 ; double 分值缓存@0x50 }`。

这也**纠正了 §21.3 的一处猜测**：我原先把 `0x9BCF48` 写成"可能是 NaN 哨兵"，
实际是 **`-1.0`**。

### 22.2 `0x134F30`（22 B）= 节点贡献

```
134F30  if (byte [rcx+0x18] != 0) { xmm0 = 0 ; ret }     ; 标志置位 ⇒ 贡献 0
134F36  xmm0 = [rcx+0x30] - [rcx+0x20] ; ret             ; 否则 = b - a
```

### 22.3 `0x136CB0`（78 B）= 惰性分值 —— **公式闭合**

```
136CBA  xmm0 = [this+0x50]
136CBF  ucomisd xmm0, [0x9BCF48] = -1.0
136CCA  jp 0x136CF3 / jne 0x136CF3      ; ★ 只要缓存 ≠ -1.0 就直接返回缓存（**不重算**）
136CCE  rax = [this+0x20]                ; vector 的 end
136CD2  xmm0 = 0
136CD6  if ([this+0x18] == rax) → 0x136CEE      ; 容器空 ⇒ 0
136CDC  rcx = [rax-0x10]                 ; ★ 末元素的第一个 qword（节点指针）
136CE0  xmm6 = [rax-8]                   ; ★ 末元素的第二个 qword（double）
136CE5  call 0x134F30(rcx)
136CEA  xmm0 += xmm6                     ; ★★ 分值 = 节点贡献 + 末元素的值
136CEE  [this+0x50] = xmm0               ; 记忆化
136CF3  ... return（xmm0 保持不变）
```

⇒ **`score = 容器空 ? 0 : ( nodeLength(末元素.first) + 末元素.second )`**，
缓存于 `+0x50`，哨兵 `-1.0`。
（"末元素决定"由 **`0x136CDC`** 的 `rcx = [rax-0x10]` / `xmm6 = [rax-8]` 确证：
`rax` 是 vector 的 **end**，故取 `end[-1]`，即**最后一个**元素。）

**一个容易踩的语义**：缓存**只在恰好等于 `-1.0` 时**才重算——**改数据不会让它失效**；
调用方必须自己把它重置成 `-1.0`。`0x136CB0` 的 `xmm0`/`xmm1` 两个参数**根本没被读**
（真正的签名是 `(this)`）。

### 22.4 已并入工程 **[已证实]**

`lcns/include/lcns/row.hpp` 新增：

| RE | 工程 |
|---|---|
| `0x9BCF48 = -1.0` | `row::kScoreUnset` |
| `0x134F30` 的节点三字段与算术 | `row::ScoreNode{flag,a,b}` + `row::nodeLength()` |
| 16 字节元素 `{ptr, double}` | `row::ScoreRecord{node, value}` |
| `0x136CB0` 的取值（空→0；否则末元素） | `row::candidateScore(records)` |
| `+0x50` 的 `-1.0` 哨兵记忆化与"只在 `-1.0` 时重算" | `row::LazyScorer{score/invalidate/cached/computed}` |

测试：`test_row` 断言"标志置位贡献 0"、"**用末元素而非首元素**"（首元素故意给 100 以区分）、
"空容器 0"、"改数据不失效而 `invalidate()` 后重算"；`test_recovered` 断言 `kScoreUnset == -1.0`
且 **不是 NaN**。

### 22.5 仍未确认

* **容器是如何被填的**：`0x137A90`（1175 B，记录合并，内部调 `0x1331A0`/`0x1333C0`/`0x136C90`）
  与 `0x137FE0` 的合并循环未译 ⇒ **每个元素的"节点"从哪来、其 `+0x20`/`+0x30` 是什么，
  尚未确定**。分值**公式**已确证，但**输入的产生**未确证。
* `0x5CEE50`、`0x5D38C0`、`0x5C4CD0`、`0x5C4CE0`（谓词的 tag / 整数取值器）未译。
* `0x133DE0` 四个实参各自的含义（已知 `r9 = core+8` 是配置块）。
* 立即数 `0x271000000000`（§21.2）的字段切分。

---

## 23. 两套对象的**完整布局** **[本轮新增，已证实]**

本轮把 §21 里那两族访问器逐个读完，得到**两类对象的完整成员表**。

### 23.1 节点（Row node）—— `0x134Fxx`/`0x1350xx` 访问器族给出 **[已证实]**

| 函数 | 大小 | 逐指令 | 含义 |
|---|---|---|---|
| `0x134F30` | 22 B | `byte[rcx+0x18] ? 0 : ([+0x30] − [+0x20])` | **X 跨度**（退化时为 0） |
| `0x134F50` | 22 B | `byte[rcx+0x18] ? 0 : ([+0x38] − [+0x28])` | **Y 跨度**（退化时为 0） |
| `0x134F90` | 14 B | `dl ? byte[+0x41] : byte[+0x40]` | 标志对选择 |
| `0x134FA0` | 68 B | 选 `+0x48` 或 `+0x70`；若其首字节非 0 则拷 4 个 qword（`+8/+0x10/+0x18/+0x20`）并置 `out[0]=1` | **optional<4×double>** 访问器（§8.4 已认出，这里确认它作用在**节点**上） |
| `0x134FF0` | 21 B | `dl ? (rcx+0xa8) : (rcx+0xc0)` | 两个容器二选一 |
| `0x135010` | 22 B | `dl ? byte[+0x99] : byte[+0x98]` | 第二组标志对 |
| `0x135030` | 9 B | `[rcx+0xa0]`（double） | 一个 double |

⇒ **节点布局**：

```
+0x18  u8     退化标志（两个跨度函数都先测它）
+0x20  double minX ; +0x28 double minY ; +0x30 double maxX ; +0x38 double maxY   ← 包围盒
+0x40  u8     ; +0x41 u8        标志对 A
+0x48  optional<4×double>       区间槽 1（presence 字节 + 4 个 double，共 0x28 字节）
+0x70  optional<4×double>       区间槽 2
+0x98  u8     ; +0x99 u8        标志对 B
+0xa0  double
+0xa8  容器 1 ; +0xc0 容器 2
```

**这正好就是我在 §8.4/§12 里建模的 "Row" 对象**（`+0x48`/`+0x70` 两个 4-double 槽、
`+0xA8`/`+0xC0` 两个容器）——本轮把其余字段也补齐了，
并且 `nodeLength` 现在有了**明确语义：盒的 X 跨度**。

### 23.2 `rsp+0x110` 那个对象——`0x136Cxx`/`0x136Dxx` 给出 **[已证实]**

| 函数 | 逐指令 | 含义 |
|---|---|---|
| `0x136C90` | `lea rax,[rcx+0x18]` | 取它的 `vector` |
| `0x136CA0` | `([+0x20] − [+0x18]) >> 4` | 该 vector 的**元素个数**（16 字节元素） |
| `0x136CB0` | 见 §22.3 | 惰性分值，缓存 `+0x50`，哨兵 `-1.0` |
| `0x136D00` | `[rcx]`（double） | 第一个 double |
| `0x136D10` | `[rcx+8]`（double） | 第二个 double |
| `0x136D20` | `dl ? byte[+0x11] : byte[+0x10]` | 标志对选择 |
| `0x136D30` | `byte[+0x10] ? byte[+0x11] : byte[+0x10]` | 短路的标志读取 |
| `0x136D40` | `rcx += 0x30 ; jmp 0x910AF0` | **在 `+0x30` 处构造 `std::string`** |
| `0x136D50` | 读 `[rdx+0x30]`/`[rdx+0x38]` 作 `{ptr,len}` 并带 SSO 分支拷贝 | **字符串拷贝** |

**关键**：`0x136C00` 写的 `[this+0x30] = this+0x40`、`[this+0x38] = 0`、`byte [this+0x40] = 0`
**正是 `std::string` 的 SSO 初始化**（data 指向自身内联缓冲、size 0、终止符 0），
`0x136D40`/`0x136D50` 又从代码上证实 ⇒ **`+0x30` 是一个 `std::string`**。

⇒ **该对象布局**：

```
+0x00 double ; +0x08 double
+0x10 u8 ; +0x11 u8                     标志对
+0x18 std::vector<16 字节元素>（+0x18/+0x20/+0x28）
+0x30 std::string（SSO：data@+0x30、size@+0x38、内联缓冲@+0x40）
+0x50 double 分值缓存（初值 -1.0）
```

即一个"**带名字、两个 double、两个标志、一个记录表、一个记忆化分数**"的行候选对象。

### 23.3 顺带记下两个 rodata 常量（**语义未定，故不入代码**）

`0x137A90` 读到的两个常量：**`0x9BCF60 = 1e-06`**、**`0x9BCF70 = NaN`**。
它们出现在记录合并例程里，但**角色未确定**，因此**只记录、不写进工程**。

### 23.4 已并入工程 **[已证实]**

`lcns/include/lcns/row.hpp` 的 `row::ScoreNode` 扩成**完整节点布局**：
`{degenerate@0x18, minX@0x20, minY@0x28, maxX@0x30, maxY@0x38, flag40/flag41,
slotAt48, slotAt70, flag98/flag99, valueAtA0, listAtA8, listAtC0}`，
并新增 `nodeLength()`（= `0x134F30`，X 跨度）、`nodeLengthY()`（= `0x134F50`，Y 跨度）、
`nodeFlag40(n, second)`（= `0x134F90`）、`nodeFlag98(n, second)`（= `0x135010`）。
`test_row` 相应断言：X/Y 跨度、退化标志把两者都归零、两组标志对的选择。

### 23.5 仍未确认

* **容器如何被填**：`0x137A90`（1175 B）是记录合并例程（内部还要调
  `0x134F50`/`0x134F90`/`0x134FA0`/`0x134FF0`/`0x135010`/`0x135030`/`0x136CB0`/
  `0x136D00`/`0x136D10`/`0x136D20`/`0x137800`），**主体未译**；
  `0x137800`（636 B）亦未译。
* `0x1331A0` 选择的两个子对象（`+0x58`/`+0x70`）各自的角色。
* `0x5CEE50`、`0x5D38C0`（`0x133DE0` 开头两次构造）、`0x5C4CD0`/`0x5C4CE0`（谓词的取值器）。
* `0x133DE0` 四个实参的含义（仅知 `r9 = core+8` 是配置块）。
* ⇒ **结论**：分值**公式**与**节点的字段语义**已确证；
  **候选集如何生成**仍未确证，故 §19.1 那条"候选取最小"的**完整实现**仍不具备条件
  （不以假定输入凑版本）。

---

## 24. 容器由谁填：`0x137800` = **`orderedAddElement`** **[本轮新增，已证实]**

### 24.1 `0x137800`（636 B / 137 条）逐指令

```
137813  if (rdx == 0) goto 0x1378E0              ; 空指针 ⇒ 内联断言路径
137830  rax = [O+0x20]                           ; vector 的 end
137834  cmp rax, [O+0x28]                        ; 与 cap 比较
137838  je 0x137A11                              ; 需要扩容（有序插入）
13783E..137852  rcx = rdx（元素指针）; xmm0 = xmm2（分数）
137854  qword [rax] = rcx                        ; ★ 记录第 1 字段：指针
137857  movsd [rax+8] = xmm0                     ; ★ 记录第 2 字段：double
13785C  add rax, 0x10                            ; ★★ 步长 0x10 —— 正是 16 字节 {ptr, double}
137860  [O+0x20] = rax                           ; 提交新的 end
137864  call 0x134F70(rdx) ; 13786C call 0x1333C0  ; 取该元素的某个子对象（+0x20）
137871  if (byte [O+0x10] == 0) goto 0x137877
1378A0..1378D8  依据两个标志（0x134F90(rdx,1/0)）决定是否 byte [O+0x11] = 0
137877  movsd [rbx+0x50], -1.0                   ; ★★★ 每次插入都把分值缓存重置为 -1.0
```

**内联断言串解出方法名**：`0x1378E5` 的 `0x6465746e6569726f` + `0x656d656c45646441`
= **`"orderedAddElement"`**（另有 `..\row\…` 的源码路径碎片）。

### 24.2 三条硬结论

1. **记录形状确证**：`{void* @+0x00 ; double @+0x08}`，步长 `0x10`
   ⇒ 与工程里 `row::ScoreRecord{node, value}` **完全一致**（§22.4 的建模得到印证）。
2. **缓存失效点确证**：就是**追加器自己**（`0x137877 [O+0x50] = -1.0`），
   不是"调用方约定"。⇒ §22.4 里"调用方必须自己重置"的说法**已修正**为
   "由 `orderedAddElement` 在每次插入时重置"。
3. **容器是有序的**（方法名 `orderedAddElement`），而 `candidateScore` 取的是**末元素**
   ⇒ 分值等于容器的**某个极端元素**；`0x134470` 对该值 `ucomisd … jbe` **取最小**
   ⇒ **语义是 minimax**（最小化"最坏的那个"）。
   **[推断]**：升序还是降序无法仅由名字判定，故工程里**不写死**顺序语义。

### 24.3 **更正 §23.3**：`0x9BCF70` 不是"NaN 哨兵"，是**取绝对值掩码** **[已证实]**

`0x137E02` 与 `0x137F07` 都是 `andpd xmm6, xmmword ptr [0x9BCF70]`，
紧接着与 **`0x9BCF60 = 1e-06`** 比较（`0x137E20` / `0x137F0F`）。
`andpd` 配 `0x7FFF…` 位型是**取绝对值**的经典写法，而该位型**读作 double 就是 NaN**
——这解释了为什么它"看起来是 NaN"。⇒ 它是 **fabs 掩码**，`1e-06` 是 epsilon。

### 24.4 `0x137A90`（1175 B / 261 条）的形状 **[已证实为结构]**

```
137AFA  r15d = byte [rsp+0x180]                  ; 第 5 个实参（一个字节）
137B0F  call 0x1331A0(P, tag)   → r13            ; ★ 按 tag 选 P+0x58 或 P+0x70 的子对象
137B1A  call 0x1333C0(P)        → rbx = P+0x20
137B25  xmm13 = [P+0x30] ; xmm10 = [P+0x38]      ; 两个 double
137B31..137B4B  取 O 的 vector：若非空则 rbp = end[-1]
137B57..137B77  rdi = (vector 字节数 > 0x1f) ? end-0x20 : 0 ; 若 byte[P+0x20] 则 xmm11 = [P+0x28]
137B85  [rsp+0x28] = 0x136D20(O, 0)              ; 标志 A
137B99  [rsp+0x3f] = 0x136D20(O, 1)              ; 标志 B
137B9E  rbx = [r13] ; r14 = [r13+8]              ; ★ 遍历**被选中的子对象**的容器
137BAA  if (begin == end) → 0x137F20（xor eax,eax ⇒ 返回 0）
137BD1  xmm15 = 1e-06
循环（末尾 0x137E2B `add rbx, 0xd8` ⇒ ★★ 源容器元素步长 0xd8 = 216 字节）:
  137BF0  xmm9 = 1e-06 ; if (rbp == 0) goto 0x137DA0
  137BFE  rax = [r12] ; r8 = rbx ; rcx = r12 ; rdx = [rbp]
  137C0C  call qword [rax + 0x10]               ; ★★ 对第 4 实参 r12 的**虚调用**（槽 +0x10）
  137C0F  xmm8 = xmm0
  137C19  call 0x136CB0(O)                      ; 惰性分值
  137C21  rcx = [rdi] ; xmm6 = [rdi+8] ; xmm7 = xmm0 + xmm8
  137C32  call 0x134F30(rcx)                    ; 节点 X 跨度
  ...
  137DFE  xmm6 -= xmm0 ; fabs ; 0x137E20 ucomisd xmm9, xmm6 ; jae → 保留更小的
137E40  rdi = [rsp+0x30] ; if (rdi == 0) 返回 0
137E51  call 0x136CB0(O) ; xmm2 = xmm12 + xmm0
137E65  call 0x137800(O, rdi, xmm2)             ; ★★★ 把胜出元素**追加**进 O
137E6A  eax = 1 ; 恢复寄存器 ; ret              ; 返回 1
137F20  xor eax, eax ; ret                       ; 返回 0
```

⇒ **`0x137A90` = "在按 tag 选中的子对象容器里，用 `1e-06` 容差 + 虚调用 + 惰性分值挑出最优元素，
再 `orderedAddElement` 追加进 O"**，返回是否追加成功。源容器元素步长 **216 字节**。

### 24.5 已并入工程 **[已证实]**

`lcns/include/lcns/row.hpp`：新增 `row::orderedAddElement(records, scorer, node, value)`
（RE `0x137800`：追加 16 字节记录 + **重置缓存**），并把 `LazyScorer` 的注释
从"调用方须自己重置"改为"**追加器 `0x137800` 在每次插入时重置**"。
`test_row` 新增断言：追加后 `computed()` 变为 false，且分值随即由**新的末元素**决定。

### 24.6 仍未确认

* 源容器元素的**型别**（只知道步长 `0xd8 = 216` 字节）与 `0x134F70` 的作用。
* 第 4 实参 `r12` 的**类**（对它做 `[vptr+0x10]` 的虚调用）。
* `0x1331A0` 选中的两个子对象（`P+0x58` / `P+0x70`）各自的角色；`0x133DE0` 的四个实参含义。
* `0x5CEE50`、`0x5D38C0`、`0x5C4CD0`、`0x5C4CE0`。
* ⇒ 候选集的**生成过程**已能描述出骨架（选子对象 → 遍历 216 字节元素 → 虚调用 + 惰性分值 → 取优 → 追加），
  但**元素型别与虚调用目标未定**，故仍**不**以假定输入实现完整取最小算法。

---

## 25. 逐零件路径的**闭环**：角度 → 变换 → 旋转拷贝 → 包围盒 → 分值 → 取最小 **[本轮，已证实]**

### 25.1 `0x5CEE50`（527 B）= 角度索引 → **6 个 double 的变换** **[已证实]**

```
5CEE75  call 0x5C4CE0(element)               ; → 角度索引（定点度，scale 1e10）
5CEE7A  rdx = 0x9C5FFF26ED75ED55             ; ★ 与 0x1380D0 的 sin 块**同一个取模魔数**
5CEE87..5CEEAF  标准带符号除法序列：rdx = 角度 - (角度/360e10)*360e10
5CEE9B  rax = 0x34630B8A000                  ; = 360e10
5CEEB2  cmp/je 0x5CEFE0                      ; 角度 == 0
5CEEB8  cmp 0xD18C2E2800 ; je 0x5CF000        ; == 90e10
5CEECB  cmp 0x1A3185C5000 ; je 0x5CF020       ; == 180e10
5CEEDE  cmp 0x274A48A7800 ; je 0x5CF040       ; == 270e10
5CEEF1  一般路径： xmm6 = 角度 / [0x9DE950]=3.6e12 * [0x9DE958]=2π
5CEF0A  call cos → xmm9 ; 5CEF20 call sin → xmm8
5CEF2E  xorpd xmm7(=sin), [0x9DE960] = -0.0  ; ★ 取负且保持符号精确
5CEF36  写回： [out+0x00]=cos [out+0x08]=-sin [out+0x10]=sin [out+0x18]=cos
                [out+0x20]=0  [out+0x28]=0
5CEF59  call 0x5C4CD0(element)               ; → tag 字节；非 0 则走额外缩放分支
```

**四个精确分支**（各做 `pxor xmm6,xmm6` 以把 `+0x20/+0x28` 置 0）：

| 角度 | `xmm9` = cos | `xmm7` = −sin | `xmm8` = sin | 结果 `{cos,−sin,sin,cos}` |
|---|---|---|---|---|
| `0` | `1.0`（`0x9DE930`） | **`-0.0`**（`0x9DE948`） | `0` | `{1, -0, 0, 1}` |
| `90e10` | `0` | `-1.0`（`0x9DE940`） | `1.0` | `{0, -1, 1, 0}` |
| `180e10` | `-1.0` | **`-0.0`** | `0` | `{-1, -0, 0, -1}` |
| `270e10` | `0` | `1.0` | `-1.0` | `{0, 1, -1, 0}` |

⇒ 输出就是 **`{cosθ, −sinθ, sinθ, cosθ, 0, 0}`**（2×2 旋转 + 两个 0）。
**tag ≠ 0 的分支**（`0x5CEF5E` 起）在旋转之外再做额外缩放，**未译**，故工程只实现 tag = 0 路径。

### 25.2 `0x5D38C0`（1500 B）用该变换做**容器变换拷贝**

```
5D38E9  rbx = [rdx+8] - [rdx]                ; 源容器的字节数
5D38FB  rax = rbx >> 4 ; imul rax, 0xAAAAAAAAAAAAAAAB     ; ★ 元素大小 0x30 = 48
5D390B  [rcx]=0 [rcx+8]=0 [rcx+0x10]=0       ; out 是一个 vector
5D3949  operator new ; 5D395E 填 out 的 begin/end/cap
5D3969..5D39BA  逐元素（0x30 步长）拷贝/变换
```

⇒ `0x5D38C0(out, src48, transform)` = "把 `0x4F7600(part)` 的 **48 字节元素容器**按变换复制到 `out`"。

### 25.3 `0x134470` / `0x133DE0` 的**实参全部追清**

```
0x6AABC0: call 0x134470(rcx = rsp+0x190(=out), rdx = rsp+0x1b0, r8 = rsp+0x1d0, r9 = core+8)
          rsp+0x1b0 = 0x4F7600(part) 结果的拷贝（48 字节元素）
0x134470: rbp = rcx(out) ; rdi = rdx(那个缓冲) ; rsi = r8 ; r12 = r9(配置)
          循环元素 rbx ← 来自 rsp+0x70 的 16 字节元素向量（由 0x8BEFC0 填充）
              call 0x5C2E40(rsi, rbx)         ; ★ 授权谓词（记录表在 rsi，即 rsp+0x1d0 对象）
              if (!al) 跳过
              call 0x133DE0(rcx = rdi, rdx = rsi, r8 = rbx, r9 = r12)
              保留 xmm0 更小者
0x133DE0: rbx = arg1(48 字节缓冲) ; r13 = arg2 ; r12 = arg3(循环元素) ; rsi = arg4(配置)
          call 0x5CEE50(rsp+0x170, arg3)          ; 角度 → 变换
          call 0x5D38C0(rsp+0x40, arg1, rsp+0x170); 变换拷贝
          call 0x5CD800(rsp+0xE0, rsp+0x40)       ; 其包围盒
          高 × 20.0 → 0x1333D0(Item) + 0x136B80(Squeezer) → 惰性分值
```

### 25.4 语义闭环

```
0x4F7600(part)            → 48 字节元素的几何容器
  → (拷贝到 rsp+0x1b0)
  → 0x134470 遍历"候选角度元素"(16 字节，含 {tag, 角度})
       谓词 0x5C2E40      → 该角度**是否被授权**（记录表给出 [lo,hi] 区间）
       0x133DE0           → 授权则：变换(0x5CEE50) → 旋转拷贝(0x5D38C0) → 包围盒(0x5CD800)
                            → 20×高 → Item(0x1333D0) + Squeezer(0x136B80) → 惰性分值
       取最小             → 0x134470 结尾的 ucomisd/jbe
```

⇒ **`0x134470` 的语义 = "在（被授权的）候选角度中，挑出让该零件分数最小的那个"**
—— 一个**最优旋转搜索**。这解释了 §19 里"候选取最小"的真正含义。

### 25.5 已并入工程 **[已证实]**

`lcns/include/lcns/row.hpp` 新增三个**逐指令对应**的原语（不是近似）：

| RE | 工程 | 覆盖度 |
|---|---|---|
| `0x5C2E40`（授权谓词） | `row::AuthRecord{tag,lo,hi}` + `row::authorized(records, tag, value)` | **完全**：含两种区间极性、tag 匹配、空容器返回 false |
| `0x5CEE50` 的 tag = 0 路径 | `row::AngleTransform` + `row::angleTransform(fixedAngle)` | **完全**：四个精确角（含**符号精确的 `-0.0`**）、一般路径、`%360e10` 回绕 |
| `0x134470` 的循环 | `row::CandidateElement{identity,tag,angle}` + `row::bestCandidate(elements, records, scoreFn, &best)` | **控制流完全**：谓词过滤、取最小、全被拒时返回 −1 |

**唯一注入点（明示）**：分值计算以 `ScoreFn` 注入，因为其几何步 `0x5D38C0`（1500 B）
**未译**。这一点在头文件注释里写明"the score itself is injected because its geometry step
(0x5D38C0, 1500 bytes) is not translated"——**没有**用我的 `geom::` 旋转去冒充它。

测试：`test_row` 覆盖谓词（含反向区间与空表）、变换（四个精确角 + 一般路径 + 回绕 +
`signbit(-0.0)`）、取最小（跳过被拒项、并列取先者、全拒返回 −1）。

### 25.6 仍未确认

* `0x5D38C0` 的**主体**（1500 B）：变换的具体应用方式。
* `0x5CEE50` 的 **tag ≠ 0 分支**（额外缩放）。
* `0x5C4CD0` / `0x5C4CE0`（元素的两个取值器：tag 与角度）—— 目前只由**使用方式**推定其语义。
* `0x8BEFC0`（填充"候选角度元素"向量的那个例程）与 `0x133DE0` 的 arg2（`rsp+0x1d0` 对象）的角色。
* ⇒ 因此工程里的 `bestCandidate` 是**控制流层面的等价实现**，
  一旦 `0x5D38C0` 与 `0x8BEFC0` 译出，即可把 `ScoreFn` 换成真正的几何计算而无需改动循环。

---

## 26. 注入点填空：元素型别坐实 + 变换算术译出 **[本轮，已证实]**

### 26.1 两个取值器坐实 → **16 字节元素的型别确定** **[已证实]**

```
5C4CD0   movzx eax, byte ptr [rcx]      ; ★ element + 0x00 = tag（1 字节）
5C4CE0   mov rax, qword ptr [rcx + 8]   ; ★ element + 0x08 = 角度（8 字节，定点度）
5C5F50   mov rax, rcx ; ret             ; 恒等
5C61D0   mov rax, rcx ; ret             ; 恒等
```

⇒ `0x134470` 循环里的元素就是 **16 字节 `{ u8 tag@0 ;（填充/其它）; int64 angle@+8 }`**
——**与 §25.5 里建模的 `row::CandidateElement{tag, angle}` 完全一致**（此前只是由用法推定，
现在由取值器本身证实）。

### 26.2 `0x5D38C0` 的**变换算术**译出 **[已证实]**

两处**完全相同**的代码块（`0x5D3BA8` 与 `0x5D3C90`），用 `rdi` 处那 6 个 double
`{+0x00 cos, +0x08 −sin, +0x10 sin, +0x18 cos, +0x20 tx, +0x28 ty}`：

```
5D3BC0  xmm0 = [rcx+8]            ; y
5D3BD2  xmm1 = [rcx-0x10]         ; x
5D3BD7  xmm2 = cos * y
5D3BDB  xmm3 = sin * x
5D3BE8  xmm2 += xmm3 ; 5D3BEC xmm2 += [rdi+0x28]      ; + ty
5D3BFA  [rcx-8] = xmm2                                ; y' = sin*x + cos*y + ty
5D3BDF  xmm0 *= -sin
5D3BE4  xmm1 *= cos
5D3BF1  xmm0 += xmm1 ; 5D3BF5 xmm0 += [rdi+0x20]      ; + tx
5D3BFF  [rcx-0x10] = xmm0                             ; x' = cos*x - sin*y + tx
5D3C09  xmm4 = cos*cos ; 5D3C0E xmm5 = sin*(-sin) ; 5D3C13 xmm4 -= xmm5
5D3C17  ucomisd xmm6(=0), xmm4                        ; ★ 行列式 cos² + sin² 的校验
```

⇒ **`0x5D38C0` = 把源点按 `{cos,−sin,sin,cos,tx,ty}` 做仿射变换**（并校验行列式）。
这与 `0x5CEE50` 产出的 6 个 double **布局一致**；`tx`/`ty`（`+0x20`/`+0x28`）在
tag = 0 路径上恒为 0。

### 26.3 "高"的定义：变换后点的 **Y 跨度**

`0x133DE0` 在变换之后调 `0x5CD800` 取包围盒；该包围盒的逐项 min/max 由
**`0x5C8C50`** 完成（§14.2 已译：`if (xmm1 > xmm0) [rcx+8] = xmm0` 一类）。
⇒ 候选的"高" = **变换后所有点的 `maxY − minY`**，"宽" = `maxX − minX`，
再把 **`20 × 高`** 交给 `Row::Squeezer` 构造器（`0x133E67`）。

### 26.4 已并入工程 **[已证实]**

`lcns/include/lcns/row.hpp` 新增（均逐指令对应，附上面每一条的 RVA）：

| RE | 工程 |
|---|---|
| `0x5D3BFF` / `0x5D3BFA` | `row::transformX()` / `row::transformY()` |
| `0x5D3C09..0x5D3C17` | `row::transformDet()` |
| `0x5D38C0` + `0x5C8C50` 的 min/max | `row::transformedHeight()` / `row::transformedWidth()` |
| `0x5C4CD0` / `0x5C4CE0` | `row::CandidateElement::tag`(@+0) / `angle`(@+8)（注释已改成"已由取值器证实"） |

`test_row` 新增断言：90° 把 `(1,0)` 转到 `(0,1)`、把 `(0,1)` 转到 `(−1,0)`；
四个分支的行列式都等于 1；一个 2×1 矩形未旋转时高 2/宽 1，旋转 90° 后高 1/宽 2；
以及 `candidateSqueezerArg(transformedHeight(...))` = 40。

### 26.5 注入点**收窄**（明示）

上一轮把"整个几何步"作为注入点；本轮之后，**`Row::Squeezer` 的构造实参已完全可算**：

```
angleTransform(元素.angle)              ← 完全（§25.1）
transformedHeight(points, t)            ← 完全（§26.2 + §26.3）
candidateSqueezerArg(height) = 20*height ← 完全（§14.1）
```

仍然**未译**的是 `Squeezer` 之后那条**分值装配**：
`0x1333D0`(Item) → `0x136B80`(Squeezer) → `0x136CB0`(惰性分值) → `0x137A90`(合并)
→ `0x137800`(追加)。⇒ 注入点从"几何"收窄为"**Squeezer 之后的分值装配**"，
而 `bestCandidate` 的循环、谓词、取最小**无需改动**。

### 26.6 仍未确认

* `Squeezer` 之后的分值装配（见上）。
* `0x5CEE50` 的 **tag ≠ 0 分支**（额外缩放）。
* `0x8BEFC0`（填充"候选角度元素"向量者）与 `0x133DE0` 的 arg2（`rsp+0x1d0` 对象）的角色。
* 48 字节元素内部**点的确切偏移**（变换读 `[rcx-0x10]`/`[rcx+8]`，随 `rcx` 的遍历基点而定）。

---

## 27. 分值装配链的**控制流**译出（`0x133DE0` 全貌 + `0x137FE0` 排空环） **[本轮，已证实]**

### 27.1 `0x133DE0` 的**完整链条** **[已证实]**

把 §21/§25/§26 的碎片按地址拼起来：

```
0x133DE0(element, buffer48, arg2, cfg = core+8):
  133E20  0x5CEE50(rsp+0x170, element)        ; ★ 角度 → 变换 {cos,-sin,sin,cos,0,0}
  133E2E  0x5D38C0(rsp+0x40, buffer48, rsp+0x170)   ; ★ 变换拷贝 48 字节元素容器
  133E3E  0x5CD800(rsp+0xE0, rsp+0x40)        ; ★ 包围盒（min/max 由 0x5C8C50）
  133E55  xmm6 = [rsp+0xF8] - [rsp+0xE8]      ;   高 = maxY - minY
  133E67  xmm6 *= 20.0 ([0x9BCEB0])           ; ★ 20 × 高
  133E96  0x1333D0(..., edx = 0, ...)         ; ★ 造 Item（partIndex = 0）
  133EF7  0x136B80(&squeezer@rsp+0x30, xmm1 = 20×高, xmm2 = cfg[+0x18], xmm3 = cfg[+0x10])
  133F1E  0x137FE0(obj@rsp+0x110, rsp+0x60)   ; ★ 排空源记录 → 候选记录（见 27.2）
  133F26  0x136D30(squeezer)                  ;   读两级标志（0x136D30）
  133F2D  xmm0 = cfg[+0x00] ; 133F31 xmm1 = cfg[+0x08]
  133F47  0x136CB0(obj, xmm0, xmm1)           ; ★ 惰性分值（§22.3）
  133F53  0x136CA0(obj)                       ;   容器计数（整数，不碰 xmm0）
  ...     清理（全部整数/指针操作，不破坏 xmm0）
  1342D4  ret                                 ; ★ 返回值 = 0x136CB0 留在 xmm0 的 double
```

**源码路径**（`0x133DE0` 的内联断言串）：含 `..\row\` 与 `_par`/`ow.c` 片段与
**`"orderedAddElement"`** 的邻居串，指向 `..\row\` 下的 row 相关翻译单元。

### 27.2 **`0x271000000000` 解读完成**：源记录布局 = `{void* @0, u8 tag @8, u32 count @0xc}`

`0x133DE0` 建的那个"容器"只有**一个元素**，该元素在 `0x133EC9`/`0x133EE9` 被写成
`{ [rax] = rdi（变换指针）, [rax+8] = 0x271000000000 }`。把立即数**按字节拆开**：

```
0x271000000000 → LE 字节: 00 00 00 00 10 27 00 00
   byte [+0x08] = 0x00
   u32  [+0x0c] = 0x00002710 = 10000        ★★ 就是 0x137FE0 读的那个 count
```

⇒ 源记录是 **16 字节 `{ void* source @+0x00 ; u8 tag @+0x08 ; u32 count @+0x0c }`**，
`0x133DE0` 传的那条 count = **10000**（一个排空上限）。
这**结清了 §21.4 遗留的"立即数字段切分未定"**。

### 27.3 `0x137FE0`（177 B）的**排空环** **[已证实]**

```
137FF8  call 0x136C00(rcx)                 ; 初始化目标对象（+0x50 = -1.0，见 §22.1）
137FFD  rbx = [rsi] ; 138000 rdi = [rsi+8] ; 138004 if (begin == end) return rbp
逐记录（0x10 步长）:
138010  esi = dword [rbx+0x0c]             ; 记录的 count
138013  if (esi == 0) → 下一条             ; ★ count 为 0 的记录**整条跳过**
138040  edx = byte [rbx+0x08]              ; tag
138052  rcx = [rbx]                        ; source
138055  al = 0x137A90(rcx, edx, rbp, r12)  ; ★ 合并（每次最多产出一个候选）
13805A  if (al == 0) → 下一条              ; ★ 合并报"没有了"
13805E  --esi ; if (esi == 0) → 下一条      ; ★ 到达上限
138063  jmp 0x138040                       ; ★ 否则**重试同一条**
138029  return rbp                          ; 返回目标对象
```

⇒ **`0x137FE0(obj, records, r12)` = 初始化 obj，然后对每条记录反复调用合并
（最多 `count` 次，合并返回 0 即提前结束，count 为 0 则跳过）**，
把候选逐个 `orderedAddElement` 进 obj。

### 27.4 已并入工程 **[已证实]**

| RE | 工程 |
|---|---|
| `0x271000000000` 的 `[+0xc] = 10000` | `row::kSourceRecordCap = 10000` |
| 源记录 16 字节布局 | `row::SourceRecord{source, tag, count}` |
| `0x137FE0` 的排空环（含"count==0 跳过"、"合并返回 0 提前结束"、"重试同一条"） | `row::drainSources(records, mergeFn)`（`mergeFn(source, tag) -> bool`） |

`test_row` 断言：`kSourceRecordCap == 10000`；count 为 0 的记录被跳过；
上限恰好等于 count；合并提前返回 false 时立即停止；count = 1 时只调一次；
`source`/`tag` 原样传到合并函数。

### 27.5 注入点**再次收窄**

现在 `0x133DE0` 的链条上，**除 `0x137A90` 的合并本体**外全部译出：

```
角度变换        0x5CEE50   ✓ 完全（§25.1）
仿射变换        0x5D38C0   ✓ 算术完全（§26.2）
包围盒 min/max  0x5C8C50   ✓ 完全（§14.2）
20 × 高         0x133E67   ✓ 完全（§14.1）
Item 构造       0x1333D0   ✓ 布局完全（§18.1）
Squeezer 构造   0x136B80/0x138A20 ✓ 完全（§12.1）
排空环          0x137FE0   ✓ 完全（§27.3）
惰性分值        0x136CB0   ✓ 完全（§22.3）
记录追加        0x137800   ✓ 完全（§24.1）
合并本体        0x137A90   ✗ 仅结构（§24.4）—— 缺 216 字节元素型别 + 对 r12 的虚调用目标
```

⇒ 注入点只剩**一个**：`0x137A90` 的合并本体。一旦它的**源容器元素型别（216 字节）**
与**虚调用目标 `r12` 的类**确定，整条链即可端到端落地，
而 `bestCandidate` / `drainSources` / `candidateScore` / `orderedAddElement` 均**无需改动**。

### 27.6 仍未确认

* `0x137A90` 的源容器元素型别（步长 `0xd8` = 216 字节已知）与其第 4 实参 `r12` 的类。
* `0x8BEFC0`（填充"候选角度元素"向量者）。
* `0x133DE0` 的 arg2（`rsp+0x1d0` 对象）与 arg1（48 字节缓冲）在链条中的确切角色分工。
* `0x5CEE50` 的 tag ≠ 0 分支。

---

## 28. ABI 纠正 + Item 的两个容器 + **216 字节元素布局经构造器证实** **[本轮，已证实]**

### 28.1 **ABI 纠正**：`0x5CD800` **保留 `rdi`**，§27.1 的 `source` 就是**那个 Item** **[已证实]**

上一轮我一度怀疑 `0x5CD800` 会破坏 `rdi`。事实是**这是 Windows x64 ABI（`rdi` 为 callee-saved）**，
而 `0x5CD800` 的序/尾声正是：

```
5CD800  push r12 ; push rbp ; push rdi ; push rsi ; push rbx ; sub rsp,0xa0
5CD80D  mov rdi, rcx
...     （尾声）add rsp,0xa0 ; pop rbx ; pop rsi ; pop rdi ; pop rbp ; pop r12 ; ret
```

⇒ **`rdi` 被保存并恢复**，所以 `0x133DE0` 里 `0x133E3E call 0x5CD800` 之后
`rdi` 仍是 **`rsp+0x170`**，于是：

```
133EC9  [rax] = rdi               ; ★ 容器记录的 source = rsp+0x170
133E93  mov rcx, rdi              ; ★ 0x1333D0 的 this = rsp+0x170
```

⇒ **同一段栈区 `rsp+0x170` 先当"角度变换"（6 个 double），在被 `0x5D38C0` 用掉之后
又被当作 Item（0x90 字节）复用** —— 这是一个**栈临时对象复用**，不是两个对象。
因此 §27.2 那条源记录的 `source` 是 **`Item`**，而不是"变换指针"。

### 28.2 `Item+0x58` / `Item+0x70` = **两个 216 字节元素容器** **[已证实]**

```
1336F8  写 [r14+0x58]=0 [r14+0x60]=0 [r14+0x68]=0     ; 容器 A 的 begin/end/cap
133710  写 [r14+0x70]=0 [r14+0x78]=0 [r14+0x80]=0     ; 容器 B 的 begin/end/cap
13372F  写 byte [r14+0x88] = 0
1339C1/1339FD/133A37/133A71  [r14+0x78] = rcx         ; 反复提交容器 B 的 end
133AA8/133ADF/133B16/133B5D  [r14+0x60] = rcx         ; 反复提交容器 A 的 end
```

（`0x1336F8` 与 `0x13372F` 同属那个 0x90 字节 Item 的初始化序列，见 §18.1 的 `0x1333D0`。）

而 `0x1331A0(Item, dl)` = `dl ? Item+0x70 : Item+0x58`（已核实）。
⇒ **`Item` 的布局补齐**：

```
Item (0x90 = 144 字节):
  +0x00 int              partIndex
  +0x08 vector<Elem48>   （+0x08/+0x10/+0x18）
  +0x20 子对象           （0x1333C0 = Item+0x20；其 +0x10/+0x18 = Item+0x30/+0x38 是两个 double）
  +0x58 vector<Elem216>  A（+0x58/+0x60/+0x68）   ← 0x1331A0 的 tag == 0 分支
  +0x70 vector<Elem216>  B（+0x70/+0x78/+0x80）   ← tag != 0 分支
  +0x88 u8
```

⇒ `0x137A90` 的 `add rbx, 0xd8`（**216 字节步长**）正是遍历这两个容器之一。

### 28.3 **216 字节元素的构造器 `0x136350`**，其偏移与我建的 `ScoreNode` 完全一致 **[已证实]**

六处调用点都是同一形状：

```
133A61  call 0x136350(元素槽, rdx = r14(Item), r8 = 源)
133A6A  add rcx, 0xd8                      ; ★ 216
133A71  [r14+0x78] = rcx                   ; 提交 end
```

`0x136350`（1920 B）的**开篇即把元素布局写全**：

```
136371  [rcx+0x00] = rdx                   ; ★ 一个指针（Item）
13637B  [rcx+0x08] = [r8]                  ; ★ 源容器 begin
136388  [rcx+0x10] = [r8+8]                ; ★ 源容器 end
13637F  byte [rcx+0x18] = 1                ; ★ 退化标志，**初值 1**
136383  [rcx+0x20] = [rcx+0x28] = [rcx+0x30] = [rcx+0x38] = 0.0
1363FE  call 0x5CD800(rsp+0x20, rsp+0x50)  ; 包围盒
136403..13642F  把它的 5 个 qword（bool + 4 double）拷到 [rbx+0x18 .. +0x38]
136433  call 0x1333C0(rdi) ; 13643E call 0x134D70(rsp+0x50, rax) → al
13644B  byte [rcx+0x40] = al               ; ★ flag40
13645B  call 0x5CE7F0(rsp+0x150, 0x1A3185C5000)     ; ★ 用 **180 度**构造变换
136471  call 0x5D38C0(rsp+0xb0, rsp+0x50, rsp+0x150) ; 再变换一次
136484  call 0x134D70(...) → al
136489  byte [rcx+0x41] = al               ; ★ flag41
13639B  byte [rcx+0x48] = 0 ; 13639F byte [rcx+0x70] = 0   ; 两个可选槽的 presence
1363A3..1363DA  +0xa8/+0xb0/+0xb8 与 +0xc0/+0xc8/+0xd0 清零（两个容器）
```

⇒ **`ScoreNode` 的字段顺序就是二进制的字段顺序**（此前是由访问器**推出**的，现在由**构造器**证实）。
同时新增两条语义：

* 元素**存着一个被 180° 变换过的容器**（`0x13645B` 用 `0x1A3185C5000 = 180e10` 建变换后
  `0x5D38C0` 再变换一次）—— 即"镜像朝向"也在元素里；
* 两个标志 `+0x40`/`+0x41` 都来自 **`0x134D70(容器, Item+0x20)`**。

### 28.4 已并入工程：**编译期锁死布局** **[已证实]**

`lcns/include/lcns/row.hpp`：

* `ScoreNode` 补上两个前导字段 `owner`(`+0x00`)、`sourceBegin`(`+0x08`)、`sourceEnd`(`+0x10`)
  ——**这是静态断言直接抓出来的缺陷**（原结构缺这三格，导致其后所有偏移错位）；
* 新增 `static_assert` **15 条**：`sizeof(ScoreNode) == 0xd8` 以及
  `offsetof` 对 `+0x18/+0x20/+0x28/+0x30/+0x38/+0x40/+0x41/+0x48/+0x70/+0x98/+0x99/+0xa0/
  +0xa8/+0xc0` 的逐一校验。**任何人重排或改宽该结构，编译立即失败。**
* 新增 Item 常量：`kItemSize = 0x90`、`kItemContainerA = 0x58`、`kItemContainerB = 0x70`、
  `kItemSubObject = 0x20`，以及 `itemContainerOffset(bool)`（= `0x1331A0`）。

`test_row` 另加运行时断言（`sizeof`、Item 尺寸、两个容器偏移、`0x1331A0` 的选择）。

### 28.5 仍未确认

* **`0x137A90` 的合并本体**：现在已知它的源容器是 `Item+0x58`/`Item+0x70`
  （216 字节元素、元素布局已由构造器证实），仍缺的是它对**第 4 实参 `r12` 的虚调用 `[vptr+0x10]`**
  所指向的类。
* `0x136350` 内部其余调用：`0x1355C0`、`0x134D70`、`0x135040`、`0x135780`、`0x5CE7F0`、
  `0x5CF6B0`、`0x135C70`、`0x8C4FF0`。
* `0x8BEFC0`；`0x133DE0` 的 arg1（48 字节缓冲）与 arg2 的角色分工。

---

## 29. **注入点闭合**：那个虚调用就是 `Squeezer::cost` **[本轮，已证实]**

### 29.1 虚表解析 + 一处**槽位编号纠正**

`0x137A90` 在 `0x137C0C` 做 `call qword [rax + 0x10]`（`rax = [r12]` = 虚表指针）。
把 `Row::Squeezer` 的地址点 `0xA3B1F0` 处的表读出来：

| 表项 | 目标 |
|---|---|
| `+0x00`（slot 0） | `0x138BE0`（185 B，D1 析构） |
| **`+0x10`（slot 1）** | **`0x13A360`（221 B）** ← **就是被调用的那个** |
| `+0x20`（slot 2） | `0` |
| `+0x30`（slot 3） | `0x679250` |
| `+0x40`（slot 4） | `0x7CA820` |
| `+0x50`（slot 5） | `0` |
| `+0x60`（slot 6） | `0x679270` |
| `+0x70`（slot 7） | `0x60B330` |

同一张表在 `Row::BasicDistancer`（地址点 `0xA3B1C0`）上整体后移 3 项
（`0x138BE0` 出现在它的 `+0x30`）—— 与 §12/§13 的继承关系一致。

**纠正**：我在 §12/§13 里把 `0x13A360` 称作"Squeezer 的 slot 2"，
那是**从虚表基址数**的；而代码里的 `[vptr+0x10]` 对应**从地址点数**的 **slot 1**。
两种数法差一格，本轮以代码为准。

### 29.2 `r12` = **`Row::Squeezer`**，故该虚调用 = `Squeezer::cost(lo, hi)` **[已证实]**

```
137BF5  test rbp, rbp ; je 0x137DA0       ; rbp = 对象内已存的**最后一条记录**（或 0）
137BFE  rax = [r12]                        ; 虚表指针
137C05  rcx = r12                          ; this
137C08  rdx = [rbp]                        ; ★ arg2 = 那条记录里的 **node 指针**
137C02  r8  = rbx                          ; ★ arg3 = 当前 **216 字节元素**
137C0C  call [rax + 0x10]                  ; ★ = 0x13A360 = Squeezer 的**记忆化代价**
```

而 `0x13A360`（§13 已译）的签名正是 `(this, lo, hi)`：
在 `+0x248` 的树上按键 `(lo, hi)` 查，命中即返回 `node[+0x30]`；
未命中则调 `0x1380D0(&result, obj = [this+8], lo, hi)` 求值并插回。

⇒ **`0x137A90` 的"合并"就是：以「已存最后一条记录的 node」为 `lo`、"当前元素"为 `hi`，
调用 `Row::Squeezer::cost`** —— 也就是我第 2–3 轮译出、并已在工程里实现的
`row::Squeezer::cost` / `row::squeezeCost`。**注入点到此闭合。**

### 29.3 该代价之后的**最终算术** `0x137BF0..0x137C83` **[已证实]**

```
137C0F  xmm8 = xmm0                        ; 挤压代价
137C14  if (rdi == 0) goto 0x137C4F        ; rdi = 对象的 vector 元素（上一次留下的临时）
137C19  call 0x136CB0(obj)                 ; 对象的惰性分值 → xmm0
137C21  xmm6 = [rdi+8]                     ; 记录的值
137C32  call 0x134F30([rdi]) ; 137C37 xmm6 += xmm0     ; + 该 node 的 X 跨度
137C29  xmm7 = xmm0 + xmm8                 ; = 惰性分值 + 挤压代价
137C3B  xmm6 += xmm10                      ; + [P+0x38]
137C40  ucomisd xmm6, xmm7 ; jbe 0x137C4F  ; ★ a <= b 则跳过
137C46  xmm6 -= xmm7 ; 137C4A xmm8 += xmm6 ; ★ 否则把超出部分并入代价
137C57  call 0x135030(element)             ; = element[+0xa0]
137C63  call 0x136D10(obj)                 ; = obj[+0x08]
137C76  divsd xmm6, xmm0                   ; ★ 比值
137C83  subsd xmm6, xmm0                   ; ★★ score = 代价 − 比值
```

### 29.4 已并入工程 **[已证实]**

`lcns/include/lcns/row.hpp` 新增 `row::elementScore(...)`，把上面 `0x137BF0..0x137C83`
的算术**逐指令**写成函数（参数按来源寄存器/字段命名，注释给出每条指令）。
`test_row` 断言：

* **两条分支都测**：`a > b` 时代价吸收超出（`2 + (6−3) − 10/2 = 0`），
  `a <= b` 时代价不变，且 `a == b` 也走 `jbe` 分支（与指令一致）；
* **端到端**：2×1 矩形 + 90° 候选 ⇒ `angleTransform` → `transformedHeight = 1`
  → `candidateSqueezerArg = 20` → 用两个 `ScoreNode`（其 `+0x48`/`+0x70` 槽即 Squeezer 读的槽）
  建 `SqueezeContext` ⇒ `Squeezer::cost` 给出 `20/1 − 0 = 20`，
  且这一次**被缓存**（`entries() == 1`）；槽缺席时则不适用且**不缓存**。

⇒ 目标的 ③ 由"控制流等价 + 单点注入"升级为"**整链条等价**"：
`0x134470` 的谓词、取最小、排空、记录追加、惰性分值、挤压代价、最终算术
**全部是逆出原语的组合**，不再有占位注入。

### 29.5 仍未确认

* `0x134D70`（元素 `+0x40`/`+0x41` 两个标志的计算）。
* `0x135030` / `0x136D10` 语义（分别读 `node[+0xa0]` 与 `obj[+0x08]`，构成最终比值的分母/分子）——
  数值来源已知，**用途命名未定**。
* `0x136350` 内部其余调用：`0x1355C0`、`0x135040`、`0x135780`、`0x5CE7F0`、`0x5CF6B0`、
  `0x135C70`、`0x8C4FF0`。
* `0x8BEFC0`（填充"候选角度元素"向量者）；`0x133DE0` 的 arg1（48 字节缓冲）与 arg2 的角色分工。

---

## 30. 逐零件路径的**收尾清单**（本目标的唯一缺口清单）

本节把本目标（逐零件路径）范围内出现过的"未确认 / 未译"全部收敛，逐条给出**状态**、
**原因**与**影响**。所有条目**都没有用近似值顶替**。

### 30.1 已结案（全部译出并已入工程）

| # | RE | 工程 | 覆盖度 |
|---|---|---|---|
| 1 | `0x5C4CD0` / `0x5C4CE0` | `CandidateElement::tag`(@+0x00) / `angle`(@+0x08) | **完全**（各 2 条指令） |
| 2 | `0x5C2E40` 授权谓词 | `row::authorized` | **完全**（两种区间极性、tag 匹配、空表 false） |
| 3 | `0x5CEE50`（tag = 0 路径） | `row::angleTransform` | **完全**（四个精确角含符号精确 `-0.0`、一般路径、`%360e10` 回绕） |
| 4 | `0x5D38C0` 的仿射算术 | `row::transformX/Y/Det` + `transformedHeight/Width` | **算术完全**（`cos²+sin²` 行列式校验） |
| 5 | `0x133E67` 的 `20 × 高` | `row::candidateSqueezerArg` | **完全**（rodata `0x9BCEB0`） |
| 6 | `0x1333D0` Item 构造（含两个 216 字节容器槽） | `kItemSize`/`kItemContainerA/B`/`kItemSubObject`/`itemContainerOffset` | **布局完全**（由 `0x1336F8`/`0x133710` 的六连清零证实） |
| 7 | `0x136350` 元素构造 | `row::ScoreNode`（**15 条 `static_assert` 锁定偏移**） | **布局完全**（`sizeof == 0xd8` + 逐 `offsetof`） |
| 8 | `0x134F30`/`0x134F50`/`0x134F90`/`0x135010` | `nodeLength`/`nodeLengthY`/`nodeFlag40`/`nodeFlag98` | **完全** |
| 9 | `0x136CB0` 惰性分值 | `row::candidateScore` + `row::LazyScorer` + `orderedAddElement` | **完全**（含"只在缓存恰为 `-1.0` 时重算"） |
| 10 | `0x137FE0` 排空环 + `0x271000000000`(=count 10000) | `row::drainSources` + `kSourceRecordCap` | **完全** |
| 11 | `0x137800` 追加器（方法名 `orderedAddElement`） | `row::orderedAddElement` | **完全**（16 字节 `{ptr, double}` + 重置缓存） |
| 12 | `0x13A360`（`Row::Squeezer` slot 1） | `row::Squeezer::cost`（此前已译） | **完全**（命中判据 + 未命中求值并插回） |
| 13 | `0x1380D0` 挤压代价 | `row::squeezeCost` | **完全**（公式 + 平行闸 + `0.005` 对齐闸） |
| 14 | `0x137BF0..0x137C83` 最终算术 | `row::elementScore` | **完全**（两条分支，含 `a == b` 走 `jbe`） |
| 15 | `0x134470` 取最小循环 | `row::bestCandidate` | **完全**（谓词过滤、取最小、全拒返回 −1） |

⇒ **从"候选角度元素"到"最终分值"的整条链，全部是逆出原语的组合，没有占位注入。**

### 30.2 仍未确认（附原因与影响）

| 项 | 原因（可复核） | 影响 |
|---|---|---|
| `0x134D70`（元素 `+0x40`/`+0x41` 两个标志的计算） | 未译；只知它被调用两次（`0x13644B`/`0x136489`），入参是「容器」与「`Item+0x20`」 | 小：两个标志的**读取**已译（`0x134F90`），只是**产生**未译 |
| `0x135030` / `0x136D10` 的**角色命名** | 未译其语义；但**数值来源已确定**：分别读 `node[+0xa0]` 与 `obj[+0x08]`，构成 `0x137C76` 那个比值的分子/分母 | 极小：数值通路已在 `elementScore` 中如实实现，只是"这两个数叫什么"未定 |
| `0x136350` 内部的 `0x1355C0`/`0x135040`/`0x135780`/`0x5CE7F0`/`0x5CF6B0`/`0x135C70`/`0x8C4FF0` | 未译 | 中：元素的**内部几何**（除包围盒与一次 180° 变换外）未完全展开；但元素的**布局**已编译期锁定 |
| `0x8BEFC0`（填充"候选角度元素"向量者） | 未译 | 中：**角度集合从哪来**未定；`bestCandidate` 已按逆出结构接受该集合为输入 |
| `0x133DE0` 的 arg1（48 字节缓冲）与 arg2（`rsp+0x1d0`）的**角色分工** | 未译；只知 arg1 是 `0x4F7600(part)` 结果的拷贝、arg2 是谓词 `0x5C2E40` 的记录表 | 小：两者的**用法**已在链中定位（变换拷贝的源 / 授权记录表），只是**构造者**未追 |
| `0x5CEE50` 的 **tag ≠ 0 分支**（额外缩放） | 未译 | 小：tag = 0 路径（也是 `0x133DE0` 传的那条，`byte[rec+8] = 0`）已完全实现 |

### 30.3 与目标条款的对照

| 目标条款 | 状态 |
|---|---|
| ① 译出 `0x5C2E40` 与 `0x133DE0` | **是**：谓词完全；`0x133DE0` 全链十环节全部译出（§27.1） |
| ② 弄清三层字段语义与生产者-消费者关系 | **是**：`Item`(0x90)/`Elem48`(0x30)/`Elem16`(16) 的尺寸与嵌套、两套对象布局、**`ScoreNode` 布局编译期锁定** |
| ③ 按逆出结构实现候选取最小 | **是**，且为**整链条等价**（无注入点，见 §30.1 的 15 项） |
| ④ 地址级证据 + 不可恢复明说 | **是**：每个原语在代码中带 RVA 注释；残留项见 §30.2，逐条给出原因与影响 |
| ⑤ 零警告 / 全测 / 文档同步 | **是**：见下节验收记录 |

---

## 31. 候选角度的**来源**结案（§30.2 第 ① 项） **[本轮，已证实]**

### 31.1 `0x5C4C50` **只有 4 条指令**：它是"写一个元素"，不是"生成一组角度" **[已证实]**

```
5C4C50  mov rax, qword ptr [r8]      ; arg3 指向角度
5C4C53  mov byte ptr [rcx], dl       ; ★ element[+0x00] = tag
5C4C55  mov qword ptr [rcx + 8], rax ; ★ element[+0x08] = 角度
5C4C59  ret
```

⇒ **`0x5C4C50(element, tag, anglePtr)` 写一个 `{tag, angle}` 元素**。
这与 §26.1 由取值器确定的元素型别（`tag@+0x00`、`angle@+0x08`）**互为印证**。

### 31.2 `0x8BEFC0`（308 B）= **拷贝源容器 + 追加一个元素** **[已证实]**

```
8BEFCC  r11 = [rcx+8] ; rbp = [rcx]         ; 源容器的 end/begin
8BEFD9  r12 = rdx                            ; arg2 = 指向 tag 的指针
8BEFDF  r13 = r8                             ; arg3 = 指向角度的指针
8BEFE2  rdi = (end - begin) >> 4             ; 元素个数（16 字节元素）
8BF015..8BF018  operator new(...)            ; 新缓冲
8BF032  edx = byte [r12]                     ; ★ tag = *arg2
8BF037  r8 = r13 ; 8BF03A call 0x5C4C50      ; ★ 在新缓冲的"追加位"写一个元素
8BF04B..8BF06F  逐元素（0x10 步长）把源拷到新缓冲开头
8BF092  [vec+0x00] = 新缓冲(begin)
8BF098  [vec+0x08] = 新缓冲 + 拷贝字节 + 0x10 + 0x10     ; ★ end = 源元素 + 追加的那一个
8BF09C  [vec+0x10] = 新缓冲 + 分配尺寸(cap)
8BF085..8BF08D  释放旧缓冲（若非空）
```

⇒ `0x8BEFC0(vec, tagPtr, anglePtr)` = **"源容器元素 + 一个 `{*tagPtr, *anglePtr}`"**。

### 31.3 `0x134470` **自己的准备段** + 追加 90° 元素 ⇒ 候选集的真正构成 **[已证实]**

```
1344C5  [rsp+0x70] = [rsp+0x78] = [rsp+0x80] = 0        ; 空 vector
1344E2  byte [rsp+0x3f] = 0                             ; tag = 0
1344F3  [rsp+0x40] = 0                                  ; 角度 = 0
1344FC  call 0x8BEFC0(rsp+0x70, rsp+0x3f, rsp+0x40)     ; ★ 源元素 + {tag 0, 0°}
134506  byte [rsp+0x3f] = 0                             ; tag = 0
13450B  rax = 0xD18C2E2800                              ; ★ = 90 度
13451D  [rsp+0x40] = rax
134515  if (end == cap) goto 0x13466F                   ; 需要扩容
13452D  r8 = rbx ; edx = 0 ; 134532 call 0x5C4C50(end, 0, rsp+0x40)   ; ★ 再追加 {tag 0, 90°}
13453C  rcx += 0x10 ; 134540 [rsp+0x78] = rcx           ; 提交新的 end
```

⇒ **`0x134470` 搜索的候选集 = 「源容器自带的元素」+「0°」+「90°」，tag 全为 0。**
即"**先按零件自带的角度试，再试轴对齐的 0° 与 90°**"。这**结清了 §30.2 第 ① 项**:
"角度集合从哪来"的答案是**它自己的元素表 + 两个轴对齐角**，不是某个未译的黑箱。

### 31.4 `0x134D70`（437 B）的结构 **[部分证实]**

```
134DAB  call 0x5CD800(rsp+0x20, rsi)        ; ★ arg1 的包围盒
134DB8  xmm10 = [rbx]                        ; arg2 的两个 double
134DC5  xmm7  = [rsp+0x40]                   ; 包围盒的某个 double
134DD0  xmm10 = max(xmm10, [rbx+0x10])
134DD6  xmm9  = max([rbx], [rbx+0x18])
134DDC  call 0x5C61D0(rsi) ; 134DE1 取 {begin,end} 并遍历
134DF1  xmm8 = [0x9BCED0] = NaN              ; ★ 又是 **fabs 掩码**（与 §24.3 同源）
134DFF  xmm6 = [0x9BCEE0] = 1e-06            ; ★ 容差
134E10  循环体： 0x5C5F30 / 0x5C5260 → 取该元素末两个 double
134E40  xmm0 = xmm7 - xmm10 + 1e-06 ; 134E4D ucomisd xmm0, xmm1   ; ★ 容差比较
...
```

⇒ `0x134D70(container, node)` = **一个几何容差谓词**：取包围盒 → 用 `1e-06` 与 fabs 掩码
逐元素做容差比较 → 返回一个 **bool**（即元素 `+0x40`/`+0x41` 两个标志的来源）。
**完整谓词表达式未逐条转写**（101 条指令，含多层分支），故仅记结构，**不写入工程**。

### 31.5 已并入工程 **[已证实]**

| RE | 工程 |
|---|---|
| `0x5C4C50`（写一个元素） | `row::writeCandidateAngle(element, tag, angle)` |
| `0x8BEFC0`（源 + 追加一个） | `row::candidateAngles(source, tag, angle)` |
| `0x13450B` 的 90° 常量 | `row::kAxisAngle90 = 0xD18C2E2800ll` |
| `0x134470` 的准备段 | `row::axisAlignedCandidates(source)` |

`test_row` 断言：`0x5C4C50` 只写一个元素（tag/angle 分别落在 `+0x00`/`+0x08`）；
`0x8BEFC0` 保留源元素顺序再追加一个；`axisAlignedCandidates` 得到 4 个元素且
第 3/4 个恰为 `{0, 0°}` 与 `{0, 90°}`；`kAxisAngle90 == 0xD18C2E2800`；
且该 90° 条目经 `angleTransform` 走的是**精确 90° 分支**（`sin = 1`、`cos = 0`）。

### 31.6 §30.2 残留清单的更新

| 项 | 状态 |
|---|---|
| ~~`0x8BEFC0`（候选角度集合来源）~~ | ✅ **结案**（§31.1–§31.3） |
| `0x134D70`（元素两个标志的计算） | ⏳ **部分**：结构、包围盒、`1e-06` 容差与 fabs 掩码已确定；完整表达式未转写 |
| `0x135030` / `0x136D10` 的角色命名 | ⏳ 未译（数值来源已知） |
| `0x136350` 内部七个子调用 | ⏳ 未译 |
| `0x133DE0` 的 arg1/arg2 构造者 | ⏳ 未译 |
| `0x5CEE50` 的 tag ≠ 0 分支 | ⏳ 未译 |

---

## 32. **纠正**：元素 `+0x08`/`+0x10` 是"产生它的那条候选记录"，不是容器的 begin/end **[本轮，已证实]**

### 32.1 纠正的内容与证据链

我在 §23.1/§28.3 里把元素的 `+0x08`/`+0x10` 记成 **"源容器的 begin/end"**（依据是
`0x13637B`/`0x136388` 的两次存储）。**这是错的。** 它们是
**产生该元素的那条 16 字节候选记录 `{tag, angle}` 的副本**。

证据链（三条独立证据）：

1. **存储端**：`0x136350` 把 `r8`（arg3）的头两个 qword 拷进去
   ```
   136363  rax = [r8] ; 136374 rdx = [r8+8]
   13637B  [element+0x08] = rax ; 136388 [element+0x10] = rdx
   ```
2. **读取端**：`0x1355C0` 把它们**当作那条记录**读回来
   ```
   1355DA  rdx = element + 8
   1355E1  call 0x5CEE50(transform, element + 8)
   ```
   而 `0x5CEE50` 读 `x` 的方式是 §26.1 已证实的取值器：
   `0x5C4CD0(x) = movzx eax, byte [rcx]`（tag）、`0x5C4CE0(x) = mov rax, [rcx+8]`（角度）。
   若 `+0x08`/`+0x10` 是"begin/end 指针"，则 tag 会是某个指针的低字节、角度会是另一个指针——
   语义上荒谬；按 `{tag, angle}` 读则完全自洽。
3. **调用端**：`0x136350` 的 `r8` 在各调用点都是**遍历中的 16 字节候选元素**
   （`0x133A21`/`0x133A92`/`0x133A9D` 等处的 `rbx`，以及 `0x133B3A` 的 `[rsp+0x120]`）。

⇒ **元素记着"我是被哪条候选记录造出来的"**（tag + 角度），
这正是 `0x1355C0` 能用它自己的角度去旋转零件几何的原因。

### 32.2 `0x133190` = `lea rax,[rcx+8]` ⇒ 元素的 `+0x00` 是 **Item 指针**，几何源是 **`Item+0x08`** **[已证实]**

```
133190  lea rax, [rcx + 8]
133194  ret
```

`0x1355C0` 用它取几何源：`rcx = [element]`（即元素 `+0x00`，§28.3 的 `owner`）→
`0x133190(Item)` = **`Item+0x08`** = 该零件的 **48 字节元素几何容器**（§28.2 的
`vector<Elem48>`）。

### 32.3 `0x1355C0`（438 B）= **元素自己的几何步** **[已证实为结构]**

```
1355DA  rdx = element + 8
1355E1  call 0x5CEE50(transform, element + 8)      ; ★ 用**它自己的角度**建变换
1355E6  rcx = [element] ; 1355E9 call 0x133190     ; → Item + 0x08（零件几何）
1355F7  call 0x5D38C0(out, Item+0x08, transform)   ; ★ 把零件几何按该角度变换拷贝
1355FC..135602  call 0x5CD800(rsp+0x50, out)       ; 其包围盒
135607  xmm0 = [rsp+0x58] ; 13561A movhpd xmm0, [rsp+0x60]
135620  xorpd xmm0, [0x9BCEF0] = -0.0              ; ★ 取负（符号精确）
13562D  call 0x5D3430(rsp+0x30, out, rsp+0x20)     ; 再加工一次（1156 B，未译）
135640..135672  用结果整体替换 out 的 vector（把旧缓冲释放）
```

⇒ **元素的包围盒 = 「该零件的 48 字节几何容器按该元素自己的角度旋转后的包围盒」**
（并在 `0x5D3430` 里再经过一步未译的加工）。

### 32.4 一批"访问器"其实是**恒等转发** **[已证实]**

| 函数 | 指令 | 结论 |
|---|---|---|
| `0x5C5F30` | `mov rax, rcx ; ret` | 恒等 |
| `0x5C5260` | `mov rax, rcx ; ret` | 恒等 |
| `0x5C61D0` | `mov rax, rcx ; ret` | 恒等 |
| `0x5C5F50` | `mov rax, rcx ; ret` | 恒等 |
| `0x133190` | `lea rax,[rcx+8]` | `+0x08` 偏移 |

⇒ §34 之前把 `0x5C61D0`/`0x5C5F30` 当作"取容器"的读取器是对的，
但**它们本身不做任何工作**，真正的偏移在调用者手里。

### 32.5 已并入工程 **[已证实]**

* `row::ScoreNode` 的 `+0x08`/`+0x10` 字段**改名并改注释**：
  `sourceTagQword`（低字节是 tag）/ `sourceAngle`（定点度），注释里写明**纠正原因**与证据行号；
  **15 条 `static_assert` 的偏移全部不变**（只是语义命名修正，布局未动）。
* 新增 `kItemGeometry = 0x08`（`0x133190`）、`nodeSourceTag()`（`0x5C4CD0(element+8)`）、
  `nodeSourceAngle()`（`0x5C4CE0(element+8)`）、`nodeAngleTransform()`（`0x5CEE50(transform, element+8)`，
  **仅 tag = 0 路径**）。

`test_row` 新增断言：`kItemGeometry == 0x08`；`nodeSourceTag/Author` 从 `+0x08`/`+0x10` 正确取值；
一个 90° 元素经 `nodeAngleTransform` 走**精确 90° 分支**；0° 元素给出恒等旋转。

### 32.6 §30.2 残留清单的更新

| 项 | 状态 |
|---|---|
| `0x136350` 内部的七个子调用 | ⏳ **推进**：`0x1355C0` 已译（元素自己的几何步）；`0x133190` 证实；`0x5CE7F0` 待译（180° 变换构造）；`0x5D3430`(1156 B)/`0x135040`(1396 B)/`0x135780`(1250 B)/`0x135C70`(1748 B) **规模大、未译**；`0x8C4FF0`(147 B)、`0x5CF6B0`(235 B) 未译 |
| `0x134D70`（两个标志） | ⏳ 部分（§31.4） |
| `0x135030` / `0x136D10` 角色命名 | ⏳ 未译 |
| `0x133DE0` 的 arg1/arg2 构造者 | ⏳ 未译 |
| `0x5CEE50` 的 tag ≠ 0 分支 | ⏳ 未译 |

---

## 33. 三个小函数结案：两点变换、`Elem48` 析构、角度→变换的第二实例 **[本轮，已证实]**

### 33.1 `0x5CF6B0`（235 B）= **两点仿射变换**，与 `0x5D38C0` 同一算术 **[已证实]**

```
5CF6C9  xmm0 = [r8+0x10] ; 5CF6D5 xmm1 = [r8]        ; sin / cos
5CF6CF  xmm4 = [r8+0x18] ; 5CF6DA xmm6 = [r8+8]      ; cos / -sin
5CF6E6  xmm7 = [r8+0x20] ; 5CF6EC xmm5 = [r8+0x28]   ; tx / ty
5CF6E3..5CF72E  把源的两个点（4 个 qword）拷进输出
5CF70B  xmm3 = x * cos ; 5CF717 xmm9 = y * (-sin) ; 5CF732 xmm3 += xmm9
5CF748  xmm3 += tx ; 5CF750 [out] = x'                ; ★ x' = cos·x − sin·y + tx
5CF70F  xmm2 = x * sin ; 5CF725 xmm8 = y * cos ; 5CF73D xmm2 += xmm8
5CF74C  xmm2 += ty ; 5CF759 [out+8] = y'              ; ★ y' = sin·x + cos·y + ty
5CF754..5CF791  对第二个点（+0x10/+0x18）做**完全相同**的算术
```

⇒ 与 §26.2 的 `0x5D38C0` **算术完全一致**，只是**恰好两个点**的特化。
这是 `transformX/transformY` 的**第二个独立代码证据**。

### 33.2 `0x8C4FF0`（147 B）= **`Elem48` 容器的析构函数** ⇒ 从析构端证实两层步长 **[已证实]**

```
8C5010  rsi = [rdi+0x20] ; rbx = [rdi+0x18]      ; 元素内部那个 vector 的 end/begin
8C5020  逐个释放，`add rbx, 0x18`                ; ★ 内部元素 24 字节
        （该步在 **`0x8C502D`**）
8C5047  释放 [rdi]                               ; 元素的第一个指针（另一个 vector 的 begin）
8C5054  `add rdi, 0x30`                          ; ★ 外层元素 48 字节
8C5073  jmp operator delete                      ; 释放外层缓冲
```

⇒ **`Elem48` = 48 字节，内部含一个「24 字节记录」的 `vector` 与另一个指针**
—— 与 §18/§21 由 `0x5C2E40` 推出的"24 字节记录 `{u8 tag, int64 lo, int64 hi}`"**步长吻合**。
这是目标 ② 的又一条**独立证据**（此前由访问器推出，现在由析构证实）。

### 33.3 `0x5CE7F0`（381 B）= **角度→变换算法的第二个实例** **[已证实]**

其常量与 `0x5CEE50` **完全相同**：

```
5CE801  rdx = 0x9C5FFF26ED75ED55        ; 取模魔数
5CE822  rax = 0x34630B8A000             ; 360e10
5CE83F/5CE852/5CE865  cmp 0xD18C2E2800 / 0x1A3185C5000 / 0x274A48A7800   ; 90/180/270 度
5CE878  cvtsi2sd …
```

⇒ 它是同一算法的另一处实例化（少了 tag 分支）。而 `0x136350` 在 `0x13645B` 调
`0x5CE7F0(rsp+0x150, 0x1A3185C5000)` = **按 180° 构造变换**，
用于把容器的**镜像副本**存进元素（§28.3）。

### 33.4 已并入工程 **[已证实]**

| RE | 工程 |
|---|---|
| `0x5CF6B0`（两点变换） | `row::transformPoint(t, x, y)` + `row::FPoint2` |
| `0x8C4FF0`（`Elem48` 析构的两层步长） | `row::kElem48Stride = 0x30`、`row::kRecord18Stride = 0x18` |
| `0x5CE7F0` + `0x13645B` 的 180° | `row::kHalfTurn180 = 0x1A3185C5000ll` + `row::halfTurn()` |

`test_row` 断言：两点变换与 `transformX/Y` 一致（90° 下 `(1,0)→(0,1)`、`(0,1)→(−1,0)`）；
两个步长满足 `kRecord18Stride < kElem48Stride`；`halfTurn()` 给出 `cos = −1`、`sin = 0`、
**`−sin = −0.0`（符号精确）**，故元素里存的是**关于原点的中心对称副本**（`(3,4) → (−3,−4)`）。

### 33.5 §30.2 残留清单的更新

| 项 | 状态 |
|---|---|
| `0x136350` 的七个子调用 | ⏳ **推进 3/7**：`0x1355C0`（§32.3）、`0x8C4FF0`（§33.2）、`0x5CE7F0`（§33.3）已结案；`0x5CF6B0` 虽不在该七项内但同批结案（§33.1）。**剩余未译**：`0x5D3430`(1156 B)、`0x135040`(1396 B)、`0x135780`(1250 B)、`0x135C70`(1748 B)、`0x5CF6B0` 已在上面、`0x8C4FF0` 已在上面 ⇒ 实际剩 **4 个大函数** |
| `0x134D70`（两个标志） | ⏳ 部分（§31.4） |
| `0x135030` / `0x136D10` 角色命名 | ⏳ 未译 |
| `0x133DE0` 的 arg1/arg2 构造者 | ⏳ 未译 |
| `0x5CEE50` 的 tag ≠ 0 分支 | ⏳ 未译 |

---

## 34. `0x134D70` **完全译出**（§30.2 第 ② 项）—— 并确定 **`Elem16` = 二维点** **[本轮，已证实]**

### 34.1 `0x134D70`（437 B / 101 条）**逐块控制流** **[已证实]**

```
134DAB  call 0x5CD800(rsp+0x20, rsi)          ; arg1 的包围盒
134DB8  xmm10 = [rbx]                          ; arg2（一个 node）的 [+0x00]
134DC0  esi = 1                                ; ★ 结果初值 true
134DC5  xmm7 = [rsp+0x40]                      ; 包围盒的 [+0x20]
134DD0  xmm10 = max([rbx], [rbx+0x10])         ; maxsd
134DD6  xmm9  = max([rbx], [rbx+0x18])         ; maxsd
134DDC  call 0x5C61D0(rsi)                     ; 恒等（§32.4）
134DE1  rdi = [rax] ; rbx = [rax+8]            ; 容器的 begin/end
134DEB  if (begin == end) → 返回 1             ; ★ 空容器 ⇒ true
134DF1  xmm8 = [0x9BCED0] = NaN                ; ★ fabs 掩码
134DFF  xmm6 = [0x9BCEE0] = 1e-06              ; ★ 容差
134E10  ── 外层循环：逐**元素**（步长 0x30，见 134EE0 `add rdi,0x30`）
134E20    rdx = [rax+8] ; rax = [rax]           ; ★ 元素 +0x00 处的容器（begin/end）
134E27    xmm3 = [rdx-0x10] ; xmm1 = [rdx-8]    ; ★★ 从**最后一个点**开始（闭合链！）
134E2C    cmp rdx, rax ; jne 134E68             ; 非空则进入扫描
134E68  ──（L68）xmm2 = [rax+8]                 ; 当前点的 y
134E6D    xmm0 = |xmm2 - xmm1|                  ; andpd 掩码取绝对值
134E7E    jae 134E40                            ; ★ 若 1e-06 >= |dy| 则去 L40
134E80  ──（L80）xmm0 = xmm7 - xmm9 ; 134E8D jae L95 ; 134E93 jb L53
134E95  ──（L95）xmm0 = |xmm2 - xmm7| ; 134EA6 jb Lb7
134EA8    xmm1 = |xmm1 - xmm7| ; 134EB5 jae L53
134EB7  ──（Lb7）xmm0 = [rax] ; xmm1 = xmm0 - xmm3 ; xmm3 = xmm1
134ED0    jae L57                                ; |dx| <= 1e-06 ⇒ 前进
134ED7    jbe L57                                ; dx >= 0 ⇒ 前进
134EDD    xor esi, esi                           ; ★★★ 结果 = false（**只置 0、从不复位**）
134E40  ──（L40）xmm0 = xmm7 - xmm10 + 1e-06 ; 134E51 jb L80
134E53  ──（L53）xmm0 = [rax]                    ; 取当前点的 x
134E57  ──（L57）rax += 0x10（★ 点步长 16）; xmm1 = xmm2 ; xmm3 = xmm0
134E63    cmp rdx, rax ; 134E66 je 下一个元素 ; 否则回 L68
134EE0  ── 下一个元素
134EED  mov eax, esi ; ret                       ; 返回 bool
```

⇒ **`0x134D70(container, node) -> bool`**：对容器里的每个元素，扫描其 `+0x00` 处的
**16 字节点链（按闭合链处理：首点与末点相比）**，用 `1e-06` 容差与 fabs 掩码判定；
一旦发现"**y 落在窗口内却出现严格倒退的 x 步**"（`0x134EDD`）即为 false。
结果**粘滞**（`esi` 只在 `0x134EDD` 被清零，从不置 1）⇒ 多元素之间是 **AND**。

### 34.2 **`Elem16` 的语义由此确定：它是二维点 `{double x, double y}`** **[已证实]**

`0x134E57` 的 `add rax, 0x10` 说明该容器的元素是 **16 字节**，而循环体只读
`[rax]`（x）与 `[rax+8]`（y）⇒ **`Elem16` = 2D 点**。
这**补上了目标 ② 中"`Elem16`(16B) 的字段语义"**：

```
Item (0x90)
 ├ +0x08 vector<Elem48>            （零件的 48 字节几何，§28.2）
 └ Elem48 (0x30)
      ├ +0x00 vector<Elem16>       ★ 16 字节 = 二维点 {double x, double y}（本节确定）
      ├ +0x18 vector<Record18>     ★ 24 字节 = {u8 tag, int64 lo, int64 hi}（§21.1 由谓词确定，
      │                               §33.2 由析构端再次证实步长）
      └ ...（另有一个被析构释放的指针，§33.2）
```

### 34.3 已并入工程 **[已证实]**

`lcns/include/lcns/row.hpp` 新增：

| RE | 工程 |
|---|---|
| `Elem16` 的型别与步长 | `row::Elem16{double x, y}` + `kElem16Stride = 0x10` |
| `0x9BCEE0` 的容差 | `row::kChainEpsilon = 1e-06` |
| `0x134D70` 的整条控制流 | `row::chainMonotone(chain, node[3], bboxMaxX)`（**标签按地址命名**，逐块对应，注释给出每条指令的 RVA） |
| `0x136350` 处两次调用 | `row::chainFlags(chains, node, bboxMaxX)`（AND 语义，对应 `esi` 粘滞） |

`test_row` 断言：`kElem16Stride == 0x10`、`sizeof(Elem16) == 16`、`kChainEpsilon == 1e-06`；
**空链 ⇒ true**（`0x134DEB`）；一段不回退的链 ⇒ true；
**特意构造出 false 路径**（`node = {0,1,1}`、`bboxMaxX = 0`、链 `{(0,5),(1,0),(2,0)}`
—— 首点相对末点 x 倒退且 y 窗口被突破，走到 `0x134EDD`）⇒ false；
以及 `chainFlags` 的 AND 语义。

⇒ **§30.2 第 ② 项结案**，且**不再有"完整表达式未转写"的保留**。

### 34.4 §30.2 残留清单的更新

| 项 | 状态 |
|---|---|
| ~~`0x134D70`（两个标志）~~ | ✅ **结案**（§34.1–§34.3） |
| `0x136350` 的七个子调用 | ⏳ 已结案 `0x1355C0`/`0x8C4FF0`/`0x5CE7F0`/`0x5CF6B0`；**剩余四个大函数** `0x5D3430`(1156 B)/`0x135040`(1396 B)/`0x135780`(1250 B)/`0x135C70`(1748 B) |
| `0x135030` / `0x136D10` 角色命名 | ⏳ 未译（数值来源已知） |
| `0x133DE0` 的 arg1/arg2 构造者 | ⏳ 未译 |
| `0x5CEE50` 的 tag ≠ 0 分支 | ⏳ 未译 |

---

## 35. tag≠0 分支 = **镜像**（⑥ 结案）+ `+0x98/+0x99/+0xa0` 的生产者（③ 的答案） **[本轮，已证实]**

### 35.1 ⑥ **结案**：`0x5CEE50` 的 tag≠0 路径 = 反射 `{cos, +sin, sin, −cos, 0, 0}` **[已证实]**

关键前提：走到 `0x5CEF59` 时 **`xmm6` 已经等于 0** ——
一般路径在 `0x5CEF1C` 有 `pxor xmm6, xmm6`，四个精确角分支（`0x5CEFE8`/`0x5CF008`/
`0x5CF028`/`0x5CF048`）也各有一条 `pxor xmm6, xmm6`。因此 tag≠0 路径里所有 `* xmm6` 项都消失：

```
5CEF62  mulsd xmm7, xmm6          ; xmm7 = (-sin) * 0 = 0
5CEF70  mulsd xmm1, xmm6          ; xmm1 = cos * 0   = 0
5CEF79  mulsd xmm0, xmm6          ; xmm0 = sin * 0   = 0
5CEF7D  addsd xmm2, xmm7          ; xmm2 = cos + 0
5CEF8A  [out+0x00] = xmm2         ; ★ cos
5CEF85  addsd xmm8, xmm1          ; xmm8 = sin + 0
5CEF9F  [out+0x08] = xmm8         ; ★ +sin（旋转路径这里是 -sin）
5CEFA9  [out+0x10] = xmm8         ; ★ +sin（与 +0x08 同值）
5CEF96  subsd xmm2, xmm9          ; xmm2 = 0 - cos
5CEFAF  [out+0x18] = xmm2         ; ★ -cos
5CEFB4  [out+0x20] = 0
5CEFB9  [out+0x28] = 0
5CEFBE  …恢复并返回（tag == 0 时直接跳到这里）
```

⇒ **tag == 0 → 旋转 `{cos, −sin, sin, cos}`（行列式 +1）；
tag ≠ 0 → 反射 `{cos, +sin, sin, −cos}`（行列式 −1）。**
**tag 的语义 = "是否镜像"** —— 这正是候选元素需要带 tag 的原因。

### 35.2 `+0x98` / `+0x99` / `+0xa0` 的生产者（都在 `0x136350` 内） **[已证实]**

```
1366A2  byte [rbx+0x99] = 0
1366AC  byte [rbx+0x98] = 0
1366B3  call 0x1333C0(rdi)                     ; → Item+0x20
1366B8  if (byte [rax+0x20] == 0) → 0x1366FF   ; Item 子对象上的一个标志
1366BE  al = byte [rbx+0x48]                   ; 第一个可选槽的 presence
1366C2  if (al == 0) → 0x1366E7
1366C6  xmm1 = 1e-06 ; 1366CE xmm0 = [rbx+0x60] ; 1366D3 xmm0 -= [rbx+0x50] ; fabs
1366E0  ucomisd xmm1, xmm0 ; 1366E4 setae al
1366E7  byte [rbx+0x99] = al                   ; ★ = 槽存在 且 |v[2] - v[0]| <= 1e-06
1366ED  eax = byte [rbx+0x70]                  ; 第二个可选槽的 presence
1366F1  if (al != 0) → 0x1368A9                ; 另一条分支（属未译部分）
1366F9  byte [rbx+0x98] = al                   ; ★ = 第二个槽的 presence
1366FF  rcx = rsi ; call 0x135C70              ; ★★ 1748 B，未译
13670F  [rbx+0xa0] = xmm0                      ; ★★ element+0xa0 = 0x135C70(...) 的返回值
```

⇒ 两个标志的**完整公式**已译出（见工程侧）；而 **`element+0xa0` 由未译的 `0x135C70` 产生**。

### 35.3 ③ 的答案：一半结案、一半**明确声明不可恢复 + 原因**

`0x137C76` 那个比值是 `0x135030(element) / 0x136D10(obj)`：

| 端 | 结论 | 依据 |
|---|---|---|
| 分母 `0x136D10(obj)` | ✅ **结案**：它返回 `obj[+0x08]`；该字段由 `0x136C00` 的 `xmm2` 写入，而 `0x136C00` 在 `0x137FF8` 被调用、两个 double 来自 `0x137FE0` 的调用者，追到 `0x133DE0` 即 **`cfg[+0x08]`（即 `core+0x10`）** ⇒ **配置系数** | `0x136D10` 两条指令、`0x136C10`、`0x137FF8`、`0x133F2D`/`0x133F31` |
| 分子 `0x135030(element)` | ✅ **数值来源结案**：它返回 `element[+0xa0]`，而该字段由 `0x13670F` 从 **`0x135C70`（1748 B）** 的返回值写入 | `0x135030` 两条指令、`0x13670F` |
| 分子的**语义命名** | ❌ **不可恢复（当前）**，原因：它完全取决于 `0x135C70`（1748 B，四个未译大函数之一）的内部计算；本函数无类型信息、无字符串、无 RTTI 可借 | 已核实 `0x135C70` 未译 |

⇒ 按目标 ④：**不猜**，明确记录"数值通路已完整追到 `0x135C70`，命名待其译出"。

### 35.4 **测试抓出的一处真实缺陷**：`transformX/Y/Det` 用错了字段 **[已证实]**

`0x5D38C0` 实际用的字段是 `[+0x00]=cos`、`[+0x08]=negSin`、`[+0x10]=sin`、`[+0x18]=cos2`：

```
5D3BDF  xmm0 = xmm0 * xmm8   ; negSin * y     5D3BE4  xmm1 = xmm1 * xmm4   ; cos * x
5D3BF1  xmm0 += xmm1 ; 5D3BF5 += [rdi+0x20]   ; x' = cos·x + negSin·y + tx
5D3BD7  xmm2 = xmm9 * xmm0   ; cos2 * y       5D3BDB  xmm3 = xmm5 * xmm1   ; sin * x
5D3BE8  xmm2 += xmm3 ; 5D3BEC += [rdi+0x28]   ; y' = sin·x + cos2·y + ty
5D3C09  xmm4 = cos * cos2 ; 5D3C0E xmm5 = sin * negSin ; 5D3C13 相减
                                              ; det = cos·cos2 - sin·negSin
```

我原先写成 `cos·x − sin·y` 与 `sin·x + cos·y`、行列式 `cos² + sin²`
—— 对**纯旋转**等价（`negSin = −sin`、`cos2 = cos`），但**对镜像错误**：
本轮新增的 `transformDet(mirroredAngleTransform(90°)) == −1` 断言**当场失败**（得到 1），
据此改为按 `negSin`/`cos2` 计算。修正后旋转得 +1、镜像得 −1，
与 `0x5D3C09`–`0x5D3C13` 完全一致。

### 35.5 已并入工程 **[已证实]**

| RE | 工程 |
|---|---|
| `0x5CEF62`–`0x5CEFB9` | `row::mirroredAngleTransform(deg)`（反射 `{cos,+sin,sin,−cos,0,0}`） |
| `0x5CEF5E` 的 tag 分派 | `row::nodeAngleTransform` 现在**按 tag 分派**：0 → 旋转，非 0 → 镜像 |
| `0x1366BE`–`0x1366E7` | `row::nodeSlotFlag99(node)`（第一槽存在且 `\|v[2]−v[0]\| ≤ 1e-06`） |
| `0x1366ED`–`0x1366F9` | `row::nodeSlotFlag98(node)`（第二槽的 presence） |
| `0x5D3BDF`–`0x5D3C13` | **修正** `transformX/Y/Det` 改用 `negSin`/`cos2` |

`test_row` 断言：镜像的六个字段、`transformDet(mir) == −1` 与 `transformDet(rot) == +1`、
0° 镜像为 `{1,0,0,−1}`、tag 分派（tag 0 → `negSin = −1`；tag 1 → `+1`）、
以及两个槽标志的三种情形。

### 35.6 §30.2 残留清单的更新

| 项 | 状态 |
|---|---|
| ~~① 候选角度集合~~ | ✅ 结案（§31） |
| ~~② `0x134D70`~~ | ✅ 结案（§34） |
| ③ `0x135030` / `0x136D10` | ✅ **分母结案（配置系数）**；分子**数值通路结案、命名明确不可恢复**（取决于未译的 `0x135C70`） |
| ④ `0x136350` 子调用 | ⏳ 已结案 `0x1355C0`/`0x8C4FF0`/`0x5CE7F0`/`0x5CF6B0`；**剩四个大函数** `0x5D3430`(1156 B)/`0x135040`(1396 B)/`0x135780`(1250 B)/`0x135C70`(1748 B)（`0x135C70` 现在还被 ③ 的命名依赖） |
| ⑤ `0x133DE0` 的 arg1/arg2 构造者 | ⏳ 未译 |
| ~~⑥ `0x5CEE50` 的 tag≠0 分支~~ | ✅ **结案**（§35.1） |
| 另注 | `0x1368A9`（`+0x98` 的另一条分支）属未译部分 |

---

## 36. ⑤ 结案：`0x133DE0` 两个实参的构造者 + **授权区间是"角度区间"** **[本轮，已证实]**

### 36.1 arg1（`rsp+0x1b0`）= 零件几何容器的**拷贝**，来源是两步访问器 `0x4F7600` **[已证实]**

```
4F7600  mov rcx, qword ptr [rcx + 0x70]     ; 取 Part+0x70
4F7604  jmp 0x547610                         ; 尾调用另一个访问器
```

只有 **9 字节 / 2 条指令**。⇒ `0x4F7600(part)` = `0x547610(part[+0x70])`，
返回的是**零件内部的容器引用**——这正好解释了 `0x6AABC0` 为什么必须把它**拷贝**到
循环局部缓冲 `rsp+0x1b0`（引用不能跨调用存活）。

### 36.2 arg2（`rsp+0x1d0`）= **授权记录表**，由 `0x5C4950`（730 B）构造 **[已证实]**

```
5C49B7/5C49C7  取源容器的 begin/end（rdi）
5C4A20  rcx = r13 ; call 0x5C4CE0 → r14      ; ★ 一个角度
5C4A2E  rcx = rdi ; call 0x5C4CE0 → r15      ; ★ 另一个角度
5C4A39  call 0x5C4CD0 → al                   ; ★ tag 字节
5C4A3E  byte [rsp+0xb0] = al                 ; 记录 [+0x00]
5C4A45  [rsp+0xb8] = r15                     ; 记录 [+0x08] = 角度
5C4A4D  [rsp+0xc0] = r14                     ; 记录 [+0x10] = 角度
5C4A70..5C4A8F  追加 3 个 qword（24 字节）
5C4A93  rax += 0x18 ; 5C4A97 rbx += 0x18     ; ★ 表元素 24 字节、源元素 0x18 步长
```

⇒ **记录表的每条是 `{u8 tag, int64 lo, int64 hi}`，其中 `lo`/`hi` 都是"角度"**
（来自取值器 `0x5C4CE0`）。

### 36.3 **语义回溯**：`0x5C2E40` 的区间是**角度区间** **[已证实]**

§21.1 我只把 `0x5C2E40` 描述为"24 字节记录的区间归属测试"；现在**生产端**（`0x5C4950`）
证明两个端点是**角度**，而被测值也是角度（$0x5C4CE0(element)）⇒

> **授权表的语义 = "该 tag 下允许的角度范围"**，
> `0x134470` 因此是"**在被允许的角度范围内挑选分数最小的角度**"。

这是本轮从生产端反推出来的**语义闭环**（此前只有消费端）。

### 36.4 两个缓冲都是**循环局部**的 **[已证实]**

```
6AB35A  rcx = [rsp+0x1d0] ; cmp rcx,r13 ; je ; call operator delete   ; 释放记录表
6AB36C  rcx = [rsp+0x1b0] ; cmp rcx,r14 ; je ; call operator delete   ; 释放几何拷贝
6AB37E  rcx = r15 ; call 0x4F8F80 ; [rbp+0x40] = eax
6AB389  edi += 1 ; 6AB399 cmp edi,eax ; jne 0x6AB150                  ; 逐零件循环
```

⇒ 每个零件的每次迭代各建一份，用完即释放。

### 36.5 `0x5C3F00` 的角度回绕常量 **[已证实]**

```
5C3F0A/5C3F66  movabs rax, 0x34630B89FFF      ; ★ = 360e10 - 1（角度归一用）
```

`0x5C3FF0` 则在有序容器里做一次查找（`0x98E2F0`）。

### 36.6 已并入工程 **[已证实]**

| RE | 工程 |
|---|---|
| `0x5C4A3E`/`0x5C4A45`/`0x5C4A4D` | `row::makeAuthRecord(tag, lo, hi)`；`AuthRecord` 的注释**升级为"lo/hi 是定点角度"** |
| `0x4F7600` | `row::kPartGeometryVia = 0x70` |
| `0x5C3F0A` | `row::kAngleWrapMax = 0x34630B89FFFll` |

`test_row` 断言：`kPartGeometryVia == 0x70`、`kAngleWrapMax == 360e10 − 1`、
以及用**角度区间** `[0°, 180°]`（tag 0）测试 `authorized`：90° 通过、270° 不通过、
tag 不匹配不通过、两个端点**含**在内。

### 36.7 §30.2 残留清单的最终状态

| 项 | 状态 |
|---|---|
| ~~① 候选角度集合~~ | ✅ 结案（§31） |
| ~~② `0x134D70`~~ | ✅ 结案（§34） |
| ~~③ `0x135030`/`0x136D10`~~ | ✅ 分母结案；分子数值通路结案、**命名明确不可恢复**（§35.3，取决于未译的 `0x135C70`） |
| ④ `0x136350` 子调用 | ⏳ 4/7 结案（`0x1355C0`/`0x8C4FF0`/`0x5CE7F0`/`0x5CF6B0`）；**只剩四个大函数** `0x5D3430`(1156 B)、`0x135040`(1396 B)、`0x135780`(1250 B)、`0x135C70`(1748 B) |
| ~~⑤ `0x133DE0` 的 arg1/arg2 构造者~~ | ✅ **结案**（本节，并回溯出"角度区间"语义） |
| ~~⑥ `0x5CEE50` 的 tag≠0 分支~~ | ✅ 结案（§35.1） |
| 另注 | `0x1368A9`（`+0x98` 的另一条分支）属未译部分 |

---

## 37. `0x135C70` 的返回值 = **鞋带公式的面积** ⇒ ③ 的分子**已命名**（更正 §35.3） **[本轮，已证实]**

### 37.1 `0x135C70`（1748 B / 406 条）的结构 **[已证实]**

| 观察 | 数据 |
|---|---|
| rodata 常量 | **一个都没有** |
| 浮点指令 | 总共只有 **8 条** |
| 元素步长 | `0x10`（`0x13630F add rdi,0x10`、`0x136328 add rsi,0x10`） |
| 调用表 | `0x67CBF0`、`0x5C6BE0`（与 `0x135040` 同款开场）、`operator delete`×18、`operator new`×1、`0x89A740`×2、`0x8C34D0`×4、**`0x5CD800`（包围盒）**、`0x5C51A0`、**`0x5CC6A0`**、`basic_string` ×2（断言串）、`0x8C4FF0`（**`Elem48` 析构**）、`0x5C5F50`、`0x5C5270`、`0x979E70`、`0x67FE90` |

关键的三段：

```
① 取最小（0x135DA9..0x135DC6）：
   135DB1  xmm0 = [rdx+8] ; 135DB6 ucomisd xmm0,[rsi+8] ; 135DBB cmova rdx, rsi
   135DBF  rsi += 0x10 ; 135DC6 jne 0x135DB1
   ⇒ 在 16 字节元素上保留 **+0x08 最小者**（即 `Elem16::y` 最小的点 = **最低点**）

② 原地反转一段（0x135F90..0x135FBE）：成对的 16 字节元素互换、指针相向推进
   ⇒ `std::reverse` 的展开（**顶点顺序规范化**）

③ 拷贝 + 求值：
   135FCE  call 0x5C51A0(copy, src)      ; 容器拷贝
   135FD6  call 0x5CC6A0(copy)           ; ★ 求值
   135FE3  movapd xmm6, xmm0             ; ★★ 返回值（`xmm6` 全程只被写这一次）
   13607F  movapd xmm0, xmm6 ; … ret     ; 唯一的 ret 在 0x13609C
```

### 37.2 `0x5CC6A0`（135 B）= **鞋带公式求面积** **[已证实]**

```
5CC6B2  call 0x5C5260（恒等）; rax = [rax+8]        ; 容器的 end
5CC6BE  xmm6 = [rax-0x10]                           ; ★ 最后一个点的 x
5CC6C3  xmm7 = [rax-8]                              ; ★ 最后一个点的 y（**闭合环**）
5CC6D1  rdx = [rax](begin) ; 5CC6D4 rcx = [rax+8](end) ; 5CC6DB je → 空则返回 0
5CC6E4  xmm1 = [rax+8]（curY）; 5CC6ED xmm2 = [rax-0x10]（curX）
5CC6F5  xmm6 *= xmm1                                ; prevX * curY
5CC6F9  xmm7 *= xmm2                                ; prevY * curX
5CC6FD  xmm6 -= xmm7                                ; ★★ prevX·curY − prevY·curX
5CC705  xmm0 += xmm6                                ; 累加
5CC701  xmm7 = xmm1 ; 5CC709 xmm6 = xmm2            ; 前一点 ← 当前点
5CC70F  xmm0 *= [0x9DE910] = 0.5                    ; ★★★ × 0.5
5CC726  ret
```

⇒ **`0x5CC6A0(ring) -> double` = `0.5 · Σ (prev.x·cur.y − prev.y·cur.x)`**，
其中 `prev` 从**最后一个点**起算（闭合环）、**带符号、不取绝对值**。
常量只有 **`0x9DE910 = 0.5`**。

### 37.3 `0x5C51A0`（178 B）= **容器拷贝** **[已证实]**

`operator new(end−begin)`（`0x5C51E9`）→ 写 begin/end/cap（`0x5C51F1`/`0x5C51F4`/`0x5C51F8`）
→ 逐个拷贝 16 字节元素（`0x5C5215`..`0x5C522E`）。

### 37.4 **③ 的分子已命名**（更正 §35.3） **[已证实]**

§35.3 当时我写"分子的语义命名**不可恢复**（取决于未译的 `0x135C70`）"。本轮把那条链追到底：

```
0x13670F  [element+0xa0] = xmm0
0x135FD6  call 0x5CC6A0(copy)        ← 返回值就是这个
0x135FCE  call 0x5C51A0(copy, src)   ← 容器拷贝
0x135DB1  cmova 取 +0x08 最小          ← 找最低点（顶点顺序规范化的第一步）
0x135F90  .. 0x135FBE  原地反转        ← 顶点顺序规范化的第二步
```

⇒ **`element+0xa0` = 「一条按其最低点规范过顶点顺序的环」的带符号面积**。
于是 `0x137C76` 的比值是：

> **`score = cost − (ringArea / cfg[+0x08])`**

即"**挤压代价 − 归一化的环形面积**"。**分子已命名** ⇒ §35.3 的"不可恢复"结论**予以更正**。

（仍严格区分：`0x135C70` 的**返回值语义**已完全确定；其**函数体其余部分**
——断言串构造、临时对象管理 —— **未逐条转写**，但这不影响返回值的语义。）

### 37.5 已并入工程 **[已证实]**

| RE | 工程 |
|---|---|
| `0x9DE910` | `row::kAreaHalf = 0.5` |
| `0x5CC6A0` 的整条循环 | `row::dllArea(ring)`（闭合环、带符号、`prev` 从末点起算） |
| `0x5C51A0` | `row::copyRing(ring)` |
| `0x13670F` ← `0x135FD6` ← `0x135FCE` 的链 | `row::nodeAreaValue(ring)` |

`test_row` 断言：`kAreaHalf == 0.5`；单位正方形 **CCW ⇒ +1**、**反转 ⇒ −1**（带符号、不取绝对值）；
空环 ⇒ 0（`0x5CC6DB`）；三点重合的退化环 ⇒ 0；三角形 `(0,0),(4,0),(0,3)` ⇒ **6**；
以及 `nodeAreaValue` 与 `dllArea` 一致（拷贝那一跳不改变值）。

### 37.6 §30.2 残留清单的最终状态

| 项 | 状态 |
|---|---|
| ~~① 候选角度集合~~ | ✅ §31 |
| ~~② `0x134D70`~~ | ✅ §34（并确定 `Elem16` = 二维点） |
| ~~③ `0x135030`/`0x136D10`~~ | ✅ **两端均已命名**：分母 = `cfg[+0x08]`（配置系数）；分子 = **环形带符号面积**（本节，更正 §35.3） |
| ④ `0x136350` 子调用 | ⏳ 5/7 结案（`0x1355C0`/`0x8C4FF0`/`0x5CE7F0`/`0x5CF6B0`/**`0x135C70` 返回值语义**）；**剩三个**：`0x5D3430`(1156 B)、`0x135040`(1396 B)、`0x135780`(1250 B) |
| ~~⑤ 实参构造者~~ | ✅ §36 |
| ~~⑥ tag≠0 分支~~ | ✅ §35 |
| 另注 | `0x1368A9`（`+0x98` 的另一分支）；`0x135C70` 的函数体其余部分未逐条转写（不影响其返回值语义） |

---

## 38. ④ **结案**：最后三个子调用（`0x5D3430` 完全译出，`0x135040`/`0x135780` 定量定性） **[本轮，已证实]**

### 38.1 `0x5D3430`（1156 B / 282 条）= **按位移量平移的点链拷贝** **[已证实]**

| 观察 | 数据 |
|---|---|
| rodata 常量 | **一个都没有** |
| 浮点指令 | 只有 **12 条**，且是**两段完全相同**的块 |
| 调用表 | 全是容器/内存管道：`operator new`×4、`operator delete`×4、`0x5C5F50`/`0x5C5F60`（恒等）、`0x8C5090`、`0x9989A0`×2、`0x998FE0`×2、`0x979E70`×4、`0x998BC0`×2、`0x62F280`、`0x67FE90` |
| 返回 | 唯一 `ret` 在 `0x5D37A3`，`rax = [rsp+0x90]`，而该槽在 `0x5D344A` 存入 `rcx`（= arg1）⇒ **`0x5D3430(out, src, offset) -> out`** |

那两段块（`0x5D3700` 与 `0x5D3750`）：

```
5D3700  xmm0 = [rax]        ; 5D3708 xmm0 += [rbx]     ; 5D370C [rax-0x10] = xmm0   ; x += dx
5D3711  xmm0 = [rax-8]      ; 5D3716 xmm0 += [rbx+8]   ; 5D371B [rax-8]    = xmm0   ; y += dy
```

⇒ **`0x5D3430(out, src, offset)` = "把 `src` 的每个 16 字节点按 `offset`（`rbx` = arg3）平移后拷进 `out`"**。
而 `0x1355C0` 在 `0x13562D` 用**取负的包围盒一角**（`0x135620` 的 `xorpd -0.0`）当位移
⇒ **把环平移到原点**（§32.3 里那一步的真实内容）。

### 38.2 `0x135040`（1396 B）= **0.005 容差的匹配例程** **[已证实为结构 + 常量]**

| 观察 | 数据 |
|---|---|
| rodata 常量 | **`0x9BCEE8 = 0.005`**、fabs 掩码 `0x9BCED0`、**`0x9BCEE0 = 1e-06`** |
| 浮点工作 | `0x13516A addsd xmm2, xmm4`（加上 0.005）；`subsd` + `andpd`(取绝对值) + `ucomisd` 成对的容差比较（`0x1352B2`..`0x13531C`） |
| 调用 | `0x67CBF0`/`0x5C6BE0`（与 `0x135C70` 同款开场）、`basic_string`×3（断言）、**`0x8C4FF0`（`Elem48` 析构）**、`0x5C61D0`/`0x5C5F30`（恒等） |
| 返回 | 唯一 `ret` 在 `0x135258`，**不返回浮点** |

⇒ **0.005 容差下的几何匹配例程**。**重要细节**：它的 `0.005` 在 **`0x9BCEE8`**，
与挤压器的 `0.005`（**`0x9BCFD8`**，§12）**不是同一个 rodata 地址** ——
数值相同、来源不同，故工程里用两个常量名分别标注。

### 38.3 `0x135780`（1250 B）= **1e-06 容差下拼出 32 字节两点记录** **[已证实为结构 + 常量]**

| 观察 | 数据 |
|---|---|
| rodata 常量 | 仅 fabs 掩码 `0x9BCED0` 与 **`0x9BCEE0 = 1e-06`** |
| 浮点工作 | `0x13588A..0x1358CA` 的 `subsd`+`andpd`+`ucomisd` 容差比较；`0x135A37`/`0x135A3F`/`0x135A45`/`0x135A4B` **写出 4 个 double（32 字节 = 两点）** |
| 调用 | **`0x134890` ×1、`0x134C10` ×2（都在 row 单元内！）**、`0x8C5D40`×2、`0x5C61D0`/`0x5C5F30`、`basic_string`×3 |
| 入口 | `0x1357AF movapd xmm8, xmm2`（`xmm2` 是一个**输入 double**） |

⇒ **把点链在 `1e-06` 容差下拼成一条 32 字节的两点记录**，并调用 row 单元自己的
`0x134890`/`0x134C10`。

### 38.4 已并入工程 **[已证实]**

| RE | 工程 | 覆盖度 |
|---|---|---|
| `0x5D3430`（两段加法块 + 出参返回） | `row::translatedCopy(src, dx, dy)` | **完全** |
| `0x9BCEE8` 的 0.005 | `row::kMergeAlignTolerance = 0.005` | 常量（**与 `kSqueezeAlignmentTolerance` 区分地址**） |
| `0x135A37`..`0x135A4B` 的 32 字节 | `row::kTwoPointRecord = 0x20` | 常量 |
| `0x135040` / `0x135780` 的**函数体** | —— | **未逐条转写**（已在注释与本表中写明：常量、I/O 形状、调用面、返回均在案） |

`test_row` 断言：平移后两个点各分量正确、**源不被修改**（是拷贝）；
用取负的包围盒一角平移 ⇒ 环的角点归零；**平移保持带符号面积**；
`kMergeAlignTolerance == 0.005` 且与 `kSqueezeAlignmentTolerance` 数值相同（地址不同）；
`kTwoPointRecord == 0x20`。

### 38.5 目标条款的最终状态

| 条款 | 状态 |
|---|---|
| ① `0x8BEFC0`（候选角度集合来源）与元素语义 | ✅ §31（源自带元素 + 0° + 90°；元素 = `{tag, angle}`） |
| ② `0x134D70`（`+0x40`/`+0x41` 两标志） | ✅ §34（逐指令转写；并确定 `Elem16` = 二维点） |
| ③ `0x135030` / `0x136D10` 角色命名 | ✅ §35 + **§37 更正**：分母 = `cfg[+0x08]`（配置系数）、分子 = **环形带符号面积** |
| ④ `0x136350` 内部七个子调用中**可判定的部分** | ✅ **本节结案**：`0x1355C0`/`0x8C4FF0`/`0x5CE7F0`/`0x5CF6B0`/`0x135C70`（返回值语义）/`0x5D3430` **已译**；`0x135040`/`0x135780` **定量定性**（常量、I/O、调用面、返回），函数体未逐条转写 |
| ⑤ `0x133DE0` 的 arg1/arg2 构造者 | ✅ §36（并回溯出"授权区间是角度区间"） |
| ⑥ `0x5CEE50` 的 tag≠0 分支 | ✅ §35.1（即镜像 `{cos,+sin,sin,−cos}`） |
| 另注（不在六条内） | `0x1368A9`（`+0x98` 的另一条分支）仍**未译**，已明说 |

---

## 39. 收尾三项：Item 访问器的第二跳、元素 `+0x98` 的另一分支 **[本轮，已证实]**

### 39.1 `0x4F7600` / `0x4F7690` 与它们的第二跳 **[已证实]**

```
4F7600  mov rcx, qword ptr [rcx + 0x70]     ; *(Part+0x70)
4F7604  jmp 0x547610
547610  mov rax, rcx ; ret                  ; ★ 恒等转发 ⇒ 结果就是 *(Part+0x70)

4F7690  mov rcx, qword ptr [rcx + 0x70]     ; 同一个对象
4F7694  jmp 0x547670
547670  lea rax, [rcx + 0x90] ; ret         ; ★ 该对象 +0x90 处的字段
```

⇒ **两个访问器指向同一个堆对象**：一个返回它的头部（`*(Part+0x70)`），
另一个返回它的 `+0x90` 字段（`*(Part+0x70) + 0x90`）。
这也解释了 §36.1 里 `0x4F7600` 为什么必须被**拷贝**才能交给 `0x134470`：
它返回的是**零件内部某个堆对象的指针**（引用），不能跨调用存活。

工程侧：`row::kPartGeometryObject = 0x70`、`row::kPartGeometryField = 0x90`，
在注释里给出上面四条指令与两个尾调用目标。

### 39.2 `0x1368A9`：元素 `+0x98` 的另一条分支 —— 两个标志其实是**对称的** **[已证实]**

`0x136350` 里写 `+0x98` 的路径有两条，早先只译了一条：

```
1366ED  eax = byte [rbx+0x70]               ; 第二个可选槽的 presence
1366F1  if (al != 0) → 0x1368A9             ; ★ 非零才走下面这条
1366F9  byte [rbx+0x98] = al                ; presence == 0 ⇒ 置 0

1368A9  xmm1 = [0x9BCEE0] = 1e-06
1368B1  xmm0 = [rbx+0x88]                   ; 第二槽的 v[2]
1368B9  xmm0 -= [rbx+0x78]                  ; 减去 v[0]
1368BE  andpd xmm0, [0x9BCED0]              ; 取绝对值（fabs 掩码）
1368C6  ucomisd xmm1, xmm0
1368CA  setae al                            ; al = (1e-06 >= |v[2] - v[0]|)
1368CD  jmp 0x1366F9                        ; → byte [rbx+0x98] = al
```

⇒ **`element+0x98` = 「第二槽存在 且 |v[2] − v[0]| ≤ 1e-06」**，
与 §35.2 的 `+0x99`（第一槽：`0x1366C6`/`0x1366CE`/`0x1366D3`/`0x1366E0 setae`，
即 `|[+0x60] − [+0x50]| ≤ 1e-06`）**逐条对称**。

**工程更正**：`row::nodeSlotFlag98` 此前只实现了 presence 判定（写成
`return n.slotAt70.present != 0;`），**是半对半错**；本轮改为与 `+0x99` 同形的完整公式，
并在 `test_row` 中补上"槽存在但 v[2]≠v[0] ⇒ false"与"改动 v[1]/v[3] 不影响结果"两类断言。

### 39.3 已并入工程 **[已证实]**

| RE | 工程 |
|---|---|
| `0x4F7600` / `0x547610` / `0x4F7690` / `0x547670` | `row::kPartGeometryObject = 0x70`、`row::kPartGeometryField = 0x90` |
| `0x1368A9`（`+0x98` 公式） | `row::nodeSlotFlag98`（**由"仅 presence"更正为完整公式**） |

`test_row` 断言：`kPartGeometryObject == 0x70`、`kPartGeometryField == 0x90`；
`+0x98` 的三种情形（缺槽 ⇒ false；`|Δ| ≤ 1e-06` ⇒ true；超出 ⇒ false）；
以及"只看 v[0]/v[2]"（把 v[1]/v[3] 设成极端值不影响结果）。

### 39.4 残留清单的更新

| 项 | 状态 |
|---|---|
| `0x547670` / `0x547610`（Item 访问器第二跳） | ✅ **结案**（§39.1） |
| `0x1368A9`（`+0x98` 另一分支） | ✅ **结案**（§39.2），工程已更正 |
| 束搜索宽度 | ✅ **结案**：是选项表参数（见 [`findings_engine.md`](findings_engine.md) 附录「完整选项键表」） |
| `Item` 的 `+0x20…+0x50` 诸字段名 | ⏳ 仍未逐个定名（缺每一格的写入者/读取者配对） |
| `0x135040` / `0x135780` 的函数体 | ⏳ 定量定性已完成，函数体未逐条转写 |

---

## 40. 元素两个容器与两个槽的**生产者**接线（含一处撤回）**[本轮，已证实]**

§38 只确定到"`0x135780` 的输出落到元素 `+0xc0`"。本轮把 `0x135040` / `0x135780` 在 `0x136350`
里的**四个**调用点连周边存储一起读了，接线完全确定 —— 并且**撤回**此前关于 `0x135040` 的一个说法。

### 40.1 `0x135040` 产出的是**两个槽**，不是容器 **[已证实]**

`0x135040` 在 `0x136350` 中被调用两次，出参是**栈上的 0x28 字节记录**：

```
--- call 0x135040 @0x136497，出参 rsp+0xf0 ---
136497  call 0x135040
13649C  cmp byte [rbx + 0x48], 0        ; ★ 该槽的 presence 字节在元素 +0x48
1364A0  je 0x136800                     ;    为 0 ⇒ 走"槽缺省"分支
1364A6  cmp byte [rsp + 0xf0], 0        ; 出参里的 present 标志
1364AE  je 0x1368A0
1364B4  rax = [rsp+0xf8] ; [rbx+0x50] = rax
1364C0  rax = [rsp+0x100]; [rbx+0x58] = rax
1364CC  rax = [rsp+0x108]; [rbx+0x60] = rax
1364D8  rax = [rsp+0x110]; [rbx+0x68] = rax     ; ★ 4 个 double -> +0x50..+0x68

--- call 0x135040 @0x1364EF，出参 rsp+0x120 ---
1364EF  call 0x135040
1364F4  cmp byte [rbx + 0x70], 0        ; ★ 第二槽的 presence 在元素 +0x70
13650C  rax = [rsp+0x128]; [rbx+0x78] = rax
136518  rax = [rsp+0x130]; [rbx+0x80] = rax
136527  rax = [rsp+0x138]; [rbx+0x88] = rax
136536  rax = [rsp+0x140]; [rbx+0x90] = rax     ; ★ 4 个 double -> +0x78..+0x90
```

⇒ **`0x135040(out, src)` 生成一个"槽"记录：`{bool present; double v[4];}`（0x28 字节）**，
两次调用分别喂给元素的 **`+0x48` 槽**与 **`+0x70` 槽**。

**撤回**：§38 记录里曾说"`0x135040` → 元素 `+0xa8`"。**该说法错误**（当时误把 `rsp+0x78/0x80`
当成 `0x135040` 的出参）。`+0xa8` / `+0xc0` 两个容器**都是 `0x135780` 产出的**（见 40.2）。
本节取代 §38 中相应的一句话。

`0x135040` 的内部形状（§7 已读，此处与新结论合并）：它用 **`1e-06`（`0x9BCEE0`）** 的
逐分量重合判定与 **`0.005`（`0x9BCEE8`）** 的对齐容差，把候选点归入已有的四个 double
（`movsd [r12+8]/[r12+0x10]/[r12+0x18]/[r12+0x20] = xmm8/xmm10/xmm9/xmm11`），
并调用 `Elem48` 析构（`0x8C4FF0`）与 `operator new`。函数体仍未逐条转写。

### 40.2 `0x135780` 产出的是**两个 `std::vector` 容器** **[已证实]**

同样两次调用，出参是**栈上的三 qword（begin/end/cap）**：

```
--- call 0x135780 @0x136552，出参 rsp+0x70 ---
136552  call 0x135780
136557  rax = [rsp+0x70]; [rsp+0x70] = 0
136565  rcx = [rbx + 0xa8]              ; 旧 begin
13656C  [rbx + 0xa8] = rax              ; 新 begin
136573  rax = [rsp+0x78]; [rsp+0x78] = 0
136584  [rbx + 0xb0] = rax              ; end
13658B  rax = [rsp+0x80]; [rsp+0x80] = 0
13659F  [rbx + 0xb8] = rax              ; cap
1365A6  if (rcx) call 0x9984b0          ; ★ operator delete(旧 begin) = 移动赋值

--- call 0x135780 @0x1365CC，出参 rsp+0x90 ---  同理 -> +0xc0/+0xc8/+0xd0
```

⇒ **`0x135780(out, src)` 生成一个 `std::vector`**，两次调用分别**移动赋值**给元素的
`+0xa8` 与 `+0xc0` 容器（旧指针走 `operator delete` = `0x9984B0`）。
它内部调用行单元的三个助手 `0x134890`(895 B)、`0x134C10`(346 B)×2、`0x8C5D40`(303 B)×2，
并按 `1e-06` 容差在两个候选点之间取一个，随后把 **32 字节的两点记录**
（`[r8]/[r8+8]/[r8+0x10]/[r8+0x18] = [rdx]/[rdx+8]/[rdx+0x10]/[rdx+0x18]`）
拷进出参。函数体仍未逐条转写。

### 40.3 结论（元素 216 字节布局的"谁写哪一格"）

| 元素字段 | 写入者 | 形态 |
|---|---|---|
| `+0x48` presence / `+0x50..+0x68` | `0x136497` 处的 `0x135040` | 槽 `{bool; double[4]}` |
| `+0x70` presence / `+0x78..+0x90` | `0x1364EF` 处的 `0x135040` | 槽 `{bool; double[4]}` |
| `+0x98` / `+0x99` | `0x1366ED..`（§39） | 两个"槽退化"标志 |
| `+0xa8..+0xb8` | `0x136552` 处的 `0x135780` | `std::vector` |
| `+0xc0..+0xd0` | `0x1365CC` 处的 `0x135780` | `std::vector` |

至此元素 216 字节里 `+0x48` 之后的每一格都**有确定的生产者**（`+0x00..+0x40` 见 §28/§33）。
