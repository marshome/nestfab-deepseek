# 逆向发现 — 核心嵌套搜索引擎与策略 (Engine / Multi / Pack)

针对 `D:\Nesting\nestfab\libcns_dump_64.dll`（内存 dump，ImageBase `0x6B4C0000`，`BAB0` 段 file offset == RVA）。
文中所有地址为 **RVA（文件内偏移即 RVA）**。标注约定：

- **【证实】** = 由反汇编指令流 / rodata 字符串直接读出
- **【强推断】** = 由调用图 + 结构体偏移 + 字符串一致推断
- **【未确认】** = 未完成，留给后续
- 所有 vtable 槽位**没有**名称（虚函数未被 `dbg::symlog` 插桩），下文槽位名是**依据行为推断**的，不要当成符号名。

---

## 0. 工具/方法备注

- `re\vtables.json` 的 `vtable_rva` 是 **vtable 起始地址**（= 前两个 qword：offset-to-top(0) + typeinfo 指针），`slots[]` 是 **slot0 所在的 6 个 qword 表**，即实际函数地址数组，`slots[0]` 位于 `vtable_rva + 0x10`。443 条全部满足这个约定（已用 raw qword 校验）。
- 由于虚函数没有 `__func__` 字符串，**无法**用 tracer 名库给槽位命名；名字只能靠行为 + RTTI 类名 + 构造器交叉定位。
- 关键定位技巧：**构造器会 `lea reg,[rip+disp]` 装载 vtable 首址**。用「构造器 → 装载的 vtable RVA」即可把「分配 + 构造」映射到具体类（脚本 `re\ctor.py`）。
- 参考文件：`re\out_29.txt`（几何/算法字符串 + 全 RTTI 类名表）、`re\vtable_methods.txt`（类 → 槽 RVA）、`re\prof2.pkl`（每函数 strings/callees/callers）。

---

## 1. `Engine::` 家族 — 引擎循环

### 1.1 引擎接口（3 个虚槽）【证实】

| 类 | vtable RVA | v0 (dtor) | v1 (deleting dtor) | v2 = **`Run`** |
|---|---|---|---|---|
| `Engine::CloudEngine`     | `0xA3CED0` | `0x755000` | `0x754FB0` | `0x26A60` (15430 B) |
| `Engine::MultiEngine`     | `0xA3CF00` | `0x7559E0` | `0x755970` | `0x755050` (2329 B) |
| `Engine::DelayedEngine`   | `0xA3CF70` | `0x757200` | `0x7571B0` | `0x756EC0` (750 B) |
| `Engine::NestingEngine`   | `0xA3CFA0` | `0x757A70` | `0x757A10` | `0x757250` (1975 B) |
| `Engine::InfiniteEngine`  | `0xA3CFD0` | `0x759B20` | `0x759AD0` | `0x759A80` (80 B) |
| `Engine::CompositeEngine` | `0xA3D000` | `0x75BC30` | `0x75BBA0` | `0x759B70` (8230 B) |
| `Engine::EquivalentEngine`| `0xA3D030` | `0x75CB40` | `0x75CAC0` | `0x75BCC0` (3569 B) |

`Run` 的签名由调用点 `0x2516E` 反推：**`Result Run(const Problem&, double time_limit, Observer&, Result&)`**
（`rdx`=Problem、`xmm3`=double、`r8`=Observer、`rcx`=返回 Result 缓冲）。

### 1.2 线程入口 / 引擎循环外壳【证实】

线程绑定（RTTI `NSt6thread11_State_implISt12_Bind_simpleIFPFvPKSt10shared_ptrIN6Engine6EngineEEPKN9Structure7ProblemEdPNS8_8ObserverEPNS3_6ResultEES7_SB_dPNS3_17CompositeObserverESF_EEEE`，vtable `0xA542F0`）
说明存在自由函数 **`void Fn(const shared_ptr<Engine>*, const Problem*, double, Observer*, Result*, CompositeObserver*?)`**。

- **`RunThreadLocalComputation` @ RVA `0x25100`**（687 B，字符串 `RunThreadLocalComputation` @ `0x9AE3C0`、`..\engine\engine.cpp` @ `0x9AE334`、断言 `engine && problem && observer && result` @ `0x9AE350`）
  - 断言 4 个非空指针后 `call qword ptr [rax+0x10]`（`0x2516E`）= **虚调用 `Engine::Run`**
    （对象首址 `[shared_ptr]` → `[obj]`=vptr → `+0x10` = **slot2**）
  - 返回值（Result，元素 `0x138` 字节）被搬入出参，然后 `0x8EEE40` 析构临时对象。
- **`0x44E0`**（3795 B，字符串 `Engine finished.` @ `0x9AC23C`、` in ` / ` sec.`、`*** EXCEPTION ***: ` @ `0x9AC258`）
  - 初始化一个计时器/日志（`0x60D980`、`0x5F3900`）
  - `[rbp+0x48]` != 0 时走「取消」分支：拼字符串 `RunThreadLocalComputation`（`0x5106`–`0x51A5` 就地 movabs 常量）+ 文件路径 `cns_local.cpp`?? 实际为常量 `cnsl_local.cpp`（`0x51B1` movabs `0x61636f6c5f736e63`="cns_loca" + `0x70632e6c`="l.cp" + 'p'），说明它把线程名写进日志
  - `[rbx]` = `shared_ptr<Engine>`，`mov rax,[rdx]; call [rax+0x10]` @ `0x4591` → **再次虚调用 `Engine::Run`**
  - 捕获 `...`（`0x9989A0` / `0x998BC0` = `__cxa_begin_catch`/`__cxa_end_catch`，`0x52A4 cmp rdx,1` 判定 exception 类型），打印 `*** EXCEPTION ***: ` + `what()`
  - **结论**：`0x44E0` 是**每个 worker 线程的循环外壳**（跑一个 Engine 实例、计时、异常兜底，输出 `Engine finished.` / ` in N sec.`）。**【证实】**

### 1.3 Observer 接口（6 虚槽）与三个观察者【证实 + 强推断】

`Structure::Observer` vtable `0xA53550`（6 槽，实现全是 `ret`/`xor eax,eax;ret` 的弱默认）。

| slot | 推定名 | 依据 |
|---|---|---|
| v0 | `Start()` 回调 | `BestObserver` v0 = `0x756CF0` 转发到包裹对象的 `+0x10`(=slot0) |
| v1 | `Stop()`/`Finish()` 回调 | 同上转发到 `+0x18`(=slot1) |
| v2 | `bool ...(bool)` | 基类 `0x7C2460` = `xor eax,eax; ret` |
| v3 | **`NewNestingFound(bool)`** | `BestObserver` v3 = `0x755A50`：`mov rcx,[rcx+0x10]; mov rax,[rcx]; jmp [rax+0x18]` → 转发到被包裹者的 **slot3**；被包裹者（`Structure::Observer`）slot3 基类为空实现，说明这是一个**布尔通知型回调**，`EquivalentObserver` v5 `0x75DDF0` 的字符串 `NewNestingFound`(`0x9AE400`) + `..\engine\engine.cpp` 与之呼应 |
| v4 | **`NewIntermediateSolutionFound(...)`** | `BestObserver` v4 = `0x755A80`（4242 B）+ 字符串 `NewIntermediateSolutionFound ` @ `0x9AC206`（引用函数 `0x33A0`）；`CompositeObserver` v4 = `0x75CDA0`（4111 B） |
| v5 | 最终结果 / `NewNestingFound`（另一路径） | `BestObserver` v5 = `0x755A60`（18 B）：`rcx=[rcx+0x10]; rax=[rcx];`**`jmp [rax+0x28]`（slot5）**；`EquivalentObserver` v5 = `0x75DDF0` = `NewNestingFound` |

- **`Engine::BestObserver`** vtable `0xA3CF30` = `[0, 0xA19090, 0x756CF0, 0x756B20, 0x755A40, 0x755A50, 0x755A80, 0x755A60]`
  → 它是个**纯转发装饰器**：`[this+0x10]` 存被包裹 `Observer*`，v0/v2/v4/v5 全部 `jmp [wrapped_vptr + 0x10/0x18/0x28/0x30]`。**它自己唯一的真实逻辑在 `NewIntermediateSolutionFound`（slot4，`0x755A80`）**——所以 v4 才是承载「保留最好解」语义的槽，v5 只是个转发。
- **`Engine::CompositeObserver`** vtable `0xA3D060`：v4=`0x75CDA0`(4111 B)、v5=`0x75CD30`(100 B)、v2=`0x75CBC0`。构造器 **`0x8D4500`**（751 B；字符串 `CompositeObserver` @ `0x9AE3E0`、`m_state && m_problem && m_observer` @ `0x9AE378`、`..\engine\engine.cpp`）。它唯一被 `0x759B70`（`CompositeEngine::Run`）在 `0x759DE7` 调用 → **CompositeEngine 为每个子引擎建一个 CompositeObserver，聚合并发结果**。
- **`Engine::EquivalentObserver`** vtable `0xA3D0A0`：v5=`0x75DDF0`（621 B，`NewNestingFound`）、v4=`0x75E060`（128 B）；v2/v3 转发到 `[this+8]`。用于把「等价问题」（`m_equivalent_problem`，见 `0x9AC4A8` 断言）上的解映射回原问题。
- `Multi::TraceObserver`（`0xA3B700`）v4=`0x5ED40`、v5=`0x5F030`（7075 B）→ 全量落日志；`Multi::NestingObserver`（`0xA3B7C0`）v2=`0x697060`(66B)、v3=`0x6970B0`(9B)；
  `Multi::WrapObserver`（`0xA3B5E0`）v2=`0x7D2160`(55B)。

`CompositeObserver` 的 `v4` 里有大段 `vector<pair<double, ...>>` 的深拷贝（元素 `0x78`/`sizeof=120`：`movabs rdx,0x6f96f96f96f96f97` 是 **÷120** 的魔数），**证实它保存的是「一批 nesting + 评分」的容器**。

### 1.4 引擎循环：什么触发一次新迭代【强推断 + 部分证实】

- **`Engine::MultiEngine::Run` @ `0x755050`（2329 B）** 是主编排：
  1. `0x755120` 读 `Problem::seed`（`0x24A80` = `movzx eax,[rcx+8]`），`0x755208` 读 `Problem::nb_max_threads`（`0x24A90` = `mov eax,[rcx+0xc]`）→ `cvtsi2sd` 存到 `[rbx+0x40]`（Supervisor 的 nr_threads）。**【证实】**
  2. `0x755260` 调 **`0x2F860` = Supervisor 构造包装**：内部先 `0x4EC00` 构造 **`AlgoParameters`**（5633 B，含 `nb_max_threads`、`nb_strips_first`、`nb_strips_filling_advanced`、`enable_database`、`database_relax_every`、`enable_beautifier`、`nb_iterations_before_tiling`、`enable_beam`、`beam_frequency_ratio`、`beam_distinct_angle`、`enable_rectangle`、`force_rectangle`、`nb_rectangle_try`、`nb_iterations_before_rectangle_dual`、`nb_iterations_before_rectangle_advance`、`nb_rectangle_advance_try`、`enable_last_compaction`、`enable_rotate_compact_postop`、…），再 `0x2F2C0`（1432 B）构造真正的 **`Multi::Supervisor`**。
  3. `0x7552A7` 之后按一个整型 state（0/1/2，来自对 observer 的两次虚调用 `0x7555AB`/`0x7555D6`，返回 bool）选择 **3 种不同的 Supervisor 包装**，分别 `0x7C24C0` 构造。**【强推断：state 决定「本地 / 云端 / 混合」三条路径】**
  4. 后续 `0x7554E0`–`0x755700` 是 **std::map<string,...> 的字符串查找循环**（`0x63F300` = `std::string::compare`，`0x979FE0`/`0x97A040` = `_Rb_tree` 的 lower/upper bound；`mov r8d,4` + `lea rcx,[rsi+0x10]` + `movabs` 常量组 `'seed'`/`'strategy'`… —— `0x755138` 处 `mov dword ptr [rsp+0xb0],0x64656573` = ASCII `"seed"`）→ 从 `Problem` 的 extra-parameters map 里取 `seed` 等键。
  5. `0x755767` 调 `0x987220`(702 B)、`0x7557C0` 调 `0x930180`(313 B) → 启动 Supervisor 线程。
- **`Supervisor::Run` @ `0x827F0`（5274 B）**（由线程绑定 `NSt6thread11_State_implISt12_Bind_simpleIFPFvPN5Multi10SupervisorEjjES4_jjEEEE`，vtable `0xA54320` 佐证：`void Fn(Supervisor*, uint, uint)`）：
  - `0x82831` `0x500710`(175 B) + `0x8283C` `0x4FF910`(8 B) → 准备 strategy 描述器 / 取 problem
  - `0x8286E`–`0x829D2`：把 `rdx`（strategy 描述器，`StrategyDescriber`）的字段成批拷到栈上局部 `struct`：偏移 `+0x20/+0x24/+0x28/+0x2c/+0x30/+0x60/+0x68/+0x69/+0x6a/+0x6c/+0x70` —— 和 `StrategyAdder` 里读的 `[rbx]..[rbx+0x20]` 一一对应。**【证实：策略描述器是一个 ~0x28 字节 POD 配置结构】**
  - `0x832BD` 调 `0x342E0` = **`Multi::NestingNester` 构造器** → 每条策略就是一个 Nester 实例
  - `0x83328` `0x4DD60`、`0x8333B` `0x6BF40`、`0x8334B` `0x64330` → 包一个 observer（`Multi::WrapObserver`/`TraceObserver`）
  - `0x835E8` / `0x83856`（`call qword ptr [rax+8]`）和 `0x30B60`/`0x30EB0`（Supervisor 的 dtor 对）→ 收尾
  - `0x838BB` `0x697150`、`0x83876` `0x69A370` → 取消/通知
- **`Engine::InfiniteEngine::Run` @ `0x759A80`（80 B）是最干净的「迭代循环」证据【证实】**：
  ```
  ucomisd xmm3, [rip+...] (= -1.0，位于 0x9AE740)
  if (time_limit == -1.0)  { r9 = [rsp+0x60]; call 0x757AE0 }   ; 无时限 → 走 NestingEngine::Run 的无限模式
  else { rdx=[[rdx+0x10]](inner engine); rcx=[rsp+0x60](result); call [inner_vptr+0x10] }  ; 否则直接委托内层引擎
  ```
  → `-1.0` 是**「无限时间」的哨兵值**；`MakeMaxTimeEngine` / `MakeSkipSmallTimeEngine` 就是构造 `DelayedEngine` 的两个工厂（见下）。
- **`Engine::DelayedEngine::Run` @ `0x756EC0`（750 B）** 用于「延时后剩余时间再跑一轮」；`Engine::CompositeEngine::Run` @ `0x759B70` 里 `0x759C88` 构造 `0x52DB30`(112 B) 的对象 → 循环 `0x75B445` 调 `[rax+0x10]`，每个子引擎配一个 `CompositeObserver`（`0x759DE7`）。

### 1.5 `MaxTime` / `skip small time` / 时间限制【证实常量】

- **`MakeMaxTimeEngine` / `MakeSkipSmallTimeEngine` 是返回 `shared_ptr<Engine::Engine>` 的自由函数**，其局部类 `AuxEngine` 的 RTTI 留在 rodata：
  - `0x9AE440`：`*ZN6Engine17MakeMaxTimeEngineERKSt10shared_ptrINS_6EngineEEdE9AuxEngine`
  - `0x9AE4A0`：`*ZN6Engine23MakeSkipSmallTimeEngineERKSt10shared_ptrINS_6EngineEEdE9AuxEngine`
  - `0x9AE520` / `0x9AE5C0`：对应的 `_Sp_counted_ptrIP...AuxEngine...`
  - `0x9AE3AB`：`!original.empty()`（参数校验）
  → **函数体本身没有被 tracer 命名，且未在 `prof2.pkl` 里以名字出现，需要按「返回 shared_ptr 且构造 AuxEngine」的模式定位。【未确认：确切 RVA】**
- **时间限制的实现：`Multi::SupervisorCanceller::ProbeCancel` @ `0x30030`（485 B）【证实】**
  ```
  if ([this+8] == 0) assert(...'..\multi\supervisor.cpp', line 0x366)     ; 0x9AECE7 路径
  if ([this+0x30] != 0) return 1                                          ; 已取消
  sup = [this+8]; prob = [sup+8]
  if ([prob+0x408] == 0.0) { canc = (0x2FEF0(prob) != 0); }
  else {
      x = 0x5F3980(prob)          ; 取已用时间
      if (x / [prob+0x408] > 1.0) canc = 1;    ; 常量 double 1.0 @ 0x9AEE88
  }
  if (canc) { [this+0x30]=1;                 ; 粘滞标志
              cv = [sup+8+0x528]; nothrow lock(cv); __gthread_cond_broadcast(cv); unlock(cv); }
  return [this+0x30];
  ```
  → **`Problem+0x408` 是「允许时间上限（秒）」**；`elapsed/limit > 1.0` 即触发全局取消（**比例阈值 = 1.0，不是 0.98**）。
  「**skip small time**」的语义由此对应：`MakeSkipSmallTimeEngine` 给内层引擎的 time limit 是**很小的一段**，若该段内没找到改进就跳过（其 `AuxEngine` 的 `Run` 直接不调用内层），是 `DelayedEngine` 的特化。
- **`Utils::Canceller` 基类 vtable `0xA3BD70`**，slot2（`ProbeCancel` 接口，`bool()`）基类实现 = `0x7D7D20` = `xor eax,eax; ret`（**默认永不取消**）。具体子类：

| 类 | vtable | slot2 实现 | 行为 |
|---|---|---|---|
| `Multi::SupervisorCanceller` | `0xA3BA90` | `0x30030` (485 B) | 时间用尽 / 外部取消 → 广播 condvar（**总闸**） |
| `Multi::CompactCanceller` | `0xA3B870` | `0x7D2610` (991 B) | 字符串 `Compact cancelled !` @ `0x9AECFF`；压缩后优化阶段的取消闸 |
| `Multi::NoFitMapCanceller`  | `0xA3B8E0` | `0x7D29F0` (698 B) | NoFit map 计算阶段 |
| `Multi::RCompactCanceller` | `0xA3B910` | `0x7D2CB0` (9 B) | **`xor eax,eax;ret`** → 旋转压缩阶段**不可取消** |
| `Tiling::WarpCanceller`   | `0xA3D160` | `0x7D7940` | tiling warp |

---

## 2. `Multi::Supervisor` / 策略调度

### 2.1 Supervisor 对象

- vtable `0xA3B4D0`，**只有 2 个槽**：`0x30B60`（847 B，析构：释放 6 个 mutex/condvar `+0x500..+0x528`、清理 `+0x4d0` 的 list<shared_ptr>、把 vptr 装成 `0xA3B4E0`）、`0x30EB0`（862 B）。
- `Supervisor` 成员（由 dtor 与 `Supervisor::Run` 读写归纳，**【强推断】**）：
  - `+0x0` vptr
  - `+0x8` `Implementation*`（真正的大脑；`ProbeCancel` 用 `[[this+8]+8]` 取 `Problem`）
  - `+0x4c8`,`+0x4d0`,`+0x4e0` 若干 `std::list<shared_ptr<...>>`（已启动的策略/引擎）
  - `+0x500..+0x528` 6 个 `pthread_mutex_t`/`cond_t`（**一个用于「有新结果」通知，`+0x528` 就是 ProbeCancel 广播的那个**）
  - `+0x3c4` 一个 int（`0x68A6E0` 读）—— 与线程数/迭代数相关
- `0x30270`（333 B，字符串 `m_implementation->m_strategist` @ `0x9AED48`、`strategist` @ `0x9AEE20`）→ **`Supervisor::Strategist()` 访问器**。

### 2.2 「策略」= `StrategyDescriber` 的 POD 描述符 + `Strategist` 的 `operator()`

线程绑定 `...IFPFvPN5Multi10SupervisorEjjE...`：**每条策略启动一个线程**，入口 `Supervisor::Run(Supervisor*, unsigned strategy_id, unsigned rank)`（`0x827F0`）。

**调度核心：`Multi::AdvancedStrategist::operator()` @ `0x2DF60`（481 B）【证实】**
```
if ([this+0x18]+0x81 != 0) { c = construct cfg{mode=2, ..., ratio=1.0}; Add(c); }   ; 走 0x2CCF0(0x2C2B0)
else if (CanX([this+0x10])) Add(mode=2,...);      ; 0x4FC260
else if (CanY([this+0x10])) Add(mode=3,...);      ; 0x4FC2F0
else if (CanZ([this+0x10])) Add(mode=4,...);      ; 0x4FC300
else                        Add(默认, 0x2D330);   ; 无 cfg
```
- 三处 `movsd` 常量 **全部 = `1.0` @ `0x9AEC90`**（`0x2DFE3`/`0x2E060`/`0x2E0DA`）→ 配置里的 double 字段是**「比例」参数，默认 1.0**。
- 配置结构（栈上 `[rsp+0x20]`，40 字节，`0x2CCF0` 里被拷来拷去）：
  `+0x00 int mode`，`+0x04..+0x0a` 6 个 bool，`+0x0c int n`，`+0x10 qword`，`+0x18 int`，`+0x1c int`，`+0x20 double ratio`。

**`0x2CCF0`（264 B）= 配置的级联展开【证实】**：
```
call 0x2C4D0(cfg{mode, n=cfg.n})                     ; 第一遍
n = cfg.n
if (n > 2)  { cfg.n = 2;          call 0x2C4D0 }     ; 第二遍，收窄 n
if (n > 4)  { cfg.n = (n+1)/2;    call 0x2C4D0       ; 第三遍
              cfg.n = n-1;        call 0x2C4D0 }     ; 第四遍
```
→ 同一个策略被**按 `n` 递减的多个变体重复添加**：`n → 2 → (n+1)/2 → n-1`。这是「**逐步放宽/收窄搜索预算**」的级联调度（一种 *iterated deepening of the effort budget*，不是遗传算法）。

**`StrategyAdder::Add`（本质是 `0x2C4D0`，2072 B）【证实】**：读配置的各字段，`new` 出具体 Nester 并挂到策略链上。已由「分配大小 + 装载的 vtable」证明的分支：

| 分支（`0x2C4D0` 内偏移） | 分配大小 | 构造器 | → 类 |
|---|---|---|---|
| `0x2CB50` (`[rbx]==2`) | `0x20` | `0x77440` | **`Multi::RectangleNester`** |
| `0x2CB70` (`[rbx]==3`) | `0x20` | `0x8F210(…, r8d=0)` | **`Multi::RowNester`**（非 pipe） |
| `0x2CB91` (`[rbx]==4`) | `0x20` | `0x8F210(…, r8d=1)` | **`Multi::RowNester`**（pipe 模式，`[rax+0x161]`=`SetPipeMode`） |
| `0x2CAC3` (`mode==1`) | `0x9f8`→`0xa40` | `0x342E0` | **`Multi::NestingNester`**（真正的主打包器） |
| `0x2CA30` (`[rbx+5]`=`enable_last_compaction`?) | `0x9f8` | `0xB0270` | **`Multi::CompactNester`** |
| `0x2CA77` (`[[rsi+0x18]+0x168]`，来自 `0x4FC380` 返回的标志字节) | `0x9e8` | `0xB3A70` | **`Multi::FilterNester`** |
| `0x2C580`/`0x2C953` | `0x28` | `0x780E0` | 一个带 `n`（`[rbx+0xc]`）的包装（**`Multi::LimitedNester`？【强推断】**） |
| `0x2C604` (`[rsi+0x10]`+`0x4FC2E0`) | `0x60` | `0x7EE50` | **`Multi::NoFillNester`** |

`0x2CA01` 分配 + `0x4AAD0` 构造 = **`Multi::LimitedNester`**（`0x4AAD0` 装载 vtable `0xA3B660`）。
`0x2CAB1`→`0xB0000`+`0xB0040`/`0xAFD60` = **SheetSelector 选择**（`AllSheetSelector` `0xA3B840` / `RandomSheetSelector` `0xA3BA60` / `NoMixSheetSelector` `0xA3B9D0` / `LargestSheetSelector` `0xA3BAC0`）。这几个由 `[rdi+0x2c4]`（`0x4FC250`）与 `[rdi+0x2c0]` 两个标志驱动。

### 2.3 线程数与 `SetLocalMaximumThreads`

- `SetLocalMaximumThreads` 字符串 @ `0x9ACD12`，引用函数 **`0xD3B0`**（导出 API 层）→ 写入 `Problem`/`LaunchingOrder` 的字段。
- **`nb_max_threads` @ `0x9AE39B`，引用函数 `0x25C20`（2333 B，`..\engine\engine.cpp` 区）与 `0x4EC00`（`AlgoParameters` 构造）**。
- `Engine::MultiEngine::Run` 在 `0x755208` 通过 `0x24A90`（`mov eax,[rcx+0xc]`）读到一个 int 并 `cvtsi2sd` 存 `[rbx+0x40]` → **就是 `nb_max_threads`**，传给 Supervisor。【证实】
- `0x4EC00` 里还读到 `nb_threads`（见 `0x1B64E0` 断言 `nb_slices == uparams.nb_threads`）。
- `Packer Cache max threads: ` @ `0x9BD49E`（`0x76A130`）→ PackerCache 也有自己的线程上限。
- **未确认**：`nb_max_threads` 的确切默认值（需要追 `0x25C20` 的 map 默认值写入处）。

### 2.4 结果合并

- `Multi::CompositeNester`（vtable `0xA3B790`，注意 `vtables.json` 里没有它，需从 rodata RTTI 表补）—— 从名字与 `Engine::CompositeEngine` 的 `CompositeObserver`（`0x8D4500`）可判定为「**跑多个子 nester 取最好**」。它的实际槽实现 **【未确认】**。
- 合并的具体载体 = `Observer::slot4 NewIntermediateSolutionFound`：
  - `CompositeObserver::v4` = `0x75CDA0`（4111 B，聚合 + 打分 + 深拷贝 vector）
  - `BestObserver::v4` = `0x755A80`（4242 B，同样深拷贝 `vector<pair<double,…>>`，元素 120 字节）
  - `Observer::slot5` = `0x755A60`/`0x75DDF0` = 简单的「有新 nesting」转发（最终 `BestObserver` 保最好解）
- 日志串 `Improving best` @ `0x9AC22D`（由 `0x33A0` 引用）、`NewIntermediateSolutionFound ` @ `0x9AC206` + ` parts and ` + ` sheets.`、`Engine finished.` + ` in ` + ` sec.` @ `0x9AC23C` 共同构成循环的进度输出。

---

## 3. 具体 Nester（放置启发式）

**公共接口（6 虚槽）【强推断】**：v0 dtor、v1 deleting dtor、v2 **名字/`Name()`（返回 `const char*`）**、v3 **`bool Prepare/Setup(...)`**、v4 **`double Estimate()`**、v5 **`Nesting Run(...)`（放置主体）**。证据：v2 在 `TilingNester`=`0xB4430`、`DatabaseNester`=`0xB4430`、`RowNester`=`0xB4430`、`RectangleNester`=`0xB4430` 等多个类里是**同一个 4 字节函数**（`mov eax,<imm>; ret` 返回常量字符串指针），v3 常是小函数，v5 总是该类最大的函数（1650 B … 16 KB）。

| 类 | vtable | v5 (主体) | 启发式（一句话 + 证据） |
|---|---|---|---|
| `Multi::FlipNester` | `0xA3B490` | `0x4B870` (3496 B) | **把整个问题镜像/翻面后再嵌套**。`0x4B933` 处 movabs `0x7261726f706d6574`+`0x6570696c665f7961`+'d' = ASCII **`"temporary_flipped"`**，随后 `0x4FB5F0` 生成翻转副本、`0x4B680` 跑嵌套。可配 `flip_parts_ratio`。 |
| `Multi::FilterNester` | `0xA3B4F0` | `0xB3AE0` (2254 B) | **先用一个廉价过滤器/下界剪掉不可能改好的解，再嵌套**。v4=`0xB46F0`(894 B) 与 `NoFillNester`/`CompactNester` 共享（基类默认）；字符串 `Filter ` @ `0x10166192` 区；构造器 `0xB3A70`(98 B)。 |
| `Multi::NoFillNester` | `0xA3B530` | `0x7F240` (8440 B) | **禁止「填空/补洞」的嵌套**：字符串 `NoFill(` + `%llu`，v2=`0xB4440`。即不允许把零件塞进已有 nesting 的空隙，只做整体排布（用于多解探索的多样性）。 |
| `Multi::TilingNester` | `0xA3B5A0` | `0x46940` (16258 B，最大) | **用 Tiling 模块（`Tiling::BoxMultiTiler`/`SqueezeMultiTiler` + `BiModulePattern`/`MultiOrientedPartPattern` + Density/Quantity/Reusable/…Evaluator）把板材切成重复图案，再对图案打包**。构造器 `0x45AF0`(1637 B) 里同时装载 vtable `0xA3B5B0` 与 **`Multi::PartUpdaterLimiter` `0xA3BA10`**（增量更新零件）；字符串 `Tiling` @ `0x10156208`、`strategy`。 |
| `Multi::CompactNester` | `0xA3B610` | `0xB13D0` (9393 B) | **在已有嵌套上做 compaction（滑动/旋转去空隙）后再评估**；构造器 `0xB0270`，分配 `0x9f8` 字节。 |
| `Multi::LimitedNester` | `0xA3B650` | `0x4AB40` (1650 B) | **限制型包装器**：只允许前 N 个零件/前 N 个角度，或对子 nester 做「限量」调用（v3=`0x4A960`，v4=`0x4A8D0`(140 B) 与 FlipNester v4=`0x4B2B0`(108 B) 同源 → 两者与 `0x4A960`/`0x4B1C0` 共享代码，说明 Limited 是 Flip 的同族包装）。 |
| `Multi::NestingNester` | `0xA3B690` | **`0x378E0` (14374 B)** — 主打包器 | 见 §3.1。 |
| `Multi::DatabaseNester` | `0xA3B740` | `0x5B250` (4495 B)【确认：`vtables.json` 槽 5】 | **用历史/数据库（`tree_db` + `bucket_manager`）缓存并复用过去算过的 nesting**。v2/v4 是 4 B/6 B 返回常量，v3=`0x5B1C0`(37 B)。相关：`tree_db.cpp`（`0x1C12D0`…）、`bucket_manager.hpp`。字符串/断言见 `hashes`、`bucket_manager`。 |
| `Multi::CompositeNester` | `0xA3B790` | **【未确认】** | 「跑一组子 nester 取最优」（与 `Engine::CompositeEngine` 同构）。 |
| `Multi::RectangleNester` | `0xA3B800` | `0x75FB0` (5261 B) | **矩形快速路径**：所有零件/板都矩形时用解析排布（`enable_rectangle`/`force_rectangle`/`nb_rectangle_try`/`nb_iterations_before_rectangle_dual` 驱动；源文件字符串 `..\multi\rectangle_nester.cpp` @ out_29）。v3=`0x6C9B0`(41 B)，v4=`0x77780`(402 B)。 |
| `Multi::MultiTorchNester` | `0xA3B8A0` | `0x7BCC0` (12232 B) | **多火焰/多头切割模式**：断言 `res <= y * 1.001` @ `0x10164004`、调试串 `test2` @ `0x10164021`；与 `Tiling::MultitorchEvaluator`/`OldMultitorchEvaluator` 配合（`SetMultiTorchMode`/`SetDetailedMultiTorchObjective`）。 |
| `Multi::RowNester` | `0xA3BB30` | `0x913E0` (12380 B) | **按「行/条带」放置**：字符串 `Row ` + `Pipe ` + `%llu`，`Pipe` 由 `0x8F210(…,r8d=1)` 的第二个参数选择（`SetRowMode`/`SetPipeMode`/`GetRow`/`GetNumberOfRows` 佐证）。 |
| `Pack::BestNester` | `0xA3B400` | `0x15E410` (316 B) | **遍历一组子 nester（`rdi=vector<...>`，`0x15E447` 取 begin/end），逐个调用其虚 `+0x10` 槽，然后 `0x15E6A0` 做比较/择优**。 |
| `Pack::KnapsackNester` | `0xA3B430` | `0x15DD70` (59 B) | **背包式选件**：读 `[rdx+8]`、`[rdx+0x14]` 两个整数参数转调 `0x15D1F0`（容量/件数），`r9d=1`。 |
| `Pack::RecursiveNester` | `0xA3B460` | `0x165680` (125 B) | **递归装箱**：`0x5F4310`/`0x5F4340` 是一对 RAII/lock guard，中间转调 **`0x164FE0`（递归主体）**；v0/v1 是 2119/7633 B 的 dtor（说明对象持有一个大容器）。 |

补充：`Pack::Recursive`/`Pack::BestCuts` 类型名 @ `0x9BD86E`/`0x9BD87E`（由 `0x99BB90` 打印）；`Packer`/`Packer raw` @ `0x9BD292`/`0x9BD299`。

### 3.1 `Multi::NestingNester::Run` = 0x378E0（14374 B）——主打包器【强推断】

构造器 `0x342E0`（422 B）证实对象布局：
- 先 `0xB4470`（基类 `Multi::Nester` 构造）→ vptr `0xA3B6A0`
- `[+0x18]`/`[+0x20]` = 传入的 `StrategyDescriber` 的两个 qword（`[rdi]`,`[rdi+8]`），即 **mode/flags + double 参数**
- `[+0x28]` = `cvttsd2si(0x33A70(0xB4D90(ctx)))` → **int 迭代/预算上限**
- `[+0x30]` = `0x52C440(ctx) / 0x4F8380(0x523050(ctx))` → **double 比例**（很可能是 `nesting_pow_boost`）
- `[+0x38..+0x9F8]` = **`std::mt19937` 状态**（`imul eax,eax,0x6c078965` = MT19937 种子常数，`[+0x9f8]=0x270=624`）→ **有随机数发生器**
- `[+0xA00]` = `0x4F0C20(...)` 构造的 `Tiling::PackerCache` 之类
- 断言（同函数字符串）：`parameters().nesting_pow_boost >= 1.0` @ `0x10153808`、`deg_steps.size() == try_parts_ratio.size()` @ `0x10153880`、以及键名 `sheet`/`packer_cache`/`biggest`/`strategy`/`Run`

`Run` 的主要 callee（`0x378E0`）：
- `0x31DB0`（2284 B，字符串 `supervisor`）→ 取 supervisor/ctx
- `0x3F070`/`0x434D0`（`..\multi\nesting_context.cpp`）→ `Multi::NestingContext` / `NestingContextPool`
- `0x344D0` (6748 B)、`0x35F30` (6436 B) → 两段核心排布
- `0x185750`/`0x185A40`/`0x187020`/`0x189CA0`（都在 `tiled_multipart.cpp` 区，见 `..\nesting\tiled_multipart.cpp`）
- `0x4F1F60` (2299 B)、`0x65F350` (751 B)、`0x678AE0` (590 B, `compact.hpp` 区)

---

## 4. `Multi::Node` / `TerminalNode` / `SplitNode` / 束搜索

**【证实】是束搜索 / 树搜索**：

- **`Multi::Node`** 基类 vtable `0xA3BB00`（`N5Multi6NesterE` 旁边，slot 布局 4 槽）。
- **`Multi::TerminalNode`** vtable `0xA3B570`：v2 = `0x974F0` = **`movsd xmm0,[rcx+0x48]; ret`** → **返回 `+0x48` 处的 double 作为该节点的价值/评分**。
- **`Multi::SplitNode`** vtable `0xA3BB70`：v2 = `0x97510` = **`movsd xmm0,[rcx+0x50]; ret`** → 内部节点的评分在 `+0x50`。
- 两者 v3 分别是 `0x97500`/`0x97520`（6 B，另一 double/指针取值）。
- `Multi::Node::NodeSize` 逻辑由 `NodeSize` 字符串 @ `0x9C2460` 区佐证（该 RVA 同时被 CryptoPP 的 `ByteQueue` 复用，属**同名不同函数**，注意别混）。
- **树数据库 `..\nesting\algos\tree_db.cpp`**：`0x1C12D0`（892 B，断言 `itr != m_nodes.rend()` @ `0x10221912`，`__func__ = FindNode` @ `0x10222776`）、`0x1C1650`（12 B）、`0x1C16E0`/`0x1C18A0`/`0x1C1A60`/`0x1C1F30`/`0x1C2110`/`0x1C37A0`/`0x1C4350`。
- **`0x22CCA0`（2916 B）= 束搜索的树准备**，字符串 `Preparing tree for beam ` @ `0x9C1E94`、`Length reduced ` @ `0x9C1E...`、`Simplified `、`Offsets computed `、`Tree Logged `。它 `call 0x1C1650`（tree_db）然后遍历一个锁保护的同构容器（`0x63F6C0`/`0x63F6B8` = `pthread_mutex_lock/unlock`）并对每个元素 `0x978010(memcpy)` + `0x868F70(set value)` 填 beam 参数。
- **beam 参数**（`AlgoParameters::AlgoParameters` @ `0x4EC00`，5633 B）：
  - `enable_beam` @ `0x9AFB62`
  - `beam_frequency_ratio` @ `0x9AFB6E`
  - `beam_distinct_angle` @ `0x9AFE2D`
- **束宽常量：【未确认】**。`beam_*` 三个键值都从 `Problem` 的 map / 参数文件读入，**没有在代码里找到硬编码的 beam width 立即数**。`0x22CCA0` 里 `0x1C1650` 返回的 `eax`（存 `ebp`）被写入每个树节点（`0x22CD57 mov edx,ebp; call 0x868F70`）——那是一个 **int 参数**，最可能是 beam width 或 beam 层数，但需要看 `0x1C1650` 的实现才能定名。**【未确认，但这是下一步最小切入口】**
- **节点扩展/评分函数**：`Multi::SplitNode` 的 `+0x50` double 是评分；`TerminalNode` 的 `+0x48` double。具体的 split/expand 例程 **【未确认】**（`Node`/`SplitNode`/`TerminalNode` 的 dtor 分别在 `0x6938E0`/`0x693870`、`0x6AC2E0`/`0x6AC250`）。
- `Multi::BeamNesting` 与 `Multi::HoleRenester` **在 `vtables.json` 里没有 vtable**，只在类型名打印函数 `0x99A070`（字符串 `Multi::HoleRenester` @ `0x9B0ACF`、`Multi::Compact` @ `0x9B0A3A`、`Multi::Rectangle` @ `0x9B0A64` 区）里作为**名字字面量**出现。→ 这两个类是 **`_GLOBAL__N_1` 内部类或纯非虚类**。【未确认其实现 RVA】

---

## 5. Compaction 后优化

### 5.1 `Compact::Compacter::Implementation`（vtable `0xA3D470`）

- 槽：v0 `0x774F50`(147 B)、v1 `0x774EB0`(155 B)、**v2 `0x7F4140`(115 B)**。
- `0x7F4140`【证实】：
  ```
  ctx = [this+0x40];  a = 0x4FC3B0(ctx)             ; 取某个 geometry/box 对象
  edi = 0x54D100(a);  rbp = 0x54D120(a)             ; 两个 int 属性（很像 n_rows / n_cols）
  obj = operator new(0x1E8)
  xmm1 = [this+0x48]  (double)
  xmm2 = xmm1 ; r9d = edi ; [rsp+0x20] = rbp
  obj = 0x252B60(obj, xmm1, xmm1, r9d, rbp)          ; 真正的工作函数
  ```
- **`0x252B60`（1389 B）= Compacter 工作内核【证实】**：
  ```
  [obj+0]  = f1 ; [obj+8] = f2
  [obj+0x10] = min(f1,f2) / 10.0        ; 常量 double 10.0 @ 0x9C2BB0
  xmm7 = -0.0（符号位掩码，@0x9C2BC0）；xmm8 = 0.0
  xmm1 = 0 - f1（xorpd 符号翻转）
  构造区间/网格 (xmm1, 0, f1+f2) → 0x5CA780(…) / 0x5C6BE0(…)
  0x2664F0(obj+0x18, grid, 0, 1)        ; 枚举网格
  然后遍历结果：对每个候选 (rsi[i]+0x18 .. rsi[i]+0x20) 逐项 move
  ```
  → **Compaction = 在 `min(w,h)/10` 的网格步长上做「滑动 + 旋转」的局部搜索**；`[+0x10]` 的 `min/10` 就是**位移步长（tolerance / mesh）**。
- 模块字符串（`compact.hpp` 区，`0x9BED00`/`0x9BFE99`/`0x9C048F`/`0x9C0CAA`）：`compacting ...`、`before_shake` / `shaker_` / `=>` / `after_shake`（**"shake" 抖动**）、`Compaction success : `（`0x9C0B0E`，由 `0x1EC0B0`(5758 B) 打印）、`Swap Postop begin` / `Trying swap ` / `Swap 180 begin` / `Rot 180 computed` / `Trying swap180 `（`0x1DA0C0`，14251 B）。
- `compact.hpp` 的具名函数（可由 `__func__` 定为函数）：
  - **`CompactAux`** = `0x1DA0C0`（14251 B，`..\nesting\algos\compact.hpp`）+ `0x677CB0`（1395 B）+ `0x677CB0` 同族
  - **`RotateCompact`** = `0x1F2D00`（1766 B）+ **`0x678230`（885 B）**
  - **`NoOverlap`** = `0x678630`（595 B，断言 `groups.empty() || (groups.size() == nesting.nesteds().size())`）
  - 断言 `sol.nestings().size() == 1`（多个 compact 函数共享）
- **`RotateCompact @ 0x678230` 的接受测试【证实】**：
  ```
  if (1e-6 > param)   return 0;                 ; 常量 double 1e-6 @ 0x9BF5D0
  ... 构造一个候选 nesting（0x1F0920）并做 compact（0x51E7E0）...
  ```
  → **只有当传入的改善阈值/时间片 > 1e-6 时才尝试旋转压缩**；这是「小量不折腾」的早退。
- `RCompact::RotateLogger` vtable `0xA533D0`，8 个槽全是 **1–5 字节的空函数**（`0x7B3080`/`0x7B3070`/`0x7B3030`/…）→ **纯观察者/日志钩子接口（Release 版无操作）**，真正的「接受/拒绝」判定在 `RotateCompact` 内部。**【证实】**

### 5.2 接受测试（综合）【强推断】

- 阈值常量：`1e-6`（`0x9BF5D0`，RotateCompact 早退门限）
- 触发调度的参数键：`enable_last_compaction` @ `0x9AFD52`、`enable_rotate_compact_postop` @ `0x9B04CF`、`nb_iterations_before_rotate_compact_postop` @ `0x9B04F0`
- 成功判据打印 `Compaction success : `，失败/被取消打印 `Compact cancelled !`（`0x9AECFF`，由 `Multi::CompactCanceller::ProbeCancel`/`0x7D2610` 与 `0x68A6E0` 输出）
- 三者关系：`Multi::CompactNester`（策略层，`0xB13D0`）→ `Compact::Compacter::Implementation`（`0x7F4140` → `0x252B60`，网格滑动/旋转）→ `RotateCompact`/`CompactAux`（`compact.hpp` 的几何级去重叠与 180° 交换）→ `RCompact::RotateLogger`（日志钩子）；全程由 `Multi::CompactCanceller` 按时间闸门中断。
- **编译单元**：`..\nesting\algos\compact.hpp` 与 `..\nesting\algos\multinesting_optimizer.cpp`（`0x1B64E0` 4654 B，断言 `nb_slices == uparams.nb_threads`，`__func__ = SeveralNestAllAndDraw`；`0x1AAFE0` 2871 B，`__func__ = MakeOriginalPartsNesting`）。

---

## 6. 收尾（Finalisation）阶段

**核心函数 `0x1B33B0`（9910 B）**【证实】：它同时引用

- `Finalize : Parts renested in holes` @ `0x9BF078`
- `Finalize : Nesting packed bottom left` @ `0x9BF0A0`
- `$$$$$$$$$$$$$ CLUSTERS $$$$$$$$$$$$$$$$$$$$$ ` @ `0x9BF000` 区
- `USE_POSTOP => `、`postop_estimate`、`epos`、`btime`、`Using seed `

同时它引用 `..\nesting\algos\postop.cpp` 区（`0x1CB100`/`0x1C97A0`/`0x1C8390`/`0x1C8D30`/`0x1C9290`/`0x7C5B70`）与 `postop_move.cpp`（`0x644480`/`0x672DA0`/`0x1E1BF0`/`0x643910`/`0x650F70`/`0x6507B0`）。

因此**收尾是 3 个后处理 pass**（**【证实】顺序即字符串出现顺序**）：

1. **`postop` 通用后处理**（`postop.cpp`）：`0x1B33B0` 的分支，含 `USE_POSTOP` 开关、`postop_estimate` 评分。
2. **`Finalize : Parts renested in holes`** — 把零件重新塞进已有 nesting 的**孔洞**。关联：
   - **`RenestInHoles`** = `0x40720`（字符串 `0x9AF598`）
   - `Multi::HoleRenester`（类型名 `0x9B0ACF`，无 vtable → 非虚实现）
   - 几何断言 `main_box.bottom_left().x() + tolerance > GetBox().bottom_left()...` @ `0x9BDB30`（由 `0x170BB0` 引用）、`box.bottom_left().x() > -1e-6 && box.bottom_left().y() > -1e-6` @ `0x9BE2C0`（由 `0x193420` 引用）—— 都带 **`1e-6` 容差**。
3. **`Finalize : Nesting packed bottom left`** — 「**packed bottom left**」收尾：
   - 与 `BottomLeft` 字符串 @ `0x9DB5C7`（由 `0x511080` 引用）
   - 与 `postop_move.cpp` 的「把每个 nested part 沿 -x/-y 方向推到底」的移动例程（`0x1E1BF0` 等）
   - 这是经典 **BL（bottom-left）/ BLF 稳定化**：所有零件在不与其它零件或板边重叠的前提下，尽量向左下移动，使解规范化、便于去重与比较。

`Multi::RectangleNester`（`0x75FB0`）与 `Tiling::BoxMultiTiler`（v2 `0x7E7FC0` 278 B、v3 `0x7E7E90` 293 B）/`SqueezeMultiTiler`（v2 `0x7E91A0` 157 B）是矩形快速路径的另一条收尾线。

---

## 7. 总结：搜索范式

**【证实】**

- **不是遗传算法**：无任何 GA 字符串；`out_29.txt` 明确 `GA/genetic = 0 hits`。
- **不是纯随机重启**：`NestingNester` 里嵌了**自己的 `std::mt19937`**（`0x342E0` 内 `imul …,0x6c078965` + `[+0x9f8]=0x270`）→ 只是**带随机扰动的确定性局部搜索**。
- **是「多策略并发 + 迭代改进 + 束/树搜索 + 后处理压缩」的混合**：
  1. `MultiEngine::Run` 从 `Problem` 读 `seed`/`nb_max_threads`/策略表，构造 `AlgoParameters`（`0x4EC00`）和 `Supervisor`（`0x2F860`/`0x2F2C0`）。
  2. `Supervisor::Run`（`0x827F0`）按 `StrategyDescriber` 逐条实例化 Nester（`0x342E0` 等）并**每策略一线程**（`NSt6thread...SupervisorE`）。
  3. `AdvancedStrategist::operator()`（`0x2DF60`）选 4 条路（mode 2/3/4/默认），每条路经 `0x2CCF0` **级联展开成 1–4 个预算递减的变体**（`n → 2 → (n+1)/2 → n-1`）。
  4. `Multi::NestingNester::Run`（`0x378E0`）是主打包器，配合 `Tiling::*` 模块与 `tree_db`（`0x1C12D0 FindNode`）做**束/树搜索**（`0x22CCA0` 打印 `Preparing tree for beam`）。
  5. 中间解经 `Observer::slot4 NewIntermediateSolutionFound`（`0x755A80` / `0x75CDA0`）上报并在 `BestObserver` 中择优；`CompositeEngine` 用 `CompositeObserver`（`0x8D4500`）聚合多个子引擎。
  6. `SupervisorCanceller::ProbeCancel`（`0x30030`）以 `elapsed / Problem[+0x408] > 1.0` 为唯一总闸广播取消；`CompactCanceller`（`0x7D2610`）单独管压缩阶段；`RCompactCanceller`（`0x7D2CB0`）不可取消。
  7. 最后 `0x1B33B0` 跑 postop → renest-in-holes → packed-bottom-left 三个收尾 pass。

**【未确认 / 后续最小切入口】**

| 项 | 说明 |
|---|---|
| `MakeMaxTimeEngine` / `MakeSkipSmallTimeEngine` 的 RVA | 只有 `AuxEngine` 的 RTTI（`0x9AE440`/`0x9AE4A0`）；方法是找返回 `shared_ptr<Engine>` 且 `new` 出 `0x??` 大小 `AuxEngine` 的函数 |
| **beam width 常量** | 未找到硬编码立即数。切入口：`0x1C1650`（12 B，返回 int）的实现，以及 `0x22CCA0` 中 `ebp` 的来源 |
| `Multi::CompositeNester` 的 6 个槽 RVA | `0xA3B790`（rodata RTTI 有，`vtables.json` 缺）→ 直接读 `0xA3B790+0x10` 起 6 个 qword |
| `Multi::Node` 的扩展/split 例程 | 只有评分槽（`0x974F0`/`0x97510`）；split 主体未定位 |
| `Multi::BeamNesting` / `Multi::HoleRenester` 实现 RVA | 无 vtable，只能靠 `RenestInHoles`（`0x40720`）与 `0x1B33B0` 的下游 callee 反推 |
| `SetLocalMaximumThreads`（`0xD3B0`）写入的确切字段 & `nb_max_threads` 默认值 | 未追 |
| `EquivalentEngine`（`0x75BCC0`）的「等价问题」映射细节 | 未读 |

### 7.1 交付前补充确认（补测）

- **`Multi::CompositeNester` 的实际 vtable 起始 = `0xA3B780`**（slots 表在 `0xA3B790` → `[0xB4440, 0x998FB0, 0xB46F0, 0x998FB0, —, —]`，即大多槽沿用 `Multi::Nester` 基类的空实现 `0x998FB0`(=1 字节 `ret`) 与 `0xB4440`/`0xB46F0`；`0xA3B790` 处是它内层的数据/子对象边界）。→ **`CompositeNester` 本身几乎没有覆写**，它是**组合壳**，真正的多子 nester 遍历在基类/`Pack::BestNester`（`0x15E410`）那一层。**【证实，修正上表】**
- **`Multi::Nester`（基类）vtable 起始 = `0xA3BAF0`**，slots = `[0xB4430, 0x998FB0, 0x998FB0, 0x998FB0]`（前两组是 dtor 对，后两组为空 `ret`）。所有具体 nester 都覆写这几个空实现。
- **`Multi::TerminalNode` vtable 起始 = `0xA3B560`**，slots = `[0x6938E0, 0x693870, 0x974F0, 0x97500]`；**`Multi::SplitNode` 起始 = `0xA3BB60`**，slots = `[0x6AC2E0, 0x6AC250, 0x97510, 0x97520]`。
  → 4 槽布局 = `[dtor, deleting-dtor, <double eval()>, <其他>]`；`TerminalNode::eval() = [this+0x48]`、`SplitNode::eval() = [this+0x50]`（均为 double）。**【证实】**
- 修正：§4 里写的 `Node`「4 槽/6 槽」计数是 `vtables.json` 的 slot 数组长度（有些类多一个 secondary vtable），**类的实际主 vtable 槽数以上面补测为准**。


---

## 附：**完整选项键表**（rodata `0x9AF8F0`–`0x9AFF80`）**[已证实]**

引擎的全部用户旋钮都以**字符串键**的形式集中存放在这段 rodata 里。逐键与它的
**唯一 `lea` 引用点**（即选项注册/解析区 `0x4ED00`–`0x4F500` 内的读取位置）如下 ——
用与 vtable 相同的方法取得：全代码段线性反汇编，搜 `lea reg,[rip+X]`，X 取该键的地址。

| 键（RVA） | 读取点 | 键（RVA） | 读取点 |
|---|---|---|---|
| `nb_strips_default` `0x9AFA8F` | — | `nb_strips_first` `0x9AFAA2` | — |
| `nb_strips_filling_advanced` `0x9AFAB2` | — | `enable_database` `0x9AFACD` | — |
| `database_relax_every` `0x9AFADD` | — | `enable_beautifier` `0x9AFAF2` | — |
| `nb_iterations_before_tiling` `0x9AFB04` | — | `nb_iterations_before_tiling_evaluated` `0x9AFB20` | — |
| `adaptative_price_max_random` `0x9AFB46` | — | `enable_beam` `0x9AFB62` | `0x4EE5A` |
| `beam_frequency_ratio` `0x9AFB6E` | `0x4EE8B` | `beam_flip_frequency_ratio` `0x9AFB83` | `0x4EEAB` |
| **`beam_width` `0x9AFB9D`** | **`0x4EECB`** | `beam_buckets_per_part` `0x9AFBA8` | `0x4EEEE` |
| `enable_filter` `0x9AFBBE` | — | `seed` `0x9AFBCC` | — |
| `enable_tiling` `0x9AFBD1` | — | `nesting_offset_ratio` `0x9AFBDF` | — |
| `enable_flip` `0x9AFBF4` | — | `trace_nesting` `0x9AFC00` | — |
| `trace_solution` `0x9AFC0E` | — | `trace_best_solution` `0x9AFC1D` | — |
| `boost_price_max_random` `0x9AFC31` | — | `combined_price_frequency` `0x9AFC48` | — |
| `linear_price_frequency` `0x9AFC61` | — | `boost_price_frequency` `0x9AFC78` | — |
| `random_price_frequency` `0x9AFC8E` | — | `enable_multi_sheet` `0x9AFCA5` | — |
| `enable_multi_thread` `0x9AFCB8` | — | `nb_max_threads` `0x9AFCCC` | — |
| `verbose` `0x9AFCDB` | — | `nb_iterations_first` `0x9AFCE3` | — |
| `nb_iterations_before_enlarge` `0x9AFCF7` | — | `nb_iterations_before_enlarge_tiling` `0x9AFD18` | — |
| `linear_fill_frequency` `0x9AFD3C` | — | `enable_last_compaction` `0x9AFD52` | — |
| `enable_database_float_filler` `0x9AFD69` | — | `enable_best_float_filler` `0x9AFD86` | — |
| `nb_max_nested_parts_float_filler` `0x9AFDA0` | — | `nb_iterations_before_float_filler` `0x9AFDC8` | — |
| `float_filler_reduction_ratio` `0x9AFDEA` | — | **`beam_advanced_width` `0x9AFE07`** | **`0x4F342`** |
| **`beam_expert_width` `0x9AFE1B`** | **`0x4F365`** | `beam_distinct_angle` `0x9AFE2D` | `0x4F388` |
| `nb_iterations_before_advanced_nesting` `0x9AFE48` | — | `nb_iterations_before_small_rotation_nesting` `0x9AFE70` | — |
| `nb_iterations_before_beam_advanced` `0x9AFEA0` | `0x4F3EE` | `nb_iterations_before_beam_expert` `0x9AFEC8` | `0x4F411` |
| `enable_beautifier_optimizer` `0x9AFEE9` | — | `enable_nesting_boost` `0x9AFF05` | — |
| `nesting_pow_boost` `0x9AFF1A` | — | `nesting_max_context_size` `0x9AFF2C` | — |
| `enable_beautifier_intermediate` `0x9AFF48` | — | `simple_fill_frequency` `0x9AFF67` | — |
| `enable_last_postop` `0x9AFF7D` | — | | |

> 说明：束相关的 8 个键**各有且仅有一条 `lea`**，全部落在 `0x4EE5A`–`0x4F411`；
> 其余键的读取点落在同一注册区（本表列出的是束族与 `nb_iterations_*` 族，
> 它们与 `AdvancedStrategist` 的 mode/预算级联（§7.2）一一对应：
> `beam_advanced_width`/`beam_expert_width` ↔ mode 2/3，`nb_iterations_before_beam_advanced/expert` ↔ 预算切换点）。

### 束搜索宽度**不是常量**（原 §7.2 的"未确认"由此结案）**[已证实]**

早先的结论写着"beam width 的具体常量未找到（切入口：`0x1C1650` 与 `0x22CCA0` 中 `ebp` 的来源）"。
**原因是它本来就不存在常量**：宽度来自选项表里的三个键
`beam_width`（读取点 `0x4EECB`）、`beam_advanced_width`（`0x4F342`）、`beam_expert_width`（`0x4F365`）。
另有运行期打印点 `'Beam width='` 的 `lea` 在 **`0x655DC6`**，
以及统计键 `'#beam_nodes'`/`'#beam_calls'`/`'#beam_skipped'`/`'#beam_tries'`/`'beam_tree_size'`/`'beam_tree_mo'`
（`0x9BF13B`–`0x9BF17F`），TU 为 `..\nesting\algos\old_beam.cpp`。

⇒ **该项从"未确认"转为"结案（附原因）"**：束宽是**按名字查参数**得到的，
"找不到魔数"是预期结果，而不是信息缺失。

---

## 附 2：`AdvancedStrategist` 的**模式分派器**（`0x2DF60`）完全解出 **[本轮，已证实]**

`0x2DF60` 只有 481 B / 108 条指令，本轮逐条读完。它是一个**四路模式分派器**，
而且选路依据正是**已恢复的两个配置闸**：

```
2DF66  rax = [rcx + 0x18]                  ; 另一个配置对象
2DF6A  cmp byte [rax + 0x81], 0 ; jne 0x2DFD3      ; ① 非 0 ⇒ cascade(mode = 2)

2DF79  rcx = [rcx + 0x10]                  ; ★ Pb（Set* 参数块）
2DF7D  call 0x4FC260      ; = Pb[0xC8]
2DF84  jne 0x2DFC0        ; ② 非 0 ⇒ 0x2CE00(this, arg)      （mode 2 的专用体）

2DF8A  call 0x4FC2F0      ; = Pb[0x170]  ★ 就是 SetPipeMode 的 pipe 闸（§15/§16.1）
2DF91  jne 0x2E0C4        ; ③ 非 0 ⇒ cascade(mode = 3)

2DF9B  call 0x4FC300      ; = Pb[0x1A0]  ★ 就是 SetCommonCutParameters 的共边闸（§15/§16.1）
2DFA8  jne 0x2E050        ; ④ 非 0 ⇒ cascade(mode = 4)

2DFAE  call 0x2D330       ; ⑤ 都非 0 ⇒ 默认体（3118 B）
```

### 交给 cascade 的参数块（0x28 字节，`r8` 传入）**[已证实]**

`0x2E050`（mode 4）与 `0x2E0C4`（mode 3）与 `0x2DFD3`（mode 2）都构造同一形态的块，
只有第一个 dword 不同：

| 偏移 | 类型 | mode=2 时 | mode=3 | mode=4 | 说明 |
|---:|---|---:|---:|---:|---|
| `+0x00` | int | 2 | 3 | 4 | **模式号** |
| `+0x04..+0x09` | u8×6 | 0 | 0 | 0 | |
| `+0x0A` | u8 | **1** | **1** | **1** | 唯一的非零布尔 |
| `+0x0B` | u8 | 0 | 0 | 0 | |
| `+0x0C` | int | 0 | 0 | 0 | |
| `+0x10` | qword | 0 | 0 | 0 | |
| `+0x18` | int | 0 | 0 | 0 | |
| `+0x1C` | int | 0 | 0 | 0 | |
| `+0x20` | double | **1.0** | **1.0** | **1.0** | rodata `0x9AEC90` = 1.0 |

三个分支都先调用 `0x2C2B0`(527 B) 做预备，再把该块交给 **`0x2CCF0`(264 B) = 预算级联**
（`StrategyDescriber::cascade()` 的来源）后返回。

### 同一 `Pb` 上的**全部**短访问器（`0x4FC260`–`0x4FC310`）**[已证实]**

这些 10–15 字节的函数是读 `Pb`（`*this[0x10]`）字段的规范入口，与 §15/§16 的配置结论一致：

| 函数 | 读 | 含义 |
|---|---|---|
| `0x4FC260` | `Pb[0xC8]` | 模式判据 ② |
| `0x4FC270` | `(double)Pb[0xD0]` | 一个权重/比例 |
| `0x4FC280` | `Pb[0xCA]` | |
| `0x4FC290` / `0x4FC2A0` | `Pb[0xE0]` / `Pb[0xE1]` | |
| `0x4FC2B0` | `Pb + 0xE0`（取地址） | |
| `0x4FC2C0` | `Pb + 0xC8`（取地址） | |
| `0x4FC2D0` | `Pb[0xE8]` | = `computeComplexityCap` 的源头（§7.2） |
| `0x4FC2E0` | `Pb[0x120] > 1` | |
| `0x4FC2F0` | `Pb[0x170]` | **pipe 闸**（模式判据 ③） |
| `0x4FC300` | `Pb[0x1A0]` | **共边闸**（模式判据 ④） |
| `0x4FC310` | `Pb + 0x1C8` → `jmp 0x54D100` | 共边参数块尾部转发 |

### 状态更新

* **模式分派器与参数块布局：✅ 结案。**
* `0x2CE00`(1055 B, mode 2 专用体) 与 `0x2D330`(3118 B, 默认体)：**仍未逐条转写** ——
  登记项 `engine.advanced_strategist` 保持 `NotReversed`，但注记已更新为"选路已定、体未译"。

---

## 附 3：级联的**孪生体**与 `0x2D330` 的**默认调度表** **[本轮，已证实]**

### 附 3.1 `0x2CCF0` 与 `0x2D220` 是**逐指令相同**的两个 264 B 例程

两者只差 0x130 的地址偏移，寄存器分配与指令序列**完全一致**：

```
2CCF0 / 2D220   push r12,rbp,rdi,rsi,rbx ; sub rsp,0x50
                rbx = r8 (描述符) ; rdi = rcx (this) ; rbp = rdx (arg)
                call 0x2C4D0                      ; ★ StrategyAdder::Add (2072 B)
                esi = dword [rbx + 0xC]           ; ★ n = 描述符 +0x0C
                if (n <= 2) return                ; 2CD0B cmp esi,2 / jle
                Add(mode = [rbx+0], n = 2)        ; 块拷贝到 rsp+0x20，+0x2C := 2
                if (n > 4) Add(mode, n = (n+1)/2) ; 2CD5B cmp esi,4
                Add(mode, n = n - 1)              ; n == 4 时直接落到这一步
```

要点：
* **级联公式确认**：`n -> 2 -> (n+1)/2 -> n-1`，且 `n <= 2` 时**只做一次 Add**（不进循环）。
* `esi` 是 callee-saved，所以 `2CD5B` 的 `cmp esi,4` 用的确实是描述符里的 `n`（不是 Add 的返回值）。
* 描述符是按值拷贝到栈上 (`rsp+0x20`) 后传入的，**只有 `+0x0C` 被改写**，其余字段原样复制。
* ⇒ **`0x2D220` 就是 `0x2CCF0`**（同一模板的两处实例化）。工程里的 `StrategyDescriber::cascade()`
  同时对应这两个地址。

### 附 3.2 40 字节描述符的**字段语义**（按用途解出）**[已证实]**

`0x2D330` 在栈上构造该块（基址 `rsp+0x80`）并交给 `0x2D220`；`0x2DF60` 构造同一形态的块
（基址 `rsp+0x20`）。两者合起来给出每个字段的含义：

| 偏移 | 类型 | 语义 | 证据 |
|---:|---|---|---|
| `+0x00` | int | **mode**（1 / 2 / 3 / 4） | `0x2D330` 全部 8 处写 1；`0x2DF60` 写 2/3/4 |
| `+0x04..+0x09` | bool[6] | **逐步使能标志**（不是填充） | 每一步设置**不同子集**，见附 3.3 |
| `+0x0C` | int | **n（调度宽度）** | `0x2CCF0`/`0x2D220` 读它做级联；`0x2D330` 多数步骤写 `r12d` |
| `+0x10` | double | 默认调度里恒为 **0.0** | `movsd [rsp+0x90], xmm6`（`pxor xmm6,xmm6`） |
| `+0x18` | int | 从选项对象拷贝 | 取 `[rax+0x110]` / `[rax+0xE8]` / `[r13+0xEC]` |
| `+0x1C` | int | 计算出的计数（两步用到） | `cvtsi2sd` → `divsd` → `call 0x62F940` → `cvttsd2si` |
| `+0x20` | double | 默认调度与分派器都写 **1.0** | rodata `0x9AEC90` |

### 附 3.3 `0x2D330` 的默认调度：**8 处 `0x2D220` 调用，全部 mode=1**

靠 6 个使能标志的不同组合（`+0x04..+0x0A`，下表按该顺序写 `1/0`）与选项对象的各闸区分：

| # | 调用点 | 使能标志 (`04,05,06,07,08,09,0A`) | n | `+0x18` | 前置闸 |
|---:|---|---|---:|---|---|
| 1 | `0x2D416` | `0,0,1,0,0,0,0` | 0 | 0 | `[+0x1E8] != 0` ⇒ 转到 `0x2DA20` |
| 2 | `0x2D521` | `0,bpl,0,0,0,0,0` | `r12d` | `[+0x110]` | `[+0x59]` ⇒ `0x2DAC1`；`[+0x80]` ⇒ `0x2DC60`；`bpl = [+0x10C]` |
| 3 | `0x2D5B2` | `0,bpl,1,0,1,0,0` | `r12d` | `[+0xE8]` | `[+0x58]` ⇒ `0x2DA32` |
| 4 | `0x2D639` | `0,bpl,0,0,1,0,0` | `r12d` | `[+0xE8]` | — |
| 5 | `0x2D71E` | `0,bpl,0,0,1,0,1` | `r12d` | `[r13+0xEC]` | `[r13+0x138] != 0`；计数 = `int(0x62F940(ratio) )`，`ratio = x / [r13+0x140]` |
| 6 | `0x2D7D7` | `1,bpl,0,0,1,0,1` | 0 | `[r12+0xEC]` | 计数 = `int(0x62F940(x / [r12+0x148]))` |
| 7 | `0x2D885` | `0,0,0,1,0,0,0` | 0 | 0 | `0x4FC310`（= `Pb+0x1C8`，共边参数块）为 0 |

其中 `bpl` 来自函数入口：`0xB58A0(this)` 的返回值，或（`[+0x1E8]` 路径下）`[+0x10C]`。
`r12` 由 `0x5221E0(Pb)` 与 `0x523050(Pb)` 产生（后者给出指针，`0x4F8390` 其取值与 `xmm8` 比较，
`ja 0x2D7E1` 控制另一条分支）。

**仍未译**：`0x2C4D0`（`StrategyAdder::Add`，2072 B —— mode/标志到具体 Nester 的映射表）、
以及各闸体 `0x2DA00`/`0x2DA20`/`0x2DA32`/`0x2DAC1`/`0x2DC60`/`0x2D7E1`/`0x2D650`。
登记项 `engine.advanced_strategist` 因此保持 `NotReversed`，但注记升级为
"**分派器 + 描述符布局 + 默认调度表已解出，未译的是 Add 的映射表与各闸体**"。

---

## 附 4：`Multi::StrategyAdder::Add`（`0x2C4D0`，2072 B）**完全解出** **[本轮，已证实]**

这是引擎调度层最后一块空白：`0x2DF60` 的四个 mode、`0x2D330` 的八步调度，
最终都要经它变成具体策略对象。**两条独立证据同时给出映射**，互为交叉验证：
① 对描述符 `mode` 的 `cmp/je` 分派链；② 每个分支 `operator new` 的**尺寸**与随后**构造的类**
（类名由 `re/vtables.json` 的虚表地址点确定）。

### 附 4.1 mode → 类（`descriptor[+0x00]`）**[已证实]**

| mode | 构造的类 | `operator new` 尺寸 | 证据 |
|---:|---|---:|---|
| **0** | `Multi::TilingNester` | 0x20 = 32 B | `2C525 mov ecx,0x20` → `2C55C call 0x45AF0` |
| **1** | `Multi::NestingNester` | **0xA40 = 2624 B** | `2CB1C mov ecx,0xA40` → `2CB33 call 0x342E0` |
| **2** | `Multi::RectangleNester` | 0x20 | `2CB50` → `2CB64 call 0x77440` |
| **3** | `Multi::RowNester`（`r8d = 0`） | 0x20 | `2CB70` → `2CB87 call 0x8F210` |
| **4** | `Multi::RowNester`（**`r8d = 1` = pipe**） | 0x20 | `2CB91` → `2CBAB call 0x8F210` |
| **≥5** | —（**断言**） | — | `2C51A jne 0x2C7A0` → 断言串 `descriptor.algorithm == ...` |

> **口径更正**：本工程早期版本的 `makeStrategy()` 里 modes 5..12（Compact/Filter/NoFill/
> Limited/Tiling/MultiTorch/Database/Flip）**是自创的**，二进制没有这些 mode。
> 现在它们改为由**标志**驱动（见附 4.2），`makeStrategy(≥5)` 返回 `nullptr` 并注明"原库在此断言"。
> 是 `test_nester` 里那 8 条旧断言把这个自创暴露出来的（改后会空指针崩溃）。

### 附 4.2 标志 → 追加的策略（同一次 Add 内按此顺序）**[已证实]**

| 判据 | 追加的类 | `new` 尺寸 | 证据 |
|---|---|---:|---|
| `[+0x05] != 0` | `Multi::CompactNester` | 0x9F8 = 2552 B | `2CA30` → `2CA4C call 0xB0270` |
| 且 `options[+0x168] != 0` | `Multi::FilterNester` | 0x9E8 = 2536 B | `2CA6A` → `2CA8E call 0xB3A70` |
| `[+0x04] != 0` | `Multi::FlipNester` | 0x28 = 40 B | `2C584 jne 0x2C953` → `2C96C call 0x4B570` |
| `[+0x0C] > 0` | `Multi::MultiTorchNester` | 0x28 | `2C58A/2C58F` → `2C5AA call 0x780E0`，**`r9d = [+0x0C]`** |
| `[+0x18] != 0` | `Multi::LimitedNester` | 0x48 = 72 B | `2C5C8` → `2C9E0`：先 `call 0x4AA50` 再 `2CA0C call 0x4AAD0` |
| `[+0x1C] != 0` | `Multi::LimitedNester` | 0x48 | `2C5D3` → `2C990`：先 `call 0x4AA90` 再 `2C9BC call 0x4AAD0` |
| `[+0x20] == 1.0` 且 `Pb[+0x120] > 1` | `Multi::NoFillNester` | 0x60 = 96 B | `2C5E3 ucomisd` → `2C5FB call 0x4FC2E0` → `2C61D call 0x7EE50` |

⇒ 顺带确定了一件事：**描述符 `+0x0C` 不只是"调度宽度"，它就是 `MultiTorchNester` 的火焰/线程数**
（以 `r9d` 传入）。这与 `0x2DF60` 分派器里把 `+0xC` 留给级联读 `n` 是同一字段的两种用法。

### 附 4.3 **新发现的族**：板材选择器（`SheetSelector`）**[已证实]**

Add 的尾部按 `options[+0x2C4]`、`options[+0x2C0]` 与 `0x4FC250(Pb)` 的结果构造其中之一：

| 类 | 构造点 | 说明 |
|---|---|---|
| `Multi::RandomSheetSelector` | `0xB0040`，Add 在 `2C673` 调用 | 随机选板 |
| `Multi::NoMixSheetSelector` | `0xAFD60`，Add 在 `2C686` 调用 | 不混板 |
| `Multi::LargestSheetSelector` | `0xB0000`（49 B 的构造器） | 选最大板 |

此前的报告**完全没有**这一族（`SheetSelector` 在 vtable 名单里出现过，但没被归到任何算法路径）。

### 附 4.4 TU 与断言串

`Add` 内联拼出的串（`movabs`）给出源文件与断言内容：
`'AddStrat'` + `'egyR'`（`"AddStrategyR..."`）、`'..\multi'` + `'\multi.c'`（**`..\multi\multi.cpp`**）、
以及 `'descript'`/`'ion.algo'`/`'rithm =='`/`' Algorit'`/`'hm::Tili'`
（一条把 `descriptor.algorithm` 与某个 `...::Tili...` 相比的断言）。

### 附 4.5 落到工程

* `lcns::makeStrategy(mode)` 改为**实证表**（0..4，≥5 → `nullptr`）；
* `lcns::makeDefaultStrategies()` 改为按附 4.2 的**标志结果**构造列表（并注明哪几条来自标志、
  预算记账仍是近似）；
* `engine.hpp` 新增 10 个**分配尺寸常量**（`kTilingNesterBytes` … `kFilterNesterBytes`）与
  `kStrategyModeCount = 5`，并在注释里记下选择器三兄弟；
* `test_recovered.cpp` 断言这些常量 + `makeStrategy(0..4)` 的 `dynamic_cast` 类型 + `≥5` 为 `nullptr`；
  `test_nester.cpp` 的 8 条旧断言改为实证表；
* 登记表新增 **`engine.strategy_adder`（已恢复）**，并把 `engine.advanced_strategist` 的
  "未译"清单缩小为 **`0x2CE00`(1055 B) + 7 个闸体**。

---

## 附 5：`0x2CE00`（mode-2 体）与 `0x2D330` 的其余路线 —— **新功能概念：tooling / shear** **[本轮，已证实]**

### 附 5.1 `0x2CE00`（1055 B / 208 条指令）：模式 2 = **shear / tooling 路线**

结构（无任何 rodata 字符串引用，字符串是**内联拼**出来的）：

```
2CE23  call 0x2C2B0                 ; prepare（与 0x2DF60 各 mode 分支同一预备调用）
2CE28  rax = [rbx+0x10]             ; Pb
2CE2C  call 0x5223A0                ; 返回一个 bool（edi）
2CE37  call 0x4FC2C0                ; ★ 取 &Pb[0xC8]（就是选 mode 2 的那个字节的地址）
2CE3C  cmp byte [rax+1], 0          ; ★ 再看 Pb[0xC9]（紧跟其后的第二个字节）
2CE40  jne 0x2D0E0                  ;   非 0 -> 另一条支路
2CE46  test dil, dil ; je 0x2D048   ;   bool == 0 -> 另一条支路
2CE54..2CEDF  内联拼一条 74 (0x4A) 字节的断言串
```

**内联拼出的断言串**（`movabs` 逐 8 字节写入，按存储顺序）**[已证实]**：

| 片段 | RVA |
|---|---|
| `'!is_tool'` | `0x2CE9B` |
| `'ing && "'` | `0x2CEA8` |
| `'Normal s'` | `0x2CEB6` |
| `'hear is '` | `0x2CEC4` |
| `'incompat'` | `0x2CED2` |
| `'ible wit'` | `0x2CEE0` |
| `'g contac'` | `0x2CEEE` |

拼起来即 **`!is_tooling && "Normal shear is incompatible with ... contact ..."`**
（前段与 `Normal shear is incompatible with` 是确定的；尾部 `g contac…` 之后还有片段，说明整串更长，
此处只声明已读出的部分）。同一函数里另有 `'AddShear'`(`0x2CF69`) 与源路径 `'..\\multi'`(`0x2CFD5`)。

⇒ **这是两个此前完全没有记录的功能概念**：
* **`tooling`**（工装/接触判据，`is_tooling` 是布尔谓词）——而 `Pb[0xC9]` 是它的开关字节；
* **`shear`**（剪切/斜切）——并有名为 **`AddShear…`** 的函数；"Normal shear" 与 tooling 互斥（由断言保证）。

二者与工程已知的 `shear*` 选项键、`Pb+0xC8` 区域的开关是同一套东西；
**模式 2 就是这条路线**（`0x2DF60` 用 `Pb[0xC8]` 选它）。

### 附 5.2 `0x2D330` 的七个"闸体"：四个是**新步骤**，一个是**函数尾声**

| 地址 | 实际是什么 | 证据 |
|---|---|---|
| `0x2DA00` | `cpuid` 探针后读 `options[+0x1E8]`，非 0 则 `prepare(0x2C2B0)` 再回主流程 | `2DA00 xor eax,eax / cpuid / 2DA06 jne 0x2DCF0`；`2DA10 movzx ebp,[rax+0x1E8]`；`2DA28 call 0x2C2B0`；`2DA2D jmp 0x2D383` |
| `0x2DA20` | 同上的 `[+0x1E8]` 支路：`prepare` 后回主流程 | `2DA28 call 0x2C2B0` |
| `0x2DA32` | **新步骤**：mode 1 + **`+0x04 = 1`（Flip 标志）**，`+0x18 = options[+0x110]` | `2DA41 [rsp+0x80]=1`；`2DAA3 [rsp+0x84]=1`；`2DA5C [rsp+0x98]=[rax+0x110]`；`2DAB3 call 0x2D220` |
| `0x2DAC1` | **新步骤**：mode **0**，先 `0x2BE50` 造描述符对象，把 `options[+0x60]` 写进 `[obj+0x18]`，再 `cascade` | `2DAC5 ebp=[rax+0x60]`；`2DB56 call 0x2BE50`；`2DB64 [rax+0x18]=ebp`；`2DB67 call 0x2CCF0` |
| `0x2DC60` | **新步骤**：mode **2**（即 shear/tooling 路线） | `2DC69 [rsp+0x80]=2` |
| `0x2D7E1` | **新步骤**：`0xAD5E0(x) == 1` 且 `Pb+0x1C8`（共边参数块）为 0 时，mode 1 | `2D7E4 call 0xAD5E0`；`2D7E9 cmp eax,1`；`2D7F6 call 0x4FC310`；`2D80C [rsp+0x80]=1` |
| **`0x2D650`** | **不是闸体，是函数尾声** | `2D650 movaps xmm6,[rsp+0xb0] … 2D67A ret` |

紧随 `0x2D680` 又是一段 mode 1 的步骤构造（`+0x8C = r12d`、`+0x18 = [r13+0x150]`）。

**结论**：`0x2D330` 的默认调度 = 我此前列出的 **8 个 mode-1 步**（附 3.3）
**加上**这里的四个附加路线（mode 1 + Flip 标志、mode 0、mode 2、mode 1 带 `[r13+0x150]`），
各自的开关来自选项对象的不同字节（`+0x1E8`、`+0x58/0x59`、`+0x80`、`+0x138`、`+0x110`、`+0x150`、`+0x60`、`+0x168`、`+0x2C0/0x2C4`）。

### 附 5.3 落到工程与登记表

* `engine.hpp` 新增：`kPbToolingByte = 0xC9`（tooling 开关，紧跟选 mode2 的 `+0xC8`）、
  `kPbShearSelectorByte = 0xC8`、`kPbMode2Route = 2`；并在注释里写明 **mode 2 = shear/tooling 路线**、
  "Normal shear 与 tooling 互斥"、
  以及 `0x2D650` 是尾声而非闸体这一事实（避免后人再把它当步骤去读）。
* 登记表新增 **`engine.mode2_shear_route`**（`Structural`：路线与开关已定、断言串已读出，**函数体未转写**）；
  `engine.advanced_strategist` 的剩余项收敛为"`0x2CE00` 的三条支路体 + `0x2DA00` 的 `cpuid` 探针分支"。

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

### 附 6.4 第二遍：Multi::FilterNester::Run（`0xB3AE0`，2,254 B）**[已证实 + 未解]**

* 函数：`0xb3ae0`，2254 字节 / **496 条指令**
* 被调用者（21 个）：`0xb4d80`(9B，10 调用者)、`0x609e20`(221B，9 调用者)、`0x97a090`(1599B，17 调用者)、`0x6c0e0`(5B，19 调用者)、`0x998500`(109B，2318 调用者)、`0xb44d0`(531B，23 调用者)、`0xb4d20`(69B，12 调用者)、`0x9984b0`(5B，5721 调用者)、`0x51d2f0`(5B，102 调用者)、`0xb4d70`(5B，9 调用者)、`0x434d0`(407B，10 调用者)、`0x51d320`(416B，17 调用者)、`0x90ecb0`(650B，185 调用者)、`0x51faf0`(743B，16 调用者)、`0x63f2f0`(0B)、`0x4d3ee0`(12B，11 调用者)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x979e70`(51B，676 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x62f280`(171B，5209 调用者)
* 字符串：`Filter `
* 浮点常量：无
* 立即数：`1`×1, `2`×8, `3`×1, `5`×1, `7`×1, `8`×2, `16`×14, `26`×1, `59`×1, `110`×1, `116`×1, `312`×2
* 字段偏移（41 个）：`+0x1`、`+0x8`、`+0x10`、`+0x12`、`+0x14`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc3`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe5`、`+0xe8`、`+0xf0`、`+0x100`、`+0x110`、`+0x120`、`+0x170`、`+0x178`、`+0x198`、`+0x1a0`、`+0x1a8`、`+0x1b0`

**尚未解**：过滤器保留/淘汰的判据（下界比较用哪个字段）、它调用的

### 附 6.5 超热共享辅助的定性（goal round 13）**[已证实]**

两个 `Run` 体的调用面收敛到少数超热函数，先攻它们杠杆更高。逐个读出的结果是：**大部分是基础设施**。

| 地址 | 字节 | 调用者 | 定性 | 依据 |
|---|---:|---:|---|---|
| `0x9984B0` | 5 | **5,721** | `operator delete` thunk | 只有 1 条指令 |
| `0x998500` | 109 | **2,318** | `operator new` | 尺寸经 `ecx` 传入（见 `0x2C525`/`0x2CB1C`） |
| `0x910BA0` | 109 | 1,002 | `std::string::_M_create` | 自身字符串即该名字；工具链 |
| `0x90ECB0` | 650 | 185 | 走 `basic_string::_M_replace` 的字符串路径 | 字符串 `basic_string::_M_replace`；工具链 |
| `0x979E70` | 51 | 676 | 删除器包装 | 转调两个各 476 调用者的分配器辅助 |
| **`0x60A620`** | 2,620 | **680** | ★ **共享错误/断言上报器** | 自身字符串：`*** INTERNAL ERROR: please contact support ***`、`: error `、`(assertion failed in ` |
| **`0xB44D0`** | 531 | 23 | ★ **校验辅助**（借上报器组错误信息） | 调用 `0x910BA0`（建串）+ `0x60A620`（上报）+ `0x62F280` |
| `0x62F280` | 171 | **5,209** | **未定性**的基础设施 | 无字符串；1 个 0 字节 thunk 被调用者；立即数 `1672`；字段 `+0x18…+0x1E0` |
| `0x7C1CF0` | 200 | 117 | 析构型辅助 | 调 `operator delete` 与 `0x92ECB0` |

**可操作的结论**：`Run` 体里大量「调用」是**报错、分配、建字符串**，不是算法步骤。
**`0x60A620` 的 680 个调用点就是原库的前置条件校验点**（它格式化 `(assertion failed in …`，
调用点会传文件/行信息）。⇒ 以后凡见 `call 0x60a620` 或 `call 0xb44d0`，即可判定为**前置条件校验/参数拒绝**，
不必逐条跟进 —— 这直接降低所有 `Run` 体的解读成本。

`0x62F280`（5,209 调用者）仍未定性：**本档不给它编名字**。

### 附 6.6 第三遍：`Multi::FlipNester::Run`（`0x4B870`，3,496 B）**[已证实 + 未解]**

* 函数：`0x4b870`，3496 字节 / **713 条指令**
* 被调用者（21 个）：`0x51cc90`(312B，17 调用者)、`0x4f8370`(6B，74 调用者)、`0x4f8380`(6B，85 调用者)、`0x910ba0`(109B，1002 调用者)、`0x4fb5f0`(408B)、`0x9984b0`(5B，5721 调用者)、`0xb44d0`(531B，23 调用者)、`0x64330`(28B，21 调用者)、`0xb4d20`(69B，12 调用者)、`0x4b680`(493B)、`0x92ecb0`(791B，180 调用者)、`0x51d320`(416B，17 调用者)、`0x90ecb0`(650B，185 调用者)、`0x51faf0`(743B，16 调用者)、`0xb4d90`(9B，19 调用者)、`0x51e7e0`(1294B，47 调用者)、`0x60a620`(2620B，680 调用者)、`0x910af0`(168B，345 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x7c0c90`(608B，6 调用者)、`0x62f280`(171B，5209 调用者)
* 字符串：`Flip `
* 浮点常量：无
* 立即数：`1`×1, `3`×1, `5`×2, `8`×2, `16`×17, `17`×1, `24`×6, `32`×1, `48`×4, `86`×1, `100`×1, `110`×1, `116`×1, `120`×3, `1144`×2
* 字段偏移（108 个）：`+0x8`、`+0x10`、`+0x12`、`+0x14`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x148`、`+0x150`、`+0x160`、`+0x168`、`+0x178`、`+0x180`、`+0x1a8`、`+0x1b0`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1e3`、`+0x1f8`、`+0x200`、`+0x210`、`+0x248`、`+0x288`、`+0x2d0`、`+0x2f0`、`+0x310`、`+0x318`、`+0x320`、`+0x325`、`+0x328`、`+0x330`、`+0x338`、`+0x340`、`+0x348`、`+0x350`、`+0x358`、`+0x360`、`+0x368`、`+0x388`、`+0x390`、`+0x398`、`+0x3a0`、`+0x3a8`、`+0x3ac`、`+0x3b0`、`+0x3b1`、`+0x3b4`、`+0x3b8`、`+0x3c0`、`+0x3c8`、`+0x3d0`、`+0x3d8`、`+0x3e0`、`+0x3e8`、`+0x3f0`、`+0x3f8`、`+0x400`、`+0x408`、`+0x410`、`+0x418`、`+0x420`、`+0x428`、`+0x430`、`+0x438`、`+0x440`、`+0x450`、`+0x460`、`+0x4c8`、`+0x4e0`、`+0x4e8`、`+0x4f0`

**尚未解**：翻转判据（按哪个指标决定采用镜像解）、镜像后的坐标变换在哪一步做、`0xB4440`（31 B）的角色。`strategy.flip` 仍标 `Substituted`。

### 附 6.7 第四遍：`Multi::DatabaseNester::Run`（`0x5B250`，4,495 B）**[已证实 + 未解]**

* 函数：`0x5b250`，4495 字节 / **897 条指令**
* 被调用者（49 个）：`0x51cc90`(312B，17 调用者)、`0xb44d0`(531B，23 调用者)、`0xb4d70`(5B，9 调用者)、`0x303c0`(94B)、`0xaef10`(12B，12 调用者)、`0x522a40`(64B，7 调用者)、`0xaef80`(622B，14 调用者)、`0xb4d80`(9B，10 调用者)、`0xb44b0`(4B)、`0x316f0`(574B)、`0x51d0c0`(5B，103 调用者)、`0x51d2f0`(5B，102 调用者)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x9984b0`(5B，5721 调用者)、`0x6c0e0`(5B，19 调用者)、`0x64330`(28B，21 调用者)、`0x434d0`(407B，10 调用者)、`0x51d320`(416B，17 调用者)、`0x82a0a0`(188B，11 调用者)、`0x51faf0`(743B，16 调用者)、`0x92ecb0`(791B，180 调用者)、`0xb4d90`(9B，19 调用者)、`0x4fc260`(11B，25 调用者)、`0x4fc2f0`(11B，18 调用者)、`0x4fc300`(11B，16 调用者)、`0x30250`(11B，25 调用者)、`0x30260`(9B，25 调用者)、`0x4fc310`(15B，16 调用者)、`0xaab20`(279B)、`0x5238b0`(193B，19 调用者)、`0x31b50`(396B，7 调用者)、`0x6a820`(80B，6 调用者)、`0x69fe0`(820B，7 调用者)、`0x4db80`(474B，8 调用者)、`0x30a30`(187B)、`0xab9d0`(1257B)、`0x51e7e0`(1294B，47 调用者)、`0x31210`(159B)、`0x910a60`(136B，185 调用者)、`0x97ab50`(75B，352 调用者)、`0xab140`(75B)、`0x998500`(109B，2318 调用者)、`0xad400`(451B)、`0xab190`(86B，6 调用者)、`0x910af0`(168B，345 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x62f280`(171B，5209 调用者)、`0x874220`(75B，22 调用者)
* 字符串：`basic_string::append`
* 浮点常量：**1**（`0x9b08f8`）
* 立即数：`1`×4, `3`×2, `8`×8, `16`×32, `22`×1, `24`×1, `26`×1, `28`×2, `32`×2, `35`×1, `65`×1, `101`×1, `110`×1, `119`×1, `120`×1, `1224`×2, `2660`×1, `10599`×1
* 字段偏移（87 个）：`+0x4`、`+0x8`、`+0x10`、`+0x12`、`+0x14`、`+0x18`、`+0x20`、`+0x22`、`+0x28`、`+0x30`、`+0x38`、`+0x48`、`+0x50`、`+0x58`、`+0x64`、`+0x68`、`+0x7c`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xd0`、`+0xf0`、`+0xf8`、`+0x100`、`+0x110`、`+0x118`、`+0x120`、`+0x130`、`+0x138`、`+0x140`、`+0x150`、`+0x170`、`+0x178`、`+0x180`、`+0x188`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c4`、`+0x1c8`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1ec`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x210`、`+0x218`、`+0x220`、`+0x230`、`+0x248`、`+0x260`、`+0x280`、`+0x2a0`、`+0x2b0`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x2f8`、`+0x308`、`+0x328`、`+0x330`、`+0x338`、`+0x340`、`+0x343`、`+0x348`、`+0x358`、`+0x378`、`+0x380`、`+0x3a8`、`+0x3b0`、`+0x3c0`、`+0x3f8`、`+0x438`、`+0x480`、`+0x4a0`、`+0x530`、`+0x538`

**尚未解**：tree_db/bucket_manager 的存取协议、键的构成、以及它如何与 `0x22CCA0`（束树准备）配合。`strategy.database` 仍标 `Substituted`。

### 附 6.8 第五遍：`Multi::RectangleNester::Run`（`0x75FB0`，5,261 B）**[已证实 + 未解]**

* 函数：`0x75fb0`，5261 字节 / **985 条指令**
* 被调用者（31 个）：`0x5f4310`(35B，45 调用者)、`0x51cdd0`(478B，22 调用者)、`0xb44d0`(531B，23 调用者)、`0xb4d80`(9B，10 调用者)、`0xb4d90`(9B，19 调用者)、`0x4fc260`(11B，25 调用者)、`0x30220`(39B，9 调用者)、`0x30260`(9B，25 调用者)、`0x73280`(11567B)、`0x93da50`(408B，15 调用者)、`0x9984b0`(5B，5721 调用者)、`0x6c8b0`(251B)、`0x6caa0`(533B)、`0x63f2f8`(0B)、`0xaed20`(447B)、`0x70150`(8524B)、`0x92ecb0`(791B，180 调用者)、`0x6c9e0`(177B)、`0x910a60`(136B，185 调用者)、`0x51faf0`(743B，16 调用者)、`0x5f4340`(140B，67 调用者)、`0x90ecb0`(650B，185 调用者)、`0x4f9bc0`(18B，17 调用者)、`0x96970`(2929B)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x910af0`(168B，345 调用者)、`0x62f280`(171B，5209 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x891b40`(52B，240 调用者)、`0x97ab50`(75B，352 调用者)
* 字符串：`basic_string::append`
* 浮点常量：无
* 立即数：`1`×7, `2`×1, `3`×1, `5`×1, `8`×1, `9`×2, `15`×1, `16`×20, `29`×1, `30`×1, `32`×1, `72`×1, `101`×2, `110`×1, `112`×1, `116`×1, `120`×4, `224`×2, `624`×2, `680`×1, `2504`×1, `3160`×2
* 字段偏移（132 个）：`+0x8`、`+0xc`、`+0x10`、`+0x12`、`+0x14`、`+0x18`、`+0x1c`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x44`、`+0x48`、`+0x50`、`+0x58`、`+0x5c`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x81`、`+0x88`、`+0x8c`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xd9`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0xf9`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x153`、`+0x158`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x180`、`+0x188`、`+0x190`、`+0x198`、`+0x1b8`、`+0x1c0`、`+0x1c8`、`+0x1d0`、`+0x1d8`、`+0x1dc`、`+0x1e0`、`+0x1e1`、`+0x1e4`、`+0x1e8`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x208`、`+0x210`、`+0x218`、`+0x220`、`+0x228`、`+0x230`、`+0x238`、`+0x240`、`+0x248`、`+0x250`、`+0x258`、`+0x260`、`+0x268`、`+0x270`、`+0x280`、`+0x288`、`+0x290`、`+0x295`、`+0x298`、`+0x2a0`、`+0x2a8`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2d8`、`+0x2f8`、`+0x300`、`+0x308`、`+0x310`、`+0x318`、`+0x31c`、`+0x320`、`+0x321`、`+0x324`、`+0x328`、`+0x330`、`+0x338`、`+0x340`、`+0x348`、`+0x350`、`+0x358`、`+0x360`、`+0x368`、`+0x370`、`+0x378`、`+0x380`、`+0x388`、`+0x390`、`+0x398`、`+0x3a0`、`+0x3a8`、`+0x3b0`

**尚未解**：矩形快路径的选取规则（何时走矩形而非一般多边形）、`0x77780`(402 B) 与 `0x75FB0` 的分工、以及它与 `problem.part_gap()==0` 断言的关系。`strategy.rectangle` 仍标 `Substituted`。

### 附 6.9 `0x73280`（11,567 B，目前最大的未识别函数）**[已证实 + 未解]**

* 函数：`0x73280`，11567 字节 / **2262 条指令**
* 被调用者（54 个）：`0x4fc5a0`(8B，114 调用者)、`0x523050`(174B，33 调用者)、`0x5223a0`(403B，7 调用者)、`0x4fc260`(11B，25 调用者)、`0x4fc5b0`(319B，85 调用者)、`0x4f73a0`(5B，9 调用者)、`0x72c80`(1524B)、`0x4f7600`(9B，50 调用者)、`0x5ec4e0`(370B，6 调用者)、`0x8befc0`(308B)、`0x5cd800`(610B，113 调用者)、`0x54cbd0`(10B)、`0x4f7740`(41B，10 调用者)、`0x54cbf0`(10B)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x9984b0`(5B，5721 调用者)、`0x4f7770`(41B，17 调用者)、`0x5cd7d0`(44B)、`0x5c8c50`(255B，57 调用者)、`0x5c4c50`(10B，65 调用者)、`0x4f7690`(9B，29 调用者)、`0x5c2e40`(138B，32 调用者)、`0x5cee50`(527B，52 调用者)、`0x5d38c0`(1500B，51 调用者)、`0x998500`(109B，2318 调用者)、`0x8c0ef0`(337B，7 调用者)、`0x4f76d0`(4B，15 调用者)、`0x5ce240`(42B，13 调用者)、`0x93d750`(765B)、`0x93da50`(408B，15 调用者)、`0x8beec0`(256B)、`0x5c4c60`(109B，16 调用者)、`0x5c4dd0`(189B，37 调用者)、`0x99a5f0`(130B)、`0x62f280`(171B，5209 调用者)、`0x9989a0`(125B，837 调用者)、`0x998fe0`(79B，783 调用者)、`0x979e70`(51B，676 调用者)、`0x998bc0`(124B，833 调用者)、`0x99a672`(84B)、`0x8c4ff0`(147B，123 调用者)、`0x4ef250`(165B，10 调用者)、`0x4f8380`(6B，85 调用者)、`0x4f8370`(6B，74 调用者)、`0x159c70`(152B)、`0x4ee1f0`(1637B)、`0x5d2900`(186B，28 调用者)、`0x5ce7f0`(381B，16 调用者)、`0x5ce970`(269B，38 调用者)、`0x5c9210`(264B)、`0x6ccc0`(1565B)、`0x67fe90`(104B，155 调用者)、`0x983ca0`(145B，289 调用者)
* 字符串：`vector::_M_range_check: __n (which is %zu) >= this`
* 浮点常量：**0.99**（`0x9b15e0`）、**0.99**（`0x9b15e0`）
* 立即数：`1`×15, `3`×5, `4`×4, `5`×4, `7`×1, `10`×2, `11`×1, `14`×1, `16`×32, `19`×1, `24`×11, `29`×4, `40`×8, `41`×3, `48`×13, `69`×2, `72`×1, `112`×4, `115`×1, `116`×1, `139`×1, `222`×1, `224`×4, `239`×1, `243`×1, `1768`×2, `10361`×1, `10536`×2
* 字段偏移（184 个）：`+0x1`、`+0x4`、`+0x8`、`+0x10`、`+0x12`、`+0x14`、`+0x16`、`+0x18`、`+0x1c`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x44`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb5`、`+0xb6`、`+0xb7`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xf0`、`+0x100`、`+0x110`、`+0x114`、`+0x118`、`+0x11c`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x160`、`+0x170`、`+0x180`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1f0`、`+0x1f8`、`+0x210`、`+0x218`、`+0x220`、`+0x230`、`+0x238`、`+0x250`、`+0x258`、`+0x270`、`+0x278`、`+0x290`、`+0x298`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2f0`、`+0x2f8`、`+0x300`、`+0x310`、`+0x318`、`+0x320`、`+0x330`、`+0x338`、`+0x340`、`+0x350`、`+0x358`、`+0x360`、`+0x370`、`+0x378`、`+0x380`、`+0x390`、`+0x398`、`+0x3a0`、`+0x3a8`、`+0x3b0`、`+0x3c0`、`+0x3c8`、`+0x3d0`、`+0x3d8`、`+0x3e0`、`+0x3f0`、`+0x3f8`、`+0x400`、`+0x408`、`+0x410`、`+0x420`、`+0x428`、`+0x430`、`+0x438`、`+0x440`、`+0x450`、`+0x460`、`+0x478`、`+0x480`、`+0x488`、`+0x490`、`+0x498`、`+0x4a0`、`+0x4b0`、`+0x4b8`、`+0x4c0`、`+0x4c8`、`+0x4d0`、`+0x4d8`、`+0x4e0`、`+0x4f0`、`+0x4f8`、`+0x500`、`+0x529`、`+0x540`、`+0x548`、`+0x550`、`+0x558`、`+0x55a`、`+0x55b`、`+0x560`、`+0x568`、`+0x570`、`+0x578`、`+0x580`、`+0x588`、`+0x590`、`+0x598`、`+0x5a0`、`+0x5a8`、`+0x5b0`、`+0x5c0`、`+0x5c8`、`+0x5d0`、`+0x5d7`、`+0x5d8`、`+0x5da`、`+0x5de`、`+0x5e0`、`+0x5e8`、`+0x5f0`、`+0x5f8`、`+0x600`、`+0x608`、`+0x610`、`+0x618`、`+0x620`、`+0x628`、`+0x630`、`+0x640`、`+0x650`、`+0x660`、`+0x670`、`+0x680`、`+0x690`、`+0x6a0`、`+0x6b0`、`+0x6c0`、`+0x6d0`、`+0x730`、`+0x738`、`+0x748`

**尚未解**：它到底是矩形排样内核还是通用几何例程（无字符串、无浮点常量，无法从这两项判断）、它与 `0x70150`(8,524 B) 的分工、以及它的入参结构。**本档不给它编名字**。

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
即 **1% 覆盖松弛**。这与我在 `..\nesting\algos\bucket_manager.hpp` 断言里读到的
`eval.m_c <= max_surface * 1.05`（5% 上界）属于**同一类机制**（都用面积乘一个接近 1 的系数做容差）。

**为什么标"推断"而不是"已证实"**：算术形状（成对差分相乘=面积、比较、`jbe` 极性）证据充分，
但**没有符号或字符串直接说明**它是"覆盖松弛"；语义是从算式反推的。
已按此谨慎命名落到 `lcns::kAreaCoverageSlack`，注释里写明证据与推断的边界。

### 附 6.11 `0x70150`（8,524 B，第二个巨物）**[已证实 + 未解]**

* 函数：`0x70150`，8524 字节 / **1659 条指令**
* 被调用者（33 个）：`0x50bd0`(137B，8 调用者)、`0xb4d90`(9B，19 调用者)、`0x6d470`(11478B)、`0x50c60`(5785B，6 调用者)、`0x9984b0`(5B，5721 调用者)、`0x92ecb0`(791B，180 调用者)、`0x50680`(640B，6 调用者)、`0x910af0`(168B，345 调用者)、`0x8e6400`(1770B，29 调用者)、`0x8ea9d0`(335B，25 调用者)、`0x92e360`(2378B，22 调用者)、`0x8e1fb0`(744B，27 调用者)、`0x8ea720`(423B，25 调用者)、`0x8e7af0`(338B，21 调用者)、`0x90c0a0`(338B，20 调用者)、`0xb4d80`(9B，10 调用者)、`0xb44d0`(531B，23 调用者)、`0x97a090`(1599B，17 调用者)、`0x50bc0`(4B，6 调用者)、`0x97a830`(75B，571 调用者)、`0x998500`(109B，2318 调用者)、`0x92dee0`(1148B，49 调用者)、`0x63f2f0`(0B)、`0x910ba0`(109B，1002 调用者)、`0x63f2f8`(0B)、`0x9989a0`(125B，837 调用者)、`0x7bb7a0`(54B，56 调用者)、`0x998fe0`(79B，783 调用者)、`0x697150`(221B，11 调用者)、`0x62f280`(171B，5209 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x979e70`(51B，676 调用者)、`0x998bc0`(124B，833 调用者)
* 字符串：`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`
* 浮点常量：**0.5**（`0x9b1618`）、**0.001**（`0x9b1640`）、**0.25**（`0x9b1638`）
* 立即数：`1`×4, `2`×1, `3`×5, `4`×3, `8`×3, `15`×3, `16`×10, `24`×3, `40`×1, `104`×3, `120`×11, `2984`×2
* 字段偏移（142 个）：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x54`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x84`、`+0x88`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x150`、`+0x180`、`+0x188`、`+0x1c8`、`+0x210`、`+0x230`、`+0x250`、`+0x278`、`+0x280`、`+0x290`、`+0x2b8`、`+0x2c8`、`+0x308`、`+0x350`、`+0x370`、`+0x390`、`+0x3b8`、`+0x3c0`、`+0x3d0`、`+0x408`、`+0x448`、`+0x490`、`+0x4b0`、`+0x4d0`、`+0x4f0`、`+0x4f8`、`+0x500`、`+0x510`、`+0x528`、`+0x548`、`+0x550`、`+0x558`、`+0x560`、`+0x568`、`+0x56c`、`+0x570`、`+0x571`、`+0x574`、`+0x578`、`+0x580`、`+0x588`、`+0x5a0`、`+0x5a8`、`+0x5b0`、`+0x5b8`、`+0x5c0`、`+0x5c8`、`+0x5d0`、`+0x5e8`、`+0x5f0`、`+0x608`、`+0x610`、`+0x611`、`+0x618`、`+0x620`、`+0x628`、`+0x630`、`+0x638`、`+0x640`、`+0x648`、`+0x650`、`+0x670`、`+0x690`、`+0x698`、`+0x6a0`、`+0x6b0`、`+0x6c8`、`+0x6e8`、`+0x700`、`+0x708`、`+0x70c`、`+0x710`、`+0x711`、`+0x714`、`+0x718`、`+0x720`、`+0x728`、`+0x740`、`+0x748`、`+0x750`、`+0x758`、`+0x760`、`+0x768`、`+0x770`、`+0x788`、`+0x790`、`+0x7a8`、`+0x7b0`、`+0x7b1`、`+0x7b8`、`+0x7c0`、`+0x7c8`、`+0x7d0`、`+0x7d8`、`+0x7e0`、`+0x7e8`、`+0x7f0`

**尚未解**：它与 `0x73280`(11,567 B) 的分工、是否为

### 附 6.12 `0x6D470`（11,478 B，第三个巨物）**[已证实 + 未解]**

* 函数：`0x6d470`，11478 字节 / **2116 条指令**
* 被调用者（51 个）：`0x14b9c0`(192B)、`0x14db40`(888B)、`0x4fc2c0`(10B，7 调用者)、`0x14f300`(107B)、`0x4f9bc0`(18B，17 调用者)、`0x4f9480`(1849B，17 调用者)、`0x4f8fb0`(33B，17 调用者)、`0x4f8fe0`(534B，14 调用者)、`0x5cd800`(610B，113 调用者)、`0x5d1810`(104B，20 调用者)、`0x14e140`(1483B)、`0x14c8c0`(1057B)、`0x6c7f0`(177B)、`0x60a620`(2620B，680 调用者)、`0x9984b0`(5B，5721 调用者)、`0x62f280`(171B，5209 调用者)、`0x14ed80`(173B)、`0x14f6e0`(200B)、`0x998500`(109B，2318 调用者)、`0x609e20`(221B，9 调用者)、`0x51cdd0`(478B，22 调用者)、`0x63f2f0`(0B)、`0x4fc5a0`(8B，114 调用者)、`0x6c0e0`(5B，19 调用者)、`0x979fe0`(5B，165 调用者)、`0x941b40`(408B)、`0x51e7e0`(1294B，47 调用者)、`0x92ecb0`(791B，180 调用者)、`0x4fc320`(11B，7 调用者)、`0x4f8c60`(4B，17 调用者)、`0x5d2200`(62B)、`0x14d510`(355B)、`0x14eee0`(294B)、`0x14f010`(625B)、`0x14fd00`(2211B)、`0x14d7f0`(381B)、`0x4d3ee0`(12B，11 调用者)、`0x14d430`(48B)、`0x4fc5b0`(319B，85 调用者)、`0x4f76d0`(4B，15 调用者)、`0x97a090`(1599B，17 调用者)、`0x910ba0`(109B，1002 调用者)、`0x5d1880`(326B)、`0x5d2a40`(19B，17 调用者)、`0x5d2900`(186B，28 调用者)、`0x51fa30`(177B，6 调用者)、`0x979ff0`(74B，98 调用者)、`0x987220`(702B，126 调用者)、`0x979e70`(51B，676 调用者)、`0x4f8370`(6B，74 调用者)、`0x4f8380`(6B，85 调用者)
* 字符串：`sheet`、`NestAllPartsAux`、`..\multi\rectangle_nester.cpp`、`sheet->is_rectangular()`、`NestAllPartsAux`、`..\multi\rectangle_nester.cpp`、`availables.size() == nb_parts`、`NestAllPartsAux`
* 浮点常量：**0.99**（`0x9b15e0`）、**0.1**（`0x9b1610`）、**1**（`0x9b1580`）、**0.5**（`0x9b1618`）、**0.5**（`0x9b1618`）、**0.5**（`0x9b1618`）、**0.5**（`0x9b1618`）
* 立即数：`1`×9, `2`×3, `4`×1, `8`×3, `10`×3, `13`×3, `16`×50, `19`×2, `29`×6, `31`×1, `32`×3, `40`×1, `41`×2, `48`×3, `112`×6, `115`×3, `120`×1, `128`×1, `224`×6, `396`×1, `416`×1, `449`×1, `491`×3, `2664`×2, `10361`×2, `10536`×3
* 字段偏移（158 个）：`+0x1`、`+0x4`、`+0x8`、`+0x10`、`+0x12`、`+0x18`、`+0x1c`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x8c`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x14c`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x180`、`+0x188`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c8`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1e8`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x208`、`+0x210`、`+0x218`、`+0x220`、`+0x230`、`+0x238`、`+0x240`、`+0x250`、`+0x258`、`+0x260`、`+0x270`、`+0x290`、`+0x2b0`、`+0x2d0`、`+0x2e0`、`+0x2f0`、`+0x300`、`+0x310`、`+0x318`、`+0x320`、`+0x330`、`+0x338`、`+0x340`、`+0x350`、`+0x358`、`+0x360`、`+0x370`、`+0x378`、`+0x380`、`+0x390`、`+0x398`、`+0x3a0`、`+0x3b0`、`+0x3b8`、`+0x3c0`、`+0x3d0`、`+0x3d8`、`+0x3e0`、`+0x3f0`、`+0x3f8`、`+0x400`、`+0x410`、`+0x418`、`+0x420`、`+0x430`、`+0x450`、`+0x460`、`+0x470`、`+0x4a0`、`+0x4d0`、`+0x500`、`+0x530`、`+0x560`、`+0x590`、`+0x598`、`+0x5a0`、`+0x5a8`、`+0x5b0`、`+0x5b8`、`+0x5c0`、`+0x5d8`、`+0x600`、`+0x608`、`+0x610`、`+0x618`、`+0x620`、`+0x628`、`+0x630`、`+0x638`、`+0x670`、`+0x678`、`+0x680`、`+0x688`、`+0x690`、`+0x698`、`+0x6e0`、`+0x708`、`+0x720`、`+0x728`、`+0x730`、`+0x738`、`+0x740`、`+0x750`、`+0x758`、`+0x760`、`+0x76a`、`+0x778`、`+0x7c0`、`+0x7c8`、`+0x7d0`、`+0x7da`、`+0x7e8`

**尚未解**：它与 `0x70150`/`0x73280` 的分工；本档不给它编名字。

### 附 6.13 第六遍：`Multi::NoFillNester::Run`（`0x7F240`，8,440 B）**[已证实 + 未解]**

* 函数：`0x7f240`，8440 字节 / **1503 条指令**
* 被调用者（33 个）：`0xb44d0`(531B，23 调用者)、`0xb4d20`(69B，12 调用者)、`0xb4d90`(9B，19 调用者)、`0x51e7e0`(1294B，47 调用者)、`0x4fc2e0`(14B，52 调用者)、`0x5235f0`(54B，28 调用者)、`0x998500`(109B，2318 调用者)、`0x9984b0`(5B，5721 调用者)、`0x92ecb0`(791B，180 调用者)、`0x63f2f0`(0B)、`0x4fc3d0`(10B，28 调用者)、`0x542ef0`(55B，6 调用者)、`0x53d0f0`(2046B，7 调用者)、`0x51d0c0`(5B，103 调用者)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x905f30`(256B)、`0x51d090`(4B，53 调用者)、`0x51cdd0`(478B，22 调用者)、`0x7ef20`(792B)、`0x51d310`(5B，20 调用者)、`0x51fde0`(30B，18 调用者)、`0x51d320`(416B，17 调用者)、`0x7ed90`(192B)、`0x90ecb0`(650B，185 调用者)、`0x910a60`(136B，185 调用者)、`0x51faf0`(743B，16 调用者)、`0x983ca0`(145B，289 调用者)、`0x891b40`(52B，240 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x62f280`(171B，5209 调用者)、`0x979e70`(51B，676 调用者)、`0x97ab50`(75B，352 调用者)
* 字符串：`%llu`、`NoFill(`、`vector::_M_range_check: __n (which is %zu) >= this`、`vector::_M_range_check: __n (which is %zu) >= this`、`basic_string::append`、`basic_string::append`
* 浮点常量：**0.5**（`0x9b1800`）、**0.3**（`0x9b1808`）
* 立即数：`1`×6, `2`×5, `3`×9, `4`×3, `7`×1, `8`×2, `15`×2, `16`×30, `26`×1, `32`×1, `41`×1, `55`×1, `103`×1, `110`×1, `120`×2, `1288`×2, `10341`×1
* 字段偏移（163 个）：`+0x1`、`+0x4`、`+0x8`、`+0xc`、`+0x10`、`+0x12`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x34`、`+0x36`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x180`、`+0x188`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c8`、`+0x1d0`、`+0x1e0`、`+0x1e8`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x208`、`+0x210`、`+0x218`、`+0x220`、`+0x250`、`+0x258`、`+0x270`、`+0x278`、`+0x280`、`+0x288`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2a8`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2e8`、`+0x2f0`、`+0x2f8`、`+0x300`、`+0x308`、`+0x30c`、`+0x310`、`+0x311`、`+0x314`、`+0x318`、`+0x320`、`+0x328`、`+0x330`、`+0x338`、`+0x340`、`+0x348`、`+0x350`、`+0x358`、`+0x360`、`+0x368`、`+0x370`、`+0x378`、`+0x380`、`+0x388`、`+0x390`、`+0x398`、`+0x3a0`、`+0x3b0`、`+0x3b8`、`+0x3c0`、`+0x3c3`、`+0x3c8`、`+0x3d0`、`+0x3d8`、`+0x3e0`、`+0x3e8`、`+0x3f0`、`+0x3f8`、`+0x400`、`+0x408`、`+0x410`、`+0x428`、`+0x430`、`+0x438`、`+0x440`、`+0x448`、`+0x44c`、`+0x450`、`+0x451`、`+0x454`、`+0x458`、`+0x460`、`+0x468`、`+0x470`、`+0x478`、`+0x480`、`+0x488`、`+0x490`、`+0x498`、`+0x4a0`、`+0x4a8`、`+0x4b0`、`+0x4b8`、`+0x4c0`、`+0x4c8`、`+0x4d0`、`+0x4d8`、`+0x4e0`、`+0x4f0`、`+0x560`、`+0x570`、`+0x578`、`+0x580`

**尚未解**：禁填充判据（哪些孔洞被排除）、它与 `0x7BF0C0` 的关系（该地址同时出现在 `GetLeatherLayer` 与 quality 断言处）。`strategy.nofill` 仍标 `Substituted`。

### 附 6.14 第七遍：`Multi::CompactNester::Run`（`0xB13D0`，9,393 B）**[已证实 + 未解]**

* 函数：`0xb13d0`，9393 字节 / **1811 条指令**
* 被调用者（47 个）：`0x51cc90`(312B，17 调用者)、`0x50ba0`(8B)、`0xb44d0`(531B，23 调用者)、`0xb4d20`(69B，12 调用者)、`0x9984b0`(5B，5721 调用者)、`0x92ecb0`(791B，180 调用者)、`0x97a830`(75B，571 调用者)、`0x4f8370`(6B，74 调用者)、`0x97a090`(1599B，17 调用者)、`0x4f8380`(6B，85 调用者)、`0x64380`(34B，7 调用者)、`0xb4d70`(5B，9 调用者)、`0x30260`(9B，25 调用者)、`0x51d8f0`(1139B，8 调用者)、`0xb4d90`(9B，19 调用者)、`0x50c60`(5785B，6 调用者)、`0x50bb0`(9B)、`0xb4d80`(9B，10 调用者)、`0x998500`(109B，2318 调用者)、`0x92dee0`(1148B，49 调用者)、`0x63f2f0`(0B)、`0x910ba0`(109B，1002 调用者)、`0x63f2f8`(0B)、`0x51d2f0`(5B，102 调用者)、`0xb0380`(4167B)、`0x50bc0`(4B，6 调用者)、`0x5235f0`(54B，28 调用者)、`0x63f2e8`(0B)、`0x6c0e0`(5B，19 调用者)、`0x4ca00`(601B，9 调用者)、`0x60a620`(2620B，680 调用者)、`0x434d0`(407B，10 调用者)、`0x51d320`(416B，17 调用者)、`0x910a60`(136B，185 调用者)、`0x51faf0`(743B，16 调用者)、`0x9989a0`(125B，837 调用者)、`0x7bb7a0`(54B，56 调用者)、`0x998fe0`(79B，783 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x62f280`(171B，5209 调用者)、`0x90ecb0`(650B，185 调用者)、`0x910af0`(168B，345 调用者)、`0x97ab50`(75B，352 调用者)、`0x697150`(221B，11 调用者)、`0x8e6390`(107B，48 调用者)、`0x979e70`(51B，676 调用者)、`0x998bc0`(124B，833 调用者)
* 字符串：`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::append`
* 浮点常量：**0.05**（`0x9b1f88`）、**1**（`0x9b1f38`）、**1**（`0x9b1f90`）、**0.05**（`0x9b1f88`）、**1.1**（`0x9b1f98`）、**0.9**（`0x9b1fa0`）
* 立即数：`1`×10, `2`×8, `3`×8, `4`×5, `5`×2, `6`×1, `8`×6, `15`×4, `16`×33, `20`×3, `24`×3, `27`×1, `81`×1, `104`×3, `110`×1, `112`×3, `116`×1, `120`×9, `1496`×2
* 字段偏移（180 个）：`+0x1`、`+0x4`、`+0x8`、`+0xc`、`+0x10`、`+0x12`、`+0x14`、`+0x18`、`+0x1a`、`+0x1c`、`+0x20`、`+0x24`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x54`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x10d`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x180`、`+0x188`、`+0x190`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c8`、`+0x1d0`、`+0x1d8`、`+0x1f8`、`+0x200`、`+0x208`、`+0x210`、`+0x218`、`+0x21c`、`+0x220`、`+0x221`、`+0x224`、`+0x228`、`+0x230`、`+0x238`、`+0x240`、`+0x248`、`+0x250`、`+0x258`、`+0x260`、`+0x268`、`+0x270`、`+0x278`、`+0x280`、`+0x288`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2a8`、`+0x2b0`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2d3`、`+0x2d8`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x2f8`、`+0x300`、`+0x308`、`+0x310`、`+0x318`、`+0x338`、`+0x340`、`+0x348`、`+0x350`、`+0x358`、`+0x35c`、`+0x360`、`+0x361`、`+0x364`、`+0x368`、`+0x370`、`+0x378`、`+0x380`、`+0x388`、`+0x390`、`+0x398`、`+0x3a0`、`+0x3a8`、`+0x3b0`、`+0x3b8`、`+0x3c0`、`+0x3c8`、`+0x3d0`、`+0x3d8`、`+0x3e0`、`+0x3e8`、`+0x3f0`、`+0x400`、`+0x408`、`+0x410`、`+0x415`、`+0x420`、`+0x428`、`+0x430`、`+0x438`、`+0x440`、`+0x448`、`+0x450`、`+0x458`、`+0x478`、`+0x480`、`+0x488`、`+0x490`、`+0x498`、`+0x49c`、`+0x4a0`、`+0x4a1`、`+0x4a4`、`+0x4a8`、`+0x4b0`、`+0x4b8`、`+0x4c0`、`+0x4c8`、`+0x4d0`、`+0x4d8`、`+0x4e0`、`+0x4e8`、`+0x4f0`、`+0x4f8`、`+0x500`、`+0x508`、`+0x510`、`+0x518`、`+0x520`、`+0x528`、`+0x530`、`+0x580`、`+0x5a0`、`+0x5b0`、`+0x5c0`、`+0x638`、`+0x640`、`+0x648`、`+0x650`

**尚未解**：压缩（compact）的具体操作（平移收敛？空洞填补？）、它与 `0xB0130`(309 B)/`0xB46F0`(894 B) 的分工。`strategy.compact` 仍标 `Substituted`。

### 附 6.15 三个巨物的分工确定了：`0x6D470` = `NestAllPartsAux` **[已证实]**

`0x6D470`（11,478 B / 2,116 条指令）**内联拼出的字符串直接给出身份**：

| 字符串 | 含义 |
|---|---|
| `'NestAllPartsAux'` | 函数名 |
| `'..\\multi\\rectangle_nester.cpp'` | **所属 TU = `..\multi\rectangle_nester.cpp`** |
| `'sheet->is_rectangular()'` | 断言：**只接受矩形板材** |
| `'availables.size() == nb_parts'` | 断言：可用零件数组覆盖全部零件 |

常量：**`0.99`**（`0x9B15E0` —— 与 `0x73280` **同一个**面积松弛）、`0.1`、`1`、`0.5`×4。

⇒ **三者关系**：`0x6D470`（`NestAllPartsAux`，`rectangle_nester.cpp` 的核心放置例程）调用
`0x73280`（11,567 B，读 `Pb[+0xC8]` 与选项）与 `0x70150`（8,524 B，含 `0.5`/`0.25`/`0.001` 折半细化）。
**它们不是"未知巨物"，而是矩形策略的内核层**，且 `0.99` 面积松弛在 `0x73280` 与 `0x6D470` 中**共用**。

### 附 6.16 另外两个 `Run` 体的常量（附 6.13 / 6.14 的补充）**[已证实]**

* `Multi::NoFillNester::Run`（`0x7F240`，8,440 B / 1,503 条指令）：追踪前缀 **`'NoFill('`**（已入库为
  `kTraceNoFill`）；常量 **`0.5`、`0.3`**；被调用者含 `0x4FC2E0`（`Pb[+0x120] > 1`，与 mode-2 的 tooling 闸同一判据）。
* `Multi::CompactNester::Run`（`0xB13D0`，9,393 B / 1,811 条指令）：常量 **`0.05`、`1.0`、`1.1`、`0.9`**
  —— `1.1`/`0.9` 是**成对的 10% 缩放系数**，强烈提示"放大后重试 / 收缩后重试"；`0.05` 像步长。
  **语义为推断**，未入库命名常量。

### 附 6.17 `0x770D10` = `Packer::Run`（`..\tiling\packer.cpp`）**[已证实]**

内联串给出身份：`'..\\tiling\\packer.cpp'`、`'Run'`、`'availables.size() == m_problem.GetNumberOfParts()'`（前置条件：可用零件数组覆盖问题全部零件）。

* 字节/指令：**8230 B / 1641 条指令**
* 被调用者（65 个）：`0x5f4310`(35B)、`0x4fc5a0`(8B)、`0x1505e0`(177B)、`0x60a620`(2620B)、`0x9984b0`(5B)、`0x4fc260`(11B)、`0x4f8370`(6B)、`0x910ba0`(109B)、`0x15ed50`(944B)、`0x4fff80`(1035B)、`0x522580`(849B)、`0x998500`(109B)、`0x6845d0`(152B)、`0x5f4340`(140B)
* 字符串：`..\tiling\packer.cpp`、`Run`、`availables.size() == m_problem.GetNumber`、`prices.size() == m_problem.GetNumberOfPa`
* 浮点常量：**1**(`0x9bd360`)、**0.999**(`0x9bd390`)
* 立即数：`1`×14, `2`×1, `3`×5, `4`×9, `5`×6, `7`×4, `8`×4, `14`×1, `15`×1, `16`×33, `18`×1, `19`×3, `20`×4, `24`×2, `32`×1, `56`×1, `57`×1, `71`×1, `72`×1, `96`×2, `100`×2, `110`×1, `116`×2, `144`×8, `410`×1, `411`×1, `1528`×2
* 字段偏移（128 个）：+0x1`、`+0x4`、`+0x6`、`+0x8`、`+0x9`、`+0xc`、`+0x10`、`+0x12`、`+0x14`、`+0x16`、`+0x18`、`+0x1c`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xbf`、`+0xc0`、`+0xd0`、`+0xe0`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x150`、`+0x160`、`+0x180`、`+0x1a0`、`+0x1c0`、`+0x1e0`、`+0x1e8`、`+0x1f0`、`+0x200`、`+0x208`、`+0x220`、`+0x240`、`+0x260`、`+0x268`、`+0x280`、`+0x2a0`、`+0x2c0`、`+0x2e0`、`+0x300`、`+0x320`、`+0x328`、`+0x330`、`+0x340`、`+0x348`、`+0x350`、`+0x360`、`+0x368`、`+0x370`、`+0x380`、`+0x388`、`+0x390`、`+0x3a0`、`+0x3a8`、`+0x3b0`、`+0x3c0`、`+0x3c8`、`+0x3d0`、`+0x3e0`、`+0x3e8`、`+0x3f0`、`+0x400`、`+0x410`、`+0x440`、`+0x448`、`+0x450`、`+0x457`、`+0x490`、`+0x4a0`、`+0x4a8`、`+0x4b0`、`+0x4b8`、`+0x4c0`、`+0x4c8`、`+0x4d0`、`+0x4d8`、`+0x4e0`、`+0x4e8`、`+0x4f0`、`+0x4f8`、`+0x500`、`+0x501`、`+0x510`、`+0x518`、`+0x520`、`+0x523`、`+0x527`、`+0x528`、`+0x52e`、`+0x530`、`+0x568`、`+0x590`、`+0x5a0`、`+0x5b0`、`+0x5c0`、`+0x5d0`、`+0x5e0`、`+0x640`、`+0x648`、`+0x650`、`+0x660`、`+0x668`、`+0x670`、`+0x678

**尚未解**：`Packer::Run` 的主循环结构、它如何消费 `Compute*Tilings` 产出的图案、以及 `availables` 与 `m_problem` 的绑定方式。

### 附 6.18 第八遍：`Multi::MultiTorchNester::Run`（`0x7BCC0`，12,232 B）**[已证实 + 未解]**

* 函数：`0x7bcc0`，12232 字节 / **2378 条指令**
* 被调用者（53 个）：`0x51cdd0`(478B，22 调用者)、`0x4f8370`(6B，74 调用者)、`0x4f8380`(6B，85 调用者)、`0xb4d90`(9B，19 调用者)、`0x4fc3d0`(10B，28 调用者)、`0x543030`(67B)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x9984b0`(5B，5721 调用者)、`0x5235f0`(54B，28 调用者)、`0x998500`(109B，2318 调用者)、`0x79da0`(4611B)、`0x51d0c0`(5B，103 调用者)、`0x78110`(671B)、`0x77e40`(671B)、`0x92ecb0`(791B，180 调用者)、`0x63f2f0`(0B)、`0x944530`(133B，165 调用者)、`0x9454d0`(89B，139 调用者)、`0x8aab00`(181B，133 调用者)、`0x978010`(959B，421 调用者)、`0x8688e0`(545B，125 调用者)、`0x869d00`(5B，96 调用者)、`0x97a830`(75B，571 调用者)、`0x8aabc0`(41B，257 调用者)、`0x9445e0`(87B，237 调用者)、`0x51e7e0`(1294B，47 调用者)、`0xb44d0`(531B，23 调用者)、`0x266d50`(31B，25 调用者)、`0xb4d70`(5B，9 调用者)、`0x30af0`(108B，9 调用者)、`0x6c0e0`(5B，19 调用者)、`0x434d0`(407B，10 调用者)、`0x63f2f8`(0B)、`0x910af0`(168B，345 调用者)、`0x4fd0e0`(4B)、`0x4fc5a0`(8B，114 调用者)、`0x4f7680`(9B，10 调用者)、`0x4fc5b0`(319B，85 调用者)、`0x5c4c60`(109B，16 调用者)、`0x4f7690`(9B，29 调用者)、`0x5c2e40`(138B，32 调用者)、`0x7afb0`(3334B)、`0x783b0`(816B)、`0x64350`(39B，7 调用者)、`0xb4d20`(69B，12 调用者)、`0x90bef0`(220B，25 调用者)、`0x8f4240`(220B)、`0x91a7c0`(160B，36 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x62f280`(171B，5209 调用者)、`0x915ec0`(68B，73 调用者)、`0x979e70`(51B，676 调用者)
* 字符串：`res <= y * 1.001`、`basic_string::_M_construct null not valid`、`res <= y * 1.001`、`test2`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`
* 浮点常量：**0.05**（`0x9b1768`）、**1.001**（`0x9b1740`）、**0.999**（`0x9b1758`）、**0.5**（`0x9b1750`）、**0.999**（`0x9b1758`）、**3**（`0x9b1770`）、**0.999**（`0x9b1758`）、**0.25**（`0x9b1760`）、**0.999**（`0x9b1758`）、**0.999**（`0x9b1758`）、**0.5**（`0x9b1750`）、**3**（`0x9b1770`）、**0.25**（`0x9b1760`）、**1.001**（`0x9b1740`）、**0.999**（`0x9b1758`）、**1.001**（`0x9b1740`）、**0.999**（`0x9b1758`）、**1.001**（`0x9b1740`）、**1.001**（`0x9b1740`）、**1.001**（`0x9b1740`）、**1.001**（`0x9b1740`）、**1.001**（`0x9b1740`）、**0.999**（`0x9b1758`）、**0.25**（`0x9b1760`）、**0.5**（`0x9b1750`）、**0.99**（`0x9b1748`）、**1.001**（`0x9b1740`）、**0.5**（`0x9b1750`）、**0.99**（`0x9b1748`）、**0.99**（`0x9b1748`）、**0.99**（`0x9b1748`）
* 立即数：`1`×21, `2`×8, `3`×10, `4`×3, `5`×4, `8`×7, `14`×2, `15`×4, `16`×56, `18`×2, `19`×1, `24`×5, `26`×1, `30`×4, `64`×4, `100`×1, `104`×4, `110`×2, `116`×1, `120`×4, `197`×1, `203`×1, `297`×1, `357`×1, `1640`×2, `12592`×1
* 字段偏移（137 个）：`+0x1`、`+0x8`、`+0x10`、`+0x12`、`+0x14`、`+0x18`、`+0x1c`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xf0`、`+0x110`、`+0x130`、`+0x138`、`+0x140`、`+0x150`、`+0x158`、`+0x160`、`+0x170`、`+0x178`、`+0x180`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x210`、`+0x218`、`+0x220`、`+0x230`、`+0x238`、`+0x240`、`+0x250`、`+0x258`、`+0x260`、`+0x270`、`+0x278`、`+0x280`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2d3`、`+0x2d8`、`+0x2de`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x2f8`、`+0x300`、`+0x318`、`+0x320`、`+0x328`、`+0x330`、`+0x338`、`+0x340`、`+0x378`、`+0x3c0`、`+0x3e0`、`+0x418`、`+0x420`、`+0x421`、`+0x428`、`+0x430`、`+0x438`、`+0x440`、`+0x450`、`+0x458`、`+0x460`、`+0x463`、`+0x465`、`+0x468`、`+0x46e`、`+0x470`、`+0x478`、`+0x480`、`+0x488`、`+0x490`、`+0x4a8`、`+0x4b0`、`+0x4b8`、`+0x4c0`、`+0x4c8`、`+0x4d0`、`+0x508`、`+0x550`、`+0x570`、`+0x5a8`、`+0x5b0`、`+0x5b1`、`+0x5b8`、`+0x5c0`、`+0x5c8`、`+0x5d0`、`+0x5e0`、`+0x5f0`、`+0x600`、`+0x610`、`+0x620`、`+0x630`、`+0x640`、`+0x650`、`+0x6c0`、`+0x6c8`、`+0x6d0`、`+0x6d8`、`+0x6e0`

**尚未解**：火焰（torch）排布的几何约束、`+0xC` 传来的火数与它的关系（见 `0x2C4D0` 的 `r9d`）、以及 `0x7C98A0` 一族辅助的分工。`strategy.multitorch` 仍标 `Substituted`。

### 附 6.19 第九遍：`Multi::RowNester::Run`（`0x913E0`，12,380 B）**[已证实 + 未解]**

* 函数：`0x913e0`，12380 字节 / **2370 条指令**
* 被调用者（51 个）：`0xb44d0`(531B，23 调用者)、`0x13c560`(104B)、`0x8c280`(221B)、`0x51cc90`(312B，17 调用者)、`0x998500`(109B，2318 调用者)、`0x63f2f0`(0B)、`0x4f8fb0`(33B，17 调用者)、`0x8ff70`(5226B)、`0x9984b0`(5B，5721 调用者)、`0x92ecb0`(791B，180 调用者)、`0x910ba0`(109B，1002 调用者)、`0x51faf0`(743B，16 调用者)、`0xb4d90`(9B，19 调用者)、`0x5235f0`(54B，28 调用者)、`0x51cdd0`(478B，22 调用者)、`0x145960`(1979B)、`0x149b40`(2328B)、`0x1370a0`(511B)、`0x13eb20`(2318B)、`0x1372a0`(162B)、`0x14a460`(1885B)、`0x148dd0`(40B)、`0x8e1f0`(2381B)、`0x8d2d0`(192B)、`0x90ecb0`(650B，185 调用者)、`0x910a60`(136B，185 调用者)、`0x8f290`(801B)、`0x5475a0`(95B，9 调用者)、`0x142690`(13008B)、`0x136d50`(159B)、`0x97a830`(75B，571 调用者)、`0x14abc0`(591B)、`0x51e1c0`(136B)、`0x51d0c0`(5B，103 调用者)、`0x51f470`(549B，20 调用者)、`0x9108e0`(256B，60 调用者)、`0x63f2f8`(0B)、`0x910af0`(168B，345 调用者)、`0x4f8370`(6B，74 调用者)、`0x4f8380`(6B，85 调用者)、`0x60a620`(2620B，680 调用者)、`0x9989a0`(125B，837 调用者)、`0x998fe0`(79B，783 调用者)、`0x679070`(54B，21 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x62f280`(171B，5209 调用者)、`0x979e70`(51B，676 调用者)、`0x998bc0`(124B，833 调用者)、`0x8bcc40`(104B)、`0x8be160`(104B)、`0x97ab50`(75B，352 调用者)
* 字符串：`%llu`、`Row `、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`Pipe `、`basic_string::append`、`basic_string::append`、`basic_string::append`
* 浮点常量：无
* 立即数：`1`×9, `2`×9, `3`×2, `4`×6, `5`×2, `8`×5, `15`×4, `16`×42, `17`×1, `23`×1, `24`×2, `32`×2, `64`×2, `88`×4, `96`×2, `110`×1, `112`×2, `116`×1, `120`×9, `426`×1, `1736`×2
* 字段偏移（211 个）：`+0x1`、`+0x5`、`+0x8`、`+0x10`、`+0x11`、`+0x14`、`+0x16`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x140`、`+0x148`、`+0x150`、`+0x160`、`+0x168`、`+0x170`、`+0x180`、`+0x188`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1c0`、`+0x1c8`、`+0x1e0`、`+0x1e8`、`+0x1f0`、`+0x200`、`+0x208`、`+0x210`、`+0x220`、`+0x228`、`+0x230`、`+0x240`、`+0x248`、`+0x250`、`+0x258`、`+0x260`、`+0x268`、`+0x270`、`+0x271`、`+0x278`、`+0x280`、`+0x288`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2b0`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x2f8`、`+0x300`、`+0x308`、`+0x310`、`+0x318`、`+0x338`、`+0x340`、`+0x348`、`+0x350`、`+0x358`、`+0x35c`、`+0x360`、`+0x361`、`+0x364`、`+0x368`、`+0x370`、`+0x378`、`+0x380`、`+0x388`、`+0x390`、`+0x398`、`+0x3a0`、`+0x3a8`、`+0x3b0`、`+0x3b8`、`+0x3c0`、`+0x3c8`、`+0x3d0`、`+0x3d8`、`+0x3e0`、`+0x3e8`、`+0x3f0`、`+0x400`、`+0x408`、`+0x410`、`+0x411`、`+0x412`、`+0x413`、`+0x418`、`+0x420`、`+0x428`、`+0x430`、`+0x438`、`+0x440`、`+0x448`、`+0x450`、`+0x458`、`+0x478`、`+0x480`、`+0x488`、`+0x490`、`+0x498`、`+0x49c`、`+0x4a0`、`+0x4a1`、`+0x4a4`、`+0x4a8`、`+0x4b0`、`+0x4b8`、`+0x4c0`、`+0x4c8`、`+0x4d0`、`+0x4d8`、`+0x4e0`、`+0x4e8`、`+0x4f0`、`+0x4f8`、`+0x500`、`+0x508`、`+0x510`、`+0x518`、`+0x520`、`+0x528`、`+0x530`、`+0x540`、`+0x548`、`+0x550`、`+0x555`、`+0x558`、`+0x560`、`+0x568`、`+0x570`、`+0x578`、`+0x580`、`+0x588`、`+0x590`、`+0x598`、`+0x5b8`、`+0x5c0`、`+0x5c8`、`+0x5d0`、`+0x5d8`、`+0x5dc`、`+0x5e0`、`+0x5e1`、`+0x5e4`、`+0x5e8`、`+0x5f0`、`+0x5f8`、`+0x600`、`+0x608`、`+0x610`、`+0x618`、`+0x620`、`+0x628`、`+0x630`、`+0x638`、`+0x640`、`+0x648`、`+0x650`、`+0x658`、`+0x660`、`+0x668`、`+0x670`、`+0x680`、`+0x690`、`+0x6a0`、`+0x6b0`、`+0x720`、`+0x730`、`+0x738`

**尚未解**：行/管排样的分层与轨道模型（`RowNester` 的槽 #3/#4 参数如何进入）、以及它与 `0x8CD20`/`0x8C010` 两个极小访问器的关系。`strategy.row` 仍标 `Substituted`（行核心已恢复见 `module.row`）。

### 附 6.20 第十遍：`Multi::NestingNester::Run`（`0x378E0`，14,374 B，基础放置器）**[已证实 + 未解]**

* 函数：`0x378e0`，14374 字节 / **2841 条指令**
* 被调用者（75 个）：`0x5f4310`(35B，45 调用者)、`0xb4d70`(5B，9 调用者)、`0x31db0`(2284B，14 调用者)、`0xb44d0`(531B，23 调用者)、`0xb4d80`(9B，10 调用者)、`0x3f750`(768B，8 调用者)、`0x6c0e0`(5B，19 调用者)、`0x3e3e0`(854B，7 调用者)、`0x9984b0`(5B，5721 调用者)、`0x90c200`(327B，8 调用者)、`0xb4d90`(9B，19 调用者)、`0x524890`(669B，6 调用者)、`0x4f8390`(420B，35 调用者)、`0x4fc310`(15B，16 调用者)、`0x33ea0`(116B)、`0x33f20`(194B)、`0x4fc5a0`(8B，114 调用者)、`0x30220`(39B，9 调用者)、`0x891b40`(52B，240 调用者)、`0x523050`(174B，33 调用者)、`0x4f8370`(6B，74 调用者)、`0x4f8380`(6B，85 调用者)、`0x3b7b0`(8B)、`0x185750`(208B)、`0x5238b0`(193B，19 调用者)、`0x6c470`(852B，7 调用者)、`0x4f1f60`(2299B)、`0x678ae0`(590B，7 调用者)、`0x4fc3d0`(10B，28 调用者)、`0x189ca0`(571B)、`0x185a40`(736B)、`0x609e20`(221B，9 调用者)、`0x3f070`(1733B)、`0x4fc340`(11B，7 调用者)、`0x35f30`(6436B)、`0x3b7c0`(66B)、`0x31ce0`(142B，14 调用者)、`0x51d0c0`(5B，103 调用者)、`0x434d0`(407B，10 调用者)、`0x33040`(177B)、`0x910a60`(136B，185 调用者)、`0x992750`(226B，31 调用者)、`0x32f80`(181B)、`0x51faf0`(743B，16 调用者)、`0x932420`(408B，36 调用者)、`0x5f4340`(140B，67 调用者)、`0x344d0`(6748B)、`0x3b870`(21B)、`0x3ba90`(17B)、`0x998500`(109B，2318 调用者)、`0x609f00`(284B)、`0x187020`(1171B)、`0x90bef0`(220B，25 调用者)、`0x60a620`(2620B，680 调用者)、`0x899820`(1426B，13 调用者)、`0x4cf30`(399B)、`0x4fc2e0`(14B，52 调用者)、`0x4f8f80`(7B，52 调用者)、`0xad5e0`(75B，8 调用者)、`0x52f810`(7B，8 调用者)、`0x52f820`(7B)、`0x32e20`(177B)、`0x63f2f0`(0B)、`0x4fc5b0`(319B，85 调用者)、`0x4f1e30`(136B)、`0x4d3ed0`(11B)、`0x910af0`(168B，345 调用者)、`0x65f350`(751B，65 调用者)、`0x62f280`(171B，5209 调用者)、`0x679010`(54B，60 调用者)、`0x979e70`(51B，676 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x97ab50`(75B，352 调用者)、`0x669d70`(128B，10 调用者)、`0x983ca0`(145B，289 调用者)
* 字符串：`strategy`、`deg_steps.size() == try_parts_ratio.size()`、`Run`、`..\multi\nesting_nester.cpp`、`parameters().nesting_pow_boost >= 1.0`、`Run`、`..\multi\nesting_nester.cpp`、`biggest`
* 浮点常量：**1**（`0x9af0e0`）、**0.33**（`0x9af180`）、**1**（`0x9af0e0`）、**1**（`0x9aeff0`）、**1**（`0x9aeff8`）、**1**（`0x9af000`）、**0.015**（`0x9af168`）、**0.5**（`0x9af0e8`）、**5**（`0x9af030`）、**15**（`0x9af038`）、**30**（`0x9af040`）、**0.2**（`0x9af010`）、**0.33**（`0x9af018`）、**0.5**（`0x9af020`）、**1**（`0x9af0e0`）、**1**（`0x9af0e0`）、**1**（`0x9af0e0`）、**2**（`0x9af060`）、**1**（`0x9af068`）、**1**（`0x9af070`）、**0.5**（`0x9af078`）、**0.7**（`0x9af178`）、**1**（`0x9af0e0`）
* 立即数：`1`×56, `2`×8, `3`×9, `4`×8, `5`×2, `6`×1, `7`×1, `8`×3, `9`×1, `10`×1, `15`×1, `16`×56, `24`×3, `29`×1, `32`×2, `48`×2, `50`×2, `64`×4, `89`×9, `100`×1, `208`×1, `269`×10, `391`×1, `408`×1, `512`×1, `548`×1, `554`×1, `577`×1, `582`×1, `3864`×2
* 字段偏移（132 个）：`+0x4`、`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x1c`、`+0x1d`、`+0x1e`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x44`、`+0x48`、`+0x4c`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xc0`、`+0xd0`、`+0xe0`、`+0xf0`、`+0xf4`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x130`、`+0x150`、`+0x170`、`+0x190`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1d0`、`+0x1f0`、`+0x210`、`+0x230`、`+0x250`、`+0x270`、`+0x290`、`+0x29c`、`+0x2a0`、`+0x2b0`、`+0x2d0`、`+0x2f0`、`+0x310`、`+0x330`、`+0x350`、`+0x358`、`+0x370`、`+0x390`、`+0x3b0`、`+0x3d0`、`+0x3d8`、`+0x3f0`、`+0x410`、`+0x418`、`+0x430`、`+0x450`、`+0x470`、`+0x490`、`+0x4d8`、`+0x508`、`+0x520`、`+0x528`、`+0x530`、`+0x538`、`+0x540`、`+0x548`、`+0x550`、`+0x558`、`+0x560`、`+0x564`、`+0x568`、`+0x570`、`+0x578`、`+0x580`、`+0x584`、`+0x585`、`+0x588`、`+0x590`、`+0x598`、`+0x5a0`、`+0x5b0`、`+0x5f8`、`+0x628`、`+0x640`、`+0x670`、`+0x690`、`+0x6a8`、`+0x6c8`、`+0x6e0`、`+0x6f0`、`+0x700`、`+0x710`、`+0x718`、`+0x720`、`+0x730`、`+0x738`、`+0x740`、`+0x748`、`+0x750`、`+0x758`、`+0x768`、`+0x770`、`+0x778`、`+0x780`、`+0x788`、`+0x790`、`+0x7a0`、`+0x7b0`、`+0x7b8`、`+0x7c0`、`+0x7d0`、`+0x7d8`、`+0x7e0`、`+0x7e8`、`+0x7f0`、`+0x7f8`

**尚未解**：主放置循环的步进顺序、`0x35F30`(6,436 B) 与 `0x31DB0`(2,284 B) 两个大辅助的分工、以及它与 `0x3F070`(GetNestingPart) 的数据交换。`strategy.nesting`/`search.pack_all` 仍标 `Substituted` —— **这是排料质量差距的主因**。

### 附 6.21 第十一遍：`Multi::TilingNester::Run`（`0x46940`，16,258 B，最大 `Run` 体）**[已证实 + 未解]**

* 函数：`0x46940`，16258 字节 / **3115 条指令**
* 被调用者（72 个）：`0x5f4310`(35B，45 调用者)、`0xb44b0`(4B)、`0x455c0`(177B，6 调用者)、`0x998500`(109B，2318 调用者)、`0x63f2f0`(0B)、`0xb4d90`(9B，19 调用者)、`0x4fc260`(11B，25 调用者)、`0x6c0e0`(5B，19 调用者)、`0x4c630`(964B)、`0x6c100`(367B)、`0x9984b0`(5B，5721 调用者)、`0x51cdd0`(478B，22 调用者)、`0x65b30`(1411B)、`0xb44d0`(531B，23 调用者)、`0x5475a0`(95B，9 调用者)、`0xaed20`(447B)、`0x50bd0`(137B，8 调用者)、`0x30250`(11B，25 调用者)、`0x524210`(61B)、`0x62fe20`(270B，90 调用者)、`0x303c0`(94B)、`0xaef10`(12B，12 调用者)、`0x97a830`(75B，571 调用者)、`0x92dee0`(1148B，49 调用者)、`0xaef80`(622B，14 调用者)、`0x51d320`(416B，17 调用者)、`0x82a0a0`(188B，11 调用者)、`0x92ecb0`(791B，180 调用者)、`0x695c70`(327B)、`0x693950`(4157B)、`0x50bc0`(4B，6 调用者)、`0x910ba0`(109B，1002 调用者)、`0x63f2f8`(0B)、`0x5235f0`(54B，28 调用者)、`0x51d0a0`(31B，17 调用者)、`0x51d0c0`(5B，103 调用者)、`0x45780`(177B)、`0x910a60`(136B，185 调用者)、`0x90ecb0`(650B，185 调用者)、`0x51faf0`(743B，16 调用者)、`0x5f4340`(140B，67 调用者)、`0x8e5ce0`(815B，17 调用者)、`0x97a090`(1599B，17 调用者)、`0x50680`(640B，6 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x4fc280`(11B)、`0x9de40`(904B)、`0x4f8370`(6B，74 调用者)、`0x4f8380`(6B，85 调用者)、`0x7d12a0`(3762B)、`0x910af0`(168B，345 调用者)、`0x8e6400`(1770B，29 调用者)、`0x8ea9d0`(335B，25 调用者)、`0x92e360`(2378B，22 调用者)、`0x8e1fb0`(744B，27 调用者)、`0x8ea720`(423B，25 调用者)、`0x8e7af0`(338B，21 调用者)、`0x90c0a0`(338B，20 调用者)、`0x9989a0`(125B，837 调用者)、`0x7bb7a0`(54B，56 调用者)、`0x998fe0`(79B，783 调用者)、`0x69a370`(144B，16 调用者)、`0x62f280`(171B，5209 调用者)、`0x697150`(221B，11 调用者)、`0x8d18c0`(88B)、`0x4f8390`(420B，35 调用者)、`0x998bc0`(124B，833 调用者)、`0x979e70`(51B，676 调用者)、`0x8e6390`(107B，48 调用者)、`0x8eef90`(328B，24 调用者)、`0x97ab50`(75B，352 调用者)、`0x679010`(54B，60 调用者)
* 字符串：`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`Tiling`、`strategy`
* 浮点常量：**1**（`0x9af948`）、**1**（`0x9af948`）、**1.5**（`0x9af9a8`）
* 立即数：`1`×23, `2`×8, `3`×17, `4`×7, `6`×1, `8`×1, `15`×9, `16`×27, `24`×9, `40`×1, `104`×6, `112`×1, `120`×14, `312`×5, `3080`×2
* 字段偏移（239 个）：`+0x1`、`+0x4`、`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x31`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x54`、`+0x58`、`+0x60`、`+0x64`、`+0x68`、`+0x6c`、`+0x70`、`+0x74`、`+0x78`、`+0x7c`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa7`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x140`、`+0x150`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x180`、`+0x188`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1c0`、`+0x1e0`、`+0x1e8`、`+0x200`、`+0x208`、`+0x210`、`+0x220`、`+0x228`、`+0x230`、`+0x240`、`+0x248`、`+0x250`、`+0x260`、`+0x268`、`+0x270`、`+0x280`、`+0x288`、`+0x2a0`、`+0x2a8`、`+0x2b0`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x300`、`+0x320`、`+0x328`、`+0x330`、`+0x338`、`+0x348`、`+0x350`、`+0x358`、`+0x360`、`+0x368`、`+0x370`、`+0x378`、`+0x388`、`+0x398`、`+0x3a0`、`+0x3a8`、`+0x3b0`、`+0x3b8`、`+0x3c0`、`+0x3d0`、`+0x3d8`、`+0x3e0`、`+0x3f0`、`+0x3f8`、`+0x400`、`+0x408`、`+0x410`、`+0x418`、`+0x420`、`+0x428`、`+0x440`、`+0x448`、`+0x450`、`+0x458`、`+0x460`、`+0x468`、`+0x46c`、`+0x470`、`+0x471`、`+0x474`、`+0x478`、`+0x480`、`+0x488`、`+0x490`、`+0x498`、`+0x4a0`、`+0x4a8`、`+0x4b0`、`+0x4b8`、`+0x4c0`、`+0x4c8`、`+0x4d0`、`+0x4d8`、`+0x4e0`、`+0x4e8`、`+0x4f0`、`+0x4f8`、`+0x500`、`+0x510`、`+0x518`、`+0x520`、`+0x530`、`+0x538`、`+0x540`、`+0x548`、`+0x550`、`+0x558`、`+0x560`、`+0x568`、`+0x588`、`+0x590`、`+0x598`、`+0x5a0`、`+0x5a8`、`+0x5ac`、`+0x5b0`、`+0x5b1`、`+0x5b4`、`+0x5b8`、`+0x5c0`、`+0x5c8`、`+0x5d0`、`+0x5d8`、`+0x5e0`、`+0x5e8`、`+0x5f0`、`+0x5f8`、`+0x600`、`+0x608`、`+0x610`、`+0x618`、`+0x620`、`+0x628`、`+0x630`、`+0x638`、`+0x640`、`+0x648`、`+0x650`、`+0x651`、`+0x658`、`+0x660`、`+0x668`、`+0x670`、`+0x678`、`+0x680`、`+0x688`、`+0x690`、`+0x698`、`+0x6a0`、`+0x6b0`、`+0x6b8`、`+0x6c0`、`+0x6d0`、`+0x6d8`、`+0x6e0`、`+0x6e8`、`+0x6f0`、`+0x6f8`、`+0x700`、`+0x708`、`+0x728`、`+0x730`、`+0x738`、`+0x740`、`+0x748`、`+0x74c`、`+0x750`、`+0x751`、`+0x754`、`+0x758`、`+0x760`、`+0x768`、`+0x770`、`+0x778`、`+0x780`、`+0x788`、`+0x790`、`+0x798`、`+0x7a0`、`+0x7a8`、`+0x7b0`、`+0x7b8`、`+0x7c0`、`+0x7c8`、`+0x7d0`、`+0x7d8`、`+0x7e0`、`+0x7e8`、`+0x7f0`、`+0x7f1`、`+0x7f8`

**尚未解**：图案（pattern）如何铺满板材、与 `packer_cache` 的 16 个图案键如何对接、以及它是否调用 `Packer::Run 0x770D10`。`strategy.tiling` 仍标 `Substituted`。

### 附 6.22 `0x344D0`（6,748 B，`NestingNester::Run` 的最大辅助）**[已证实 + 未解]**

* 函数：`0x344d0`，6748 字节 / **1440 条指令**
* 被调用者（33 个）：`0x5475a0`(95B，9 调用者)、`0x4fc5a0`(8B，114 调用者)、`0x998500`(109B，2318 调用者)、`0x63f2e8`(0B)、`0x51cdd0`(478B，22 调用者)、`0x525370`(107B，13 调用者)、`0x4f8f80`(7B，52 调用者)、`0x52f810`(7B，8 调用者)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x9984b0`(5B，5721 调用者)、`0xad5e0`(75B，8 调用者)、`0x4f8380`(6B，85 调用者)、`0x4f8370`(6B，74 调用者)、`0x4fc350`(12B)、`0x64380`(34B，7 调用者)、`0x3dbe0`(2033B，6 调用者)、`0x63f2f0`(0B)、`0x3bcc0`(1089B)、`0x40db0`(2917B)、`0x3b7b0`(8B)、`0x1aa5d0`(173B)、`0x40070`(1697B，7 调用者)、`0x92ecb0`(791B，180 调用者)、`0x4fc320`(11B，7 调用者)、`0x93c6e0`(590B，19 调用者)、`0x93bc20`(590B，24 调用者)、`0x910af0`(168B，345 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x62f280`(171B，5209 调用者)、`0x65bb20`(217B，23 调用者)、`0x775c00`(932B，108 调用者)、`0x979e70`(51B，676 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×26, `2`×11, `3`×2, `8`×3, `16`×11, `24`×7, `27`×2, `31`×1, `32`×9, `37`×2, `39`×1, `41`×1, `48`×4, `80`×2, `88`×1, `110`×2, `112`×2, `120`×2, `276`×1, `277`×1, `1304`×2, `10536`×1
* 字段偏移（131 个）：`+0x1`、`+0x4`、`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x1a`、`+0x1c`、`+0x1e`、`+0x20`、`+0x24`、`+0x26`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x150`、`+0x158`、`+0x160`、`+0x170`、`+0x188`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1f8`、`+0x228`、`+0x250`、`+0x258`、`+0x260`、`+0x270`、`+0x278`、`+0x280`、`+0x288`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2a8`、`+0x2c8`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2e8`、`+0x2ec`、`+0x2f0`、`+0x2f1`、`+0x2f4`、`+0x2f8`、`+0x300`、`+0x308`、`+0x310`、`+0x318`、`+0x320`、`+0x328`、`+0x330`、`+0x338`、`+0x340`、`+0x348`、`+0x350`、`+0x358`、`+0x360`、`+0x368`、`+0x370`、`+0x378`、`+0x380`、`+0x390`、`+0x398`、`+0x3a0`、`+0x3c0`、`+0x3c8`、`+0x3d8`、`+0x3e0`、`+0x3f0`、`+0x3f8`、`+0x410`、`+0x420`、`+0x428`、`+0x440`、`+0x448`、`+0x460`、`+0x478`、`+0x490`、`+0x4c8`、`+0x4f0`、`+0x500`、`+0x560`、`+0x568`、`+0x570`、`+0x578`、`+0x580`、`+0x588`、`+0x590`

**尚未解**：它在放置循环里的角色（候选生成？碰撞/合法性判定？）、与 `0x35F30` 的分工。**不给它编名字**。

### 附 6.23 `0x35F30`（6,436 B，`NestingNester::Run` 的第二大辅助）**[已证实 + 未解]**

* 函数：`0x35f30`，6436 字节 / **1569 条指令**
* 被调用者（26 个）：`0x3d610`(784B)、`0x5475a0`(95B，9 调用者)、`0x4fc5a0`(8B，114 调用者)、`0x998500`(109B，2318 调用者)、`0x63f2e8`(0B)、`0x1816a0`(2016B，39 调用者)、`0x16c450`(79B，19 调用者)、`0x63f2f0`(0B)、`0x3bcc0`(1089B)、`0x9984b0`(5B，5721 调用者)、`0x40db0`(2917B)、`0x3b7b0`(8B)、`0x1aa5d0`(173B)、`0x197090`(1418B)、`0x97a040`(5B，125 调用者)、`0x983ca0`(145B，289 调用者)、`0x8fdfa0`(437B，13 调用者)、`0x932420`(408B，36 调用者)、`0x4fc320`(11B，7 调用者)、`0x93c6e0`(590B，19 调用者)、`0x93bc20`(590B，24 调用者)、`0x40070`(1697B，7 调用者)、`0x62f280`(171B，5209 调用者)、`0x979e70`(51B，676 调用者)、`0x8b4ae0`(196B，30 调用者)、`0x6ac370`(694B，57 调用者)
* 字符串：`vector::_M_range_check: __n (which is %zu) >= this`
* 浮点常量：**1.5**（`0x9af148`）
* 立即数：`1`×42, `2`×11, `3`×5, `7`×1, `8`×6, `16`×1, `24`×9, `25`×1, `32`×16, `48`×8, `80`×2, `127`×1, `728`×1, `952`×2, `1024`×2
* 字段偏移（79 个）：`+0x1`、`+0x4`、`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x7f`、`+0x80`、`+0x90`、`+0x98`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xf0`、`+0xf8`、`+0x110`、`+0x118`、`+0x138`、`+0x158`、`+0x168`、`+0x190`、`+0x1a0`、`+0x1c0`、`+0x1c8`、`+0x1d8`、`+0x1e0`、`+0x1f0`、`+0x1f8`、`+0x210`、`+0x220`、`+0x230`、`+0x240`、`+0x260`、`+0x268`、`+0x278`、`+0x280`、`+0x290`、`+0x298`、`+0x2b0`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x300`、`+0x318`、`+0x330`、`+0x348`、`+0x350`、`+0x358`、`+0x360`、`+0x368`、`+0x370`、`+0x378`、`+0x380`、`+0x390`、`+0x3a0`、`+0x400`、`+0x408`、`+0x410`、`+0x418`、`+0x420`、`+0x428`、`+0x430`

**尚未解**：同上；两者谁是

### 附 6.24 `0x693950`（4,157 B，`TilingNester::Run` 的最大辅助）**[已证实 + 未解]**

* 函数：`0x693950`，4157 字节 / **770 条指令**
* 被调用者（37 个）：`0x50bd0`(137B，8 调用者)、`0x51cc90`(312B，17 调用者)、`0x2fdd0`(129B，6 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x2fe60`(129B，6 调用者)、`0x6c0e0`(5B，19 调用者)、`0x455c0`(177B，6 调用者)、`0x998500`(109B，2318 调用者)、`0x63f2f0`(0B)、`0x6c470`(852B，7 调用者)、`0x4fc2e0`(14B，52 调用者)、`0x4efbf0`(127B)、`0x4f8f80`(7B，52 调用者)、`0x52f840`(10B)、`0x52f820`(7B)、`0x30250`(11B，25 调用者)、`0x1565c0`(73B)、`0x9984b0`(5B，5721 调用者)、`0x92ecb0`(791B，180 调用者)、`0x51d0a0`(31B，17 调用者)、`0x5203d0`(19B，45 调用者)、`0x520410`(16B，12 调用者)、`0x4fc260`(11B，25 调用者)、`0x51d090`(4B，53 调用者)、`0x997950`(1532B)、`0x51d0c0`(5B，103 调用者)、`0x4fc3d0`(10B，28 调用者)、`0x4f1f60`(2299B)、`0x60a620`(2620B，680 调用者)、`0x4f8370`(6B，74 调用者)、`0x4f8380`(6B，85 调用者)、`0x910af0`(168B，345 调用者)、`0x697150`(221B，11 调用者)、`0x62f280`(171B，5209 调用者)、`0x891b40`(52B，240 调用者)、`0x679010`(54B，60 调用者)、`0x979e70`(51B，676 调用者)
* 字符串：`sheet`、`GetPackerParameters`、`..\multi\tiling_nester.cpp`
* 浮点常量：**0.5**（`0x9af928`）、**1**（`0x9af948`）、**0.5**（`0x9af928`）
* 立即数：`1`×15, `3`×3, `16`×10, `32`×1, `120`×2, `369`×1, `1208`×2
* 字段偏移（137 个）：`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x32`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x5f`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x94`、`+0xa0`、`+0xc0`、`+0xd0`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x110`、`+0x118`、`+0x120`、`+0x130`、`+0x138`、`+0x140`、`+0x150`、`+0x158`、`+0x160`、`+0x170`、`+0x178`、`+0x180`、`+0x190`、`+0x191`、`+0x1a0`、`+0x1a4`、`+0x1ac`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1e0`、`+0x1e8`、`+0x1f0`、`+0x200`、`+0x208`、`+0x210`、`+0x218`、`+0x220`、`+0x228`、`+0x230`、`+0x238`、`+0x258`、`+0x260`、`+0x268`、`+0x270`、`+0x278`、`+0x27c`、`+0x280`、`+0x281`、`+0x284`、`+0x288`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2a8`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x2f8`、`+0x300`、`+0x308`、`+0x310`、`+0x320`、`+0x328`、`+0x330`、`+0x331`、`+0x340`、`+0x348`、`+0x350`、`+0x358`、`+0x360`、`+0x368`、`+0x370`、`+0x378`、`+0x398`、`+0x3a0`、`+0x3a8`、`+0x3b0`、`+0x3b8`、`+0x3bc`、`+0x3c0`、`+0x3c1`、`+0x3c4`、`+0x3c8`、`+0x3d0`、`+0x3d8`、`+0x3e0`、`+0x3e8`、`+0x3f0`、`+0x3f8`、`+0x400`、`+0x408`、`+0x410`、`+0x418`、`+0x420`、`+0x428`、`+0x430`、`+0x438`、`+0x440`、`+0x448`、`+0x450`、`+0x460`、`+0x470`、`+0x480`、`+0x490`、`+0x4a0`、`+0x500`、`+0x510`、`+0x520`、`+0x528`、`+0x530`、`+0x538`、`+0x540`

**尚未解**：它与 `packer_cache` 的 16 个图案键如何对接。**不给它编名字**。

### 附 6.25 由辅助函数反推出的两条结构事实 **[已证实]**

* `0x344D0`（6,748 B，`NestingNester::Run` 的最大辅助）**没有任何字符串、没有浮点常量**，但它调用
  **`0x3DBE0`(ToNesting)**、**`0x40070`(ComputeGroups)**、**`0x3BCC0`(NestedQuantities)** ——
  这三个正是 round 6 里在 `..\multi\nesting_context.cpp` 识别出的 API。
  ⇒ **`0x344D0` 是"排样器 ↔ 排样上下文"的粘合层**（把结果写回上下文、算分组、算已排数量）。
* `0x693950`（4,157 B，`TilingNester::Run` 的最大辅助）自带字符串
  **`'..\multi\tiling_nester.cpp'`、`'GetPackerParameters'`、`'sheet'`**
  ⇒ **新 TU：`..\multi\tiling_nester.cpp`**，且其中存在 **`GetPackerParameters`** 取件入口。
  常量 `0.5`、`1.0`。

### 附 6.26 当前最大的未识别领域函数 `0x7e1480` **[已证实 + 未解]**

* 函数：`0x7e1480`，17034 字节 / **3386 条指令**
* 被调用者（9 个）：`0x63f2f8`(0B)、`0x6e6120`(8168B，18 调用者)、`0x9984b0`(5B，5721 调用者)、`0x998500`(109B，2318 调用者)、`0x63f300`(0B)、`0x63f2f0`(0B)、`0x6e4750`(25B，26 调用者)、`0x998390`(79B)、`0x62f280`(171B，5209 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×167, `2`×41, `3`×66, `8`×32, `32`×2, `64`×12, `96`×8, `920`×2
* 字段偏移（130 个）：`+0x1`、`+0x8`、`+0x10`、`+0x14`、`+0x15`、`+0x20`、`+0x28`、`+0x30`、`+0x34`、`+0x35`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x180`、`+0x188`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c8`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1e8`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x204`、`+0x205`、`+0x210`、`+0x218`、`+0x220`、`+0x224`、`+0x225`、`+0x230`、`+0x238`、`+0x240`、`+0x244`、`+0x245`、`+0x250`、`+0x258`、`+0x260`、`+0x264`、`+0x265`、`+0x270`、`+0x278`、`+0x280`、`+0x284`、`+0x285`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2a4`、`+0x2a5`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2c4`、`+0x2c5`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2e4`、`+0x2e5`、`+0x2f0`、`+0x2f8`、`+0x300`、`+0x304`、`+0x305`、`+0x310`、`+0x318`、`+0x320`、`+0x324`、`+0x325`、`+0x330`、`+0x338`、`+0x340`、`+0x344`、`+0x345`、`+0x350`、`+0x358`、`+0x360`、`+0x364`、`+0x365`、`+0x370`、`+0x378`、`+0x380`、`+0x384`、`+0x385`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.27 `0x68F750`（15,812 B，带具名断言）**[已证实 + 未解]**

* 函数：`0x68f750`，15812 字节 / **3128 条指令**
* 被调用者（55 个）：`0x3b7c0`(66B)、`0x998500`(109B，2318 调用者)、`0x63f2f0`(0B)、`0x51d090`(4B，53 调用者)、`0xaaa60`(177B，7 调用者)、`0x60a620`(2620B，680 调用者)、`0x9984b0`(5B，5721 调用者)、`0x5235f0`(54B，28 调用者)、`0x4fc5a0`(8B，114 调用者)、`0x4d3ee0`(12B，11 调用者)、`0x8cef00`(254B)、`0xab240`(732B)、`0x96e2d0`(266B)、`0x51cff0`(159B，21 调用者)、`0x51cab0`(478B，18 调用者)、`0x51d310`(5B，20 调用者)、`0x51fde0`(30B，18 调用者)、`0x51d0c0`(5B，103 调用者)、`0x520440`(479B，56 调用者)、`0x4f76a0`(4B，57 调用者)、`0x51f470`(549B，20 调用者)、`0x51e7e0`(1294B，47 调用者)、`0x5228e0`(54B)、`0x5f3900`(22B，58 调用者)、`0x64330`(28B，21 调用者)、`0x430e0`(147B，7 调用者)、`0x5f3980`(10B，44 调用者)、`0x5f3960`(17B，77 调用者)、`0x7c1430`(2235B，33 调用者)、`0x693520`(634B)、`0x910ba0`(109B，1002 调用者)、`0x97a830`(75B，571 调用者)、`0x92dee0`(1148B，49 调用者)、`0x520620`(4B)、`0x60cb0`(51B)、`0x267020`(8B)、`0x92ecb0`(791B，180 调用者)、`0x910af0`(168B，345 调用者)、`0x8e6400`(1770B，29 调用者)、`0x8ea9d0`(335B，25 调用者)、`0x92e360`(2378B，22 调用者)、`0x8e1fb0`(744B，27 调用者)、`0x8ea720`(423B，25 调用者)、`0x8e7af0`(338B，21 调用者)、`0x63f2f8`(0B)、`0x8e5ce0`(815B，17 调用者)、`0x9989a0`(125B，837 调用者)、`0x7bb7a0`(54B，56 调用者)、`0x998fe0`(79B，783 调用者)、`0x8e6390`(107B，48 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x62f280`(171B，5209 调用者)、`0x979e70`(51B，676 调用者)、`0x998bc0`(124B，833 调用者)、`0x63f2e8`(0B)
* 字符串：`nesting.multiplicity() == 1u`、`GetCandidates`、`..\multi\float_filler.cpp`、`part_number < m_reduced_problem.GetNumberOfParts()`、`RawFillNesting`、`..\multi\float_filler.cpp`、`nested_part.part()`、`RemoveNullPricesParts`
* 浮点常量：无
* 立即数：`1`×20, `2`×4, `3`×11, `4`×6, `15`×1, `16`×58, `17`×1, `18`×2, `20`×1, `24`×10, `25`×2, `63`×2, `93`×2, `104`×7, `112`×7, `115`×1, `120`×20, `126`×1, `140`×1, `174`×2, `265`×1, `407`×1, `3048`×2, `10536`×2
* 字段偏移（162 个）：`+0x1`、`+0x4`、`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x24`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x54`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa8`、`+0xac`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x149`、`+0x150`、`+0x158`、`+0x160`、`+0x170`、`+0x178`、`+0x180`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1b0`、`+0x1d0`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x210`、`+0x218`、`+0x220`、`+0x230`、`+0x250`、`+0x270`、`+0x290`、`+0x2b0`、`+0x2d0`、`+0x2f0`、`+0x310`、`+0x330`、`+0x350`、`+0x370`、`+0x37a`、`+0x390`、`+0x398`、`+0x3a0`、`+0x3b0`、`+0x3c0`、`+0x3c8`、`+0x3d0`、`+0x3d4`、`+0x3d8`、`+0x3e0`、`+0x3f0`、`+0x3f8`、`+0x400`、`+0x410`、`+0x418`、`+0x420`、`+0x430`、`+0x438`、`+0x440`、`+0x450`、`+0x458`、`+0x460`、`+0x470`、`+0x478`、`+0x480`、`+0x490`、`+0x4b0`、`+0x4d0`、`+0x4f0`、`+0x510`、`+0x530`、`+0x538`、`+0x540`、`+0x548`、`+0x550`、`+0x558`、`+0x560`、`+0x564`、`+0x568`、`+0x590`、`+0x598`、`+0x5a0`、`+0x5b0`、`+0x5b8`、`+0x5c0`、`+0x5c8`、`+0x5d0`、`+0x5d8`、`+0x5e0`、`+0x5e8`、`+0x608`、`+0x610`、`+0x618`、`+0x620`、`+0x628`、`+0x62c`、`+0x630`、`+0x631`、`+0x634`、`+0x638`、`+0x640`、`+0x648`、`+0x650`、`+0x658`、`+0x660`、`+0x668`、`+0x670`、`+0x678`、`+0x680`、`+0x688`、`+0x690`、`+0x698`、`+0x6a0`、`+0x6a8`、`+0x6b0`、`+0x6b8`、`+0x6c0`、`+0x6d0`、`+0x6f8`、`+0x700`、`+0x710`、`+0x748`、`+0x788`、`+0x7d0`、`+0x7f0`

**已读出的结构线索**：断言串 `'part_number < m_reduced_problem.GetNumberOfParts()'` 表明存在一个 **reduced problem**（与 tu.equivalent 的等价化简同族），并按零件号索引。**尚未解**：reduced problem 的构造者、它与等价问题的关系。**不给它编名字**。

### 附 6.28 ``0x6E6120``（8,168 B，``0x7E1480`` 的唯一大被调用者） **[已证实 + 未解]**

* 函数：`0x6e6120`，8168 字节 / **1792 条指令**
* 被调用者（15 个）：`0x6e50a0`(4219B)、`0x998500`(109B，2318 调用者)、`0x63f2f8`(0B)、`0x9984b0`(5B，5721 调用者)、`0x6e6120`(8168B，18 调用者)、`0x58b770`(209B)、`0x62ec20`(330B)、`0x6e3880`(274B，6 调用者)、`0x6e4aa0`(1528B，6 调用者)、`0x6e4770`(806B)、`0x6e32d0`(1452B，6 调用者)、`0x63f2f0`(0B)、`0x62ed70`(341B)、`0x6e2ea0`(1067B)、`0x62f280`(171B，5209 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×49, `2`×25, `3`×38, `8`×14, `392`×2
* 字段偏移（52 个）：`+0x1`、`+0x8`、`+0x10`、`+0x14`、`+0x15`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x76`、`+0x77`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x170`、`+0x174`、`+0x175`、`+0x1e0`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.29 ``0x5AC040``（15,111 B） **[已证实 + 未解]**

* 函数：`0x5ac040`，15111 字节 / **2761 条指令**
* 被调用者（29 个）：`0x6ac630`(246B)、`0x592330`(72B，10 调用者)、`0x6b8910`(288B)、`0x592380`(240B，6 调用者)、`0x58b850`(2150B)、`0x63f2f8`(0B)、`0x9984b0`(5B，5721 调用者)、`0x5a9c90`(2739B)、`0x966dc0`(2150B)、`0x5a6480`(71B，10 调用者)、`0x5a6580`(114B，18 调用者)、`0x592520`(328B)、`0x592870`(8756B)、`0x96dcf0`(1494B)、`0x5a6be0`(3840B)、`0x8c8610`(866B)、`0x5ab5c0`(2678B)、`0x8ce990`(291B，7 调用者)、`0x684b00`(82B，34 调用者)、`0x998500`(109B，2318 调用者)、`0x6ac730`(1407B)、`0x6e4750`(25B，26 调用者)、`0x9989a0`(125B，837 调用者)、`0x998fe0`(79B，783 调用者)、`0x8c8980`(138B)、`0x8c9c30`(232B，8 调用者)、`0x62f280`(171B，5209 调用者)、`0x998bc0`(124B，833 调用者)、`0x979e70`(51B，676 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×60, `2`×13, `3`×76, `5`×4, `8`×8, `32`×7, `63`×4, `112`×2, `160`×22, `352`×4, `1544`×2, `2672`×1, `2688`×1, `2719`×2
* 字段偏移（236 个）：`+0x8`、`+0x10`、`+0x14`、`+0x15`、`+0x18`、`+0x20`、`+0x24`、`+0x28`、`+0x30`、`+0x34`、`+0x35`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x64`、`+0x65`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x84`、`+0x85`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb4`、`+0xb5`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd4`、`+0xd5`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x104`、`+0x105`、`+0x110`、`+0x118`、`+0x120`、`+0x124`、`+0x125`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x158`、`+0x160`、`+0x170`、`+0x178`、`+0x180`、`+0x188`、`+0x190`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b4`、`+0x1b5`、`+0x1c0`、`+0x1c8`、`+0x1d0`、`+0x1d4`、`+0x1d5`、`+0x1d8`、`+0x1e0`、`+0x1e8`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x204`、`+0x205`、`+0x210`、`+0x218`、`+0x220`、`+0x224`、`+0x225`、`+0x230`、`+0x238`、`+0x240`、`+0x248`、`+0x250`、`+0x254`、`+0x255`、`+0x260`、`+0x268`、`+0x270`、`+0x274`、`+0x275`、`+0x280`、`+0x288`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2a4`、`+0x2a5`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2c4`、`+0x2c5`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x2f4`、`+0x2f5`、`+0x300`、`+0x308`、`+0x310`、`+0x314`、`+0x315`、`+0x320`、`+0x328`、`+0x330`、`+0x338`、`+0x340`、`+0x344`、`+0x345`、`+0x350`、`+0x358`、`+0x360`、`+0x364`、`+0x365`、`+0x370`、`+0x378`、`+0x380`、`+0x388`、`+0x390`、`+0x394`、`+0x395`、`+0x3a0`、`+0x3a8`、`+0x3b0`、`+0x3b4`、`+0x3b5`、`+0x3c0`、`+0x3c8`、`+0x3d0`、`+0x3d8`、`+0x3e0`、`+0x3e4`、`+0x3e5`、`+0x3f0`、`+0x3f8`、`+0x400`、`+0x404`、`+0x405`、`+0x410`、`+0x418`、`+0x420`、`+0x428`、`+0x430`、`+0x434`、`+0x435`、`+0x440`、`+0x448`、`+0x450`、`+0x454`、`+0x455`、`+0x460`、`+0x468`、`+0x470`、`+0x478`、`+0x480`、`+0x484`、`+0x485`、`+0x490`、`+0x498`、`+0x4a0`、`+0x4a4`、`+0x4a5`、`+0x4b0`、`+0x4b8`、`+0x4c0`、`+0x4c8`、`+0x4d0`、`+0x4d4`、`+0x4d5`、`+0x4e0`、`+0x4e8`、`+0x4f0`、`+0x4f4`、`+0x4f5`、`+0x500`、`+0x508`、`+0x510`、`+0x518`、`+0x520`、`+0x524`、`+0x525`、`+0x530`、`+0x538`、`+0x540`、`+0x544`、`+0x545`、`+0x550`、`+0x558`、`+0x560`、`+0x568`、`+0x570`、`+0x574`、`+0x575`、`+0x578`、`+0x580`、`+0x588`、`+0x590`、`+0x594`、`+0x595`、`+0x5a0`、`+0x5a8`、`+0x5b0`、`+0x5b8`、`+0x5c0`、`+0x5c4`、`+0x5c5`、`+0x5d0`、`+0x5d8`、`+0x5e0`、`+0x5e4`、`+0x5e5`、`+0x5f0`、`+0x5f8`、`+0x650`、`+0x660`、`+0x668`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.30 ``0x5BA600``（14,064 B） **[已证实 + 未解]**

* 函数：`0x5ba600`，14064 字节 / **2885 条指令**
* 被调用者（29 个）：`0x973180`(1807B)、`0x96b3b0`(900B)、`0x5b9d80`(888B)、`0x5a64d0`(81B)、`0x5b2a70`(556B)、`0x9984b0`(5B，5721 调用者)、`0x6bac60`(92B)、`0x5b3bf0`(546B)、`0x6ba000`(456B)、`0x6ba980`(186B)、`0x6ba1d0`(1773B)、`0x6b9900`(976B)、`0x684b00`(82B，34 调用者)、`0x9615a0`(1388B)、`0x6b9cd0`(292B)、`0x998500`(109B，2318 调用者)、`0x6baa40`(532B)、`0x63f2f8`(0B)、`0x8f4900`(220B，6 调用者)、`0x6874f0`(558B)、`0x6accb0`(2253B)、`0x62f280`(171B，5209 调用者)、`0x6849f0`(270B，7 调用者)、`0x6e4750`(25B，26 调用者)、`0x7d1070`(105B)、`0x5a6580`(114B，18 调用者)、`0x5b34b0`(74B)、`0x6ba8c0`(178B)、`0x6b9e00`(501B)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×56, `2`×26, `3`×72, `5`×1, `8`×29, `30`×2, `48`×1, `63`×6, `135`×1, `264`×2, `288`×2, `384`×8
* 字段偏移（84 个）：`+0x1`、`+0x4`、`+0x5`、`+0x8`、`+0xc`、`+0x10`、`+0x20`、`+0x28`、`+0x30`、`+0x34`、`+0x35`、`+0x38`、`+0x40`、`+0x44`、`+0x45`、`+0x48`、`+0x50`、`+0x54`、`+0x55`、`+0x58`、`+0x60`、`+0x64`、`+0x65`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x84`、`+0x85`、`+0x88`、`+0x90`、`+0x94`、`+0x95`、`+0x98`、`+0xa0`、`+0xa4`、`+0xa5`、`+0xa8`、`+0xb0`、`+0xb4`、`+0xb5`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd4`、`+0xd5`、`+0xd8`、`+0xe0`、`+0xe4`、`+0xe5`、`+0xe8`、`+0xf0`、`+0xf4`、`+0xf5`、`+0xf8`、`+0x100`、`+0x104`、`+0x105`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x124`、`+0x125`、`+0x128`、`+0x130`、`+0x134`、`+0x135`、`+0x138`、`+0x140`、`+0x144`、`+0x145`、`+0x148`、`+0x150`、`+0x154`、`+0x155`、`+0x158`、`+0x160`、`+0x164`、`+0x168`、`+0x170`、`+0x660`、`+0x668`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.31 ``0x6B4160``（13,438 B） **[已证实 + 未解]**

* 函数：`0x6b4160`，13438 字节 / **3034 条指令**
* 被调用者（7 个）：`0x998500`(109B，2318 调用者)、`0x962020`(1285B)、`0x6bee90`(1994B)、`0x5c8c50`(255B，57 调用者)、`0x9984b0`(5B，5721 调用者)、`0x62f280`(171B，5209 调用者)、`0x979e70`(51B，676 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×177, `2`×12, `3`×24, `4`×45, `48`×3, `56`×12, `63`×42, `120`×42, `168`×3
* 字段偏移（21 个）：`+0x1`、`+0x3`、`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x34`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x5c`、`+0x60`、`+0x64`、`+0x68`、`+0x70`、`+0x80`、`+0x90`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.32 ``0x501B60``（13,199 B） **[已证实 + 未解]**

* 函数：`0x501b60`，13199 字节 / **2762 条指令**
* 被调用者（38 个）：`0x998500`(109B，2318 调用者)、`0x54ce60`(5B，43 调用者)、`0x92dee0`(1148B，49 调用者)、`0x97a830`(75B，571 调用者)、`0x9989a0`(125B，837 调用者)、`0x9984b0`(5B，5721 调用者)、`0x998fe0`(79B，783 调用者)、`0x63f6c8`(0B)、`0x92ad10`(528B)、`0x910ba0`(109B，1002 调用者)、`0x63f2f8`(0B)、`0x92b340`(605B，7 调用者)、`0x531f20`(71B)、`0x8f8c20`(137B)、`0x8ec9e0`(137B，9 调用者)、`0x63f6d0`(0B)、`0x92ecb0`(791B，180 调用者)、`0x92b940`(597B)、`0x92bba0`(687B)、`0x62f280`(171B，5209 调用者)、`0x67fe90`(104B，155 调用者)、`0x4fdfe0`(6439B)、`0x979e70`(51B，676 调用者)、`0x998bc0`(124B，833 调用者)、`0x4fbd80`(177B，14 调用者)、`0x60a620`(2620B，680 调用者)、`0x7c0c90`(608B，6 调用者)、`0x8c5090`(147B，133 调用者)、`0x903ce0`(197B)、`0x8bf8c0`(196B，15 调用者)、`0x9296d0`(2241B，7 调用者)、`0x63f2f0`(0B)、`0x500a90`(3003B)、`0x929fa0`(1495B，24 调用者)、`0x7c0ef0`(414B，7 调用者)、`0x7c0a80`(520B)、`0x8ebec0`(475B)、`0x8e87e0`(89B，16 调用者)
* 字符串：`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`sheet`、`Implementation`、`..\structure\problem.cpp`、`basic_string::_M_construct null not valid`、`part`、`Implementation`
* 浮点常量：无
* 立即数：`1`×5, `2`×2, `3`×12, `4`×19, `5`×1, `8`×6, `15`×4, `16`×55, `24`×35, `32`×4, `48`×21, `80`×3, `98`×1, `103`×1, `216`×4, `968`×2
* 字段偏移（133 个）：`+0x4`、`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x64`、`+0x68`、`+0x6c`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa4`、`+0xa8`、`+0xa9`、`+0xaa`、`+0xac`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe4`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x180`、`+0x188`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c8`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1e8`、`+0x1e9`、`+0x1f0`、`+0x1f4`、`+0x1f8`、`+0x1fc`、`+0x200`、`+0x208`、`+0x210`、`+0x218`、`+0x220`、`+0x228`、`+0x230`、`+0x238`、`+0x239`、`+0x23a`、`+0x23c`、`+0x240`、`+0x248`、`+0x250`、`+0x258`、`+0x260`、`+0x268`、`+0x270`、`+0x278`、`+0x280`、`+0x288`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2a8`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2e4`、`+0x2e8`、`+0x2f0`、`+0x2f8`、`+0x300`、`+0x308`、`+0x310`、`+0x318`、`+0x320`、`+0x324`、`+0x328`、`+0x330`、`+0x338`、`+0x340`、`+0x348`、`+0x350`、`+0x358`、`+0x360`、`+0x368`、`+0x370`、`+0x378`、`+0x380`、`+0x388`、`+0x390`、`+0x398`、`+0x3a0`、`+0x3b0`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.33 ``0x631890``（12,852 B） **[已证实 + 未解]**

* 函数：`0x631890`，12852 字节 / **2860 条指令**
* 被调用者（24 个）：`0x63f320`(0B)、`0x63f340`(0B)、`0x631790`(151B)、`0x631830`(91B)、`0x6316d0`(141B)、`0x63f4d8`(0B)、`0x63f310`(0B)、`0x631760`(35B)、`0x630110`(104B)、`0x63f1f0`(0B)、`0x63f238`(0B)、`0x630280`(90B)、`0x63f2a8`(0B)、`0x631640`(141B)、`0x639470`(594B)、`0x63f328`(0B)、`0x631580`(48B)、`0x637b90`(318B)、`0x63f390`(0B)、`0x63f208`(0B)、`0x6315b0`(135B)、`0x62f890`(164B)、`0x6396d0`(519B)、`0x63f200`(0B)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×109, `2`×14, `4`×9, `8`×31, `9`×8, `10`×4, `12`×5, `16`×8, `22`×1, `31`×6, `32`×3, `36`×1, `37`×2, `39`×1, `40`×1, `42`×2, `43`×3, `44`×1, `45`×5, `48`×9, `50`×1, `51`×1, `52`×1, `54`×1, `64`×4, `73`×1, `76`×1, `83`×2, `88`×1, `93`×3, `94`×2, `97`×1, `99`×1, `100`×6, `101`×3, `104`×2, `105`×3, `106`×1, `108`×3, `109`×1, `110`×3, `112`×2, `113`×1, `115`×2, `116`×1, `120`×3, `122`×1, `128`×16, `200`×2, `253`×1, `255`×1, `256`×5, `328`×2, `512`×1, `1024`×10, `1028`×1, `1536`×11
* 字段偏移（42 个）：`+0x1`、`+0x2`、`+0x3`、`+0x8`、`+0x10`、`+0x28`、`+0x30`、`+0x38`、`+0x3c`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb4`、`+0xb8`、`+0xc0`、`+0xc4`、`+0xc8`、`+0xd0`、`+0xe8`、`+0xec`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x130`、`+0x190`、`+0x1a0`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.34 ``0x5B48D0``（12,545 B） **[已证实 + 未解]**

* 函数：`0x5b48d0`，12545 字节 / **2401 条指令**
* 被调用者（14 个）：`0x998500`(109B，2318 调用者)、`0x63f2f8`(0B)、`0x9984b0`(5B，5721 调用者)、`0x5a6600`(72B，6 调用者)、`0x62f940`(215B，47 调用者)、`0x853d50`(317B)、`0x943290`(247B)、`0x86c530`(291B)、`0x6e4750`(25B，26 调用者)、`0x684b00`(82B，34 调用者)、`0x9989a0`(125B，837 调用者)、`0x998fe0`(79B，783 调用者)、`0x62f280`(171B，5209 调用者)、`0x998bc0`(124B，833 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×64, `2`×36, `3`×94, `4`×2, `5`×2, `7`×2, `8`×25, `16`×6, `96`×1, `160`×2, `192`×4, `240`×2, `272`×4, `352`×2, `384`×6, `568`×2
* 字段偏移（91 个）：`+0x1`、`+0x8`、`+0x10`、`+0x14`、`+0x15`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x34`、`+0x35`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x64`、`+0x65`、`+0x68`、`+0x70`、`+0x74`、`+0x78`、`+0x80`、`+0x84`、`+0x85`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb4`、`+0xb5`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd4`、`+0xd5`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x104`、`+0x105`、`+0x110`、`+0x118`、`+0x120`、`+0x124`、`+0x125`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x154`、`+0x155`、`+0x158`、`+0x160`、`+0x164`、`+0x168`、`+0x170`、`+0x174`、`+0x175`、`+0x178`、`+0x180`、`+0x188`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1a4`、`+0x1a5`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c4`、`+0x1c5`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1e8`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x204`、`+0x208`、`+0x210`、`+0x218`、`+0x220`、`+0x280`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.35 ``0x6D7250``（12,157 B） **[已证实 + 未解]**

* 函数：`0x6d7250`，12157 字节 / **2552 条指令**
* 被调用者（12 个）：`0x998500`(109B，2318 调用者)、`0x960640`(1059B)、`0x8c8330`(280B)、`0x6d19f0`(1348B)、`0x6d1130`(2237B)、`0x8c7df0`(410B，11 调用者)、`0x6d1f40`(2614B)、`0x8c7880`(1390B)、`0x9984b0`(5B，5721 调用者)、`0x6ca5e0`(309B)、`0x62f280`(171B，5209 调用者)、`0x979e70`(51B，676 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×9, `3`×44, `24`×8, `56`×59, `63`×16, `1000`×2
* 字段偏移（127 个）：`+0x8`、`+0x10`、`+0x18`、`+0x1c`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xbf`、`+0xc0`、`+0xc1`、`+0xc2`、`+0xc3`、`+0xc4`、`+0xc5`、`+0xc6`、`+0xc7`、`+0xc8`、`+0xc9`、`+0xca`、`+0xcb`、`+0xcc`、`+0xcd`、`+0xce`、`+0xcf`、`+0xd0`、`+0xd1`、`+0xd2`、`+0xd3`、`+0xd4`、`+0xd5`、`+0xd6`、`+0xd7`、`+0xd8`、`+0xd9`、`+0xda`、`+0xdb`、`+0xdc`、`+0xdd`、`+0xde`、`+0xdf`、`+0xe0`、`+0xe8`、`+0xf0`、`+0x100`、`+0x108`、`+0x110`、`+0x120`、`+0x128`、`+0x130`、`+0x140`、`+0x148`、`+0x150`、`+0x160`、`+0x168`、`+0x170`、`+0x180`、`+0x188`、`+0x190`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1c0`、`+0x1c8`、`+0x1d0`、`+0x1e0`、`+0x1e8`、`+0x1f0`、`+0x200`、`+0x208`、`+0x210`、`+0x220`、`+0x228`、`+0x230`、`+0x240`、`+0x248`、`+0x250`、`+0x260`、`+0x268`、`+0x270`、`+0x280`、`+0x288`、`+0x290`、`+0x2a0`、`+0x2a8`、`+0x2b0`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x300`、`+0x308`、`+0x310`、`+0x320`、`+0x328`、`+0x330`、`+0x340`、`+0x348`、`+0x350`、`+0x360`、`+0x368`、`+0x370`、`+0x380`、`+0x388`、`+0x390`、`+0x3a0`、`+0x3a8`、`+0x3b0`、`+0x3c0`、`+0x3c8`、`+0x3d0`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.36 `0x255390` **[已证实 + 未解]**

* 函数：`0x255390`，12065 字节 / **2751 条指令**
* 被调用者（21 个）：`0x909bd0`(306B)、`0x255110`(629B)、`0x96d580`(346B)、`0x9984b0`(5B，5721 调用者)、`0x62f280`(171B，5209 调用者)、`0x6c3a40`(2191B)、`0x6c4590`(1839B)、`0x6b7b60`(1407B)、`0x6c0350`(1056B)、`0x6c0770`(2126B)、`0x998500`(109B，2318 调用者)、`0x906430`(305B)、`0x962530`(437B)、`0x6c0fc0`(9141B)、`0x6c42d0`(691B)、`0x6c3380`(219B)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x6c3460`(1494B)、`0x5c8eb0`(122B，41 调用者)、`0x906030`(260B)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×72, `2`×1, `3`×12, `4`×2, `5`×3, `16`×5, `20`×1, `24`×23, `27`×1, `31`×2, `56`×3, `63`×14, `72`×14, `112`×1, `159`×1, `184`×1, `407`×1, `520`×2
* 字段偏移（61 个）：`+0x1`、`+0x4`、`+0x5`、`+0x8`、`+0x10`、`+0x18`、`+0x1a`、`+0x1c`、`+0x20`、`+0x28`、`+0x30`、`+0x34`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x81`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xe0`、`+0xe8`、`+0xf0`、`+0x100`、`+0x108`、`+0x110`、`+0x120`、`+0x128`、`+0x130`、`+0x140`、`+0x148`、`+0x150`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x180`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1a2`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1d0`、`+0x1e0`、`+0x1f0`、`+0x250`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.37 `0x88380` **[已证实 + 未解]**

* 函数：`0x88380`，12013 字节 / **2948 条指令**
* 被调用者（16 个）：`0x5c8eb0`(122B，41 调用者)、`0x85940`(2072B)、`0x5c8ff0`(161B)、`0x62fe20`(270B，90 调用者)、`0x85210`(1839B)、`0x9984b0`(5B，5721 调用者)、`0x62f280`(171B，5209 调用者)、`0x87a80`(2298B)、`0x5c8c50`(255B，57 调用者)、`0x876a0`(983B)、`0x84b80`(1672B)、`0x998500`(109B，2318 调用者)、`0x8c32b0`(256B，21 调用者)、`0x8ea8d0`(256B)、`0x84880`(555B)、`0x63f2f0`(0B)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×29, `2`×1, `4`×8, `5`×3, `15`×1, `16`×29, `24`×4, `31`×2, `63`×4, `72`×1, `88`×4, `328`×2
* 字段偏移（39 个）：`+0x1`、`+0x4`、`+0x5`、`+0x8`、`+0x10`、`+0x14`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x44`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x9f`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x110`、`+0x120`、`+0x130`、`+0x190`、`+0x1a0`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.38 `0x6b1560` **[已证实 + 未解]**

* 函数：`0x6b1560`，11250 字节 / **2767 条指令**
* 被调用者（6 个）：`0x998500`(109B，2318 调用者)、`0x960d60`(412B)、`0x6bdbd0`(1651B)、`0x9984b0`(5B，5721 调用者)、`0x62f280`(171B，5209 调用者)、`0x979e70`(51B，676 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×179, `5`×43, `32`×3, `63`×42, `80`×42, `120`×3
* 字段偏移（16 个）：`+0x1`、`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x24`、`+0x28`、`+0x30`、`+0x38`、`+0x3c`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.39 `0x12f460` **[已证实 + 未解]**

* 函数：`0x12f460`，10885 字节 / **2263 条指令**
* 被调用者（33 个）：`0x62ebe0`(0B)、`0x998500`(109B，2318 调用者)、`0x60f570`(98B，124 调用者)、`0x63f238`(0B)、`0x12da10`(177B)、`0x861a30`(74B，105 调用者)、`0x63f2e8`(0B)、`0x8a8160`(41B，6 调用者)、`0x6f4430`(362B，10 调用者)、`0x6f3500`(1118B)、`0x6f3020`(929B)、`0x9984b0`(5B，5721 调用者)、`0x6f4670`(508B)、`0x6f0ea0`(98B，22 调用者)、`0x6f0e30`(105B，7 调用者)、`0x942fb0`(43B，8 调用者)、`0x6eff10`(345B，11 调用者)、`0x6f8630`(121B，17 调用者)、`0x6efae0`(41B)、`0x6f4000`(23B)、`0x62f280`(171B，5209 调用者)、`0x6ea7e0`(141B，7 调用者)、`0x990e80`(20B，61 调用者)、`0x6f4650`(21B)、`0x99b1d2`(193B)、`0x9989a0`(125B，837 调用者)、`0x998bc0`(124B，833 调用者)、`0x891b80`(23B，23 调用者)、`0x891b40`(52B，240 调用者)、`0x6eb860`(126B)、`0x6eb180`(1677B)、`0x998fe0`(79B，783 调用者)、`0x99b170`(98B)
* 字符串：`UWVSH`、`UWVSH`、`ntp`、`AWAVAUATUWVSH`、`AWAVAUATUWVSH`、`0a\`、`Pb\`、`p`\`
* 浮点常量：无
* 立即数：`1`×64, `2`×6, `3`×1, `4`×5, `6`×2, `8`×2, `16`×6, `19`×1, `24`×1, `32`×1, `64`×6, `80`×4, `88`×4, `95`×1, `96`×1, `97`×1, `120`×1, `128`×1, `156`×1, `160`×1, `239`×1, `240`×1, `241`×1, `252`×1, `258`×1, `500`×1, `995`×2, `1234`×2, `1237`×1, `4096`×1, `5048`×2, `10035`×1
* 字段偏移（102 个）：`+0x8`、`+0xc`、`+0x10`、`+0x14`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x34`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x83`、`+0x84`、`+0x88`、`+0x8c`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x160`、`+0x168`、`+0x170`、`+0x180`、`+0x188`、`+0x190`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c2`、`+0x1c8`、`+0x1e0`、`+0x1e8`、`+0x200`、`+0x208`、`+0x220`、`+0x228`、`+0x230`、`+0x240`、`+0x248`、`+0x250`、`+0x258`、`+0x260`、`+0x268`、`+0x270`、`+0x278`、`+0x290`、`+0x298`、`+0x2b0`、`+0x2b4`、`+0x2b8`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x2f8`、`+0x300`、`+0x308`、`+0x310`、`+0x318`、`+0x320`、`+0x330`、`+0x338`、`+0x340`、`+0x344`、`+0x348`、`+0x350`、`+0x358`、`+0x360`、`+0x368`、`+0x3a0`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.40 `0x151ba0` **[已证实 + 未解]**

* 函数：`0x151ba0`，9869 字节 / **1849 条指令**
* 被调用者（4 个）：`0x9984b0`(5B，5721 调用者)、`0x151ba0`(9869B)、`0x1511f0`(2467B)、`0x910af0`(168B，345 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×4, `7`×5, `63`×1, `112`×2, `120`×1, `255`×1, `376`×2, `2175`×2
* 字段偏移（55 个）：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x44`、`+0x48`、`+0x50`、`+0x54`、`+0x58`、`+0x5c`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xcc`、`+0xd0`、`+0xd8`、`+0xdc`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x144`、`+0x148`、`+0x14c`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x1c0`、`+0x1d0`、`+0x1d8`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.41 `0x58fc60` **[已证实 + 未解]**

* 函数：`0x58fc60`，9654 字节 / **1877 条指令**
* 被调用者（9 个）：`0x998500`(109B，2318 调用者)、`0x63f2f8`(0B)、`0x9984b0`(5B，5721 调用者)、`0x74d8a0`(8056B)、`0x74c9c0`(3796B)、`0x58e600`(5724B)、`0x74bb30`(2255B)、`0x6e4750`(25B，26 调用者)、`0x62f280`(171B，5209 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×54, `2`×27, `3`×79, `8`×22, `32`×2, `664`×2
* 字段偏移（105 个）：`+0x8`、`+0x10`、`+0x14`、`+0x15`、`+0x20`、`+0x28`、`+0x30`、`+0x34`、`+0x35`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x54`、`+0x55`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x74`、`+0x75`、`+0x78`、`+0x80`、`+0x84`、`+0x85`、`+0x90`、`+0x98`、`+0xa0`、`+0xa4`、`+0xa5`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc4`、`+0xc5`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe4`、`+0xe5`、`+0xf0`、`+0xf8`、`+0x100`、`+0x104`、`+0x105`、`+0x110`、`+0x118`、`+0x120`、`+0x124`、`+0x125`、`+0x130`、`+0x138`、`+0x140`、`+0x144`、`+0x145`、`+0x150`、`+0x158`、`+0x160`、`+0x164`、`+0x165`、`+0x170`、`+0x178`、`+0x180`、`+0x184`、`+0x185`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1a4`、`+0x1a5`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c4`、`+0x1c5`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1e4`、`+0x1e5`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x204`、`+0x205`、`+0x210`、`+0x218`、`+0x220`、`+0x224`、`+0x225`、`+0x230`、`+0x238`、`+0x240`、`+0x244`、`+0x245`、`+0x250`、`+0x258`、`+0x260`、`+0x264`、`+0x265`、`+0x270`、`+0x278`、`+0x280`、`+0x284`、`+0x285`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.42 `0x1f5c20` **[已证实 + 未解]**

* 函数：`0x1f5c20`，9576 字节 / **1850 条指令**
* 被调用者（54 个）：`0x183f60`(16B，19 调用者)、`0x66f530`(95B)、`0x1f2d00`(1766B)、`0x891b40`(52B，240 调用者)、`0x62f280`(171B，5209 调用者)、`0x1f0b80`(4253B)、`0x8b85f0`(88B)、`0x8b8a70`(579B)、`0x1f0660`(60B)、`0x60a620`(2620B，680 调用者)、`0x9984b0`(5B，5721 调用者)、`0x678890`(399B)、`0x51c450`(80B)、`0x51c030`(530B，30 调用者)、`0x1f4ba0`(4221B)、`0x8ba4f0`(88B，46 调用者)、`0x1eea80`(383B)、`0x1f05a0`(177B，6 调用者)、`0x1b33b0`(9910B)、`0x172460`(128B，16 调用者)、`0x5f3900`(22B，58 调用者)、`0x1f06a0`(90B)、`0x910a60`(136B，185 调用者)、`0x992750`(226B，31 调用者)、`0x1f1c20`(2606B)、`0x5f3980`(10B，44 调用者)、`0x7b5b00`(132B)、`0x678a80`(88B)、`0x92ecb0`(791B，180 调用者)、`0x1816a0`(2016B，39 调用者)、`0x998500`(109B，2318 调用者)、`0x63f2f0`(0B)、`0x8b9ea0`(337B，16 调用者)、`0x5f3960`(17B，77 调用者)、`0x6ac370`(694B，57 调用者)、`0x979e70`(51B，676 调用者)、`0x8b4ae0`(196B，30 调用者)、`0x669980`(70B，11 调用者)、`0x4fc210`(12B，13 调用者)、`0x1f2650`(1705B)、`0x1f36a0`(5373B)、`0x52d260`(2232B)、`0x51ca80`(30B，8 调用者)、`0x8eef90`(328B，24 调用者)、`0x1b64e0`(4654B)、`0x97ab50`(75B，352 调用者)、`0x9989a0`(125B，837 调用者)、`0x66da30`(91B，19 调用者)、`0x998fe0`(79B，783 调用者)、`0x998bc0`(124B，833 调用者)、`0x1f8300`(72B，10 调用者)、`0x90f9e0`(72B，27 调用者)、`0x9926b0`(159B，78 调用者)、`0x775600`(1124B，39 调用者)
* 字符串：`plates.size() > 0`、`NestProblem`、`..\nesting\structure_interface_private.hpp`、`params.m_initial_solution->Bindable(spb)`、`NestProblem`、`..\nesting\structure_interface_private.hpp`、`!res.m_nestings.empty()`、`NestProblem`
* 浮点常量：**0.95**（`0x9c0f20`）、**0.05**（`0x9c0f28`）、**0.5**（`0x9c0ee0`）、**3**（`0x9c0f38`）、**0.1**（`0x9c0f40`）
* 立即数：`1`×23, `2`×3, `3`×14, `4`×2, `9`×1, `12`×1, `13`×1, `16`×42, `24`×1, `26`×1, `32`×4, `40`×16, `48`×2, `80`×4, `297`×1, `304`×1, `328`×1, `344`×3, `368`×1, `381`×1, `391`×1, `2008`×2
* 字段偏移（122 个）：`+0x4`、`+0x5`、`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x20`、`+0x24`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x4c`、`+0x50`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe4`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x158`、`+0x160`、`+0x170`、`+0x178`、`+0x180`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1d0`、`+0x1f0`、`+0x210`、`+0x230`、`+0x250`、`+0x270`、`+0x290`、`+0x2b0`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2f0`、`+0x310`、`+0x318`、`+0x320`、`+0x330`、`+0x350`、`+0x370`、`+0x390`、`+0x3b0`、`+0x3d0`、`+0x3f0`、`+0x410`、`+0x430`、`+0x450`、`+0x458`、`+0x460`、`+0x470`、`+0x478`、`+0x480`、`+0x488`、`+0x490`、`+0x498`、`+0x4a0`、`+0x4a8`、`+0x4b0`、`+0x4b8`、`+0x4c0`、`+0x4c8`、`+0x4e0`、`+0x4e4`、`+0x4e5`、`+0x4e8`、`+0x4ec`、`+0x4f0`、`+0x4f8`、`+0x500`、`+0x504`、`+0x508`、`+0x510`、`+0x518`、`+0x520`、`+0x528`、`+0x530`、`+0x538`、`+0x540`、`+0x568`、`+0x758`、`+0x770`、`+0x780`、`+0x790`、`+0x7a0`、`+0x7b0`、`+0x7c0`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.43 `0x6c0fc0` **[已证实 + 未解]**

* 函数：`0x6c0fc0`，9141 字节 / **2175 条指令**
* 被调用者（8 个）：`0x6c0350`(1056B)、`0x6c4590`(1839B)、`0x9984b0`(5B，5721 调用者)、`0x998500`(109B，2318 调用者)、`0x906430`(305B)、`0x962530`(437B)、`0x6c0770`(2126B)、`0x62f280`(171B，5209 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×121, `3`×22, `5`×1, `24`×9, `31`×1, `63`×30, `72`×30, `168`×2
* 字段偏移（23 个）：`+0x1`、`+0x4`、`+0x5`、`+0x8`、`+0x10`、`+0x18`、`+0x1c`、`+0x20`、`+0x28`、`+0x30`、`+0x34`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x5c`、`+0x60`、`+0x68`、`+0x70`、`+0x80`、`+0x90`、`+0xf0`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.44 `0x74f820` **[已证实 + 未解]**

* 函数：`0x74f820`，8400 字节 / **1503 条指令**
* 被调用者（11 个）：`0x63f2f8`(0B)、`0x6fef10`(1451B)、`0x998500`(109B，2318 调用者)、`0x9984b0`(5B，5721 调用者)、`0x6e6120`(8168B，18 调用者)、`0x6e39a0`(3501B，9 调用者)、`0x6e4aa0`(1528B，6 调用者)、`0x6e1440`(2289B)、`0x6e11c0`(627B)、`0x6e32d0`(1452B，6 调用者)、`0x62f280`(171B，5209 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×61, `2`×12, `3`×53, `8`×26, `936`×2
* 字段偏移（140 个）：`+0x8`、`+0x10`、`+0x14`、`+0x15`、`+0x20`、`+0x28`、`+0x2e`、`+0x2f`、`+0x30`、`+0x34`、`+0x35`、`+0x38`、`+0x40`、`+0x50`、`+0x58`、`+0x60`、`+0x64`、`+0x65`、`+0x70`、`+0x78`、`+0x80`、`+0x84`、`+0x85`、`+0x90`、`+0x98`、`+0xa0`、`+0xa4`、`+0xa5`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc4`、`+0xc5`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe4`、`+0xe5`、`+0xf0`、`+0xf8`、`+0x100`、`+0x104`、`+0x105`、`+0x110`、`+0x118`、`+0x120`、`+0x124`、`+0x125`、`+0x130`、`+0x138`、`+0x140`、`+0x144`、`+0x145`、`+0x150`、`+0x158`、`+0x160`、`+0x164`、`+0x165`、`+0x170`、`+0x178`、`+0x180`、`+0x184`、`+0x185`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1a4`、`+0x1a5`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c4`、`+0x1c5`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1e4`、`+0x1e5`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x204`、`+0x205`、`+0x230`、`+0x238`、`+0x240`、`+0x244`、`+0x245`、`+0x250`、`+0x258`、`+0x260`、`+0x264`、`+0x265`、`+0x270`、`+0x278`、`+0x280`、`+0x284`、`+0x285`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2a4`、`+0x2a5`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2c4`、`+0x2c5`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2e4`、`+0x2e5`、`+0x2f0`、`+0x2f8`、`+0x300`、`+0x304`、`+0x305`、`+0x310`、`+0x318`、`+0x320`、`+0x324`、`+0x325`、`+0x330`、`+0x338`、`+0x340`、`+0x344`、`+0x345`、`+0x350`、`+0x358`、`+0x360`、`+0x364`、`+0x365`、`+0x370`、`+0x378`、`+0x380`、`+0x384`、`+0x385`、`+0x388`、`+0x390`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.45 `0x681fa0` **[已证实 + 未解]**

* 函数：`0x681fa0`，7633 字节 / **1891 条指令**
* 被调用者（2 个）：`0x683d80`(2119B)、`0x9984b0`(5B，5721 调用者)
* 字符串：`AWAVAUATUWVSH`、`AWAVAUATUWVSH`
* 浮点常量：无
* 立即数：`56`×2
* 字段偏移（3 个）：`+0x8`、`+0x10`、`+0x28`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.46 `0x8ef0e0` **[已证实 + 未解]**

* 函数：`0x8ef0e0`，7416 字节 / **1591 条指令**
* 被调用者（22 个）：`0x910af0`(168B，345 调用者)、`0x8e6400`(1770B，29 调用者)、`0x8ea9d0`(335B，25 调用者)、`0x92f060`(272B，16 调用者)、`0x8e1fb0`(744B，27 调用者)、`0x8ea720`(423B，25 调用者)、`0x63f2f0`(0B)、`0x9984b0`(5B，5721 调用者)、`0x92ecb0`(791B，180 调用者)、`0x998500`(109B，2318 调用者)、`0x97a830`(75B，571 调用者)、`0x92dee0`(1148B，49 调用者)、`0x910ba0`(109B，1002 调用者)、`0x63f2f8`(0B)、`0x9989a0`(125B，837 调用者)、`0x7bb7a0`(54B，56 调用者)、`0x998fe0`(79B，783 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x979e70`(51B，676 调用者)、`0x998bc0`(124B，833 调用者)、`0x62f280`(171B，5209 调用者)、`0x8e6390`(107B，48 调用者)
* 字符串：`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`
* 浮点常量：无
* 立即数：`1`×10, `3`×13, `4`×14, `15`×6, `16`×6, `24`×6, `104`×6, `120`×8, `152`×2, `312`×12
* 字段偏移（42 个）：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x54`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.47 `0x147180` **[已证实 + 未解]**

* 函数：`0x147180`，7237 字节 / **1354 条指令**
* 被调用者（9 个）：`0x136d30`(13B，7 调用者)、`0x9984b0`(5B，5721 调用者)、`0x136d10`(6B，12 调用者)、`0x136cb0`(78B，9 调用者)、`0x147180`(7237B)、`0x146130`(2075B)、`0x910af0`(168B，345 调用者)、`0x679070`(54B，21 调用者)、`0x62f280`(171B，5209 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×4, `3`×3, `48`×2, `63`×1, `88`×5, `175`×1, `312`×2, `1495`×2
* 字段偏移（40 个）：`+0x8`、`+0x10`、`+0x11`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x69`、`+0x70`、`+0x71`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd1`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x120`、`+0x190`、`+0x198`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.48 `0x635fc0` **[已证实 + 未解]**

* 函数：`0x635fc0`，7120 字节 / **1499 条指令**
* 被调用者（25 个）：`0x63f320`(0B)、`0x63f238`(0B)、`0x63f050`(97B)、`0x63e530`(99B，11 调用者)、`0x63f000`(67B)、`0x63f4d8`(0B)、`0x635b50`(922B)、`0x63ed10`(264B)、`0x63ddb0`(249B)、`0x63e930`(249B)、`0x63ee50`(251B)、`0x63e7b0`(377B)、`0x63ea80`(371B)、`0x63ea30`(65B)、`0x63e430`(246B，17 调用者)、`0x63f2f8`(0B)、`0x63e650`(38B)、`0x63e680`(289B)、`0x63ef50`(169B)、`0x637cd0`(325B)、`0x63deb0`(60B)、`0x635f30`(139B)、`0x63d4c0`(2288B)、`0x63df80`(905B)、`0x635aa0`(172B)
* 字符串：`inity`
* 浮点常量：**1**（`0xa07000`）、**2**（`0xa07008`）、**0.5**（`0xa07010`）、**1**（`0xa07000`）、**0.5**（`0xa07010`）、**1**（`0xa07000`）
* 立即数：`1`×81, `2`×5, `3`×5, `4`×8, `5`×2, `6`×3, `8`×9, `9`×8, `15`×11, `16`×12, `17`×7, `20`×4, `21`×1, `22`×1, `31`×10, `32`×4, `33`×6, `34`×3, `37`×1, `40`×1, `43`×1, `45`×3, `48`×9, `53`×3, `64`×1, `69`×1, `73`×1, `78`×1, `80`×3, `88`×1, `105`×1, `110`×1, `120`×1, `163`×1, `360`×2, `2047`×4
* 字段偏移（50 个）：`+0x1`、`+0x2`、`+0x4`、`+0x8`、`+0xc`、`+0x10`、`+0x14`、`+0x18`、`+0x1c`、`+0x1f`、`+0x20`、`+0x28`、`+0x30`、`+0x44`、`+0x48`、`+0x4c`、`+0x50`、`+0x58`、`+0x60`、`+0x64`、`+0x68`、`+0x6c`、`+0x70`、`+0x78`、`+0x80`、`+0x84`、`+0x88`、`+0x8c`、`+0x9c`、`+0xa0`、`+0xa4`、`+0xa8`、`+0xac`、`+0xb0`、`+0xb4`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xe0`、`+0xf0`、`+0x100`、`+0x110`、`+0x120`、`+0x130`、`+0x140`、`+0x150`、`+0x1b8`、`+0x1c0`、`+0x1c8`、`+0x1d0`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.49 `0x530110` **[已证实 + 未解]**

* 函数：`0x530110`，6835 字节 / **1269 条指令**
* 被调用者（29 个）：`0x5f4310`(35B，45 调用者)、`0x51d0c0`(5B，103 调用者)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x9984b0`(5B，5721 调用者)、`0x520440`(479B，56 调用者)、`0x4f7600`(9B，50 调用者)、`0x5203d0`(19B，45 调用者)、`0x5203f0`(19B，33 调用者)、`0x5d3ea0`(2155B，27 调用者)、`0x5cd800`(610B，113 调用者)、`0x5c8a90`(437B，16 调用者)、`0x5c8eb0`(122B，41 调用者)、`0x52fdb0`(602B)、`0x908d60`(253B)、`0x93da50`(408B，15 调用者)、`0x4f76a0`(4B，57 调用者)、`0x5cee50`(527B，52 调用者)、`0x5ce7b0`(50B，32 调用者)、`0x5ce970`(269B，38 调用者)、`0x563a40`(45B，7 调用者)、`0x57a680`(33B)、`0x57a9f0`(143B)、`0x4f72a0`(5B)、`0x54cbb0`(10B，16 调用者)、`0x526bd0`(1485B)、`0x5f4340`(140B，67 调用者)、`0x62f280`(171B，5209 调用者)、`0x8c5090`(147B，133 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：**0.5**（`0x9dbca0`）、**0.001**（`0x9dbca8`）、**0.001**（`0x9dbca8`）
* 立即数：`1`×6, `3`×5, `4`×7, `7`×4, `8`×2, `9`×2, `13`×3, `16`×30, `24`×1, `34`×3, `35`×7, `36`×2, `41`×2, `48`×1, `77`×3, `89`×2, `90`×2, `112`×7, `116`×7, `1368`×2, `10536`×3
* 字段偏移（129 个）：`+0x1`、`+0x4`、`+0x6`、`+0x8`、`+0xc`、`+0x10`、`+0x14`、`+0x16`、`+0x18`、`+0x20`、`+0x22`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0xa0`、`+0xb0`、`+0xc0`、`+0xd0`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x150`、`+0x160`、`+0x170`、`+0x180`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1c0`、`+0x1c8`、`+0x1e0`、`+0x1e8`、`+0x1f0`、`+0x200`、`+0x208`、`+0x210`、`+0x220`、`+0x228`、`+0x230`、`+0x240`、`+0x248`、`+0x250`、`+0x260`、`+0x268`、`+0x270`、`+0x280`、`+0x288`、`+0x290`、`+0x2a0`、`+0x2a8`、`+0x2b0`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x300`、`+0x308`、`+0x310`、`+0x320`、`+0x328`、`+0x330`、`+0x340`、`+0x348`、`+0x350`、`+0x360`、`+0x361`、`+0x364`、`+0x368`、`+0x370`、`+0x378`、`+0x380`、`+0x388`、`+0x390`、`+0x398`、`+0x3a0`、`+0x3a8`、`+0x3b0`、`+0x3b8`、`+0x3c0`、`+0x3f0`、`+0x420`、`+0x450`、`+0x480`、`+0x488`、`+0x490`、`+0x497`、`+0x498`、`+0x4a0`、`+0x4b0`、`+0x4b8`、`+0x4c0`、`+0x4c7`、`+0x4c8`、`+0x4c9`、`+0x4cd`、`+0x4d0`、`+0x4e0`、`+0x4f0`、`+0x500`、`+0x510`、`+0x520`、`+0x530`、`+0x540`、`+0x5a0`、`+0x5b0`、`+0x5b8`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.50 `0x6ad580` **[已证实 + 未解]**

* 函数：`0x6ad580`，8964 字节 / **2142 条指令**
* 被调用者（7 个）：`0x998500`(109B，2318 调用者)、`0x960a70`(739B)、`0x6bacc0`(1055B)、`0x592330`(72B，10 调用者)、`0x9984b0`(5B，5721 调用者)、`0x62f280`(171B，5209 调用者)、`0x979e70`(51B，676 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×74, `2`×12, `3`×12, `4`×21, `48`×3, `63`×18, `120`×18, `136`×3
* 字段偏移（21 个）：`+0x1`、`+0x3`、`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x24`、`+0x28`、`+0x30`、`+0x34`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x54`、`+0x58`、`+0x60`、`+0x64`、`+0x68`、`+0x70`、`+0x78`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.51 `0x5b7a90` **[已证实 + 未解]**

* 函数：`0x5b7a90`，8833 字节 / **1741 条指令**
* 被调用者（17 个）：`0x998500`(109B，2318 调用者)、`0x687720`(365B)、`0x871320`(282B，6 调用者)、`0x5a4cd0`(75B)、`0x6848e0`(266B)、`0x6e4750`(25B，26 调用者)、`0x5a6580`(114B，18 调用者)、`0x63f2f8`(0B)、`0x9984b0`(5B，5721 调用者)、`0x6874f0`(558B)、`0x5a6650`(114B)、`0x8c8df0`(1865B)、`0x5b79e0`(162B)、`0x684b00`(82B，34 调用者)、`0x8fbdc0`(290B)、`0x62f280`(171B，5209 调用者)、`0x8c9c30`(232B，8 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×22, `2`×36, `3`×68, `8`×9, `32`×3, `64`×1, `144`×3, `352`×1, `416`×1, `488`×2
* 字段偏移（83 个）：`+0x8`、`+0x10`、`+0x14`、`+0x15`、`+0x20`、`+0x28`、`+0x30`、`+0x34`、`+0x35`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x64`、`+0x65`、`+0x68`、`+0x70`、`+0x78`、`+0x7c`、`+0x80`、`+0x84`、`+0x85`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb4`、`+0xb5`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd4`、`+0xd5`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x104`、`+0x105`、`+0x110`、`+0x118`、`+0x120`、`+0x124`、`+0x125`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x154`、`+0x155`、`+0x158`、`+0x160`、`+0x164`、`+0x168`、`+0x170`、`+0x174`、`+0x175`、`+0x178`、`+0x180`、`+0x188`、`+0x190`、`+0x194`、`+0x198`、`+0x1a0`、`+0x1a4`、`+0x1a5`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c4`、`+0x1c5`、`+0x1d0`、`+0x1d8`、`+0x230`、`+0x660`、`+0x668`、`+0x670`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.52 `0x53790` **[已证实 + 未解]**

* 函数：`0x53790`，8763 字节 / **1467 条指令**
* 被调用者（3 个）：`0x9984b0`(5B，5721 调用者)、`0x92ecb0`(791B，180 调用者)、`0x910af0`(168B，345 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`3`×1, `112`×3, `120`×6, `424`×5, `440`×1, `520`×2
* 字段偏移（121 个）：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x2c`、`+0x30`、`+0x31`、`+0x34`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xec`、`+0xf0`、`+0xf1`、`+0xf4`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x11c`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x180`、`+0x188`、`+0x18c`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c8`、`+0x1d0`、`+0x1d8`、`+0x1dc`、`+0x1e0`、`+0x1e8`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x208`、`+0x210`、`+0x218`、`+0x220`、`+0x228`、`+0x230`、`+0x238`、`+0x240`、`+0x244`、`+0x248`、`+0x249`、`+0x24c`、`+0x250`、`+0x258`、`+0x260`、`+0x268`、`+0x270`、`+0x278`、`+0x280`、`+0x288`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2a8`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x2f8`、`+0x300`、`+0x308`、`+0x310`、`+0x318`、`+0x320`、`+0x328`、`+0x330`、`+0x334`、`+0x338`、`+0x340`、`+0x348`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.53 `0x22e960` **[已证实 + 未解]**

* 函数：`0x22e960`，6710 字节 / **1363 条指令**
* 被调用者（29 个）：`0x197620`(60B)、`0x932420`(408B，36 调用者)、`0x9984b0`(5B，5721 调用者)、`0x6585a0`(3986B)、`0x659540`(3986B)、`0x22d820`(181B)、`0x60a620`(2620B，680 调用者)、`0x1bebc0`(53B)、`0x1bec00`(683B)、`0x16c200`(81B，15 调用者)、`0x16c710`(22B)、`0x998500`(109B，2318 调用者)、`0x16c730`(33B)、`0x1d52c0`(214B)、`0x1a1570`(191B，10 调用者)、`0x1beeb0`(21B)、`0x1a1630`(159B，11 调用者)、`0x1708e0`(5B，20 调用者)、`0x1be6a0`(1241B)、`0x1969e0`(68B)、`0x657d20`(653B)、`0x1d53a0`(7403B)、`0x97a040`(5B，125 调用者)、`0x9364f0`(713B，7 调用者)、`0x8ff720`(305B)、`0x1bff90`(1981B，7 调用者)、`0x86ff70`(137B)、`0x99cef0`(104B)、`0x62f280`(171B，5209 调用者)
* 字符串：`m_left >= s_min && m_right <= s_max`、`NestingWindow`、`..\nesting\algos\../nesting.hpp`
* 浮点常量：**0.0001**（`0x9c20e0`）、**0.0001**（`0x9c20e0`）
* 立即数：`1`×10, `2`×4, `3`×10, `4`×2, `5`×3, `8`×4, `15`×2, `16`×6, `19`×2, `24`×20, `28`×2, `31`×2, `32`×4, `88`×1, `264`×1, `480`×2, `500`×1, `1000`×2, `1032`×2
* 字段偏移（124 个）：`+0x4`、`+0x8`、`+0xf`、`+0x10`、`+0x14`、`+0x18`、`+0x1c`、`+0x20`、`+0x28`、`+0x30`、`+0x34`、`+0x38`、`+0x40`、`+0x48`、`+0x4c`、`+0x50`、`+0x54`、`+0x58`、`+0x5c`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xd0`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x160`、`+0x180`、`+0x1a0`、`+0x1a4`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c4`、`+0x1c8`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1e4`、`+0x1e8`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x204`、`+0x208`、`+0x210`、`+0x218`、`+0x220`、`+0x228`、`+0x238`、`+0x250`、`+0x280`、`+0x288`、`+0x290`、`+0x294`、`+0x298`、`+0x2a0`、`+0x2a8`、`+0x2b0`、`+0x2b4`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x300`、`+0x308`、`+0x310`、`+0x314`、`+0x318`、`+0x320`、`+0x328`、`+0x330`、`+0x338`、`+0x340`、`+0x350`、`+0x358`、`+0x360`、`+0x368`、`+0x36c`、`+0x370`、`+0x378`、`+0x380`、`+0x388`、`+0x398`、`+0x3a0`、`+0x3b0`、`+0x3c0`、`+0x3d0`、`+0x3e0`、`+0x3f0`、`+0x450`、`+0x458`、`+0x468`、`+0x470`、`+0x478`、`+0x480`、`+0x488`、`+0x490`、`+0x498`、`+0x4a0`、`+0x4a8`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.54 `0x513880` **[已证实 + 未解]**

* 函数：`0x513880`，6150 字节 / **1221 条指令**
* 被调用者（41 个）：`0x4fc5a0`(8B，114 调用者)、`0x4fc5b0`(319B，85 调用者)、`0x4f7600`(9B，50 调用者)、`0x5d2f50`(1242B)、`0x5cd800`(610B，113 调用者)、`0x5c8c50`(255B，57 调用者)、`0x8c4ff0`(147B，123 调用者)、`0x50fb50`(239B)、`0x4f7050`(4B，20 调用者)、`0x4fc930`(8B，37 调用者)、`0x50fd00`(60B，9 调用者)、`0x60a620`(2620B，680 调用者)、`0x9984b0`(5B，5721 调用者)、`0x523050`(174B，33 调用者)、`0x4f8390`(420B，35 调用者)、`0x5dedd0`(136B，12 调用者)、`0x5daeb0`(1363B)、`0x5e0ae0`(679B，7 调用者)、`0x8c4c60`(911B，28 调用者)、`0x5d2420`(195B)、`0x4f76a0`(4B，57 调用者)、`0x5dddd0`(1350B，8 调用者)、`0x5dfc50`(66B，15 调用者)、`0x4f7720`(26B，7 调用者)、`0x54ce90`(3B，16 调用者)、`0x54ce60`(5B，43 调用者)、`0x4f7770`(41B，17 调用者)、`0x605680`(1379B，16 调用者)、`0x50fc40`(177B，13 调用者)、`0x4f76d0`(4B，15 调用者)、`0x50fe50`(90B)、`0x4f7030`(4B，17 调用者)、`0x992750`(226B，31 调用者)、`0x910a60`(136B，185 调用者)、`0x5de880`(1347B，10 调用者)、`0x5deeb0`(806B，16 调用者)、`0x5132b0`(1478B)、`0x905730`(107B，22 调用者)、`0x904f30`(702B)、`0x62f280`(171B，5209 调用者)、`0x97ab50`(75B，352 调用者)
* 字符串：`problem.GetNumberOfSheets() != 0`、`DrawHtmlPartsTable`、`..\structure\svg_io.cpp`、`&nbsp dimensions: `、`&nbsp contribution: `、`&nbsp per-sheet: `、`&nbsp priority: `、`&nbsp quantity: `
* 浮点常量：**0.5**（`0x9db9f0`）、**0.8**（`0x9dba10`）、**0.1**（`0x9dba18`）
* 立即数：`1`×7, `2`×1, `4`×4, `5`×2, `16`×73, `64`×1, `848`×1, `1001`×1, `1560`×2
* 字段偏移（119 个）：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x10c`、`+0x110`、`+0x120`、`+0x130`、`+0x138`、`+0x140`、`+0x150`、`+0x170`、`+0x178`、`+0x190`、`+0x198`、`+0x1b0`、`+0x1b8`、`+0x1d0`、`+0x1d8`、`+0x1f0`、`+0x1f8`、`+0x210`、`+0x218`、`+0x220`、`+0x228`、`+0x230`、`+0x250`、`+0x270`、`+0x278`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2a8`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2f0`、`+0x310`、`+0x330`、`+0x350`、`+0x370`、`+0x390`、`+0x3b0`、`+0x3d0`、`+0x3f0`、`+0x410`、`+0x418`、`+0x420`、`+0x428`、`+0x430`、`+0x450`、`+0x470`、`+0x478`、`+0x480`、`+0x488`、`+0x490`、`+0x498`、`+0x4a0`、`+0x4a8`、`+0x4b0`、`+0x4d0`、`+0x4f0`、`+0x4f8`、`+0x500`、`+0x508`、`+0x510`、`+0x518`、`+0x520`、`+0x528`、`+0x530`、`+0x540`、`+0x548`、`+0x550`、`+0x558`、`+0x560`、`+0x570`、`+0x578`、`+0x580`、`+0x588`、`+0x590`、`+0x5a0`、`+0x5b0`、`+0x5c0`、`+0x5d0`、`+0x5e0`、`+0x5f0`、`+0x600`、`+0x660`、`+0x668`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.55 `0x264af0` **[已证实 + 未解]**

* 函数：`0x264af0`，6107 字节 / **1128 条指令**
* 被调用者（12 个）：`0x998500`(109B，2318 调用者)、`0x62fe20`(270B，90 调用者)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x9984b0`(5B，5721 调用者)、`0x2639f0`(1448B)、`0x263fa0`(349B)、`0x2671f0`(97B)、`0x8db130`(485B)、`0x8dba30`(305B)、`0x8dbd40`(410B)、`0x62f280`(171B，5209 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：**1**（`0x9c2cc0`）、**1**（`0x9c2cc0`）
* 立即数：`1`×2, `3`×1, `4`×2, `9`×4, `16`×20, `18`×4, `24`×1, `34`×4, `35`×4, `56`×2, `58`×4, `64`×1, `96`×2, `101`×4, `776`×2
* 字段偏移（82 个）：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x21`、`+0x22`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xe0`、`+0xe8`、`+0xf0`、`+0x100`、`+0x110`、`+0x120`、`+0x128`、`+0x130`、`+0x140`、`+0x148`、`+0x150`、`+0x160`、`+0x170`、`+0x180`、`+0x188`、`+0x190`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b9`、`+0x1c0`、`+0x1c8`、`+0x1d0`、`+0x1d8`、`+0x1d9`、`+0x1e0`、`+0x1e1`、`+0x1e2`、`+0x1e8`、`+0x1f0`、`+0x200`、`+0x208`、`+0x210`、`+0x218`、`+0x219`、`+0x220`、`+0x221`、`+0x228`、`+0x230`、`+0x238`、`+0x240`、`+0x248`、`+0x250`、`+0x258`、`+0x260`、`+0x270`、`+0x280`、`+0x290`、`+0x2a0`、`+0x2b0`、`+0x2c0`、`+0x2d0`、`+0x2e0`、`+0x2f0`、`+0x350`、`+0x368`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.56 `0x553e00` **[已证实 + 未解]**

* 函数：`0x553e00`，5858 字节 / **1397 条指令**
* 被调用者（6 个）：`0x96a390`(1159B)、`0x520440`(479B，56 调用者)、`0x4f76a0`(4B，57 调用者)、`0x910af0`(168B，345 调用者)、`0x552270`(52B)、`0x7bb7e0`(99B，7 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×1, `3`×11, `4`×3, `5`×2, `7`×2, `104`×2, `120`×37, `839`×2
* 字段偏移（17 个）：`+0x8`、`+0x10`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x54`、`+0x58`、`+0x60`、`+0x68`、`+0xb0`、`+0xb8`、`+0xc0`、`+0x348`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.57 `0x63bf20` **[已证实 + 未解]**

* 函数：`0x63bf20`，5521 字节 / **1273 条指令**
* 被调用者（16 个）：`0x63e430`(246B，17 调用者)、`0x63deb0`(60B)、`0x63e530`(99B，11 调用者)、`0x63bd00`(122B)、`0x63ec00`(266B)、`0x63bcd0`(48B)、`0x63ddb0`(249B)、`0x63e650`(38B)、`0x63e7b0`(377B)、`0x63e680`(289B)、`0x63e930`(249B)、`0x63e5a0`(169B)、`0x63ea30`(65B)、`0x63bda0`(379B)、`0x63ea80`(371B)、`0x63f2f8`(0B)
* 字符串：`NaN`、`Infinity`
* 浮点常量：**0.176091**（`0xa07298`）、**1.5**（`0xa07288`）、**0.28953**（`0xa07290`）、**0.30103**（`0xa072a0`）、**1**（`0xa072b8`）、**7**（`0xa072d0`）、**0.5**（`0xa072f0`）、**1**（`0xa072b8`）、**10**（`0xa072c0`）、**7**（`0xa072d0`）、**5**（`0xa072d8`）、**5**（`0xa072d8`）、**0.30103**（`0xa072b0`）、**10**（`0xa072c0`）、**10**（`0xa072c0`）、**0.5**（`0xa072f0`）、**10**（`0xa072c0`）、**3**（`0xa072c8`）、**7**（`0xa072d0`）
* 立即数：`1`×79, `2`×12, `3`×4, `4`×8, `5`×5, `7`×1, `8`×2, `9`×1, `10`×8, `14`×3, `16`×9, `20`×1, `22`×1, `31`×5, `32`×20, `48`×6, `49`×4, `57`×8, `168`×2, `1022`×1, `1077`×1, `2039`×1
* 字段偏移（30 个）：`+0x1`、`+0x4`、`+0x8`、`+0xc`、`+0x10`、`+0x14`、`+0x18`、`+0x28`、`+0x30`、`+0x38`、`+0x3c`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x5c`、`+0x60`、`+0x64`、`+0x68`、`+0x70`、`+0x78`、`+0x7c`、`+0x8c`、`+0x90`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.58 `0x751aa0` **[已证实 + 未解]**

* 函数：`0x751aa0`，5463 字节 / **1025 条指令**
* 被调用者（11 个）：`0x63f2f8`(0B)、`0x6fc810`(3B)、`0x9984a0`(5B，653 调用者)、`0x9984b0`(5B，5721 调用者)、`0x910ba0`(109B，1002 调用者)、`0x63f300`(0B)、`0x8f1fe0`(464B，19 调用者)、`0x998500`(109B，2318 调用者)、`0x9984e0`(5B，587 调用者)、`0x754cd0`(21B，9 调用者)、`0x62f280`(171B，5209 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×33, `2`×19, `15`×1, `16`×16, `32`×3, `808`×2
* 字段偏移（87 个）：`+0x8`、`+0x10`、`+0x18`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x120`、`+0x128`、`+0x130`、`+0x140`、`+0x148`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x180`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c8`、`+0x1d0`、`+0x1e0`、`+0x1e8`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x208`、`+0x210`、`+0x218`、`+0x220`、`+0x230`、`+0x238`、`+0x240`、`+0x248`、`+0x250`、`+0x258`、`+0x260`、`+0x268`、`+0x270`、`+0x280`、`+0x288`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2a8`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x2f8`、`+0x300`、`+0x308`、`+0x310`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.60 两条新识别 **[已证实]**

* **`0x513880`（6,150 B）= `DrawHtmlPartsTable`（`..\structure\svg_io.cpp`）**：
  自带字符串 `'DrawHtmlPartsTable'`、`'..\structure\svg_io.cpp'`，以及一张**逐零件报表**的列名
  `'&nbsp dimensions: '`、`'&nbsp contribution: '`、`'&nbsp per-sheet: '`、`'&nbsp priority: '`、
  `'&nbsp quantity: '`，外加前置条件 `'problem.GetNumberOfSheets() != 0'`。
  ⇒ **`svg_io.cpp` 不只写 SVG，它还生成 HTML 报表**（这解释了该 TU 169 KB 未引用里的一大部分）。
  常量 `0.5`、`0.8`、`0.1`。
* **`0x22E960`（6,710 B）= `NestingWindow`**：字符串 `'NestingWindow'`、
  `'..\nesting\algos\../nesting.hpp'`、断言 `'m_left >= s_min && m_right <= s_max'`，
  常量 **`0.0001`**。⇒ 这正是 round 4 在 bucket_manager 调用面里认出的 `NestingWindow 0x20CCE0`
  的**同族实现点**（`..\nesting\nesting.hpp` 里的窗口类型），且窗口边界有不变量。
* **`0x63BF20`（5,521 B）**：字符串 `'NaN'`、`'Infinity'`，常量里含 **`0.30103`(=log10 2)**、
  **`0.176091`(=log10 1.5)**、`0.28953`、`1.5`、`7`、`10`、`5`
  ⇒ **对数刻度/坐标轴计算**（很可能是上面那张报表/图表的坐标换算）。**[推断，证据充分]**

### 附 6.61 `0x4c0a50` **[已证实 + 未解]**

* 函数：`0x4c0a50`，5334 字节 / **908 条指令**
* 被调用者（47 个）：`0x51bfc0`(67B，34 调用者)、`0x51c4a0`(5B，8 调用者)、`0x51ca80`(30B，8 调用者)、`0x92dee0`(1148B，49 调用者)、`0x92c240`(1237B)、`0x51d0c0`(5B，103 调用者)、`0x520320`(159B，17 调用者)、`0x533bc0`(728B)、`0x9984b0`(5B，5721 调用者)、`0x51d090`(4B，53 调用者)、`0x4fc210`(12B，13 调用者)、`0x51cff0`(159B，21 调用者)、`0x51cab0`(478B，18 调用者)、`0x51d310`(5B，20 调用者)、`0x51fde0`(30B，18 调用者)、`0x4fcd80`(513B，7 调用者)、`0x4b9df0`(418B，7 调用者)、`0x5ced50`(196B，24 调用者)、`0x5d2900`(186B，28 调用者)、`0x82a3e0`(109B，51 调用者)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x520650`(4B，24 调用者)、`0x5203d0`(19B，45 调用者)、`0x5203f0`(19B，33 调用者)、`0x5c4dd0`(189B，37 调用者)、`0x5203c0`(4B，20 调用者)、`0x51f7f0`(180B，10 调用者)、`0x5387c0`(1876B)、`0x92ecb0`(791B，180 调用者)、`0x8eef90`(328B，24 调用者)、`0x62f280`(171B，5209 调用者)、`0x910af0`(168B，345 调用者)、`0x51d0d0`(5B，7 调用者)、`0x51e7a0`(57B)、`0x51e1b0`(8B，9 调用者)、`0x51e6b0`(66B)、`0x51dd80`(660B，10 调用者)、`0x4ba7a0`(455B)、`0x51e670`(62B，6 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x8ee670`(337B，8 调用者)、`0x4bb040`(2101B)、`0x52d260`(2232B)、`0x51c030`(530B，30 调用者)、`0x92c720`(139B，7 调用者)、`0x7bfd70`(166B)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×3, `13`×1, `16`×14, `18`×1, `24`×1, `34`×1, `120`×2, `312`×3, `1098`×1, `1432`×2
* 字段偏移（162 个）：`+0x8`、`+0x10`、`+0x18`、`+0x1c`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x7c`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x150`、`+0x170`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1b0`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x210`、`+0x218`、`+0x220`、`+0x228`、`+0x230`、`+0x238`、`+0x240`、`+0x258`、`+0x270`、`+0x278`、`+0x280`、`+0x288`、`+0x2a0`、`+0x2a8`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2c8`、`+0x2d8`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x2f8`、`+0x300`、`+0x308`、`+0x310`、`+0x318`、`+0x320`、`+0x328`、`+0x330`、`+0x338`、`+0x340`、`+0x348`、`+0x350`、`+0x358`、`+0x360`、`+0x378`、`+0x380`、`+0x388`、`+0x390`、`+0x398`、`+0x39c`、`+0x3a0`、`+0x3a1`、`+0x3a4`、`+0x3a8`、`+0x3b0`、`+0x3b8`、`+0x3c0`、`+0x3c8`、`+0x3d0`、`+0x3d8`、`+0x3e0`、`+0x3e8`、`+0x3f0`、`+0x3f8`、`+0x400`、`+0x408`、`+0x410`、`+0x418`、`+0x420`、`+0x428`、`+0x430`、`+0x440`、`+0x448`、`+0x450`、`+0x458`、`+0x45d`、`+0x460`、`+0x468`、`+0x470`、`+0x478`、`+0x480`、`+0x488`、`+0x490`、`+0x498`、`+0x4a0`、`+0x4b8`、`+0x4c0`、`+0x4c8`、`+0x4d0`、`+0x4d8`、`+0x4dc`、`+0x4e0`、`+0x4e1`、`+0x4e4`、`+0x4e8`、`+0x4f0`、`+0x4f8`、`+0x500`、`+0x508`、`+0x510`、`+0x518`、`+0x520`、`+0x528`、`+0x530`、`+0x538`、`+0x540`、`+0x548`、`+0x550`、`+0x558`、`+0x560`、`+0x568`、`+0x570`、`+0x580`、`+0x5e0`、`+0x5e8`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.62 `0x8e4570` **[已证实 + 未解]**

* 函数：`0x8e4570`，5265 字节 / **1174 条指令**
* 被调用者（13 个）：`0x8c5130`(2087B，13 调用者)、`0x8e1fb0`(744B，27 调用者)、`0x9984b0`(5B，5721 调用者)、`0x998500`(109B，2318 调用者)、`0x891b40`(52B，240 调用者)、`0x9989a0`(125B，837 调用者)、`0x7b7b00`(243B，8 调用者)、`0x998fe0`(79B，783 调用者)、`0x979e70`(51B，676 调用者)、`0x998bc0`(124B，833 调用者)、`0x67fe90`(104B，155 调用者)、`0x62f280`(171B，5209 调用者)、`0x8c4ff0`(147B，123 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×16, `3`×9, `4`×6, `16`×12, `24`×8, `48`×8, `64`×1, `104`×8, `232`×12
* 字段偏移（31 个）：`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xb9`、`+0xbc`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.63 `0x5a4d70` **[已证实 + 未解]**

* 函数：`0x5a4d70`，5209 字节 / **1034 条指令**
* 被调用者（7 个）：`0x63f2f8`(0B)、`0x998500`(109B，2318 调用者)、`0x9984b0`(5B，5721 调用者)、`0x6e6120`(8168B，18 调用者)、`0x63f2f0`(0B)、`0x6e4750`(25B，26 调用者)、`0x62f280`(171B，5209 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×48, `2`×10, `3`×39, `8`×21, `9`×1, `16`×3, `280`×2
* 字段偏移（48 个）：`+0x1`、`+0x2`、`+0x8`、`+0x10`、`+0x14`、`+0x15`、`+0x20`、`+0x28`、`+0x2c`、`+0x30`、`+0x34`、`+0x35`、`+0x38`、`+0x40`、`+0x44`、`+0x45`、`+0x50`、`+0x58`、`+0x60`、`+0x64`、`+0x65`、`+0x70`、`+0x78`、`+0x80`、`+0x84`、`+0x85`、`+0x90`、`+0x98`、`+0xa0`、`+0xa4`、`+0xa5`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc4`、`+0xc5`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe4`、`+0xe5`、`+0xf0`、`+0xf8`、`+0x100`、`+0x104`、`+0x105`、`+0x168`、`+0x170`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.64 `0x56ba0` **[已证实 + 未解]**

* 函数：`0x56ba0`，4992 字节 / **864 条指令**
* 被调用者（4 个）：`0x9984b0`(5B，5721 调用者)、`0x92ecb0`(791B，180 调用者)、`0x53150`(1585B)、`0x910af0`(168B，345 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×6, `2`×1, `16`×1, `63`×4, `120`×3, `424`×10, `488`×2
* 字段偏移（70 个）：`+0x1`、`+0x2`、`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xcc`、`+0xd0`、`+0xd1`、`+0xd4`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x180`、`+0x188`、`+0x18c`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1bc`、`+0x1c0`、`+0x1c8`、`+0x1d0`、`+0x238`、`+0x240`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.65 `0x6afe10` **[已证实 + 未解]**

* 函数：`0x6afe10`，4918 字节 / **1115 条指令**
* 被调用者（7 个）：`0x998500`(109B，2318 调用者)、`0x9626f0`(1264B)、`0x6bbc30`(739B)、`0x5c8c50`(255B，57 调用者)、`0x9984b0`(5B，5721 调用者)、`0x62f280`(171B，5209 调用者)、`0x979e70`(51B，676 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×60, `2`×12, `3`×8, `4`×17, `48`×3, `56`×6, `63`×14, `120`×14, `136`×3
* 字段偏移（19 个）：`+0x1`、`+0x3`、`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x34`、`+0x38`、`+0x3c`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x64`、`+0x68`、`+0x70`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.66 `0xabec0` **[已证实 + 未解]**

* 函数：`0xabec0`，4882 字节 / **1049 条指令**
* 被调用者（34 个）：`0x504ef0`(207B，10 调用者)、`0x5ce780`(37B)、`0x4fc5a0`(8B，114 调用者)、`0x4fc5b0`(319B，85 调用者)、`0x97a830`(75B，571 调用者)、`0x998500`(109B，2318 调用者)、`0x9296d0`(2241B，7 调用者)、`0x63f2f0`(0B)、`0x4f7030`(4B，17 调用者)、`0x9989a0`(125B，837 调用者)、`0x7c0ef0`(414B，7 调用者)、`0x998fe0`(79B，783 调用者)、`0x979e70`(51B，676 调用者)、`0x8ebec0`(475B)、`0x9984b0`(5B，5721 调用者)、`0x5007c0`(716B，54 调用者)、`0x62f280`(171B，5209 调用者)、`0x910a60`(136B，185 调用者)、`0x4f7040`(5B)、`0x4f7260`(4B)、`0x4f7270`(4B，6 调用者)、`0x4f7600`(9B，50 调用者)、`0x5d38c0`(1500B，51 调用者)、`0x4f7630`(9B)、`0x501650`(8B)、`0x929fa0`(1495B，24 调用者)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x7c0a80`(520B)、`0x8c5090`(147B，133 调用者)、`0x97ab50`(75B，352 调用者)、`0x63f2f8`(0B)、`0x998bc0`(124B，833 调用者)、`0x67fe90`(104B，155 调用者)
* 字符串：`_reduced`、`basic_string::append`
* 浮点常量：无
* 立即数：`1`×4, `2`×2, `3`×5, `4`×5, `7`×1, `8`×2, `15`×2, `16`×18, `18`×1, `24`×13, `25`×1, `48`×6, `64`×1, `112`×1, `216`×4, `568`×2
* 字段偏移（72 个）：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x24`、`+0x28`、`+0x2c`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x69`、`+0x6a`、`+0x6c`、`+0x70`、`+0x78`、`+0x7c`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x110`、`+0x118`、`+0x120`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x180`、`+0x188`、`+0x190`、`+0x1a0`、`+0x1a4`、`+0x1a8`、`+0x1ac`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c8`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1e8`、`+0x1e9`、`+0x1ea`、`+0x1ec`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x208`、`+0x210`、`+0x218`、`+0x220`、`+0x280`、`+0x288`、`+0x290`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.67 `0x8afdb0` **[已证实 + 未解]**

* 函数：`0x8afdb0`，4805 字节 / **1174 条指令**
* 被调用者（10 个）：`0x8c5130`(2087B，13 调用者)、`0x998500`(109B，2318 调用者)、`0x9984b0`(5B，5721 调用者)、`0x9989a0`(125B，837 调用者)、`0x998fe0`(79B，783 调用者)、`0x979e70`(51B，676 调用者)、`0x67fe90`(104B，155 调用者)、`0x998bc0`(124B，833 调用者)、`0x8c5090`(147B，133 调用者)、`0x62f280`(171B，5209 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×2, `3`×4, `4`×12, `6`×3, `16`×24, `24`×16, `48`×16, `64`×12, `104`×2
* 字段偏移（12 个）：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0xb0`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.68 `0x22ad80` **[已证实 + 未解]**

* 函数：`0x22ad80`，4689 字节 / **1083 条指令**
* 被调用者（28 个）：`0x185820`(538B，11 调用者)、`0x229590`(1286B)、`0x9984b0`(5B，5721 调用者)、`0x998500`(109B，2318 调用者)、`0x63f2f8`(0B)、`0x93b6a0`(1400B)、`0x93bc20`(590B，24 调用者)、`0x93c400`(735B)、`0x93c6e0`(590B，19 调用者)、`0x983ca0`(145B，289 调用者)、`0x178670`(1423B)、`0x63f2f0`(0B)、`0x8f3720`(674B)、`0x226920`(319B)、`0x8fdfa0`(437B，13 调用者)、`0x63f2e8`(0B)、`0x998570`(88B，12 调用者)、`0x22aca0`(213B)、`0x9984c0`(5B，12 调用者)、`0x225ac0`(615B)、`0x8f3ab0`(674B)、`0x226e10`(6607B)、`0x97ab50`(75B，352 调用者)、`0x7baf10`(224B)、`0x62f280`(171B，5209 调用者)、`0x229db0`(2143B)、`0x979e70`(51B，676 调用者)、`0x6ac370`(694B，57 调用者)
* 字符串：`vector::_M_range_check: __n (which is %zu) >= this`、`vector::reserve`
* 浮点常量：**1.5**（`0x9c1de8`）、**1**（`0x9c1df8`）
* 立即数：`1`×20, `2`×1, `3`×17, `4`×2, `5`×2, `7`×1, `8`×24, `16`×1, `24`×2, `25`×1, `31`×1, `32`×5, `48`×2, `127`×1, `240`×4, `728`×2, `1024`×4
* 字段偏移（66 个）：`+0x1`、`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x7f`、`+0x80`、`+0x88`、`+0x90`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x140`、`+0x148`、`+0x150`、`+0x158`、`+0x160`、`+0x1b0`、`+0x1e0`、`+0x238`、`+0x268`、`+0x280`、`+0x290`、`+0x2a0`、`+0x2b0`、`+0x2c0`、`+0x320`、`+0x330`、`+0x338`、`+0x340`、`+0x348`、`+0x350`、`+0x358`、`+0x360`、`+0x368`、`+0x370`、`+0x378`、`+0x400`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.69 `0x697270` **[已证实 + 未解]**

* 函数：`0x697270`，4602 字节 / **1136 条指令**
* 被调用者（11 个）：`0x51d090`(4B，53 调用者)、`0x5235d0`(28B，10 调用者)、`0x998500`(109B，2318 调用者)、`0x63f2e8`(0B)、`0x63f2f8`(0B)、`0x63f2f0`(0B)、`0x9984b0`(5B，5721 调用者)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x979e70`(51B，676 调用者)、`0x62f280`(171B，5209 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×21, `2`×44, `3`×10, `4`×14, `8`×8, `13`×1, `16`×12, `32`×8, `34`×1, `56`×1, `115`×1, `134`×1, `280`×2
* 字段偏移（33 个）：`+0x1`、`+0x4`、`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x1c`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x68`、`+0x70`、`+0x78`、`+0x90`、`+0x98`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xed`、`+0xf0`、`+0xf8`、`+0x100`、`+0x178`、`+0x180`、`+0x188`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.70 `0x56b7d0` **[已证实 + 未解]**

* 函数：`0x56b7d0`，4548 字节 / **953 条指令**
* 被调用者（20 个）：`0x5c4c40`(12B，25 调用者)、`0x559ff0`(5B)、`0x5c2e40`(138B，32 调用者)、`0x559fe0`(5B，29 调用者)、`0x5cd800`(610B，113 调用者)、`0x5ce7b0`(50B，32 调用者)、`0x56a840`(308B)、`0x9984b0`(5B，5721 调用者)、`0x5cd1f0`(276B)、`0x998500`(109B，2318 调用者)、`0x8e3940`(2840B)、`0x8c4ff0`(147B，123 调用者)、`0x891b40`(52B，240 调用者)、`0x7b7b00`(243B，8 调用者)、`0x62f280`(171B，5209 调用者)、`0x979e70`(51B，676 调用者)、`0x9989a0`(125B，837 调用者)、`0x998fe0`(79B，783 调用者)、`0x67fe90`(104B，155 调用者)、`0x998bc0`(124B，833 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：无
* 立即数：`1`×8, `3`×6, `4`×6, `16`×12, `24`×8, `48`×8, `104`×5, `232`×2, `712`×2
* 字段偏移（89 个）：`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xb9`、`+0xbc`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x179`、`+0x17c`、`+0x180`、`+0x188`、`+0x190`、`+0x198`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1c8`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1e8`、`+0x1f0`、`+0x1f8`、`+0x208`、`+0x210`、`+0x218`、`+0x220`、`+0x228`、`+0x230`、`+0x238`、`+0x240`、`+0x248`、`+0x250`、`+0x258`、`+0x260`、`+0x268`、`+0x269`、`+0x26c`、`+0x270`、`+0x278`、`+0x280`、`+0x288`、`+0x2a0`、`+0x2b0`、`+0x310`、`+0x318`、`+0x320`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.71 `0x71a370` **[已证实 + 未解]**

* 函数：`0x71a370`，4546 字节 / **813 条指令**
* 被调用者（22 个）：`0x5e5fa0`(178B)、`0x5c61d0`(4B，67 调用者)、`0x5c5f30`(4B，103 调用者)、`0x5e6300`(86B，14 调用者)、`0x701220`(73B，16 调用者)、`0x5c5f40`(5B，81 调用者)、`0x5c5260`(4B，81 调用者)、`0x8d3b40`(540B)、`0x7011c0`(82B，34 调用者)、`0x706970`(1907B)、`0x730300`(4025B)、`0x9984b0`(5B，5721 调用者)、`0x873f20`(75B)、`0x70c940`(141B，32 调用者)、`0x73aec0`(895B)、`0x8f13b0`(253B)、`0x99fea0`(47B，8 调用者)、`0x9989a0`(125B，837 调用者)、`0x998bc0`(124B，833 调用者)、`0x9988c0`(86B，476 调用者)、`0x999030`(108B，476 调用者)、`0x62f280`(171B，5209 调用者)
* 字符串：**一个都没有**（纯算法体）
* 浮点常量：**1**（`0x9dfbc8`）、**1**（`0x9dfbc8`）、**1**（`0x9dfbc8`）
* 立即数：`1`×25, `2`×2, `3`×5, `4`×4, `8`×3, `10`×2, `16`×4, `24`×1, `32`×1, `48`×1, `120`×4, `200`×1, `1144`×2
* 字段偏移（115 个）：`+0x1`、`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x71`、`+0x78`、`+0x80`、`+0x88`、`+0x93`、`+0x94`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x12e`、`+0x12f`、`+0x130`、`+0x140`、`+0x148`、`+0x150`、`+0x160`、`+0x168`、`+0x170`、`+0x180`、`+0x188`、`+0x190`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1c0`、`+0x1d0`、`+0x1e0`、`+0x1e8`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x210`、`+0x218`、`+0x220`、`+0x228`、`+0x230`、`+0x240`、`+0x260`、`+0x270`、`+0x290`、`+0x2a0`、`+0x2a8`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x300`、`+0x308`、`+0x310`、`+0x318`、`+0x320`、`+0x328`、`+0x330`、`+0x338`、`+0x340`、`+0x348`、`+0x350`、`+0x358`、`+0x360`、`+0x368`、`+0x370`、`+0x378`、`+0x380`、`+0x388`、`+0x390`、`+0x398`、`+0x3a0`、`+0x3a8`、`+0x3b0`、`+0x3b8`、`+0x3c0`、`+0x3c1`、`+0x3d0`、`+0x3e0`、`+0x3f0`、`+0x400`、`+0x410`、`+0x420`、`+0x430`、`+0x440`、`+0x450`、`+0x460`、`+0x4c0`、`+0x4c8`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.72 `0x5bf1d0` **[已证实 + 未解]**

* 函数：`0x5bf1d0`，4535 字节 / **921 条指令**
* 被调用者（22 个）：`0x63f370`(0B)、`0x61e510`(221B，13 调用者)、`0x61e7b0`(724B，10 调用者)、`0x612250`(504B，10 调用者)、`0x910af0`(168B，345 调用者)、`0x9984b0`(5B，5721 调用者)、`0x61ea90`(594B，13 调用者)、`0x610bd0`(408B)、`0x97a830`(75B，571 调用者)、`0x618850`(696B，15 调用者)、`0x6197e0`(477B)、`0x913690`(109B，49 调用者)、`0x63f2f8`(0B)、`0x9135d0`(191B，33 调用者)、`0x62f280`(171B，5209 调用者)、`0x9988c0`(86B，476 调用者)、`0x910a60`(136B，185 调用者)、`0x875f00`(67B，6 调用者)、`0x999030`(108B，476 调用者)、`0x875eb0`(65B，8 调用者)、`0x998c70`(41B，420 调用者)、`0x97ab50`(75B，352 调用者)
* 字符串：`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、` directory`、`test tools require to set DATA variable to a valid`
* 浮点常量：无
* 立即数：`1`×14, `2`×1, `3`×2, `7`×7, `9`×1, `10`×1, `12`×1, `16`×42, `116`×1, `616`×2
* 字段偏移（66 个）：`+0x4`、`+0x6`、`+0x8`、`+0x10`、`+0x17`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x50`、`+0x60`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xe0`、`+0xe8`、`+0xf0`、`+0x100`、`+0x108`、`+0x110`、`+0x120`、`+0x128`、`+0x140`、`+0x148`、`+0x150`、`+0x160`、`+0x168`、`+0x170`、`+0x180`、`+0x188`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1c0`、`+0x1c8`、`+0x1d0`、`+0x1d2`、`+0x1e0`、`+0x1e8`、`+0x1f0`、`+0x200`、`+0x208`、`+0x210`、`+0x21c`、`+0x220`、`+0x228`、`+0x230`、`+0x238`、`+0x240`、`+0x248`、`+0x250`、`+0x257`、`+0x258`、`+0x2b0`、`+0x2c0`

**尚未解**：身份、所属 TU、角色。**不给它编名字**。

### 附 6.73 两条新事实 **[已证实]**

* **`0xABEC0`（4,882 B）** 自带字符串 **`'_reduced'`** ⇒ 与 **reduced problem**（`tu.equivalent` 的等价化简、
  `tu.float_filler` 消费的那个）同族 —— 这是该族第三条独立证据（前两条：`0x68F750` 的
  `m_reduced_problem.GetNumberOfParts()` 与 `0xABEC0` 的 `_reduced` 名片段）。
* **`0x5BF1D0`（4,535 B）** 自带字符串 **`'test tools require to set DATA variable to a valid'`** 与
  `' directory'` ⇒ **原库还带测试工具代码，而且从导出可达**。这条值得单独记：它意味着"从 168 个导出
  可达"的集合里**包含测试/诊断代码**，评估完成度时应当把这类排除或单列，而不是当成领域算法。
  **[已证实为字符串；"是测试工具"为直接结论]**

### 附 7 `0x68ab50` **[已证实 + 未解]**

* 函数：`0x68ab50`，13071 字节 / **2574 条指令**
* 被调用者（48 个）：`0x693520`(634B)、`0x7c1430`(2235B，33 调用者)、`0x51e7e0`(1294B，47 调用者)、`0x4fc5a0`(8B，114 调用者)、`0x51d0c0`(5B，103 调用者)、`0x520440`(479B，56 调用者)、`0x4f76a0`(4B，57 调用者)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x9984b0`(5B，5721 调用者)、`0x97a830`(75B，571 调用者)、`0x63f2f8`(0B)、`0x998500`(109B，2318 调用者)、`0x92dee0`(1148B，49 调用者)、`0x63f2f0`(0B)、`0x520620`(4B)、`0x51f470`(549B，20 调用者)、`0x5f3900`(22B，58 调用者)、`0x60cb0`(51B)、`0x267020`(8B)、`0x5f3980`(10B，44 调用者)、`0x51cff0`(159B，21 调用者)、`0x51cab0`(478B，18 调用者)、`0x51d310`(5B，20 调用者)、`0x51fde0`(30B，18 调用者)、`0x92ecb0`(791B，180 调用者)、`0x5f3960`(17B，77 调用者)、`0x5235f0`(54B，28 调用者)、`0x5228e0`(54B)、`0x64330`(28B，21 调用者)、`0x430e0`(147B，7 调用者)、`0x910af0`(168B，345 调用者)、`0x8e6400`(1770B，29 调用者)、`0x8ea9d0`(335B，25 调用者)、`0x92e360`(2378B，22 调用者)、`0x8e1fb0`(744B，27 调用者)、`0x8ea720`(423B，25 调用者)、`0x8e7af0`(338B，21 调用者)、`0xaaa60`(177B，7 调用者)、`0x8e5ce0`(815B，17 调用者)、`0x9989a0`(125B，837 调用者)、`0x7bb7a0`(54B，56 调用者)、`0x998fe0`(79B，783 调用者)、`0x8e6390`(107B，48 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x62f280`(171B，5209 调用者)、`0x998bc0`(124B，833 调用者)、`0x979e70`(51B，676 调用者)
* 字符串：`index < m_reduced_problem.GetNumberOfParts()`、`ReducedPartNumber`、`..\multi\float_filler.cpp`、`index < m_reduced_problem.GetNumberOfParts()`、`ReducedPartNumber`、`..\multi\float_filler.cpp`
* 浮点常量：无
* 立即数：`1`×23, `3`×10, `4`×6, `14`×1, `15`×10, `16`×41, `17`×1, `18`×2, `20`×1, `24`×6, `25`×3, `50`×1, `93`×2, `104`×7, `112`×4, `115`×1, `120`×18, `126`×1, `174`×1, `2392`×2, `10536`×3
* 字段偏移（196 个）：`+0x4`、`+0x8`、`+0x10`、`+0x18`、`+0x1c`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x54`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa8`、`+0xaf`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x180`、`+0x189`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1b0`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1f0`、`+0x210`、`+0x230`、`+0x250`、`+0x270`、`+0x290`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2f0`、`+0x2f8`、`+0x300`、`+0x310`、`+0x318`、`+0x320`、`+0x330`、`+0x338`、`+0x340`、`+0x350`、`+0x358`、`+0x360`、`+0x370`、`+0x37a`、`+0x390`、`+0x398`、`+0x3a0`、`+0x3b0`、`+0x3b8`、`+0x3c0`、`+0x3c8`、`+0x3d0`、`+0x3d4`、`+0x3d8`、`+0x3e0`、`+0x3f0`、`+0x3f8`、`+0x400`、`+0x408`、`+0x410`、`+0x418`、`+0x420`、`+0x424`、`+0x428`、`+0x430`、`+0x438`、`+0x450`、`+0x478`、`+0x480`、`+0x490`、`+0x4c8`、`+0x508`、`+0x550`、`+0x570`、`+0x590`、`+0x598`、`+0x5a0`、`+0x5b0`、`+0x5b8`、`+0x5c0`、`+0x5c8`、`+0x5d0`、`+0x5d8`、`+0x5e0`、`+0x5e8`、`+0x600`、`+0x608`、`+0x610`、`+0x618`、`+0x620`、`+0x628`、`+0x62c`、`+0x630`、`+0x631`、`+0x634`、`+0x638`、`+0x640`、`+0x648`、`+0x650`、`+0x658`、`+0x660`、`+0x668`、`+0x670`、`+0x678`、`+0x680`、`+0x688`、`+0x690`、`+0x698`、`+0x6a0`、`+0x6a8`、`+0x6b0`、`+0x6b8`、`+0x6c0`、`+0x6d0`、`+0x6d8`、`+0x6e0`、`+0x6f0`、`+0x6f8`、`+0x700`、`+0x708`、`+0x710`、`+0x718`、`+0x720`、`+0x728`、`+0x740`、`+0x748`、`+0x750`、`+0x758`、`+0x760`、`+0x768`、`+0x76c`、`+0x770`、`+0x771`、`+0x774`、`+0x778`、`+0x780`、`+0x788`、`+0x790`、`+0x798`、`+0x7a0`、`+0x7a8`、`+0x7b0`、`+0x7b8`、`+0x7c0`、`+0x7c8`、`+0x7d0`、`+0x7d8`、`+0x7e0`、`+0x7e8`、`+0x7f0`、`+0x7f8`

**尚未解**：身份/角色未定；不给它编名字。

### 附 7 `0x6a3c80` **[已证实 + 未解]**

* 函数：`0x6a3c80`，11549 字节 / **2357 条指令**
* 被调用者（116 个）：`0x62ebe0`(0B)、`0x2fcd0`(151B)、`0x2fdd0`(129B，6 调用者)、`0x2fe60`(129B，6 调用者)、`0x5f3900`(22B，58 调用者)、`0x7d4b00`(3037B)、`0x5f4310`(35B，45 调用者)、`0x62730`(177B，11 调用者)、`0x51bfc0`(67B，34 调用者)、`0x4fc2e0`(14B，52 调用者)、`0x69db70`(3638B)、`0x8eee40`(328B，44 调用者)、`0x92ecb0`(791B，180 调用者)、`0x6a1180`(1230B)、`0x6a1650`(2873B)、`0x66b80`(37B)、`0x6a2a50`(4647B)、`0x62830`(84B)、`0x51c790`(743B，6 调用者)、`0x9984b0`(5B，5721 调用者)、`0xaf1f0`(792B)、`0x5f3980`(10B，44 调用者)、`0x30420`(180B)、`0xaef10`(12B，12 调用者)、`0x305b0`(1035B)、`0x62ac0`(369B)、`0x605660`(28B)、`0x978010`(959B，421 调用者)、`0x868f70`(545B，60 调用者)、`0x2fc90`(54B)、`0x605bf0`(1395B，7 调用者)、`0xae6b0`(477B)、`0x605680`(1379B，16 调用者)、`0x522920`(114B)、`0x522a40`(64B，7 调用者)、`0x528bf0`(275B，6 调用者)、`0x523980`(187B)、`0x8688e0`(545B，125 调用者)、`0xb50b0`(3B)、`0x6c0f0`(6B)、`0x627f0`(60B，12 调用者)、`0x51d320`(416B，17 调用者)、`0x910a60`(136B，185 调用者)、`0x529c40`(360B)、`0x90ecb0`(650B，185 调用者)、`0x6c0e0`(5B，19 调用者)、`0x867bf0`(337B，157 调用者)、`0x867df0`(180B，171 调用者)、`0x82b7b0`(494B，58 调用者)、`0x309c0`(103B)、`0x8aabc0`(41B，257 调用者)、`0x9445e0`(87B，237 调用者)、`0xaef80`(622B，14 调用者)、`0x5f4340`(140B，67 调用者)、`0x874220`(75B，22 调用者)、`0x5f3960`(17B，77 调用者)、`0x51c020`(4B，33 调用者)、`0x51d090`(4B，53 调用者)、`0x60a620`(2620B，680 调用者)、`0xaddf0`(577B，8 调用者)、`0x523050`(174B，33 调用者)、`0xad5e0`(75B，8 调用者)、`0x51d2f0`(5B，102 调用者)、`0x4f8390`(420B，35 调用者)、`0x69e9b0`(6606B，6 调用者)、`0x51d0c0`(5B，103 调用者)、`0x7c1430`(2235B，33 调用者)、`0x526690`(7B，9 调用者)、`0x6a0380`(185B)、`0x51faf0`(743B，16 调用者)、`0x51c030`(530B，30 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x2fd70`(93B)、`0x63f2f8`(0B)、`0x899820`(1426B，13 调用者)、`0x303c0`(94B)、`0xaf6a0`(28B)、`0x4fc230`(12B，9 调用者)、`0x9878c0`(112B，67 调用者)、`0x91fd80`(121B，91 调用者)、`0x8ef0e0`(7416B，13 调用者)、`0x92f060`(272B，16 调用者)、`0x609e20`(221B，9 调用者)、`0x97a090`(1599B，17 调用者)、`0x8264e0`(136B，200 调用者)、`0xb50e0`(3B)、`0xb50d0`(3B)、`0xb50c0`(3B)、`0x8691a0`(545B，26 调用者)、`0x5231e0`(127B)、`0x4fc320`(11B，7 调用者)、`0x998500`(109B，2318 调用者)、`0x92dee0`(1148B，49 调用者)、`0x6be30`(97B)、`0x4fc5a0`(8B，114 调用者)、`0x69f90`(65B)、`0x326a0`(90B)、`0x522250`(327B)、`0x5d830`(5167B)、`0xaef30`(10B)、`0xaef20`(10B)、`0x4fc380`(10B，14 调用者)、`0x57ad10`(289B)、`0x51c010`(4B，21 调用者)、`0x16bb20`(670B)、`0x8ee020`(1610B，19 调用者)、`0x97ab50`(75B，352 调用者)、`0x696390`(357B)、`0x62f280`(171B，5209 调用者)、`0x978750`(51B，300 调用者)、`0x979e70`(51B，676 调用者)、`0x9989a0`(125B，837 调用者)、`0x998fe0`(79B，783 调用者)、`0x525370`(107B，13 调用者)、`0xad630`(478B，6 调用者)、`0x998bc0`(124B，833 调用者)
* 字符串：`iter`、` evaluation_ratio: `、` #sheets: `、` #parts: `、` dim: `、`strategy`、`, ...`、`properties.base_solution().empty()`
* 浮点常量：**1**（`0x9b11d0`）、**0.5**（`0x9b11d8`）、**0.2**（`0x9b1238`）、**1**（`0x9b11d0`）、**0.0001**（`0x9b1278`）、**0.0001**（`0x9b1278`）、**1.5**（`0x9b1270`）、**0.9**（`0x9b1260`）、**0.8**（`0x9b1258`）、**0.6**（`0x9b1250`）、**0.8**（`0x9b1258`）、**1.1**（`0x9b1268`）、**0.9**（`0x9b1260`）
* 立即数：`1`×32, `2`×14, `3`×9, `4`×5, `5`×2, `6`×1, `7`×3, `8`×1, `9`×1, `10`×6, `12`×2, `14`×1, `16`×72, `17`×1, `19`×1, `20`×2, `23`×1, `24`×1, `28`×1, `30`×1, `64`×2, `176`×1, `200`×1, `312`×7, `360`×1, `624`×2, `895`×1, `1000`×2, `1272`×1, `2504`×1, `5192`×2
* 字段偏移（146 个）：`+0x1`、`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x2c`、`+0x30`、`+0x38`、`+0x40`、`+0x43`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa6`、`+0xa7`、`+0xa8`、`+0xb0`、`+0xc0`、`+0xd0`、`+0xe0`、`+0xf0`、`+0x100`、`+0x108`、`+0x120`、`+0x140`、`+0x160`、`+0x180`、`+0x1a0`、`+0x1a8`、`+0x1c0`、`+0x1c8`、`+0x1e0`、`+0x1e8`、`+0x200`、`+0x208`、`+0x220`、`+0x228`、`+0x240`、`+0x248`、`+0x260`、`+0x268`、`+0x270`、`+0x274`、`+0x278`、`+0x280`、`+0x288`、`+0x2a0`、`+0x2b5`、`+0x2c0`、`+0x2dc`、`+0x2e0`、`+0x2e9`、`+0x2ec`、`+0x2f0`、`+0x300`、`+0x320`、`+0x330`、`+0x340`、`+0x34c`、`+0x358`、`+0x360`、`+0x370`、`+0x380`、`+0x388`、`+0x3a0`、`+0x3c0`、`+0x3c8`、`+0x3d0`、`+0x3d4`、`+0x3d8`、`+0x3e0`、`+0x3e8`、`+0x3f0`、`+0x3f8`、`+0x400`、`+0x408`、`+0x420`、`+0x440`、`+0x460`、`+0x480`、`+0x490`、`+0x4a0`、`+0x4c0`、`+0x4e0`、`+0x4e8`、`+0x4f0`、`+0x500`、`+0x508`、`+0x510`、`+0x518`、`+0x520`、`+0x530`、`+0x538`、`+0x540`、`+0x548`、`+0x560`、`+0x568`、`+0x570`、`+0x578`、`+0x580`、`+0x588`、`+0x590`、`+0x598`、`+0x5b0`、`+0x5b8`、`+0x5c0`、`+0x5c8`、`+0x5d0`、`+0x5d8`、`+0x5e0`、`+0x5e8`、`+0x600`、`+0x608`、`+0x610`、`+0x618`、`+0x620`、`+0x628`、`+0x630`、`+0x650`、`+0x670`、`+0x678`、`+0x680`、`+0x688`、`+0x698`、`+0x6a0`、`+0x6a8`、`+0x6b0`、`+0x6b8`、`+0x6c0`、`+0x710`、`+0x770`、`+0x778`、`+0x780`、`+0x788`、`+0x7a0`

**尚未解**：身份/角色未定；不给它编名字。

### 附 7 `0x4c8670` **[已证实 + 未解]**

* 函数：`0x4c8670`，13786 字节 / **2784 条指令**
* 被调用者（49 个）：`0x51d2f0`(5B，102 调用者)、`0x4f8350`(4B，11 调用者)、`0x4c4bf0`(550B)、`0x82a3e0`(109B，51 调用者)、`0x9984b0`(5B，5721 调用者)、`0x51d090`(4B，53 调用者)、`0x97a830`(75B，571 调用者)、`0x998500`(109B，2318 调用者)、`0x92dee0`(1148B，49 调用者)、`0x63f2f0`(0B)、`0x51d300`(4B，18 调用者)、`0x910ba0`(109B，1002 调用者)、`0x63f2f8`(0B)、`0x8ee020`(1610B，19 调用者)、`0x9989a0`(125B，837 调用者)、`0x7bb7a0`(54B，56 调用者)、`0x998fe0`(79B，783 调用者)、`0x8eee40`(328B，44 调用者)、`0x62f280`(171B，5209 调用者)、`0x935910`(605B)、`0x4c4e20`(1532B)、`0x51d0c0`(5B，103 调用者)、`0x63f300`(0B)、`0x979fe0`(5B，165 调用者)、`0x987220`(702B，126 调用者)、`0x5203d0`(19B，45 调用者)、`0x5203f0`(19B，33 调用者)、`0x5cee50`(527B，52 调用者)、`0x5ce7b0`(50B，32 调用者)、`0x5ce970`(269B，38 调用者)、`0x51cff0`(159B，21 调用者)、`0x5ced50`(196B，24 调用者)、`0x5d2a40`(19B，17 调用者)、`0x5d2900`(186B，28 调用者)、`0x520440`(479B，56 调用者)、`0x520200`(286B)、`0x51f470`(549B，20 调用者)、`0x51cc90`(312B，17 调用者)、`0x92ecb0`(791B，180 调用者)、`0x51bfc0`(67B，34 调用者)、`0x51c4a0`(5B，8 调用者)、`0x51ca80`(30B，8 调用者)、`0x51d0a0`(31B，17 调用者)、`0x520320`(159B，17 调用者)、`0x520420`(27B)、`0x910af0`(168B，345 调用者)、`0x8e6390`(107B，48 调用者)、`0x979e70`(51B，676 调用者)、`0x998bc0`(124B，833 调用者)
* 字符串：`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`、`basic_string::_M_construct null not valid`
* 浮点常量：无
* 立即数：`1`×22, `3`×16, `4`×9, `8`×1, `15`×11, `16`×21, `24`×9, `31`×1, `80`×1, `104`×9, `112`×1, `120`×15, `312`×8, `1624`×2
* 字段偏移（146 个）：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x54`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa8`、`+0xac`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x180`、`+0x188`、`+0x190`、`+0x1a0`、`+0x1b0`、`+0x1c0`、`+0x1d0`、`+0x1e0`、`+0x1f0`、`+0x1f8`、`+0x200`、`+0x210`、`+0x218`、`+0x220`、`+0x230`、`+0x250`、`+0x258`、`+0x260`、`+0x270`、`+0x278`、`+0x280`、`+0x288`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2a8`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x300`、`+0x330`、`+0x360`、`+0x390`、`+0x3c0`、`+0x3f0`、`+0x410`、`+0x418`、`+0x420`、`+0x428`、`+0x430`、`+0x438`、`+0x440`、`+0x448`、`+0x450`、`+0x458`、`+0x460`、`+0x468`、`+0x490`、`+0x4e8`、`+0x510`、`+0x518`、`+0x520`、`+0x528`、`+0x530`、`+0x538`、`+0x540`、`+0x548`、`+0x550`、`+0x558`、`+0x560`、`+0x568`、`+0x570`、`+0x588`、`+0x590`、`+0x598`、`+0x5a0`、`+0x5a8`、`+0x5ac`、`+0x5b0`、`+0x5b1`、`+0x5b4`、`+0x5b8`、`+0x5c0`、`+0x5c8`、`+0x5d0`、`+0x5d8`、`+0x5e0`、`+0x5e8`、`+0x5f0`、`+0x5f8`、`+0x600`、`+0x608`、`+0x610`、`+0x618`、`+0x620`、`+0x628`、`+0x630`、`+0x638`、`+0x640`、`+0x6a0`、`+0x6a8`、`+0x6b0`

**尚未解**：身份/角色未定；不给它编名字。

### 附 7 `0x6f8f30` **[已证实 + 未解]**

* 函数：`0x6f8f30`，13410 字节 / **3214 条指令**
* 被调用者（8 个）：`0x63f3f0`(0B)、`0x63f2b0`(0B)、`0x998500`(109B，2318 调用者)、`0x9984b0`(5B，5721 调用者)、`0x888f50`(65B，19 调用者)、`0x6e9ad0`(108B)、`0x889070`(80B，37 调用者)、`0x62f280`(171B，5209 调用者)
* 字符串：`sha1 too many bytes`、`C:\Users\renaud\nest\external\boost_1_63_0/boost/u`、`void boost::uuids::detail::sha1::process_byte(unsi`、`sha1 too many bytes`、`C:\Users\renaud\nest\external\boost_1_63_0/boost/u`、`void boost::uuids::detail::sha1::process_byte(unsi`、`sha1 too many bytes`、`C:\Users\renaud\nest\external\boost_1_63_0/boost/u`
* 浮点常量：无
* 立即数：`1`×127, `2`×18, `3`×17, `4`×19, `5`×16, `7`×1, `8`×41, `12`×17, `16`×26, `19`×16, `20`×3, `24`×11, `39`×16, `56`×3, `57`×1, `59`×16, `64`×15, `79`×16, `80`×16, `104`×13, `128`×1, `696`×2
* 字段偏移（72 个）：`+0x1`、`+0x4`、`+0x8`、`+0xc`、`+0x10`、`+0x13`、`+0x14`、`+0x18`、`+0x1c`、`+0x20`、`+0x28`、`+0x2c`、`+0x30`、`+0x34`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x64`、`+0x68`、`+0x6c`、`+0x70`、`+0x80`、`+0x84`、`+0x88`、`+0xa0`、`+0xb3`、`+0xb4`、`+0xb8`、`+0xbc`、`+0xc0`、`+0xc4`、`+0xc8`、`+0xcc`、`+0xd0`、`+0xd4`、`+0xd8`、`+0xdc`、`+0xe0`、`+0xe4`、`+0xe8`、`+0xec`、`+0xee`、`+0xef`、`+0xf0`、`+0xf1`、`+0xf2`、`+0xf3`、`+0x110`、`+0x114`、`+0x118`、`+0x11c`、`+0x120`、`+0x124`、`+0x128`、`+0x12c`、`+0x130`、`+0x134`、`+0x138`、`+0x13c`、`+0x140`、`+0x144`、`+0x148`、`+0x14c`、`+0x250`、`+0x260`、`+0x270`、`+0x280`、`+0x290`、`+0x2a0`、`+0x300`

**尚未解**：身份/角色未定；不给它编名字。

### 附 7 `0x2a3520` **[已证实 + 未解]**

* 函数：`0x2a3520`，12744 字节 / **2026 条指令**
* 被调用者（17 个）：`0x9984a0`(5B，653 调用者)、`0x90f5e0`(263B，29 调用者)、`0x63f238`(0B)、`0x9109e0`(95B，25 调用者)、`0x477cd0`(104B)、`0x82a3e0`(109B，51 调用者)、`0x4798b0`(573B)、`0x475370`(73B，14 调用者)、`0x9984b0`(5B，5721 调用者)、`0x9984e0`(5B，587 调用者)、`0x47b790`(142B)、`0x4797b0`(92B)、`0x47b680`(188B，8 调用者)、`0x479010`(90B)、`0x63f2f8`(0B)、`0x62f280`(171B，5209 调用者)、`0x9990a0`(51B，449 调用者)
* 字符串：`exmip1`、`AUATUWVSH`、`p0033`、`flugpl`、`enigma`、`mod011`、`probing`、`mas76`
* 浮点常量：**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**6**（`0x9c5a10`）、**16**（`0x9c5a20`）、**7**（`0x9c5a30`）、**12**（`0x9c5a40`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**4**（`0x9c5ac0`）、**4**（`0x9c5ad0`）、**6**（`0x9c5ae0`）、**25**（`0x9c5af0`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9a44e0`）、**1**（`0x9a4800`）、**1**（`0x9a4be0`）、**1**（`0x9a5300`）、**1**（`0x9a5a60`）、**1**（`0x9a6200`）、**1**（`0x9c5a08`）、**1**（`0x9a68c0`）、**1**（`0x9a6ba0`）、**1**（`0x9a6d80`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9a6ec0`）、**2**（`0x9a7000`）、**1**（`0x9c5a08`）
* 立即数：`1`×123, `2`×28, `3`×21, `4`×9, `5`×4, `6`×6, `7`×15, `8`×19, `9`×6, `10`×5, `11`×5, `12`×3, `13`×8, `14`×3, `15`×4, `16`×9, `17`×5, `18`×10, `19`×4, `20`×3, `21`×6, `22`×6, `23`×2, `24`×5, `25`×8, `26`×5, `27`×5, `28`×6, `29`×9, `30`×2, `31`×7, `32`×3, `33`×7, `34`×5, `35`×5, `36`×5, `37`×4, `38`×2, `39`×4, `40`×6, `41`×3, `42`×5, `43`×3, `44`×4, `45`×3, `46`×4, `47`×5, `48`×5, `49`×2, `50`×2, `51`×3, `52`×6, `53`×4, `54`×2, `55`×1, `56`×2, `57`×2, `58`×2, `59`×4, `60`×4, `61`×3, `62`×3, `63`×2, `64`×3, `65`×3, `66`×2, `67`×1, `71`×1, `73`×2, `74`×2, `75`×1, `77`×1, `79`×1, `82`×1, `83`×1, `85`×2, `86`×1, `89`×1, `92`×1, `93`×2, `94`×1, `99`×1, `100`×1, `102`×1, `103`×1, `104`×1, `110`×1, `111`×1, `114`×2, `116`×2, `118`×1, `119`×1, `123`×2, `127`×1, `128`×3, `132`×2, `133`×1, `134`×1, `136`×1, `138`×1, `140`×1, `141`×1, `144`×1, `146`×2, `147`×2, `148`×2, `149`×1, `150`×1, `151`×3, `152`×1, `154`×1, `155`×1, `157`×2, `160`×3, `164`×3, `166`×1, `170`×1, `173`×1, `177`×1, `179`×2, `180`×2, `181`×3, `182`×2, `183`×2, `184`×1, `185`×3, `188`×1, `190`×1, `192`×1, `193`×2, `194`×1, `195`×2, `196`×1, `197`×1, `199`×1, `200`×2, `201`×1, `202`×1, `204`×2, `205`×1, `206`×2, `208`×2, `209`×1, `212`×1, `213`×2, `216`×2, `218`×1, `219`×1, `220`×4, `222`×2, `226`×1, `229`×1, `230`×1, `231`×1, `232`×2, `234`×1, `235`×1, `236`×1, `240`×2, `243`×2, `244`×1, `245`×2, `247`×1, `248`×1, `249`×1, `250`×1, `251`×2, `253`×1, `254`×1, `255`×1, `256`×1, `257`×1, `258`×1, `260`×2, `262`×2, `263`×1, `264`×2, `266`×1, `267`×1, `268`×1, `269`×1, `272`×1, `273`×1, `274`×1, `278`×1, `282`×2, `284`×1, `286`×1, `287`×1, `288`×2, `289`×1, `292`×1, `294`×1, `319`×2, `320`×1, `353`×1, `375`×1, `378`×1, `383`×1, `384`×1, `408`×1, `413`×1, `422`×1, `423`×1, `424`×1, `464`×2, `480`×1, `508`×1, `521`×1, `533`×1, `537`×1, `548`×2, `552`×1, `574`×1, `584`×2, `604`×1, `628`×1, `688`×1, `690`×1, `693`×1, `712`×1, `724`×1, `753`×1, `773`×1, `778`×1, `783`×1, `840`×1, `847`×1, `852`×1, `870`×1, `878`×1, `1152`×1, `1168`×1, `1208`×1, `1224`×1, `1256`×1, `1298`×1, `1350`×1, `1372`×2, `1448`×1, `1532`×1, `1541`×1, `1557`×1, `1560`×1, `1561`×1, `1580`×1, `1585`×1, `1588`×1, `1589`×1, `1614`×1, `1615`×1, `1616`×1, `1617`×1, `1626`×1, `1630`×1, `1631`×1, `1642`×1, `1643`×1, `1644`×1, `1645`×1, `1650`×1, `1654`×1, `1658`×1, `1659`×1, `1696`×1, `1792`×1, `1808`×1, `1886`×1, `1980`×1, `1989`×1, `2025`×1, `2032`×1, `2655`×1, `2756`×1, `2984`×2, `6000`×1, `7195`×1, `7548`×1, `8904`×1, `9502`×1, `9505`×1, `9507`×1, `9511`×1, `9512`×1, `9513`×1, `9514`×1, `9515`×1, `9516`×1, `9521`×1, `9522`×1, `9526`×1, `9534`×1, `9535`×1, `9536`×1, `9537`×1, `9542`×1, `9543`×1, `9544`×1, `9548`×1, `9550`×1, `9554`×1, `9557`×1, `10724`×1, `10757`×1, `10958`×1
* 字段偏移（76 个）：`+0x1`、`+0x2`、`+0x3`、`+0x4`、`+0x5`、`+0x6`、`+0x7`、`+0x8`、`+0xe`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x50`、`+0x70`、`+0x78`、`+0x80`、`+0xa0`、`+0xa4`、`+0xa8`、`+0xac`、`+0xb0`、`+0xb4`、`+0xb8`、`+0xbc`、`+0xc0`、`+0xc4`、`+0xc8`、`+0xcc`、`+0xd0`、`+0xd4`、`+0xd8`、`+0xdc`、`+0xe0`、`+0xe4`、`+0xf0`、`+0x150`、`+0x198`、`+0x1c0`、`+0x208`、`+0x218`、`+0x380`、`+0x384`、`+0x388`、`+0x38c`、`+0x390`、`+0x394`、`+0x398`、`+0x39c`、`+0x3a0`、`+0x3a4`、`+0x3a8`、`+0x3ac`、`+0x3b0`、`+0x3b4`、`+0x3b8`、`+0x3bc`、`+0x3c0`、`+0x3c4`、`+0x3c8`、`+0x3cc`、`+0x3d0`、`+0x3d4`、`+0x3d8`、`+0x3dc`、`+0x3e0`、`+0x3e4`、`+0x3e8`、`+0x3ec`、`+0x3f0`、`+0x3f4`、`+0x4d8`、`+0x4e8`

**尚未解**：身份/角色未定；不给它编名字。

### 附 7 `0x446920` **[已证实 + 未解]**

* 函数：`0x446920`，15271 字节 / **3014 条指令**
* 被调用者（41 个）：`0x437260`(181B)、`0x3f5070`(1131B)、`0x438000`(618B)、`0x4197d0`(803B，100 调用者)、`0x41b850`(657B，38 调用者)、`0x41b320`(329B，72 调用者)、`0x41a3d0`(455B，100 调用者)、`0x63f238`(0B)、`0x90ecb0`(650B，185 调用者)、`0x910a60`(136B，185 调用者)、`0x90f9e0`(72B，27 调用者)、`0x640ec0`(361B，15 调用者)、`0x9984e0`(5B，587 调用者)、`0x63f2f8`(0B)、`0x90f5e0`(263B，29 调用者)、`0x63f2e8`(0B)、`0x4348f0`(82B)、`0x998500`(109B，2318 调用者)、`0x974520`(581B，8 调用者)、`0x63f2f0`(0B)、`0x9984b0`(5B，5721 调用者)、`0x63f258`(0B)、`0x434a10`(3839B)、`0x437320`(1666B)、`0x4379b0`(1602B)、`0x434810`(34B，7 调用者)、`0x63f270`(0B)、`0x434540`(708B)、`0x434950`(177B)、`0x9984a0`(5B，653 调用者)、`0x43d740`(3871B)、`0x435910`(3871B)、`0x97a830`(75B，571 调用者)、`0x910ba0`(109B，1002 调用者)、`0x63f390`(0B)、`0x63f268`(0B)、`0x62f280`(171B，5209 调用者)、`0x437240`(27B)、`0x9990a0`(51B，449 调用者)、`0x97ab50`(75B，352 调用者)、`0x63f310`(0B)
* 字符串：`row`、`NAME          `、`  FREE`、`OBJROW`、`COLUMNS`、`  IEEE`、`%d,%d,`、`%d,%d,`
* 浮点常量：**1**（`0x9d5ce0`）、**1**（`0x9d5ce0`）、**1**（`0x9d5ce0`）、**1**（`0x9d5ce0`）
* 立即数：`1`×97, `2`×34, `3`×23, `4`×32, `5`×13, `6`×8, `7`×20, `8`×38, `10`×1, `13`×3, `14`×1, `15`×3, `16`×35, `32`×7, `44`×2, `48`×3, `61`×6, `63`×2, `64`×1, `67`×1, `69`×2, `71`×4, `76`×3, `82`×5, `271`×1, `1016`×2, `8224`×5
* 字段偏移（97 个）：`+0x1`、`+0x2`、`+0x3`、`+0x4`、`+0x5`、`+0x6`、`+0x7`、`+0x8`、`+0xa`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x2c`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x4c`、`+0x50`、`+0x58`、`+0x60`、`+0x64`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xfb`、`+0xfc`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x124`、`+0x128`、`+0x130`、`+0x138`、`+0x148`、`+0x14c`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x180`、`+0x1a0`、`+0x1c0`、`+0x1e0`、`+0x200`、`+0x220`、`+0x228`、`+0x230`、`+0x240`、`+0x248`、`+0x250`、`+0x260`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2a3`、`+0x2a4`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2d0`、`+0x2d1`、`+0x2d2`、`+0x2d3`、`+0x2d4`、`+0x2d5`、`+0x2d6`、`+0x2d7`、`+0x2d8`、`+0x3a0`、`+0x3b0`、`+0x3c0`、`+0x3d0`、`+0x3e0`、`+0x440`、`+0x460`、`+0x468`、`+0x470`、`+0x478`

**尚未解**：身份/角色未定；不给它编名字。

### 附 8.x `0x68ab50` **[已证实 + 未解]**

* 函数：`0x68ab50`，13071 字节 / **2574 条指令**
* 被调用者（48 个）：`0x693520`(634B)、`0x7c1430`(2235B，33 调用者)、`0x51e7e0`(1294B，47 调用者)、`0x4fc5a0`(8B，114 调用者)、`0x51d0c0`(5B，103 调用者)、`0x520440`(479B，56 调用者)、`0x4f76a0`(4B，57 调用者)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x9984b0`(5B，5721 调用者)、`0x97a830`(75B，571 调用者)、`0x63f2f8`(0B)、`0x998500`(109B，2318 调用者)、`0x92dee0`(1148B，49 调用者)、`0x63f2f0`(0B)、`0x520620`(4B)、`0x51f470`(549B，20 调用者)、`0x5f3900`(22B，58 调用者)、`0x60cb0`(51B)、`0x267020`(8B)、`0x5f3980`(10B，44 调用者)、`0x51cff0`(159B，21 调用者)、`0x51cab0`(478B，18 调用者)、`0x51d310`(5B，20 调用者)、`0x51fde0`(30B，18 调用者)、`0x92ecb0`(791B，180 调用者)、`0x5f3960`(17B，77 调用者)、`0x5235f0`(54B，28 调用者)、`0x5228e0`(54B)、`0x64330`(28B，21 调用者)、`0x430e0`(147B，7 调用者)、`0x910af0`(168B，345 调用者)、`0x8e6400`(1770B，29 调用者)、`0x8ea9d0`(335B，25 调用者)、`0x92e360`(2378B，22 调用者)、`0x8e1fb0`(744B，27 调用者)、`0x8ea720`(423B，25 调用者)、`0x8e7af0`(338B，21 调用者)、`0xaaa60`(177B，7 调用者)、`0x8e5ce0`(815B，17 调用者)、`0x9989a0`(125B，837 调用者)、`0x7bb7a0`(54B，56 调用者)、`0x998fe0`(79B，783 调用者)、`0x8e6390`(107B，48 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x62f280`(171B，5209 调用者)、`0x998bc0`(124B，833 调用者)、`0x979e70`(51B，676 调用者)
* 字符串：`index < m_reduced_problem.GetNumberOfParts()`、`ReducedPartNumber`、`..\multi\float_filler.cpp`、`index < m_reduced_problem.GetNumberOfParts()`、`ReducedPartNumber`、`..\multi\float_filler.cpp`
* 浮点常量：无
* 立即数：`1`×23, `3`×10, `4`×6, `14`×1, `15`×10, `16`×41, `17`×1, `18`×2, `20`×1, `24`×6, `25`×3, `50`×1, `93`×2, `104`×7, `112`×4, `115`×1, `120`×18, `126`×1, `174`×1, `2392`×2, `10536`×3
* 字段偏移（196 个）：`+0x4`、`+0x8`、`+0x10`、`+0x18`、`+0x1c`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x54`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0x9c`、`+0xa0`、`+0xa1`、`+0xa4`、`+0xa8`、`+0xaf`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x180`、`+0x189`、`+0x190`、`+0x198`、`+0x1a0`、`+0x1b0`、`+0x1d0`、`+0x1d8`、`+0x1e0`、`+0x1f0`、`+0x210`、`+0x230`、`+0x250`、`+0x270`、`+0x290`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2f0`、`+0x2f8`、`+0x300`、`+0x310`、`+0x318`、`+0x320`、`+0x330`、`+0x338`、`+0x340`、`+0x350`、`+0x358`、`+0x360`、`+0x370`、`+0x37a`、`+0x390`、`+0x398`、`+0x3a0`、`+0x3b0`、`+0x3b8`、`+0x3c0`、`+0x3c8`、`+0x3d0`、`+0x3d4`、`+0x3d8`、`+0x3e0`、`+0x3f0`、`+0x3f8`、`+0x400`、`+0x408`、`+0x410`、`+0x418`、`+0x420`、`+0x424`、`+0x428`、`+0x430`、`+0x438`、`+0x450`、`+0x478`、`+0x480`、`+0x490`、`+0x4c8`、`+0x508`、`+0x550`、`+0x570`、`+0x590`、`+0x598`、`+0x5a0`、`+0x5b0`、`+0x5b8`、`+0x5c0`、`+0x5c8`、`+0x5d0`、`+0x5d8`、`+0x5e0`、`+0x5e8`、`+0x600`、`+0x608`、`+0x610`、`+0x618`、`+0x620`、`+0x628`、`+0x62c`、`+0x630`、`+0x631`、`+0x634`、`+0x638`、`+0x640`、`+0x648`、`+0x650`、`+0x658`、`+0x660`、`+0x668`、`+0x670`、`+0x678`、`+0x680`、`+0x688`、`+0x690`、`+0x698`、`+0x6a0`、`+0x6a8`、`+0x6b0`、`+0x6b8`、`+0x6c0`、`+0x6d0`、`+0x6d8`、`+0x6e0`、`+0x6f0`、`+0x6f8`、`+0x700`、`+0x708`、`+0x710`、`+0x718`、`+0x720`、`+0x728`、`+0x740`、`+0x748`、`+0x750`、`+0x758`、`+0x760`、`+0x768`、`+0x76c`、`+0x770`、`+0x771`、`+0x774`、`+0x778`、`+0x780`、`+0x788`、`+0x790`、`+0x798`、`+0x7a0`、`+0x7a8`、`+0x7b0`、`+0x7b8`、`+0x7c0`、`+0x7c8`、`+0x7d0`、`+0x7d8`、`+0x7e0`、`+0x7e8`、`+0x7f0`、`+0x7f8`

见该 TU 的其它条目；**未解部分不给它编名字**。

### 附 8.x `0x6a3c80` **[已证实 + 未解]**

* 函数：`0x6a3c80`，11549 字节 / **2357 条指令**
* 被调用者（116 个）：`0x62ebe0`(0B)、`0x2fcd0`(151B)、`0x2fdd0`(129B，6 调用者)、`0x2fe60`(129B，6 调用者)、`0x5f3900`(22B，58 调用者)、`0x7d4b00`(3037B)、`0x5f4310`(35B，45 调用者)、`0x62730`(177B，11 调用者)、`0x51bfc0`(67B，34 调用者)、`0x4fc2e0`(14B，52 调用者)、`0x69db70`(3638B)、`0x8eee40`(328B，44 调用者)、`0x92ecb0`(791B，180 调用者)、`0x6a1180`(1230B)、`0x6a1650`(2873B)、`0x66b80`(37B)、`0x6a2a50`(4647B)、`0x62830`(84B)、`0x51c790`(743B，6 调用者)、`0x9984b0`(5B，5721 调用者)、`0xaf1f0`(792B)、`0x5f3980`(10B，44 调用者)、`0x30420`(180B)、`0xaef10`(12B，12 调用者)、`0x305b0`(1035B)、`0x62ac0`(369B)、`0x605660`(28B)、`0x978010`(959B，421 调用者)、`0x868f70`(545B，60 调用者)、`0x2fc90`(54B)、`0x605bf0`(1395B，7 调用者)、`0xae6b0`(477B)、`0x605680`(1379B，16 调用者)、`0x522920`(114B)、`0x522a40`(64B，7 调用者)、`0x528bf0`(275B，6 调用者)、`0x523980`(187B)、`0x8688e0`(545B，125 调用者)、`0xb50b0`(3B)、`0x6c0f0`(6B)、`0x627f0`(60B，12 调用者)、`0x51d320`(416B，17 调用者)、`0x910a60`(136B，185 调用者)、`0x529c40`(360B)、`0x90ecb0`(650B，185 调用者)、`0x6c0e0`(5B，19 调用者)、`0x867bf0`(337B，157 调用者)、`0x867df0`(180B，171 调用者)、`0x82b7b0`(494B，58 调用者)、`0x309c0`(103B)、`0x8aabc0`(41B，257 调用者)、`0x9445e0`(87B，237 调用者)、`0xaef80`(622B，14 调用者)、`0x5f4340`(140B，67 调用者)、`0x874220`(75B，22 调用者)、`0x5f3960`(17B，77 调用者)、`0x51c020`(4B，33 调用者)、`0x51d090`(4B，53 调用者)、`0x60a620`(2620B，680 调用者)、`0xaddf0`(577B，8 调用者)、`0x523050`(174B，33 调用者)、`0xad5e0`(75B，8 调用者)、`0x51d2f0`(5B，102 调用者)、`0x4f8390`(420B，35 调用者)、`0x69e9b0`(6606B，6 调用者)、`0x51d0c0`(5B，103 调用者)、`0x7c1430`(2235B，33 调用者)、`0x526690`(7B，9 调用者)、`0x6a0380`(185B)、`0x51faf0`(743B，16 调用者)、`0x51c030`(530B，30 调用者)、`0x7c1cf0`(200B，117 调用者)、`0x2fd70`(93B)、`0x63f2f8`(0B)、`0x899820`(1426B，13 调用者)、`0x303c0`(94B)、`0xaf6a0`(28B)、`0x4fc230`(12B，9 调用者)、`0x9878c0`(112B，67 调用者)、`0x91fd80`(121B，91 调用者)、`0x8ef0e0`(7416B，13 调用者)、`0x92f060`(272B，16 调用者)、`0x609e20`(221B，9 调用者)、`0x97a090`(1599B，17 调用者)、`0x8264e0`(136B，200 调用者)、`0xb50e0`(3B)、`0xb50d0`(3B)、`0xb50c0`(3B)、`0x8691a0`(545B，26 调用者)、`0x5231e0`(127B)、`0x4fc320`(11B，7 调用者)、`0x998500`(109B，2318 调用者)、`0x92dee0`(1148B，49 调用者)、`0x6be30`(97B)、`0x4fc5a0`(8B，114 调用者)、`0x69f90`(65B)、`0x326a0`(90B)、`0x522250`(327B)、`0x5d830`(5167B)、`0xaef30`(10B)、`0xaef20`(10B)、`0x4fc380`(10B，14 调用者)、`0x57ad10`(289B)、`0x51c010`(4B，21 调用者)、`0x16bb20`(670B)、`0x8ee020`(1610B，19 调用者)、`0x97ab50`(75B，352 调用者)、`0x696390`(357B)、`0x62f280`(171B，5209 调用者)、`0x978750`(51B，300 调用者)、`0x979e70`(51B，676 调用者)、`0x9989a0`(125B，837 调用者)、`0x998fe0`(79B，783 调用者)、`0x525370`(107B，13 调用者)、`0xad630`(478B，6 调用者)、`0x998bc0`(124B，833 调用者)
* 字符串：`iter`、` evaluation_ratio: `、` #sheets: `、` #parts: `、` dim: `、`strategy`、`, ...`、`properties.base_solution().empty()`
* 浮点常量：**1**（`0x9b11d0`）、**0.5**（`0x9b11d8`）、**0.2**（`0x9b1238`）、**1**（`0x9b11d0`）、**0.0001**（`0x9b1278`）、**0.0001**（`0x9b1278`）、**1.5**（`0x9b1270`）、**0.9**（`0x9b1260`）、**0.8**（`0x9b1258`）、**0.6**（`0x9b1250`）、**0.8**（`0x9b1258`）、**1.1**（`0x9b1268`）、**0.9**（`0x9b1260`）
* 立即数：`1`×32, `2`×14, `3`×9, `4`×5, `5`×2, `6`×1, `7`×3, `8`×1, `9`×1, `10`×6, `12`×2, `14`×1, `16`×72, `17`×1, `19`×1, `20`×2, `23`×1, `24`×1, `28`×1, `30`×1, `64`×2, `176`×1, `200`×1, `312`×7, `360`×1, `624`×2, `895`×1, `1000`×2, `1272`×1, `2504`×1, `5192`×2
* 字段偏移（146 个）：`+0x1`、`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x2c`、`+0x30`、`+0x38`、`+0x40`、`+0x43`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa6`、`+0xa7`、`+0xa8`、`+0xb0`、`+0xc0`、`+0xd0`、`+0xe0`、`+0xf0`、`+0x100`、`+0x108`、`+0x120`、`+0x140`、`+0x160`、`+0x180`、`+0x1a0`、`+0x1a8`、`+0x1c0`、`+0x1c8`、`+0x1e0`、`+0x1e8`、`+0x200`、`+0x208`、`+0x220`、`+0x228`、`+0x240`、`+0x248`、`+0x260`、`+0x268`、`+0x270`、`+0x274`、`+0x278`、`+0x280`、`+0x288`、`+0x2a0`、`+0x2b5`、`+0x2c0`、`+0x2dc`、`+0x2e0`、`+0x2e9`、`+0x2ec`、`+0x2f0`、`+0x300`、`+0x320`、`+0x330`、`+0x340`、`+0x34c`、`+0x358`、`+0x360`、`+0x370`、`+0x380`、`+0x388`、`+0x3a0`、`+0x3c0`、`+0x3c8`、`+0x3d0`、`+0x3d4`、`+0x3d8`、`+0x3e0`、`+0x3e8`、`+0x3f0`、`+0x3f8`、`+0x400`、`+0x408`、`+0x420`、`+0x440`、`+0x460`、`+0x480`、`+0x490`、`+0x4a0`、`+0x4c0`、`+0x4e0`、`+0x4e8`、`+0x4f0`、`+0x500`、`+0x508`、`+0x510`、`+0x518`、`+0x520`、`+0x530`、`+0x538`、`+0x540`、`+0x548`、`+0x560`、`+0x568`、`+0x570`、`+0x578`、`+0x580`、`+0x588`、`+0x590`、`+0x598`、`+0x5b0`、`+0x5b8`、`+0x5c0`、`+0x5c8`、`+0x5d0`、`+0x5d8`、`+0x5e0`、`+0x5e8`、`+0x600`、`+0x608`、`+0x610`、`+0x618`、`+0x620`、`+0x628`、`+0x630`、`+0x650`、`+0x670`、`+0x678`、`+0x680`、`+0x688`、`+0x698`、`+0x6a0`、`+0x6a8`、`+0x6b0`、`+0x6b8`、`+0x6c0`、`+0x710`、`+0x770`、`+0x778`、`+0x780`、`+0x788`、`+0x7a0`

见该 TU 的其它条目；**未解部分不给它编名字**。

### 附 8.x `0x2a3520` **[已证实 + 未解]**

* 函数：`0x2a3520`，12744 字节 / **2026 条指令**
* 被调用者（17 个）：`0x9984a0`(5B，653 调用者)、`0x90f5e0`(263B，29 调用者)、`0x63f238`(0B)、`0x9109e0`(95B，25 调用者)、`0x477cd0`(104B)、`0x82a3e0`(109B，51 调用者)、`0x4798b0`(573B)、`0x475370`(73B，14 调用者)、`0x9984b0`(5B，5721 调用者)、`0x9984e0`(5B，587 调用者)、`0x47b790`(142B)、`0x4797b0`(92B)、`0x47b680`(188B，8 调用者)、`0x479010`(90B)、`0x63f2f8`(0B)、`0x62f280`(171B，5209 调用者)、`0x9990a0`(51B，449 调用者)
* 字符串：`exmip1`、`AUATUWVSH`、`p0033`、`flugpl`、`enigma`、`mod011`、`probing`、`mas76`
* 浮点常量：**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**6**（`0x9c5a10`）、**16**（`0x9c5a20`）、**7**（`0x9c5a30`）、**12**（`0x9c5a40`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**4**（`0x9c5ac0`）、**4**（`0x9c5ad0`）、**6**（`0x9c5ae0`）、**25**（`0x9c5af0`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9a44e0`）、**1**（`0x9a4800`）、**1**（`0x9a4be0`）、**1**（`0x9a5300`）、**1**（`0x9a5a60`）、**1**（`0x9a6200`）、**1**（`0x9c5a08`）、**1**（`0x9a68c0`）、**1**（`0x9a6ba0`）、**1**（`0x9a6d80`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9c5a08`）、**1**（`0x9a6ec0`）、**2**（`0x9a7000`）、**1**（`0x9c5a08`）
* 立即数：`1`×123, `2`×28, `3`×21, `4`×9, `5`×4, `6`×6, `7`×15, `8`×19, `9`×6, `10`×5, `11`×5, `12`×3, `13`×8, `14`×3, `15`×4, `16`×9, `17`×5, `18`×10, `19`×4, `20`×3, `21`×6, `22`×6, `23`×2, `24`×5, `25`×8, `26`×5, `27`×5, `28`×6, `29`×9, `30`×2, `31`×7, `32`×3, `33`×7, `34`×5, `35`×5, `36`×5, `37`×4, `38`×2, `39`×4, `40`×6, `41`×3, `42`×5, `43`×3, `44`×4, `45`×3, `46`×4, `47`×5, `48`×5, `49`×2, `50`×2, `51`×3, `52`×6, `53`×4, `54`×2, `55`×1, `56`×2, `57`×2, `58`×2, `59`×4, `60`×4, `61`×3, `62`×3, `63`×2, `64`×3, `65`×3, `66`×2, `67`×1, `71`×1, `73`×2, `74`×2, `75`×1, `77`×1, `79`×1, `82`×1, `83`×1, `85`×2, `86`×1, `89`×1, `92`×1, `93`×2, `94`×1, `99`×1, `100`×1, `102`×1, `103`×1, `104`×1, `110`×1, `111`×1, `114`×2, `116`×2, `118`×1, `119`×1, `123`×2, `127`×1, `128`×3, `132`×2, `133`×1, `134`×1, `136`×1, `138`×1, `140`×1, `141`×1, `144`×1, `146`×2, `147`×2, `148`×2, `149`×1, `150`×1, `151`×3, `152`×1, `154`×1, `155`×1, `157`×2, `160`×3, `164`×3, `166`×1, `170`×1, `173`×1, `177`×1, `179`×2, `180`×2, `181`×3, `182`×2, `183`×2, `184`×1, `185`×3, `188`×1, `190`×1, `192`×1, `193`×2, `194`×1, `195`×2, `196`×1, `197`×1, `199`×1, `200`×2, `201`×1, `202`×1, `204`×2, `205`×1, `206`×2, `208`×2, `209`×1, `212`×1, `213`×2, `216`×2, `218`×1, `219`×1, `220`×4, `222`×2, `226`×1, `229`×1, `230`×1, `231`×1, `232`×2, `234`×1, `235`×1, `236`×1, `240`×2, `243`×2, `244`×1, `245`×2, `247`×1, `248`×1, `249`×1, `250`×1, `251`×2, `253`×1, `254`×1, `255`×1, `256`×1, `257`×1, `258`×1, `260`×2, `262`×2, `263`×1, `264`×2, `266`×1, `267`×1, `268`×1, `269`×1, `272`×1, `273`×1, `274`×1, `278`×1, `282`×2, `284`×1, `286`×1, `287`×1, `288`×2, `289`×1, `292`×1, `294`×1, `319`×2, `320`×1, `353`×1, `375`×1, `378`×1, `383`×1, `384`×1, `408`×1, `413`×1, `422`×1, `423`×1, `424`×1, `464`×2, `480`×1, `508`×1, `521`×1, `533`×1, `537`×1, `548`×2, `552`×1, `574`×1, `584`×2, `604`×1, `628`×1, `688`×1, `690`×1, `693`×1, `712`×1, `724`×1, `753`×1, `773`×1, `778`×1, `783`×1, `840`×1, `847`×1, `852`×1, `870`×1, `878`×1, `1152`×1, `1168`×1, `1208`×1, `1224`×1, `1256`×1, `1298`×1, `1350`×1, `1372`×2, `1448`×1, `1532`×1, `1541`×1, `1557`×1, `1560`×1, `1561`×1, `1580`×1, `1585`×1, `1588`×1, `1589`×1, `1614`×1, `1615`×1, `1616`×1, `1617`×1, `1626`×1, `1630`×1, `1631`×1, `1642`×1, `1643`×1, `1644`×1, `1645`×1, `1650`×1, `1654`×1, `1658`×1, `1659`×1, `1696`×1, `1792`×1, `1808`×1, `1886`×1, `1980`×1, `1989`×1, `2025`×1, `2032`×1, `2655`×1, `2756`×1, `2984`×2, `6000`×1, `7195`×1, `7548`×1, `8904`×1, `9502`×1, `9505`×1, `9507`×1, `9511`×1, `9512`×1, `9513`×1, `9514`×1, `9515`×1, `9516`×1, `9521`×1, `9522`×1, `9526`×1, `9534`×1, `9535`×1, `9536`×1, `9537`×1, `9542`×1, `9543`×1, `9544`×1, `9548`×1, `9550`×1, `9554`×1, `9557`×1, `10724`×1, `10757`×1, `10958`×1
* 字段偏移（76 个）：`+0x1`、`+0x2`、`+0x3`、`+0x4`、`+0x5`、`+0x6`、`+0x7`、`+0x8`、`+0xe`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x50`、`+0x70`、`+0x78`、`+0x80`、`+0xa0`、`+0xa4`、`+0xa8`、`+0xac`、`+0xb0`、`+0xb4`、`+0xb8`、`+0xbc`、`+0xc0`、`+0xc4`、`+0xc8`、`+0xcc`、`+0xd0`、`+0xd4`、`+0xd8`、`+0xdc`、`+0xe0`、`+0xe4`、`+0xf0`、`+0x150`、`+0x198`、`+0x1c0`、`+0x208`、`+0x218`、`+0x380`、`+0x384`、`+0x388`、`+0x38c`、`+0x390`、`+0x394`、`+0x398`、`+0x39c`、`+0x3a0`、`+0x3a4`、`+0x3a8`、`+0x3ac`、`+0x3b0`、`+0x3b4`、`+0x3b8`、`+0x3bc`、`+0x3c0`、`+0x3c4`、`+0x3c8`、`+0x3cc`、`+0x3d0`、`+0x3d4`、`+0x3d8`、`+0x3dc`、`+0x3e0`、`+0x3e4`、`+0x3e8`、`+0x3ec`、`+0x3f0`、`+0x3f4`、`+0x4d8`、`+0x4e8`

见该 TU 的其它条目；**未解部分不给它编名字**。

### 附 8.x `0x446920` **[已证实 + 未解]**

* 函数：`0x446920`，15271 字节 / **3014 条指令**
* 被调用者（41 个）：`0x437260`(181B)、`0x3f5070`(1131B)、`0x438000`(618B)、`0x4197d0`(803B，100 调用者)、`0x41b850`(657B，38 调用者)、`0x41b320`(329B，72 调用者)、`0x41a3d0`(455B，100 调用者)、`0x63f238`(0B)、`0x90ecb0`(650B，185 调用者)、`0x910a60`(136B，185 调用者)、`0x90f9e0`(72B，27 调用者)、`0x640ec0`(361B，15 调用者)、`0x9984e0`(5B，587 调用者)、`0x63f2f8`(0B)、`0x90f5e0`(263B，29 调用者)、`0x63f2e8`(0B)、`0x4348f0`(82B)、`0x998500`(109B，2318 调用者)、`0x974520`(581B，8 调用者)、`0x63f2f0`(0B)、`0x9984b0`(5B，5721 调用者)、`0x63f258`(0B)、`0x434a10`(3839B)、`0x437320`(1666B)、`0x4379b0`(1602B)、`0x434810`(34B，7 调用者)、`0x63f270`(0B)、`0x434540`(708B)、`0x434950`(177B)、`0x9984a0`(5B，653 调用者)、`0x43d740`(3871B)、`0x435910`(3871B)、`0x97a830`(75B，571 调用者)、`0x910ba0`(109B，1002 调用者)、`0x63f390`(0B)、`0x63f268`(0B)、`0x62f280`(171B，5209 调用者)、`0x437240`(27B)、`0x9990a0`(51B，449 调用者)、`0x97ab50`(75B，352 调用者)、`0x63f310`(0B)
* 字符串：`row`、`NAME          `、`  FREE`、`OBJROW`、`COLUMNS`、`  IEEE`、`%d,%d,`、`%d,%d,`
* 浮点常量：**1**（`0x9d5ce0`）、**1**（`0x9d5ce0`）、**1**（`0x9d5ce0`）、**1**（`0x9d5ce0`）
* 立即数：`1`×97, `2`×34, `3`×23, `4`×32, `5`×13, `6`×8, `7`×20, `8`×38, `10`×1, `13`×3, `14`×1, `15`×3, `16`×35, `32`×7, `44`×2, `48`×3, `61`×6, `63`×2, `64`×1, `67`×1, `69`×2, `71`×4, `76`×3, `82`×5, `271`×1, `1016`×2, `8224`×5
* 字段偏移（97 个）：`+0x1`、`+0x2`、`+0x3`、`+0x4`、`+0x5`、`+0x6`、`+0x7`、`+0x8`、`+0xa`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x2c`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x4c`、`+0x50`、`+0x58`、`+0x60`、`+0x64`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xfb`、`+0xfc`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x124`、`+0x128`、`+0x130`、`+0x138`、`+0x148`、`+0x14c`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x180`、`+0x1a0`、`+0x1c0`、`+0x1e0`、`+0x200`、`+0x220`、`+0x228`、`+0x230`、`+0x240`、`+0x248`、`+0x250`、`+0x260`、`+0x290`、`+0x298`、`+0x2a0`、`+0x2a3`、`+0x2a4`、`+0x2b0`、`+0x2b8`、`+0x2c0`、`+0x2d0`、`+0x2d1`、`+0x2d2`、`+0x2d3`、`+0x2d4`、`+0x2d5`、`+0x2d6`、`+0x2d7`、`+0x2d8`、`+0x3a0`、`+0x3b0`、`+0x3c0`、`+0x3d0`、`+0x3e0`、`+0x440`、`+0x460`、`+0x468`、`+0x470`、`+0x478`

见该 TU 的其它条目；**未解部分不给它编名字**。

### 附 8.x `0x314e20` **[已证实 + 未解]**

* 函数：`0x314e20`，12995 字节 / **2793 条指令**
* 被调用者（26 个）：`0x9984a0`(5B，653 调用者)、`0x9984e0`(5B，587 调用者)、`0x6426b0`(300B，31 调用者)、`0x63f2e8`(0B)、`0x3f7640`(1951B，28 调用者)、`0x3f6050`(607B，74 调用者)、`0x3f9090`(59B，32 调用者)、`0x9984b0`(5B，5721 调用者)、`0x998500`(109B，2318 调用者)、`0x3f8870`(41B，9 调用者)、`0x3ef4f0`(15B)、`0x6427e0`(442B，10 调用者)、`0x9990e0`(267B，170 调用者)、`0x2d6f70`(235B)、`0x30aea0`(1805B)、`0x419610`(9B，27 调用者)、`0x652630`(39B，72 调用者)、`0x2d4f60`(369B)、`0x30b5b0`(165B，19 调用者)、`0x2d29d0`(74B)、`0x2ff7c0`(282B)、`0x4197d0`(803B，100 调用者)、`0x41b470`(489B，57 调用者)、`0x41a3d0`(455B，100 调用者)、`0x9990a0`(51B，449 调用者)、`0x62f280`(171B，5209 调用者)
* 字符串：`How did we get scalingFlag_ %d and non NULL rowSca`
* 浮点常量：**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**0.0001**（`0x9c9b88`）、**0.001**（`0x9c9c98`）、**1**（`0x9c9b10`）、**0.001**（`0x9c9c98`）、**1**（`0x9c9b10`）、**0.001**（`0x9c9c98`）、**1**（`0x9c9b10`）、**1**（`0x9c9b10`）、**0.001**（`0x9c9c98`）、**0.001**（`0x9c9c98`）
* 立即数：`1`×96, `2`×18, `3`×32, `4`×14, `5`×3, `6`×4, `7`×6, `8`×20, `9`×1, `10`×7, `11`×1, `14`×5, `15`×1, `16`×6, `29`×2, `31`×2, `32`×2, `63`×9, `64`×2, `82`×1, `120`×1, `128`×1, `231`×1, `248`×2, `255`×3
* 字段偏移（86 个）：`+0x4`、`+0x7`、`+0x8`、`+0x10`、`+0x14`、`+0x18`、`+0x20`、`+0x28`、`+0x2c`、`+0x30`、`+0x34`、`+0x38`、`+0x3e`、`+0x3f`、`+0x40`、`+0x48`、`+0x4c`、`+0x50`、`+0x58`、`+0x60`、`+0x64`、`+0x68`、`+0x70`、`+0x78`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x134`、`+0x138`、`+0x13c`、`+0x140`、`+0x144`、`+0x148`、`+0x14a`、`+0x150`、`+0x198`、`+0x1d8`、`+0x1dc`、`+0x1e0`、`+0x1e4`、`+0x1f8`、`+0x298`、`+0x2a0`、`+0x390`、`+0x3b0`、`+0x3b8`、`+0x3c0`、`+0x3c8`、`+0x3d0`、`+0x3d8`、`+0x3e0`、`+0x3e8`、`+0x3f0`、`+0x3f8`、`+0x418`、`+0x428`、`+0x430`、`+0x438`、`+0x468`、`+0x470`、`+0x478`、`+0x480`、`+0x488`、`+0x490`、`+0x498`、`+0x4c0`、`+0x4c8`、`+0x4ec`、`+0x520`、`+0x524`、`+0x540`、`+0x694`

见该 TU 的其它条目；**未解部分不给它编名字**。

### 附 8.x `0x380610` **[已证实 + 未解]**

* 函数：`0x380610`，12268 字节 / **2601 条指令**
* 被调用者（46 个）：`0x63f3f0`(0B)、`0x9984e0`(5B，587 调用者)、`0x4a9a50`(91B)、`0x422240`(424B)、`0x4a98f0`(169B)、`0x4a99a0`(169B)、`0x63f2f0`(0B)、`0x9984a0`(5B，653 调用者)、`0x3010e0`(1289B，10 调用者)、`0x2b23f0`(6B，13 调用者)、`0x4a9d10`(481B)、`0x30cf50`(216B)、`0x30e8a0`(46B，8 调用者)、`0x30e8d0`(49B，6 调用者)、`0x309cd0`(20B，7 调用者)、`0x2be2b0`(22B)、`0x312a20`(721B，16 调用者)、`0x978010`(959B，421 调用者)、`0x8688e0`(545B，125 调用者)、`0x867bf0`(337B，157 调用者)、`0x867df0`(180B，171 调用者)、`0x652630`(39B，72 调用者)、`0x371140`(672B)、`0x63f2e8`(0B)、`0x3223d0`(3994B，13 调用者)、`0x373c20`(1289B)、`0x2b7520`(10B)、`0x63f2f8`(0B)、`0x467070`(358B)、`0x9990a0`(51B，449 调用者)、`0x3118c0`(203B，6 调用者)、`0x2b16a0`(104B)、`0x466d90`(725B，11 调用者)、`0x37be00`(10004B)、`0x46ec60`(254B，30 调用者)、`0x469260`(400B，13 调用者)、`0x3117b0`(261B)、`0x2bbf80`(1316B)、`0x465de0`(86B，46 调用者)、`0x302b50`(109B，32 调用者)、`0x978750`(51B，300 调用者)、`0x62f280`(171B，5209 调用者)、`0x8264e0`(136B，200 调用者)、`0x63f420`(0B)、`0x99dd80`(152B)、`0x311060`(1443B，21 调用者)
* 字符串：`Time to decompose `、` seconds`、`Start of pass %d`、`suminf %g`、`suminf %g`、`Sum of artificials after solve is %g`、`For subproblem ray %d smallest - %g, largest %g - `、`For subproblem %d smallest - %g, largest %g - dj %`
* 浮点常量：**1**（`0x9ccd50`）、**1**（`0x9ccd50`）、**1**（`0x9ccd50`）、**1**（`0x9ccd50`）、**1**（`0x9ccd50`）、**0.1**（`0x9cceb8`）、**1**（`0x9ccd50`）
* 立即数：`1`×135, `2`×31, `3`×26, `4`×16, `5`×6, `6`×3, `7`×11, `8`×9, `9`×2, `10`×4, `11`×1, `16`×13, `18`×1, `19`×1, `34`×1, `50`×2, `200`×2, `500`×2, `1736`×10, `2392`×2
* 字段偏移（79 个）：`+0x1`、`+0x4`、`+0x8`、`+0xc`、`+0x10`、`+0x14`、`+0x18`、`+0x1c`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x43`、`+0x50`、`+0x58`、`+0x60`、`+0x64`、`+0x68`、`+0x6c`、`+0x70`、`+0x78`、`+0x80`、`+0x84`、`+0x88`、`+0x8c`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x12c`、`+0x130`、`+0x138`、`+0x140`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x180`、`+0x1a0`、`+0x1a8`、`+0x1b0`、`+0x1b8`、`+0x1e0`、`+0x240`、`+0x244`、`+0x248`、`+0x250`、`+0x258`、`+0x268`、`+0x270`、`+0x278`、`+0x288`、`+0x290`、`+0x298`、`+0x2e0`、`+0x30c`、`+0x318`、`+0x568`、`+0x6d0`、`+0x72c`

见该 TU 的其它条目；**未解部分不给它编名字**。

### 附 9 严格归属聚类里冒出来的两个新身份 **[已证实]**

严格口径（每个调用者都等于同一个具名函数）下共 **93 个入口 / 162 个匿名辅助 / 22,913 字节**
（对比宽松口径的 318 组 / 448,661 B —— 说明**大多数匿名函数并非私有**，此前的宽松表确实偏乐观）。
其中两条是有价值的新身份：

* **`0x14620` = `NewLaunchingOrder`**（自带该名字），拥有 **3 个私有辅助 / 1,935 B**。
  ⇒ 这是 `LaunchingOrder` 的构造入口（`LaunchingOrder` 是 lcns 已建模的 `model` 成员），
  其私有辅助即"建单"过程的内部步骤。
* **`0x8BA70` 自带字符串 `'..\multi\marker.cpp'`** ⇒ **新 TU：`..\multi\marker.cpp`**
  （标记/打标模块），拥有 **2 个私有辅助 / 1,654 B**。
* 另有一条工具线索：`0x8A9510` 自带字符串 `'.,-+xX0123456789abcdef012345'` ⇒ **base64/编码字母表**
  （在授权/加密路径一族里），拥有 5 个私有辅助 / 1,811 B。**[推断：base64 字母表]**

### 附 10 `0x1d7960` **[已证实 + 未解]**

* 函数：`0x1d7960`，10072 字节 / **2144 条指令**
* 被调用者（40 个）：`0x1c85a0`(947B)、`0x1816a0`(2016B，39 调用者)、`0x16c450`(79B，19 调用者)、`0x170250`(57B，28 调用者)、`0x677cb0`(1395B，7 调用者)、`0x9984b0`(5B，5721 调用者)、`0x998500`(109B，2318 调用者)、`0x983ca0`(145B，289 调用者)、`0x8fd680`(456B)、`0x8ab960`(487B，9 调用者)、`0x8fd850`(126B)、`0x8fdaa0`(126B)、`0x775c00`(932B，108 调用者)、`0x62f280`(171B，5209 调用者)、`0x8ab5d0`(337B，29 调用者)、`0x1c8300`(104B，12 调用者)、`0x910ba0`(109B，1002 调用者)、`0x60a620`(2620B，680 调用者)、`0x98df60`(311B，10 调用者)、`0x5f3bc0`(8B，43 调用者)、`0x16c2f0`(190B，25 调用者)、`0x1d76b0`(676B)、`0x16c4a0`(23B，14 调用者)、`0x5f4340`(140B，67 调用者)、`0x97a830`(75B，571 调用者)、`0x873380`(40B，31 调用者)、`0x1ec0b0`(5758B)、`0x63f2f8`(0B)、`0x65c090`(91B，9 调用者)、`0x8fd8d0`(456B)、`0x8b4ae0`(196B，30 调用者)、`0x6ac370`(694B，57 调用者)、`0x63f2f0`(0B)、`0x9989a0`(125B，837 调用者)、`0x998fe0`(79B，783 调用者)、`0x979e70`(51B，676 调用者)、`0x998bc0`(124B，833 调用者)、`0x669980`(70B，11 调用者)、`0x66da30`(91B，19 调用者)、`0x8f2f30`(220B)
* 字符串：`vector::_M_range_check: __n (which is %zu) >= this`、`vector::_M_range_check: __n (which is %zu) >= this`、`vector::_M_range_check: __n (which is %zu) >= this`、`vector::_M_range_check: __n (which is %zu) >= this`
* 浮点常量：**1.5**（`0x9c04f0`）、**1.5**（`0x9c04f0`）、**1.5**（`0x9c04f0`）、**0.99995**（`0x9c0508`）、**1.5**（`0x9c04f0`）
* 立即数：`1`×39, `2`×2, `3`×24, `4`×1, `5`×6, `6`×2, `7`×4, `8`×8, `9`×1, `15`×1, `16`×3, `20`×1, `24`×3, `25`×4, `31`×3, `32`×27, `40`×22, `48`×5, `80`×7, `127`×4, `185`×1, `344`×1, `1224`×2, `4096`×4
* 字段偏移（126 个）：`+0x1`、`+0x5`、`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`、`+0x78`、`+0x7f`、`+0x80`、`+0x88`、`+0x90`、`+0x98`、`+0xa0`、`+0xa8`、`+0xb0`、`+0xb8`、`+0xc0`、`+0xc8`、`+0xd0`、`+0xd8`、`+0xe0`、`+0xe8`、`+0xf0`、`+0xf8`、`+0x100`、`+0x108`、`+0x110`、`+0x118`、`+0x120`、`+0x128`、`+0x130`、`+0x138`、`+0x140`、`+0x148`、`+0x150`、`+0x158`、`+0x160`、`+0x168`、`+0x170`、`+0x178`、`+0x188`、`+0x190`、`+0x1a0`、`+0x1b0`、`+0x1d0`、`+0x1d8`、`+0x1e8`、`+0x1f0`、`+0x200`、`+0x208`、`+0x220`、`+0x230`、`+0x238`、`+0x240`、`+0x248`、`+0x250`、`+0x258`、`+0x260`、`+0x268`、`+0x270`、`+0x278`、`+0x288`、`+0x290`、`+0x2a0`、`+0x2a8`、`+0x2b8`、`+0x2c0`、`+0x2c8`、`+0x2d0`、`+0x2d8`、`+0x2e0`、`+0x2e8`、`+0x2f0`、`+0x300`、`+0x308`、`+0x310`、`+0x318`、`+0x319`、`+0x330`、`+0x338`、`+0x348`、`+0x350`、`+0x360`、`+0x368`、`+0x380`、`+0x390`、`+0x398`、`+0x3a0`、`+0x3a8`、`+0x3b0`、`+0x3b8`、`+0x3c0`、`+0x3d0`、`+0x3e8`、`+0x400`、`+0x418`、`+0x420`、`+0x428`、`+0x430`、`+0x438`、`+0x440`、`+0x448`、`+0x450`、`+0x460`、`+0x470`、`+0x480`、`+0x490`、`+0x4a0`、`+0x4b0`、`+0x518`、`+0x520`、`+0x528`、`+0x530`、`+0x538`、`+0x540`

**尚未解**：身份/角色未定；不给它编名字。

### 附 11 一对孪生函数与一个 `UWVSH` 块（goal round 62）**[已证实为结构]**

| 地址 | 字节 | 指令 | 字符串 | 浮点常量 |
|---|---:|---:|---|---|
| `0x4D1950` | 4,190 | **883** | 只有 `basic_string::_M_construct` | 见本轮输出 |
| `0x4D29D0` | 4,203 | **883** | 同上 | 同上 |
| `0x1192C0` | 4,152 | 884 | `UWVSH` | — |

**可确定的**：`0x4D1950` 与 `0x4D29D0` 的**指令数完全相同（883）**、字节数只差 13、调用面与字符串一致
⇒ 典型的**模板实例化孪生**（同一模板的两组类型参数）。这类函数**只需读通一个**即可推及另一个，
是后面提高效率的关键（一对 8.4 KB 只需读一遍）。

**不可确定的**：模板参数是什么、这一族在哪个 TU。**不编名字**，只记结构。
`0x1192C0` 自带 `UWVSH`（与 `0x2A3520` 同类前缀）⇒ 与那批"带 UWVSH 前缀"的函数同族，前缀本身无意义（是编译器生成的栈布局标记）。

### 附 12 孪生族（模板实例化）清单（goal round 63）**[已证实为结构判据]**

**判据**：**指令数 + 字节数完全相同**且都 ≥200 指令/2KB 的未引用领域函数，视作**同一模板的实例化**（round 62 已验证一对：`0x4D1950`/`0x4D29D0` 都是 883 指令、调用面一致）。⇒ **读一份即可推及全族**。

本轮找到 **3 族 / 6 个函数 / 14624 字节**。

| 成员数 | 指令 | 字节 | 成员 |
|---:|---:|---:|---|
| 2 | 652 | 2705 | `0x18f4b0` `0x18ff50` |
| 2 | 517 | 2479 | `0x827240` `0x827bf0` |
| 2 | 455 | 2128 | `0x702120` `0x703a10` |

**口径**：这是**结构判据**（同尺寸 ⇒ 同模板），**不是身份**：族成员各自做什么仍未读，故本条只作为**读一份覆盖一族**的工作方法。

### 附 13 按**调用面**聚类的族（goal round 64）**[结构判据]**

**判据**：两个未引用领域函数若共享一批**有辨识度**的被调用者（调用者数 ≤ 60，排除 `operator new`、错误上报器这类人人都调的），则视为**同一族**。这比 round 63 的「字节数完全相同」宽松得多。

本轮找到 **13 族 / 57 个函数 / 26565 字节**。

| 成员数 | 共享被调用者 | 成员 |
|---:|---:|---|
| 3 | 4 | `0x8d9830` `0x8d9ce0` `0x8da1b0` |
| 12 | 5 | `0x6ca720` `0x6ca840` `0x6ca960` `0x6caa80` `0x6caba0` `0x6cacc0` `0x6cade0` `0x6caf00` |
| 3 | 19 | `0x1acf30` `0x1ad3a0` `0x1ad7e0` |
| 11 | 4 | `0x92ce40` `0x92cf60` `0x92d080` `0x92d1a0` `0x92d2c0` `0x92d3e0` `0x92d500` `0x92d620` |
| 3 | 8 | `0x520a30` `0x520e30` `0x521210` |
| 3 | 5 | `0x87b6a0` `0x87c3c0` `0x87c960` |
| 3 | 6 | `0x20fc10` `0x212830` `0x212ab0` |
| 3 | 3 | `0x868490` `0x8686c0` `0x868d40` |
| 3 | 3 | `0x8894b0` `0x88b6f0` `0x88b840` |
| 3 | 4 | `0x81df30` `0x81e0b0` `0x81e1e0` |
| 3 | 3 | `0x13b760` `0x13b880` `0x13b960` |
| 3 | 3 | `0x64c6b0` `0x64cb30` `0x64d420` |
| 4 | 3 | `0x1a5390` `0x1a5460` `0x1a5500` `0x1a5970` |

**口径**：这是**结构判据**，**不是身份**：共享被调用者只说明同族，族成员各自做什么仍未读。用途是**读一份推及全族**。

### 附 14 等距大族的成员定性（goal round 65）**[已读指令，身份部分已定]**

round 64 发现两个**成员等距排列**的族（0x6CA720 一族 12 个、0x92CE40 一族 11 个，间距均约 0x120）。本轮读其中的具体成员：

* **`0x6ca720`**（0x6CA720 family (12 members)）279 B / 78 条指令；字符串 `10BeamValues`；被调用者 `0x1a2ab0`, `0x608e40`, `0x62f280`, `0x6d5980`, `0x82b7b0`, `0x8f17b0`, `0x91fd80`, `0x978010`, `0x9984b0`；
* **`0x6ca840`**（next member of the same family, to see the difference）279 B / 78 条指令；字符串 `10Off2Weight`；被调用者 `0x1a2ab0`, `0x608e40`, `0x62f280`, `0x6d5980`, `0x82b7b0`, `0x8f17b0`, `0x91fd80`, `0x978010`, `0x9984b0`；
* **`0x92ce40`**（0x92CE40 family (11 members)）284 B / 86 条指令；字符串 `无`；被调用者 `0x1a8d70`, `0x62f280`, `0x89e0d0`, `0x92c7b0`, `0x92dbf0`, `0x9984b0`, `0x998500`, `0x9989a0`, `0x998bc0`, `0x998fe0`；
* **`0x1acf30`**（0x1ACF30 family (19 shared callees)）1121 B / 267 条指令；字符串 `..\nesting\algos\multinesting_optimizer.cpp、nestings.size() == before_size、RecordAndReplaceIfBetter`；被调用者 `0x183f50`, `0x1a8d70`, `0x1a9350`, `0x1aaba0`, `0x1baf20`, `0x1bb490`, `0x1bbd90`, `0x1bc4a0`, `0x1c09b0`, `0x1c0a00`；

### 附 15 十二个参数名（goal round 66）**[已证实]**

`0x6CA720` 一族 12 个成员（279 B / 78 指令，间距恰为 `0x120`）各自携带一个**长度前缀**名，下列为二进制里实际存的字符串：

* `0x6ca720` → `10BeamValues`
* `0x6ca840` → `10Off2Weight`
* `0x6ca960` → `10PartRatios`
* `0x6caa80` → `11RepeatSheet`
* `0x6caba0` → `11TilingLimit`
* `0x6cacc0` → `13ODescriptions`
* `0x6cade0` → `13PosDirections`
* `0x6caf00` → `14ODescriptions2`
* `0x6cb020` → `6UseMap`
* `0x6cb140` → `7OPricer`
* `0x6cb260` → `7ZfSizes`
* `0x6cb380` → `8DegSteps`

**前缀的十进制数等于名字长度（12/12）**⇒ 编码为 `<len><name>`。
**其中两个名字含数字**（`Off2Weight`、`ODescriptions2`），所以判定时**不能要求纯字母** —— 我第一版校验器就是这么错的，它拒绝写入（没把半成品写进 C++）。同时 12 个处理器因此有了**真实名字**。

### 附 16 参数名的引用方（goal round 67）**[已证实为引用关系]**

12 个参数名字符串各自的引用者中，**排除 12 个处理器自身**后剩：
（无：除处理器自身外没有其他引用者）

**口径**：引用关系是硬事实；「它就是参数解析器」是推论，本条不下该结论。

### 附 17 十二个处理器是否通过表达到（goal round 68）**[已证实]**

**调用者**：有

**作为 64 位数据出现**：0 处，覆盖 0 个处理器。


**口径**：「地址出现在数据里」是硬事实（指针或嵌入常量）；「它是一张分发表」需要连续且等距才成立。

### 附 18 参数系统的消费方 `0x6D33A0`（goal round 69）**[已读，部分已定]**

* 规模：**188 B / 58 条指令**
* 字符串（0 条）：无
* 调用：共 12 次（12 个不同），其中 **十二个处理器占 12 个**
* 处理器调用顺序：`0x6ca720`(BeamValues) → `0x6ca840`(Off2Weight) → `0x6ca960`(PartRatios) → `0x6caa80`(RepeatSheet) → `0x6caba0`(TilingLimit) → `0x6cacc0`(ODescriptions) → `0x6cade0`(PosDirections) → `0x6caf00`(ODescriptions2) → `0x6cb020`(UseMap) → `0x6cb140`(OPricer) → `0x6cb260`(ZfSizes) → `0x6cb380`(DegSteps)
* cmp/test 数：0；间接跳转：0

**口径**：「它调用了这些处理器」是硬事实；选择机制如何得看上面的计数与跳转形态。

### 附 19 一个参数处理器的全体：`0x6CA720` = `BeamValues`（goal round 70）**[已读全部 78 条指令]**

代码清单与结论见本轮输出；共 78 条指令，调用 9 个不同被调用者。

### 附 20 参数系统的取值例程 `0x978010`（goal round 71）**[已读结构]**

* 规模：**959 B / 255 条指令**；字符串：无
* 被调用者（10 个）：`0x62f280`, `0x8264e0`, `0x8682a0`, `0x868380`, `0x9456a0`, `0x978750`, `0x97a6d0`, `0x9989a0`, `0x998bc0`, `0x998fe0`
* 浮点常量：无
* 访问的字段偏移：+0x10, +0x18, +0x19, +0x1c, +0x20, +0x28, +0x2c, +0x30, +0x38, +0x59, +0x60, +0x68

**口径**：只读了结构（调用面/字段/常量），本轮**不下行为结论**。

### 附 21 「查找结果」的构造者 `0x8682A0`（goal round 72）**[已读]**

* 规模：**100 B / 35 条指令**；字符串：无
* 被调用者（1）：`0x867df0`
* 浮点常量：无；调用者数：13

**口径**：代码清单见本轮输出；结论只写指令能支持的部分。

### 附 22 `0x867DF0`：是配置查找还是**反序列化**（goal round 73）**[已读 52 条指令]**

* 规模：180 B / 52 条；字符串：无；被调用者 5 个：`0x62f280`, `0x9456a0`, `0x9989a0`, `0x998bc0`, `0x998fe0`
* 指针式 add/sub （含内存操作数）：3；**单字节读取**：0

**口径**：代码清单在本轮输出；若出现“指针推进 + 剩余长度比较 + 整块拷贝”则反序列化成立，否则仍为寻找。

### 附 23 `0x8F17B0` 与 iostream 候选簇的规模（goal round 74）**[已读]**

未引用领域函数中，**调用了 iostream 内部例程**（`0x867DF0`/`0x978010`/`0x8682A0`/`0x9456A0`）的：**76 个 / 55575 字节**；其中**自带字符串**：47 / 39761 B；**完全无字符串**：29 / 15814 B。

**口径**：这是**候选数**，**不是重新归类**。

**`0x8F17B0`**：104 B / 29 条，字符串 `无`，调用者 27 个。

### 附 24 `0x82B7B0` 与四个**有证据的** libstdc++ 排除项（goal round 75）

**`0x82B7B0`**：494 B / 126 条指令，字符串 `无`，被调用者 58 个；它被参数处理器用 `[rdi+8]` 调用（round 70）。

**排除项**（每一个都是逐条读过才进来的，证据写在 `covlib.py` 的 `LIBSTDCXX_EVIDENCED` 里）：`0x867DF0`（eofbit）、`0x8682A0`（badbit）、`0x978010`（流提取路径）、`0x8F17B0`（`vector<string>` 移动插入，SSO 布局）。

**归类前的正式口径（`g_coverage.py`）**：

```
﻿reachable from the exports: 6181 functions, 4670042 bytes (47.0% of all code)
   cited reachable     :   2041  (2467801 bytes)  -> 52.8% of reachable bytes
=== top 35 NOT-cited reachable functions (the concrete work list) ===
   not-cited reachable: 4140 functions, 2202241 bytes (47.2% of reachable)
=== of the un-cited reachable code (identity evidence required, round 7) ===
   third party to LINK (see third_party/README.md):   379 fns,    55875 B (1.2% of reachable)
   toolchain libstdc++/MinGW                      :   225 fns,   230975 B (4.9%)
   libcns DOMAIN code STILL TO REVERSE            :  3536 fns,  1915391 B (41.0%)
```

**归类后的正式口径（g_coverage.py）**：

```nreachable from the exports: 6181 functions, 4670042 bytes (47.0% of all code)
   cited reachable     :   2041  (2467801 bytes)  -> 52.8% of reachable bytes
=== top 35 NOT-cited reachable functions (the concrete work list) ===
   not-cited reachable: 4140 functions, 2202241 bytes (47.2% of reachable)
```n

**口径声明（归类前 / 后）**：两个数字都在这里，而且这次排除只动了 4 个**逐条读过**的库例程（共 1,343 字节）。

```
[BEFORE]
   reachable from the exports: 6181 functions, 4670042 bytes (47.0% of all code)
      cited reachable     :   2041  (2467801 bytes)  -> 52.8% of reachable bytes
      third party to LINK:   379 fns,    55875 B (1.2% of reachable)
      toolchain libstdc++/MinGW :   225 fns,   230975 B (4.9%)
      libcns DOMAIN code STILL TO REVERSE:  3536 fns,  1915391 B (41.0%)

[AFTER]
﻿reachable from the exports: 6181 functions, 4670042 bytes (47.0% of all code)
   cited reachable     :   2041  (2467801 bytes)  -> 52.8% of reachable bytes
=== top 35 NOT-cited reachable functions (the concrete work list) ===
   not-cited reachable: 4140 functions, 2202241 bytes (47.2% of reachable)
```

### 附 25 字符串构造族（goal round 76）**[已读，假设被推翻]**

**我的假设是错的**：我以为 `0x90F310` 与 `0x910BA0` 是**同一函数**（指令序列相同），实际**不同**（50 vs 28 条指令）。读完后正确的看法是：

* **`0x90F310` = `std::string::_M_construct`**：函数体里就带着字面断言 `basic_string::_M_construct null not valid`，并将长度与 **`0xf`（15）** 比较 —— 这正是 32 字节 `std::string` 的 **SSO 容量**；超过时调 `0x910BA0` 分配。
* **`0x910BA0` = 其分配助手**（堆情形），1002 个调用者。

**指标副作用（必须一起报）**：这两个例程登记为工具链时发生了**两件事**：① 它们**离开了领域桶**；② 但把它们的地址写进 `covlib.py` **同时也算一次引用**。所以：领域未引用 **4140 → 4139**，而已引用 **2041 → 2042**。只报其中一个都会隐藏另一个效应。

### 附 26 参数驱动 `0x6D33A0` 的调用者（goal round 77）**[已读]**

`0x6D33A0`（依次调用 12 个参数处理器）的调用者共 **1** 个：

* `0x1a7c00`（1578 B）字符串：`vector::reserve`、`strip_x`

**口径**：调用关系与调用点上下文是硬事实；「该对象在领域模型里是什么」需要读调用者才能下。

### 附 27 `0x1A7C00` 的全部字符串（goal round 78）**[已读]**

规模 1578 B；字符串 **2** 条；**TU 路径：**无****；被调用者 21 个。

* `vector::reserve`
* `strip_x`

**口径**：字符串与引用位置是硬事实；「这些名字构成什么」需要读它们如何被使用。

### 附 28 第一份类档案：`Utils::Canceller`（goal round 88）**[已读结构]**

来源：round 87 的 **vtable 地址点**通道（只有 `+0x10` 被引用，起点与 type_info 槽均为 0）。

本类被引用 vtable 地址点的可达函数：**24**。

| 函数 | 字节 | 指令 | 被调用者 | 字符串 | 字段偏移 |
|---|---:|---:|---:|---|---|
| `0x30a30` | 187 | 55 | 3 | 无 | +0x8, +0x10, +0x18, +0x20, +0x28, +0x30 |
| `0x32700` | 1669 | 357 | 34 | 无 | +0x8, +0xc, +0x10, +0x18, +0x20, +0x28 |
| `0x67460` | 8995 | 1754 | 51 | `basic_string::_M_construct null not valid` | +0x8, +0xc, +0x10, +0x14, +0x18, +0x1a |
| `0x1f2d00` | 1766 | 372 | 24 | `vector::_M_range_check: __n (which is %zu) >`、`..\nesting\structure_interface_private.hpp` | +0x8, +0x10, +0x18, +0x20, +0x28, +0x30 |
| `0x261e00` | 86 | 22 | 2 | 无 | +0x28, +0x2c, +0x30, +0x40 |
| `0x4da8e0` | 331 | 90 | 6 | 无 | +0x8, +0x10, +0x18, +0x20, +0x28, +0x30 |
| `0x4ed480` | 2163 | 499 | 22 | `basic_string::_M_construct null not valid` | +0x8, +0x9, +0x10, +0x18, +0x20, +0x28 |
| `0x55fc70` | 1799 | 426 | 15 | 无 | +0x8, +0x10, +0x18, +0x20, +0x28, +0x38 |
| `0x589cc0` | 1081 | 291 | 13 | 无 | +0x18, +0x20, +0x30, +0x40, +0x48, +0x60 |
| `0x59c560` | 1961 | 420 | 12 | 无 | +0x8, +0x10, +0x14, +0x16, +0x18, +0x20 |
| `0x59cd10` | 7356 | 1619 | 17 | 无 | +0x8, +0x10, +0x14, +0x16, +0x18, +0x20 |
| `0x59e9d0` | 10198 | 2154 | 18 | 无 | +0x8, +0x10, +0x12, +0x14, +0x18, +0x20 |
| `0x5a2690` | 2286 | 527 | 17 | 无 | +0x8, +0x10, +0x14, +0x16, +0x18, +0x20 |
| `0x5afb80` | 73 | 19 | 1 | 无 | +0x8, +0x10, +0x20, +0x30, +0x38, +0x40 |
| `0x665bf0` | 840 | 182 | 13 | 无 | +0x8, +0x10, +0x18, +0x20, +0x28, +0x30 |
| `0x665f40` | 5289 | 1092 | 40 | `basic_string::_M_construct null not valid`、`cns_no_fit.cpp` | +0x4, +0x6, +0x8, +0xc, +0x10, +0x18 |
| `0x6673f0` | 6952 | 1375 | 43 | 无 | +0x4, +0x6, +0x8, +0xc, +0x10, +0x18 |
| `0x674680` | 8881 | 1933 | 32 | 无 | +0x4, +0x6, +0x8, +0xc, +0x10, +0x18 |
| `0x68a6e0` | 1125 | 267 | 27 | `..\multi\supervisor.cpp`、`nesting.Bindable(m_problem)` | +0x8, +0xc, +0x10, +0x18, +0x28, +0x2c |
| `0x68f750` | 15812 | 3128 | 55 | `part_number < m_reduced_problem.GetNumberOfP`、`..\multi\float_filler.cpp` | +0x1, +0x4, +0x8, +0x10, +0x18, +0x20 |
| `0x697100` | 40 | 11 | 1 | 无 | +0x18 |
| `0x697130` | 19 | 4 | 0 | 无 | 无 |
| `0x69a690` | 49 | 14 | 1 | 无 | +0x10, +0x20 |
| `0x69a6d0` | 33 | 10 | 0 | 无 | +0x10 |

**两条通道合计**：有类归属的**未引用**函数，RTTI **82** 个、vtable **458** 个、**并集 494**（重叠 46）。

**口径**：“引用了该类 vtable 地址点”是硬事实；「它是构造/析构”是**推论**（需读指令才能定）。

### 附 30 取消钩子与工程已有知识的对照（goal round 91）**[已读]**

**先执行固定检查项 7**（新概念前先搜工程）：六个取消钩子地址在 `lcns/` 里的出现情况见本轮输出。

其次读最大的一个钩子 `0x7D2610`（`Multi::CompactCanceller`，991 B）与 `0x7E80E0`（`Tiling::WarpCanceller`，19 B）：结构数据在本轮输出，结论只写指令能支持的部分。

### 附 31 第七个取消器：代理者（goal round 92）**[已逐条读完 7 条指令]**

`Tiling::WarpCanceller::ProbeCancel` = **`0x7E80E0`**（19 B / 7 条）：取 `[rcx+8]` 作为被包装对象，**空则返回 false**（`xor eax,eax; ret`），否则 **尾调用其 vtable 的 `+0x10` 槽**（即它自己的 `ProbeCancel`）。
⇒ 它是**代理器**（把问题转发给内层），而不是自己答。

**已落到 `lcns`**：`nester.hpp` 新增 `DelegatingCanceller`（与既有 `Canceller` 同一节，**而不是另起一个重复接口**），并在同位置记下 `0x7D2610`（`CompactCanceller::ProbeCancel`）的证据：它自己的函数体里就带着 **`ProbeCancel`**、`m_supervisor`、`Compact cancelled !` 与常量 **0.5 / 1.05 / 60.0** —— **方法名是从二进制里读出来的，不是我编的**。

### 附 32 有证据的第三方归类（goal round 94）**[规则 + 前后数字]**

**规则（严格）**：一个函数被归为库代码，当且仅当 ① 它经 RTTI 或 vtable 地址点引用的**每一个**类都带库名前缀（`N5boost`/`N8CryptoPP`/`N4Json`/`N9__gnu_cxx`/`NSt`/`N5cxx11`/`N3dbg`），且 ② 它**自己没有任何字符串**（无 TU 路径、无断言文本）。保留字符串的函数**不动** —— 领域代码也会捕获 boost 异常。

符合规则者：**29 个函数 / 10829 字节**（third_party 19，toolchain 10）。

**归类前的正式口径**：

```
﻿   cited reachable     :   2049  (2474936 bytes)  -> 53.0% of reachable bytes
=== top 35 NOT-cited reachable functions (the concrete work list) ===
   not-cited reachable: 4132 functions, 2195106 bytes (47.0% of reachable)
=== of the un-cited reachable code (identity evidence required, round 7) ===
   third party to LINK (see third_party/README.md):   379 fns,    55875 B (1.2% of reachable)
   toolchain libstdc++/MinGW                      :   223 fns,   228658 B (4.9%)
   libcns DOMAIN code STILL TO REVERSE            :  3530 fns,  1910573 B (40.9%)
```

### 附 33 逐函数精读（goal round 102）**[入口/调用面/常量/字段]**

#### `0x243820`（15524 B / 2949 条）

* 自带文本：`pv|`
* 被调用者：**83** 个；调用者：**4** 个
* 浮点常量：`0.01`、`0.998`、`0.017453`、`3`、`3`、`0.017453`
* 字段偏移：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`
* 入口指令：`push r15 push r14 push r13 push r12 push rbp`

#### `0x4c5450`（12535 B / 2759 条）

* 自带文本：`from_`、`_fakeoptional`
* 被调用者：**105** 个；调用者：**4** 个
* 浮点常量：无
* 字段偏移：`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x1c`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`
* 入口指令：`push r15 push r14 push r13 push r12 push rbp`

#### `0x17c790`（6634 B / 1674 条）

* 自带文本：`AVAUATUWVSH`
* 被调用者：**13** 个；调用者：**3** 个
* 浮点常量：无
* 字段偏移：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`
* 入口指令：`push r15 push r14 push r13 push r12 push rbp`

### 附 34 逐函数精读（第二批，goal round 104）**[入口/调用面/常量/字段]**

#### `0x1c9c80`（5243 B / 1033 条，调用者 2）

* 自带文本：`Timing = `、`Step=`、` Strips=`、`Width=`
* 被调用者中**自带文本**者：`0x1c97a0`(`!m_logs->empty()`)、`0x1c9c80`(`Timing = `)、`0x1ec0b0`(`Compaction success : `)、`0x677cb0`(`..\nesting\algos\compact.hpp`)
* 浮点常量：`1`、`0.01`、`1`
* 字段偏移：`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`
* 调用序（前 14）：`0x5f3980` `0x1994e0` `0x6dd700` `0x63f6c0` `0x8688e0` `0x63f6b8` `0x6dd700` `0x63f6c0` `0x8688e0` `0x63f6b8` `0x6dd900` `0x1994e0` `0x6dd700` `0x63f6c0`

#### `0x653670`（4698 B / 903 条，调用者 2）

* 自带文本：`%llu`、`bucket_`、`beam_slice_`、`%lld`
* 浮点常量：无
* 字段偏移：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`
* 调用序（前 14）：`0x775600` `0x1bff90` `0x7751e0` `0x1bf170` `0x775c00` `0x7751e0` `0x775c00` `0x239a10` `0x239a10` `0x2399d0` `0x992750` `0x9926b0` `0x992750` `0x910a60`

#### `0x688fa0`（4604 B / 939 条，调用者 2）

* 自带文本：`%lld`、`cc_cost`、`cc_ratio`
* 被调用者中**自带文本**者：`0x545290`(`@w|`)、`0x5f4560`(`Po|`)、`0x68a1a0`(`raw_evaluation_ratio_100`)
* 浮点常量：无
* 字段偏移：`+0x1`、`+0x4`、`+0x6`、`+0x8`、`+0xc`、`+0x10`、`+0x14`、`+0x18`、`+0x1a`、`+0x20`、`+0x38`、`+0x40`
* 调用序（前 14）：`0x2fb50` `0x51c790` `0x9984b0` `0x9984b0` `0xaef30` `0x51c790` `0x9984b0` `0xaef20` `0x6c0e0` `0x51c790` `0x9984b0` `0x5f4560` `0x90ecb0` `0x51c790`

#### `0x687e20`（4478 B / 948 条，调用者 2）

* 自带文本：`Time: `、` sec`、`Memory: `、` mbytes`
* 被调用者中**自带文本**者：`0x688fa0`(`%lld`)、`0x8ab0a0`(`VSH`)
* 浮点常量：无
* 字段偏移：`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x43`、`+0x48`、`+0x50`
* 调用序（前 14）：`0xaf510` `0xaf6a0` `0xaef80` `0x998500` `0x8ab0a0` `0x909e40` `0x8ab100` `0xaef10` `0x998500` `0x97a830` `0x998500` `0x92dee0` `0x998500` `0x998500`

### 附 35 共性切削的评估侧（goal round 105）

#### `0x688fa0`（4604 B / 939 条）

* 自带文本：`%lld`、`cc_cost`、`cc_ratio`
* 浮点常量：无
* 字段偏移：`+0x1`、`+0x4`、`+0x6`、`+0x8`、`+0xc`、`+0x10`、`+0x14`、`+0x18`、`+0x1a`、`+0x20`、`+0x38`、`+0x40`
* 调用序（前 16）：`0x2fb50` `0x51c790` `0x9984b0` `0x9984b0` `0xaef30` `0x51c790` `0x9984b0` `0xaef20` `0x6c0e0` `0x51c790` `0x9984b0` `0x5f4560` `0x90ecb0` `0x51c790` `0x9984b0` `0x9984b0`

#### `0x68a1a0`（1334 B / 319 条）

* 自带文本：`raw_evaluation_ratio_100`、`raw_evaluation_ratio_10`
* 浮点常量：`10`、`1`
* 字段偏移：`+0x8`、`+0xc`、`+0xe`、`+0x10`、`+0x27`、`+0x28`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x58`、`+0x60`
* 调用序（前 16）：`0x528bf0` `0x605bf0` `0x910ba0` `0x51c790` `0x9984b0` `0x9984b0` `0x5297c0` `0x605bf0` `0x51c790` `0x9984b0` `0x9984b0` `0x51c260` `0x4fc2e0` `0x51c260` `0x5452a0` `0x528bf0`

### 附 36 `0x68A1A0` 的四个未归属被调用者（goal round 106）

#### `0x528bf0`（275 B / 59 条，调用者 6，被调用者 7）

* 自带文本：无
* 浮点常量：`0.95`
* 字段偏移：`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x48`、`+0x50`、`+0x58`、`+0x60`、`+0x68`、`+0x70`
* 调用序（前 12）：`0x51c260` `0x4fc230` `0x522d60` `0x522b30` `0x528020` `0x51c260` `0x5461b0` `0x523a40`

#### `0x5297c0`（881 B / 175 条，调用者 5，被调用者 13）

* 自带文本：无
* 浮点常量：`1`
* 字段偏移：`+0x8`、`+0x10`、`+0x14`、`+0x20`、`+0x28`、`+0x30`、`+0x40`、`+0x48`、`+0x50`、`+0x58`
* 调用序（前 12）：`0x51c020` `0x51c020` `0x51d2f0` `0x4f8d30` `0x52f8c0` `0x52f8b0` `0x522d60` `0x528d10` `0x523a40` `0x910ba0` `0x910ba0` `0x60a620`

#### `0x51c260`（496 B / 116 条，调用者 12，被调用者 4）

* 自带文本：无
* 浮点常量：无
* 字段偏移：`+0x8`、`+0x10`、`+0x14`、`+0x16`、`+0x18`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x50`
* 调用序（前 12）：`0x910ba0` `0x910ba0` `0x60a620` `0x9984b0` `0x9984b0` `0x9984b0` `0x9984b0` `0x9984b0` `0x62f280` `0x9984b0`

#### `0x5452a0`（197 B / 54 条，调用者 4，被调用者 5）

* 自带文本：无
* 浮点常量：`0.01`
* 字段偏移：`+0x28`、`+0x30`、`+0x50`、`+0x60`
* 调用序（前 12）：`0x5238b0` `0x524b30` `0x9984b0` `0x5238b0` `0x524890` `0x9984b0` `0x9984b0` `0x62f280`

### 附 37 `0x51C260` 全读与下一环（goal round 107）

#### `0x51C260`（496 B / 116 条，12 个调用者）


#### `0x522d60`（528 B / 126 条，调用者 6）

* 自带文本：无
* 浮点常量：无
* 字段偏移：`+0x8`、`+0x10`、`+0x14`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`
* 调用序（前 10）：`0x51c020` `0x51c020` `0x51d2f0` `0x4f8f80` `0x910ba0` `0x910ba0` `0x60a620` `0x9984b0` `0x9984b0` `0x9984b0`

#### `0x522b30`（555 B / 129 条，调用者 4）

* 自带文本：无
* 浮点常量：无
* 字段偏移：`+0x8`、`+0x10`、`+0x14`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`
* 调用序（前 10）：`0x51c020` `0x51c020` `0x51d2f0` `0x4f8d30` `0x910ba0` `0x910ba0` `0x60a620` `0x9984b0` `0x9984b0` `0x9984b0`

#### `0x5461b0`（904 B / 202 条，调用者 3）

* 自带文本：无
* 浮点常量：无
* 字段偏移：`+0x8`、`+0x10`、`+0x18`、`+0x1a`、`+0x1c`、`+0x1e`、`+0x20`、`+0x28`
* 调用序（前 10）：`0x4fc2e0` `0x4fc2d0` `0x544ec0` `0x523630` `0x524b30` `0x545cf0` `0x9984b0` `0x4fbe50` `0x544ec0` `0x910ba0`

#### `0x523a40`（1044 B / 264 条，调用者 7）

* 自带文本：无
* 浮点常量：`0.5`
* 字段偏移：`+0x1`、`+0x8`、`+0x10`、`+0x14`、`+0x18`、`+0x1c`、`+0x28`、`+0x30`
* 调用序（前 10）：`0x51c250` `0x910ba0` `0x910ba0` `0x60a620` `0x9984b0` `0x9984b0` `0x9984b0` `0x51c260` `0x523630` `0x5238b0`

#### `0x5238b0`（193 B / 60 条，调用者 19）

* 自带文本：无
* 浮点常量：无
* 字段偏移：`+0x8`、`+0x10`
* 调用序（前 10）：`0x4fc5a0` `0x998500` `0x63f2e8` `0x4fc5b0` `0x4f7060` `0x4fc5a0` `0x9984b0` `0x62f280`

#### `0x524b30`（735 B / 169 条，调用者 7）

* 自带文本：无
* 浮点常量：无
* 字段偏移：`+0x1`、`+0x8`、`+0x10`、`+0x14`、`+0x18`、`+0x20`、`+0x28`、`+0x2c`
* 调用序（前 10）：`0x4fc5a0` `0x910ba0` `0x910ba0` `0x910ba0` `0x60a620` `0x9984b0` `0x9984b0` `0x9984b0` `0x4fc5b0` `0x4f7660`

#### `0x524890`（669 B / 154 条，调用者 6）

* 自带文本：无
* 浮点常量：无
* 字段偏移：`+0x1`、`+0x8`、`+0x10`、`+0x14`、`+0x18`、`+0x20`、`+0x28`、`+0x2c`
* 调用序（前 10）：`0x4fc5a0` `0x910ba0` `0x910ba0` `0x60a620` `0x9984b0` `0x9984b0` `0x9984b0` `0x4fc5b0` `0x4f7640` `0x9984b0`

### 附 38 桶 A 第 1 批：自带文本的未引用函数（goal round 112）

#### `0x65a8c0`（3926 B / 954 条，调用者 16）

* 自带文本：`map::at`
* 被调用者中带文本者：`0x60a620`(`*** INTERNAL ERROR: please contact suppo`)、`0x65a8c0`(`map::at`)
* 浮点常量：`1.5`
* 字段偏移：`+0x1`、`+0x2`、`+0x4`、`+0x8`、`+0x10`、`+0x14`、`+0x16`、`+0x18`、`+0x20`、`+0x24`
* 调用序（前 10）：`0x97aba0` `0x910ba0` `0x910ba0` `0x60a620` `0x9984b0` `0x9984b0` `0x9984b0` `0x9984b0` `0x8fdfa0` `0x998500`

#### `0x173760`（3892 B / 900 条，调用者 5）

* 自带文本：``$ck`
* 浮点常量：`1`
* 字段偏移：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`
* 调用序（前 10）：`0x1783e0` `0x998500` `0x998500` `0x998500` `0x5cee50` `0x5ce7b0` `0x5ce970` `0x5d0500` `0x8c4530` `0x9989a0`

#### `0x16f350`（3829 B / 751 条，调用者 2）

* 自带文本：`remaining.size() == res.size()`
* 被调用者中带文本者：`0x60a620`(`*** INTERNAL ERROR: please contact suppo`)
* 浮点常量：无
* 字段偏移：`+0x1`、`+0x4`、`+0x8`、`+0x10`、`+0x14`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`
* 调用序（前 10）：`0x5c4cf0` `0x944530` `0x9454d0` `0x9454d0` `0x8aab00` `0x9454d0` `0x978010` `0x978010` `0x8693d0` `0x978010`

#### `0x608f60`（3745 B / 829 条，调用者 2）

* 自带文本：`True`、`true`、`false`、`False`
* 浮点常量：`1`
* 字段偏移：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`
* 调用序（前 10）：`0x606310` `0x82a3e0` `0x606310` `0x8aab00` `0x8aaaf0` `0x8aaaf0` `0x8aaaf0` `0x8aaaf0` `0x9916e0` `0x8aabc0`

#### `0x6d4ad0`（3574 B / 795 条，调用者 3）

* 自带文本：`333333`
* 浮点常量：`0.1`、`0.5`、`1`、`1.2`、`1.3`、`1.4`
* 字段偏移：`+0x1`、`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`
* 调用序（前 10）：`0x8bb280` `0x910af0` `0x90c0a0` `0x910af0` `0x90c0a0` `0x910af0` `0x90c0a0` `0x910af0` `0x90c0a0` `0x910af0`

#### `0x1adc20`（3261 B / 655 条，调用者 3）

* 自带文本：`choosen`、`database`
* 被调用者中带文本者：`0x1aaef0`(`new`)、`0x1acf30`(`..\nesting\algos\multinesting_optimizer.`)、`0x1ad3a0`(`..\nesting\algos\multinesting_optimizer.`)、`0x1ad7e0`(`..\nesting\algos\multinesting_optimizer.`)、`0x1fb810`(`..\nesting\ios\log_ios.cpp`)
* 浮点常量：`0.25`、`0.999`、`3`
* 字段偏移：`+0x8`、`+0xc`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`
* 调用序（前 10）：`0x1a6320` `0x1c0750` `0x183f60` `0x1fb5f0` `0x775500` `0x775600` `0x775c00` `0x1bb490` `0x1bd410` `0x1be400`

### 附 39 `0x1ADC20` 深读：多排样优化器的 choosen/database（goal round 113）

* 规模：3261 B / 655 条，调用者 3；自带文本：`choosen`、`database`

**常量 `0.999`（加载于 `0x1ae387`）的上下文**：

```
1ae36d   call 0x183f60
1ae372   test eax, eax
1ae374   je 0x1ae4fa
1ae37a   mov rcx, qword ptr [rsp + 0xc68]
1ae382   call 0x1f8410
1ae387   movsd xmm6, qword ptr [rip + 0x811249]
1ae38f   mov rcx, r13
1ae392   mulsd xmm6, xmm0
```

**常量 `3`（加载于 `0x1ae646`）的上下文**：

```
1ae628   mov eax, dword ptr [rax + 0xc]
1ae62b   jmp 0x1ae132
1ae630   mov qword ptr [rsp + 0x78], 4
1ae639   lea rdx, [rsp + 0x70]
1ae63e   lea rbx, [rsp + 0x8b0]
1ae646   lea rax, [rip + 0x810cf3]
1ae64d   mov rcx, rbx
1ae650   mov qword ptr [rsp + 0x70], rax
```

**常量 `0.25`（加载于 `0x1ae698`）的上下文**：

```
1ae682   imul rcx, rdx
1ae686   test rcx, rcx
1ae689   js 0x1ae7a2
1ae68f   pxor xmm0, xmm0
1ae693   cvtsi2sd xmm0, rcx
1ae698   mulsd xmm0, qword ptr [rip + 0x810f20]
1ae6a0   mov eax, eax
1ae6a2   pxor xmm1, xmm1
```

### 附 40 桶 A 第 2 批（goal round 114）

#### `0x69be80`（3226 B / 668 条，调用者 3）

* 自带文本：`m_base && "call SetActiveNesting first"`、`GetActiveParts`
* 被调用者中带文本者：`0x4fc5b0`(`..\structure\problem.cpp`)、`0x60a620`(`*** INTERNAL ERROR: please contact sup`)
* 浮点常量：无
* 字段偏移：`+0x8`、`+0x10`、`+0x12`、`+0x18`、`+0x20`、`+0x22`、`+0x28`、`+0x30`、`+0x34`、`+0x38`

#### `0x1ac390`（2962 B / 597 条，调用者 2）

* 自带文本：`never`、`pos1`、`pos2`
* 被调用者中带文本者：`0x1aa460`(`#################### Map Stats #######`)
* 浮点常量：`0.1`、`0.25`、`0.3`、`0.33`、`0.5`、`0.66`
* 字段偏移：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`、`+0x48`、`+0x50`

#### `0xbdc50`（2727 B / 667 条，调用者 1）

* 自带文本：`VSH`、`PSSR_MEM: message recovery disabled`
* 浮点常量：无
* 字段偏移：`+0x1`、`+0x2`、`+0x3`、`+0x4`、`+0x5`、`+0x6`、`+0x7`、`+0x8`、`+0x9`、`+0x10`

#### `0x6dc7f0`（2679 B / 518 条，调用者 2）

* 自带文本：`VSH`、`thread.entry_event`、`thread.exit_event`、`thread`
* 被调用者中带文本者：`0x6eaf20`(`VSH`)
* 浮点常量：无
* 字段偏移：`+0x8`、`+0xc`、`+0x10`、`+0x14`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`

#### `0x625f20`（2652 B / 674 条，调用者 11）

* 自带文本：`auto`、`decltype(auto)`
* 被调用者中带文本者：`0x6242f0`(`_GLOBAL_`)、`0x625920`(`string literal`)、`0x625f20`(`auto`)
* 浮点常量：无
* 字段偏移：`+0x1`、`+0x2`、`+0x8`、`+0x10`、`+0x12`、`+0x18`、`+0x20`、`+0x28`、`+0x2c`、`+0x30`

#### `0x6daec0`（2636 B / 516 条，调用者 2）

* 自带文本：`VSH`、`thread.entry_event`、`thread.exit_event`、`thread`
* 被调用者中带文本者：`0x6eaf20`(`VSH`)
* 浮点常量：无
* 字段偏移：`+0x8`、`+0xc`、`+0x10`、`+0x14`、`+0x18`、`+0x20`、`+0x28`、`+0x30`、`+0x38`、`+0x40`

### 附 41 桶 A 的真实规模与新恢复的 API 名（goal round 115）

* `0x69BE80` 的断言原文给出两个**真实方法名**：`SetActiveNesting`、`GetActiveParts`，并说明后者的**前置条件**（先 Set 才能 Get）；断言的条件本身是 `m_base` 非空。
* 桶 A 按**库标记串**（`PSSR_MEM`、`thread.entry_event`、`decltype(auto)`、`map::at` 等）重算：库代码 **8** 个，**剩余领域文本函数 187 个**。

### 附 42 桶 A 第 3 批（名字类文本优先，goal round 116）

#### `0x6e82a0`（144 B / 32 条，调用者 3）

* 自带文本：`C:\Users\renaud\nest\external\boost_1_63_0/boost/multiprecis`、`Subtraction resulted in a negative value, but the type is un`、`void boost::multiprecision::backends::detail::raise_subtract`
* 其中**工程里尚无**的标识符：`cpp_int`
* 浮点常量：无

#### `0x60d380`（1536 B / 376 条，调用者 2）

* 自带文本：`no COFF symbols`、`magic number in optional header not recognized`、`size of optional header did not match expectation`、`invalid size in COFF string table`
* 其中**工程里尚无**的标识符：无
* 被调用者中带文本者：`0x60c2f0`(`bad stream cursor position specified`)、`0x60c430`(`bad stream cursor position specified`)、`0x60c5c0`(`failed to read from file`)
* 浮点常量：无

#### `0x874dd0`（1130 B / 154 条，调用者 7）

* 自带文本：`%m/%d/%y`、`%H:%M:%S`、`Sunday`、`Monday`
* 其中**工程里尚无**的标识符：`anuary`、`aturday`、`ctober`、`ebruary`、`ecember`
* 浮点常量：无

#### `0x12ba20`（354 B / 102 条，调用者 2）

* 自带文本：`sntl_admin_context_new`、`sntl_admin_get`、`sntl_admin_free`、`sntl_admin_context_delete`
* 其中**工程里尚无**的标识符：无
* 浮点常量：无

#### `0x6e8110`（215 B / 51 条，调用者 4）

* 自带文本：`overflow in `、`C:\Users\renaud\nest\external\boost_1_63_0/boost/multiprecis`、`void boost::multiprecision::backends::detail::raise_overflow`
* 其中**工程里尚无**的标识符：`cpp_int`
* 浮点常量：无

#### `0x8268e0`（316 B / 65 条，调用者 1）

* 自带文本：`space`、`print`、`cntrl`、`upper`
* 其中**工程里尚无**的标识符：`alnum`、`blank`、`cntrl`
* 浮点常量：无

### 附 43 镜像里的**构建树路径**（goal round 117）**[每条带函数地址]**

原始构建根：`C:\Users\renaud\nest\`。以下是从镜像字符串里枚举出的路径，分为**原工程自己的文件**与**external 下的第三方库**。

**external 库名（出现次数）**：`Clp-1.15.3`(15)、`boost_1_63_0`(10)


### 附 44 按**自带文本**判定库代码（goal round 118）

**规则**：一个函数的**每一条**自带文本都命中库证据模式（`external\` 路径、库文件名、或这些库已知的消息文本）⇒ 库代码，**命中的模式逐个存储**作为证据。

本批：库代码 **188** 个 / 263623 字节；剩余“领域文本” **178** 个 / 108435 字节。

使用的证据前几：`vector::`(97)、`basic_string`(82)、`PK_`(4)、`AllocatorBase`(3)、`Clp`(1)、`IteratedHashBase`(1)

### 附 45 桶 A 剩余部分：线程生命周期与其他（goal round 119）

#### `0x1cc0`（427 B / 116 条，调用者 2，被调用者 9）

* 自带文本：`// LocalCancel waiting for threads termination`
* 浮点常量：无
* 调用序（前 10）：`0x63f6c0` `0x63f6b8` `0x63f6c0` `0x63f6b8` `0x64aea0` `0x63f6c0` `0x8ab100` `0x63f6c0` `0x9984b0` `0x63f6b8`

#### `0x5d90`（427 B / 117 条，调用者 2，被调用者 10）

* 自带文本：`// LocalTerminate waiting for threads termination`
* 浮点常量：无
* 调用序（前 10）：`0x63f6c0` `0x63f6b8` `0x63f6c0` `0x63f6b8` `0x64aea0` `0x63f6c0` `0x8ab100` `0x63f6c0` `0x9984b0` `0x63f6b8`

#### `0x86160`（1234 B / 305 条，调用者 3，被调用者 17）

* 自带文本：`__small_mark__`、`__big_mark__`
* 浮点常量：`0.5`
* 调用序（前 10）：`0x504ef0` `0x4fc1f0` `0x97a040` `0x54cbb0` `0x4f7740` `0x54cbb0` `0x4f7770` `0x4f7630` `0x97a040` `0x5c3d90`

#### `0xbafd0`（150 B / 39 条，调用者 3，被调用者 7）

* 自带文本：`PK_MessageEncodingMethod: this signature scheme does not support messa`
* 浮点常量：无
* 调用序（前 10）：`0x9988c0` `0xbaf30` `0x7b1f70` `0x9984b0` `0x999030` `0x998c70` `0x62f280` `0x9984b0`

#### `0x12abd0`（467 B / 120 条，调用者 2，被调用者 6）

* 自带文本：`GetOd`、`_GetOd@4`
* 浮点常量：无
* 调用序（前 10）：`0x12a990` `0x12a710` `0x7c30c0` `0x9984b0` `0x910af0` `0x9984b0` `0x62f280`

### 附 46 线程生命周期对：`0x1CC0` / `0x5D90`（goal round 120）**[全读]**

#### `0x1cc0`（427 B / 116 条，LocalCancel）

* 自带文本：`// LocalCancel waiting for threads termination`
* 调用者 2、被调用者 9：`0x62f280` `0x63f6b8` `0x63f6c0` `0x64aea0` `0x8761b0` `0x8ab100` `0x97abf0` `0x990e80` `0x9984b0`

#### `0x5d90`（427 B / 117 条，LocalTerminate）

* 自带文本：`// LocalTerminate waiting for threads termination`
* 调用者 2、被调用者 10：`0x53c0` `0x62f280` `0x63f6b8` `0x63f6c0` `0x64aea0` `0x8761b0` `0x8ab100` `0x97abf0` `0x990e80` `0x9984b0`

### 附 47 线程关闭状态门与下一批（goal round 124）

#### `0x3c110`（639 B / 160 条，调用者 2，被调用者 15）

* 自带文本：`basic_string::append`、`enlarged_`
* 浮点常量：`1`
* 字段偏移：`+0x8`、`+0x9`、`+0x10`、`+0x18`、`+0x20`、`+0x38`、`+0x40`、`+0x48`
* 调用序（前 10）：`0x4f8370` `0x4f9bc0` `0x4f9e80` `0x4f8350` `0x9108e0` `0x910a60` `0x910a60` `0x4f8370` `0x4f8380` `0x998500`

#### `0x86160`（1234 B / 305 条，调用者 3，被调用者 17）

* 自带文本：`__small_mark__`、`__big_mark__`
* 浮点常量：`0.5`
* 字段偏移：`+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x38`、`+0x40`、`+0x60`、`+0x68`
* 调用序（前 10）：`0x504ef0` `0x4fc1f0` `0x97a040` `0x54cbb0` `0x4f7740` `0x54cbb0` `0x4f7770` `0x4f7630` `0x97a040` `0x5c3d90`

#### `0x12abd0`（467 B / 120 条，调用者 2，被调用者 6）

* 自带文本：`GetOd`、`_GetOd@4`
* 浮点常量：无
* 字段偏移：`+0x8`、`+0x10`、`+0x20`、`+0x30`、`+0x4c`、`+0x50`、`+0x58`、`+0x60`
* 调用序（前 10）：`0x12a990` `0x12a710` `0x7c30c0` `0x9984b0` `0x910af0` `0x9984b0` `0x62f280`

### 附 48 `1.000001` 与 `+0x4C` 的交叉核对（goal round 125）

* `0x3C110`（自带 `enlarged_`）加载 **`1.000001`** ⇒ 已作为 `kRelativeEpsilon` 落进 `engine.hpp`（比 `kToleranceUpper = 1.001` 紧一个数量级）。
* `0x12ABD0` 访问 **`+0x4C`** 的次数与比较值：见本轮输出（若出现 9/10 以外的值，则状态机可扩展；若只读不比，则如实记为“只读”）。

### 附 49 两个带“机制名”的函数（goal round 127）

**`0x86160` 引用 `__small_mark__`（@`0x862bf`）的上下文**：

```
8629c    call 0x5c6be0
862a1    lea r13, [rsp + 0xc0]
862a9    lea rax, [r13 + 0x10]
862ad    mov rcx, r13
862b0    lea r8, [rip + 0x92b631]
862b7    mov qword ptr [rsp + 0xc0], rax
862bf    lea rdx, [rip + 0x92b614]
862c6    call 0x84ac0
862cb    mov qword ptr [rsp + 0x20], rdi
862d0    mov r9, rsi
```

**`0x86160` 引用 `__big_mark__`（@`0x86440`）的上下文**：

```
86421    mov rcx, rdi
86424    call 0x5c6be0
86429    lea rax, [r12 + 0x10]
8642e    mov rcx, r12
86431    lea r8, [rip + 0x92b4bd]
86438    mov qword ptr [rsp + 0xe0], rax
86440    lea rdx, [rip + 0x92b4a2]
86447    call 0x84ac0
8644c    mov qword ptr [rsp + 0x20], rsi
86451    mov r9, rdi
```

**`0x86160` 加载 `0.5`（@`0x8622f`）的上下文**：

```
86217    mov rcx, rdi
8621a    call 0x5c3d90
8621f    lea rax, [rsp + 0x100]
86227    movapd xmm1, xmm6
8622b    movapd xmm7, xmm6
8622f    movsd xmm0, qword ptr [rip + 0x92b779]
86237    xorpd xmm7, xmmword ptr [rip + 0x92b781]
8623f    mov rcx, rax
```

* `0x86160`：被调用者 17 个；字段 `+0x8`、`+0x10`、`+0x18`、`+0x20`、`+0x38`、`+0x40`、`+0x60`、`+0x68`、`+0x80`、`+0xa0`

**`0x3c110` 引用 `enlarged_`（@`0x3c204`）的上下文**：

```
3c1e2    movabs rax, 0x7fffffffffffffff
3c1ec    sub rax, qword ptr [rsp + 0x48]
3c1f1    cmp rax, 8
3c1f5    jbe 0x3c346
3c1fb    mov r8d, 9
3c201    mov rcx, rbp
3c204    lea rdx, [rip + 0x97311d]
3c20b    call 0x910a60
3c210    mov r8, qword ptr [rbx + 8]
3c214    mov rcx, rbp
```

**`0x3c110` 加载 `1`（@`0x3c178`）的上下文**：

```
3c160    mov rcx, r8
3c163    mov qword ptr [rsp + 0x38], rdx
3c168    movsd xmm6, qword ptr [r9 + 0x18]
3c16e    call 0x4f8370
3c173    mov rdx, qword ptr [rsp + 0x38]
3c178    mulsd xmm0, qword ptr [rip + 0x973620]
3c180    ucomisd xmm6, xmm0
3c184    jbe 0x3c135
```

* `0x3c110`：被调用者 15 个；字段 `+0x8`、`+0x9`、`+0x10`、`+0x18`、`+0x20`、`+0x38`、`+0x40`、`+0x48`、`+0x50`、`+0x60`

### 附 50 增长溢出守卫与三参数日志例程（goal round 128）

* **已落 `lcns`**：`exceedsGrowthLimit(n)` 完全按 `0x3C110` 的四条指令转写（`INT64_MAX − n ≤ 8`），并加边界测试（room=8 失败、room=9 通过）。
* **`0x84AC0`**（`__small_mark__`/`__big_mark__` 两处都调用它，入参为缓冲区、标记名、另一串）：177 B / 60 条，自带文本 `无`，被调用者 3 个，常量 `无`。

### 附 51 `0x5C6BE0` 与两个标记的上下文（goal round 129）

* **`0x5C6BE0`**（65 B / 19 条，**46 个调用者**）：一次性清零 `[rcx]`/`[rcx+8]`/`[rcx+0x10]`
  —— 即**24 字节头部**（`std::vector` 形状）——然后调 `0x8C4530`；
  异常路径调 `0x8C5090` + `0x62F280`（重抛）⇒ **容器默认构造助手（带 RAII 清理）**。
* **`0x86160` 两个标记之间**：先把**两个 double 各存两处**（`[rsp+0x130]/[rsp+0x138]` 与 `[rsp+0xe0]/[rsp+0xe8]`）
  ⇒ 形如**两个二维点**；随后 `call 0x5CA780`（几何运算）、`call 0x5C6BE0`（建容器）、
  再 `call 0x84AC0`（拼标记行，`rdx='__small_mark__'`、`r8=另一串`）、最后 `call 0x501660`（`r8d=1`）。
  ⇒ 标记行的两个输入是**两个坐标**；“small/big”的选择分支在本轮窗口之后，**尚未读到**。

**口径**：清零三个八字节与两个 double 的存储位置是指令事实；
“两个点”与“容器”是对形态的读法。

### 附 52 两个标记是**阶段标记**，不是尺寸阈值（goal round 130）**[否定结果]

假设：`small/big` 由某个尺寸/面积阈值决定。**该假设不成立**。

在两个标记之间（`0x862C6`…`0x86447`）的**分支骨架**里：

* **没有任何浮点比较**（无 `comisd`/`ucomisd`，也无浮点常量）；
* 出现的比较全是**指针比较**（`cmp rbp,rdi`、`cmp rsi,r15`、`cmp rdi,rsi`），
  且夹着**大量 `call 0x9984B0`（operator delete）**；
* 两个标记前的形态**完全对称**：各自先存**两个 double**（`small` 用 `xmm0/xmm1`，
  `big` 用 `xmm6/xmm7`），再 `call 0x5CA780`（几何运算）、`call 0x5C6BE0`（建 24 字节容器）、`call 0x84AC0`（拼标记行）。

⇒ 合理读法：**它们是同一例程里两个相继阶段的标记**（前一阶段的容器在中间被拆除），
**而不是按尺寸分支**。`small/big` 很可能指的是**阶段名**（如“先粗后细”），
但**本轮只能说“不是尺寸阈值”**，它们到底指什么尚无证据。

**口径**：“区间内无浮点比较”与“两标记前形态对称”是指令事实；
“阶段标记”是推读。

### 附 53 `0x1AC390` 的比例算式（goal round 131）**[已读到算式，语义未定]

规模 2,962 B / 597 条；自带文本 `never`、`pos1`、`pos2`（分别引用于
`0x1AC433`/`0x1AC976`/`0x1ACD4E`）；24 个被调用者。

**读到的算式（指令层面）**：

```
1AC5BF  test edx,edx
1AC5C1  jle  0x1AC5D1
1AC5C3  movsd xmm11,[0.3]        ; 仅当 edx > 0
1AC5CC  mulsd xmm11, xmm6        ;   xmm11 = 0.3 * xmm6
        （否则 xmm11 = xmm8，即保持原值）
...
1AC753  movsd xmm2,[0.33]
1AC760  mulsd xmm2, xmm11        ; xmm2 = 0.33 * xmm11
```

⇒ **两阶段缩放：`0.33 × (0.3 × v)`，且第一阶段（`0.3`）受 `edx > 0` 门控**；
`0.5`/`0.25`/`0.1` 分别装入 `xmm10`/`xmm12`/`xmm13`，看位置像**迭代求解的上/下限**。

**本轮不落码**：`v`、`edx` 与那三个限值的**含义未确认**，
写成函数就是猜。已按惯例记录算式与常量加载位置，待读到操作数来源后再落。

### 附 54 `never`/`pos1`/`pos2` 是**输出字段名**，不是枚举（goal round 133）

**全镜像只有 7 个这类短名**：`auto`、`left`、`never`、`none`、`pos1`、`pos2`、`right`
（各 1–3 次），分散在 11 个函数里 ⇒ **不存在所谓“选项词汇表**。

**用法（逐条指令）**：`pos1` @ `0x1AC976` 与 `pos2` @ `0x1ACD4E` 都是

```
1AC96B  lea rcx,[rsp+0xa0]        ; 第 1 个参数（目标/缓冲）
1AC963  mov rdx,[rsp+0x390]       ; 第 2 个参数（值）
1AC976  lea r8,[pos1]            ; ★ 第 3 个参数 = 字段名
1AC973  mov r9,rdi                ; 第 4 个参数
1AC97D  call 0x92D500
```

⇒ **它们是写进某种结构化输出的字段名**（形如 `(context, value, "pos1", ...)`），
很可能是 JSON/CSV；`never` 同样是一个**值/关键字**（它出现在 `0x1AC390`、`0x1AEE00`、`0x1B33B0` 三处）。

**因此对 `0x1AC390` 的整体定性（推断，但有两条独立证据）**：它既算 **质量指标**
（`0.33 × 0.3 × avg(a×b)`，round 132）又**写报告**（字段 `pos1`/`pos2`/`never`）
⇒ 很可能是**排样结果的评估/导出例程**。

**口径**：“只有 7 个短名”、“三个参数的位置”是事实；“JSON/CSV 导出”是推断。

### 附 55 `0x92D500` 是**容器插入助手**，不是文档写入器（goal round 134）

规模 284 B / 86 条，3 个调用者，10 个被调用者；**自带文本：无**；无浮点常量。

```
入口：mov ecx, 0x60          ← 申请 96 字节（一个节点）
      call 0x89E0D0 / 0x92C7B0 / 0x92DBF0 …
```

⇒ 它**分配并链接一个 96 字节节点**（即**把一个 (名字,值) 插入内存中的容器**），
**不是**直接写 JSON/CSV/HTML。

**因此修正 round 133 的推断**：`pos1`/`pos2` 先被插入**结构化容器**，
**写文档的那一步在别处**（尚未读到）；“JSON/CSV”仍为可能，但**本轮证据只支持到“容器”**。

**口径**：“无自带文本”、“申请 0x60 字节”是指令事实；“节点/容器插入”是对形态的读法。

### 附 56 容器的第二个使用者：带**随机种子**的大例程（goal round 135）

`0x92D500`（插入 96 字节节点）的调用者只有 **2** 个：

| 调用者 | 规模 | 自带文本 |
|---|---:|---|
| `0x1AC390` | 2,962 B / 597 条 | `never`、`pos1`、`pos2` |
| **`0x1B33B0`** | **9,910 B / 1,946 条** | `never`、**`Using seed `**、`vector::_M_range_check` |

⇒ **新的领域事实**：`0x1B33B0` 会打印 **`Using seed `**（**随机种子的可复现性记录**），
说明它是**带种子的随机搜索**（或随机初始化）例程；
而它与 `0x1AC390` **共用同一个结果容器**（都调 `0x92D500` 插入）
⇒ 两者属**同一套评估/统计输出**。

**工具层面**：本轮脚本在打印调用点时误用了 `ins.mem`（对没有内存操作数的指令取属性）而中断，
**上面的结论只用到它成功打印的部分**；下一次读调用点会用正确的属性名。

### 附 57 种子的推导与两个位置插入点（goal round 136）**[逐条读到]**

**（一）种子是算出来的，不是读时钟**（`0x1B33B0`，`Using seed ` @ `0x1B3446`）：

```
1B340B  mov edx,[rsi+8]              ; 对象状态（偏移 +8）
1B3411  movsd xmm2,[r13]
1B3427  call 0x1A9060                ; 先算一个值
1B342C  mulsd xmm0,[rip + 0x80C0FC]  ; × 一个缩放常量
1B3434  cvttsd2si rax,xmm0           ; ⇒ ★ 种子
1B3439  mov [rsp+0xe0],rax
1B3446  lea rdx,['Using seed '] ; 1B3450 call 0x6DD680   ; 写标签
1B3455  lea rdx,[rsi+0x24]     ; 1B345C call 0x6DE080   ; 写数值
```

⇒ **种子由对象状态推导**（无时钟调用），这正是它被**记入日志以便复现**的原因。
**尚未读**：`0x80C0FC` 处的缩放常量到底是多少（已列为下一步，**不猜**）。

**（二）`0x1AC390` 的两个插入点对称**：

```
1AC951  divsd xmm0,xmm9 ; 1AC956 cvttsd2si eax,xmm0   ; 商截断为整数（pos2 处 1ACD29 同形）
1AC96B  lea rcx,[rsp+0xa0]   ; 容器
1AC963  mov rdx,[rsp+0x390]  ; 值
1AC976  lea r8,['pos1']      ; ★ 字段名
1AC973  mov r9,rdi           ; 元素指针（之后 add rdi,0x10）
1AC97D  call 0x92D500
```

⇒ **每个元素记两个位置度量**（都是除以 `xmm9` 后截断的商），名字就是 `pos1`/`pos2`。

**检查项 7**：`lcns` 已有 `seed` 80 处、`mt19937` 12 处、`random_device` 2 处 ⇒ **随机种子这个概念工程里已有**，本轮不新建。

### 附 58 种子的缩放常量 = `1000000.0`，与对 round 136 的**更正**（goal round 137）

**地址口径修正**：`0x80C0FC` 是 **RIP 相对位移**，不是 RVA。正确解析 = `0x1B342C + 8 + 0x80C0FC` = **rva `0x9BF530`**（与 `never`@`0x9BEF44` **同一只读区**，互相印证）。

**读出的值**：

| rva | 值 |
|---|---:|
| `0x9BF528` | `0.9999` |
| **`0x9BF530`** | **`1000000.0`** |
| `0x9BF538` | `-1.0` |

⇒ 种子 = **`(int)(f(…) × 1e6)`**，即**按微秒缩放**的量 ⇒ `f` 很可能是**时间源**。

**更正 round 136**：当时我写“种子由对象状态推导（无时钟调用）”——**我并没有读 `0x1A9060` 的内部**，那句话**超出了证据**。现已据 `1e6` 这个缩放将“时间源”列为**主要假设**，并在本轮检查 `0x1A9060` 的被调用者以定性。

**两个新常量**：`0.9999`、`-1.0`（同一数据块，**使用点尚未读到**，不落码）。

### 附 59 种子来自**应用自己的 QPC 计时器**（goal round 138）**[假设→事实]

**决定性证据**：

1. 镜像里有**计时器自己的失败文本**：`'Timer: QueryPerformanceCounter failed with error '`（`0x9B6790`）、`'Timer: QueryPerformanceFrequency failed with error '`（`0x9B67C8`）；
2. `0x178590` / `0x1785C0`（各 38 字节）都调 `0x5CD800` 后**相减两个 double 字段**（`[rsp+0x38]−[rsp+0x28]` 与 `[rsp+0x40]−[rsp+0x30]`）⇒ **两个“已经历时长”访问器**；
3. 配合 `kSeedScale = 1e6` ⇒ 种子 = **微秒量级的历时**。

⇒ round 137 的“时间源”假设**已成为事实**。

**同时排除一个候选**：`0x62FD90`（138 字节 / 29 条 / 18 个调用者）**不是计时器**，而是把值归一化到 **(−0.5, 0.5]** 的助手（对 `0.0`/`0.5` 做 `ucomisd`，用 `±1.0` 步进，负分支用符号位 `0x8000000000000000` 取反）——与已恢复的 `normaliseAngle` **是两个不同函数**，待下一轮读完再定性。

### 附 60 更正 round 138 的因果链（goal round 139）**[反向证据]**

round 138 根据“两个 38 字节访问器调 `0x5CD800` 后相减两个 double”推论它们是**计时器的历时访问器**。本轮读了 `0x5CD800`，**该推论不成立**：

* `0x5CD800` = **610 字节 / 145 条 / ★ 113 个调用者** —— 这是**通用助手**的规模；
* 它以 **`0x30` 步长**遍历容器（`5CD860 add rbx,0x30`，配 `0x5C61D0`/`0x5C5F30`/`0x5C5260`）；
* 并构造一个 **25 字符串**（`5CD8A8 mov qword [rsp+0x50],0x19` + `basic_string::_M_create`）。

**保留（仍为事实）**：镜像确实携带计时器自己的失败文本（`0x9B6790` / `0x9B67C8`）⇒ **应用确实拥有 QPC 计时器**（字符串层面的事实，不依赖上述链条）。

**不成立**：“这一条调用链就是那个计时器”。

**因此种子的乘数目前只能说是**“两个计算量之差 × 1e6”**，**是否为时间尚未证实**。`0x62F940`（归一化助手内部调用的那个）**本轮未读到**，不作声明。

### 附 61 两个函数都从**各自入口**读完：内联 `round()` 与 (−0.5, 0.5] 包裹（goal round 140）

**`0x62F940`（215 B / 45 条 / ★ 0 个被调用者 / 47 个调用者）= 编译器内联的 `round()`**：

```
62F940  movq rax,xmm0 ; 62F948 sar rcx,0x34 ; 62F94C and ecx,0x7ff ; 62F952 sub ecx,0x3ff
62F958  cmp ecx,0x33 ; jg <已是整数>
62F96E  movabs rdx,0xFFFFFFFFFFFFF ; 62F978 sar rdx,cl   ; 小数掩码
62F984  addsd xmm0,[1e300] ; 62F98C ucomisd … ; 62F996 test rax,rax ; jle …
62F99B  movabs r8,0x10000000000000 ; 62F9A5 shr r8,cl ; 62F9A8 add rax,r8   ; 加半个 ulp
62F9AB  not rdx ; 62F9AE and rax,rdx                            ; 截断
```

⇒ **四舍五入（中间值远离零）**，负指数分支镜像同样处理符号。

**`0x62FD90` = 用它包装的 (−0.5, 0.5] 归一化**（入口已读，round 138 已看全身）：`round(x)`、`round(x)−x`、若 `> 0.5` 则 `−1.0`。

**两者均已落进 `lcns/geom.hpp`**（`wrapToHalf` / `halfFraction`），并加测试（含 `x=0.3/0.6/−0.6/0.5/−0.5` 与一个循环验证 `[−0.5, 0.5)`）。

### 附 62 `0x1A9060` **全读**：一个完整可判定的聚合/比值算法（goal round 141）

```
1A908B  rbx=[rcx] ; 1A908E rsi=[rcx+8]     ; 容器 [begin,end)
1A9092  edi=edx                            ; 整数计数
1A9094  xmm8=xmm2                          ; 阈值参数
循环（add rbx,0xF0）：
   1A90B3 call 0x1785C0 ; 1A90C2 maxsd xmm7,xmm0
   1A90C6 call 0x178590 ; 1A90CE maxsd xmm6,xmm0
1A90E4  cvtsi2sd xmm0,edi ; 1A90ED divsd xmm6,xmm0   ; 两个峰值之和 / 计数 = 平均
1A90E8  ucomisd xmm8,0 ; jbe <直接返回平均>
1A90F8  xmm0 = 阈值/平均 ; 1A90FC call 0x62FD90   ; 取最近整数
1A9112  eax=(int)xmm0 ; 1A911B cmp eax,200 ; 1A9120 cmovl eax,200   ; 下限 200
1A910A  xmm6=[0.9999] ; 1A9116 mulsd xmm6,xmm8 ; 1A9127 divsd xmm6,xmm1
```

⇒ **已恢复**：步长 `0xF0`（240 字节）、两个逐元素峰值的平均、阈值为正时的
`0.9999 × 阈值 / max(round(阈值/平均), 200)`、以及两个常量 `0.9999`、`200`。
**这也把 round 137 发现的那个孤立 `0.9999` 接上了**。

**对 round 137–138 的再次更正**：种子 = `(int)(本函数结果 × 1e6)`，而本函数算的是**质量比值**，**与计时器无关**。计时器字符串仍是事实，但**不在这条链上**。

### 附 63 种子转换在**两个独立位置**得到印证（goal round 142）

**`0x1A9150`（27 B / 6 条，全读）就是“种子”本身**：

```
1A9154  call 0x1A9060               ; 上一轮读完的聚合/比值
1A9159  mulsd xmm0,[1e6]            ; × 1000000.0
1A9161  cvttsd2si rax,xmm0          ; 向零截断
```

与 `0x1B33B0` 内部的 `1B3427..1B3434` **完全同序列** ⇒ **两个独立位置印证**。

**且种子不只是记录**：`0x1B33B0` 在 `1B3469` 又 **重新读取**该槽位（`lea rax,[rsp+0xE0] ; mov rdx,rax ; mov [rsp+0x58],rax`）并**传给后续调用** ⇒ 种子**确实被使用**。

**已落 `lcns`**：`seedFromRatio(double)`（含两处证据注释）+ 测试（含截断而非四舍五入、负数、与 `ratioFromAverage` 的组合）。

### 附 64 种子的传入点（goal round 143）**[事实 + 一条标注的假设]

`0x1B33B0` 中种子的传入点（逐条）：

```
1B3469  lea rax,[rsp+0xE0]        ; &seed
1B3478  cvtsi2sd xmm3,[rsi]       ; 对象里的一个 double
1B347C  mov rdx,rax               ; ★ 种子作为第 2 个参数
1B3491  mov eax,[rsi+0x24] ; 1B3494 mov [rsp+0x20],eax
1B3498  movsd xmm2,[rsi+0x10]
1B349D  call 0x1A3560             ; 接收种子的那个调用
1B34A2  lea rax,['never'] ; 1B34AC mov edx,0x1E(30) ; 1B350F call 0x6D6940
```

**事实**：种子以**第二个参数**传给 `0x1A3560`，同时带两个来自对象的 double（`[rsi]`、`[rsi+0x10]`）与一个 int（`[rsi+0x24]`）；紧接着出现字符串 `'never'` 与常量 **30**。

**假设（未证实，不进结论）**：`'never'` + `30` 像是某种**“不设限”模式与一个计数/阈值**。

**本轮不对 `0x1A3560` 做任何定性** —— 它的入口尚未读（遵守 round 139 的规矩）。

### 附 65 种子初始化的是 **`std::mt19937`**（goal round 144）**[决定性结论]

`0x1A3560`（266 B / 66 条，**只有一个调用者** `0x1B33B0`）的入口逐条：

```
1A3567  mov rax,[rdx]                 ; 第 2 个参数 = &seed
1A356E  mov [rcx],rax                 ; 保存种子
1A357E  mov ecx,0x9C8 ; call 0x998500 ; operator new(2504)
1A3590  mov [rax],ebx                 ; state[0] = 种子
1A3592  mov edx,r8d ; shr edx,0x1E ; xor edx,r8d ; imul edx,edx,0x6C078965
1A35A1  mov [rax+rcx*4],r8d ; add rcx,1 ; cmp rcx,0x270 ; jne …
1A35B6  mov qword [rax+0x9C0],0x270   ; 下标字 = 624
```

**三个可验证常量把身份钉死**：`0x6C078965 = 1812433253`（**MT19937 初始化乘数**）、`0x270 = 624`（**状态字数**）、`0x9C8 = 2504 = 624×4 + 8`（**分配字节数**）。

⇒ **种子初始化的是 `std::mt19937`**，回答了 round 143 悬置的问题：**种子确实用于初始化随机引擎**。

**对工程的含义**：引擎本体是 **C++ 标准库**（工具链，**不转写**），**只有这层种子胶水是领域代码**。已落 `lcns`：三个常量 + `mt19937InitStep`（递归式转写）+ 测试（用标准 seed 5489 的参考值验证）。

### 附 66 `0x1A3560` 尾部：运行上下文的构造（goal round 145）

```
1A35DA  call 0x998500                 ; 第二块分配
1A35E2  mov dword [rax+8],1 ; … [rax+0xC],1
1A35F5  lea rax,[rip+0x8B38E4] ; 1A35FC mov [r8],rax     ; +0 处一个指针
1A35FF  lea rdi,[r8+0x10] ; xor eax,eax ; rep stosq      ; 清零 64 字节
1A3613  mov [r8+0x28],rax ; 1A361E mov [r8+0x30],rax      ; rax = r8+0x18：两个指针指向同一节点
1A3626  mov [r8+0x58],rax ; 1A362A mov [r8+0x60],rax      ; rax = r8+0x48：又一对
1A362E  call 0x898A80                 ; (rcx=r8, rdx=数据指针)
1A363B  mov [rsi+0x20],rax ; 1A3644 mov [rsi+0x30],rax ; 1A3633 mov qword [rsi+0x38],0
```

⇒ 两对**自指向的指针**是**两个空的序列哨兵** ⇒ 第二个对象是**容器**；种子、两个 double 与 mt19937 指针在第一个对象上。
**两个 double 的含义未证实，不作声明**。

**探测器第二次误报**：`lea rax,[rip+0x8B38E4]` 被打印为 `CONST 8.93842e-315`，因为扫描器把**任何 rip 相对操作数**当作数据读取，而 **`lea` 取的是地址**。纪律：**常量只能从真正解引用该操作数的指令（`movsd`/`mulsd`…）读取，绝不从 `lea` 读**。

### 附 67 `0x1B33B0` 的**参数表**（14 个真常量，带 RVA）与插入助手（goal round 146）

**口径修正的结果**：只取**真正解引用**的操作数（排除 `lea`），而 `lea` 会贡献的“假常量”数量为 **0** ⇒ **此前记录的常量清单未被污染**，只是 round 145 打印的那一行有误。

| 值 | rva |
|---|---|
| `1e+06` | `0x9BF530`（已落 `kSeedScale`）|
| `-1` | `0x9BF538`（round 137 首见）|
| `1000` | `0x9BF510`（两处）|
| `10000` | `0x9BF650` |
| `1e+08` | `0x9BF628` |
| `0.7` | `0x9BF630` |
| `0.5` | `0x9BF590` |
| `0.15` | `0x9BF638` |
| `1.5` | `0x9BF618` |
| `0.03` | `0x9BF648` |
| **`30`** | `0x9BF640` —— **与 round 143 的 `mov edx,0x1E` 相同** |
| `0.25` | `0x9BF5C0` |
| `0.9` | `0x9BF5B8` |

⇒ **只把“用法已读到”的落进 `lcns`**（`1e6`、`-1`、`30`）；其余作为**待命名清单**记在此处并带 RVA —— **仅凭数值起名就是自编**。

**`0x898A80`（44 B，全读）**：`mov rbx,rcx ; mov rcx,rdx ; lea rdx,[静态对象] ; add rbx,0x10 ; call 0x861A30 ; test al,al ; mov eax,0 ; cmovne rax,rbx` ⇒ 返回 **容器+0x10 或 nullptr**，即**插入第一个元素并以返回其地址表示成功**。

### 附 68 `0x1B33B0` 的**预算算式**（goal round 147）**[可判定，已落码]

```
1B474E  xmm5=[1e8] ; 1B4756 [rsi+0x18]=xmm5      ; 字段 +0x18 置为 1e8
1B492B  xmm7=[0.7] ; 1B4933 mulsd xmm7,[rsi+0x18]  ; 0.7 × base
1B4938  xmm1=[0.5] ; 1B4956 mulsd xmm1,xmm7         ; 0.5 × (0.7 × base)
1B4978  xmm0=[0.15] ; 1B4983 mulsd xmm0,[rsi+0x18]  ; 0.15 × base
1B4B2C  xmm6=[1000]
1B4B48  cvtsi2sd xmm0,rax ; 1B4B4D divsd xmm0,xmm6 ; 1B4B51 subsd xmm7,xmm0
1B4B84  cvtsi2sd xmm0,rax ; 1B4B89 divsd xmm0,xmm6 ; 1B4B8D subsd xmm7,xmm0
1B4B95  cvtsi2sd xmm0,r12d ; 1B4B9E addsd xmm1,xmm0
```

⇒ **已恢复**：基数 `1e8`、三个权重 `0.7`/`0.5`/`0.15`、因子 `1000`、两次 **`计数/1000` 的递减**、以及 `0.5×(0.7×base)` 上的一次整数加。
**未恢复**：那两个被减的整数到底量的是什么（因此参数只按**位置**命名，不按猜想的语义）。已落 `lcns`：五个常量 + `weightedBudget`/`budgetAfterTwoCounts`/`halfOfWeightedBudget`/`smallWeightedBudget` + 10 条测试。

### 附 69 被减的两个整数 = **时间差**，魔数除法已**实验确认**（goal round 148）

```
1B4B14  call 0x8A8190                 ; 取一个 tick
1B4B19  sub rax,[rsp+0x48]            ; ★ 与先前的值相减 = 已经历 tick 差
1B4B1E  movabs rbp,0x431BDE82D7B634DB ; 魔数
1B4B37  imul rbp ; 1B4B3E mov rax,rdx ; 1B4B41 sar rax,0x12 ; 1B4B45 sub rax,rcx
1B4B48  cvtsi2sd xmm0,rax ; 1B4B4D divsd xmm0,[1000] ; 1B4B51 subsd xmm7,xmm0
1B4B55  call 0x8A8190 ; 1B4B5A sub rax,[rsp+0x78] ; 同样处理 ; 1B4B8D subsd xmm7,xmm0
1B4B95  cvtsi2sd xmm0,r12d ; 1B4B9E addsd xmm1,xmm0
```

**实验确认（不凭记忆）**：在 Python 里**完全模拟该序列**（`imul` 有符号 128 位 → `sar rdx,18` → 符号校正），对 **12 个样本（含负数）**与**向零截断的 ÷1,000,000** 完全一致（而 ÷1000、÷1e7、÷1e8 均不一致）。
**第一次实验报“不一致”的原因**：我拿 Python 的**向下取整**去比，而指令实现的是**向零截断** —— 差异只在负数余数上。修正后一致。

⇒ 再除以 `1000` ⇒ **tick 源是 1e9 缩放（纳秒），被减掉的是“已经历秒数”**，即预算形如 **`0.7×base − 历时秒数`**。已把 `budgetAfterTwoCounts` 更名为 `budgetAfterElapsedTicks`，并加 `kTickDivisor = 1000000`（含实验依据）。

**仍未恢复**：`0x8A8190` 到底读的是什么（计数器/时钟/合成值），只知道它的**两次读数在此处被相减**。

### 附 70 tick 源是**纳秒时钟**，round 148 的算术从另一端被印证（goal round 149）**[链条闭合]

`0x8A8190`（9 条指令 / **14 个调用者**）全读：

```
8A8194  xor ecx,ecx                       ; 参数 1 = 0
8A8196  lea rdx,[rsp+0x20]                ; 参数 2 = &一个两字段结构
8A819B  call 0x63F730                     ; 填写 {秒, 纳秒}（+0 / +8）
8A81A0  movsxd rdx,dword [rsp+0x28]       ; 纳秒字段符号扩展
8A81A5  imul rax,qword [rsp+0x20],0x3B9ACA00   ; 秒 × 1,000,000,000
8A81AE  add rax,rdx                       ; + 纳秒
```

⇒ 返回 **秒×1e9 + 纳秒 = 纳秒计数**；这**从另一端确认了 round 148**：`/1e6 再 /1000` 正好是 **`/1e9`**，即把纳秒化为**秒**。

**完整链条（现已闭合）**：`0x8A8190` 取纳秒 → 两次读数相减 → `/1e9` 得历时秒数 → 从 **`0.7×1e8`** 的预算里减掉。

**已落 `lcns`**：`kNanosecondsPerSecond = 1000000000`、`nanosecondsFromPair`、`nanosecondsToSeconds`，并加一条**跨函数一致性测试**（预算减去的正是 `nanosecondsToSeconds(1e9) = 1`）。

### 附 71 `0x1B33B0` 剩余常量的三段算式，且两段与 round 147 的预算**拼合**（goal round 151）

```
1B4FE5  xmm1=[r13] ; 1B4FEB mulsd xmm1,[r13+8] ; 1B4FF1 mulsd xmm1,[1.5] ; 1B4FF9 ucomisd
        ⇒ 阈值 = 1.5 × (a × b)
1B5113  xmm0=[0.03] ; 1B511B mulsd xmm0,[rsi+0x18]              ⇒ 0.03 × base
1B5153  xmm2=[30] ; 1B515B xmm1=[0.25] ; 1B5169 mulsd xmm1,[rsi+0x18]
1B5182  cvtsi2sd xmm0,rax ; 1B5187 divsd xmm0,[1000] ; 1B518F mulsd xmm2,xmm0
1B5193  subsd xmm1,xmm2 ; 1B519D cvttsd2si r12d,xmm1
        ⇒ 0.25×base − 30×(count/1000)，截断入 r12d
1B535D  cvtsi2sd xmm0,rax ; 1B536A divsd xmm0,xmm6 ; 1B5373 subsd xmm7,xmm0 ; 1B5377 mulsd xmm7,[0.9]
        ⇒ 0.9 × (0.7×base − count/1000)
```

**关键拼接**：round 147 读到 `1B4B95 cvtsi2sd xmm0,r12d ; 1B4B9E addsd xmm1,xmm0`，即 **`0.5×(0.7×base) + trunc(0.25×base − 30×count/1000)`** —— 两段属于**同一表达式**。

**边界说明**：这里的两处除法用的是**常量 1000**（`divsd`），与 round 148 的**魔数乘法（1e6）**不同 ⇒ 这里的计数单位与那里不同，因此参数**仍按位置命名**（不猜单位）。已落 `lcns`：四个常量 + `limitFromPair`/`countBudgetLimit`/`decayedBudget`/`extraWeightedBudget` + 12 条测试。

### 附 72 算出的限额去向：**报告器**与 `Expected_time`（goal round 152）

```
1B5197  ucomisd xmm6,xmm1 ; 1B519B ja <skip> ; 1B519D cvttsd2si r12d,xmm1   ; 限额（条件截断）
1B51BF  mov r8d,0x148(328) ; 1B51D6 call 0x1A8DB0                            ; 格式化器
1B51FD  call 0x92D500                                                        ; 容器插入（round 133/134）
1B5220  mov dword [rsp+0x20],r12d                                            ; 限额写进下一条消息
1B5258  call 0x92D620                                                        ; 第二种插入
1B537F  movsd [rsp+0x28],xmm7   ; 1B5385 call 0x1AC390 ; 1B538D call 0x65C320
        （`0x65C320` 自带文本 **'Expected_time …'**）
```

⇒ **确认报告路径**：`0x1AC390` 就是 round 131–134 描述的**报告输出例程**，算出的限额被**格式化后插入同一容器**；`0.9 衷减后的预算` 则交给**`Expected_time`** 路径。

**新领域串**：`0x65C320` 自带 **`Expected_time …`** —— 这是字符串层面的事实。

**另读到一个逐元素循环**：步长 **`0x158`（344 字节）**，调 `0x1D0D70`，带 `r9d=1`、`[rsp+0x28]=0x2D(45)`、`[rsp+0x20]=0`（常量 45 已记录，**含义未定**）。

### 附 73 时间报告器的自带文本，**闭合了预算链条**（goal round 152）

`0x65C320`（414 B / 2 个调用者）自带文本（**逐条照录**）：

```
'Expected_time '
' real_time '
' guessed_time '
'Section end '
'##################### <='
```

它正是 **0.9 衷减后的预算** 被交给的那个函数。结合 round 147–151 的预算算术：

⇒ **那些算出的限额是“时间”限额**；本例程报告一个阶段的**预期 / 实际 / 猜测**时间，并以**一行 `##### <=` 横幅**收尾。

同时回看 round 143 的一个悬置：当时把 `'never'` + `30` 标为“可能是不设限模式”的假设，现在已知同一函数内确有**时间限额**语义（常量 30 与 1000 在 `0.25×base − 30×count/1000` 中）—— **假设得到侧面支持，但仍未直接读到 `'never'` 的分支，故仍不升为结论**。

### 附 74 `'never'` 的**三个位置**：假设得到加强，但**仍未定案**（goal round 153）

三处都是 `lea`（**取地址**）并作为**字符串参数**存入：

| 位置 | 紧接着什么 | 伴随 | 
|---|---|---|
| `0x1B34A2` | `call 0x1A3560`（**std::mt19937 构造**）| `edx = 0x1E(30)`、`r8 = rbx`，存入 `[rsp+0x13b0]` |
| `0x1B38E2` | `call 0x1A8D70` | `rdx = [r12+8] − [r12]`（容器字节跨度）、魔数 `0x82FA0BE82FA0BE83`，存入 `[rsp+0x730]` |
| **`0x1B507D`** | **`call 0x8A8190`（纳秒时钟）** | `edx = 1`，存入 `[rsp+0x6c0]`，随后 `call 0x6D6940` |

⇒ 三处中有**两处紧接时间/限额计算之后**，其中**一处直接跟在时钟读取之后**，因此 `'never'` 的行为很像**“不是数字的限额”的标签**。这**实质性地加强**了 round 143 的假设，但**仍未定案**：读到的是“字符串被存为参数”，**而不是选它的那个比较/分支**。

另记：`0x1B38F5` 的魔数 `0x82FA0BE82FA0BE83`（作用于容器跨度）待用 round 148 的**同一数值实验**确定它除的是多少。

### 附 75 魔数是**哈希乘法，不是除法**；且 `+0x4C` 在 0xF0 步长上**求和**（goal round 154）

```
1B38E2  lea rax,['never']            ; 字符串地址
1B38E9  sub rdx,[r12]                ; rdx = [r12+8] − [r12]（字节跨度）
1B38F5  movabs rax,0x82FA0BE82FA0BE83
1B3912  sar rdx,3                    ; 跨度 / 8
1B3919  imul rdx,rax                 ; ★ 只取低 64 位：**没有高位、没有 sar**
1B391D  call 0x6D6940
```

⇒ 这是**一次乘法式哈希**（作用于 `跨度/8`），**不是除法**。round 153 计划“用实验找除数”**前提就错了**；而**实验本身报了真话**（没有任何截断除数能匹配）。

**同一窗口内的新证据**：

```
1B392A  rdx=[rdi] ; r8=[rdi+8] ; 1B3933 cmp rdx,r8 ; je …
1B3940  add ecx,[rdx+0x4C]        ; ★ 累加 +0x4C 处的 dword
1B3943  add rdx,0xF0              ; 步长 0xF0（240 字节）
1B394F  cmp eax,ecx ; jle 0x1B4760
```

⇒ **`+0x4C`**（就是 rounds 120/124 里线程关闭对**与 9/10 相比**的那个字段）在此处是**逐记录的 dword，被跨容器求和后与一个计数相比**。

而 **`0xF0`（240 字节）与 round 141（`0x1A9060`）用的步长相同** ⇒ **两处在遍历同一种记录**（记录大小 240 字节）。

这也**与 round 125 的更正不矛盾**：当时纠正的是“`0x12ABD0` 里的 `+0x4C` 是栈位而非字段”，而本轮读到的是**另一处、确实是对象字段**的 `+0x4C`。

### 附 76 `+0x4C` 有 **49 个写入点**；“和 vs 计数”分支构造**时间限额记录**（goal round 155）

**用 `covlib.field_writes_scan(0x4C, 可达集, width=4, is_float=False)` 测得**（该助手会**考虑基址寄存器**，因此 `[rsp+0x4C]` 这类栈位不会被当成字段，即 round 125 的错）：

```
writers of a 32-bit +0x4C among reachable functions: 49 sites
```

其中最小的几个是**纯 setter**（`0x178560` 4 B、`0x170940` 22 B、`0x468110` 121 B、`0x40BF0`/`0x40CD0` 各 223 B），最大的 `0x3D8E50` 3504 B；其中 `0x1C0750`（604 B）带 **vector 越界断言**。
⇒ `+0x4C` 是**一个被广泛写入、并会被求和比较的逐记录 dword**。

**分支目标 `0x1B4760`**（条件为 `if (eax <= ecx) goto`）：

```
1B4760  mov rcx,r12 ; 1B4763 call 0x1F8350
1B4768  movsd xmm6,[1000] ; 1B4773 mulsd xmm6,xmm0     ; 某值 × 1000
1B4777  call 0x1F8300 ; 1B477C neg eax ; 1B4784 mov r13d,eax   ; 返回的整数取负
1B4787  cvttsd2si rax,xmm6 ; 1B478C mov [rsp+0x50],rax
1B47A1  mov dword [rsp+0x748],r13d   ; 取负后的整数
1B47A9  mov byte  [rsp+0x758],0      ; 一个置零的字节
1B47B1  mov qword [rsp+0x750],rax    ; ×1000 后的值
1B47B9  call 0x1AA890
```

⇒ 该分支在**栈上拼出三字段记录**（取负整数、置零字节、×1000 的值）并传出去 ——**与 rounds 147–152 建立的“时间”主题一致**；判断的方向已写明为 `if (eax <= ecx)`。

### 附 77 比较的两侧与记录的消费者（goal round 156）**[入口级读取]**

**`0x1F8300`**（72 B / 10 个调用者）—— 整数计数：

```
1F8320  mov rax,[rdx+0x140] ; 1F8327 add rdx,0x158     ; 步长 0x158（344 字节）
1F832E  sub rax,[rdx-0x20] ; 1F8332 sar rax,3 ; 1F8336 imul rax,0xCCCCCCCCCCCCCCCD
1F833A  add rax,rcx ; 1F8340 mov ecx,eax              ; ★ 跨容器累加
```

`0xCCCCCCCCCCCCCCCD` 配 `sar 3` 是熟知的 **/10** 魔数 —— **但按我的纪律，待用 round 148 的实验确认，不凭记忆**。

**`0x1F8350`**（132 B / 9 个调用者）—— 浮点总量：用**与 round 154 相同的** `0x82FA0BE82FA0BE83`（`sar 3` 后相乘）算出 `count-1`，随后 `cvtsi2sd` 并 `mulsd xmm6,[rdx-0x158]`（逐元素的一个 double）⇒ **加权求和**。
⇒ 原来的 `cmp eax,ecx` 是**整数计数 vs 求和后的 `+0x4C` 计数器**。

**`0x1AA890`**（398 B / 112 条 / 3 个调用者）—— 记录消费者的开头：

```
1AA897  movabs r8,0xAAAAAAAAAAAAAAAB ; 1AA8B1 sub rdx,rcx ; 1AA8B4 sar rdx,4 ; 1AA8B8 imul rdx,r8
1AA8BC  mov r8d,[rsi+0x28] ; 1AA8C0 cmp rdx,r8 ; 1AA8C3 jb 0x1AA925     ; 计数 vs +0x28 的上限
1AA8C5  mov eax,[rsi+0x18] ; 1AA8C8 lea rbx,[rax+rax*2]               ; 字段 × 3
```

⇒ 它对一个 **24 字节步长**的容器做**上限检查**（`sar 4` + `0xAAAA…AB` = /24）。

**待验证清单**：`0xCCCCCCCCCCCCCCCD`(/10?)、`0xAAAAAAAAAAAAAAAB`(/24?)、`0x82FA0BE82FA0BE83`（round 154 已确认为**非除法**，但在 `0x1F8350` 里它同样只取低位）。

### 附 78 两个魔数除数**实验确认**：10 与 24，且移位是**另一步缩放**（goal round 157）

**实验（逐条模拟有符号 128 位乘 + 取高位 + 算术移位 + 符号校正，与**向零截断**对比，23 个样本含负数）**：

| 魔数 | 移位 | 匹配的截断除数 |
|---|---:|---|
| `0xCCCCCCCCCCCCCCCD` | `sar 3` | **10**（唯一）|
| `0xAAAAAAAAAAAAAAAB` | `sar 4` | **24**（唯一）|
| `0x82FA0BE82FA0BE83` | `sar 3` | **无** ⇒ **不是除法**（与 round 154 一致）|

**必须说清楚的区分**：每个位点是**两步** —— 一次算术移位，**再**一次魔数乘法除法：

```
0x1F832E..0x1F8336   (a − b) >> 3，再 /10   ⇒ 常规量级下净效 = (a − b) / 80
0x1AA8B1..0x1AA8B8   span    >> 4，再 /24   ⇒ 净效 = span / 384
```

我**只对除数（10 与 24）做实验确认**；移位（/8 与 /16）是**独立的一步**，我**不把它偷偷并进除数**。两个净效除数均按“两步”如实记录。

### 附 79 插入助手、**新字符串**、**跨函数确认的记录布局**（goal round 159）

```
1AA8C5  mov eax,[rsi+0x18] ; 1AA8C8 lea rbx,[rax+rax*2] ; 1AA8CC shl rbx,4   ; ★ 字段 × 48
1AA8D0  add rbx,rcx                                                          ; 被索引的记录
1AA8D3  cmp byte [rbx+0x28],0 ; jne 0x1AA8F0
1AA8DF  call 0x1A8C80 ; test al,al ; jne … ; 1AA8E8 ret                 ; 早退返回 0
1AA8F6  call 0x1A9350
1AA8FB  mov eax,[rdi+0x18] ; 1AA901 mov [rbx+0x18],eax   ; 复制三个字段
1AA904  mov rax,[rdi+0x20] ; 1AA908 mov [rbx+0x20],rax
1AA90C  movzx eax,byte [rdi+0x28] ; 1AA910 mov [rbx+0x28],al
1AA913  call 0x6D6510                                    ; ★ 带 **'!m_elements.empty()'**
1AA918  mov eax,1 ; ret                                  ; 成功返回 1
```

**（1）新领域字符串**：`0x6D6510` 带 **`!m_elements.empty()`** ⇒ 原工程里该容器叫 **`m_elements`**。

**（2）两个步长并存，各自保留**：索引用 **`字段×48`**（与 344 、与 round 157 的 `/24` 计数都不同）。**我不用新发现去覆盖旧度量**，两者并列记录。

**（3）布局在两个函数里独立印证**：被复制的记录正是 round 155 在**栈上拼出**的三字段（`+0x18` dword、`+0x20` qword、`+0x28` byte）⇒ **同一布局**。

**（4）TU 归属**：64 位 `+0x140` 的写入者共 **129 个位点 / 129 个函数**，其中 `0x40070`（1697 B）自带路径 **`..\multi\nesting_context.cpp`** ⇒ 该字段可**按名归属到 TU**。

### 附 82 `0x1B0760` 是**挤压（shake）步骤**，其自带文本给出**日志行的形状**（goal round 164）

456 条指令，2 个调用者，自带文本（**逐条照录**）：

```
'shaker_'
'compacting ...'
'before_shake'
' => '
'after_shake'
```

⇒ 该例程**挤压并报告挤压前后的质量**，日志行形如：

```
compacting ... <before_shake> => <after_shake>
```

**唯一被解引用的常量**：`1000`（在 `0x1B085E` 装入 `xmm6`）——与本 TU 内反复出现的**秒/毫秒换算**一致。

**本函数内未发现阈值常量**，因此**除了字符串与它们暗示的形状之外不落码**：**日志格式是事实，算法尚未读到**。

### 附 83 `0x1A1810` 的**步数算式族**（goal round 165）**[已落码]

自带文本：`'p.first '`、`'nb_strips '`、`'nb_double_steps '`、`'nb_int_steps'`。

```
1A184F/1A1857/1A1881   value / 0.0001 + 0.5        → int
1A1878/1A188B/1A1890   n / 1e6（作为后两处的除数）
1A1894/1A18A9          value / (n/1e6) + 0.0003  → int
1A18A1/1A18B2/1A18BA   × 10 / (n/1e6) + 0.0039
```

⇒ **每个步长一个整数计数**，形如 `(int)(value / step + rounding)`；这正是它自带文本里那三个名字的含义。

**已落 `lcns/include/lcns/steps.hpp`**：三个步长 `0.0001`/`0.0003`/`0.0039`、舍入项 `0.5`、倍数 `10`、`n/1e6` 的尺度，以及 `stepCount`/`fineStepCount`/`midStepCount`/`stepScale`，每个常量带加载地址；测试 14 条（含截断边界 `12.5+0.5=13`）。

### 附 84 纪律更正：**字符串靠 `lea`、常量靠解引用**；并据此读出三个计数的去向（goal round 166）

**更正**：round 145 的纪律（“常量只能从**解引用**的指令读”）针对的是**常量**；而**字符串只会以地址传递**，排除 `lea` 就会**漏掉所有字符串位点** —— round 166 的第一版正是这么错的（两个函数都“什么也没找到”）。
**正确规则：字符串用 `lea` 匹配；常量要求真解引用。**

换用正确规则后立刻读到（`0x1A1810`）：

```
1A190D  mov rcx,[rip+0x86671C]      ; 一个 ostream
1A1914  mov r8d,8                   ; ★ 长度 8，正是 len('p.first ')
1A191A  lea rdx,['p.first ']
1A1921  call 0x978010               ; ostream::write(ptr, len)
1A192D  movapd xmm1,xmm9 ; 1A1932 call 0x8688E0    ; << double
1A1979  mov r8d,0xA                 ; ★ 长度 10，正是 len('nb_strips ')
1A197F  lea rdx,['nb_strips ']
1A1986  call 0x978010
1A1992  mov edx,esi                 ; 算出的步数
```

⇒ **四个名字是被打印的**（长度与标签**精确一致**）。因此 round 165 落的步数算式**供给一份 `p.first / nb_strips / nb_double_steps / nb_int_steps` 的报告**；`0x978010` 即 `std::ostream::write`，与早前将其识别为 iostream 内部函数一致。

### 附 85 用**新学到的库标记**重新过一遍同一条规则（goal round 167）

规则**不变**（与 rounds 115/118 相同）：**只有当一个函数的每一条自带文本都命中已知库标记**时，才归为库代码，**命中的标记逐个存储**。本轮新增的标记均来自近几轮实读：`entry_event`/`exit_event`（boost::asio 线程池）、`transaction_safe`/`restrict`（MSVC SAL 注解）、`deque::`/`_M_new_elements_at`/`_M_construct`/`_M_create`/`__cxx11`（libstdc++）、`memcpy_s`（CRT）、`__pos (which is`（libstdc++ 越界断言）。

本轮：库代码 **201** 个 / 268920 字节（已登记）。

### 附 86 **转数（turn count）**：三个独立函数都除以 `2π`（goal round 168）**[已落码]

扫描“**除法 + 舍入项 + 截断**”惯用法，在未引用函数里找到 6 个，除数分三族：

| 除数 | 函数 | 含义（据此）|
|---|---|---|
| **`6.283185307`（2π）** | `0x24C4A0`(237 B)、`0x5C2370`(210 B)、`0x5D29C0`(125 B) | **`round(value / 2π)` = 转数** |
| `360` | `0x21B7C0`(4008 B)、`0x17E180`(752 B) | `round(value / 360)` |
| `0.0001` | `0x2098F0`(2606 B) | 与 `0x1A1810` 同一精细步长 |

**三个互相独立的函数同时除以 `6.283185307`** 是把它认作 2π 的**证据**（而非凭值猜想）；算术本身与已落的步数算式**同一三步形状**。

**已落 `steps.hpp`**：`kTwoPiRounded`、`turnCount`、`kDegreesPerTurn`、`degreeTurnCount`（各带地址）+ 10 条测试。

### 附 87 sqrt 容差与**尺度常量普查**（goal round 169）

**（a）sqrt 后与常量相比**：全部未引用函数里**只有 2 个位点**，且两者都用 **`1e-09`**（`0x55A230`、`0x5EF7E0`）⇒ **近零比较的 epsilon**。
**证据强度如实标注**：**两个独立位点比 round 168 的三个弱**。

**（b）尺度常量普查**（多少个**当前未引用**的函数使用该值）—— **这就是剩余可判定材料的分布图**：

| 常量 | 函数数 |
|---|---:|
| `0.5` | 74 |
| `1e-06` | 47 |
| `0.001` | 17 |
| `1e+06` | 17 |
| `360` | 15 |
| `0.1` | 12 |
| `1.5` | 11 |
| `0.0001` | 9 |
| `2` | 7 |
| `0.01` | 6 |
| `1e-09` | 4 |
| `10` | 4 |
| `100` | 4 |
| `1000` | 3 |

（下一轮将从这张图里挑“多函数共同使用”的值，按“读它们参与的计算”决定能否落码。）

### 附 88 `0x4E5B0` 是**读默认值表的构造函数**（goal round 170）

规模 201 条，2 个调用者，自带文本 `'333333'`。它从**只读数据表**取 double 并依次存入**同一个对象**（基址 `rcx`）：`+0x358`、`+8`、`+0x28`、`+0x30`、`+0x84`（16 字节块）、`+0x98`、`+0xA0`、`+0xE0`，以及 `+0x5A`…`+0x5E` 五个标志字节置 1。

**表槽位与值已逐个读出并列在本节**；**偏移属于本对象**，**我不把它们写成某个结构体定义**（基址已排除 `rip`/`rsp`/`rbp`，遵 round 125 的纪律）。

### 附 89 `0x4E5B0` 读的**默认值表**（goal round 170）**[每行带 RVA 与加载地址]**

共读出 **25 个 double 默认值**：

| 值 | RVA | 加载于 |
|---|---|---|
| `0.5` | `0x9B0578` | `0x4e5b0` |
| `0.0001` | `0x9B0580` | `0x4e5c8` |
| `0.01` | `0x9B0588` | `0x4e5d0` |
| `0.1` | `0x9B0590` | `0x4e5b8` |
| `0.001` | `0x9B0598` | `0x4e5c0` |
| `0.85` | `0x9B05B0` | `0x4e68e` |
| `3` | `0x9B05B8` | `0x4e67e` |
| `4` | `0x9B05C0` | `0x4e6bd` |
| `0.8` | `0x9B05C8` | `0x4e69d` |
| `15` | `0x9B05F0` | `0x4e6e1` |
| `1.2` | `0x9B05F8` | `0x4e774` |
| `0.0125` | `0x9B0600` | `0x4e794` |
| `2` | `0x9B0608` | `0x4e7b4` |
| `5` | `0x9B0610` | `0x4e7dc` |
| `0.75` | `0x9B0630` | `0x4e896` |
| `0.9` | `0x9B0638` | `0x4e88e` |
| `0.05` | `0x9B0640` | `0x4e7c4` |
| `0.25` | `0x9B0648` | `0x4e7a4` |
| `1` | `0x9B0650` | `0x4e784` |
| `0.2` | `0x9B0658` | `0x4e8dd` |
| `0.03` | `0x9B0660` | `0x4e9b7` |
| `0.02` | `0x9B0668` | `0x4e9c7` |
| `-1` | `0x9B0670` | `0x4e9d7` |
| `0.3` | `0x9B0678` | `0x4e997` |
| `1.5` | `0x9B0680` | `0x4e9a7` |

**4 个槽位判定为【非 double】（未解析）**：它们解析出来是**退正规数**（`1.6976e-312`、`5.30499e-313`、`2.122e-313`），真实默认值不可能是这个量级，因此它们**很可能是指针或 16 字节块**（`movdqa`/`movups` 读取）：`0x9B05A0`（@`0x4e676`）、`0x9B05D0`（@`0x4e6ad`）、`0x9B05E0`（@`0x4e6d1`）、`0x9B0620`（@`0x4e8a6`）。

⇒ **这是一份领域对象的参数默认值表**，每个值都有 RVA 与加载位置作证据；对应的字段偏移集合已在前一节列出。

### 附 90 **微尺度换算是工程惯例**：两个独立函数、共享常量块（goal round 171）**[已落码]

```
0x19F1F0:  19F25F cvtsi2sd xmm1,[rbx] ; 19F269 divsd xmm1,[1e6]
0x19F8F0:  19FA0E cvtsi2sd xmm2,[rdi] ; 19FA25 divsd xmm2,[1e6]
```

两者的常量取自**同一块只读数据**：

| 值 | RVA | 加载于 |
|---|---|---|
| `1e-06` | `0x9BE4F0` | `0x19F246`、`0x19FA1D` |
| `0.0001` | `0x9BE4F8` | `0x19F2CC`、`0x19FA89` |
| `1e+06` | `0x9BE508` | `0x19F269`、`0x19FA25` |

⇒ **两个互相独立的函数、同一个除数、同一块常量** ⇒ 这是**工程惯例**而非局部选择；与已落的 `kSeedScale = 1e6`、`0.0001` 步长对得上。

**已落 `lcns/include/lcns/units.hpp`**：`kMicroScale`/`kMicroInverse`/`kTenThousandth` + `microToUnit`/`unitToMicro`，测试 9 条（含与 `kStepFine` 的一致性）。

### 附 91 **共享常量槽位**：同一 RVA 被多个独立函数加载（goal round 172）

**为什么用 RVA 而不是数值**：相等的数值可能巧合，而**同一个只读槽位被三处以上引用**是惯例。

未引用领域函数中，被 **3 个以上独立函数**加载的 double 槽位共 **33** 个（列前 22）：

| RVA | 值 | 函数数 |
|---|---:|---:|
| `0x9DFBC8` | `1` | 16 |
| `0x9DFC20` | `50` | 14 |
| `0x9DFBD0` | `0.5` | 11 |
| `0x9DFBA0` | `2.22045e-16` | 9 |
| `0x9DFBD8` | `-1` | 7 |
| `0x9C2C08` | `1` | 6 |
| `0x9DC3C0` | `0.001` | 6 |
| `0x9DC3D8` | `0.5` | 6 |
| `0x9DE940` | `-1` | 6 |
| `0x9BEAB0` | `1` | 5 |
| `0x9DA000` | `360` | 5 |
| `0x9DA010` | `0.5` | 5 |
| `0x9DC3F0` | `1e-06` | 5 |
| `0x9DE930` | `1` | 5 |
| `0x9DFB98` | `1e+06` | 5 |
| `0x9B1BF8` | `0.5` | 4 |
| `0x9BEAA8` | `0.04` | 4 |
| `0x9C1BF0` | `1` | 4 |
| `0x9D9E38` | `1e-06` | 4 |
| `0x9DBE90` | `-1` | 4 |
| `0x9DBE98` | `1` | 4 |
| `0x9BEA98` | `0.5` | 3 |

### 附 92 共享常量块：**DBL_EPSILON 被 9 个独立函数使用**（goal round 172）**[已落码]

`0x9DFB98..0x9DFC20` 是一块连续只读数据，被一族函数（597–3850 字节）共用：

| RVA | 值 | 函数数 |
|---|---:|---:|
| `0x9DFB98` | `1e+06` | 5 |
| **`0x9DFBA0`** | **`2.22045e-16`** | **9** |
| `0x9DFBC8` | `1` | 16 |
| `0x9DFBD0` | `0.5` | 11 |
| `0x9DFBD8` | `-1` | 7 |
| `0x9DFC20` | `50` | 14 |

**关键：`2.22045e-16` = `2**-52` = double 的机器 epsilon**，而且它**可以用计算确认**（测试直接与 `std::numeric_limits<double>::epsilon()` 比较）—— **这一条不依赖记忆**。

其余值（`50`、`1`等）**只记录槽位与值，不起名**。

### 附 93 共享参数块 `0x9DFB98..0x9DFC20` 的**使用者族**（goal round 173）

未引用函数中访问该块的共 **47** 个；其中**同时访问 2 个以上槽位**的 **13** 个——后者就是该块所属的“族”：

| 函数 | 字节 | 访问的槽位 |
|---|---:|---|
| `0x746c10` | 3251 | `1`、`1e6`、`50` |
| `0x747b30` | 2841 | `1`、`1e6`、`eps` |
| `0x5e6060` | 129 | `1`、`eps` |
| `0x5e6360` | 251 | `-1`、`0.5` |
| `0x5e6460` | 1568 | `-1`、`0.5` |
| `0x7001c0` | 134 | `1`、`1e6` |
| `0x700460` | 2589 | `1`、`eps` |
| `0x715320` | 1964 | `1`、`eps` |
| `0x74b430` | 284 | `1`、`eps` |
| `0x74b700` | 284 | `1`、`eps` |
| `0x966510` | 803 | `1`、`eps` |
| `0x96f8f0` | 1879 | `1`、`eps` |
| `0x97b860` | 1101 | `1`、`eps` |

（每个槽位的使用者数：`1e6`→5、`eps`→9、`1`→16、`0.5`→11、`-1`→7、`50`→14）

**证据级别（必读）**：上表的 13 行**全部没有自带文本**，因此它们记录的是**“该函数加载了哪些常量槽位”**，**而不是对其逻辑的读取**。两者不同，读者应能分辨。

**本轮另两条结构观察**：

1. `0x74B430` 与 `0x74B700` **各恰好 284 字节、访问同一对槽位** ⇒ **同一模板实例化两次**的特征（如 `double`/`int` 两个版本）；
2. `0x5E6360`（251 B）与 `0x5E6460`（1568 B）**围绕 `-1`/`0.5` 这一对**，与其余围绕 `1`/`eps` 的那批**分属不同子族**。

⇒ **结论：共享常量块能把函数聚成族，但它本身不给名字、不定 TU**。

### 附 94 孪生函数**逐条比对**：同一模板两次实例化，且返回值已读出（goal round 174）

`0x74B430` 与 `0x74B700` **各 83 条指令**，**逐条相同**，仅三处差异：

1. 跳转目标（各自的地址）；
2. **各自的常量槽位**（同形不同块）；
3. **各自调用一个同形的 284 字节助手**：`0x74B390` 对 `0x74B660`。

⇒ **同一模板实例化两次（加两个助手）**。

**返回值的构造（逐条照录）**：

```
pxor xmm3,xmm3
ucomisd xmm0,xmm3
seta al                     ; 与零相比为“大”则 1，否则 0
lea eax,[rax+rax-1]         ; ★ 把 {0,1} 映为 {-1,+1}
```

上方的守卫用 **`andpd` + 符号掩码 = 取绝对值**，并与一个常量及“该常量 × `[rsp+0x20]` 参数”相比 ⇒ **容差判定**；相等情形走 `je` 路径返回 **0**。

**已落 `lcns/include/lcns/compare.hpp`**：`signOf`、`compareToZero`、`withinTolerance`（各带地址）+ 测试 9 条。
**未实现**：容差两道守卫的**先后顺序**（读得不够远，不猜）。

### 附 95 孪生的助手 = **2D 叉积（有向面积）**，比较器的参数因此得名（goal round 175）**[已落码]

`0x74B390` 与 `0x74B660` **各 34 条、逐条相同**：

```
74B395  xmm5=[rcx]      ; A.x      74B399  xmm4=[rcx+8]  ; A.y
74B39E  xmm1=[r8]       ; C.x      74B3A3  xmm0=[r8+8]   ; C.y
74B3A9  xmm3=[rdx]      ; B.x      74B3B9  xmm2=[rdx+8]  ; B.y
74B3AD  subsd xmm1,xmm5 ; C.x−A.x   74B3BE  subsd xmm0,xmm4 ; C.y−A.y
74B3CC  subsd xmm3,xmm5 ; B.x−A.x   74B3D5  subsd xmm2,xmm4 ; B.y−A.y
74B40C  movsd [rbx],xmm0                ; 一个输出分量写回
74B410  mulsd xmm1,[rsp+0x50] ; 74B41C mulsd xmm0,[rsp+0x58] ; 74B422 subsd xmm0,xmm1
```

⇒ **2D 叉积**：三角形 ABC 的**有向面积**，即标准的方向判定。

**因此孪生比较器比较的是叉积**（带绝对值容差）⇒ 它的参数是**方向量/共线度**，而不是任意标量。已落 `compare.hpp`：`crossProduct2d`、`crossComponentToStore` + 测试 10 条。

### 附 96 `0x7043B0`（全读，17 条）= **相对尺度 `max(1, |v₀..v₃|)`**（goal round 176）**[已落码]

```
7043B0  movsd xmm1,[0x7FFFFFFFFFFFFFFF]   ; 符号掩码 = fabs
7043C1  andpd xmm4,xmm1 ; 7043CA andpd xmm0,xmm1 ; 7043CE maxsd xmm4,xmm0
7043D7  andpd xmm3,xmm1 ; 7043E3 andpd xmm2,xmm1 ; 7043DB maxsd xmm3,xmm4 ; 7043EF maxsd xmm2,xmm3
7043E7  movsd xmm1,[1.0] ; 7043F3 maxsd xmm1,xmm2   ; ★ max(1, 四个分量的绝对值)
7043F7  movsd [rcx],xmm1
```

⇒ 返回**四个分量绝对值的最大者，下限为 1.0**。两个助手把它存在 `r9` 指向的位置，孪生随后用“常量 × 该尺度”作为**相对容差** ⇒ **这就是它们的比较为何具有尺度不变性**。
全部读自指令，非推断。

### 附 97 `0x5E6360` 的四字段公式，与比较器的 **27 个调用者**（goal round 177）**[已落码]

```
5E637A  xmm7=[rcx+0x18]  5E637F xmm9=[rcx+8]  5E6385 xmm6=[rcx+0x10]  5E638F xmm0=[rcx+0x20]
5E6394  xmm8 = (+0x18) − (+8)     5E639C xmm0 = (+0x20) − (+0x10)
5E63A0  mulsd xmm8,xmm0               ; ★ 两个差之积
5E63AA  addsd xmm6,xmm6 ; 5E63D5 mulsd xmm6,[0.5]
5E63BD  addsd xmm7,xmm9 ; 5E63DD mulsd xmm7,[0.5]   ; ★ +0x18 与 +8 的中点
5E63B6  mov rdx,0xFFFFFFFFFFFFFFFF ; 5E63EA mov [rax+0x28],rdx   ; ★ −1 哨兵
5E63E1  movsd [rax+0x18],xmm8
```

其中 **`0.5` 与 `−1` 取自** rounds 172–173 识别的**共享块**（rva `0x9DFBD0` / `0x9DFBD8`）。

**另一条结构事实**：孪生比较器有 **27 个调用者**（244–3850 字节、**全部无文本**）⇒ 它是一个**被广泛使用的几何内核原语**。已落 `compare.hpp`：四个字段偏移、`differenceProduct`、`midpointOf`、`doubledThenHalved`、`kSentinelMinusOne` + 测试 11 条。

### 附 98 `0x89D2F0` = **二叉搜索树的插入/查找**；并**更正 round 173 的“参数块”推断**（goal round 178）

读到：根在 `[rcx+8]`，节点左 `+0x10`、右 `+0x18`、**键 `+0x20`**；插入时 `mov ecx,0x98`（**152 字节**）并初始化新节点：

```
89D38F/89D394/89D3A1  [rsi+0x40],[rsi+0x48],[rsi+0x50] = 0.0
89D3B9/89D3BD/89D3C1  [rsi+0x60],[rsi+0x68],[rsi+0x70] = −1（qword）  ; “无下标”哨兵
89D3C5                movsd [rsi+0x78], [−1.0]
89D3CA/89D3D5/89D3E0  [rsi+0x80],[rsi+0x88],[rsi+0x90] = 0
```

**更正（重要）**：它用的 `−1.0` 来自 **rva `0x9DFBD8`** —— 正是 round 172 称为“共享参数块”、round 173 据以划“族”的同一个槽位。**一个槽位同时服务几何助手与树节点初始化**，正是**编译器合并常量池**（GCC 会把相等的浮点字面量合并到同一个 rodata 槽位）的样子，**而不是领域参数块** ⇒ **round 173 的“族”不能作为领域归组证据**。

**已落 `layout.hpp`**：节点字节数与七个偏移/哨兵常量 + 测试 14 条。

### 附 99 `0x5E78D0` 的**尺寸门**：`span > 47`，与 48 字节记录互相印证（goal round 179）**[已落码]

```
5E7925  call 0x5C5260        ; 容器 end
5E792D  mov rbx,[rax+8] ; 5E7931 call 0x5C5260 ; 5E7936 sub rbx,[rax]   ; 字节跨度
5E7939  cmp rbx,0x2F ; ja 0x5E7960     ; ★ 仅当跨度超过 47 才继续
5E793F  …恢复现场并 RET              ; 否则立即返回
```

`47` 恰好是 round 159 从 `lea rbx,[rax+rax*2] ; shl rbx,4` 测得的 **48 字节记录步长减一**，在此处当**尺寸门**用：对 48 字节记录而言，`span > 47` 即**“至少一个元素”**。
**两条独立事实指向同一记录大小**，所以这不是一个孤立常量。
已落 `layout.hpp`：`kMinSpanForOneRecord`、`hasAtLeastOneRecord` + 测试 6 条。

### 附 100 `0x6DE940` = **16 字节记录**的 size 访问器；且**哨兵惯例出现两次**（goal round 180）**[已落码]

**（a）`0x6DE940`（15 条，21 个调用者）**：

```
6DE94E  call 0x5C5260 ; 6DE951 rbx=[rax+8] ; 6DE955 call 0x5C5260 ; 6DE95A sub rbx,[rax] ; 6DE960 sar rax,4
```

⇒ 返回 `span >> 4`，即**记录为 16 字节**的容器元素数 —— 这是第**五**种步长（旁侧 48、240、344 与 `/24` 计数），**各自保留证据、互不覆盖**。

**（b）哨兵惯例，两个独立构造函数各出现一次**：

| 位置 | 三个 qword `−1` | `−1.0` double |
|---|---|---|
| `0x5E6360` 尾部 | `[rax+0x28]`、`[rax+0x30]`、`[rax+0x38]` | `[rax+0x40]`（RE `0x5E6400`）|
| `0x89D2F0`（树节点）| `[rsi+0x60]`、`[rsi+0x68]`、`[rsi+0x70]` | `[rsi+0x78]`（RE `0x89D3C5`）|

⇒ **两个独立构造函数、地址不同、惯例相同** ⇒ 值得落码。
已落 `layout.hpp`：`kSizeRecordStride`/`kSizeRecordShift`/`elementCount16`、`kSentinelCount`/`kInvalidIndexSentinel`/`kInvalidDoubleSentinel` + 测试 16 条（含四种步长互不相等、与 round 178 的 `kTreeNodeNoIndex` 一致）。

### 附 101 **步长地图**：未引用函数里所有“字节跨度右移”点（goal round 181）

扫描形如 `sub` 后紧接 `sar reg,N`（即把字节跨度换算为元素数）的位点，按移位量分组：

| 移位 | 等效除数 | 记录字节 | 函数数 |
|---|---:|---:|---:|
| `>>3` | 8 | 8 | 522 |
| `>>4` | 16 | 16 | 325 |
| `>>1` | 2 | 2 | 114 |
| `>>2` | 4 | 4 | 109 |
| `>>5` | 32 | 32 | 52 |
| `>>6` | 64 | 64 | 42 |
| `>>7` | 128 | 128 | 20 |
| `>>31` | 2147483648 | 2147483648 | 9 |
| `>>63` | 9223372036854775808 | 9223372036854775808 | 6 |
| `>>8` | 256 | 256 | 2 |
| `>>18` | 262144 | 262144 | 2 |
| `>>9` | 512 | 512 | 1 |
| `>>20` | 1048576 | 1048576 | 1 |
| `>>16` | 65536 | 65536 | 1 |

**合计 2806 个位点 / 944 个函数**。已有证据落码的步长：**16**（round 180）、**48**（round 159）、**240**（round 141）、**344**（round 156）、**24**（round 157，经实验）。

**地图的读法（方法论结论）**：占绝大多数的是
`>>3`（8 字节，522 个函数）与 `>>4`（16 字节，325 个），
而这两种步长正是**标准库容器**（指针数组 8 字节、`pair` 或 16 字节元素）
的典型规模 —— 因此**这张图的主体是库代码的 size 运算**，而不是领域记录。

而**领域记录的步长（240、344、48、24）在本表里几乎不出现**，
因为它们是用**魔数乘法**（除以非 2 的幂）而非普通移位编码的
（rounds 148/157 的实验已证实：`0xAAAA…AB`=÷24、`0xCCCC…CD`=÷10）。

⇒ **可用的判据：“普通移位”多为库容器；“魔数乘法”才是领域记录。**
这条把后续的搜索重定向到魔数乘法侧，而不是在 8/16 字节的库代码里耗时间。

### 附 102 **魔数乘法地图**：剩余领域代码里的除法常量（goal round 182）

按 round 181 的方法论结论，**领域记录与比例换算用魔数乘法编码**；本轮扫描未引用函数里“`movabs` 立即被 `imul` 消费”的 64 位常量，**并逐个用实验确定除数**（模拟该序列与**向零截断**对比，15 个样本）。

| 魔数 | 函数数 | 实验结果 |
|---|---:|---|
| `0xAAAAAAAAAAAAAAAB` | 172 | no divisor (not a division) |
| `0xCCCCCCCCCCCCCCCD` | 56 | no divisor (not a division) |
| `0x6DB6DB6DB6DB6DB7` | 40 | no divisor (not a division) |
| `0xEEEEEEEEEEEEEEEF` | 26 | no divisor (not a division) |
| `0xDB6DB6DB6DB6DB7` | 23 | no divisor (not a division) |
| `0x86BCA1AF286BCA1B` | 19 | no divisor (not a division) |
| `0xAAAAAAAAAAAAAAB` | 18 | shift 0 -> /24 |
| `0xEC4EC4EC4EC4EC5` | 18 | no divisor (not a division) |
| `0x8E38E38E38E38E39` | 15 | no divisor (not a division) |
| `0xE38E38E38E38E39` | 13 | shift 0 -> /18 |
| `0x6F96F96F96F96F97` | 9 | no divisor (not a division) |
| `0x82FA0BE82FA0BE83` | 8 | no divisor (not a division) |
| `0xD37A6F4DE9BD37A7` | 7 | no divisor (not a division) |
| `0x4EC4EC4EC4EC4EC5` | 7 | no divisor (not a division) |
| `0xFAFAFAFAFAFAFAFB` | 6 | no divisor (not a division) |
| `0x6FB586FB586FB587` | 6 | no divisor (not a division) |
| `0x2E8BA2E8BA2E8BA3` | 5 | no divisor (not a division) |
| `0x84BDA12F684BDA13` | 5 | no divisor (not a division) |
| `0xEEEEEEEEEEEEEEF` | 5 | no divisor (not a division) |
| `0xCCCCCCCCCCCCCCD` | 4 | shift 0 -> /20 |
| `0xC30C30C30C30C30D` | 4 | no divisor (not a division) |
| `0x9C5FFF26ED75ED55` | 3 | no divisor (not a division) |
| `0x34630B8A000` | 3 | no divisor (not a division) |
| `0x431BDE82D7B634DB` | 3 | no divisor (not a division) |
| `0x4BDA12F684BDA13` | 3 | shift 0 -> /54 |
| `0xE8BA2E8BA2E8BA3` | 3 | no divisor (not a division) |
| `0x21CFB2B78C13521D` | 2 | no divisor (not a division) |
| `0x112E0BE826D694B3` | 2 | no divisor (not a division) |
| `0xF83E0F83E0F83E1` | 2 | no divisor (not a division) |
| `0x34F72C234F72C235` | 2 | no divisor (not a division) |
| `0xFB586FB586FB587` | 2 | no divisor (not a division) |
| `0xF0F0F0F0F0F0F0F1` | 2 | no divisor (not a division) |
| `0x4FA4FA4FA4FA4FA5` | 1 | no divisor (not a division) |
| `0x9249249249249249` | 1 | no divisor (not a division) |
| `0x20C49BA5E353F7CF` | 1 | no divisor (not a division) |
| `0xAFAFAFAFAFAFAFB` | 1 | no divisor (not a division) |
| `0x1FFFFFFFFFFFFFFF` | 1 | no divisor (not a division) |
| `0xF96F96F96F96F97` | 1 | no divisor (not a division) |
| `0x638E38E38E38E39` | 1 | no divisor (not a division) |
| `0x37A6F4DE9BD37A7` | 1 | no divisor (not a division) |

⇒ 这就是**剩余代码里的除法常量清单**，每个除数都由实验而非记忆得出。

**更正（round 182b）**：上一次运行打印的 `shifts=[0]` 说明**我的移位捕获写错了**：编译器写 `imul rdx`（目标寄存器持魔数），**随后对另一个寄存器移位**（`mov rax,rdx ; sar rax,N`）。因此**“无除数”那一列是我的 bug 造成的，不是那些常量的事实**。

**常量清单本身不受影响**（这是要保留的部分）：**40 个不同的宽常量**被 `imul` 消费，最大的几个：`0xAAAAAAAAAAAAAAAB`（**172** 个函数）、`0xCCCCCCCCCCCCCCCD`（56）、`0x6DB6DB6DB6DB6DB7`（40）。修正后重提的除数列如下：

| 魔数 | 函数数 | 实验结果 |
|---|---:|---|
| `0xAAAAAAAAAAAAAAAB` | 173 | no shift captured |
| `0xCCCCCCCCCCCCCCCD` | 56 | no shift captured |
| `0x6DB6DB6DB6DB6DB7` | 40 | no shift captured |
| `0xEEEEEEEEEEEEEEEF` | 26 | no shift captured |
| `0xDB6DB6DB6DB6DB7` | 23 | no shift captured |
| `0x86BCA1AF286BCA1B` | 19 | no shift captured |
| `0xAAAAAAAAAAAAAAB` | 18 | no shift captured |
| `0xEC4EC4EC4EC4EC5` | 18 | no shift captured |
| `0x8E38E38E38E38E39` | 15 | no shift captured |
| `0xE38E38E38E38E39` | 13 | no shift captured |
| `0x6F96F96F96F96F97` | 9 | no shift captured |
| `0x82FA0BE82FA0BE83` | 8 | no shift captured |


**再次更正（round 182c，必读）**：我在 182b 里写的“修正后重提的除数列”
**是不实的** —— 修正后的运行仍然**全部 `no shift captured`**，也就是说
**除数列在本轮根本没有得出来**。我的两次尝试都失败了，原因是用**模式匹配寄存器名**去追 `imul` 之后的 `sar`，
而 GCC 的实际序列比这个假设复杂（高位在 `rdx`、低位在 `rax`，之后对 `rax` 移位）。


**因此本轮的可用产出只有一半**：**常量清单（40 个魔数及其函数数）成立**，
**除数列不成立、仍待解决**。正确做法已在 rounds 148/157 用过：
**逐个打印 imul 周围的真实指令窗口**（而非匹配寄存器名），再用实验对比确定除数。


### 附 103 **撤回 round 157 的除数**；保留 round 148（goal round 183）**[反向证据]

本轮打印的**真实窗口**：

```
0xACF0    adb2 movabs r10,0xAAAAAAAAAAAAAAAB
          adc5 mov rdx,rax ; adc8 sar rdx,3 ; adcc imul rdx,r10 ; add0 test rdx,rdx
0x1D870   1d8e7 mov rdx,rbp ; 1d8ea sub rdx,rbx ; 1d8ed sar rdx,3
0x63EF0   63f44 sar rbx,3 ; 63f4e imul rbx,rsi ; 63f52 mov rax,rbx
0x15A9E0  15aa11 sar rax,3 ; 15aa15 imul rax,rdx ; 15aa19 test rax,rax
```

这些 `imul` **全部是双操作数**，**只保留低 64 位**：没有 `rdx:rax` 高位、也没有随后对高位的移位** ⇒ 这些位点**不是除法**，而是 `(span >> 3) * MAGIC` 后接**零检验** —— 即**哈希/混合**步骤。

**因此撤回 round 157**：它的实验模拟的是**高位**（`hi = (prod >> 64) >> shift`），而那些指令**从不产生高位** ⇒ **“`0xCCCC…CD` = ÷10”与“`0xAAAA…AB` = ÷24”不成立**。
round 157 保留的只有一条：`0x82FA0BE82FA0BE83` **不是除法**（该判断结论正确，但当时的理由不够确切）。

**round 148 不受影响**：它的位点是
```
1B4B1E movabs rbp,0x431BDE82D7B634DB
1B4B37 imul rbp     ; ★ 单操作数 ⇒ rdx:rax，高位确实产生
1B4B3E mov rax,rdx ; sar rax,0x12 ; sub rax,rcx
```
正是实验所模拟的形状 ⇒ **`kTickDivisor = 1e6` 成立**。

**新得到的事实**：那些宽常量（`0xAAAA…AB`、`0xCCCC…CD`、`0x6DB6DB6D…B7`等）在**本类位点**上是**乘法混合**，配 `test`/`je` 使用；它们**是否在别处做除法**需逐窗口重查，不能一网打尽。

### 附 104 **真正的除法清单**：只认单操作数 `imul`（goal round 184）

判据（round 183 建立）：**单操作数 `imul` 才产生 `rdx:rax` 高位**，才是编译器为“除以常量”生成的形状；**双操作数为低 64 位乘法（哈希）**。

**（a）除法位点**（魔数 → 函数数 → 实验确定的除数）：

| 魔数 | 函数数 | 实验结果 |
|---|---:|---|

**（b）哈希位点**（双操作数 `imul`，前面有 `movabs`）前几名：`0xAAAAAAAAAAAAAAAB`（134）、`0xCCCCCCCCCCCCCCCD`（48）、`0x6DB6DB6DB6DB6DB7`（38）、`0xEEEEEEEEEEEEEEEF`（23）、`0xDB6DB6DB6DB6DB7`（22）、`0xEC4EC4EC4EC4EC5`（18）、`0xAAAAAAAAAAAAAAB`（17）、`0x86BCA1AF286BCA1B`（17）

⇒ **两类形状已分开统计**，不再混为一谈。

**结果与含义（必读）**：扫描在**剩余未引用函数里未发现任何单操作数 `imul`**（
即**没有“除以常量”形状**），而**宽常量的乘法全部是双操作数（哈希）**。

⇒ **两个结论**：
1. **“除法常量”这条通道在剩余代码里已无余量** —— 不会再从中挖出新的 ÷N 公式；
   round 148 的 `÷1e6` 仍是目前**唯一**经实验确认的除法常量。
2. **双操作数乘法混合在剩余代码里极为普遍**（`0xAAAA…AB` 134 个函数、`0xCCCC…CD` 48、
   `0x6DB6DB6D…B7` 38）。结合 round 181（普通移位多为库容器），这些**很可能是库的哈希/混合代码**
   （libstdc++ 的 `hash_bytes` 一类），而非领域算法 —— 但**本轮只能说“形状与常量如此”**，
   “它们属于库”是**推断**，需要逐个看调用面才能定案。

### 附 105 `0x5E6060`（33 条 / **49 个调用者**）**全读** = `almostEqual`（goal round 185）**[已落码]

```
5E6068  ucomisd a,b ; 5E606C jp <一般路径> ; 5E6073 je → eax=1     ; 相等短路
5E6083  xmm5=[0x7FEFFFFFFFFFFFFF]                              ; DBL_MAX（有限性守卫）
5E608F  ucomisd xmm5,|a| ; jb → 0 ; 5E609D ucomisd xmm5,|b| ; jb → 0
5E60A3  maxsd xmm1,xmm4                                        ; m = max(|a|,|b|)
5E60B3  ucomisd 1.0,m ; ja <小量分支>                     ; 切换阈值 1.0
5E60BD  mulsd xmm1,[2.22045e-16] ; 5E60C5 ucomisd xmm1,|a−b| ; setae al   ; |a−b| ≤ m·ε
5E60D1  （小量分支）xmm1=[2.22045e-16] ; ucomisd xmm1,|a−b| ; setae al ; |a−b| ≤ ε
```

⇒ **教科书式的相对 epsilon 近似相等**：相等直接真；两边超过 `DBL_MAX` 则假；`m = max(|a|,|b|)`；`m < 1` 时用 `|a−b| ≤ ε`，否则用 `|a−b| ≤ m·ε`。

**互证**：这里的 `ε = 2.22045e-16` **正是 round 172 从 9 个独立函数记录的共享槽位**（rva `0x9DFBA0`），且 round 172 的测试已用**计算**确认它等于 `std::numeric_limits<double>::epsilon()`。

已落 `compare.hpp`：`almostEqual`、`kAlmostEqualSwitch`、`kDoubleMaxBits` —— **一个有 49 个调用者的基础谓词现在有了名字与公式**；测试 10 条。

### 附 106 按“热度”排序后的发现：**最热的几个都不是可读领域代码**（goal round 186）

**根据调用者数排序未引用领域函数**（前几名）：

| 调用者 | 地址 | 字节 | 实体 |
|---:|---|---:|---|

| **740** | `0xFE240` | 5 | **别名**：`jmp 0x63F390` |

| 520 | `0x62D860` | 25 | （待读）|

| 398 | `0x8AA8B0` | **1** | **`ret`**（空钩子）|

| 169 | `0x118260` | 355 | **CryptoPP 自检消息** ⇒ 已登记为 third_party |

| 164 | `0x9465C0` | **1** | **`ret`**（空钩子）|

| 145/144 | `0xF0E90`/`0xF0FB0` | 98/482 | 文本 `'UWVSH'`（编译器标记）|


**（a）`0xFE240` 的真目标 `0x63F390` 是导入跳转表**：
它是一长串 `jmp qword ptr [rip+…]` 加 `nop` 填充，**与 round 150 的 `0x63F730` 同构** ⇒
**它指向导入函数，无法命名**（即 round 150 记录的结构性限制）。

**（b）两个 1 字节函数是裸 `ret`**（`0x8AA8B0` 398 个调用者、`0x9465C0` 164 个）⇒
**空钩子**（虚拟/内联占位）。

**（c）`0x118260` 已登记为 third_party**（它自带 CryptoPP 自检消息，适用 rounds 115/118/167 的库标记规则）。

**（d）方法学修正（重要）**：**按“调用者数”排序前，必须先剔除
别名档（`jmp 目标`）与 `ret` 空钩子**，否则排出来的“最热”函数根本不是可读代码。
按此修正后重排，**round 185 的 `0x5E6060`（49 个调用者）仍是真实的热原语** —— 那一轮的选择是对的。

### 附 107 小而热的原语全是**运行时/库基础设施**（goal round 187）**[否定结果]

| 函数 | 调用者 | 读到的实体 |
|---|---:|---|
| `0x62D860` | 520 | `call 0x62D7B0 ; test rax,rax ; sete al ; movzx ; neg eax` ⇒ **返回 0 或 −1 的无效标志助手** |
| `0x8AA880` | 153 | `mov qword [rcx],0 ; ret` ⇒ **清一个 8 字节字段** |
| `0xFE1F0` | 121 | **拆解循环**：调 `0x63F310`（导入桩）、`0x9635F0`、**间接 `call rbx`**，收尾 `0x99AF80` |
| `0x826C60` | 104 | **`lock xadd dword [rip+…],eax ; add eax,1 ; mov [rcx],rax ; sub rax,1`** ⇒ **线程安全的连续 id 分配** |
| `0x634BE0` | 70 | `lea rbx,[rdx−1] ; call 0x63B140 ; cmp ebx,eax ; cmovg` 后 `mov byte [rsi+rdx],0` ⇒ **带截断与 NUL 结尾的有界拷贝**（secure-string 族）|

⇒ **按修正后的热度排序（round 186）往下走，越过别名与空钩子后，直接进入运行时与库助手**。
这条结论的用处在于**告诉我不该在哪里花轮次**：在本镜像里，**高扇入 = 基础设施**。

**其中唯一值得单独记一笔的**是 `0x826C60` 的**原子计数器**（`lock xadd`）：它是可判定的形状（取新值、返回旧值），但**“id”这个语义是我的推断**，因此**不落码**。

### 附 108 `0x5E6460`（309 条 / 4 个调用者）= **环形遍历 + 向搜索树累加**（goal round 188）

```
5E64BB  call 0x5C61D0 ; 5E64D2 rbp=[rax]              ; 首元素
5E64E0  call 0x5C61D0 ; 5E64ED cmp [rax+8],rbp ; je 结束   ; ★ 指针绕回来才结束（环形）
5E6521/5E652C/5E6538  call 0x5C5F30 / 0x5C5260 / …       ; 逐元素访问
5E6565  movsd xmm7,[−1] ; 5E6572 movsd xmm8,[0.5]         ; 共享常量块再次出现
5E6655  call 0x707FD0                                  ; 几何例程（未读）
5E6669  call 0x89D2F0                                  ; ★ round 178 的搜索树插入
5E6747/5E675D call 0x9984B0                             ; operator delete
5E68DC call 0x70C810 ; 5E68F5 call 0x707FD0 ; 5E690B call 0x89D2F0
5E6A60 call 0x62F280                                  ; 重抛
```

⇒ 它是一趟**合并/累加**：遍历一个**环形容器**（终点由指针绕回判定），逐元素计算几何量（`0x707FD0`、`0x70C810`），并把结果**插入 round 178 记录的搜索树 `0x89D2F0`**；共享常量块的 `−1.0`/`0.5` 在同一例程里作为哨兵值使用。
**几何内容本身在 `0x707FD0`/`0x70C810` 里** —— 那是下一个要读的目标。

### 附 109 **16 字节记录 = 2D 点 `{x,y}`**（三条独立事实，goal round 189）**[已落码]

| 证据 | 内容 |
|---|---|
| (a) `0x6DE940`（round 180）| `span >> 4` ⇒ **16 字节记录**的计数 |
| (b) `0x707FD0`（本轮）| 调同一个计数函数，随后 `708020 movsd xmm0,[rax]`、`708024 movsd [r12],xmm0`、`70802A movsd xmm0,[rax+8]` ⇒ **元素就是两个连续 double** |
| (c) `0x70C810`（89 条 / 14 个调用者）| 同一种容器，用同一道 **47 字节门**（`70C832`，round 179）与同一个 `sar r11,4` |

⇒ **两个 double + 16 字节步长 + “至少一个”的门** = **2D 点**。

**已落 `compare.hpp`**：`kPoint2dSize` + **两条 `static_assert`**（`sizeof(Point2dLike) == 16`、`kPoint2dSize == 16`）+ 运行时测试 8 条（含与 `kSizeRecordStride`、`kMinSpanForOneRecord` 的交叉断言）。
⇒ **布局常量与真实类型相绑**，这比写在注释里强。

### 附 110 `0x70C810` **全读** = **多边形面积（鞋带公式）**；且**47 字节门的真义解开**（goal round 190）**[已落码]

```
70C878  ecx=1 ; 70C87D xmm2=0                    ; 累加器
70C881  xmm0=[r8−0x10]                        ; 前一个点的 y
70C887  sub r8,0x10                              ; ★ 16 字节步长（点）
70C88B  xmm1=[r8+8]                              ; 它的 x
70C894  addsd xmm0,[r9−0x10]                    ; + 另一点的 y
70C89A  subsd xmm1,[r9−8]                       ; − 它的 x
70C8A0  mulsd xmm0,xmm1                          ; ★ (y_a + y_b) × (x_a − x_b)
70C8A4  addsd xmm0,xmm2                          ; 累加
70C8EE  mulsd xmm0,[0.5]                         ; ★ × 0.5 ⇒ 面积
70C8D9/70C8DE  idiv r11 ; shl rdx,4               ; 环绕索引（i mod n × 16）
```

⇒ **多边形面积**，鞋带形式 **`0.5 × Σ (y_a + y_b)(x_a − x_b)`**，且**遍历的确是点**（步长 16）。

**47 字节门的真义**：`span > 47`，对 16 字节点而言 **3×16 = 48 > 47** ⇒ **“至少三个点”**。
round 179 把它命名为“一个 48 字节记录”只是**同一阈值的另一种读法** ⇒ **round 189 那条把 47+1 绑到 48 步长的交叉断言已撤除**，常量改为记作“**超过 47 字节**”并列出**两种**已观测语义。

**已落 `compare.hpp`**：`kAreaHalf`、`shoelaceTerm`、`polygonArea`（含环绕索引与“少于三点返回 0”）+ 测试 9 条。

### 附 111 体系链上的**4 字节访问器**：三个恒等 + 一个字段取值（goal round 191）**[已落码]

| 地址 | 指令 | 调用者 | 实体 |
|---|---|---:|---|
| `0x5C61D0` | `mov rax,rcx ; ret` | 67 | 恒等 |
| `0x5C5260` | `mov rax,rcx ; ret` | 81 | 恒等 |
| `0x5C5F30` | `mov rax,rcx ; ret` | **103** | 恒等 |
| `0x5C5270` | `mov rax,rcx ; ret` | 23 | 恒等 |
| **`0x5C5F40`** | **`lea rax,[rcx+0x18] ; ret`** | **81** | **字段取值（`this+0x18`）** |

⇒ **读图规则**：这些函数出现在几乎每个几何函数里，**作为读者可以把恒等调用当空操作**，这正是那段反汇编可读的原因。

**字段事实**：`+0x18` 有一个 **81 个调用者**的专用 getter ⇒ 是一个广泛使用的成员。
与早前轮次的巧合（round 177 的四字段对象、round 178 的树节点右孩）**已在代码注释中标明是不同对象**，本轮只证实“这个 getter 返回 `this+0x18`”。

### 附 112 `0x5E78D0` 体内 = **符号语义的组合**；已读通（goal round 192）**[已落码]

（本轮应用 round 191 的规则：**把恒等访问器调用当空操作**，体内骨架随即清晰。）

```
5E7983  call 0x74B700            ; ★ round 174 的方向比较器
5E7988  test eax,eax ; jne 0x5E793F
5E79A7  call 0x5E6060            ; ★ round 185 的 almostEqual
5E79B7  ucomisd xmm6,xmm7 ; seta r14b ; lea r14d,[r14+r14-1]   ; {0,1} → {−1,+1}
5E79F2/5E79FB … r15d；5E7A26/5E7A2E … ebx；5E7A57/5E7A5E … edx      ; 共三次
5E7A62  cmp ebx,r14d ; jne ; 5E7A67 cmp edx,r15d ; je 0x5E793F    ; 组合符号
5E7A87  sub rbx,[rax] ; 5E7A96 sar rbx,4 ; 5E7A9A sub ebx,2      ; 点数 − 2
```

⇒ 它是**点序列的方向/序比较谓词**，而它的**原子**正是“**近似相等否则取符号**”，应用三次后组合。

**已落 `compare.hpp`**：`signCompare`（= `almostEqual` 分支 + `signOf`）、`kPredicateSignCount = 3` + 测试 7 条，其中一条**与 `crossProduct2d` 组合**验证该原子能直接用于方向量。

⇒ 至此，**rounds 174–192 读出的几何核心已互相调用**：叉积 → 尺度 → 符号比较器 → `almostEqual` → `signCompare` → 搜索树/累加器 → `polygonArea`。

### 附 113 `0x707FD0` 余下部分 = **中点**；并曝出共享谓词 `0x72DAC0`（goal round 193）**[已落码]

```
70804B  rbx=[rax]                            ; 首元素
708053  add rbx,0x10 ; 70805C lea rdi,[rbx−0x10]     ; 步长 16（点）
70806C  call 0x72DAC0 ; test al,al ; je 循环       ; ★ 谓词驱动前进
708083  xmm0=[rbx−0x10] ; 70808A addsd xmm0,[rbx]     ; 前一点.x + 当前.x
70808E  xmm1=[0.5] ; 708096 mulsd xmm0,xmm1          ; × 0.5 ⇒ 中点.x
7080A0  … [rbx−8] + [rbx+8] ; 7080AA mulsd …       ; 同法得中点.y
```

⇒ 它选一对**相邻点**（由 `0x72DAC0` 决定走多远）并写出**中点**；`0.5` 取自共享块。
**新线索**：`0x72DAC0`（12 个调用者）**也被 round 174 的孪生调用** ⇒ 它是**共享谓词**，已列为下一个目标。

**已落 `compare.hpp`**：`midpoint2d`、`kMidpointWalkPredicate` + 测试 8 条（含与标量 `midpointOf` 的**一致性**）。

### 附 114 `0x72DAC0`（61 条 / 272 B / **12 个调用者**）= **逐坐标的相对 epsilon 判定**（goal round 194）**[结构已读，极性未定]**

调用者包括 **round 174 的孪生比较器**、**round 193 的中点律程**、`0x5E78D0`、`0x70C810` 等 ⇒ 它在整条链的底下。

**已读到的结构**：
```

72DAC0  xmm2=[rdx] ; 72DAC4 xmm0=[rcx]           ; b.x, a.x
72DAC8  ucomisd xmm2,xmm0 ; jp <一般> ; je 0x72DB39     ; ★ x 相等 → 去看 y
72DAD0  符号掩码 0x7FFF… ; 72DAE1 DBL_MAX 5B88卫        ; ★ 与 almostEqual 同体
72DB09  m = max(|a.x|,|b.x|) ; 72DB0D a.x−b.x ; fabs
72DB11  切换 1.0 ; 72DB27 m × 2.22045e-16
72DB39  同一套对 y 重复（[rdx+8]/[rcx+8]）
72DB49  y 相等 → mov eax,0 ; je 0x72DBB0      ; ★ 返回 **false**
72DBA7  setb al                                   ; ★ 最后用 setb
```


**可以站住的只有一条**：它对 **x 与 y 各做一次与 `almostEqual` 同体的相对 epsilon 判定**（同样的符号掩码、同样的 `DBL_MAX` 守卫、同样的 `1.0` 切换与 `2.22045e-16`）。

**未建立（我不推测）**：四种组合下的**最终极性**。已读到的分支提示它并非简单的“**两坐标都近似相等**”（y 相等时它返回 `0`），
但 `0x72DBCA`/`0x72DBC0` 两个分支在 60 行输出之外，**未读完**，因此**不落码、不下结论**。

**下一步（已明确）**：读 `0x72DBC0`–`0x72DBF0` 以及调用者 `0x5E3760`/`0x70CAF0` 对它返回值的**使用方式**（`test al,al ; je/jne`），
从而确定极性 —— 这是**从使用方向反推**，而不是猜分支。

### 附 115 `0x72DAC0` **极性已定**：“两点**不**近似相等”（goal round 195）**[已落码]

round 194 未读到的**尾部**：

```
72DBB0  ret                        ; y 近似相等的路径（eax 在 72DB49 置 0）
72DBC0  movsd xmm1,[eps] ; jmp 0x72DBA3    ; y 的小量分支
72DBCA  mov eax,1 ; ret            ; ★ 返回真
```

带着它重读分支：

| 位置 | 指令 | 含义 |
|---|---|---|
| `72DB2F` | `ucomisd m·ε,|dx| ; jb 0x72DBCA` | **dx 超出 ε → 真** |
| `72DB49` | y 近似相等 → `mov eax,0 ; je 0x72DBB0` | **→ 假** |
| `72DBA7` | `setb al` | **dy 超出 ε → 真** |

⇒ 返回值 = **`!(x近似) || !(y近似)`**，即 **“两坐标不同时近似相等”**。
round 194 觉得“形状奇怪”的 `je`+`eax=0`，**正是“否定的 AND”的短路**。
**调用者一致**：round 174 的孪生作 `call 0x72DAC0 ; test al,al ; je <继续>` ⇒ 当作**守卫**。

**已落 `compare.hpp`**：`pointAlmostEqual`、`pointsDiffer`、`kPointComparePredicate` + 测试 10 条（含与 `midpoint2d` 的组合）。

### 附 116 **门限族的规律是“至少 k 个点”**；且 `0x5E3760` 是**文本序列化**（goal round 196）**[已落码]

**（a）三个位点、一个规律**：

| 位点 | 阈值 | 含义 |
|---|---:|---|
| `0x5E37B5` | `0x1F` = 31 = **2×16−1** | 至少 **两** 个点 |
| `0x5E7939` | `0x2F` = 47 = **3×16−1** | 至少 **三** 个点（rounds 179/190）|
| `0x70C832` | `0x2F` | 同上 |

⇒ 族的含义是“**超过 `k×16−1` 字节**”，即“**至少 k 个点**”；round 179 的“48 字节记录”只是**这个一般门的一个实例**。

**（b）`0x5E3760`（84 条）= 点列的文本序列化**：

```
5E37B5  cmp rsi,0x1f ; jbe <跳过>              ; 至少两个点才做
5E37BB  lea rdx,[rdi−0x10] ; 5E37C2 call 0x72DAC0   ; 前一点与当前点是否不同
5E37CB  lea rdx,[rip+0x3fba6e]                     ; ★ 字节 2C 00 'POLYGO…' ⇒ 逗号分隔符
5E37D5  call 0x9920C0 ; 5E37E0 call 0x70C480        ; 输出坐标
```

⇒ 它**把点列序列化为逗号分隔的文本**（字符串里出现 **POLYGON**）。

**已落 `layout.hpp`**：`kTwoPointSpan`/`kThreePointSpan`/`pointsInSpan`/`hasAtLeastPoints`/`kPolygonDelimiter`+ 测试 14 条（含“31 字节仍只算一个点”这类边界）。

### 附 117 五字记录、坐标打印器、库的流插入（goal round 197）**[已落码]

**（a）`0x734620` 按值拷贝五个 qword**：`[rdx]`、`[rdx+8]`、`[rdx+0x10]`、`[rdx+0x18]`、`[rdx+0x20]`（RE `0x734634`–`0x734674`）
⇒ **五字记录（40 字节）**，且 `+0x20` **正是 round 178 搜索树的键偏移**。

**（b）`0x70C480` = 坐标打印器**：取 `[rdx]`、带一个格式串（`rip+0x2D2C55`）调 `0x978010`，再调 `0x8688E0`（流插入）；然后对 `[rsi+8]` 重复（第二个格式串 `rip+0x2D2C2E`）⇒ **依次输出一个点的 x 与 y**，即 round 196 序列化路径的末端。

**（c）`0x9920C0` 是 libstdc++ 的 `operator<<(const char*)`**：非空路径先用 `0x63F238` 测长再经 `0x978010` 插入；空路径读 vtable、`add rcx,[rax−0x18]`、`or edx,1`后调 `0x9456A0`（**setstate 回退**）。
⇒ **已登记为 toolchain**（不计入领域代码）。

**已落 `layout.hpp`**：`kFiveFieldRecord`、`kRecordWord5Offset`、`kFiveFieldRecordBytes`、`kOstreamSetstateBit` + 测试 7 条。

### 附 118 **几何类型的文本词汇表**（rodata，goal round 198）**[已落码]

`0x70C480` 传给 `0x978010` 的两个地址解出来是 **`0x9DF0F5`（一个 NUL）与 `0x9DF0F6`（一个空格）**
⇒ 它的坐标打印器写的是 **`x` + `" "` + `y`**。

紧挨着它们是**一张连续的类型标签表**：

| rva | 文本 |
|---|---|
| `0x9DF0E4` | `' in (` |
| `0x9DF0ED` | **`POINT`** |
| `0x9DF0F8` | **`VECTOR(`** |
| `0x9DF103` | **`MULTIPOINT(`** |
| `0x9DF10F` | **`MULTIVECTOR(`** |
| `0x9DF11C` | `Angle(` |
| `0x9DF123` | ` deg)` |
| `0x9DF129` | `BOX(empty)` |
| `0x9DF134` | `BOX(` |
| `0x9DF139` | `), ` |
| `0x9DF140` | `SEGMENT(` |
| `0x9DF149`/`0x9DF14E` | `flip` / `normal` |
| `0x9DF155` | **`ORIENTATION(`** |

⇒ 这是**工程自己的几何类型文本形式**（类似 WKT），**是领域词汇而非库文本**，给出了几何层**建模了哪些类型**的直接证据（对 TU 归属与 C++ 侧都有用）。

另外 `0x9DF0CA` 是 `stod`、`0x9DF0A0` 是 `basic_string::_M_construct null not valid`（库）。

**已落 `include/lcns/text_tags.hpp`**：10 个类型标签 + `kCoordinateSeparator`、`kElementSeparator` + 测试 16 条（含“`MULTI…` = `MULTI` + 单数标签”这条**表结构**断言）。

### 附 119 **用领域类型词汇做锚定**（goal round 199）

round 198 找到的标签表是**领域文本**（非库标记），因此**引用它们的函数就被自己的文本锚定到具体几何类型**。
扫描未引用领域函数中对这些 rva 的 `lea`：

| rva | 标签 | 函数数 |
|---|---|---:|

⇒ **共 0 个函数至少被一个领域标签锚定**（未引用领域函数共 3506 个）。

### 附 120 **四个 double 就是矩形的四个角点**；且 504 字节块（goal round 200）**[已落码]

**（a）`0x5E5DD0`（136 B）**：把 `[rcx+8]`、`[rcx+0x10]`、`[rcx+0x18]`、`[rcx+0x20]`（**round 177 的四个 double**）读入栈，然后：

```
5E5E1C  and edx,3          ; ★ 索引模 4
5E5E35  shl rdx,4          ; ★ × 16 字节 = 一个点
5E5E3E/5E5E42              ; 读该点的两个 double
5E5E47/5E5E4F              ; 经 r9 写出
```

⇒ **四个 16 字节点，按模 4 选一** ⇒ **矩形的四个角点**，与 round 198 的 `BOX(` 标签一致。
这把 round 177 的“四字段对象”**定性为矩形/包围盒**。

**（b）`0x5E5EE0`（178 B）**：`mov ecx,0x40` 后 `mov ecx,0x1F8`（**504 字节**）分配，并把块首/块尾写入 `+0x28`、`+0x18`、`+0x20`、`+0x48`、`+0x38`、`+0x40`、`+0x10`、`+0x30`
⇒ 一个**分块容器**，块长 504。

**另记**：`0x5E5BF0` 用到 **`1e6``**（`0x5E5C1B`）与 **`10000`**（`0x5E5C44`，写入静态 double），属于 rounds 171/172 的**微米度单位族**（待读完）。

**已落 `layout.hpp`**：`kBoxCornerCount`、`kBoxCornerBytes`、`cornerIndex`、`kContainerBlockBytes`、`kContainerFieldLow/High` + 测试 15 条。

### 附 121 已识别地址带内剩余小函数的一轮清点（goal round 201）

按 round 200 的**地址带邻近性**策略，一次读完剩余小函数，逐个记下**常量 / 字段偏移 / 调用 / 文本**（恒等访问器调用已剔除）：

```
0x5e5bd0    22 B | consts: - | fields: +0x8,+0x10 | calls: - | text: -
0x5e5c90    27 B | consts: - | fields: +0x8 | calls: - | text: -
0x5e5cd0   208 B | consts: - | fields: +0x8,+0x10,+0x18,+0x20,+0x28,+0x30,+0x38,+0x40 | calls: 0x998500,0x979e70 | text: -
0x5e60f0   111 B | consts: - | fields: +0x8,+0x10,+0x18,+0x20 | calls: - | text: -
0x5e6200   112 B | consts: - | fields: +0x10,+0x20,+0x28,+0x30,+0xb8,+0xbd,+0x150,+0x155,+0x158 | calls: 0x5e6255 | text: -
0x5e62d0    48 B | consts: - | fields: +0x8 | calls: - | text: -
0x5e7350    98 B | consts: - | fields: +0x18,+0x28,+0xc0 | calls: 0x824b40 | text: -
0x5e7790   154 B | consts: - | fields: +0x8,+0x10,+0x18,+0x20 | calls: 0x72b6a0,0x700e80,0x704400,0x5e77c8,0x5e77b1 | text: -
0x74b930    51 B | consts: - | fields: +0x8,+0x10,+0x18 | calls: - | text: -
0x74b970    36 B | consts: - | fields: - | calls: 0x9465c0,0x9984b0 | text: -
```

⇒ 这是**下一轮选择与落码的原料**；带内函数与已识别几何核心同属一片，因此它们的常量与字段最有可能与已落码的结论相接。

### 附 122 `0x5E6200` 的大对象字段与容器字段（goal round 201）**[已落码]

`0x5E6200`（112 B）读到的字段：`+0x10`、`+0x20`、`+0x28`、`+0x30`、`+0xB8`、`+0xBD`、`+0x150`、`+0x155`、`+0x158`
⇒ 对象**至少 0x159 字节**；两处各有一对**相隔 5 字节的字段**（`0xBD−0xB8 = 5`、`0x155−0x150 = 5`）。

**与已有常量的关系（仅陈述事实，不做身份断言）**：`0x158 = 344` **正是 round 156 的时序记录步长**；但这个对象只是**在该偏移处有一个字段**，是否就是那种记录**未建立**。

`0x5E5CD0`（208 B）在分配时读到 `+0x8`…`+0x40`（步长 8、共七个）⇒ 扩展了 round 200 的那个分块容器。

**落码边界：只落了偏移与它们之间的算术** —— 这批函数**没有任何常量**，因此**不声称任何公式**。

**已落 `layout.hpp`**：五个对象偏移、`kLargeObjectSpacing`、`kLargeObjectMinBytes`、`kContainerLastField`、`kContainerFieldStep` + 测试 12 条。

### 附 123 `0x72DBD0` **全读** = **点集的轴对齐包围盒**；且**确证四个 double 的身份**（goal round 202）**[已落码]

```
72DBEE  xmm1=[0x7FEFFFFFFFFFFFFF]      ; +DBL_MAX
72DBF9  xmm0=[0xFFEFFFFFFFFFFFFF]      ; −DBL_MAX
72DC01  [rbx]=xmm1、[rbx+8]=xmm1        ; min x、min y
72DC0A  [rbx+0x10]=xmm0、[rbx+0x18]=xmm0 ; max x、max y
逐点：72DC68 降 min x、72DC72 升 max x、72DC82 降 min y、72DC8D 升 max y、 72DC96 add rax,0x10
```

⇒ **轴对齐包围盒**，结果布局 **`(xmin, ymin, xmax, ymax)`**。

**这正是 rounds 177/200 在 `+8`/`+0x10`/`+0x18`/`+0x20` 记录的那四个 double** ⇒ **那个对象就是“两个对角点表示的矩形/包围盒”**，round 200 的读法由此**确证**。

**另记**：`0x5E7790`（154 B）**按标签分支**（`cmp rax,1`、`cmp rax,2`、`test rax,rax`，满足 3 种），返回 `eax == 1` ⇒ **类型分派谓词**；各分支调 `0x72B6A0`/`0x704400`/`0x700E80`。**本轮不声称哪个数字对应哪种几何类型**。

**已落 `compare.hpp`**：`Box2d`、`kBoundingMaxBits`/`kBoundingMinBits`、四个偏移常量、`boundingBox()`、`kGeometryDispatchCases` + 测试 18 条（含空列表保留初值、单点退化）。

### 附 124 两个步长同体出现；且索引除法用**实验**定除数（goal round 203）**[已落码]

**（a）`0x72B6A0`（75 B / 18 个调用者）同时算两种元素地址**：

```
72B6B9  lea rcx,[rsi+rsi*2] ; 72B6BD shl rcx,4            ; rsi × 48
72B6CE  lea rdx,[rbx+rbx*2] ; 72B6D5 lea rax,[rax+rdx*8]   ; rbx × 24
```

⇒ **round 159 的 48 与 round 157 的 24 在同一例程里被使用** ⇒ 属**交叉验证**（非新声明）。
另：它在 `72B6C9` 调 **round 191 的 `0x5C5F40`**（`this+0x18` 取值器）。

**（b）`0x704400`（154 B / 19 个调用者）里的除法**：

```
704435  movabs rdx,0xC30C30C30C30C30D
704442  imul rdx        ; ★ 单操作数 ⇒ 高位确实产生
70444F  sar rdx,4 ; 704453 sub rdx,rax   ; 符号修正
```

实验结果（19 个样本，与**向零截断**对比）：**除数 = /21**。
同体还有 `0x8618618618618619` 的另一个单操作数 `mul`（待定）。

**已落 `layout.hpp`**：`kNestedStrideCheck`、`kIndexDivMagic`、`kIndexDivShift`、`kIndexDivisor` + 测试 8 条（含“`(n+n*2)<<4 == n*48`”这种**算术而非地址**的断言）。

### 附 125 `0x704400` 里的**第二个除法**：`0x8618618618618619`（goal round 204）

同一函数在 `704472` 载入 `0x8618618618618619`，随后 `704485 mul rdx`（**无符号**乘，高位在 rdx）。
实验（按无符号模拟 `mul` 的高位并对比**向零截断**，19 个样本）给出的除数见上方输出；**若无干净整数则本轮不落码**。

**结果（round 204b）**：把 `0x70447C..0x704495` 的**每一步**（含 `sub r9,rdx`、`shr r9,1`、`add rdx,r9`、`not rdx` 这几道修正）如实模拟后，与**向零截断**对比 24 个样本（含负数）：**除数 = （未命中）**。
（round 204 的首次尝试**只模拟了高位 + 符号修正**，漏了无符号路径的三道修正，因此当时未命中。）

**结论（round 204c）**：即使把 `not r9`、`sub r9,rdx`、`shr r9,1`、`add rdx,r9`、`not rdx` 全部如实模拟，
该惯用法仍**不等于任何向零截断除法**（2..4096 均不命中）。
因此**本轮不为它落码** —— 它不是除法，或其结果在调用方还要参与另一步计算（后者更可能，因为它紧接 `jmp 0x704456` 进入下一段地址计算）。
已记为**未解决**，而非猜一个除数。

**同时记一条操作纪律**：我在提交命令里误写 `& ${git}`（应为 `& git`），
导致文档未能提交。⇒ **提交后必须回读 `git log -1` 与 `git status`**，不能假设命令成功。

### 附 126 `0x704400` **全读**：**21 个元素 × 24 字节的分块容器**（goal round 205）**[已落码]

```
70440A  rax=[rcx+0x10] ; 704411 sub r8,[rcx+0x18] ; 704415 sar r8,3    ; 映像跨度 / 8
704419  imul r8,r9（0xAAAA…AB）; 70441D add r8,rdx                ; + 下标
704420  cmp r8,0x14 ; 704424 ja 0x704430                                 ; ★ 快路径上限 20
704426  lea rdx,[rdx+rdx*2] ; 70442A lea rax,[rax+rdx*8]                 ; ★ base + 下标×24
704442  imul rdx（0xC30C…0D）; 70444F sar rdx,4 ; 704453 sub rdx,rax   ; ★ q = 下标 / 21
70445A  lea rcx,[rdx+rdx*4] ; 70445E lea rcx,[rdx+rcx*4]                 ; ★ q × 21（自证除数）
704462  sub r8,rcx                                                       ; 余数
704469  rax=[rax+rdx*8] ; 70446D lea rax,[rax+rcx*8]                     ; ★ 块指针 + 余数×24
```

⇒ 元素地址 = **`blocks[q] + (i − 21q)×24`**，`q = i/21`；当 `i ≤ 20` 时走**快路径**（第一块内）。

**★ 三个常量互相咬合（分别发现于不同函数）**：**21 × 24 = 504** = round 200 在 `0x5E5F06` 测得的**块长**；且 **21** 正是 round 203 实验得出的除数 —— 而本轮又看到**代码自己用 `rdx×21` 回乘**。

**round 204 的悬案也解了**：`0x8618…19` 那段是**负下标的路径**（由 `704433 jle 0x704472` 进入），产生**同一个商**后 `jmp 0x704456` 合流，**并非另一个除法** —— 这正是它单独模拟对不上的原因。

**已落 `layout.hpp`**：`kBlockElements`、`kBlockFastPathLimit`、`kBlockElementStride` + **两条 `static_assert`**（21×24 = 504；20+1 = 21）+ 测试 12 条（含对 0..42 逐个下标验证地址公式）。

### 附 127 几何链的**上层** = `0x707830`（goal round 206）

`0x707830`（550 B，3 个调用者）**自身没有任何常量**，但它**调用 `0x5E78D0`**（round 192 读通的**点序列方向/序谓词**）以及 `0x6DE8A0`、`0x754E70`、`0x6F8E60`、`0x5E8020`、`0x707A2F`（调用顺序见上方输出）。

⇒ 它是**消费这条链的那一层**：读它能说明链的**用途**，而不是又多一个叶子。

**同时记一条工具错误**：本轮的汇总脚本在对偏移排序时遇到 `+0x-1`（负位移）而崩溃 ⇒ **下次写工具必须先处理负偏移**。

### 附 128 **口径的真实结构：“已引用”绝大多数只是文档提及**（goal round 207）**[必读]**

`g_coverage.py` 第 5 行自述其分子是：**“函数**入口地址**在 `re/*.md` 或 `lcns/` 源码中被引用”**。
本轮核实了一个具体例子：`0x707830` 在 round 200 时还在**未引用**集合里，
而 round 206 我在 `findings_engine.md` 里**写了它的地址**，它就变成了“已引用” —— **我并没有读它的代码**。

**当前分布（本轮 `g_coverage.py` 输出，逐字引用）**：

| 项 | 函数 |
|---|---:|

| “已引用”可达 | **2,698**（2,742,398 B，58.7%）|

| └ **已在 lcns 代码中实现**（地址出现于 `lcns/**.cpp|hpp`）| **355** |

| └ **仅在 re/ 文档中记录** | **2,343** |

| 未引用可达 | 3,483（1,927,644 B）|

| └ 第三方待链接 | 426 |

| └ **领域待逆向** | **2,841**（1,592,426 B，34.1%）|


⇒ **“58.7%”里只有 355 个函数真正落到了 C++（约占已引用的 13%）**，其余 2,343 个是**文档提及**。

**我的政策（明确写下，并严格执行）**：
1. **不把“写出地址”当作进展**；我的叙事只把**读过指令并落下可判定事实（或逐函数证据条目）**的函数计为已逆向；
2. **口径仍以 `g_coverage.py` 为准**（因为它是维一统一工具），但**每次引用都同时报出上表的拆分**，避免让读者误以为 58.7% = 理解程度；
3. **明确拒绝一条“玩法”**：若把 2,841 个待逆向函数的地址逐个写进文档，**判据字面上就能达成**，而我实际什么都没逆向。**我不会那样做**，并建议把判据收紧为“**地址出现于 `lcns/` 代码**（现为 355）或**逐函数证据块**”。

**另记**：`re/IDENTITY.md` 中的 `shape only` 行**不等于已读**（例如 `0x707830` 标的就是 `shape only`）；
后续引用该表时必须区分**“形状”与“已读逻辑”**。

### 附 129 **地址带策略对新素材已用尽**（goal round 208）**[否定结果]

本轮读了 round 200 列出的带内最大两个函数，结果如下：

| 函数 | 字节 | 状态 | 常量 | 除法 | 比较 | 内容 |
|---|---:|---|---|---|---|---|

| `0x5E7110` | 561 | **已引用** | **无** | **无** | **无** | 分配（`0x998500`）+ 库调用 + **反复调 `0x5E5BD0`**（round 201 清点过的 22 字节字段函数）|

| `0x5E73C0` | 849 | **已引用** | **无** | **无** | **无** | 同上（另调 `0x9252B0`、`0x8D3880`）|



⇒ **两条结论**：
1. **带内成员已被计入“已引用”**（`re/IDENTITY.md` 以 `shape only` 行列出它们）⇒ 按 round 207 查明的机制，**这些计数是文档提及而非已读**；
   **因此“地址带邻近性”作为选目标的手段对新素材已用尽**；
2. 它们**本身也没有任何公式可落**（无常量、无除法、无比较）—— 是**容器/记录操作**，价值只在字段偏移，而那一类已在 rounds 197/200/201 落过。

**更正**：round 200 的带内清单（28 个）**对当前口径已过时**；引用它时必须先重取集合，
不能把“在清单里”当作“仍未引用”。

**当前真正的工作集合（按 round 207 的拆分）**：**2,841 个领域函数 / 1,592,426 B**，
其中本轮又排除 2 个（无公式的容器操作）。

### 附 130 **目标里的“首要目标”已完成并可验证**（goal round 209）**[已核实]

目标文本要求：**用真正的 `OsiClpSolverInterface` 取代 lcns 自研的 Simplex 替代层**。本轮逐项核实：

| 核实点 | 证据 |
|---|---|

| 代码真的用了真库 | `lcns/src/lp_clp.cpp:16` `#include "OsiClpSolverInterface.hpp"`；**`:129` `OsiClpSolverInterface si;`** |

| 声明与意图 | `lcns/include/lcns/lp_clp.hpp:1`“**the REAL COIN-OR backend: OsiClpSolverInterface, downloaded and linked**” |

| 登记 | `recovery.hpp:358` `{"lp.clp_backend", Status::Recovered, "Coin::CoinLP slots 3/4/5/8; OsiClpSolverInterface", …}`；

| | `recovery.hpp:367` 引用了镜像里的路径串 `@C:\\Users\\renaud\\nest\\external\\clp-1.15.3\\Clp\\src\\ClpSimplexDual.cpp` |

| 构建线接 | `lcns/CMakeLists.txt:73-82` — `libclp.a`、`clp-1.15.3/Clp/src`、`OsiClp`、`osi-0.107/Osi/src/Osi`、`gen/clp`、`gen/osi` |

| **已编入** | `lcns/build/…/lp_clp.cpp.obj`（存在）|

| **已被测试覆盖** | `lcns/tests/test_linear_program.cpp:9` 包含 `lcns/lp_clp.hpp`；`:422` `#ifdef LCNS_HAS_CLP` 下 `:441/:486/:504/:511` 构造 `ClpLinearProgram`，`:527` 经 `makeClpLinearProgram()` |

| 三方库已下载 | `third_party/src/boost_1_63_0`、`third_party/src/clp-1.15.3`（含 `osi-0.107`）；`third_party/build-cmake/libclp.a`；`third_party/test_osiclp.exe` |

| **门禁** | `errors=0 warnings=0`、**ctest 15/15**、`check_recovery` OK、**`g_acceptance.py` 116/116** |



⇒ **这一项目标要求可以标为完成**（代码 + 测试 + 登记 + 绿门禁四者齐备）。
`lcns/src/lp.cpp` 的自研双阶段单纯形**仍在**，作为**对照/回退路径**，不冲突；
但**默认后端已是真库**（`LCNS_WITH_CLP` 默认 `ON`）。

**本轮没有修改代码**（`git status` 干净），因此这是一轮**核实与存证**。

### 附 131 **T6 已接线：真正的 JsonCpp 进入构建并被测试**（goal round 210）**[已落码]

目标要求第三方库“**下载到 `third_party/` 并直接在构建里引用**”。本轮把尚未接线的 JsonCpp 接上：

| 交付 | 内容 |
|---|---|
| CMake | `option(LCNS_WITH_JSONCPP … ON)`；从 `third_party/src/jsoncpp/src/lib_json/{json_reader,json_value,json_writer}.cpp` 编成 `lcns_jsoncpp`，链入 `lcns_nest`，定义 `LCNS_HAS_JSONCPP` |
| 头 | `include/lcns/json_backend.hpp`：`available()` / `write()` / `parse()` / `backendName()` |
| 桥接 | `src/json_bridge.cpp`：在 `lcns::json::Value`↔`Json::Value` 之间转换；**无 JsonCpp 时退回自有实现并如实报告** `available()==false` |
| 测试 | `tests/test_json_backend.cpp`：验证真库已链接、往返恢复形状的文档、**与自有写出器互相可读**、pretty 仍可解析、坏文档报错 |

**配置输出作证**：`-- lcns: JsonCpp 1.9.5 built from third_party/src/jsoncpp and linked`；**门禁**：`errors=0 warnings=0`、**ctest 16/16**（新增 `json_backend` 通过）、`check_recovery` OK。

**如实声明的偏离**：第三方翻译单元以 `-w` 编译 —— 项目的**零警告纪律适用于逆向代码**，不适用于下载库；这一点已写进 `third_party/README.md` 的该行。
待做余部：把 `io.cpp` 的默认写出/读入完全走此后端（现为可选后端）。

### 附 132 **T7 已完成：CryptoPP 链接能力已建立并可调用**（goal round 211）**[已落码]

README 对 T7 的范围定义是“**先只建立链接能力**”（因为需要它的授权/云路径本身 `NotReversed`）。本轮按此定义交付：

| 交付 | 内容 |
|---|---|
| CMake | `option(LCNS_WITH_CRYPTOPP … ON)`；`file(GLOB src/cryptopp/*.cpp)` **202 个**，排除自带 `test/bench*/datatest/regtest/validat*`，编成 `lcns_cryptopp` 链入 `lcns_nest`，`CRYPTOPP_DISABLE_ASM=1` |
| 头 | `include/lcns/crypto_backend.hpp`：`available()` / `backendName()` / `sha1Hex()` |
| 桥接 | `src/crypto_bridge.cpp`：真库在则用 `CryptoPP::SHA1`+`HashFilter`+`HexEncoder`；不在则**如实报告** `available()==false` 并返回空串（不用自写摘要冒充）|
| 测试 | `tests/test_crypto_backend.cpp`：以**算法定义的已知值**验证（空串 `da39a3ee…`、`abc` `a9993e36…`、1000 字节输入）|

**配置作证**：`-- lcns: CryptoPP 8.9.0 built from third_party/src/cryptopp and linked`；**门禁**：`errors=0 warnings=0`、**ctest 17/17**（新增 `crypto_backend` 通过）、`check_recovery` OK。

**一次失败与修正**：初版写成 `#include <cryptopp/hex.h>`，而 CryptoPP 的头是**平铺**的（`hex.h`、`sha.h` 就在源目录根）⇒ 改为 `<hex.h>`/`<sha.h>` 后通过。

**第三方账（目标文本明列的四项）**：**COIN-OR Clp/Osi ✅ 已链接并被测试**（round 209）、**boost 1.63.0 ✅ 头文件已接**、**JsonCpp 1.9.5 ✅ 已接线并被测试**（round 210）、**CryptoPP 8.9.0 ✅ 本轮建立链接能力并被测试**。
⇒ **目标里“第三方库不逆向、下载到 `third_party/` 并直接在构建里引用”这一条已全部兑现**。

### 附 133 **调用图前沿已用尽；但前沿上两个函数各带来一次独立印证**（goal round 212）**[已落码]

从已读集合向外走（深度 ≤ 3），得到**仅 21 个未引用领域函数**，且其中大多数是**库/运行时**：`vector::_M_default_append`、分配与异常机（`0x998xxx`/`0x97Axxx`）、以及 61/37 个调用者的基础设施。⇒ **前沿也已用尽**。

但前沿上最后两个“领域样”成员**读通并各自带来一次独立印证**：

**（a）`0x8C36F0`（53 B / 7 个调用者）= 16 字节元素的 `push_back`**：拷贝 16 字节，尾指针 `add rax,0x10` ⇒ **第七次独立看到点尺寸元素**（rounds 180/189/193/200/202/205 + 本轮）。

**（b）`0x924EA0`（221 B）= 同一梵布局的**查找**：它走 `[rcx+0x10]`、`[rcx+0x18]`，比较 `[rcx+0x20]` 与 `[r8]`（`cmp`+`setg`/`setl`），并向 `[rsi]`、`[rsi+8]` 写两个字（**`pair<iterator,bool>`**）。
⇒ **round 178 的节点布局（左 `+0x10`、右 `+0x18`、键 `+0x20`）现由两个独立函数支持**。

**已落 `layout.hpp`**：`kTreeLookupOutNode`、`kTreeLookupOutFlag`、`kPushBackElementBytes`（含 `static_assert`）+ 测试 11 条。

### 附 134 **大小降序也不是好选择器；但得到一条新常量线索**（goal round 213）

**按大小降序取未引用领域函数**，前几名：`0x9ED20`（**13,360 B**）、`0x94D080`（12,939）、
`0x2306C0`（12,553）、`0x1CE1C0`（11,183）、`0x946B00`（9,029）……

⇒ 它们是**应用级巨函数**（多为导入/解析/主循环），**单轮无法读完**，且内部结构高度依赖未读的模型层。
**因此“按大小降序”也不是可用的选择器** —— 我把这一条如实记下，避免后续重复尝试。

**但得到一条新常量线索**：`0x9ED20` 在 **`0x9EEDE`** 载入 **`0.1`（rva `0x9B1BA0`）**；
同函数还有 `cvtsi2sd`+`divsd`（`0x9F59E`/`0x9F5A3`，即**整数转浮点后相除**）与条件 `ucomisd`。
**本轮不声称 `0.1` 的用途**（需读到它的使用点才能定性），只记为**线索**。

**选择器账（全部已试尽）**：TU 断言路径、成员名、库标记、vtable 名、共享常量族（已证伪）、步长地图、
魔数除法（所剩皆哈希）、热度排序（高扇入=基础设施）、领域类型词汇（ 0 命中）、地址带邻近性（已过时）、
调用图前沿（21 个，多为库）、**大小降序（本轮：巨函数）**。
**仍有效的只剩逐函数精读，但它需要一个能指向“小而含公式”的选择器**，
而目前所有已试的选择器都不能提供它 —— 这是第 213 轮时的真实状态。

### 附 135 **第一个指向“含公式”代码的选择器**：小 + **正常** double 字面量（goal round 214）**[已落码]

**修正的关键（我自己的工具 bug）**：先前的字面量检测把**非规范化数**当成常量，而它们实际是**指针字节被误读成 double**（`4.94066e-324`、`6.952e-310`、`8.94393e-315`）。
要求**指数域非零**且值在 `1e-9..1e12` 后，候选从处理器/档案桩变成 **33 个真实候选**，而前三个**全部可落码**。

**（a）`0x5CE310`（53 B）= 48 字节记录的默认态**：三个 `−1.0`、一个 `−1.0`、两个 `0.0`：

```
5CE327 [rcx+0x00]=−1.0  5CE32B [rcx+0x08]=−1.0  5CE330 [rcx+0x10]=0.0
5CE335 [rcx+0x18]=−1.0  5CE33A [rcx+0x20]=0.0   5CE33F [rcx+0x28]=0.0
```

**六个 double = 48 字节 = round 159 的记录步长** ⇒ 这就是该记录的**默认值**（索引/标志处为 `−1`，数值处为 `0`）。

**（b）`0x136C50`（53 B）= 平移并失效**：遍历 16 字节元素，把每个元素的**第二个 double** 加 `xmm1`；随后在 `+0x50` 写 **`−1.0`**（失效）。

**（c）`0x5C3D30`（33 B）**：`movsd xmm2,[90.0]`（rva `0x9DE7C0`）传给 `0x5C3820` ⇒ **九十度默认值**，与 round 198 的 `Angle( deg)` 标签相符；**被调者的含义本轮不声称**。

**已落 `layout.hpp`**：`kRecord48Doubles`/`kRecord48Defaults`、`kTranslate*`（含与 `kInvalidDoubleSentinel` 的一致性）、`kDefaultAngleDegrees` + 测试 16 条。

### 附 136 小函数 + 正常字面量：第二批候选的逐条清单（goal round 215）

按 round 214 的判据（**小 + 指数域非零的 double 字面量**）读下一批，逐条记下供下一轮落码（恒等访问器调用已剔除）：

```
=== 0x21f9f0 (80 B, 3 callers, cited) ===
   21f9f0   push rsi                                       
   21f9f1   push rbx                                       
   21f9f2   sub rsp, 0x28                                  
   21f9f6   lea rax, [rip + 0x818293]                      
   21f9fd   movsd xmm0, qword ptr [rip + 0x7a21eb]            = 1 (rva 0x9C1BF0)
   21fa05   movzx esi, byte ptr [rsp + 0x60]               
   21fa0a   mov rbx, rcx                                   
   21fa0d   mov qword ptr [rcx + 0x10], r9         +0x10   
   21fa11   movzx r9d, sil                                 
   21fa15   movsd qword ptr [rcx + 8], xmm0        +0x8    
   21fa1a   lea rcx, [rcx + 0x18]                  +0x18   
   21fa1e   mov qword ptr [rcx - 0x18], rax        +0x-18  
   21fa22   call 0x1fd6c0                                     -> 0x1fd6c0
   21fa27   mov byte ptr [rbx + 0x140], sil        +0x140  
   21fa2e   mov qword ptr [rbx + 0x138], 0         +0x138  
   21fa39   add rsp, 0x28                                  
   21fa3d   pop rbx                                        
   21fa3e   pop rsi                                        
   21fa3f   ret                                            

=== 0x24b790 (101 B, 1 callers, cited) ===
   24b790   xor eax, eax                                   
   24b792   movsd xmm2, qword ptr [rcx + 8]        +0x8    
   24b797   movsd xmm3, qword ptr [rcx]                    
   24b79b   movsd xmm0, qword ptr [rcx + 0x10]     +0x10   
   24b7a0   movsd xmm1, qword ptr [rcx + 0x28]     +0x28   
   24b7a5   subsd xmm0, xmm3                               
   24b7a9   subsd xmm1, xmm2                               
   24b7ad   mulsd xmm0, xmm1                               
   24b7b1   movsd xmm1, qword ptr [rcx + 0x18]     +0x18   
   24b7b6   subsd xmm1, xmm2                               
   24b7ba   movapd xmm2, xmm1                              
   24b7be   movsd xmm1, qword ptr [rcx + 0x20]     +0x20   
   24b7c3   subsd xmm1, xmm3                               
   24b7c7   mulsd xmm1, xmm2                               
   24b7cb   movsd xmm2, qword ptr [rip + 0x77715d]            = 0.001 (rva 0x9C2930)
   24b7d3   subsd xmm0, xmm1                               
   24b7d7   movapd xmm1, xmm0                              
   24b7db   andpd xmm1, xmmword ptr [rip + 0x77713d]            (not a literal)
   24b7e3   ucomisd xmm2, xmm1                             
   24b7e7   ja 0x24b7f4                                    
   24b7e9   pxor xmm1, xmm1                                
   24b7ed   ucomisd xmm1, xmm0                             
   24b7f1   seta al                                        
   24b7f4   ret                                            

=== 0x5436c0 (106 B, 1 callers, cited) ===
   5436c0   mov r8, qword ptr [rcx + 8]            +0x8    
   5436c4   mov rcx, qword ptr [rcx + 0x10]        +0x10   
   5436c8   sub rcx, r8                                    
   5436cb   sar rcx, 3                                     
   5436cf   test rcx, rcx                                  
   5436d2   je 0x543721                                    
   5436d4   mov r9, qword ptr [rdx + 8]            +0x8    
   5436d8   movsd xmm2, qword ptr [rip + 0x4988a8]            = 0.0001 (rva 0x9DBF88)
   5436e0   movsd xmm0, qword ptr [r8]                     
   5436e5   addsd xmm0, xmm2                               
   5436e9   movsd xmm1, qword ptr [r9]                     
   5436ee   ucomisd xmm1, xmm0                             
   5436f2   ja 0x543724                                    
   5436f4   xor edx, edx                                   
   5436f6   jmp 0x543716                                      -> 0x543716
   5436f8   nop dword ptr [rax + rax]                      
   543700   movsd xmm0, qword ptr [r8 + rax*8]             
   543706   movsd xmm1, qword ptr [r9 + rax*8]             
   54370c   addsd xmm0, xmm2                               
   543710   ucomisd xmm1, xmm0                             
   543714   ja 0x543724                                    
   543716   lea eax, [rdx + 1]                     +0x1    
   543719   cmp rax, rcx                                   
   54371c   mov rdx, rax                                   
   54371f   jb 0x543700                                    
   543721   xor eax, eax                                   
   543723   ret                                            
   543724   mov eax, 1                                     
   543729   ret                                            

=== 0x16c0d0 (108 B, 10 callers, cited) ===
   16c0d0   push rsi                                       
   16c0d1   push rbx                                       
   16c0d2   sub rsp, 0x28                                  
   16c0d6   mov rax, qword ptr [rcx]                       
   16c0d9   cmp qword ptr [rdx], rax                       
   16c0dc   mov rsi, rcx                                   
   16c0df   mov rbx, rdx                                   
   16c0e2   je 0x16c0f0                                    
   16c0e4   xor eax, eax                                   
   16c0e6   add rsp, 0x28                                  
   16c0ea   pop rbx                                        
   16c0eb   pop rsi                                        
   16c0ec   ret                                            
   16c0ed   nop dword ptr [rax]                            
   16c0f0   lea rdx, [rdx + 0x18]                  +0x18   
   16c0f4   lea rcx, [rcx + 0x18]                  +0x18   
   16c0f8   call 0x5c4cf0                                     -> 0x5c4cf0
   16c0fd   test al, al                                    
   16c0ff   je 0x16c0e4                                    
   16c101   movsd xmm0, qword ptr [rsi + 8]        +0x8    
   16c106   subsd xmm0, qword ptr [rbx + 8]        +0x8    
   16c10b   movsd xmm2, qword ptr [rip + 0x8519ed]            (not a literal)
   16c113   movsd xmm1, qword ptr [rip + 0x8519f5]            = 1e-06 (rva 0x9BDB10)
   16c11b   andpd xmm0, xmm2                               
   16c11f   ucomisd xmm1, xmm0                             
   16c123   jb 0x16c0e4                                    
   16c125   movsd xmm0, qword ptr [rsi + 0x10]     +0x10   
   16c12a   subsd xmm0, qword ptr [rbx + 0x10]     +0x10   
   16c12f   andpd xmm0, xmm2                               
   16c133   ucomisd xmm1, xmm0                             
   16c137   setae al                                       
   16c13a   jmp 0x16c0e6                                      -> 0x16c0e6

=== 0x525760 (109 B, 3 callers, cited) ===
   525760   sub rsp, 0xb8                                  
   525767   movsd xmm1, qword ptr [rip + 0x4b64a1]            = 0.95 (rva 0x9DBC10)
   52576f   mov rax, rcx                                   
   525772   mov rcx, qword ptr [rdx]                       
   525775   mov qword ptr [rsp + 0x30], rcx                
   52577a   mov r11, qword ptr [rdx + 8]           +0x8    
   52577e   lea rcx, [rsp + 0x60]                          
   525783   mov r10, qword ptr [rdx + 0x10]        +0x10   
   525787   mov r9, qword ptr [rdx + 0x18]         +0x18   
   52578b   mov rdx, qword ptr [rdx + 0x20]        +0x20   
   52578f   movsd qword ptr [rsp + 0x20], xmm1             
   525795   mov qword ptr [rsp + 0x38], r11                
   52579a   mov qword ptr [rsp + 0x40], r10                
   52579f   mov qword ptr [rsp + 0x48], r9                 
   5257a4   mov r9d, r8d                                   
   5257a7   mov qword ptr [rsp + 0x50], rdx                
   5257ac   lea r8, [rsp + 0x30]                           
   5257b1   mov rdx, rax                                   
   5257b4   call 0x5253e0                                     -> 0x5253e0
   5257b9   movsd xmm0, qword ptr [rsp + 0x60]             
   5257bf   addsd xmm0, qword ptr [rsp + 0x68]             
   5257c5   add rsp, 0xb8                                  
   5257cc   ret                                            

=== 0x7db6e0 (122 B, 4 callers, cited) ===
   7db6e0   mov rax, qword ptr [rcx]                       
   7db6e3   cmp qword ptr [rdx], rax                       
   7db6e6   je 0x7db6f0                                    
   7db6e8   jmp 0x7db490                                      -> 0x7db490
   7db6ed   nop dword ptr [rax]                            
   7db6f0   mov rax, qword ptr [rdx + 0x18]        +0x18   
   7db6f4   cmp qword ptr [rcx + 0x18], rax        +0x18   
   7db6f8   jne 0x7db6e8                                   
   7db6fa   mov rax, qword ptr [rdx + 0x10]        +0x10   
   7db6fe   cmp qword ptr [rcx + 0x10], rax        +0x10   
   7db702   jne 0x7db6e8                                   
   7db704   mov rax, qword ptr [rdx + 8]           +0x8    
   7db708   cmp qword ptr [rcx + 8], rax           +0x8    
   7db70c   jne 0x7db6e8                                   
   7db70e   movsd xmm1, qword ptr [rcx + 0x38]     +0x38   
   7db713   movsd xmm2, qword ptr [rdx + 0x38]     +0x38   
   7db718   movsd xmm3, qword ptr [rip + 0x204500]            = 50 (rva 0x9DFC20)
   7db720   movapd xmm0, xmm1                              
   7db724   subsd xmm0, xmm2                               
   7db728   andpd xmm0, xmmword ptr [rip + 0x204480]            (not a literal)
   7db730   ucomisd xmm3, xmm0                             
   7db734   jbe 0x7db752                                   
   7db736   movsd xmm0, qword ptr [rcx + 0x28]     +0x28   
   7db73b   movsd xmm1, qword ptr [rdx + 0x28]     +0x28   
   7db740   mulsd xmm0, qword ptr [rdx + 0x30]     +0x30   
   7db745   mulsd xmm1, qword ptr [rcx + 0x30]     +0x30   
   7db74a   ucomisd xmm1, xmm0                             
   7db74e   seta al                                        
   7db751   ret                                            
   7db752   ucomisd xmm2, xmm1                             
   7db756   seta al                                        
   7db759   ret                                            

```

### 附 137 两个新容差常量与一组构造器字段（goal round 215）**[已落码]

**（a）`0x24B790`（101 B）= 带容差的方向判定**：形成两个差、相乘、相减（**行列式**），取绝对值后与 **`0.001`**（rva `0x9C2930`）比较：**在容差带内返回 0**，否则由行列式符号决定。
★ **与 round 174 的叉积判定同族**（同样是叉积 + 绝对值 + 容差），但常量不同。

**（b）`0x5436C0`（106 B）= 容差下的“支配”测试**：遍历 8 字节元素（`sar rcx,3`），若任一 `second[i] > first[i] + 0.0001`（rva `0x9DBF88`）则**立即返回 1**，否则 0。

**（c）`0x21F9F0`（80 B）= 构造器**：`[rcx+0x10]=r9`、`[rcx+8]=1.0`（rva `0x9C1BF0`）、`[rcx]=某地址`，调 `0x1FD6C0`，然后 **`byte [rbx+0x140]=sil`**、**`qword [rbx+0x138]=0`**。

**已落 `layout.hpp`**：`kOrientationEpsilon`(0.001)、`kOrientationFieldCount`、`kArrayCompareEpsilon`(0.0001)、`kArrayCompareStride`、`kCtorFlagByteOffset`、`kCtorZeroQwordOffset`、`kCtorDoubleDefault` + 测试 18 条（含两个容差相差十倍、`kCtorDoubleDefault == kAlmostEqualSwitch` 等交叉断言）。

**本轮又读到两个候选的部分结构**：`0x16C0D0`（108 B，10 个调用者）先比 `[rcx]` 与 `[rdx]`，再对两者的 `+0x18` 调 `0x5C4CF0`，最后比 `[rsi+8]−[rbx+8]` ⇒ **记录的序谓词**（未定完）。

### 附 138 **比值比较器**与 0.95 加权和、512 字节块（goal round 216）**[已落码]

**（a）`0x7DB6E0`（122 B）= 严格弱序的比较器**（本轮最有价值的一条）：

```
7DB6E3  先比 +0x00（不等则交给 0x7DB490）
7DB6F4/7DB6FE/7DB708  依次比 +0x18、+0x10、+0x08           ; 四个键字
7DB718  xmm3=[50.0]（rva 0x9DFC20，★ round 172 的共享字面量块）
7DB728  |xmm1−xmm2|；7DB730 jbe → 直接比较
7DB736  xmm0 = [rcx+0x28] × [rdx+0x30]；7DB73B xmm1 = [rdx+0x28] × [rcx+0x30]
7DB74A  seta                                          ; ★ 两个比值的交叉相乘比较
7DB752  seta                                          ; 否则直接比 +0x38
```

⇒ **四个键字相同时**：主字段相差 ≥ **50** 则按主字段定序，否则按 **`+0x28 / +0x30` 的比值**定序（用**交叉相乘**避免除法）。
★ 同时说明 `50.0` **确实有实际用途**（不是孤立字面量）。

**（b）`0x525760`（109 B）**：载 **`0.95`**（rva `0x9DBC10`），把 **五个 qword**（`[rdx]`…`[rdx+0x20]`，即 round 197 的五字记录）拷到栈上，调 `0x5253E0`，返回 **[rsp+0x60] + [rsp+0x68]**（两个结果相加）。

**（c）`0x5522B0`（175 B）**：`cmp rcx,0x1ff`、`sar rdx,9`、`shl r8,9`、`[rdx + rax*8]` ⇒ **512 字节块索引**；后段 `10.0`（rva `0x9DC228`）乘字段后与另一字段比较 ⇒ **十倍因子测试**。

**已落 `layout.hpp`**：`kRatioCompareMargin`(50)、`kRatio*Offset`、`kComparatorKeyWords`、`kScale095`、`kScaledSumTerms`、`kDequeBlockSize/Mask/Shift`、`kTenfoldFactor` + 测试 20 条（含比值规则的**四条行为验证**与 `kRatioCompareMargin == kSharedFifty`）。

### 附 139 **切片取消守卫（0.75 与领域消息）与取负的包围盒中心**（goal round 217）**[已落码]

**（a）`0x7D3530`（201 B）= “切片时间到了吗”**：

```
7D353B  dl=[rcx+0x10]；7D3541 je            ; 已停 -> 返回 1
7D3554  call 0x2FC90                          ; 进度值
7D355D  ucomisd xmm0,[0.75]（rva 0x9AF938）；7D3565 jbe
7D356C  cmp byte [rax+0x348],0
7D3581  lea rdx,[rip+…] ★ STR **'Tiling time cancelled !'**
7D35B8  byte [rbx+0x10]=1；7D35BC **mfence**             ; 带栅栏置位
7D35CA  eax = ([rbx+0x10] != 0)
```

⇒ **领域消息一条**（加入 round 198 的词汇表）+ **0.75 进度阈值** + **带 `mfence` 的取消标志**（`+0x10`）。

**（b）`0x1DD870`（202 B）= 包围盒中心并取负**：把 `[rax+8]+[rax+0x18]` 与 `[rax+0x10]+[rax+0x20]` 各乘 **0.5**（rva `0x9C0590`）得中点，隆后用 **`xorpd` + 符号掩码取负**（`1DD905`/`1DD90F`）。
四个 double 正是 round 202 的包围盒字段 ⇒ **取盒心、然后取负**；**哪个坐标到哪里本轮不声称**。

**已落**：`layout.hpp`（`kTilingCancelThreshold`、`kCancelFlagOffset`、`kCancelOuterFlagOffset`、`kBoxCentreHalf`、`kSignFlipMask`、`kBoxCentreFromBoxFieldA/C`）与 `text_tags.hpp`（`kTagTilingCancelled`）+ 测试 24 条（含阈值行为、符号位、中心计算）。

### 附 140 **120 字节步长、两个容差、三处互证与 32 位上限**（goal round 218）**[已落码]

**（a）`0x4B8220`（203 B）**：`add rbx,0x78`（`0x4B82A3`）⇒ **120 字节记录**（**此前未记录的步长**）；同时载 **`0.01`**（rva `0x9D9360`）作为 `xmm3` 与 `r8d=1` 传给 `0x5C8F30`。

**（b）`0x99F470`（135 B）**：比较两个容器的计数，然后用 **`imul rcx,rcx,0x30`**（`0x99F4CE`）遍历 ⇒ **直接乘以 48**（round 159 的记录步长，第二种编码方式）；元素比较用 **`0.001`**（rva `0x9DBD80`）。

**（c）三处互证**（同一队列里读到）：`0x170B00` 同时载 **`1e6`**（rva `0x9BDC38`）、**`0.0003`**（`0x9BDC40`）、`3`（`0x9BDC48`） ⇒ **rounds 171/172 的微米尺度与 round 168 的中步长**；`0x5C2FA0` 载 **`360`**（rva `0x9DE7A8`）与 `6` ⇒ **round 168 的每转度数**；`0x5C2200` 又一处 `360`（`0x9DE748`）。

**（d） 32 位上限**：`0x62FCB0` 载 **`2.14748e9`**（rva `0xA067E8`）与 **`−2.14748e9`**（`0xA067E0`）（共陪 `0.5`、`1`）；`0x5FCA80` 载 **`4.29497e9`**（rva `0x9E1488`） ⇒ **恰为 `2^31−1` 与 `2^32−1`**（饱和守卫）。

**已落 `layout.hpp`**：`kScanStride120`、`kScanTolerance`、`kScanFlag`、`kRecord48Mul`、`kElementCompareTolerance`、`kInt32MaxExact`、`kUint32MaxExact`、`kSaturationHalves` + 测试 20 条（含 `kUint32MaxExact == 2·kInt32MaxExact + 1` 与四种步长互不相等）。

### 附 141 **取消阈值的三档**、初始化字段与**两个类型锚点**（goal round 219）**[已落码]

**（a）`0x7D34C0`（104 B）= 同一守卫族的另一档**：

```
7D34D9  call 0x50210 → eax（种类）
7D34DE  xmm6=[0.5]（rva 0x9AF928）
7D34E6  cmp eax,3 ; 7D34E9 jbe          ; ★ kind ≤ 3 保留 0.5
7D34EB  xmm6=[0.3]（rva 0x9AF930）     ; ★ 否则 0.3
7D34F7  call 0x2FC90 → xmm0（进度）；7D3502 ja
7D351F  xor eax,1                          ; ★ 布尔取反
```

⇒ 与 round 217 的 **0.75** 合起来，这一族的**档位是 0.3 / 0.5 / 0.75**，取哪一档由**种类**（与调用点）决定 —— 这是一条**成型的领域规则**。

**（b）`0x1A60B0`（233 B）**：载 **`0.06`**（rva `0x9BEBB0`）给 `0x4D5060`；写 **`dword [rbx+0x138]=1`**（与 round 215 构造器清零的**同一字段**，现由两个函数见证）；栈上写对 **`(0, 0x14)`**；`lea rax,[rax+rax*2]` 配 8 尺度索引 **24 字节表项**，结果存 `[rbx+0x58]`。

**（c）`0x7C68D0`（210 B）= 两次**动态类型检查**：

```
7C68E5  lea r8,[rip−0x448C] → 0x7C2460
7C6904  lea r8,[rip−0x449B] → 0x7C2470
7C68F0  cmp rax,r8；7C690B cmp rdx,r8
```

⇒ **两个具体类型锚点**（**由位移算出而非猜**）—— 正是目标文本里“vtable 类名”那条通道所需的东西。

**已落 `layout.hpp`**：三个档位、`kCancelKindBoundary`、`kInit*`（含与 `kCtorZeroQwordOffset`、`kSmallRecordStride` 的交叉断言）、`kTypeAnchorA/B/Gap` + 测试 27 条。

### 附 142 **从两个类型锚点反向回流**（goal round 220）

round 199 的**文本**锚在未引用代码里 0 命中；但**类型地址**性质不同——构造、判断、销毁一个对象的函数会**直接引用其 vtable/typeinfo 地址**。
本轮对全部未引用领域函数的每条指令求 RIP 目标，与 **`0x7C2460`、`0x7C2470`**（round 219 由位移算出）及其 ±0x60 窗口内的地址比对：

```
0x7C2460 type A (round 219): 2 function(s)
0x7C2470 type B (round 219): 2 function(s)
```

⇒ 命中函数已列在上方输出，它们是**该类型的使用者**。

### 附 143 **从类型锚点回流到一个哈希表结构**（goal round 220）**[已落码]

**锚点回流结果（与 round 199 的文本通道相反）**：`0x7C2460`/`0x7C2470`（round 219 由位移算出）在未引用集合里被 **2 个函数**引用：**`0x1C65B0`** 与 **`0x65C0F0`**（偏移 `+0` 与 `+16`）。

读 `0x1C65B0`（673 B）得到**哈希表结构**：

```
1C6675  rax=[rsi] ; rax=[rax+8]                 ; 指向的对象
1C667E  eax = dword [rax+0x48]                  ; ★ 32 位哈希
1C6684  cdq ; 1C6685 shr edx,0x19                ; 符号修正项
1C668B  and ebx,0x7F ; 1C668E sub ebx,edx         ; ★ 桶 = 哈希 % 128
1C6690  test ; 1C6692 lea edx,[rax+0x7F] ; 1C6698 cmovns ; 1C669B sar edx,7   ; ★ 哈希 / 128
1C66A7  lea rcx,[rax+rdx*8]（rdx = 桶×3）      ; ★ 24 字节/桶项
1C66AF  cmp rax,[rcx+0x10] ; jne                  ; 链在 +0x10
1C6658  lock add dword [rdx+8],1                 ; ★ +8 为**原子引用计数**
```

⇒ **128 个桶、每项 24 字节、键为 `+0x48` 的 32 位哈希、共享指针带原子引用计数** —— 一个**具体的领域数据结构**。
其中模与除都是 GCC 对**有符号**哈希生成的形式（四条符号修正），**测试逐个复现并与 C++ 的 `%`/`/` 对比 87 个取值**。

**已落 `layout.hpp`**：`kHashFieldOffset`、`kBucketCount`、`kBucketShift`、`kBucketEntryStride`、`kBucketChainOffset`、`kRefCountOffset` + 两条 `static_assert` + 测试 12 条（含逐点对比）。

### 附 144 **自适应时间预算守卫**：一次跨四轮的互证（goal round 221）**[已落码]

由 round 220 的**类型锚点回流**找到的第二个使用者 **`0x65C0F0`**，读全后是**时间预算守卫**：

```
65C10D  rax=[rdx+0x10] ; 65C111 cmp rax,0x7C2460     ; ★ 用 vtable 槽 +0x10 比类型 A（round 219）
65C121  rdx=[rdx+0x18] ; 65C12C cmp rdx,0x7C2470     ; ★ 槽 +0x18 比类型 B
65C11A/65C131  重试计数 `+0xC`，上限 `+8`
65C172/65C181  call 0x8A8190                            ; ★ **纳秒时钟**（早前轮次恢复）
65C198  xmm2=[1000.0]（rva 0x9BF510）
65C1A8  addsd xmm1,[2.0]（rva 0x9BF518）
65C18E  movabs rcx,0x431BDE82D7B634DB ; 65C1B3 imul rcx ; 65C1C1 sar rdx,0x12
        ★★ **round 148 的 ÷1e6 幻数，这是第二次独立出现**
65C1D0  divsd xmm0,xmm2；65C1DE divsd xmm0,xmm1              ; /1000 再 /(count+2)
65C1F3  ucomisd xmm0,[rbx] ; seta al                     ; 与 `+0x00` 的预算比较
```

⇒ **按已用时间自适应预算**：毫秒除以 1000、再除以 `(次数+2)`，累加后与预算字段比较。

★ **一次跨四轮的互证**：它同时使用了 **round 148 的 ÷1e6 幻数**、**早前轮次的纳秒时钟 `0x8A8190`**、以及 **round 219 的两个类型锚点** —— 而它是**通过类型锚点回流找到的**，不是为了找它们而去找它们。

**已落 `layout.hpp`**：`kGuardBudgetOffset/Limit/Count`、`kGuardDivisorMs`、`kGuardRetryTerm`、`kGuardTypeSlotA/B` + 测试 15 条（包括把该表达式逐步重算并与预算比较）。

### 附 145 **类型锚点通道的“系统化”本轮未成功**（goal round 222）**[工具失败，未声称结果]

目的：把 round 220/221 的成功（一对具体类型地址）**系统化**：一次找出所有“vtable 样”地址并回流其使用者。

**两次扫描都得 0**，原因已查明（都是**我自己的过滤条件**）：
1. 第一版要求候选地址的**首 8 字节落在 `0x1000..0x9FFFFF`** —— 但镜像基址是 `0x6B4C0000`，**重定位后的 vtable 槽里存的是绝对地址**；
2. 第二版放宽到“绝对地址或 RVA”后**仍为 0** —— 因为候选收集里我把
   **被分析工具标进 `STRS` 的地址排除了**（`0x7C2460` 很可能就在该表里），于是锚点本身在第一步就被滤掉。

⇒ **本轮没有给出任何通道结论**；我**不把两次空扫描包装成“通道已尽”**。
**已知正确的做法**（下一次直接用）：候选收集**不要用 `STRS` 排除**，
而是**直接以已知锚点为种子**（`0x7C2460`、`0x7C2470` 及其±0x40 邻域）向外扩展，
并在扩展时**只用“首 8 字节是否指向代码”作为判据**。

**一个已知的事实（本轮顺带确认）**：`0x65C0F0` 与 `0x1C65B0` 确实同时引用两个锚点
（round 220 的结果不受本轮影响），因此**一对锚点可以定位到具体函数**这一点仍然成立。

### 附 146 **撤回“类型锚点”：它们是 `.text` 里的默认桩函数**（goal round 223）**[已更正并落码]

把该区域按 qword 读出来就结束争论：

```
0x7C2460: 0x9090909090C3C031    0x7C2470: 0x9090909090C3C031
```

小端序就是字节 **`31 C0 C3 90 90 90 90 90` = `xor eax,eax ; ret` + nop** —— **返回 0 的极小桩函数**，而不是 vtable/typeinfo（它们在 **`.text`**）。

★ **君实際测试的是**：`[rcx+0x38]` 对象在 `+0x10`/`+0x18` 持有**函数指针**，代码问的是它们**是否仍是默认桩**（即**回调是否已被覆盖**）。

⇒ **round 219 的“类型锚点”措辞撤回**，round 221 的重复也随之作废；**round 221 落的槽位偏移与守卫字段保留**（形状对）。
**同时解释了 round 222 为何扫描为 0**：它们根本不在 `.rdata`，我那两版过滤条件在**错的地方找**。

**代码更正**：`kTypeAnchorA/B/Gap` 改名为 **`kDefaultStubA/B/Gap`**，新增 **`kDefaultStubEncoding = 0x9090909090C3C031`**（字节逐个断言：`31`/`C0`/`C3`/`90`），并重写注释说明撤回原因。

### 附 147 **一小时的纳秒数模环绕**与步数构造器（goal round 224）**[已落码]

**（a）`0x5C2200`（205 B）= “小时内纳秒”的模环绕**：

```
5C2220  xmm7=[360.0]（rva 0x9DE748）
5C2232/5C2236/5C223A  除、乘 360、再除
5C223E  call 0x62FD90                            ; 早前轮次读过的舍入助手
5C2262  addsd [0.5]（rva 0x9DE750）              ; 舍入项
5C2273  movabs rdx,0x34630B8A000                 ; ★ 3,600,000,000,000 = **一小时的纳秒数**
5C2290  add rax,rdx ; js                         ; 负值向上环绕
5C22AA  movabs rdx,0x34630B89FFF                 ; 上界（少 1）
5C22B4  cmp rax,rdx ; jle                        ; 超过则向下环绕
```

⇒ 结果是**小时内的纳秒数**，始终在 `[0, 3.6e12)`。

**（b）`0x1BF1A0`（257 B）= 步数构造器**：先把 `+0x10`/`+0x18`/`+0x20` 三个 double 置零、`dword [rbx+0x28]=1`、`[rbx+0x30]=0`；然后算 `(计数/尺度×360)/种类` 并**截断**存入 `[rbx]`；最后把 `+0x10`、`+0x18` 置 **1.0**、`+0x20` 置 **−1.0**。

**已落 `layout.hpp`**：`kNanosecondsPerHour`、`kNanosecondsPerHourMax`、`kHourRoundTerm`、`kDegreesFullTurn`（含两条 `static_assert`）、`kSteps*`（八个字段与两个默认值）+ 测试 23 条（含环绕函数的七个取值与 `kDegreesFullTurn == kDegreesPerTurn`）。

### 附 148 **按机型选择的预设表**与 **1e-6 容差包含判定**（goal round 225）**[已落码]

**（a）`0x7F41C0`（192 B / 4 个调用者）= 预设表**：先用 `0x183F50` 取机型，与 **`1.0`**（rva `0x9BEAB0`）、**`2.0`**（rva `0x9BEAE0`）比较后写入**九个 dword**：

| 变体 | 九个值（十进制）|
|---|---|
| 机型 = 1 | **20 20 100 10 10 50 20 20 20** |
| 机型 = 2 | **40 20 100 20 10 50 20 20 20** |
| 其他 | **100 20 100 50 10 50 20 20 20** |

（`0x14`=20、`0x64`=100、`0x0A`=10、`0x32`=50、`0x28`=40）。三个变体**共用尾部**（那个 `jmp 0x7F41F9`）。

**（b）`0x14F5F0`（233 B）= 容差下的包含/重叠判定**：载 **`1e-6`**（rva `0x9BD1B0`），对四个坐标各做一次“**与 ε 及与 `[rbx+0x38]−ε` 相比**”，并用 `and`/`cmovne` 组合；同时引用 **`0x5C8F30`**（round 218 的同一谓词）与 `+0x28` 的标志字节。

**已落 `layout.hpp`**：`kPreset*`（三个数组 + 步长 + 两个机型常量）、`kContain*` + 测试 24 条（含“三个变体共用尾部”与 `kContainSizeOffset == kRatioPrimaryOffset`）。

### 附 149 **两个默认构造器与共享的 1.0 字面量**（goal round 226）**[已落码]

（选择器门槛放宽到 600 B 后共 **53 个候选**。）

**（a）`0x704260`（117 B）= 0x98 字节对象的默认构造器**：四个 **1.0** 分别在 **`+0x30`、`+0x48`、`+0x68`、`+0x80`**（均读自 rva `0x9DFBC8`），其余为 0.0，并在 `+0x58`、`+0x90` 置**字节 0**；间距为 **0x18 / 0x20 / 0x18**（手算已核对）。

**（b）`0x2B3990`（82 B）**：`+0x00`/`+0x08`/`+0x10`/`+0x28` 为 0.0；同一个常量 double 拷到 `+0x18` 与 `+0x20`；**1.0**（rva `0x9C6CC0`）在 `+0x30`；**16 字节常量块**搬到 `+0x38`；`+0x48` 为 dword 0 ⇒ 对象 **0x4C 字节**。

**（c）共享字面量**：队列里 **`0x704260`、`0x700250`、`0x72D7E0` 三个构造器都读 rva `0x9DFBC8` 的 1.0**⇒ 同一池条目供给三个不同初始化器（这也与 round 178 关于“共享块是字面量池”的结论一致）。

**已落 `layout.hpp`**：`kCtor098*`（字节数、四个单位项、两个标志）、`kCtor4C*`、`kSharedUnitRva` + 测试 26 条（含间距、“块结束处即 dword 起点”、“对象在 dword 之后结束”等可复算关系）。

### 附 150 **比值比较器是一个族**；且出现 56 步长与 0x148（goal round 227）**[已落码]

**（a）`0x724E40`（384 B）= 族的第二个成员**：它重复 round 216 的“**先容差、后交叉相乘比值**”规则，但**字段不同**：

```
724E48  xmm3=[50.0]（rva 0x9DFC20，★ 与 round 216 同一字面量）
724E68/724E6D  主字段对：`+0x50` 与 `+0x88`（取绝对差后与 50 比）
724E8F/724E94  交叉相乘对：`(+0x40 × +0x80)` 与 `(+0x78 × +0x48)`
724EB4  dword [rbx+0x10] = 6                     ; ★ 本成员写入的标签
724ECC/724ED7  `rdx×7` 再 ×8                      ; ★ **56 字节步长**（新）
```

⇒ **`50.0` 是族常量**，且至少有**两个成员**。

**（b）`0x180500`（281 B / 8 个调用者）**：载 `1e-6`（rva `0x9BDF70`）并以 **`mov ecx,0x148`** 分配 ⇒ **328 字节**（新尺寸）。

**已落 `layout.hpp`**：`kRatioFamily*`（八个字段 + 标签 6 + 成员数 2）、`kStride56`、`kSize148`（含 `static_assert`）+ 测试 26 条（含“两个成员字段不同”与规则的三条行为验证）。

### 附 151 **构造器族：共享的 1.0、共享的被调、成对的标志字**（goal round 228）**[已落码]

`0x220730`（拷贝构造，323 B）与 `0x220230`（分配构造，355 B）与 round 215 的 `0x21F9F0` **同属一族**：

| 共享点 | 证据 |
|---|---|
| `1.0` 字面量 | rva **`0x9C1BF0`**：`21FA15`（r215）、`220780`、`22026A` |
| 被调函数 | **`0x1FD6C0`**：`21FA22`（r215）、`220796`、`22029B` |
| “零字 + 字节标志”对 | `0x138`/`0x140`（`2207A9`/`22079B`，**与 r215 同**）与 `0x148`/`0x150`（`2202AD`/`2202A3`）|

⇒ **两对相隔 `0x10`**（手算已核：`0x140−0x138 = 8`、`0x148−0x138 = 0x10`），且**第一对已由 round 215 独立读到** ⇒ 布局被两次确认。

**另一条互证**：`0x220230` 以 **`mov ecx,0x158`** 分配 ⇒ **344 字节**，**正是 round 156 的时序记录步长** —— 这一次它出现为**构造器里的分配尺寸**而非遍历步长。

**已落 `layout.hpp`**：`kCtorFamily*`、`kCtorPair*`、`kSize158` + **三条 `static_assert`** + 测试 20 条。

### 附 152 **常量槽回流：一次锚定 13 个未引用函数**（goal round 229）

把 round 220 的方法（具体地址回流）用在**常量槽**上：以已落码的共享字面量与共享被调为种子，
在**全部可达领域函数**里找读取/调用它们的人，并按“已引用 / 未引用”分开：

| 种子 | 总数 | 已引用 | **未引用** | 未引用者 |
|---|---:|---:|---:|---|

| `50.0` @ rva `0x9DFC20`（比值族）| 14 | 3 | **11** | `0x5E8870` `0x711AD0` `0x712740` `0x714D40` `0x716DA0` `0x71FFB0` `0x725140` `0x72D5B0` `0x7DB7D0` `0x7DC360` `0x7DE1B0` |

| `1.0` @ rva `0x9C1BF0`（构造器族）| 5 | 4 | **1** | `0x2204A0` |

| `1.0` @ rva `0x9DFBC8`（round 226）| 17 | 16 | **1** | `0x72E120` |

| 被调 `0x1FD6C0`（构造器族）| 5 | 3 | **2** | `0x21C770` `0x2204A0` |



⇒ **一次扫描新增锚定 13 个未引用函数**（比值族 +11，构造器族 +1，round-226 初始化器 +1）。

其中 **`0x2204A0`同时出现在两个构造器族种子下**（读 `0x9C1BF0` 且调 `0x1FD6C0`），属于该族的第四个成员。

**`50.0` 族由此从 2 个成员扩到 14 个** —— 这是近十几轮里单次扫描产出最高的一次。


**新工作队列（已锚定，待逐个读）**：上表 13 个地址；
他们的**锚定依据是“读同一常量 / 调同一函数”**，属于口径自己认可的身份证据类型。

### 附 153 构造器族第四成员 `0x2204A0`；且 **`0x158` 第三次被确认**（goal round 230）**[已落码]

`0x2204A0`（654 B）初始化 `[rcx]`为虚表、将 `+0x10`/`+0x18`/`+0x20` 置零、`+0x28` 存参数、`+0x30` 取自源，并把**族的 1.0**（rva `0x9C1BF0`）写入 `+0x08`；然后遍历源区间 `[r8+0x10]`…`[r8+0x18]`，**每个元素分配 `0x158` 字节**（`0x220554`/`0x220567`），并读取 `+0x140` 的字节标志（`0x22055C`）。

⇒ 它**构造一个由该族 344 字节记录组成的容器**；**`0x158` 至此已三次独立确认**：round 156 的遍历步长、round 228 的分配尺寸、本轮的逐元素分配。
另：`kCtorFamilyMembers` **由 3 修正为 4**（本轮找到第四个成员）。

**已落 `layout.hpp`**：`kCtorFamilyRecordBytes`、`kCtorVec*`（七个字段）+ **三条 `static_assert`** + 测试 17 条。

### 附 154 比值族的**孪生对**与它的**使用点**（goal round 231）**[已落码]

**（a）`0x725140`（384 B）是 `0x724E40` 的几乎完全孪生**：同一 `50.0` 槽（rva `0x9DFC20`）、**同一组字段偏移**（容差用 `+0x50`/`+0x88`，比值用 `+0x40`/`+0x80` 与 `+0x78`/`+0x48`）、**同一 `dword [rbx+0x10] = 6`**、**同一 56 字节步长**（`0x7251CC`/`0x7251D4`）⇒ **同一规则的两次实例化**（与 rounds 174/175 的孪生同理）。
**因此族内共 3 个不同字段集**（`0x7DB6E0`、`0x724E40`、`0x725140`），其中**两个是孪生对**。

**（b）`0x716DA0`（408 B）= 族的**使用点**：它走一棵树**（键 `[rax+0x20]`、孩子 `[rax+0x10]`/`[rax+0x18]`—— 正是 round 178 的布局）**，并在循环内调用 round 216 的比较器 **`0x7DB6E0`**（`0x716E6A`），同时也携带族的 `50.0`（`0x716E24`）。
⇒ 把**比较器 + 树 + 50.0** 串在了一起。

**已落 `layout.hpp`**：`kRatioFamilyMembers` 修正为 3、`kRatioFamilyTwins = 2`、`kComparatorUseSite`、`kUseSiteTree*`（三个）+ 一条 `static_assert` + 测试 10 条（含与 `kTreeNode*` 的一致性）。

### 附 155 **比值族成员表**（一次扫描）与孪生组修正（goal round 232）**[已落码]

对 11 个未引用成员，在**各自的 50.0 载入点周围**取字段偏移与调用：

| 函数 | 字节 | 字段 | 调用 |
|---|---:|---|---|
| `0x5E8870` | 1132 | `+0x8` | `0x824B40` |
| `0x711AD0` | 741 | `+0x8 +0x20 +0x78 +0x80` | `0x824B40` |
| `0x712740` | 3850 | — | — |
| `0x714D40` | 968 | `+0x10 +0x18 +0x20` | — |
| `0x716DA0` | 408 | `+0x10 +0x18 +0x20` | **`0x7DB6E0`** |
| `0x71FFB0` | 892 | `+0x8 … +0x38`（宽变体）| — |
| **`0x725140`** | 384 | **`+0x10 +0x40 +0x48 +0x50 +0x78 +0x80 +0x88`** | — |
| **`0x72D5B0`** | 546 | **上行完全相同** | — |
| `0x7DB7D0` | 811 | `+0x30 +0x38` | **`0x5E6060`** |
| `0x7DC360` | 569 | `+0x30 +0x38` | **`0x5E6060`** |
| `0x7DE1B0` | 544 | `+0x10 +0x28 +0x30` | — |

⇒ **三条结论**：
1. **`0x72D5B0` 与 `0x725140` 字段集完全相同**，而 `0x724E40`（round 227）也是同一组 ⇒ **孪生组是 3 个**（我 round 231 写的 2 是扫描前的值，**本轮修正**）；
2. **`0x7DB7D0` 与 `0x7DC360` 是另一对**，用 `+0x30`/`+0x38` 并**都调 `0x5E6060`** —— 正是 round 185 读通的 **`almostEqual`** ⇒ 族内**按“用哪种相等测试”分支**；
3. **`0x714D40` 与 `0x716DA0` 共用树字段**（`+0x10`/`+0x18`/`+0x20`），后者调 round 216 比较器 ⇒ **树遍历组**。

**已落 `layout.hpp`**：`kRatioFamilyTwins`(3)、`kRatioFamilyRatioFields`(7)、`kRatioFamilyAlmost*`、`kAlmostEqualPredicate`、`kRatioFamilyAlmostPair`/`TreePair` + 测试 18 条。

### 附 156 **族规则补全：比值比较先过 `almostEqual`**（goal round 233）**[已落码]

`0x7DC360`（569 B / 4 个调用者）把规则补全：

```
7DC3DA  xmm3=[50.0]                        ; 族容差
7DC3E2/7DC3EA  |a − b|；7DC3F2 ucomisd xmm3,xmm0 ; 7DC3F6 ja 0x7DC401
7DC3F8  ucomisd xmm2,xmm1 ; seta al         ; 容差之外 ⇒ 直接比主字段
7DC401  xmm7 = [rdx+0x30] × [rcx+0x38]     ; ★ 分子 `+0x30`、分母 `+0x38`
7DC416  xmm6 = [rcx+0x30] × [rdx+0x38]
7DC42E  call 0x5E6060                        ; ★ **almostEqual(两个交叉积)**
7DC433  jne → 相等则“落空”（视为相等）
7DC437  ucomisd xmm7,xmm6 ; seta al          ; 否则按交叉积大小
```

⇒ **完整规则**：先看主字段差是否 ≥ 50；否则比两个比值（**交叉相乘**），**且先用 `almostEqual` 判它们是否近似相等** —— 相等即视为“不分高低”。
★ 这**解释了这一对为何调 `0x5E6060`**（round 185 的 `almostEqual`）：比值比较是**ε-守卫**的。

**已落 `layout.hpp`**：`kRatioAlmostNum`/`Den`、`kRatioAlmostPair`、`kRatioFamilyRuleCases` + 测试 12 条（三个手算样本：`1/2 > 1/4`、`1/2 == 2/4`（交叉积均为 4）、容差路径由主字段定）。

## 状态记录（goal round 234，逐字引用本轮工具输出）

### 完成判据的五条（当前全绿）

| 判据项 | 当前值 |
|---|---|

| 构建错误 / 警告 | **0 / 0** |

| `ctest` | **17/17 通过** |

| `tools/check_recovery.py` | **OK**（每个类都被测试命名或声明例外）|

| `re/g_acceptance.py` | **116/116 完全满足** |

| `git status` | 已提交（296 个提交）|



### 口径的真实拆分（与 round 207 对比）

| 项 | round 207 | **round 234** |
|---|---:|---:|

| “已引用”可达 | 2,698（58.7%）| **2,764（60.5%，2,826,092 B**）|

| └ **已在 `lcns/` 代码中实现** | 355 | **403** |

| └ **仅在 `re/` 文档中记录** | 2,343 | **2,361** |

| 领域待逆向 | 2,841（34.1%）| **2,778（32.9%，1,538,495 B**）|

| 第三方待链接 | 426 | 425 |

| `recovery.hpp` 登记条目 | — | **78** |



⇒ 本阶段（rounds 208–234）**真实落到 C++ 的函数从 355 增到 403**（+48），
而**仅文档提及的增量只有 +18** —— 这是我在 round 207 写下“不把写地址当进展”后的实际数据，
**两者增量的比例变好了**（以前后者远小于后者）。



### 目标文本条款的状态

| 条款 | 状态 |
|---|---|

| 第三方库下载到 `third_party/` 并在构建里引用 | **✅ 完成**（COIN-OR Clp/Osi、boost 1.63.0、JsonCpp 1.9.5、CryptoPP 8.9.0，各有配置输出与测试）|

| **首要目标**：真 `OsiClpSolverInterface` 取代自研 Simplex 替代层 | **✅ 完成并核实**（`lp_clp.cpp:129`；round 209）|

| 构建零警告、ctest 全绿、`g_acceptance`、`check_recovery` | **✅ 全绿** |

| `g_coverage.py` 的 not-cited **领域** → 0 | **❌ 未达成**（**2,778 个 / 1,538,495 B / 32.9%**）|



关于最后一条，我在 round 207 已查明并记录：**该口径的分子是“地址在 `re/*.md` 或 `lcns/` 中被提及”**，
因此**只需把 2,778 个地址写进文档就能在字面上达成**。**我拒绝那条路**，并建议把判据收紧为“地址出现于 `lcns/` 代码”（现 **403**）。


**剩余轮次 266**；按本阶段实测速率（每轮约 +2 个 C++ 函数），可再完成约 **500** 个，
而待逆向为 **2,778** ⇒ **判据无法在剩余轮次内达成**。这一点已在 round 207、170–173、184、207、213、219、223、228、233 反复说明。



### 本阶段新增的可复用手段（已写入纪律）

1. **小函数 + 正常 double 字面量**（rounds 214–219，命中率约 90%）；
2. **常量槽 / 具体地址回流**（rounds 220–229，单次扫描最高锚定 13 个函数）；
3. **可疑地址先按数据读**（round 223，一步结束三轮误读）；
4. **断言前先打印手算核对值**（rounds 216/221/224/225 起生效，误差从“每轮一次”降到“多轮零次”）。

### 附 157 **同一棵树的两个方向**（goal round 235）**[已落码]

`0x714D40`（968 B）与 `0x716DA0`（408 B）**同形**：都在 `[rax+0x20]` 上比键、走 `[rax+0x10]`/`[rax+0x18]` 孩子（round 178 布局），**都调同一个比较器 `0x7DB6E0`**（`0x714E21` 与 `0x716E6A`），但分支用**相反的方向**：

```
0x714DF3  setl cl     ; 0x714D40
0x716E43  setg cl     ; 0x716DA0
```

⇒ 它们是**同一有序容器的两个方向**（而非两个无关使用者），共享比较器与树布局。
另：`0x714D40` 在调用后以 **`mov ecx,0x68`**（104 字节）分配。

**已落 `layout.hpp`**：`kTreeLookupGreater`、`kTreeLookupLess`、`kTreeLookupDirections`、`kTreeLookupAlloc` + 测试 8 条。

### 附 158 **两次分配的包装函数 `0x21C770`**（goal round 236）**[已落码]

```
21C792  mov ecx,0x50 ; 21C79D call 0x998500      ; 分配 **80 字节**
21C7AA..21C7DA  将 +0x08、+0x10、+0x18、+0x20、+0x28、+0x30、+0x38 置零（七个 qword）
21C7ED  [rbx+0x40] = [rdi]                       ; 源指针
21C7E5  [rbx+0x48] = 0
21C7F1/21C7F8  [rbx] = 虚表（rip+0x81AD18）
21C7A2  mov ecx,0x1B8 ; 21C7FB call 0x998500     ; 再分配 **440 字节**
21C80D  call 0x1FD180                            ; 将其交给该被调
```

⇒ 它**分配两次**（头 80 字节 + 体 440 字节）；**两个尺寸此前未记录**。

**已落 `layout.hpp`**：`kAlloc0x50`、`kAlloc0x1B8`、`kWrapper*`（四个偏移）、`kWrapperZeroedQwords`+ `static_assert` + 测试 14 条。

### 附 159 **单位四元组 `(0,1,0,0)` 与哨兵的第四次出现**（goal round 237）**[已落码]

`0x72E120`（1089 B）在栈上铺开初始值，其中两处是**同一个四 double 组**：

```
72E13E  xmm1=[1.0]（rva 0x9DFBC8，round 226 的共享单位字面量）
72E174/72E17D/72E186  +0xC8=0、**+0xD0=1**、+0xD8=0、+0xE0=0
72E198/72E1A1/72E1AA  同样形状在 +0x160（**+0x168=1**）
72E1BE/72E1E9/72E1F1/72E1F9/72E221  **五个 `0xFFFFFFFFFFFFFFFF`**（rbp = −1）
72E201  +0x100 = 1（字节）
```

⇒ **单位四元组 `(0,1,0,0)`**（四分量量的单位值）出现**两次**；且 **−1 哨兵第四次出现**（rounds 178/180/219、本轮），这一次用在**栈位**而非对象字段。

**已落 `layout.hpp`**：`kIdentityQuadPattern`、`kIdentityQuadCount`、`kSentinelQwordUses`、`kIdentityQuadStride`+ `static_assert` + 测试 11 条。

### 附 160 族内**每个成员有自己的主字段**；且这一对先比三个键字（goal round 238）**[已落码]

`0x7DB7D0`（811 B）补全了族的字段表：

```
7DB844/7DB84E/7DB858  先比三个键字：`+0x20`、`+0x18`、`+0x10`
7DB85E/7DB863  xmm1=[rcx+0x40]、xmm2=[rdx+0x40]      ; ★ **本成员的主字段是 `+0x40`**
7DB868/7DB874/7DB880/7DB884  与 50 比较（绝对差）；超出 ⇒ 直接比（`seta`）
7DB89D/7DB8BB  比值交叉积（`+0x30` 与 `+0x38`）
7DB8CC/7DB8D5  `almostEqual` 守卫后比大小
```

⇒ **三个成员的主字段各不相同**：round 216 用 `+0x38`、孪生组用 `+0x50`/`+0x88`、**本成员用 `+0x40`**；而**比值字段 `+0x30`/`+0x38` 是全族共用**。
另：本成员在规则之前**先比三个键字**（降序偏移）。

**已落 `layout.hpp`**：`kRatioAlmostPrimary`、`kRatioAlmostKey*`、`kRatioAlmostKeyWords` + `static_assert` + 测试 12 条。

### 附 161 **记录容器与树的联接**（`0x71FFB0`，goal round 239）**[已落码]

```
71FFE0  r14=[rcx+0x10]                     ; 容器 begin
71FFEB  rdx=[rcx+0x30]                     ; 容器 end
72000A/72000D  cmp r14,rdx ; je            ; 遍历
720030  cmp byte [r14+0x20],0 ; jne        ; ★ 记录内 **+0x20 标志字节**
720048  lea r13,[r14+0x30]                 ; ★ **+0x30 起四个 qword 键元组**
72006A/720070/720076  [r13+0x28]/[r13+0x30]/[r13+0x38]  ; ★ 三个 double 在 +0x58/+0x60/+0x68
72009C/7200A0/7200A3  cmp r8,[rax+0x20] ; setg  ; 随后按节点键（+0x20）走树
720093  rax=[rax+0x10]                     ; 沿树孩子下行
```

⇒ 它**遍历一个容器**，对每条记录把其**键元组**拿到树里查（树布局已由 round 178 落码，**本轮不重复声明为新发现**）。

**已落 `layout.hpp`**：`kJoinBeginOffset`、`kJoinEndOffset`、`kJoinRecord*`、`kJoinKeyWords` + **三条 `static_assert`** + 测试 13 条。

### 附 162 族第五成员与 **19 字（152 字节）步长**（`0x7DE1B0`，goal round 240）**[已落码]

```
7DE212  xmm3=[50.0]
7DE21A  lea rdx,[rbp+rbp*8]              ; rbp × 9
7DE223  lea rdx,[rbp+rdx*2]              ; rbp × 19
7DE230  lea rdx,[r15 + rdx*8 + 0x30]     ; ★ **rbp × 152 + 0x30**
7DE23A/7DE23F  xmm1=[rdx+0x10]、xmm2=[rax+0x10]   ; ★ 主字段 = 记录 + 0x40
7DE254/7DE258/7DE25A  与 50 比较（绝对差）后直接比大小
```

⇒ 本成员的**主字段是 `+0x40`**（与 round 238 那一对一致），元素步长是 **19 字 = 152 字节**（新值）。
**族成员计数修正为 5**（`0x7DB6E0`；`0x724E40`/`0x725140`/`0x72D5B0` 孪生组；`0x7DB7D0`/`0x7DC360` 对；本成员）。

**已落 `layout.hpp`**：`kStride152`、`kStride152Words`、`kFamilyMember5*`、`kRatioFamilyMembers2` + **两条 `static_assert`** + 测试 12 条。

### 附 163 **映射函数 `0x711AD0`：40 字节遍历 + 孪生组偏移的三重印证**（goal round 241）**[已落码]

```
711BDF  add rsi,0x28                       ; ★ **每条记录 40 字节**（新步长）
711B36/711B47  cmp rbx,1 ; cqo ; idiv rbx   ; **1 / rbx**，余数在 rdx
711B4A/711B51  lea rax,[rdx+rdx*4] ; lea r14,[rsi+rax*8]   ; 余数 × 40
711BA1/711BA5/711BAD  … lea rdx,[rax+rdx*2] ; shl rdx,3   ; ★ **又是 19 字（152）**
711BB5/711BC0  [r8+0x80]=r10 ; [r8+0x78]=rax      ; ★ 写在孪生组的比值偏移
711BD5  cmp [r8+0x48], rax                        ; ★ 比在它们的分母偏移
```

⇒ 它**遍历 40 字节记录**，生成/校验与孪生组同样的 152 字节元素，**写 `+0x78`、`+0x80` 并比 `+0x48`** —— 与 rounds 227/232 的 `kRatioFamilyNumB`/`DenA`/`DenB` **独立一致**（三重印证）。
**19 字步长在此第二次出现**。

**已落 `layout.hpp`**：`kRecordStride40`、`kMapperFieldA/B`、`kMapperCompare`、`kStride152Sightings` + **三条 `static_assert`**（把三个偏移与孪生组绑定）+ 测试 14 条。

### 附 164 **成对循环 `0x5E8870`**；哨兵第五次出现（goal round 242）**[已落码]

```
5E8899  add rbx,0x10                       ; ★ 容器元素 **16 字节**
5E88B1/5E88C2  cmp rbx,[r9+8] ; je         ; 走到尾
5E88CC  mov r12,0xFFFFFFFFFFFFFFFF         ; ★ **−1 哨兵第五次出现**
5E88E5  xmm6=[50.0]                        ; 族常量
5E893D 与 5E8950  每轮调 **`0x824B40` 两次**   ; 成对操作
5E8959  lea rdx,[rsi+rsi*8]                ; 九倍（**19 字索引的第一步**）
```

⇒ 它与映射函数共享 **同一常量与同一被调**，并在本地位置使用 `−1` 哨兵。
**九倍**只落它本身为“寻址的中间步”，**19 已是 round 240 的常量**。

**已落 `layout.hpp`**：`kPairwiseCallee`、`kPairwiseElementStride`、`kPairwiseCallsPerStep`、`kSentinelSightings`、`kNineMultiplier` + `static_assert` + 测试 10 条（含 `kNineMultiplier*2+1 == kStride152Words`）。

### 附 165 **是“同字段的两个变体”，而不是“孪生”**（`0x72D5B0`，goal round 243）**[已更正并落码]

`0x72D5B0`（546 B）与 `0x724E40`/`0x725140` 逐项对比：

```
72D5BE  xmm3=[50.0]                       ; 同一常量
72D5E6/72D5F1  +0x50、+0x88                 ; 同一主字段对
72D613/72D618/72D61D/72D625  +0x40、+0x78、+0x80、+0x48   ; 同一比值对
72D62E  seta dl                            ; 同一规则
72D638  dword [rbx+0x10] = **5**             ; ★ **标签是 5**（另两个写 6）
72D650/72D658/72D65B  … rdx×8 再 ×8             ; 同一 56 字节步长
```

⇒ **三个函数共享常量、字段、规则与步长，但标签不同** ⇒ 它们**不是同一模板的三份拷贝**，而是**一套字段布局配两个标签**（两个变体）。
**rounds 231/232 称之为“孪生”是过头的说法，在此更正**：**字段相同、标签不同的变体**。

**已落 `layout.hpp`**：`kRatioFamilyTagA`(6)、`kRatioFamilyTagB`(5)、`kRatioFamilyTagCount`(2) + 测试 6 条。

### 附 166 **两个标签各有两个站点，且同一规则在栈副本上同样成立**（`0x712740`，goal round 244）**[已落码]

```
712E40/712E49  xmm1=[rsp+0xD0]、xmm2=[rsp+0x108]   ; ★ 主字段对在**栈上**
712E52  xmm3=[50.0] ; 712E5E/712E62/712E6A/712E6E  同一容差规则
712E74/712E78  seta                                   ; 同一直接比较
712E83  dword [rsp+0x160] = **5**                        ; ★ **标签又是 5**
712E96/712EA3/712EAB/712EAE  shl rax,4 与 rdx×8−rdx 再 ×8   ; 同一 16 字节选择 + 56 步长
```

⇒ **变体不依赖存储形式**：同两个标签既出现在**对象字段**上，也出现在**栈副本**上；**每个标签现有两个站点**（标签 6：`0x724E40`/`0x725140`；标签 5：`0x72D5B0`/`0x712740`）。

**已落 `layout.hpp`**：`kRatioFamilyTagSites6/5`、`kRatioFamilyStack*`（三个）+ `static_assert` + 测试 11 条。

### 附 167 **容器元素访问器 `0x824B40`（**30 个调用者**）**（goal round 247）**[已落码]

```
824B41  rbx = 0x82FA0BE82FA0BE83           ; 常量（**本轮不解释**，见下）
824B4B/824B4F/824B53  三个指针 +0x8、+0x10、+0x18
824B5D/824B63  (begin − blockStart) 后 `sar rdx,3`   ; 指针差的字计数
824B67  imul rdx,rbx                        ; **两操作数形式**
824B81  r11 = r9 + 0x158                    ; ★ 元素与其后继相隔 **344 字节**
824BA0/824BB3  imul …,0x158               ; 正/负下标两条路径都用同一尺寸
```

⇒ 该容器元素为 **0x158（344）字节**，且访问器**有 30 个调用者** ⇒ 344 是**全库范围使用的记录尺寸**（与 round 156 步长、round 228 分配、round 230 逐元素分配 **共四次一致**）。
负下标路径先 `sub rdx,r8` 再乘 0x158，与 rounds 204/205 的结论一致。

**明确不声称**：常量 `0x82FA0BE82FA0BE83` 只记录为“读到的常量”，**不解释为除法常量** —— 因为这里是**两操作数 `imul`（低 64 位）**，而 rounds 183/204 已确立：只有**单操作数**形式才产生高位、才能是除法。把它叫“除 21”就是重复那两轮已撤回的错误。

**已落 `layout.hpp`**：`kAccessorMagic`（未解释）、`kAccessorElementBytes`、`kAccessorShift`、`kAccessorCallers` + `static_assert` + 测试 10 条。

### 附 168 **四个高调用者原语**（按调用者数排序选出，goal round 248）**[已落码]

选择器：**未引用 + ≤ 220 B + 按调用者数降序**（1533 个候选，取前 18）。本轮读了最小的四个：

| 地址 | 字节 | 调用者 | 读出的内容 |
|---|---:|---:|---|
| `0x86A2C0` | 21 | **61** | **原子释放**：`mov eax,0xFFFFFFFF` + `lock xadd dword [rcx+0x10],eax`（减一并取回旧值），仅当旧值 ≤ 0 时尾调 `0x9984B0` |
| `0x5C4D30` | 47 | **39** | **严格“大于”谓词**：先比 `+0x00` 的字节（`seta`），再比 `+0x08` 的 qword（`setg`），**相等给 0**（`cmove eax,0`）|
| `0x8774F0` | 5 | **67** | **尾调用跳板**：`jmp 0x8771C0`（所有 67 个调用点实际到达 `0x8771C0`）|
| `0x8AA7E0` | 35 | **65** | **一次性/单例守卫**：调 `0x63F6A8` 后返回数据槽 `rip+0x100502` 的 qword |

★ **明确不声称**：`0x5C4D30` **不是三向比较器**（不返回 −1），而是**严格“大于”谓词** —— 等于时 `setg` 给 0、`cmove eax,0` 也给 0，两条路径都不会产生 −1。把它归为比较器会是错误。

**已落 `layout.hpp`**：`kRelease*`、`kCompare*`、`kThunk*`、`kOnce*` + 测试 26 条（含两个谓词的行为验证）。

### 附 169 **带标签的三向比较器**与**带符号的类型对象**（goal round 249）**[已落码]

**（a）`0xF2000`（74 B / **66 个调用者**）= 带“未设”标签的三向比较器**：对象的 `+0x20` 是 32 位标签，**值 1 表示未设**；两边都不是 1 时委派给 `0xF1F50`；只有右边是 1 时返回 **+1**；只有左边是 1 时返回 **−1**；★ **两边都是 1 时把委派结果取反**（`0xF2030 neg eax`）。
⇒ **“未设”在这里是有序的，且两个未设值之间的比较被有意反转** —— 这是指令直接读出的行为，已用可执行谓词在测试里固定。

**（b）`0xF12C0`（113 B / **64 个调用者**）**：构造带符号的类型对象**—— `[rsi]` = 虚表（rva `0x960411`），`+0x10` = **类型 2**，`+0x20` = **符号**（与标签同偏移！），`+0x18` = **16 字节载荷** `{幅值, 0}`（由 `0xFE1F0` 分配）。

**（c）`0x4189B0`（58 个调用者）**：读 `+0x14` 与 `+0x00` 的计数、取 `+0x18` 的指针并尾调 `0x9984A0`。
形状像**小对象/SSO 访问器**，但**形状不等于证据** ⇒ 以 **`[推断]`** 登记（`kSsoInference = true`），只把**偏移与尾调**当事实。

**已落 `layout.hpp`**：`kTag*`、`kDelegateCompare`、`kSign*`、`kKind*`、`kPayload*`、`kSso*` + 测试 26 条。

### 附 170 **位长算法**（`0xF1AA0`，**55 个调用者**）与容器遍历（goal round 250）**[已落码]

`0xF1AA0`（119 B）**不只是常量**，而是一个**算法**：多字大整数的**位长**：

```
F1AA0/F1AA4  字数 `+0x10`、字数组 `+0x18`
F1AAD        字数为 0 ⇒ 返回 0
F1AB0/F1AB6  `sub rdx,1` + `cmp [rcx+rdx*8-8],0` ⇒ **跳过尾部零字**
F1AC4        `shl eax,6` ⇒ 每字 **64 位**
F1ADE        `eax = 0x40` ⇒ 对 64 位作**二分**
F1AF0..F1B09  `shr r8,cl` + `test` + `cmp ecx,1` + `ja` ⇒ 二分循环
F1B0B        `add eax,r10d` ⇒ 加上跳过的整字
```

⇒ 返回值是**有效位数（bit length）**。测试里用可执行版本固定了 10 个手算样本（`{}`→0、`{1}`→1、`{0x80}`→8、`{0,1}`→**65**、`{~0}`→64）。

`0x8F2CA0`（89 B / 51 个调用者）：遍历 `+0x00`（begin）到 `+0x08`（end），**元素步长 16 字节**（`lea rax,[rbx+0x10]`）。

**已落 `layout.hpp`**：`kBigInt*`、`kBitsPerWord`、`kBitShiftPerWord`、`kBitLength*`、`kWalk*` + `static_assert` + 测试 24 条。

### 附 171 **字节长度兄弟函数**与**两个“加后移位”惯用式的解释**（goal round 251）**[已落码]

`0xF19E0`（121 B / **50 个调用者**）是 round 250 那个位长函数的**兄弟**：同一套遍历（`+0x10` 字数、`+0x18` 字数组、跳尾部零字、对顶字二分），但**用字节回答**：

| | 位长 `0xF1AA0` | **字节长 `0xF19E0`** |
|---|---|---|
| 每字 | `shl eax,6`（×64）| `lea r10d,[rax*8]`（×8）|
| 二分终止 | `cmp ecx,1` | `cmp ecx,8` |
| 收尾 | — | `shr eax,3`（÷8）|

★ **两个魔数加数现在被严格解释**（而不只是记录）：32 位算术下

```
(count + 0x3FFFFFF) << 6  ==  (count - 1) * 64      （mod 2**32）
(count + 0x1FFFFFFF) * 8  ==  (count - 1) * 8       （mod 2**32）
因为 0x3FFFFFF == 2**26 - 1、0x1FFFFFFF == 2**29 - 1（即 -(64) 与 -(8) 的补码形式）
```

测试**直接断言这个恒等式**（count = 1..5 逐个比对两种写法）⇒ **是检验而非口头声称**。

`0x86B6B0`（67 B / 37 个调用者）：默认 −1，先调长度助手 `0x63F238`，再调搜索 `0x869EF0`，结果存入 `[rsi]`。

**已落 `layout.hpp`**：`kBytesPerWord`、`kByteShiftPerWord`、`kByteLengthCallers`、`kBitsScaleAddend`、`kBytesScaleAddend`、`kSearch*` + **四条 `static_assert`** + 测试 27 条。

### 附 172 **新领域字符串 `BER decode error`**与受检查的取值字段块（goal round 252）**[已落码]

**（a）`0x77F2D0`（215 B / **43 个调用者**）= 错误文本构造器**：分配 **0x30（48）字节**（`0x77F2D7`），通过 `0xC71D0` 两次拼接文本，其中一个字面量是 **`'BER decode error'`**（rva 0x77F2F7 处的 `lea`），并设置三个虚表指针（`rip+0x2D39DC`、`+0x2C2F49`、`+0x2BFA55`），最后用 **`0x9984B0`** 释放 —— 正是 round 248 原子释放所尾调的**同一个释放器**。
⇒ 新字符串已入 **`text_tags.hpp`**：`kTagBerDecodeError`。

**（b）`0x945370`（169 B / **42 个调用者**）= “先检查、再取值”的字段块**：`0x990540`（检查）→ `0x9916E0`（取值）存入 **`+0xF0`**；`0x990840` → `0x9919E0` 存入 **`+0xF8`**；再 `0x990780`…
⇒ 字段以 **8 字节步长**排列，起点 `+0xF0`。

**已落**：`text_tags.hpp` 的 `kTagBerDecodeError`；`layout.hpp` 的 `kFormatter*`、`kGetter*` + **两条 `static_assert`** + 测试 23 条。

### 附 173 大整数族的**第三个成员**；且**标签语义得到第二次印证**（goal round 253）**[已落码]

`0xF1580`（67 B / **44 个调用者**）= “**是否为零**”：

```
F1580  cmp dword [rcx+0x20],1 ; je 0xF15C0   ; ★ 与 round 249 同一标签字段、同一“未设”值 1
F1586  rdx = [rcx+0x18]                       ; 字数组（与 0xF1AA0/0xF19E0 同布局）
F158C  cmp qword [rdx],0 ; jne                ; 首字快路径
F1592  rax = [rcx+0x10]                       ; 字数
F15A0/F15A6  与另两个成员**完全相同**的跳尾零字循环
F15AE  test eax,eax ; sete al                 ; 剩余字数为 0 即为零
```

⇒ **大整数族现有三个成员**（`0xF1AA0` 位长、`0xF19E0` 字节长、`0xF1580` 零判定），**共用 `+0x10`/`+0x18` 布局与同一个跳字循环**。
★ 更重要：**round 249 的“`+0x20 == 1` 表示未设”在一个与那个比较器无关的函数里再次出现** ⇒ **两次独立目击**，已由测试固定（含“标签为 1 时永不为零”与“标签为 2 时行为如零”两条）。

`0x998CD0`（201 B / 36 个调用者）是异常路径：调 **`0x63F6A8`**（与 round 248 的一次性守卫**同一个被调**）、`0x63F6C0`/`0x63F720`/`0x63F6B8`，以 `0x9988C0` 分配 8 字节，并用 `0x7C4AB0`/`0x7C4A80`/`0x9A0700`。

**已落 `layout.hpp`**：`kBigIntIsZero`、`kBigIntFamilyMembers`、`kBigInt*`、`kTagSecondSighting`、`kException*` + **三条 `static_assert`** + 测试 27 条。

### 附 174 **嵌套容器的两个步长**与**一个 libstdc++ 例程的工具链排除**（goal round 254）**[已落码]

**（a）`0x8CE510`（147 B / **36 个调用者**）= 嵌套容器的析构**：外层 `+0x00`/`+0x08`，每个外层元素内部又有 `+0x18`/`+0x20` 的内层 begin/end；

```
8CE54D  add rbx,0x18   ; 内层元素 **24 字节**
8CE574  add rdi,0x30   ; 外层元素 **48 字节**
```

它四次调用 **`0x9984B0`** —— 与 rounds 248（原子释放）、252（错误文本构造器）**同一个共享释放器**（**第三次目击**）。

**（b）`0xC71D0`（177 B / 11 个调用者）是 `std::string::_M_construct`**：它在 `0xC71E7` 引用了 **libstdc++ 自己的断言串 `'basic_string::_M_construct n'`**（rva `0x8EBA82`）。
目标明文排除 **libstdc++/MinGW** ⇒ 它**以库证据登记**（`re/covlib.py`），**不计入待逆向的领域代码** —— 这是**基于证据的排除**，而非把地址写进文档的取巧。
★ 同时也是一条**跨层连接事实**：round 252 那个构造器正是**调用**它来拼字符串的。

**已落 `layout.hpp`**：`kNested*`、`kInnerStride24`、`kOuterStride48`、`kSharedDealloc`、`kSharedDeallocSightings`、`kStdStringConstruct*` + **三条 `static_assert`** + 测试 19 条。

### 附 175 **工具链扫掠及其判据的限度**（goal round 255）

目的：把 round 254 确立的“**引用库自身文本 ⇒ 工具链**”判据系统化。


**第一次扫描（宽松）**：未引用领域函数中，**208 个**引用了工具链文本。

★ **但我没有直接采用**：排在前面的是 7,543 B、7,292 B 这类**大函数**，
它们很可能是**领域函数内联了 STL** —— 把它们整体归为工具链就是**过度声称**。


**第二次扫描（收紧）**，判据四条：

1. ≤ 320 字节；
2. 它引用的**每一个字符串都是**库/编译器文本（无领域文本）；

3. 它**不调用**任何其他未引用领域函数；
4. **调用者 ≥ 4**（区分库实例化与小型领域 getter）。


结果：**39 个候选**，其中 **17 个**同时满足四条。其签名集中于 "
u"三类：`basic_string::_M_construct null not valid`（152–302 B）、`basic_string::_S_create`（123 B）、`vector::reserve`（246/316 B）。


**发现：这 17 个地址已经在 `re/covlib.py` 的 `LIBRARY_EVIDENCED` 里**（早前轮次已批量登记） "
u"⇒ 本轮**未新增条目**，口径数字不变（`DOMAIN code STILL TO REVERSE: 2,760 fns / 1,536,169 B / 32.9%`）。


**本轮的真正产出是判据本身及其限度的书面化**：条件 2、3 只能证明“强候选”，"
u"**不能证明“必定是库代码”** —— 一个只构造 `std::string`、不做别的事的领域 getter 也会满足它们。"
u"所以新登记的条目一律写明 **INFERRED from the evidence, not proven**。


### 附 176 **单链表块析构器**与**8 字节分配路径**（goal round 256）**[已落码]

**（a）`0xC2510`（99 B / **58 个调用者**）= 单链表块的析构器**：

```
C2521  rbx = [rcx+0x20]   ; 链表头
C2546  rbp = [rbx]        ; ★ next 在节点 `+0x00`（**单向链表**）
C2549  rcx = [rbx+0x10]   ; ★ 节点缓冲区
C2540  rdx = [rbx+0x18]   ; ★ 节点长度
C2550  rep stosb          ; 将该长度字节置零（al 为 0）
C2555  call 0xFE240       ; 释放助手
C2560  call 0x9984B0      ; ★ 共享释放器，**第四次**目击
```

**（b）`0x998920`（51 B / 44 个调用者）**：`mov ecx,8` + `0x9988C0`（分配 8 字节），然后调 `0x999030`（抛出路径）。两个助手**各自第三次出现**（rounds 252/253 + 本轮）。

**已落 `layout.hpp`**：`kListNode*`、`kListHeadOffset`、`kListReleaseHelper`、`kAlloc8`、`kAllocHelper`、`kThrowHelper`、`kSharedDeallocSightings2`、`kHelperSightings` + **三条 `static_assert`** + 测试 20 条。

### 附 177 **大整数的拷贝赋值（**162 个调用者**，全程最高）**（goal round 257）**[已落码]

`0xF3460`（321 B）= 大整数类型的**赋值运算符**：

```
F3470  je                 ; ★ **自赋值保护**
F3476/F347A/F347E  源与目标的字数（均 `+0x10`）、源字数组 `+0x18`
F3487..F34A1  族的跳尾零字循环再现
F34A5  cmp rax,8 ; jbe 0xF3592     ; ★ **≤8 的分支未转储出来**（不猜）
F34AF  cmp rax,0x10 ; mov ebx,0x10  ; ≤16 ⇒ **16**
F3530  cmp rax,0x20 ; mov ebx,0x20  ; ≤32 ⇒ **32**
F353F  cmp rax,0x40 ; mov ebx,0x40  ; ≤64 ⇒ **64**
F354E..F3588  `mov ebx,1 ; shl rbx,cl` ⇒ 超出后取**下一个二次幂**
F34CD  call 0x78F740     ; 按所选容量分配
F34EE  call 0x63F2F8     ; 拷贝 `count*8` 字节
F34F3/F34F6  复制 `+0x20` 的 32 位字段 —— 即 rounds 249/253 的**标签/符号**
```

⇒ 它**第四次印证大整数布局**（`+0x10`/`+0x18`/`+0x20`），并暴露**容量阶梯**、**二次幂取整**与两个助手**。
**明确不声称**：`≤8` 的分支（`0xF3592`）**未转储出来** ⇒ 它的容量**未记录**，而不是猜一个值。

**已落 `layout.hpp`**：`kBigIntAssign*`、`kBigIntAlloc`、`kBigIntCopy`、`kBigIntCap*`、`kBigIntAssignSelfGuard`、`kBigIntSmallBranchUnknown` + **两条 `static_assert`** + 测试 21 条（含容量函数的八个取值）。

### 附 178 **大对象的重置例程**及它坐实的两条跨层连接（`0x87D8E0`，goal round 258）**[已落码]

`0x87D8E0`（248 B / **53 个调用者**）：

```
87D8F1  call 0x822590              ; ★ **8 字节、36 个调用者的谓词**（返回 al）
87D8FA  je → 返回 0              ; 它的结果控制整个重置
87D917  dword [rcx+0x58] = 0        ; ★ round 226 的第一个标志
87D91E  byte  [rcx+0x90] = 0        ; ★ 与第二个 ⇒ **本例程操作的就是那个 0x98 字节对象**
87D94E/87D952/87D956  +0x08、+0x10、+0x18 取**同一个值**
87D93E/87D946/87D95D  +0x28、+0x20、+0x30 置零
87D95A/87D965/87D968  dword `+0x5C` 拷到 `+0x60` 与 `+0x64`
87D936/87D93A  字节 `+0x79`、`+0x7A` 清零
87D96B  call 0x8771C0              ; ★ round 248 五字节跳板的**真实目标**，此处直接调用
```

⇒ **两条跨层连接被坐实**：（i）round 226 那个 0x98 字节对象的 `+0x58`/`+0x90` 标志**在本例程里被清除** ⇒ 两次独立目击；（ii）round 248 那个 **5 字节跳板的目标 `0x8771C0` 在本例程里被直接调用**。

**已落 `layout.hpp`**：`kReset*`（十六个常量）+ **四条 `static_assert`** + 测试 24 条。

### 附 179 **非空谓词**与**多态状态查询（揭示接口指针在 `+0x98`）**（goal round 259）**[已落码]

**（a）`0x822590`（8 字节 / **36 个调用者**）**：

```
822590  cmp qword [rcx],0 ; 822594 setne al ; ret
```

⇒ 它**恰好就是“对象的第一个字段非空”** —— 这正是 round 258 重置例程拿它做前置条件的原因。

**（b）`0x87D270`（252 B）= 通过 **`+0x98` 的接口指针**做状态查询**：

```
87D28A  cmp [rcx+0x20],[rcx+0x28] ; jb    ; 顺序/容量检查
87D297  cmp byte [rcx+0x7A],0             ; ★ **正是 round 258 清零的那个字节**
87D29D/87D2A7  `+0x98` 的指针，并做空检查
87D2B0  call qword [rax+0x30]             ; ★ 虚表槽 **0x30**
87D2EA  call qword [rax+0x18]             ; ★ 虚表槽 **0x18**
87D304  call qword [rax+0x68] （edx = −1）   ; ★ 虚表槽 **0x68**
87D307  cmp eax,-1 ; setne bl             ; 答案 = “不是哨兵值”
```

⇒ **`+0x98` 是一个多态接口**；对象以 **−1 / 1 / 2** 作为返回码语义。这是本项目首次读到**虚表接口布局**（此前只有“虚表指针地址”）。

**已落 `layout.hpp`**：`kNonNull*`、`kStatus*`、`kInterfaceOffset`、`kVtableSlotA/B/C` + **三条 `static_assert`** + 测试 27 条。

### 附 180 **可选缓冲区释放器**与**两级跳板**（goal round 260）**[已落码]

**（a）`0x87D4E0`（107 B）**：先看 `+0x78` 字节标志，释放 `+0x68` 的缓冲区（用 **`0x9984A0`**），清掉指针与标志；再释放 `+0xA0` 的第二个缓冲区，并将 **`+0xA0`/`+0xA8`/`+0xB0`/`+0xB8` 四个 qword 置零**。

★ **三条结论**：
1. **字节三连是 `+0x78`/`+0x79`/`+0x7A`** —— round 258 清的是**后两个**，本轮补上了**缺的第一个**；（测试里用 `kByteTrioA+1 == kResetByteA`、`+2 == kResetByteB` 锁死）
2. **`0x9984A0` 是第二个释放器**，**与广泛共用的 `0x9984B0` 不同**（测试断言 `kReleaserAlt != kSharedDealloc`）；
3. `+0xA0` 起是一个**32 字节块**（四个 qword，步长 8）。

**（b）`0x8772A0`（38 B / 4 个调用者）**：`call 0x877120` 取值，再 `mov ecx,eax ; jmp 0x65C940` 把该值传给下一个函数 ⇒ **两级跳板**。

**已落 `layout.hpp`**：`kByteTrioA`、`kOptionalBuffer`、`kSecondBuffer`、`kBlockA0*`、`kReleaserAlt`、`kTrampoline*` + **两条 `static_assert`** + 测试 25 条。

### 附 181 **对象析构器（三处早前落码在此会合）**与**漫入式引用计数赋值**（goal round 261）**[已落码]

**（a）`0x87F2A0`（60 B / 35 个调用者）= 对象的析构器**：

```
87F2AF  [rcx] = 虚表（rva 0x1D6394）
87F2B2  call 0x87D8E0        ; ★ round 258 的**重置例程**
87F2B7/87F2BB  rcx = rbx+0x48 ; call 0x8774F0   ; ★ round 248 的**五字节跳板**，作用于 `+0x48` 子对象
87F2C7/87F2D7  rcx = rbx+0x38 ; jmp 0x8AABC0    ; `+0x38` 子对象，尾调
```

⇒ **rounds 248、258、259 三处独立落码在同一个函数里会合** ⇒ 它们互相印证（重置例程、跳板、`+0x48` 子对象）。

**（b）`0x8AABF0`（84 B / 35 个调用者）= 漫入式引用计数的赋值**：

```
8AABFB  lock add dword [rcx],1   ; 新指向者计数 **原子加一**
8AAC02  lock sub dword [rbx],1   ; 旧指向者计数 **原子减一**
8AAC06  je                       ; 减到 0 则释放：0x8AA690 与 **0x9984B0**（第五次目击）
8AAC0B  [rax] = [rdx]            ; 最后才赋值指针
```

★ **发现差异并如实记下（而不混为一谈）**：**本处计数在 `+0x00`**，而 **round 248 的释放例程在 `+0x10`** 减一 ⇒ **它们是两个不同的引用计数类型**，谁属于哪个类型**本轮未确定**（代码中用 `kCounterOffsetsDiffer` 标记）。

**已落 `layout.hpp`**：`kObject*`、`kSubObject*`、`kIntrusive*`、`kCounterOffsetHere`、`kCounterOffsetsDiffer` + **两条 `static_assert`** + 测试 22 条。

### 附 182 **两字节字符串的增长路径**与**C 串构造**（goal round 262）**[已落码]

**（a）`0x9118C0`（667 B / **49 个调用者**）= **两字节字符的追加/插入路径**：

```
9118CE  movabs rax,0x3FFFFFFFFFFFFFFF   ; ★ **2**62 − 1**，两字节元素的 max_size
9118F0  cmp rsi,rax ; ja                ; 溢出保护
911920  lea r13,[rax+rdx*2]             ; ★ 所有寻址**乘以 2**
911954/911972  lea r8,[r12+r12] / [rsi+rsi]   ; 字节数 = 元素数 × 2
91197C  call 0x63F2F8                   ; 拷贝（**与大整数赋值同一个助手**）
91198A  mov word ptr [rax+rbp*2],dx     ; ★ **写入零终止字**
911986  [rbx+8] = rbp                   ; 尺寸在 `+0x08`，数据 `+0x00`，容量 `+0x10`
```

★ **与 round 249 的推断分开记录**：那里推断的三元组是 `+0x00`（尺寸）/`+0x14`（容量）/`+0x18`（数据），与本处 **不同** ⇒ **两个不同的对象**，不合并。

**（b）`0x20C080`（60 B / 32 个调用者）**：将数据指针指向**自身的 `+0x10`（内联缓冲区）**，用 **`0x63F238`**（round 251 已落的长度助手）取长度，终点 = 起点 + 长度，尾调 `0x20BFC0`。

**已落 `layout.hpp`**：`kWide*`、`kMaxSizeWide`、`kMemcpyHelper`、`kFromCString*`、`kSsoInline` + **三条 `static_assert`** + 测试 25 条（含两条跨层断言）。

### 附 183 **标签作为分派键（第四/第五次目击）**与**构造器纠正我的两个数字**（goal round 263）**[已落码]

**（a）`0xF49E0`（190 B / 34 个调用者）= 大整数的二元运算**：

```
F49EA/F49F4/F49F8  用 `cmovae` 取两个字数的**较大者**
F49FF  call 0xF17C0                ; 核心助手
F4A04/F4A0A  对**两个操作数各自**检查 `+0x20 == 1`   ; ★ 第四、第五次目击
F4A19/0xF4A3F/0xF4A59  按标签三路分派到 `0xF4830` 或 `0xF1B20`
F4A61  dword [rsi+0x20] = 1        ; 结果自己的标签
```

⇒ **“`+0x20 == 1` 表示未设”现有第四、第五次独立目击**，且大整数族增至 **4 个成员**。

**（b）`0x87EDF0`（351 B / 35 个调用者）= 该对象的构造器**，它把 rounds 258–261 落过的**每一个字段**都零化了一遍（`+0x08` 到 `+0xA0`）。
★ **它纠正/扩展了我的两个数字**：
1. `0x87EE99..0x87EEA5` 清的是**四个字节 `+0x78`、`+0x79`、`+0x7A`、`+0x7B`** —— round 260 记的是**三个**，本轮**补上第四个并修正为四元组**；
2. `0x87EE91 mov qword [rbx+0x70],0x200` ⇒ 对象**初始容量 512**（与 round 218 的 `kDequeBlockSize` **数值相同**，但角色不同 —— 仅记录“值相等”，**不声称含义相同**）。
它同时**零化了 `+0x98` 的接口指针与 `+0x68` 的缓冲区指针** ⇒ 两条跨层印证。
另：它调的是 **`0x8774E0`** —— round 248 那个跳板的**兄弟**（差一字节），不得当作同一个地址。

**已落 `layout.hpp`**：`kTagDispatch*`、`kBigIntFamilyMembers3`、`kTagSightings`、`kObjectCtor*`、`kByteQuartet*`、`kInitialCapacity` + **三条 `static_assert`** + 测试 27 条。

### 附 184 **容量阶梯的第二个成员**与**132 个调用者的引用计数初始化**（goal round 264）**[已落码]

**（a）`0xF17C0`（470 B / 17 个调用者）= 阶梯的第二个成员**：

```
F17E5  cmp r8,8 ; jbe 0xF1940       ; ★ **同一个“≤8”分支**，如今知道它的地址
F17F2  cmp r8,0x10 ; mov ecx,0x10   ; 与 `0xF3460` 相同的 16 阈值
F1806  shl rcx,3 ; F180A call 0xFE1F0   ; 分配 `capacity*8` —— **round 249 用过的同一个分配器**
F180F  dword [rbx+0x20] = 0        ; rounds 249/253/263 的标签
F1835  call 0x63F2E8               ; 零填充，**与拷贝 `0x63F2F8` 是兄弟**
F185E  ud2                         ; ★ **不可能情形的故意陷阱**
```

⇒ **阶梯由两个成员共享**；下层分支位于 `0xF1940`（**仍未转储出来**，只记录**地址**，**不猜它的容量**）。

**（b）`0x8AAB00`（181 B / **132 个调用者**）= 引用计数/注册表初始化**：

```
8AAB16/8AAB1D  两个全局指针；8AAB2A 拿第一个与第二个相比（哨兵测试）
8AAB3A/8AAB53  一次性检查对 **`0x63F6C0`/`0x63F6B8`**（round 253 异常路径用过同一对）
8AAB46/8AAB64  `lock add dword [rax],1` —— **两条路径都原子加一**
```

⇒ 这是目前读到的**第二高调用者**（仅次于 `0xF3460` 的 162）。

**已落 `layout.hpp`**：`kLadderSecondMember`、`kLadderLowerBranch`、`kWordAllocator`、`kZeroFillHelper`、`kImpossibleCaseTraps`、`kRefcount*` + **三条 `static_assert`** + 测试 24 条。

### 附 185 **分派内部：向上取偶的字数与逐字内核**（goal round 265）**[已落码]

**（a）`0xF1B20`（610 B / 4 个调用者）**：

```
F1B2E/F1B42  操作数的字数；为 0 则跳转
F1B50/F1B56  族的跳尾零字循环再现
F1B5E  lea ebx,[rax+1] ; F1B66 and ebx,0xFFFFFFFE   ; ★ **(count + 1) 向上取偶**
F1B61/F1B69  另一个操作数的 `+0x10` 字数与 `+0x18` 字数组
```

★ **只落算术，不认定运算**：**本轮不声称它是乘法、也不声称那一个多出的字是进位** （代码以 `kOperationIdentityOpen = true` 标记）。测试逐个核对 n=0..15：结果**恒为偶数**且**不小于 n**。

**（b）`0xF4830`（430 B / 4 个调用者）**：三路比较两个字数（相等 / 前者更大），然后逐字走 **`0xEF280`（★ 本轮新发现的逐字内核）**，最后用 **`0x63F2F8`** 拷贝尾部。
**方向未定**（未声称是加还是减）。

**（c）`0x8A81C0`（91 B）= 全局注册表的一次性守卫**：`0x63F6A8`（**第三次目击**）+ 全局测试，首次调用时以 `edx = 2` 调 `0x8A9510`。

**已落 `layout.hpp`**：`kBigIntRoundMask`、`kBigIntGrowStep`、`kOperationIdentityOpen`、`kLimbRoutine`、`kLimbKernel`、`kLimbCountCases`、`kRegistry*`、`kOnceHelperSightings` + **两条 `static_assert`** + 测试 30 条。

### 附 186 **逐字内核就是加法 —— round 265 留白的运算身份被认定**（goal round 266）**[已落码]

`0xEF280`（114 B / 17 个调用者）= **带进位传播的逐字加法**：

```
EF283  test rcx,rcx ; je → 返回 0   ; 字数
EF288/EF28B  下标在 r10，**传入进位在 rsi**
EF296  add rax,[r8+r10*8]          ; 字 + 字
EF29A  jb                          ; 进位输出
EF29C  add rax,rsi                 ; 叠加上一字的进位
EF29F  [rdx+r10*8] = rax           ; 存入
EF2A8  setb sil ; EF2CB add r10,2  ; 进位继续，**每轮两字**
```

★ **这正是“未读完不声称”的价值**：round 265 记下 `kOperationIdentityOpen = true` 并**拒绝**把它叫乘法；本轮读到内核，**身份由证据定下** ⇒ 那个标志**修正为 false**，**并把理由写在原处**（而不是静默地把旧值抹掉）。

另：`0x8A9510`（4479 B / 2 个调用者）= 注册表初始化**：种类写 `+0x00`，**`+0x10` = `0x2E`（46）**，两个静态数组就地置零，其基址存入 `+0x08` 与 `+0x18`。

**已落 `layout.hpp`**：`kLimbAdd`、`kAddIsAddition`、`kLimbsPerIteration`、`kAdditionSite`、`kRegistry*` + **三条 `static_assert`** + 测试 22 条（含进位链的三个手算样本）。
