# 第三方库：**下载并直接引用**，不逆向

人类指示（goal round 2）：*"如果是用的第三方库，下载并直接引用第三方库就好了，不需要把第三方库都逆向了。"*
本文档是该政策的**证据与执行记录**：每个库为什么确定被用到（二进制里的字符串 RVA）、版本证据有多强、
许可是什么、以及工程怎么引用它。

> 一旦某库按此表**已下载并已链接**，它就从"待逆向"清单中**显式排除**（`re/covlib.py::classify()`
> 的三个桶：`third_party` / `toolchain` / `domain`）。**排除必须是有证据的、写在这里的**，不是"看着像库就不管"。

## 1. 清单

| 库 | 版本 | 版本证据强度 | 判定依据（DLL 内字符串） | 许可 | 在 lcns 里干什么 |
|---|---|---|---|---|---|
| **boost** | **1.63.0** | **已证实**（8 条路径串带版本号） | `0x9AE7A0` `...\boost_1_63_0/boost/uuid/sha1.hpp`；**并被证明用到这些头**：`0x9DDCF8` `multiprecision/cpp_int.hpp`、`0x9DC6B8` `cpp_int/checked.hpp`、`0x9DCB68` `cpp_int/divide.hpp`、`0x9DCBE8` `cpp_int/misc.hpp`、`0x9DD768` `multiprecision/rational_adaptor.hpp`、`0x9DD348` `boost/rational.hpp` | Boost Software License 1.0 | 精确算术（**`cpp_int` 大整数 + `rational`/`rational_adaptor`**）+ sha1/uuid（授权与云路径） |
| **COIN-OR Clp** | **1.15.3** | **已证实**（构建路径串带版本号） | `0x9C9E1F` `@C:\Users\renaud\nest\external\clp-1.15.3\Clp\src\ClpSimplexDual.cpp`；`0x9D2D30` `Clp-1.15.3\CoinUtils\src\CoinLpIO.cpp`；外加大片 `clpModel->setSpecialOptions(...)` / `cleanupScaling()` / `smallestElementInCut()` 断言文本 | EPL-2.0 | **LP 求解器**：经 `OsiClpSolverInterface` 驱动（取代 lcns 自研 `Simplex` 兜底） |
| **COIN-OR CoinUtils** | 随 Clp 1.15.3 发行包 | **包内位置已证实**，补丁级未证实 | `0x9D2D30` 的路径把 CoinUtils 放在 `Clp-1.15.3\` 之下 | EPL-2.0 | Osi/Clp 的基础库（本次取 `stable/2.10` 波段） |
| **COIN-OR Osi** | 0.107 波段 | **API 时代证据**，补丁级未证实 | `0x9C31FC` `OsiSolverInterface`；`0x9C31A3` `OsiClpSolverInterface`；`OsiHintDo/OsiForceDo/OsiColCut` | EPL-2.0 | 原库驱动 LP 的接口层（本次取 `stable/0.107` 波段） |
| **JsonCpp** | 1.9.5 | 版本号未证实（仅键名与读写形态） | `re/findings_*.md` 记录的 problem/solution JSON 键与 `Json::Value` 形态 | MIT | problem/solution 的 JSON 序列化 |
| **CryptoPP** | 8.9.0 | 版本号未证实（仅类名） | `0x9B8C98` `CryptoPP: invalid group element`；vtable `N8CryptoPP10HexEncoderE` 等 | Boost Software License 1.0（部分公有领域） | 授权与云路径的哈希/加密 |
| *（工具链）* libstdc++ / MinGW-w64 | 随 CLion 2025.3.3 的 GCC 13.1.0 | — | `[abi:cxx11]` 是 **libstdc++ 的 ABI 标签**，不是 Abseil | GPL+exception / mingw-w64 | C++ 运行时 |

**"API 时代证据"的含义**：字符串证明了**用了这个库与这套 API**（`OsiClpSolverInterface` 就是 Osi→Clp 的桥），
但**没有**给出它自己的版本号；这类条目的版本列是"为可构建性选定的版本"，必须显式标注。
**Clp 与 boost 不属此类**：它们的版本号就在构建路径串里（1.15.3 / 1.63.0），因此按该确切版本构建。

## 2. 获取方式（`fetch.ps1` / `fetch.py`，均可重跑）

网络实测：**普通 Python HTTPS 下载超时，但 `curl.exe` 与 `git` 都能通**，因此：

```powershell
# 归档（78 MB）
curl.exe -L --retry 3 -o third_party\_archives\boost_1_63_0.tar.bz2 `
  https://archives.boost.io/release/1.63.0/source/boost_1_63_0.tar.bz2
# 源码树（浅克隆到 tag）
git clone --depth 1 --branch releases/1.17.10 https://github.com/coin-or/Clp       third_party/src/Clp
git clone --depth 1 --branch releases/0.108.11 https://github.com/coin-or/Osi      third_party/src/Osi
git clone --depth 1 --branch releases/2.11.12 https://github.com/coin-or/CoinUtils third_party/src/CoinUtils
git clone --depth 1 --branch 1.9.5            https://github.com/open-source-parsers/jsoncpp third_party/src/jsoncpp
git clone --depth 1 --branch CRYPTOPP_8_9_0   https://github.com/weidai11/cryptopp  third_party/src/cryptopp
```

或直接 `pwsh third_party\fetch.ps1`（幂等：已存在则跳过）。日志：`third_party/fetch.log`。

目录：

```
third_party/
├─ README.md        本文件
├─ fetch.py         清单 + Python 下载器（含每个库的证据字段）
├─ fetch.ps1        实际使用的 curl/git 下载脚本
├─ fetch.log        下载日志
├─ _archives/       原始归档（boost 1.63.0）
└─ src/             浅克隆的源码树（CoinUtils/Osi/Clp/jsoncpp/cryptopp）
```

## 3. 构建与引用计划

| 步骤 | 内容 | 状态 |
|---|---|---|
| T1 | 第三方库落盘 | 见 §4 |
| T2 | 用 CMake 构建 CoinUtils → Osi → Clp（MinGW，无 Fortran；Coin-OR 的 CMake 可用） | 待做 |
| T3 | `lcns` 新增 `-DLCNS_WITH_CLP=ON`（默认 ON）：编译 `src/lp_clp.cpp`，以 `OsiClpSolverInterface` 实现 `LinearProgram`，**与 `lp::Simplex` 同接口** | ✅ **已完成** |
| T4 | registry：原 `lp.simplex_backend`（`Substituted`）拆成 **`lp.clp_backend`（`Recovered`）** + **`lp.simplex_fallback`（`Substituted`）**，即「真 Clp 是默认、自研单纯形只是可选兜底」 | ✅ **已完成** |
| T5 | boost：`third_party/src/boost_1_63_0` 以 `-isystem` 加入 include 路径（`-DLCNS_WITH_BOOST=ON`，默认 ON），并在 `tests/test_recovered.cpp` 用 `static_assert(BOOST_VERSION == 106300)` 把版本**钉在证据上** | ✅ **已完成**（钩子就位；尚未把某个几何路径改写成 `boost::multiprecision`） |
| T6 | JsonCpp：替换工程自有 JSON 写出器（键名已是恢复值） | **已接线**：`LCNS_WITH_JSONCPP`（默认 ON）从 `src/jsoncpp` 编译成 `lcns_jsoncpp` 并链入 `lcns_nest`；`src/json_bridge.cpp` + `include/lcns/json_backend.hpp` 提供 `available()/write()/parse()/backendName()`；`tests/test_json_backend.cpp` 验证真库已链接、往返恢复形状、与自有写出器**互相可读**。第三方 TU 以 `-w` 编译（**遮蔽说明**：零警告纪律适用于逆向代码，不适用于下载库）。待做余部：把 `io.cpp` 内部写出器完全改为默认走此后端 |
| T7 | CryptoPP：仅在授权/云路径需要；这些路径本身是 `NotReversed`，先只建立链接能力 | **已建立**：`LCNS_WITH_CRYPTOPP`（默认 ON）将 `src/cryptopp/*.cpp`（202 个，排除其自带 test/bench/validat）编成 `lcns_cryptopp` 并链入 `lcns_nest`（`CRYPTOPP_DISABLE_ASM=1`）；`src/crypto_bridge.cpp` + `include/lcns/crypto_backend.hpp` 提供 `available()/backendName()/sha1Hex()`；`tests/test_crypto_backend.cpp` 用**算法定义的已知值**验证 SHA-1（空串、`abc`、1000 字节）。**未逆向任何 CryptoPP 代码**。第三方 TU 以 `-w` 编译（同 T6 的遮蔽说明）|

## 4. 落盘结果与构建进展（每轮更新，**不得留空**）

### 4.1 已下载

| 库 | 位置 | 说明 |
|---|---|---|
| COIN-OR **CoinUtils 2.10.x** | `src/coinutils-2.10/` | 克隆自 `stable/2.10`（带 `configure`）；版本落在 `Clp-1.15.3` 发行包的时代波段 |
| COIN-OR **Osi 0.107.x** | `src/osi-0.107/` | `stable/0.107`；同上 |
| COIN-OR **Clp 1.15.3**（**确切 tag**） | `src/clp-1.15.3/` | `releases/1.15.3`；其 `AC_INIT([Clp],[1.15.3])`、configure 生成的 `CLP_VERSION "1.15.3"` 与二进制里的路径串 `clp-1.15.3` **三方一致** |
| **JsonCpp 1.9.5** | `src/jsoncpp/` | 带 `CMakeLists.txt`，可直接 CMake 构建 |
| **CryptoPP 8.9.0** | `src/cryptopp/` | 含 CMake 支持 |
| **boost 1.63.0** | `_archives/boost_1_63_0.tar.bz2` → 已解包到 `src/boost_1_63_0/` | 78 MB 官方归档；`curl` 可达（Python urllib 会超时）；`BOOST_VERSION == 106300` 已由 `test_recovered` 断言 |

### 4.2 构建路径（已踩通的坑，逐条记录）

本机**没有 autoconf/automake/libtool/make/bash**，只有：
`C:\Program Files\Git\bin\bash.exe`（MSYS2 系）、CLion 的 `mingw32-make.exe` 与 GCC 13.1.0、`cmake`、`ninja`。
因此：

1. **不能用 git 的 tag 树重建 autotools**（无 autoconf）⇒ 改用**带 `configure` 的分支/tag**。
   （`releases/1.15.3` 这个 tag 恰好自带 `configure`，所以 Clp 用的是**确切版本**。）
2. **没有 `make`** ⇒ 在 `_shim/make.exe` 放一份 `mingw32-make.exe`，并把它放到 bash 的 `PATH` 前面。
3. **`make` 认为 `configure` 过期而想重跑 autotools**，其命令行里含未加引号的
   `C:/Program Files/...` ⇒ 报 `C:/Program: No such file or directory`（Error 127）。
   修法：`touch` 源码树里所有生成物（`configure`/`Makefile.in`/`aclocal.m4`/`config.h.in`/…），
   把 `*.am`/`*.ac` 的 mtime 退到 2020，并把 `AUTOCONF/AUTOMAKE/ACLOCAL/...` 设为 `:`。
4. **Osi/Clp 找不到 CoinUtils** ⇒ 必须显式给
   `--with-coinutils-incdir`/`--with-coinutils-lib`（Clp 另需 `--with-osi-*`）。
5. 无 `gfortran` ⇒ `--without-blas --without-lapack`（Clp 本身是纯 C++）。

脚本：`build_coinor.sh`（bash 入口，前台/后台均可重跑），日志 `build_coinor.log`。

### 4.3 状态（**已构建并验证可用**）

| 步骤 | 状态 |
|---|---|
| CoinUtils configure | ✅ `Main configuration of CoinUtils successful` |
| **CoinUtils 编译** | ✅ `libcoinutils.a` **1,732 KB**（57 个 .cpp） |
| **Osi 编译** | ✅ `libosi.a` **451 KB**（12 个 .cpp） |
| **Clp 编译** | ✅ `libclp.a` **2,804 KB**（50 + `OsiClpSolverInterface.cpp`） |
| boost 归档 | ✅ `_archives/boost_1_63_0.tar.bz2` **78.19 MB** |
| **链接验证** | ✅ `third_party/test_osiclp.cpp` → **`OSICLP-LINK-OK`**（见 §4.5） |
| **接入 lcns** | ✅ `-DLCNS_WITH_CLP=ON` 默认开启；`lcns::lp::ClpLinearProgram` 已在 `lcns_nest` 中编译并链接三个 `.a`；34 TU / 0 warning / `ctest` 15/15 |
| **双后端交叉验证** | ✅ `tests/test_linear_program.cpp` 让 `buildAndSolveLp`(0x7D7200) **同时**跑两个后端：目标值与对偶价必须一致，各自解必须可行且复现自己的目标值 |
| boost 接入 | ✅ 头文件路径已接、版本已 `static_assert` 钉住（106300） |

构建方式最终定型为：**configure 只用来生成 Clp 的 `config_clp.h`，编译改用 CMake + Ninja 直接编源码**
（`third_party/CMakeLists.txt`，产物在 `third_party/build-cmake/`）。
原因见 §4.2 第 3/4 条：autotools 生成的 makefile 坚持 `config.status --recheck`，而 libtool 的探测
在带空格的 Windows 路径上会碎。

### 4.4 构建偏差（**必须显式记录**）

| 偏差 | 原因 | 影响评估 |
|---|---|---|
| 排除 Clp 的 `Abc*.cpp` / `CoinAbc*.cpp`（14+ 个） | 是 2016 年的"加速单纯形"可选变体，用 GCC 13 编译会因不完整类型/POSIX 假设失败 | **不影响**：lcns 走 `OsiClpSolverInterface → ClpSimplex`，从不触碰 `AbcSimplex` |
| 排除 `ClpMain.cpp` | 它是独立可执行程序的 `main` | 无 |
| 排除 `ClpCholesky{Mumps,Taucs,Ufl,Wssmp,WssmpKKT}.cpp` | 需要外部求解器（MUMPS/TAUCS/UFL/WSSMP）的头文件 | **不影响**：保留自带的 `ClpCholeskyBase`/`ClpCholeskyDense` |
| 强制预包含 `compat/coin_compat.h` | 老代码依赖标准头的传递包含（如 `CoinFinite.cpp` 用 `DBL_MAX` 却没 include `<cfloat>`） | 第三方源码**保持原样未改** |
| `compat/coin_compat.h` 里 `#include "CoinFinite.hpp"` | Clp 1.15.3 的 `CbcOrClpParam.cpp:2601` 用了 `COIN_INT_MAX` 却没包含定义它的头（旧版 CoinUtils 会间接带入）。这里引入 **CoinUtils 自己的定义**，不是自编数值 | 精确 |
| 提供 `compat/endian.h` | MinGW 无 POSIX `<endian.h>`；`CoinAbcCommon.hpp` 只用 `__BYTE_ORDER`/`__LITTLE_ENDIAN` | x86-64 小端，**精确**而非近似 |
| `-DHAVE_CMATH` | configure 生成的 `config_clp.h` 不带该宏，`ClpHelperFunctions.hpp` 会 `#error` | 与实际环境一致 |
| Clp = **确切 1.15.3**（`releases/1.15.3`） | 二进制路径串实证；用该 tag 的 configure 生成 `config_clp.h`（`CLP_VERSION "1.15.3"`） | **无版本偏差** |
| CoinUtils `stable/2.10` / Osi `stable/0.107` | 二进制只证明它们位于 `Clp-1.15.3\` 包内，未给出补丁级版本 | **补丁级偏差可能存在**，已在 §1 标注为"未证实" |
| boost 仅接 include 路径 | 头文件库，无需编译 | T5 的钩子已就位；尚未把某个几何路径改写成 `boost::multiprecision` |

### 4.5 链接验证（可重跑）

`third_party/test_osiclp.cpp` 用 MPS 描述一个小 LP（`min x+2y, x+y>=1, x-y<=0`，最优 `x=y=0.5`），
经 `OsiClpSolverInterface::readMps` + `initialSolve` 求解：

```
Coin0008I LCNSLINK read with 0 errors
Coin0506I Presolve 2 (0) rows, 2 (0) columns and 4 (0) elements
Clp0006I 2  Obj 1.5
Clp0000I Optimal - objective value 1.5
cols=2 rows=2  status=1  x=0.500000 y=0.500000  obj=1.500000
OSICLP-LINK-OK
```

编译命令（需把 MinGW 放进 PATH）：

```powershell
g++ -std=gnu++11 -O2 -w -include third_party\compat\coin_compat.h -DHAVE_CMATH `
  -Ithird_party\compat -Ithird_party\src\clp-1.15\Clp\src -Ithird_party\src\clp-1.15\Clp\src\OsiClp -Ithird_party\gen\clp `
  -Ithird_party\src\osi-0.107\Osi\src\Osi -Ithird_party\gen\osi `
  -Ithird_party\src\coinutils-2.10\CoinUtils\src -Ithird_party\gen\coinutils `
  third_party\test_osiclp.cpp -o third_party\test_osiclp.exe `
  third_party\build-cmake\libclp.a third_party\build-cmake\libosi.a third_party\build-cmake\libcoinutils.a
```

⇒ **"下载并直接引用第三方库"这条指示已经落地**：Clp/Osi/CoinUtils 都是真库、真编译、真能解 LP。

## Independent confirmation from the binary itself (goal round 117)

The DLL carries absolute build paths for the external libraries and NONE for the project's own sources
(those are relative, e.g. `..\multi\supervisor.cpp`). Two external names appear, with counts:

| name in the image | hits | what third_party/ pins |
|---|---:|---|
| `Clp-1.15.3` | 15 | Clp 1.15.3, checked out at the `releases/1.15.3` tag |
| `boost_1_63_0` | 10 | boost 1.63.0 headers, pinned by `static_assert(BOOST_VERSION == 106300)` |

So the versions used here are not guesses: the binary names them. The paths look like
`C:\Users\renaud\nest\external\boost_1_63_0/boost/multiprecision/cpp_int/checked.hpp`, i.e. the
original build root was `C:\Users\renaud\nest\` with the libraries under `external\`.

That also explains the layout of the recovery documents: the application's own translation units are
only ever named by relative paths (`..\multi\supervisor.cpp`), which is why TU attribution in re/ keys
off absolute paths only for third-party code.
