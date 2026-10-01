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
