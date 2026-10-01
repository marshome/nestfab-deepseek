# nestfab —— `libcns`（Optalog CNS 排料引擎）的逆向工程与等价重建

本仓库是对一个**专有二维排料（nesting / cutting & packing）引擎** `libcns.dll`
（Optalog CNS，构建 `5.0 - 68e2d90e72b4 5449`，2019-06-28，UPX 内存转储）的
**系统化逆向记录**，以及一个力求与之等价的 C++ 重建工程 `lcns/`。

> **本仓库不包含该 DLL 本身。** 它是第三方专有二进制，公开再分发有法律风险。
> 复现分析需要你自己合法取得该文件，放到仓库根目录并命名为 `libcns_dump_64.dll`。
> 校验值：MD5 `01fea4b73a33dd233c66ca76235313fa`，SHA-256 `f63b98a94de4b2ca14785de207510ae13a570ca834bc505665bbce9e42efa847`，
> 大小 11,808,768 字节。

## 这个仓库里有什么

```
re/          逆向记录：报告、发现、探针脚本、交叉引用与函数档案
  REPORT.md            总报告（§0–§13 + 附录）：导出面、几何内核、引擎、逐零件路径、残留清单
  findings_*.md        分领域发现（LP/Clp 用法、几何、引擎、特性、云与授权、row 路径…）
  UNCOVERED_RANKED.md  按体积排序的「尚未逆向」函数清单（可复现）
  TU_MAP.md            由二进制内嵌断言路径重建的**原工程 TU 地图**
  g_coverage.py        覆盖率度量（可复现；见下文口径）
  g_tu_map.py / g_tu_list.py / g_tu_strings.py / g_fs.py   逐 TU 与逐函数的结构分析工具
  lib.py               读取转储、反汇编、字符串表等基础设施
lcns/        等价重建工程（C++17，CMake + Ninja，MinGW-w64 GCC）
  include/lcns/, src/, apps/, tests/, tools/, docs/
  docs/RECOVERY_STATUS.md   逆向状态总表（由 recovery.hpp 生成）
  docs/ARCHITECTURE.svg, ALGORITHMS.md, FLOW_*.svg   架构图与算法流程图
datasets/    外部基准：来源、许可、出处，以及对比结果
  README.md    数据集来源/许可/出处 + 复现命令 + 已完成的分析
  RESULTS.md   与文献最优值的对比表（含 ROMA/GCS/FLD/ELS/PS）
  results.csv  本工程在各实例上的原始统计
  refs/        引用的论文 LaTeX 源码（结果表的权威来源）
third_party/ 第三方库的策略与构建记录（**只留脚本与文档，不留源码/归档**）
```

## 诚实性约定（这个项目最重要的部分）

逆向工程最容易出问题的地方是**把"猜的"当成"逆出来的"**。本仓库用三层机制防这件事：

1. **每条结论带地址级证据**：常量、字段偏移、算法都注明 RVA；读不出来的项**明说读不出来并给出可复核原因**，
   绝不用近似值顶替。
2. **代码里可 grep 的状态标记**（`lcns/include/lcns/recovery.hpp`）：
   `LCNS_RECOVERED`（逐指令忠实）/ `LCNS_STRUCTURAL`（结构已恢复、实现为重写）/
   `LCNS_SUBSTITUTED`（替代实现）/ `LCNS_NOT_REVERSED`（存在但未逆向）/ `LCNS_NOT_IN_BINARY`（本工程扩展）。
   当前 **59 条登记**，`tools/check_recovery.py` 强制「代码标记集合 == 登记表集合」，
   且带具体 RVA 的缺口必须出现在 `re/` 文档中。
3. **可执行的验收测试**：`lcns/tests/test_recovered.cpp` 把工程常量与从二进制读出的数值机械绑定；
   `re/g_acceptance.py` 核对结论的地址依据是否真的出现在文档里。

## 覆盖率的口径（以及它为什么是"代理指标"）

`python re/g_coverage.py` 给出：

* 分母 = 从 168 个导出出发**可达**的函数（沿直接调用 + `re/vtables.json` 的 416 张虚表 slot 边）；
* 分子 = 入口地址**在本文档或工程里出现过**的函数；
* 三分类 = **第三方库**（待下载链接）/ **工具链**（libstdc++/MinGW）/ **领域代码**（真正要逆向的）。

被"引用"只说明**看过并写下了它是什么**，**不等于**逐指令复现 —— 后者由上面第 2 条的登记表跟踪。
脚本会排除自己生成的报告与原始数据表，否则「把某函数列为未覆盖」这件事本身就会把它算成已覆盖。

## 第三方库：下载并直接引用，不逆向

二进制里能证明用到（字符串实证）：**boost 1.63.0**、**COIN-OR CoinUtils/Osi/Clp**
（`OsiClpSolverInterface`）、**CryptoPP**、**JsonCpp**；libstdc++/MinGW 属工具链。
它们的获取、构建、以及**已踩通的坑与全部构建偏差**都记录在
[`third_party/README.md`](third_party/README.md)：

* `third_party/fetch.ps1` 下载（curl + git；普通 Python HTTPS 在此网络会超时）；
* `third_party/CMakeLists.txt` 用工程自带的 MinGW GCC 直接编译
  （autotools 生成的 makefile 会坚持 `config.status --recheck`，且 `$(SHELL)` 带空格路径会碎）；
* `third_party/test_osiclp.cpp` 是**链接验证**：解一个 MPS 小 LP，输出 `OSICLP-LINK-OK`。

## 构建

```powershell
$env:PATH = 'C:\Program Files\JetBrains\CLion 2025.3.3\bin\mingw\bin;' + $env:PATH
cd lcns
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo `
      -DCMAKE_CXX_COMPILER=g++ -DCMAKE_MAKE_PROGRAM=ninja
cmake --build build
ctest --test-dir build --output-on-failure      # 15/15
python tools/check_recovery.py                  # 代码标记 == 登记表
python tools/check_arch.py                      # 架构图布局自检
```

## 现状（一句话）

导出面、几何内核结构、逐零件路径、引擎调度层、LP 层结构、完整选项键表、
JSON/DXF/SVG 格式与授权事实**已恢复到地址级**；
**尚未完成**的是可达领域代码里约六成（详见 `re/TU_MAP.md` 与 `re/UNCOVERED_RANKED.md`），
其中最关键的是 12 个策略的 `Run` 体与主放置器 —— 这也是本工程的排料密度仍显著低于文献的原因。

## 引用与许可

* 本仓库的分析与代码：见 `LICENSE`（如有）。
* `datasets/` 下的数据**不属于本仓库**：它们的来源与许可见 [`datasets/README.md`](datasets/README.md)
  （ESICUP 数据集 CC0-1.0；OR-Datasets MIT；引用的论文 CC BY 4.0，请按其要求署名）。
* 第三方库的许可见 [`third_party/README.md`](third_party/README.md)。
* 目标二进制 `libcns.dll` 的版权属于其权利人；本仓库只包含对它的**分析与重建**，不包含它本身。
