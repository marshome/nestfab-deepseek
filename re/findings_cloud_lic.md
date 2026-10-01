# libcns_dump_64.dll — 云/网络计算路径 与 授权/机器绑定层 逆向报告

对象：`D:\Nesting\nestfab\libcns_dump_64.dll`（11,808,768 B，MD5 `01fea4b73a33dd233c66ca76235313fa`，PE32+ AMD64，
MinGW-w64 静态链接 Boost 1.63 / Clipper / COIN-OR Clp / **CryptoPP** / JsonCpp）。
**内存转储文件，不可加载、未执行**；`OriginalFirstThunk == 0`，IAT 内是转储进程的陈旧绝对地址。

标注约定：

* **[已证实]** = 由反汇编/字节直接读出；
* **[推断]** = 由上下文/常量/调用约定推断；
* **[未确认]** = 未能确定。

所有 RVA 均为文件内 RVA。辅助结论来自 `re\prof2.pkl`、`re\vtables.json`、`re\funcs.json`。

---

## 0. 关键地址速查

| 名称 | RVA | 证据 |
|---|---|---|
| `Engine::CloudEngine` vtable（地址点） | `0xA3CED0`(头) / 地址点 `0xA3CEE0` | 槽 `0x755000,0x754FB0,0x26A60` |
| `Engine::CloudEngine::Run`（唯一虚函数覆盖） | **`0x26A60`** | vtable 第 3 槽；引用 `"CloudEngine::Run "`、`"..\engine\cloud_engine.cpp"` |
| `LaunchLocalComputation`（导出，ord 51/52） | `0x2AB0` | 唯一引用 `cns_force_cloud` / `cns1.optalog.com;cns2.optalog.com` 的函数 |
| `LaunchLimitedLocalComputation`（导出，164/165） | `0x3310` | 自身 `__func__` |
| `LaunchEstimateLocalComputation`（导出，216/217） | `0x3360` | `"// LaunchEstimateLocalComputation"` |
| `LaunchComputation`（导出，35/36） | `0x6100` | 自身 `__func__` |
| `WaitComputationTermination`（导出，47/48） | `0x104D0` | 自身 `__func__` |
| `WaitNextSolution`（导出，49/50） | `0x10650` | 引用 `c:\Temp\computation_solution.html` |
| `GetComputationStatus`（导出，15/16） | `0x107E0` | 自身 `__func__` |
| `CancelComputation`（导出，53/54） | `0x10880` | `"CancelComputation "` |
| `TerminateComputation`（导出，122/123） | `0x10920` | `"TerminateComputation "` |
| `AsyncCancelAllComputationsAndDeleteLaunchingOrder`（导出，252/253） | `0xB540` | 自身 `__func__` |
| 本地调度/授权闸门 | `0x1E70` | 由 `0x2AB0`、`0x6100` 调用；引用 `"Order valid"`,`"Keys: "`,`"Launching local engines "` |
| HTTP GET 请求文本构造 | `0x6DA1F0` | 引用 `GET `/`Host: `/`Accept: */*`/`Connection: close` |
| HTTP PUT 请求文本构造 | `0x6DBD40` | 引用 `PUT `/`Content-Length: `/`Content-Type: text/plain` |
| HTTP 响应解析（状态行 `HTTP/1.1`） | `0x6DAB80` / `0x6DC480` | 引用 `"HTTP/"`、`" HTTP/1.1"`，并调用 `nanosleep` |
| HTTP GET 执行（高层） | `0x2AF30`（包装 `0x2B630`） | 端口常量 `0x50`=80 |
| HTTP PUT 执行（高层） | `0x2B660`（包装 `0x2BD20`） | 端口常量 `0x50`=80 |
| `UnSerializeSolution` | `0x1C5F0` | 自身 `__func__`；引用 `internal.cpp`、`solution.Bindable(problem)` |
| `CreateProblem`（LaunchingOrder→内部问题/Json） | `0x1EE50` | 自身 `__func__`（3076 insn） |
| `GenerateLaunchingOrderProblem` | `0xB8D0` **[推断]** | 引用 `"source_version"` 与 `"GenerateLaunchingOrderProblem"` |
| `GetPCId`（导出，170/171） | `0xC010` | 自身 `__func__` |
| GetPCId 的 worker | `0x24290` | 调用 `GetAdaptersInfo` 与 `GetVolumeInformationA` |
| `UnLockLaunchingOrder`（导出，76/77） | `0xD430` | 自身 `__func__` |
| `UnLockLaunchingOrderSntl`（导出，188/189） | `0xE180` | 自身 `__func__` |
| `UnLockLaunchingOrderOxy`（导出，222/223） | `0xE1F0` | 自身 `__func__` |
| `UnLockLaunchingOrderPCId`（导出，228/229） | `0xE260` | 自身 `__func__` |
| HASP 写/读 dongle | `0x12BBA0` / `0x12BCC0` | `hasp_login/hasp_read/hasp_write` |
| base64 blob（HASP Vendor Code） | `0x9A2080`，984 字符 | 仅两处 `lea` 引用：`0x12BC04`、`0x12BD3F` |

---

# Part 1 — 云/网络计算路径

## 1.1 CloudEngine 类模型

* `vtables.json` 中 `N6Engine11CloudEngineE`：`vtable_rva = 0xA3CED0`，槽 `[0x755000, 0x754FB0, 0x26A60]`。
  实际布局（已从 `0xA3CED0` 起逐 qword 读出）：
  `0xA3CED0 = 0`（offset-to-top），`0xA3CED8 = 0xA19050`（typeinfo），
  **地址点 `0xA3CEE0` = `0x755000`（D1 析构）、`0xA3CEE8` = `0x754FB0`（D0 删除析构）、`0xA3CEF0` = `0x26A60`（`Run`）**。[已证实]
* 结论：`Engine::` 接口只有 **一个** 业务虚函数 `Run`；其余引擎（`MultiEngine`、`NestingEngine`、`DelayedEngine`、`InfiniteEngine`、`CompositeEngine`、`EquivalentEngine`）的 vtable 都是 3 槽，`BestObserver/CompositeObserver/EquivalentObserver` 是 6 槽。CloudEngine 不额外增加虚函数 → 云端引擎的**结果通过 observer/回调**（`std::function`）向外传递，而非虚函数。
* `Utils::ConnectException / ResolveException / TimeoutException / BadResponseException`：
  RTTI `N5Utils16ConnectExceptionE`（名字串 @`0xA229C0`），typeinfo @`0xA183F0`，vtable 地址点 `0xA3BC00`，槽
  `dtor=0x6D3270`、`deleting dtor=0x6D3240`、`what()=0x7D7910`。四个类同构（`0xA3BC00/0xA3BC30/0xA3BC60/0xA3BC90`）。
  **[已证实]** 在 HTTP 请求构造器中，当传输层 `error_code` 非 0 时执行
  `lea rcx,[rcx+0x48] ; call 0x6EC000 ; __cxa_allocate_exception(8) ; vptr=0xA3BC00 ; __cxa_throw(obj, 0xA183F0, 0x6D3270)`
  （见 `0x6DA3EE`、`0x6DBFB1`）→ **连接错误抛 `Utils::ConnectException`**。
* `Utils::OstreamSink<NestingSinkModel>`：vtable `0xA3BBA0`，8 槽
  `[0x6C88E0, 0x6C9150, 0x6C9090, 0x1976B0, 0x1980B0, 0x197D90, 0x198530, 0x1977F0]`。
  其中 `0x1976B0/0x1980B0/0x197D90/0x198530/0x1977F0` 位于 app 代码段（BAB0），
  `0x6C88E0/0x6C9150/0x6C9090` 位于 UPX1。**[推断]** 它把云端返回的解序列化结果以「文本流」形式喂给 nesting 观察者。

## 1.2 本地 vs 云 的决策（`cns_force_cloud`）

`LaunchLocalComputation`（`0x2AB0`）开头即做决策：

```
0x2ACB  call 0x1BF00            ; bool IsForceCloud()
0x2AD0  test al, al
0x2AD2  jne  0x31C9             ; → 走云端
...
0x31C9  lea  r8,  "cns_force_cloud"                   ; 选项/键名
0x31D0  movq xmm3, r13                                ; 时限(秒)
0x31D5  mov  rcx, rbp                                 ; LaunchingOrder*
0x31D8  lea  rdx,  "cns1.optalog.com;cns2.optalog.com" ; 服务器列表
0x31DF  call 0x6100             ; LaunchComputation(lo, servers, "cns_force_cloud", t)
```

* `0x1BF00` = `return g_cfg->flag[1];`（`0x1BF04 call 0x1BE70` 取全局配置指针，读 `+1` 字节）。**[已证实]**
* `0x1BE70` = 用 `__cxa_guard_acquire/release`（`0x998DA0/0x998EE0`）保护的单例配置初始化器，
  内部调用 `0x65A530`（见 §1.7 日志初始化）后才返回 `0xB1F398` 处的配置对象。**[已证实]**
  因此 `0x1BF00` 的语义是 **[推断]**：*“全局选项/配置里 `cns_force_cloud` 被打开”* → 强制走云。
* `0x1BF20`（`LaunchComputation` 的守卫）= `if (0xB5D60()) return true; else return cfg->flag[2];`
  而 `0xB5D60` 是 **`xor eax,eax; ret`（恒 false）** → 实际等价于 `cfg->flag[2]`。**[已证实]**
  文件级实测：`0x3310`/`0x3360` 的 `LaunchLimited/EstimateLocalComputation` 也都最终调用 `0x2AB0`，
  即 **所有三个 “Local” 入口都可能被重定向为云端计算**。

`LaunchComputation`（`0x6100`）签名 **[推断]**：
`LaunchComputation(LaunchingOrder* lo /*rcx*/, const char* servers /*rdx*/, const char* optionName /*r8*/, double timeLimit /*xmm3*/)`
（入参在 `0x6113/0x6126/0x6132` 被保存，随后 `0x64DAC0("LaunchComputation", servers, optionName, time)` 记日志）。

`LaunchLimitedLocalComputation`（`0x3310`）**[已证实]**：
```
esi = lo->dword[0x1F8];  lo->dword[0x1F8] = 1;      ; 临时把“something”设为 1
xmm1 = const double @0x9AC350
call 0x2AB0 (LaunchLocalComputation)
lo->dword[0x1F8] = esi;                            ; 还原
```
`LaunchEstimateLocalComputation`（`0x3360`）**[已证实]**：`lo->byte[0x288] = 1; jmp 0x2AB0`（估算模式标志）。

## 1.3 HTTP 协议（boost::asio 客户端）

### 请求文本（逐字节证实）

GET（`0x6DA1F0`，目标为 `boost::asio::streambuf/ostream`，`rsi` = 会话对象）：

```
GET <path>          ; path = std::string @ [rsi+0x28]/[rsi+0x30]
 HTTP/1.1\r\n
Host: <host>\r\n    ; host = std::string @ [rsi]     / [rsi+8]
Accept: */*\r\n
Connection: close\r\n
\r\n
```

PUT（`0x6DBD40`）：

```
PUT <path> HTTP/1.1\r\n
Host: <host>\r\n
Accept: */*\r\n
Content-Length: <N>\r\n          ; N = [rsi+0x50]，body 指针 = [rsi+0x48]
Content-Type: text/plain\r\n
Connection: close\r\n
\r\n
<body>
```

（`"\r\n"` 常量位于 `0x9AEB90`；`"Accept: */*"`@`0x9AEBB8`、`"Host: "`@`0x9AEBB1`、`"PUT "`@`0x9AEBDC`、
`"Content-Length: "`@`0x9AEBE1`、`"Content-Type: text/plain"`@`0x9AEBF2`、`"Connection: close"`@`0x9AEB C6/0x9AEC0D`。）

执行层：`0x2AF30`（GET）/`0x2B660`（PUT）为 asio 客户端主体；包装层 `0x2B630`/`0x2BD20` 把
**端口常量 `0x50` = 80** 放入 `edx`、时限放入 `xmm3` 后转发。**[已证实]**
具体超时/重试见 §1.5。响应侧 `0x6DAB80`/`0x6DC480` 解析状态行（`" HTTP/1.1"`、`"HTTP/"`），
并且 **调用 `nanosleep`（thunk `0x63F728`）**，即读循环里带睡眠退避。**[已证实]**

### URL 路径与 payload 语义

在 `CloudEngine::Run`（`0x26A60`）内：

* **提交问题**：`0x27924`–`0x27949` 用 `std::string::_M_construct`（`0x26780`）构造 `"/pb/"`，
  再 `append`（`0x910A60`）一个 16 进制/UUID 字符串（`[rsp+0x180]`=ptr,`[rsp+0x188]`=len）。
  `0x26780` 的签名是 `(std::string*, char* first, char* last)`，故 `r8 = 0x9AE83B = "/pb/"+4`。
  日志 `"PUT on " <url> " problem of size " <n>`（`0x279EC/0x27A28`），
  随后 `0x27A6B call 0x2BD20` 执行 PUT，成功后打印 `"PUT done in " <t> " sec."`。
  → **`PUT /pb/<id>`，body = 序列化的问题**。**[已证实]**
* **取解**：`0x28952` `rax = "/sol/"`，`rbx = "/best_sol/"`，
  `cmove rbx, rax` 由 `0x2893F` 的比较结果决定：`0x82A3E0(body, "end")`。
  → **响应体等于 `"end"` 时用 `/sol/`，否则用 `/best_sol/`**。**[已证实]**
* **payload 种类**：`0x28E44` `rax="final"`、`0x28E58` `rbx="intermediate"`，
  `test r9d,[rsp+0x98]; cmove rbx, rax`，日志 `"Found solution " <label>`；
  `r9d` 正是上面「body 是否等于 `end`」的结果（`0x28946` 存入 `[rsp+0x98]`）。
  → **`"intermediate"`（body == "end"）↔ `/sol/`；`"final"`（body != "end"）↔ `/best_sol/`**。**[已证实]**
* 服务器名 `cns1.optalog.com;cns2.optalog.com`（`0x9AC150`）以**单个分号分隔的字符串**传入
  `LaunchComputation` 的 `rdx`；**[推断]** 由 asio 端的 host 解析器拆成候选列表并失败切换（`Utils::ResolveException` 的存在印证解析分支）。
* 其它日志串：`"Launching cloud engine "`+`"sec."`（`0x9AE803/0x9AE81B`）、
  `"GET done (response size = "`+`") in "`+`" sec."`（`0x9AE86A/0x9AE885`）、`"ERROR: "`（`0x9AE88D`）、
  `"CloudEngine::Run "`+`" vs "`（`0x9AE8DF/0x9AE8F1`）。

### 请求 ID / 随机数

`CloudEngine::Run` 开头（`0x26ADC`–`0x26E13`）：
* `CryptAcquireContextW`（新 IAT 槽 `0xB28904`）以 `(phProv, NULL, NULL, PROV_RSA_FULL=1, 0xF0000040=CRYPT_VERIFYCONTEXT|CRYPT_SILENT)` 调用，**唯一调用点 `0x26BE4`**；`CryptReleaseContext` 于 `0x278CD`、`0x2A35F`。**[已证实]**
* `new(0x9C8)` 出一个 2504 字节对象，`dword[0]=0x1571`（=5489，MT19937 默认种子）并做标准
  `* 0x6C078965` 递推展开 624 个状态字；随后用 `0x6FD230`（`std::mt19937::operator()` 风格）生成
  **16 字节 UUIDv4**：写 `[rsp+0x130..0x13F]`，并做
  `byte[0x136] = (byte[0x136] & 0x4F) | 0x40`（版本 4）、`byte[0x138] = (byte[0x138] & 0xBF) | 0x80`（variant 10xx）。
  → **计算请求 ID = 随机 UUIDv4**。**[已证实]**

## 1.4 序列化

* **问题序列化**：`LaunchingOrder` → `Json::Value` 由 `0x1EE50`（`__func__ = "CreateProblem"`）完成；
  `0xB8D0`（引用自身名 `"GenerateLaunchingOrderProblem"` 与键名 `"source_version"`）输出
  `{"source_version": <版本串>, ...}`。**[已证实键名；函数归属为推断]**
* **落盘**：`0x2C69`（`LaunchLocalComputation`）与 `0x6230`（`LaunchComputation`）都做
  `0x87D590(stream, "c:\\Temp\\cns.pb.json", 0x30)` → 建 `std::ofstream`；
  随后 `0x5070E0(ostream, &JsonValue)`、`0x5007C0` 释放；**这两个分支都在
  `0x1BF40()`（debug 日志 sink）非空时才执行**，即 `c:\Temp\cns.pb.json` 是「调试用」的问题转储。
  **[已证实]**（`cns.pb.json` 串位于 `0x9AC189` 与 `0x9AC3A4`）
* **解序列化**：`UnSerializeSolution` = **`0x1C5F0`**（454 B / 119 insn），自身引用
  `"UnSerializeSolution"`、`"solution.Bindable(problem)"`、`"internal.cpp"`。**[已证实]**
  调用点在 `CloudEngine::Run` `0x2918B` 前后：先用 `0x26780` 拼 `"UnSerializeSolution"` 与
  `"..\engine\cloud_engine.cpp"`，再以 `0x60A620(file, line=0x3D=61, expr, ...)` 抛断言/异常
  → **`Assert(UnSerializeSolution(...))` @ `..\engine\cloud_engine.cpp:61`** **[推断，行号已证实]**
* 另有断言串 `"solution.Bindable(problem)"`（`0x9AE8A9`）。**[已证实]**

## 1.5 超时 / 重试

| 位置 | 值 | 含义 |
|---|---|---|
| `0x9AE9B0` = double **120.0** | `CloudEngine::Run` `0x27A5F` `movsd xmm6` → 作为 `xmm3` 传给 `0x2BD20`（PUT） | 单次 HTTP PUT 超时 **120 s** **[已证实]** |
| `0x9AE9B8` = double **30.0** | `0x27BEA/0x27C4B`：`xmm1 = 2*t + 30.0`，`ucomisd elapsed, xmm1`/`jbe` | 轮询/整体截止 = **2×时限 + 30 s** **[已证实]** |
| `0x4A817C800` = **20 000 000 000** | `0x27F25` `movabs rdx` 加到 `0x8A8160()`（高精度时钟，ns）上，`0x27F45 cmp/jl 0x28538` | GET 轮询窗口 **20 s**（超窗后重新发起）**[已证实]** |
| `0x9AC3E8` = **1.0**，`0x9AC3F0` = **5.0** | `LaunchComputation` `0x630C`–`0x6329`：`xmm6 = t - 5.0; maxsd xmm2, 1.0` | 提交给引擎的时限 = **max(t−5, 1.0)** **[已证实]** |
| `0x989680` = 10 000 000 ns | `0x1E70` `0x2297`：`nanosleep({0,10ms})`（`0x63F728`） | 本地启动/许可等待轮询 **10 ms** **[已证实]** |
| 响应读循环内含 `nanosleep` | `0x6DAB80`/`0x6DC480` 调用 `0x63F728` | 读失败 → 睡眠后重试 **[已证实调用，退避时长未确认]** |
| 字符串 `"timeout "` | `0x9AE9C0` | 超时日志/异常文本 **[已证实]** |

四个异常类的存在（`Connect/Resolve/Timeout/BadResponse`）与上述常量一致：连接失败、DNS 解析失败、超时、响应非法各有一类。**[推断]**

## 1.6 线程 / 观察者模型

* `0x1E70`（本地调度）在 `0x2125`–`0x21B8` 打印
  `"Launching local engines " <nMulti> " threads for multi," <nNest> " threads for nesting, " <maxIter> " max iterations."`
  （串 `0x9AC0D3/0x9AC0EC/0x9AC100/0x9AC117`）；线程数来自 `lo`（`SetLocalEngineThreads` / `SetLocalMaximumThreads` /
  `SetLocalMaximumIterations`，导出 `0xDE80/0xD3B0/0xD400`）。**[已证实字符串与位置，字段偏移未逐一确认]**
* `0x1E70` 用 `operator new(8)+refcount(lock add [rsi+8],1)` 构造 `std::function` 风格的
  引用计数闭包（`0x1F33`–`0x1F94`，vtable 常量 `0xA542D0`），交给 `0x8AB0A0`（线程池/任务提交）。
  `AsyncCancelAllComputationsAndDeleteLaunchingOrder`（`0xB540`）用同样手法（vtable `0xA542A0`）提交一个
  「取消全部并删除订单」任务，然后 `0x8AB160` 等待，`0x990E80` 取异常，循环 `operator delete`。**[已证实]**
* 云端侧：`CloudEngine::Run` 全程在 **同步** 循环里 PUT/GET（无 asio 异步回调链的证据），
  结果通过 `Utils::OstreamSink<NestingSinkModel>`（vtable `0xA3BBA0`）输出。**[推断]**
* `[r13+0x50]`（`r13` = `Run` 的第 2 参数对象）是一个 **verbose/trace 开关**，
  在 `Run` 中被 `cmp byte ptr [r13+0x50],0` 检查 ≥15 次，控制 `"PUT on …"` / `"GET done …"` / `"Found solution …"` 等日志。**[已证实]**

## 1.7 日志与调试文件（`dbg::` sinks）

* **debug sink 工厂 `0x1BF40`**（被 80+ 个导出调用）**[已证实]**：
  1. `0x1BE70()` 取全局配置；`cfg->byte[0] == 0` → 返回 `NULL`（日志关闭）；
  2. 否则用 guard（`0xB1F1A0`，`__cxa_guard_acquire/release` = `0x998DA0/0x998EE0`）**惰性**执行
     `0x7BB430(&sink@0xB1F1C0, "c:\\Temp\\debug_nest.txt")`；
  3. 返回 `&0xB1F1C0`（或 `NULL`，若 `dword[0xB1F2A8] != 0`）。
  → **`c:\Temp\debug_nest.txt` 仅在配置开关打开时创建**。
* `0x7BB430`（129 insn，引用 **`"CNS informations"`**@`0x9ADD2C` 与 `0xB81F0`）是 **sink 构造函数**：
  它把 `"CNS informations"` 头 + 许可证类型写进文本 sink。**[已证实引用；语义为推断]**
* `0x65A530`（126 insn）引用 **`c:\Temp\log_nest.txt` / `c:\Temp\cloud_nest.txt` / `c:\Temp\local_nest.txt`**
  三条路径 → **[推断]** 它是「日志后端选择器」，按全局开关把 `dbg::` sink 绑定到
  总日志 / 云日志 / 本地日志之一。它被 `0x1BE70`（配置单例初始化）调用，故所有日志配置都在首次访问时确定。**[已证实调用关系]**
* 报告文件：`WaitComputationTermination`（`0x104D0`）与 `WaitNextSolution`（`0x10650`）都引用
  `c:\Temp\computation_solution.html`（`0x9AD2D8`）；`0x5190B0` 是 HTML 报告生成器，引用
  `cns_solution.css` / `../cns_solution.css` / `../../cns_solution.css`（`0x9DB887/0x9DB873/0x9DB85C`）。
  `c:\Temp\computation_solution.h` 未在字符串表中找到 **[未确认]**（可能由 `.html`/`.css` 拼接或已被优化掉）。
* 其他：`0x2EC50` `"Generating c:\Temp\internal_output.dxf"`；`0x5ED40/0x5F030`
  `c:\Temp\Traces\solution_` / `c:\Temp\Traces\nesting_`。**[已证实]**
* 日志/trace 的实现基类：RTTI `dbg::symlog`（vtable `0xA3B240`，3 槽，槽 2 = `0x60B330`）、
  `dbg::file_error`（`0xA3B210`）。**每个函数入口用 `0x64AEA0(name)` 之类登记 `__func__`**，
  这就是 BRIEF 中「靠 `__func__` 还原名字」的机制。**[已证实]**
* 许可类型常量：`0xB81F0` = `mov eax,0x64; ret`（**硬编码返回 100**）。
  由此 `0xB5A40/0xB5A60/0xB5A80/0xB5AA0/0xB5AD0/0xB5D70/0xB5910/0xB61A0` 这些「版本/版本特性」判定
  （比较值 300/1100/3000/100000/100100/1200/2300/600/1400/1300/0）在本构建中 **全部返回 false**。**[已证实]**

## 1.8 导出函数流程

* `LaunchComputation`/`LaunchLocalComputation`（`0x6100`/`0x2AB0`）：
  1. `0x1BF20`/`0x1BF00` 守卫（见 §1.2）；
  2. 可选写 `c:\Temp\cns.pb.json`（debug sink 非空时）；
  3. `new(0x1C8)` + `0x22E30(obj, lo, time, isLocal)`（`0x22E30` 只是 `movzx r9d,r9b; jmp 0x22A20`）
     → **[推断]** 构造引擎/计算上下文，`r9d = 1` 为本地、`0` 为云；
  4. 把新对象追加进 `lo->vector<Engine*>`（begin/end/cap = `lo+0x1C8/0x1D0/0x1D8`，`0x8F9220` 为插入）；
  5. `0x1E70(lo, obj)` 做授权与本地调度；
  6. **返回值为新对象（rax = rdi）**。
* `GetComputationStatus`（`0x107E0`）`rcx` = 该计算对象：
  `[rcx+0x48]` 非 0 → 串 `"Local"`（`0x9AD293`），为 0 → `"Cloud"`（`0x9AD299`）；
  然后 `0x1BE20(rcx)` 取状态码并记日志返回。`CancelComputation`（`0x10880`）→ `0x1BE30(rcx)`；
  `TerminateComputation`（`0x10920`）→ **[推断]** `0x1BE40/0x1BE50` 同类访问器（同构代码，引用 `"TerminateComputation "`）。
* `WaitComputationTermination`（`0x104D0`）、`WaitNextSolution`（`0x10650`）：
  引用 `c:\Temp\computation_solution.html`，调用 `0x1BF40`（debug sink）→ **等待时可选导出 HTML 报告**。**[已证实引用]**
* `AsyncCancelAllComputationsAndDeleteLaunchingOrder`（`0xB540`）：见 §1.6，投递异步任务后等待并释放。**[已证实]**

---

# Part 2 — 授权 / 反篡改 / 机器绑定

## 2.1 导入表真相（重要更正）

转储把**原始 thunk 数组写进了 `FirstThunk` 字段并把 `OriginalFirstThunk` 清零**，
但 `.rsrc` 中残留的 **原始按名 thunk 表 + hint/name 表**仍完好（`0xB42328`–`0xB424D8`）：

```
0xB42430: "LoadLibraryA\0GetProcAddress\0VirtualProtect\0VirtualAlloc\0VirtualFree\0"
0xB4247A: "CryptGenRandom\0GetAdaptersInfo\0nanosleep\0acos\0GetProcessMemoryInfo\0MessageBoxA\0bind\0"
```

8 个导入 DLL：`KERNEL32.DLL, ADVAPI32.dll, IPHLPAPI.DLL, libwinpthread-1.dll, msvcrt.dll, PSAPI.DLL, USER32.dll, WS2_32.dll`。
→ **全库只有 12 个导入函数**：KERNEL32 5 个（LoadLibraryA/GetProcAddress/VirtualProtect/VirtualAlloc/VirtualFree）、
每个其余 DLL 各 1 个（正是 BRIEF 列出的那 7 个）。**[已证实]**

代码真正使用的 **活 IAT** 在 `0xB288FC` 起（8 字节步长、基准 ≡4 mod 8），按 DLL 分成 8 段：

| DLL | 活 IAT 范围 | 条目数 |
|---|---|---|
| ADVAPI32 | `0xB288FC`–`0xB28914` | 4 |
| IPHLPAPI | `0xB28924` | 1 |
| KERNEL32 | `0xB28934`–`0xB28C04` | 91 |
| msvcrt | `0xB28C14`–`0xB28FA4` | 115 |
| PSAPI | `0xB28FB4` | 1 |
| libwinpthread-1 | `0xB28FC4`–`0xB29054` | 19 |
| USER32 | `0xB29064` | 1 |
| WS2_32 | `0xB29074`–`0xB29134` | 25 |

**[已证实]**（`load_prof` + `data_refs` 定位 + 槽值分类）
各 DLL 导入的具体函数名由 **链接器 thunk（`jmp qword ptr [rip+…]`）** 转发，已定位：

| 导入 | 转发 thunk | 调用者 |
|---|---|---|
| `GetAdaptersInfo` | `0x61F000` | **仅 `0x24290`（GetPCId 的 worker）** |
| `GetProcessMemoryInfo` | `0x61EFF0` | `0x57D780`、`0x57D7B0` |
| `MessageBoxA` | `0x63F760` / `0x60B070` | **[未确认]**（未发现 `call` 站点） |
| `bind` | `0x61F070` | `0x6F5DF0`、`0x6F77E0`（WS2_32 初始化） |
| `nanosleep` | `0x63F728` | `0x1E70, 0x5B00, 0x26A60, 0x5F3990, 0x6DAB80, 0x756EC0, 0x876170, 0x9993F2` |
| `acos` | `0x63F418` | `0x5EC670`、`0x5ECD90`（几何） |
| `LoadLibraryA` | `0xB28AB4`（KERNEL32 段） | `0x12BBA0`、`0x12BCC0`（HASP 加载） |
| `GetProcAddress` | `0xB28A5C` | 同上 |
| `GetVolumeInformationA` | `0xB28A84` | `0x24290`（`0x24390`）|

## 2.2 `GetPCId`（导出，RVA `0xC010`）

```
0xC016  lea rcx,"GetPCId" ; call 0x64AEA0            ; trace 登记
0xC022  if (g_once@0xB1F080)  return g_str@0xB1F0A0 ; 缓存命中，直接返回字符串首地址
0xC040  __cxa_guard_acquire(0xB1F080)
0xC065  g_str = std::string("")                      ; 初始化静态 std::string @0xB1F0A0
0xC070  call 0x24290                                 ; eax = PCId 数值
0xC07E  r8d = 0x10 ; r9 = "%ld" ; rdx = 0xAB00 ; rcx = 栈缓冲
0xC095  call 0xAC90                                  ; 生成十进制字符串
0xC101  __cxa_guard_release
0xC119  return [0xB1F0A0]                            ; 返回 std::string 的数据指针
```

* **[已证实]** `"%ld"` 常量在 `0x9AC88A`，`GetPCId` 返回的是**静态 `std::string` 的 `data()`/`c_str()`**
  （函数体没有 sret 写入，`rcx` 被覆盖用作日志参数）→ **[推断]** 签名是 `const char* GetPCId()`（缓存字符串），
  不是按值返回 `std::string`。
* **worker `0x24290`（219 insn）——机器指纹算法 [已证实]**：

```
0x2429D  malloc(0x2C0); [rsp+0x44] = 8               ; ULONG cbBuffer = 8 (8 字节不够 → 触发重试)
0x242CE  GetAdaptersInfo(buf, &cbBuffer)
0x242D3  if (rcx == 0x6F /*ERROR_NO_DATA*/) goto 0x243D0
0x242DC  GetAdaptersInfo(buf, &cbBuffer)             ; 第二次调用（重试）
0x242E7  if (eax != 0) { mac = 0 } else {
0x242EF     mac48 = big-endian 48-bit from buf[0x198..0x19D]   ; IP_ADAPTER_INFO.Address[0..5] = 首块网卡 MAC
0x24342     ebp = (mac48 >> 16)
         }
0x24349  free(buf);  ebp += (uint32)mac48
0x24363  rcx = "c:\\"                                 ; 常量 @0x9AE2F0
0x24390  call [0xB28A84] = GetVolumeInformationA("c:\\", NULL, 0, &serial@[rsp+0x90], NULL,NULL,NULL, 0)
0x24396  eax = serial (C: 卷序列号)
0x2439D  ebp += serial
0x2439F  eax *= (uint32)mac48
0x243A2  eax += ebp
0x243A4  eax ^= 0xABADCAFE                            ; 混淆常量
0x243A6  return eax
```

  → **`PCId = ((mac48 * serial) + (mac48 >> 16) + mac48 + serial) ^ 0xABADCAFE`**（全部 32 位运算）。
  输入只有两个：**首块网卡的 6 字节 MAC（经 `GetAdaptersInfo`）** 与 **`C:` 卷序列号（经 `GetVolumeInformationA`）**。
  **没有** CPU id、没有 `CryptGenRandom`、没有 `GetProcessMemoryInfo` 参与。**[已证实]**
* `0x243D0` 分支：`free` 后用 `GetAdaptersInfo` 回写的所需长度重新 `malloc` 再重试（`0x242DC`）；
  若仍失败，用内联 `movabs` 拼出 **源文件名 `..\utils\pcid_win.cpp`**（`0x244A6`–`0x244CB`）与
  **`"GetMACAddress"` / `"adapter_info"`**（`0x2440C`–`0x2445F`），再调用 `0x60A620(file, line=0x24/0x1D, …)`
  → **断言/抛异常**。**[已证实]**
* `0x24290` 的调用者：`0xC010`（GetPCId）与 `0x1780`（[推断] 某个全局初始化）。**[已证实]**

## 2.3 三个 `UnLockLaunchingOrder*` 变体

三个函数（`0xE180`/`0xE1F0`/`0xE260`）**机器码除日志字符串外完全相同**（111 字节，逐字节比对）：

```
UnLockXxx(LaunchingOrder* lo /*rcx*/, const char* a /*rdx*/, const char* b /*r8*/):
    trace("UnLockLaunchingOrderSntl|Oxy|PCId")
    r = strlen(a)                                  ; 0x63F238
    std::string::_M_replace(lo+0x248, 0, lo[0x250], a, r)   ; 0x90ECB0
    r = strlen(b)
    std::string::_M_replace(lo+0x268, 0, lo[0x270], b, r)
```

* **[已证实]**：`LaunchingOrder` 布局 = `+0x244 : int32`、`+0x248 : std::string`、`+0x268 : std::string`。
* `UnLockLaunchingOrder`（`0xD430`，导出 76/77）与它们**不同**：签名 `(lo, int)`，只有一句
  `mov dword ptr [rsi + 0x244], ebx` → **`lo->unlockMode = mode`**。**[已证实]**
* 三个变体都写**同样的两个字段**，仅日志名不同；因此 **[推断]** 它们对应三种授权来源
  （Sentinel 加密狗 / OxySec 加密狗 / PC-Id 在线授权），
  调用者用哪个变体即声明「本 key 属于哪种来源」；**判别与校验逻辑不在导出函数里，而在 `0x1E70`（见 §2.4）**。
  注意：`UnLockLaunchingOrder` 自身不写 key 字符串，只写 mode。

## 2.4 授权闸门：`0x1E70`（本地调度器）

`0x1E70(LaunchingOrder* lo /*rcx*/, Engine/Context* ctx /*rdx*/)`，由 `0x2AB0` 与 `0x6100` 调用。**[已证实]**

```
0x1E8B  if (lo->byte[0x288]) ctx->byte[0x1C0] = 1     ; 估算模式
0x1EB7  if (!0x1C7C0(lo, ctx)) return                 ; “订单合法性”检查
0x1EE0  trace("Order valid")
0x1EEC  if (ctx->byte[0x48] == 0) …                   ; 0x48 = isLocal（0 → 云，1 → 本地）
0x1EFF  trace("Start")
0x1F15  … 构造并投递本地引擎任务（见 §1.6）
0x2290  nanosleep({0,10ms}) 轮询
0x2335  r13 = lo->string[0x248].data ; rbp = lo->string[0x248].size
0x23AA  trace("Keys: ", lo->dword[0x244], " - ", string@0x248, string@0x268)   ; 0x64E710 格式化日志
0x23EC  if ( 0xB5A40() )  goto 0x2482     ; 版本判定（本构建恒 false）
0x23F9  if ( 0xB5A60() )  goto 0x2420
0x2402  if ( 0xB5AA0() )  goto 0x2430
0x240B  ctx->dword[0x4C] = 0x0B (11);  return          ; ← 未授权退出码 11
0x2420  if ( 0x12B580(&lo->string[0x248]) ) goto 0x2402 ; OxySec/HASP 单键校验
        else ctx->dword[0x4C] = 0x11 (17); return
0x2430  ctx->dword[0x4C] = 0x11 (17); return            ; ← 未授权退出码 17
0x2482  if ( lo->string[0x248] == "X" ) goto 0x23F9     ; 常量 @0x9AC040 = "X"
0x24A0  if ( 0x12C980(&lo->string[0x248]) ) goto 0x23F9 ; Sentinel Admin 单键校验
        else goto 0x2430
```

后续（`0x276B`/`0x28E2`/`0x28FA` 等）：
* `0x14E0(lo->dword[0x244])`：按 **unlock mode**（`UnLockLaunchingOrder` 写入）分支；
* `0x12B5F0(vector<string>&, …)` + `0x12CB40(vector<string>&)`：**枚举加密狗/授权里的 key 列表**；
* `0x9993B0` / `0x9993F2`：`std::string` 比较；
* `0xB5EC0(a, b)`：列表元素与订单 key 的匹配器；
* `0xB61A0(double)`：`licenseType == 0x44C (1100)` 且 `阈值 > t` 的时间型限制（本构建 `0xB81F0` 恒为 100，故恒 false）。

* **[已证实]**：`ctx->dword[0x4C]` 是**启动结果/状态码**：成功路径写 `9`（`0x200C`），
  授权失败写 `0x0B`(11) 或 `0x11`(17)。`GetComputationStatus`/`CancelComputation` 读同一对象的
  `[+0x48]`（Local/Cloud）与状态码。
* **[已证实]**：授权键来自 `LaunchingOrder+0x248` / `+0x268`，由 §2.3 的导出写入；
  校验方式是把它们与 **加密狗 API 枚举出的 key 列表** 比对（`0x12B5F0` = OxySec/HASP 侧，
  `0x12CB40` = Sentinel Admin 侧）。**DLL 自身不做密码学验签**（见 §2.6）。

## 2.5 HASP / Sentinel 加密狗层

`0x12BBA0`（写）与 `0x12BCC0`（读）—— **[已证实]**：

```
0x12BBA0 (写 dongle):
  h = LoadLibraryA([rcx])                  ; rcx = std::string* , 取 [rcx] 作 DLL 名
  if (!h) return false
  pLogin  = GetProcAddress(h, "hasp_login")   ; 0x9BCC94
  pLogout = GetProcAddress(h, "hasp_logout")  ; 0x9BCC9F
  pWrite  = GetProcAddress(h, "hasp_write")   ; 0x9BCCAB
  pLogin(0 /*feature id*/, "r75pt0RaGrw…"/*Vendor Code @0x9A2080*/, &handle@[rsp+0x3C])
  buf = new(0x90); memset(buf,0,0x90)
  for i in 0..0x80: buf[0x10+i] = (i < s.size() ? s[i] : 0x20)   ; 128 字节，空格填充
  ok = (pWrite(handle, 0xFFF4 /*file id*/, 0 /*offset*/, buf, 0x90) == 0)
  pLogout(handle); FreeLibrary(h); delete buf; return ok

0x12BCC0 (读 dongle):
  同上取 hasp_login / hasp_logout / hasp_read(0x9BCCB6)
  pLogin(0, "r75pt0RaGrw…", &handle)
  pRead(handle, 0xFFF4, 0x10 /*offset=16*/, buf@[rsp+0x60], 0x80 /*len=128*/)
  out = std::string(128, ' '); memcpy(out.data(), buf, 0x80)   ; 返回 128 字节
  pLogout; FreeLibrary
```

* **DLL 名（内联 `movabs` 拼接）**：
  `0x12ADFA` 一带 = `"hasp_windows_x64.dll"`（16 字符，见 `0x12D2F8` 的 `hasp_win`+`dows_x64`）；
  **[推断]** 由 `0x12ADB0` 函数拼出（其中还内联了 **源文件路径含 `OxySec`**，见 `0x12B190`）。
* Sentinel Admin API：`0x12C1A0` 一带内联 `"sntl_adm"`+…，长度 `0x1D = 29`
  → **`"sntl_adminapi_windows_x64.dll"`**（**[推断]**，长度吻合）；
  其函数名位于 `0x9BCB50`：`sntl_admin_context_new`、`sntl_admin_get`、`sntl_admin_free`、`sntl_admin_context_delete`。
* 其他：`0x12B607/0x12B677` 内联常量含 `haspid` / `<haspid>`（HASP 的 XML 查询，`hasp_get_info`/`hasp_get_rtc` 一类）。**[已证实字节]**
* **[推断]** `0x12B580` = 「用 `lo->key@0x248` 打开 OxySec/HASP 授权并校验」；`0x12C980` = 对应的 Sentinel Admin 版本；
  `0x12CB40` / `0x12B5F0` = 枚举 key 列表。**未逐条反编译确认，标为 [推断]**。

## 2.6 CryptoPP 的使用情况（**关键否定结论**）

* 静态链接的 CryptoPP **整体**都在文件里：`vtables.json` 中 `N8CryptoPP*` 类 RTTI 覆盖面极广——
  RSA（`PKCS1v15`/`PSS` + `SHA-1`、`OAEP`）、DSA+`SHA1`、ECDSA（`ECP`/`EC2N`）+`SHA-256`、
  DES / DES-EDE2 / DES-EDE3 / DES_XEX3 / Rijndael(AES) / SKIPJACK、`HMAC<SHA1>`、
  `HexEncoder`、Base64 编解码、PKCS#8/X509、ASN.1（`BERGeneralDecoder`/`BEREncoder`）等。
  算法名常量亦在 rodata：`"SHA-256"``0x9B44A2`、`"SHA-1"``0x9B44E0`、`"AES"``0x9B44CB`、`"DES-EDE3"``0x9B44D7`、`"DSA/"``0x9B44E6`、`"HMAC("``0x9B468B` 等。
  → **这些都是 `libcrypto++` 的全量 RTTI/名称表，不能作为「被使用」的证据。**
* 我检查过的**授权/指纹代码路径全部没有调用 CryptoPP**：
  * `0x24290`（GetPCId worker）callees = `0x60A620, 0x61F000(GetAdaptersInfo), 0x62F280, 0x63F310, 0x63F390, 0x910BA0, 0x9984B0` —— 无 CryptoPP；
  * `0x12BBA0` callees = `0x62F280, 0x9984B0, 0x998500` —— 无 CryptoPP；
  * `0x12BCC0` callees = `0x12BDCE, 0x62F280, 0x90EFA0, 0x910AF0, 0x9984B0` —— 无 CryptoPP；
  * `UnSerializeSolution`（`0x1C5F0`）只引用 `internal.cpp` / `solution.Bindable(problem)`。
* **结论**：CryptoPP 被静态链接（Boost/其它模块或未使用的模板实例带入），
  但在**授权校验路径上没有可证实的调用点**；许可验证被**委托给 Sentinel LDK 运行库（`hasp_*`）与 Sentinel Admin API（`sntl_admin_*`）**，
  DLL 自身仅做「字符串比对 + 枚举」。**若 CryptoPP 在授权中被使用，我只在由 CryptoPP 自身代码引用的 vtable 里见到痕迹
  （如 `0xCB7B0` 引用 RSA PKCS1v15/SHA1 的 `TF_VerifierImpl`），无法证明那是 app 层调用** → 标 **[未确认]**。

## 2.7 RVA `0x9A2080` 的 base64 blob —— **它就是 HASP Vendor Code**

* 原始形态：**984 个 base64 字符**（`A–Z a–z 0–9 + / =`，无换行），末尾为 `...+IbVgw==`。
  base64 解码后 **736 字节**，字节熵 **7.688 bit/byte**（近均匀），
  首 16 字节 `AF BE 69 B7 44 5A 1A BC 1C 99 56 C0 02 CC AE 49`，
  **不以 `0x30` 开头 → 不是 DER/X.509 证书**，也不是可识别文本 → **密码学随机数据 / 不透明 key blob**。
  解码结果已保存到 `re\blob_9a2080.bin`（736 B）。**[已证实]**
  （BRIEF 中「~1.4 KB」偏大：精确长度是 984 字符 / 736 字节。）
* **引用者（仅两处，均为 `lea rdx,[rip+…]` 后立刻作为 `hasp_login` 的第 2 个参数）[已证实]**：
  * `0x12BC04`（在 `0x12BBA0` 内）→ `0x12BC0E call rdi`（`rdi = hasp_login`）
  * `0x12BD3F`（在 `0x12BCC0` 内）→ `0x12BD46 call r14`（`r14 = hasp_login`）
* **判定：这是 Aladdin/SafeNet Sentinel HASP 的 「Vendor Code」（厂商代码）字符串**，
  由 HASP Vendor Suite 用厂商私钥签名生成、内嵌进产品，供 `hasp_login(featureId=0, vendorCode, &handle)` 使用。
  → **不是** 证书、不是黑名单、不是 DER；是**授权厂商凭据（key material）**。
  它本身是公开不敏感的产品常量（HASP 的安全性依赖厂商私钥，不依赖 Vendor Code 保密）。
* 与它相邻的常量（`0x9A2460/0x9A2470/0x9A2480/0x9A2488`）被 `0x132040/0x132050/0x1321D0/0x1322E0/0x132400/0x16C6E0/0x16C730/0x1A1E30/0x1A1E80` 等函数引用，
  是 blob 之后的普通数据/短串。**[已证实引用，语义未确认]**
* `re\` 目录下的早前假设「`0x9A2080` 无 RIP 引用」应更正为：**有且仅有两处引用，都是 `hasp_login` 的 vendor code 参数**（**[已证实]**，见 `dis\oxy_1.txt` 第 34 行、`dis\oxy_2.txt` 第 40 行）。

---

# 3. 明确未确认 / 未能确定

1. **`c:\Temp\computation_solution.h`**：字符串表中不存在该路径。可能在别处以拼接方式生成，或被内联优化掉 → **[未确认]**。
2. **`MessageBoxA` 的调用点**：转发 thunk `0x63F760`（及 `0x60B070`）未找到 `call` 站点 → **[未确认]** 是否真的被调用（可能只在错误对话框兜底路径，或被数据引用）。
3. **`GetProcessMemoryInfo` 的用途**：仅 `0x57D780/0x57D7B0` 调用，无字符串可佐证；无法判定是「内存监控日志」还是「反调试」→ **[未确认]**。
4. **服务器名分号列表的切换逻辑**：`cns1.optalog.com;cns2.optalog.com` 只有一个字符串常量，未在 asio 层反汇编出具体的 split + failover 代码 → **[推断]** 为「依次尝试」，**切换算法未确认**。
5. **重试次数上限**：只证实时长常量（PUT 120 s、轮询窗口 20 s、`2t+30` 截止、许可轮询 10 ms）；**没有**找到计数器/固定重试次数 → **[未确认]**。
6. **`Utils::TimeoutException` / `BadResponseException` 的抛出点**：只证实了 `ConnectException` 的 `__cxa_throw`（`0x6DA3EE`、`0x6DBFB1`）；另两个类的 vtable 存在（`0xA3BC50/0xA3BC80`）但未定位 `__cxa_throw` 调用点 → **[未确认]**。
7. **`UnLockLaunchingOrderOxy` / `PCId` 与 `Sntl` 的语义差别**：三者机器码相同，差别只在调用者约定的 key 来源与后续 `0x14E0(mode)` 分支；`0x14E0` 的具体 mode 映射（0/1/2 → 哪条校验链）未逐分支确认 → **[部分推断]**。
8. **`0x9AC040` 处的常量 `"X"`**：`0x1E70` 在 `0x2489` 用它和 `lo->key@0x248` 比较，含义未明（可能是「PC-Id 特殊标记」）→ **[未确认]**。
9. **`OxySec` 完整源文件路径**：`0x12ADB0` 内联 `movabs` 拼出 `…\renaud\nest\…\t\OxySec…`，完整字符串未逐字节重建 → **[部分确认]**（含 `OxySec` 已证实）。
10. **`CryptoPP` 是否在授权链路上被使用**：见 §2.6 → **[未确认，倾向「未使用」]**。

---

# 4. 证据文件索引（本次生成）

`re\dis\` 下均为带注释反汇编（格式：`RVA  机器码  助记符  操作数  ; 字符串/目标`）：

| 文件 | 内容 |
|---|---|
| `cloudengine_run.txt` | `CloudEngine::Run`（`0x26A60`，2992 条） |
| `launch_local.txt` / `launch_computation.txt` | `0x2AB0` / `0x6100` |
| `launch_limited_local.txt` / `launch_estimate_local.txt` | `0x3310` / `0x3360` |
| `http_req_get.txt` / `http_req_put.txt` | `0x6DA1F0` / `0x6DBD40` |
| `http_parse_a.txt` / `http_parse_b.txt` | `0x6DAB80` / `0x6DC480` |
| `http_get.txt` / `http_put.txt` / `http_get_impl.txt` / `http_put_impl.txt` | `0x2B630/0x2BD20/0x2AF30/0x2B660` |
| `h_1e70.txt` | 授权闸门 + 本地调度 |
| `h_24290.txt` | GetPCId worker（MAC + 卷序列号） |
| `getpcid.txt` / `unlock_*.txt` | `0xC010` / `0xD430,0xE180,0xE1F0,0xE260` |
| `oxy_1.txt` / `oxy_2.txt` | `0x12BBA0`（hasp_write）/ `0x12BCC0`（hasp_read） |
| `oxy_5.txt` / `sntl_1.txt` | `0x12ADB0`（含 `OxySec` 路径）/ `0x12C180` 区域 |
| `get_computation_status.txt` / `cancel_computation.txt` / `async_cancel_all.txt` | 状态/取消导出 |
| `order_valid.txt` / `opt_*.txt` / `lic_type.txt` | 订单校验与版本判定 |
| `logging_setup.txt` / `cns_infos.txt` | `0x65A530` / `0x7BB430` 日志后端 |
| `blob_9a2080.bin` | base64 blob 解码结果（736 B） |

辅助脚本：`re\libfix.py`（Python 3.14 兼容 shim）、`re\cl_util.py`、`re\dumputil.py`、`re\dump1.py`、`re\dump2.py`。
