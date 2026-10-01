# 识别清单 `re/IDENTIFIED.md`（**按证据识别，不是逆向**）

本文件由 `re/g_identify.py` 生成（goal round 8）。它对**可达、但此前从未被引用**的领域函数给出
**可复核的识别记录**，并逐条标注**证据等级**。

## 重要：本文件**不**声称这些函数已逆向

* 这里登记的是**来源与角色**：它属于哪张虚表的第几槽、被谁调用、结构指纹像什么。
* **没有**逐指令转写其函数体；保真度声明仍然只在 [`lcns/include/lcns/recovery.hpp`](../lcns/include/lcns/recovery.hpp) 的登记表里。
* `g_coverage.py` 因此把指标分三档：**代码中已实现** / **仅文档引用** / **无记录**。
  本文件让第三档变小，但**不会**让第一档变大 —— 两档必须分开看。

## 证据等级（由强到弱）

| 等级 | 含义 |
|---|---|
| `vtable` | 它是某已知虚表的第 k 槽 ⇒ 类名 + 槽号即身份（最强） |
| `name` | 已有恢复出的名字 |
| `strings` | 自身引用的字符串（格式串、源码路径、选项键） |
| `callers` | 被哪些**有名字**的函数调用（来源即证据） |
| `callees` | 它调用了哪些**有名字**的函数 |
| `shape only` | 什么名字都没有：只给出结构指纹（尺寸/指令数/形态） |

## 统计

| 证据等级 | 函数数 | 字节 |
|---|---:|---:|
| `shape only` | 3280 | 1466106 |
| `strings` | 275 | 201715 |
| `callers` | 17 | 5932 |

## 清单

| 地址 | 字节 | 调用者数 | 证据等级 | 识别记录 | 结构指纹 |
|---|---:|---:|---|---|---|
| `0x1ba4c0` | 2642 | 2 | `shape only` | has a backward branch (often a loop), 559 ins | has a backward branch (often a loop) |
| `0x8af220` | 2640 | 2 | `shape only` | has a backward branch (often a loop), 632 ins | has a backward branch (often a loop) |
| `0x182d90` | 2638 | 2 | `shape only` | has a backward branch (often a loop), 617 ins | has a backward branch (often a loop) |
| `0x6daec0` | 2636 | 2 | `strings` | UWVSH \| VSH | has a backward branch (often a loop) |
| `0x63b140` | 2625 | 5 | `shape only` | has a backward branch (often a loop), 587 ins | has a backward branch (often a loop) |
| `0x54d760` | 2622 | 3 | `shape only` | has a backward branch (often a loop), 613 ins | has a backward branch (often a loop) |
| `0x772d40` | 2622 | 3 | `shape only` | has a backward branch (often a loop), 552 ins | has a backward branch (often a loop) |
| `0x528020` | 2621 | 4 | `strings` | ..\structure\stats.cpp \| biggest | has a backward branch (often a loop) |
| `0x163170` | 2614 | 4 | `shape only` | has a backward branch (often a loop), 537 ins | has a backward branch (often a loop) |
| `0x95cdc0` | 2610 | 3 | `shape only` | has a backward branch (often a loop), 491 ins | has a backward branch (often a loop) |
| `0x2098f0` | 2606 | 3 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x700460` | 2589 | 7 | `shape only` | has a backward branch (often a loop), 569 ins | has a backward branch (often a loop) |
| `0x139800` | 2586 | 4 | `shape only` | has a backward branch (often a loop), 542 ins | has a backward branch (often a loop) |
| `0x4d7720` | 2563 | 3 | `shape only` | has a backward branch (often a loop), 513 ins | has a backward branch (often a loop) |
| `0x69cb20` | 2556 | 3 | `shape only` | has a backward branch (often a loop), 619 ins | has a backward branch (often a loop) |
| `0x54ac00` | 2555 | 3 | `shape only` | has a backward branch (often a loop), 579 ins | has a backward branch (often a loop) |
| `0x8abb50` | 2549 | 2 | `shape only` | has a backward branch (often a loop), 606 ins | has a backward branch (often a loop) |
| `0x89b7b0` | 2542 | 3 | `shape only` | has a backward branch (often a loop), 570 ins | has a backward branch (often a loop) |
| `0x722a0` | 2528 | 3 | `shape only` | has a backward branch (often a loop), 553 ins | has a backward branch (often a loop) |
| `0x95dc80` | 2528 | 2 | `shape only` | has a backward branch (often a loop), 602 ins | has a backward branch (often a loop) |
| `0x6c4cc0` | 2510 | 2 | `shape only` | has a backward branch (often a loop), 500 ins | has a backward branch (often a loop) |
| `0x8a49a0` | 2503 | 2 | `shape only` | has a backward branch (often a loop), 672 ins | has a backward branch (often a loop) |
| `0x528d10` | 2493 | 5 | `strings` | ..\structure\stats.cpp \| biggest | has a backward branch (often a loop) |
| `0x5215d0` | 2485 | 3 | `shape only` | has a backward branch (often a loop), 480 ins | has a backward branch (often a loop) |
| `0x827240` | 2479 | 2 | `strings` | cannot create shim for unknown locale::f | has a backward branch (often a loop) |
| `0x827bf0` | 2479 | 2 | `strings` | cannot create shim for unknown locale::f | has a backward branch (often a loop) |
| `0x903330` | 2468 | 2 | `shape only` | has a backward branch (often a loop), 593 ins | has a backward branch (often a loop) |
| `0x172ac0` | 2445 | 2 | `shape only` | has a backward branch (often a loop), 556 ins | has a backward branch (often a loop) |
| `0x15ae70` | 2429 | 7 | `shape only` | has a backward branch (often a loop), 488 ins | has a backward branch (often a loop) |
| `0x1b9650` | 2423 | 2 | `shape only` | has a backward branch (often a loop), 521 ins | has a backward branch (often a loop) |
| `0x681040` | 2419 | 3 | `shape only` | has a backward branch (often a loop), 494 ins | has a backward branch (often a loop) |
| `0x581fd0` | 2416 | 2 | `shape only` | has a backward branch (often a loop), 523 ins | has a backward branch (often a loop) |
| `0x1dda60` | 2414 | 2 | `shape only` | has a backward branch (often a loop), 520 ins | has a backward branch (often a loop) |
| `0x53c2c0` | 2414 | 2 | `shape only` | has a backward branch (often a loop), 509 ins | has a backward branch (often a loop) |
| `0x5c7c40` | 2411 | 5 | `shape only` | has a backward branch (often a loop), 573 ins | has a backward branch (often a loop) |
| `0x67ff00` | 2410 | 3 | `shape only` | has a backward branch (often a loop), 539 ins | has a backward branch (often a loop) |
| `0x981ab0` | 2396 | 2 | `shape only` | has a backward branch (often a loop), 557 ins | has a backward branch (often a loop) |
| `0x907610` | 2381 | 2 | `shape only` | has a backward branch (often a loop), 432 ins | has a backward branch (often a loop) |
| `0x4b8ae0` | 2377 | 3 | `shape only` | has a backward branch (often a loop), 592 ins | has a backward branch (often a loop) |
| `0x19fe90` | 2374 | 3 | `strings` | vector::reserve \| a2U0* | has a backward branch (often a loop) |
| `0x570ee0` | 2365 | 3 | `shape only` | has a backward branch (often a loop), 485 ins | has a backward branch (often a loop) |
| `0x71f670` | 2359 | 2 | `shape only` | has a backward branch (often a loop), 476 ins | has a backward branch (often a loop) |
| `0x23f960` | 2342 | 2 | `shape only` | has a backward branch (often a loop), 542 ins | has a backward branch (often a loop) |
| `0x970460` | 2329 | 4 | `shape only` | has a backward branch (often a loop), 443 ins | has a backward branch (often a loop) |
| `0x1bb490` | 2297 | 7 | `shape only` | has a backward branch (often a loop), 511 ins | has a backward branch (often a loop) |
| `0x4e9a10` | 2297 | 3 | `strings` | !GetOrientation(minimal_box).flip() \| ..\tiling\optimizer.cpp | has a backward branch (often a loop) |
| `0x155bb0` | 2294 | 3 | `shape only` | has a backward branch (often a loop), 459 ins | has a backward branch (often a loop) |
| `0x52aad0` | 2294 | 2 | `strings` | sheet \| ..\structure\stats.cpp | has a backward branch (often a loop) |
| `0x8f6a50` | 2268 | 2 | `shape only` | has a backward branch (often a loop), 554 ins | has a backward branch (often a loop) |
| `0x603740` | 2266 | 4 | `strings` | true \| false | has a backward branch (often a loop) |
| `0x96bb00` | 2254 | 3 | `shape only` | has a backward branch (often a loop), 525 ins | has a backward branch (often a loop) |
| `0x515750` | 2253 | 2 | `strings` | cluster:  | has a backward branch (often a loop) |
| `0x7b8dc0` | 2253 | 4 | `strings` | (n.nesteds().size() != nb_nested) \|\| m_c \| SetNesting | has a backward branch (often a loop) |
| `0x6c5a30` | 2250 | 2 | `shape only` | has a backward branch (often a loop), 470 ins | has a backward branch (often a loop) |
| `0x6e1d40` | 2242 | 2 | `shape only` | has a backward branch (often a loop), 451 ins | has a backward branch (often a loop) |
| `0x764ba0` | 2235 | 2 | `strings` | level  | has a backward branch (often a loop) |
| `0x939540` | 2230 | 2 | `shape only` | has a backward branch (often a loop), 524 ins | has a backward branch (often a loop) |
| `0x598fc0` | 2222 | 4 | `shape only` | has a backward branch (often a loop), 508 ins | has a backward branch (often a loop) |
| `0x963820` | 2222 | 2 | `shape only` | has a backward branch (often a loop), 432 ins | has a backward branch (often a loop) |
| `0x560380` | 2212 | 3 | `shape only` | has a backward branch (often a loop), 481 ins | has a backward branch (often a loop) |
| `0x52b3d0` | 2198 | 2 | `shape only` | has a backward branch (often a loop), 473 ins | has a backward branch (often a loop) |
| `0x4f7aa0` | 2196 | 3 | `shape only` | has a backward branch (often a loop), 500 ins | has a backward branch (often a loop) |
| `0x8fa120` | 2196 | 4 | `shape only` | has a backward branch (often a loop), 577 ins | has a backward branch (often a loop) |
| `0x98b920` | 2185 | 3 | `shape only` | has a backward branch (often a loop), 516 ins | has a backward branch (often a loop) |
| `0x553230` | 2161 | 3 | `shape only` | has a backward branch (often a loop), 519 ins | has a backward branch (often a loop) |
| `0x262980` | 2158 | 2 | `shape only` | has a backward branch (often a loop), 502 ins | has a backward branch (often a loop) |
| `0x1eb840` | 2157 | 3 | `shape only` | has a backward branch (often a loop), 483 ins | has a backward branch (often a loop) |
| `0x62b950` | 2154 | 3 | `strings` |  restrict \|  volatile | has a backward branch (often a loop) |
| `0x7dbb00` | 2140 | 2 | `shape only` | has a backward branch (often a loop), 412 ins | has a backward branch (often a loop) |
| `0x71c660` | 2138 | 2 | `shape only` | has a backward branch (often a loop), 456 ins | has a backward branch (often a loop) |
| `0x5f8e20` | 2131 | 2 | `shape only` | has a backward branch (often a loop), 451 ins | has a backward branch (often a loop) |
| `0x55a230` | 2130 | 4 | `shape only` | has a backward branch (often a loop), 412 ins | has a backward branch (often a loop) |
| `0x702120` | 2128 | 2 | `shape only` | has a backward branch (often a loop), 455 ins | has a backward branch (often a loop) |
| `0x703a10` | 2128 | 2 | `shape only` | has a backward branch (often a loop), 455 ins | has a backward branch (often a loop) |
| `0x97f850` | 2128 | 2 | `shape only` | has a backward branch (often a loop), 560 ins | has a backward branch (often a loop) |
| `0x559430` | 2126 | 2 | `shape only` | has a backward branch (often a loop), 445 ins | has a backward branch (often a loop) |
| `0x7ed7c0` | 2125 | 2 | `shape only` | has a backward branch (often a loop), 421 ins | has a backward branch (often a loop) |
| `0x55b550` | 2100 | 3 | `shape only` | has a backward branch (often a loop), 409 ins | has a backward branch (often a loop) |
| `0x17e5f0` | 2089 | 3 | `shape only` | has a backward branch (often a loop), 434 ins | has a backward branch (often a loop) |
| `0x5426c0` | 2085 | 3 | `shape only` | has a backward branch (often a loop), 443 ins | has a backward branch (often a loop) |
| `0x1b0760` | 2060 | 2 | `strings` | shaker_ \| compacting ... | has a backward branch (often a loop) |
| `0x20b610` | 2059 | 3 | `shape only` | has a backward branch (often a loop), 460 ins | has a backward branch (often a loop) |
| `0x58c330` | 2047 | 6 | `shape only` | has a backward branch (often a loop), 443 ins | has a backward branch (often a loop) |
| `0x924580` | 2035 | 5 | `shape only` | has a backward branch (often a loop), 475 ins | has a backward branch (often a loop) |
| `0x71be70` | 2025 | 2 | `shape only` | has a backward branch (often a loop), 425 ins | has a backward branch (often a loop) |
| `0x8a7340` | 2022 | 2 | `shape only` | has a backward branch (often a loop), 554 ins | has a backward branch (often a loop) |
| `0x8b5230` | 2019 | 2 | `shape only` | has a backward branch (often a loop), 460 ins | has a backward branch (often a loop) |
| `0x8b280` | 2018 | 2 | `strings` | (nx < 1000) && (ny < 1000) \| ..\multi\marker.cpp | has a backward branch (often a loop) |
| `0x1909f0` | 2011 | 2 | `shape only` | has a backward branch (often a loop), 479 ins | has a backward branch (often a loop) |
| `0x73e6f0` | 1997 | 3 | `shape only` | has a backward branch (often a loop), 385 ins | has a backward branch (often a loop) |
| `0x742e20` | 1997 | 3 | `shape only` | has a backward branch (often a loop), 385 ins | has a backward branch (often a loop) |
| `0x156be0` | 1979 | 3 | `shape only` | has a backward branch (often a loop), 406 ins | has a backward branch (often a loop) |
| `0x7e5850` | 1972 | 2 | `shape only` | has a backward branch (often a loop), 464 ins | has a backward branch (often a loop) |
| `0x8e22a0` | 1972 | 2 | `shape only` | has a backward branch (often a loop), 474 ins | has a backward branch (often a loop) |
| `0x8d82c0` | 1969 | 4 | `shape only` | has a backward branch (often a loop), 488 ins | has a backward branch (often a loop) |
| `0x5b1530` | 1968 | 2 | `shape only` | has a backward branch (often a loop), 338 ins | has a backward branch (often a loop) |
| `0x715320` | 1964 | 3 | `shape only` | has a backward branch (often a loop), 417 ins | has a backward branch (often a loop) |
| `0x656a60` | 1961 | 2 | `shape only` | has a backward branch (often a loop), 418 ins | has a backward branch (often a loop) |
| `0x1a6de0` | 1949 | 2 | `shape only` | has a backward branch (often a loop), 336 ins | has a backward branch (often a loop) |
| `0x4d8dc0` | 1945 | 4 | `shape only` | has a backward branch (often a loop), 472 ins | has a backward branch (often a loop) |
| `0x4f2a30` | 1944 | 3 | `shape only` | has a backward branch (often a loop), 409 ins | has a backward branch (often a loop) |
| `0x7b8620` | 1944 | 2 | `shape only` | has a backward branch (often a loop), 398 ins | has a backward branch (often a loop) |
| `0x6249d0` | 1942 | 2 | `shape only` | has a backward branch (often a loop), 494 ins | has a backward branch (often a loop) |
| `0x5b0cf0` | 1940 | 4 | `shape only` | has a backward branch (often a loop), 357 ins | has a backward branch (often a loop) |
| `0x5b22d0` | 1938 | 2 | `shape only` | has a backward branch (often a loop), 368 ins | has a backward branch (often a loop) |
| `0x5f1f90` | 1927 | 3 | `shape only` | has a backward branch (often a loop), 383 ins | has a backward branch (often a loop) |
| `0x5f79d0` | 1926 | 4 | `shape only` | has a backward branch (often a loop), 455 ins | has a backward branch (often a loop) |
| `0x567260` | 1924 | 2 | `shape only` | has a backward branch (often a loop), 368 ins | has a backward branch (often a loop) |
| `0x6cb4a0` | 1924 | 2 | `shape only` | has a backward branch (often a loop), 292 ins | has a backward branch (often a loop) |
| `0x95eac0` | 1922 | 2 | `shape only` | has a backward branch (often a loop), 490 ins | has a backward branch (often a loop) |
| `0xaa250` | 1913 | 2 | `shape only` | has a backward branch (often a loop), 408 ins | has a backward branch (often a loop) |
| `0x8fa9c0` | 1908 | 6 | `shape only` | has a backward branch (often a loop), 520 ins | has a backward branch (often a loop) |
| `0x7b71a0` | 1889 | 2 | `shape only` | has a backward branch (often a loop), 418 ins | has a backward branch (often a loop) |
| `0x8b6360` | 1880 | 5 | `shape only` | has a backward branch (often a loop), 479 ins | has a backward branch (often a loop) |
| `0x96f8f0` | 1879 | 3 | `shape only` | has a backward branch (often a loop), 418 ins | has a backward branch (often a loop) |
| `0x5455a0` | 1863 | 2 | `shape only` | has a backward branch (often a loop), 392 ins | has a backward branch (often a loop) |
| `0x1a66a0` | 1852 | 3 | `strings` | ..\nesting\algos\algo_parameters.cpp \| false && "field must be in 1 .. 5" | has a backward branch (often a loop) |
| `0x14ccf0` | 1850 | 6 | `shape only` | has a backward branch (often a loop), 353 ins | has a backward branch (often a loop) |
| `0x56b090` | 1849 | 2 | `shape only` | has a backward branch (often a loop), 366 ins | has a backward branch (often a loop) |
| `0x83dc0` | 1842 | 3 | `shape only` | has a backward branch (often a loop), 375 ins | has a backward branch (often a loop) |
| `0x5d5cc0` | 1840 | 2 | `strings` |   0 \| SECTION | has a backward branch (often a loop) |
| `0x6b91d0` | 1839 | 4 | `shape only` | straight line / call sequence, 509 ins | straight line / call sequence |
| `0x6bb500` | 1839 | 3 | `shape only` | straight line / call sequence, 509 ins | straight line / call sequence |
| `0x6bc540` | 1839 | 3 | `shape only` | straight line / call sequence, 509 ins | straight line / call sequence |
| `0x6bd4a0` | 1839 | 5 | `shape only` | straight line / call sequence, 509 ins | straight line / call sequence |
| `0x6be760` | 1839 | 4 | `shape only` | straight line / call sequence, 509 ins | straight line / call sequence |
| `0x6bfc20` | 1839 | 3 | `shape only` | straight line / call sequence, 509 ins | straight line / call sequence |
| `0x1efe50` | 1829 | 2 | `shape only` | has a backward branch (often a loop), 427 ins | has a backward branch (often a loop) |
| `0x9520b0` | 1828 | 3 | `shape only` | has a backward branch (often a loop), 406 ins | has a backward branch (often a loop) |
| `0x5db410` | 1827 | 11 | `shape only` | has a backward branch (often a loop), 376 ins | has a backward branch (often a loop) |
| `0x4f9fe0` | 1821 | 5 | `shape only` | has a backward branch (often a loop), 423 ins | has a backward branch (often a loop) |
| `0x2665f0` | 1819 | 2 | `shape only` | has a backward branch (often a loop), 422 ins | has a backward branch (often a loop) |
| `0x94bb20` | 1816 | 2 | `shape only` | has a backward branch (often a loop), 300 ins | has a backward branch (often a loop) |
| `0x56a980` | 1801 | 2 | `shape only` | has a backward branch (often a loop), 352 ins | has a backward branch (often a loop) |
| `0x713650` | 1790 | 2 | `shape only` | has a backward branch (often a loop), 312 ins | has a backward branch (often a loop) |
| `0x4b83e0` | 1788 | 3 | `shape only` | has a backward branch (often a loop), 422 ins | has a backward branch (often a loop) |
| `0x1a9450` | 1787 | 3 | `strings` | infos | has a backward branch (often a loop) |
| `0x6cbe80` | 1786 | 8 | `strings` | table | has a backward branch (often a loop) |
| `0x721ff0` | 1781 | 2 | `shape only` | has a backward branch (often a loop), 414 ins | has a backward branch (often a loop) |
| `0x723b20` | 1781 | 2 | `shape only` | has a backward branch (often a loop), 414 ins | has a backward branch (often a loop) |
| `0x927ef0` | 1770 | 3 | `shape only` | has a backward branch (often a loop), 429 ins | has a backward branch (often a loop) |
| `0x139110` | 1769 | 2 | `shape only` | has a backward branch (often a loop), 343 ins | has a backward branch (often a loop) |
| `0x8c9540` | 1767 | 3 | `shape only` | has a backward branch (often a loop), 356 ins | has a backward branch (often a loop) |
| `0xb51c0` | 1756 | 4 | `callers` | called by 0x6100 LaunchComputation | has a backward branch (often a loop) |
| `0x9d760` | 1755 | 3 | `shape only` | has a backward branch (often a loop), 440 ins | has a backward branch (often a loop) |
| `0x1eb160` | 1755 | 2 | `shape only` | has a backward branch (often a loop), 384 ins | has a backward branch (often a loop) |
| `0x59a870` | 1755 | 3 | `shape only` | has a backward branch (often a loop), 439 ins | has a backward branch (often a loop) |
| `0x73d250` | 1746 | 3 | `shape only` | has a backward branch (often a loop), 346 ins | has a backward branch (often a loop) |
| `0x7418f0` | 1746 | 3 | `shape only` | has a backward branch (often a loop), 346 ins | has a backward branch (often a loop) |
| `0x539740` | 1742 | 2 | `shape only` | has a backward branch (often a loop), 421 ins | has a backward branch (often a loop) |
| `0x4d5060` | 1732 | 3 | `strings` | random  | has a backward branch (often a loop) |
| `0x17c0d0` | 1726 | 2 | `shape only` | has a backward branch (often a loop), 370 ins | has a backward branch (often a loop) |
| `0x5ef7e0` | 1724 | 2 | `shape only` | has a backward branch (often a loop), 318 ins | has a backward branch (often a loop) |
| `0x515090` | 1723 | 2 | `strings` | basic_string::append \| sheet dimensions:  | has a backward branch (often a loop) |
| `0x254740` | 1722 | 2 | `shape only` | has a backward branch (often a loop), 461 ins | has a backward branch (often a loop) |
| `0x7e0550` | 1720 | 2 | `shape only` | has a backward branch (often a loop), 421 ins | has a backward branch (often a loop) |
| `0x5c26e0` | 1719 | 7 | `shape only` | has a backward branch (often a loop), 355 ins | has a backward branch (often a loop) |
| `0x5fa240` | 1710 | 4 | `shape only` | has a backward branch (often a loop), 357 ins | has a backward branch (often a loop) |
| `0x2539e0` | 1706 | 2 | `shape only` | has a backward branch (often a loop), 459 ins | has a backward branch (often a loop) |
| `0x254090` | 1706 | 4 | `shape only` | has a backward branch (often a loop), 459 ins | has a backward branch (often a loop) |
| `0x4ea310` | 1706 | 2 | `shape only` | has a backward branch (often a loop), 364 ins | has a backward branch (often a loop) |
| `0x5f9680` | 1703 | 4 | `shape only` | has a backward branch (often a loop), 378 ins | has a backward branch (often a loop) |
| `0x959660` | 1699 | 3 | `shape only` | has a backward branch (often a loop), 387 ins | has a backward branch (often a loop) |
| `0x1642e0` | 1687 | 2 | `shape only` | has a backward branch (often a loop), 348 ins | has a backward branch (often a loop) |
| `0x4e4a60` | 1687 | 3 | `shape only` | has a backward branch (often a loop), 350 ins | has a backward branch (often a loop) |
| `0xfdb10` | 1685 | 7 | `shape only` | has a backward branch (often a loop), 451 ins | has a backward branch (often a loop) |
| `0x53d990` | 1680 | 2 | `shape only` | has a backward branch (often a loop), 397 ins | has a backward branch (often a loop) |
| `0x22a610` | 1676 | 2 | `shape only` | has a backward branch (often a loop), 432 ins | has a backward branch (often a loop) |
| `0x32700` | 1669 | 3 | `shape only` | has a backward branch (often a loop), 357 ins | has a backward branch (often a loop) |
| `0x1cd840` | 1667 | 3 | `shape only` | has a backward branch (often a loop), 398 ins | has a backward branch (often a loop) |
| `0x97b150` | 1660 | 2 | `shape only` | has a backward branch (often a loop), 452 ins | has a backward branch (often a loop) |
| `0x518910` | 1659 | 4 | `shape only` | has a backward branch (often a loop), 321 ins | has a backward branch (often a loop) |
| `0x5ea470` | 1656 | 5 | `shape only` | has a backward branch (often a loop), 380 ins | has a backward branch (often a loop) |
| `0x25eb60` | 1653 | 2 | `shape only` | has a backward branch (often a loop), 323 ins | has a backward branch (often a loop) |
| `0x8b4bb0` | 1653 | 6 | `shape only` | has a backward branch (often a loop), 426 ins | has a backward branch (often a loop) |
| `0x20f590` | 1650 | 4 | `shape only` | has a backward branch (often a loop), 372 ins | has a backward branch (often a loop) |
| `0x4d86c0` | 1650 | 2 | `strings` | basic_string::_M_construct null not vali \|  \|  | has a backward branch (often a loop) |
| `0x871b20` | 1649 | 1 | `shape only` | has a backward branch (often a loop), 457 ins | has a backward branch (often a loop) |
| `0x8ee7d0` | 1633 | 2 | `shape only` | has a backward branch (often a loop), 346 ins | has a backward branch (often a loop) |
| `0x625170` | 1631 | 4 | `shape only` | has a backward branch (often a loop), 436 ins | has a backward branch (often a loop) |
| `0x8d390` | 1625 | 2 | `shape only` | has a backward branch (often a loop), 378 ins | has a backward branch (often a loop) |
| `0x55d2f0` | 1622 | 4 | `shape only` | has a backward branch (often a loop), 339 ins | has a backward branch (often a loop) |
| `0x164980` | 1620 | 2 | `strings` | UWVSH | has a backward branch (often a loop) |
| `0x76f340` | 1617 | 3 | `shape only` | has a backward branch (often a loop), 329 ins | has a backward branch (often a loop) |
| `0x8b1e30` | 1615 | 3 | `shape only` | has a backward branch (often a loop), 403 ins | has a backward branch (often a loop) |
| `0x1bf2b0` | 1610 | 2 | `strings` |  Sa \|  Sq | has a backward branch (often a loop) |
| `0x8ee020` | 1610 | 19 | `shape only` | has a backward branch (often a loop), 332 ins | has a backward branch (often a loop) |
| `0x673c60` | 1607 | 2 | `strings` | ..\nesting\algos\tree_db.cpp \| m_is_right[node] | has a backward branch (often a loop) |
| `0x462d0` | 1605 | 3 | `strings` | basic_string::_M_construct null not vali \| ..\multi\tiling_nester.cpp | has a backward branch (often a loop) |
| `0x20e200` | 1600 | 2 | `strings` | vector::_M_range_check: __n (which is %z \| ..\nesting\algos\algo_helpers.hpp | has a backward branch (often a loop) |
| `0x872cc0` | 1599 | 1 | `shape only` | straight line / call sequence, 397 ins | straight line / call sequence |
| `0x9a690` | 1590 | 2 | `shape only` | has a backward branch (often a loop), 384 ins | has a backward branch (often a loop) |
| `0x538180` | 1587 | 2 | `shape only` | has a backward branch (often a loop), 379 ins | has a backward branch (often a loop) |
| `0xfcd80` | 1586 | 10 | `shape only` | has a backward branch (often a loop), 398 ins | has a backward branch (often a loop) |
| `0x55ed00` | 1579 | 4 | `shape only` | has a backward branch (often a loop), 381 ins | has a backward branch (often a loop) |
| `0x1a7c00` | 1578 | 5 | `strings` | vector::reserve \| strip_x | has a backward branch (often a loop) |
| `0x4e5b0` | 1574 | 2 | `strings` | 333333 \| 333333 | straight line / call sequence |
| `0x261ff0` | 1572 | 13 | `shape only` | has a backward branch (often a loop), 379 ins | has a backward branch (often a loop) |
| `0x4e93c0` | 1569 | 3 | `shape only` | has a backward branch (often a loop), 320 ins | has a backward branch (often a loop) |
| `0x5e6460` | 1568 | 4 | `shape only` | has a backward branch (often a loop), 309 ins | has a backward branch (often a loop) |
| `0x6bbf20` | 1561 | 2 | `shape only` | has a backward branch (often a loop), 385 ins | has a backward branch (often a loop) |
| `0x21ca20` | 1559 | 2 | `shape only` | has a backward branch (often a loop), 424 ins | has a backward branch (often a loop) |
| `0x20e840` | 1552 | 2 | `strings` | vector::_M_range_check: __n (which is %z \| ..\nesting\algos\algo_helpers.hpp | has a backward branch (often a loop) |
| `0x587ec0` | 1552 | 5 | `shape only` | has a backward branch (often a loop), 394 ins | has a backward branch (often a loop) |
| `0x5f73c0` | 1549 | 2 | `shape only` | has a backward branch (often a loop), 347 ins | has a backward branch (often a loop) |
| `0x1a1810` | 1545 | 2 | `strings` | p.first  \| nb_strips  | has a backward branch (often a loop) |
| `0x60d380` | 1536 | 2 | `strings` | no COFF symbols \| magic number in optional header not reco | has a backward branch (often a loop) |
| `0x776940` | 1530 | 2 | `strings` | VSH \| basic_string::_M_construct null not vali | has a backward branch (often a loop) |
| `0x1506a0` | 1527 | 3 | `shape only` | has a backward branch (often a loop), 324 ins | has a backward branch (often a loop) |
| `0x6270b0` | 1526 | 4 | `shape only` | has a backward branch (often a loop), 420 ins | has a backward branch (often a loop) |
| `0x7ee7b0` | 1526 | 3 | `strings` | ..\tiling\optimizer.cpp \| !best.empty() | has a backward branch (often a loop) |
| `0x535660` | 1525 | 2 | `shape only` | has a backward branch (often a loop), 375 ins | has a backward branch (often a loop) |
| `0x625920` | 1524 | 3 | `strings` | string literal \| std | has a backward branch (often a loop) |
| `0x70fbe0` | 1517 | 3 | `shape only` | has a backward branch (often a loop), 399 ins | has a backward branch (often a loop) |
| `0x710f60` | 1517 | 3 | `shape only` | has a backward branch (often a loop), 399 ins | has a backward branch (often a loop) |
| `0x54f5d0` | 1516 | 2 | `shape only` | has a backward branch (often a loop), 353 ins | has a backward branch (often a loop) |
| `0x94ca90` | 1512 | 3 | `shape only` | has a backward branch (often a loop), 344 ins | has a backward branch (often a loop) |
| `0x8eab20` | 1506 | 3 | `shape only` | has a backward branch (often a loop), 334 ins | has a backward branch (often a loop) |
| `0x52be50` | 1505 | 5 | `shape only` | has a backward branch (often a loop), 342 ins | has a backward branch (often a loop) |
| `0x5d6a90` | 1502 | 6 | `strings` | VERTEX \| 0.0 | has a backward branch (often a loop) |
| `0x94a30` | 1501 | 2 | `shape only` | has a backward branch (often a loop), 352 ins | has a backward branch (often a loop) |
| `0x163bb0` | 1498 | 3 | `shape only` | has a backward branch (often a loop), 369 ins | has a backward branch (often a loop) |
| `0x54a350` | 1497 | 3 | `shape only` | has a backward branch (often a loop), 372 ins | has a backward branch (often a loop) |
| `0x9285e0` | 1495 | 3 | `shape only` | has a backward branch (often a loop), 420 ins | has a backward branch (often a loop) |
| `0x938000` | 1495 | 2 | `shape only` | has a backward branch (often a loop), 420 ins | has a backward branch (often a loop) |
| `0x939e00` | 1495 | 22 | `shape only` | has a backward branch (often a loop), 420 ins | has a backward branch (often a loop) |
| `0x941e20` | 1495 | 2 | `shape only` | has a backward branch (often a loop), 420 ins | has a backward branch (often a loop) |
| `0x535090` | 1486 | 3 | `shape only` | has a backward branch (often a loop), 397 ins | has a backward branch (often a loop) |
| `0x576cd0` | 1481 | 4 | `shape only` | has a backward branch (often a loop), 336 ins | has a backward branch (often a loop) |
| `0x22e390` | 1478 | 19 | `shape only` | has a backward branch (often a loop), 408 ins | has a backward branch (often a loop) |
| `0x94ae70` | 1465 | 2 | `shape only` | has a backward branch (often a loop), 274 ins | has a backward branch (often a loop) |
| `0x935f30` | 1464 | 2 | `shape only` | has a backward branch (often a loop), 347 ins | has a backward branch (often a loop) |
| `0x6bf660` | 1462 | 2 | `shape only` | has a backward branch (often a loop), 384 ins | has a backward branch (often a loop) |
| `0x952970` | 1461 | 2 | `shape only` | has a backward branch (often a loop), 388 ins | has a backward branch (often a loop) |
| `0x233990` | 1459 | 2 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x973890` | 1455 | 3 | `shape only` | has a backward branch (often a loop), 344 ins | has a backward branch (often a loop) |
| `0x1918d0` | 1448 | 5 | `shape only` | has a backward branch (often a loop), 349 ins | has a backward branch (often a loop) |
| `0x2072f0` | 1446 | 4 | `shape only` | has a backward branch (often a loop), 329 ins | has a backward branch (often a loop) |
| `0x247b30` | 1445 | 2 | `shape only` | has a backward branch (often a loop), 334 ins | has a backward branch (often a loop) |
| `0x7f2ae0` | 1445 | 6 | `shape only` | has a backward branch (often a loop), 316 ins | has a backward branch (often a loop) |
| `0x1fd820` | 1443 | 2 | `shape only` | has a backward branch (often a loop), 336 ins | has a backward branch (often a loop) |
| `0x72e930` | 1442 | 2 | `shape only` | has a backward branch (often a loop), 227 ins | has a backward branch (often a loop) |
| `0x72eee0` | 1442 | 2 | `shape only` | has a backward branch (often a loop), 227 ins | has a backward branch (often a loop) |
| `0x8ba70` | 1436 | 2 | `strings` | ..\multi\marker.cpp \| problem.mark_properties().size > 0.0 | has a backward branch (often a loop) |
| `0x4f67e0` | 1436 | 2 | `shape only` | has a backward branch (often a loop), 362 ins | has a backward branch (often a loop) |
| `0x1d47a0` | 1429 | 2 | `shape only` | has a backward branch (often a loop), 371 ins | has a backward branch (often a loop) |
| `0x1a3db0` | 1427 | 2 | `strings` | part.geometric_infos().hull().size() ==  \| ..\nesting\algos\algo_parameters.cpp | has a backward branch (often a loop) |
| `0x54ba40` | 1425 | 2 | `shape only` | has a backward branch (often a loop), 306 ins | has a backward branch (often a loop) |
| `0x8721a0` | 1423 | 1 | `shape only` | straight line / call sequence, 398 ins | straight line / call sequence |
| `0x872730` | 1423 | 1 | `shape only` | straight line / call sequence, 398 ins | straight line / call sequence |
| `0x60f7e0` | 1422 | 7 | `strings` | .exe \| .com | has a backward branch (often a loop) |
| `0x937a70` | 1420 | 2 | `shape only` | has a backward branch (often a loop), 359 ins | has a backward branch (often a loop) |
| `0x5884d0` | 1419 | 9 | `shape only` | has a backward branch (often a loop), 354 ins | has a backward branch (often a loop) |
| `0x56fab0` | 1418 | 3 | `strings` | ERROR.... | has a backward branch (often a loop) |
| `0x233f50` | 1414 | 8 | `shape only` | has a backward branch (often a loop), 334 ins | has a backward branch (often a loop) |
| `0xaf7d0` | 1413 | 2 | `shape only` | has a backward branch (often a loop), 340 ins | has a backward branch (often a loop) |
| `0x8d5dd0` | 1413 | 3 | `shape only` | has a backward branch (often a loop), 297 ins | has a backward branch (often a loop) |
| `0x6c78f0` | 1411 | 2 | `strings` | ../utils/evaluated_object.hpp \| inserted | has a backward branch (often a loop) |
| `0x6af890` | 1407 | 1 | `shape only` | straight line / call sequence, 389 ins | straight line / call sequence |
| `0x6b75e0` | 1407 | 1 | `shape only` | straight line / call sequence, 389 ins | straight line / call sequence |
| `0x4d260` | 1401 | 2 | `strings` | basic_string::_M_construct null not vali \| basic_string::append | has a backward branch (often a loop) |
| `0x4e3950` | 1397 | 2 | `shape only` | has a backward branch (often a loop), 290 ins | has a backward branch (often a loop) |
| `0x971340` | 1397 | 2 | `shape only` | has a backward branch (often a loop), 294 ins | has a backward branch (often a loop) |
| `0x9718c0` | 1397 | 2 | `shape only` | has a backward branch (often a loop), 294 ins | has a backward branch (often a loop) |
| `0x8cd50` | 1396 | 2 | `shape only` | has a backward branch (often a loop), 321 ins | has a backward branch (often a loop) |
| `0x161cd0` | 1394 | 3 | `shape only` | has a backward branch (often a loop), 341 ins | has a backward branch (often a loop) |
| `0x8c7310` | 1390 | 2 | `shape only` | has a backward branch (often a loop), 370 ins | has a backward branch (often a loop) |
| `0x225460` | 1389 | 2 | `shape only` | has a backward branch (often a loop), 358 ins | has a backward branch (often a loop) |
| `0x5b2cc0` | 1388 | 5 | `shape only` | has a backward branch (often a loop), 297 ins | has a backward branch (often a loop) |
| `0x4dd300` | 1385 | 8 | `shape only` | has a backward branch (often a loop), 267 ins | has a backward branch (often a loop) |
| `0x1baf20` | 1382 | 6 | `shape only` | has a backward branch (often a loop), 344 ins | has a backward branch (often a loop) |
| `0x18e2a0` | 1380 | 3 | `shape only` | has a backward branch (often a loop), 314 ins | has a backward branch (often a loop) |
| `0x4f1020` | 1380 | 2 | `shape only` | has a backward branch (often a loop), 315 ins | has a backward branch (often a loop) |
| `0x2605f0` | 1378 | 3 | `shape only` | has a backward branch (often a loop), 304 ins | has a backward branch (often a loop) |
| `0x5634d0` | 1378 | 3 | `shape only` | has a backward branch (often a loop), 265 ins | has a backward branch (often a loop) |
| `0x4e3330` | 1377 | 4 | `shape only` | has a backward branch (often a loop), 308 ins | has a backward branch (often a loop) |
| `0x59d30` | 1373 | 2 | `strings` | ..\multi\database.cpp \| sheet | has a backward branch (often a loop) |
| `0x161240` | 1373 | 2 | `shape only` | has a backward branch (often a loop), 298 ins | has a backward branch (often a loop) |
| `0x22da70` | 1373 | 5 | `shape only` | has a backward branch (often a loop), 265 ins | has a backward branch (often a loop) |
| `0x5894e0` | 1372 | 2 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x986cc0` | 1371 | 11 | `shape only` | has a backward branch (often a loop), 332 ins | has a backward branch (often a loop) |
| `0x4d0950` | 1370 | 2 | `shape only` | has a backward branch (often a loop), 340 ins | has a backward branch (often a loop) |
| `0x54c640` | 1370 | 2 | `shape only` | has a backward branch (often a loop), 316 ins | has a backward branch (often a loop) |
| `0x561c40` | 1369 | 2 | `shape only` | has a backward branch (often a loop), 318 ins | has a backward branch (often a loop) |
| `0x2631f0` | 1365 | 3 | `shape only` | has a backward branch (often a loop), 320 ins | has a backward branch (often a loop) |
| `0x4bb9b0` | 1364 | 2 | `shape only` | has a backward branch (often a loop), 283 ins | has a backward branch (often a loop) |
| `0x5df6f0` | 1363 | 9 | `shape only` | has a backward branch (often a loop), 321 ins | has a backward branch (often a loop) |
| `0x7b2a60` | 1362 | 2 | `shape only` | has a backward branch (often a loop), 377 ins | has a backward branch (often a loop) |
| `0x50ac80` | 1357 | 3 | `strings` | !!! Error extracting infos for  \| !!! | has a backward branch (often a loop) |
| `0x150ca0` | 1352 | 2 | `shape only` | has a backward branch (often a loop), 291 ins | has a backward branch (often a loop) |
| `0x4e8e50` | 1349 | 3 | `shape only` | has a backward branch (often a loop), 280 ins | has a backward branch (often a loop) |
| `0x1d7160` | 1348 | 2 | `shape only` | has a backward branch (often a loop), 273 ins | has a backward branch (often a loop) |
| `0x564060` | 1348 | 2 | `shape only` | has a backward branch (often a loop), 308 ins | has a backward branch (often a loop) |
| `0x6dd900` | 1348 | 22 | `shape only` | has a backward branch (often a loop), 273 ins | has a backward branch (often a loop) |
| `0x24e3f0` | 1345 | 2 | `shape only` | has a backward branch (often a loop), 275 ins | has a backward branch (often a loop) |
| `0x62d100` | 1338 | 3 | `strings` | _GLOBAL_ | has a backward branch (often a loop) |
| `0x6bcf60` | 1336 | 3 | `shape only` | has a backward branch (often a loop), 303 ins | has a backward branch (often a loop) |
| `0x4df310` | 1335 | 4 | `shape only` | has a backward branch (often a loop), 282 ins | has a backward branch (often a loop) |
| `0x7ec460` | 1335 | 3 | `shape only` | has a backward branch (often a loop), 290 ins | has a backward branch (often a loop) |
| `0x660010` | 1334 | 8 | `shape only` | straight line / call sequence, 234 ins | straight line / call sequence |
| `0x68a1a0` | 1334 | 2 | `strings` | raw_evaluation_ratio_100 \| raw_evaluation_ratio_10 | has a backward branch (often a loop) |
| `0x926e80` | 1331 | 2 | `shape only` | has a backward branch (often a loop), 313 ins | has a backward branch (often a loop) |
| `0x1b0220` | 1329 | 3 | `shape only` | has a backward branch (often a loop), 305 ins | has a backward branch (often a loop) |
| `0x4faaf0` | 1326 | 3 | `shape only` | has a backward branch (often a loop), 328 ins | has a backward branch (often a loop) |
| `0x975e90` | 1325 | 2 | `shape only` | has a backward branch (often a loop), 327 ins | has a backward branch (often a loop) |
| `0x525e0` | 1316 | 2 | `strings` | production_cost > 0.0 \| ..\multi\database.cpp | has a backward branch (often a loop) |
| `0x5ff5a0` | 1315 | 3 | `shape only` | has a backward branch (often a loop), 359 ins | has a backward branch (often a loop) |
| `0x141f90` | 1313 | 3 | `shape only` | has a backward branch (often a loop), 284 ins | has a backward branch (often a loop) |
| `0x70d610` | 1313 | 2 | `shape only` | has a backward branch (often a loop), 277 ins | has a backward branch (often a loop) |
| `0x13be60` | 1312 | 2 | `shape only` | has a backward branch (often a loop), 287 ins | has a backward branch (often a loop) |
| `0x25f890` | 1302 | 5 | `shape only` | has a backward branch (often a loop), 250 ins | has a backward branch (often a loop) |
| `0x5c66c0` | 1298 | 10 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x54d130` | 1297 | 3 | `shape only` | has a backward branch (often a loop), 306 ins | has a backward branch (often a loop) |
| `0x5f6620` | 1297 | 2 | `strings` | %lf \| basic_string::append | has a backward branch (often a loop) |
| `0x9683b0` | 1297 | 4 | `shape only` | has a backward branch (often a loop), 251 ins | has a backward branch (often a loop) |
| `0x5c3820` | 1295 | 8 | `shape only` | has a backward branch (often a loop), 282 ins | has a backward branch (often a loop) |
| `0x5f9d30` | 1295 | 2 | `shape only` | has a backward branch (often a loop), 299 ins | has a backward branch (often a loop) |
| `0x956570` | 1294 | 3 | `shape only` | has a backward branch (often a loop), 303 ins | has a backward branch (often a loop) |
| `0x5336b0` | 1293 | 3 | `shape only` | has a backward branch (often a loop), 347 ins | has a backward branch (often a loop) |
| `0x3010e0` | 1289 | 10 | `shape only` | has a backward branch (often a loop), 189 ins | has a backward branch (often a loop) |
| `0xa3900` | 1288 | 2 | `shape only` | has a backward branch (often a loop), 278 ins | has a backward branch (often a loop) |
| `0x961b10` | 1285 | 3 | `shape only` | has a backward branch (often a loop), 310 ins | has a backward branch (often a loop) |
| `0x531f70` | 1281 | 2 | `shape only` | has a backward branch (often a loop), 335 ins | has a backward branch (often a loop) |
| `0x70f450` | 1281 | 7 | `shape only` | has a backward branch (often a loop), 247 ins | has a backward branch (often a loop) |
| `0x7107d0` | 1281 | 7 | `shape only` | has a backward branch (often a loop), 247 ins | has a backward branch (often a loop) |
| `0x13f430` | 1276 | 5 | `shape only` | has a backward branch (often a loop), 273 ins | has a backward branch (often a loop) |
| `0x8fa70` | 1275 | 2 | `shape only` | has a backward branch (often a loop), 296 ins | has a backward branch (often a loop) |
| `0x2393f0` | 1275 | 5 | `shape only` | has a backward branch (often a loop), 306 ins | has a backward branch (often a loop) |
| `0x1a4420` | 1274 | 2 | `shape only` | has a backward branch (often a loop), 275 ins | has a backward branch (often a loop) |
| `0x8ca600` | 1273 | 2 | `shape only` | has a backward branch (often a loop), 349 ins | has a backward branch (often a loop) |
| `0x8e8db0` | 1273 | 2 | `shape only` | has a backward branch (often a loop), 311 ins | has a backward branch (often a loop) |
| `0x5f6b40` | 1270 | 2 | `strings` | basic_string::append \| ' is not a number. | has a backward branch (often a loop) |
| `0xaac40` | 1269 | 3 | `strings` | strategy \| FloatFilled | has a backward branch (often a loop) |
| `0x958460` | 1267 | 2 | `shape only` | has a backward branch (often a loop), 337 ins | has a backward branch (often a loop) |
| `0x958960` | 1267 | 2 | `shape only` | has a backward branch (often a loop), 337 ins | has a backward branch (often a loop) |
| `0x959d10` | 1267 | 2 | `shape only` | has a backward branch (often a loop), 337 ins | has a backward branch (often a loop) |
| `0x63ac50` | 1263 | 2 | `strings` | NaN \| Inf | has a backward branch (often a loop) |
| `0x18efc0` | 1261 | 2 | `shape only` | has a backward branch (often a loop), 315 ins | has a backward branch (often a loop) |
| `0x81e330` | 1261 | 5 | `shape only` | has a backward branch (often a loop), 266 ins | has a backward branch (often a loop) |
| `0x81e820` | 1261 | 6 | `shape only` | has a backward branch (often a loop), 266 ins | has a backward branch (often a loop) |
| `0x8e9cc0` | 1257 | 3 | `shape only` | has a backward branch (often a loop), 317 ins | has a backward branch (often a loop) |
| `0x17a680` | 1253 | 9 | `shape only` | has a backward branch (often a loop), 281 ins | has a backward branch (often a loop) |
| `0x1b9fd0` | 1253 | 4 | `shape only` | has a backward branch (often a loop), 325 ins | has a backward branch (often a loop) |
| `0x5d2a60` | 1253 | 3 | `shape only` | has a backward branch (often a loop), 300 ins | has a backward branch (often a loop) |
| `0x93e2c0` | 1252 | 2 | `shape only` | has a backward branch (often a loop), 302 ins | has a backward branch (often a loop) |
| `0x956080` | 1249 | 2 | `shape only` | has a backward branch (often a loop), 302 ins | has a backward branch (often a loop) |
| `0x1d870` | 1248 | 4 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x4edd00` | 1248 | 2 | `shape only` | has a backward branch (often a loop), 217 ins | has a backward branch (often a loop) |
| `0x9269a0` | 1241 | 4 | `shape only` | has a backward branch (often a loop), 314 ins | has a backward branch (often a loop) |
| `0x4ea9c0` | 1240 | 2 | `shape only` | has a backward branch (often a loop), 192 ins | has a backward branch (often a loop) |
| `0x1d3330` | 1239 | 2 | `shape only` | has a backward branch (often a loop), 350 ins | has a backward branch (often a loop) |
| `0x9759b0` | 1237 | 2 | `shape only` | has a backward branch (often a loop), 293 ins | has a backward branch (often a loop) |
| `0x86160` | 1234 | 3 | `strings` | __small_mark__ \| __big_mark__ | has a backward branch (often a loop) |
| `0x927630` | 1234 | 2 | `shape only` | has a backward branch (often a loop), 289 ins | has a backward branch (often a loop) |
| `0x17f4b0` | 1231 | 3 | `shape only` | has a backward branch (often a loop), 304 ins | has a backward branch (often a loop) |
| `0x957870` | 1231 | 2 | `shape only` | has a backward branch (often a loop), 291 ins | has a backward branch (often a loop) |
| `0x4de050` | 1224 | 2 | `shape only` | has a backward branch (often a loop), 264 ins | has a backward branch (often a loop) |
| `0x67f330` | 1220 | 5 | `strings` | MULTIPOLYGON | has a backward branch (often a loop) |
| `0x8d9ce0` | 1220 | 7 | `shape only` | has a backward branch (often a loop), 273 ins | has a backward branch (often a loop) |
| `0x57bd20` | 1217 | 2 | `shape only` | has a backward branch (often a loop), 304 ins | has a backward branch (often a loop) |
| `0x5c4140` | 1217 | 2 | `shape only` | has a backward branch (often a loop), 296 ins | has a backward branch (often a loop) |
| `0x53cc30` | 1215 | 2 | `strings` | vector::_M_range_check: __n (which is %z \| !torch_configs.empty() | has a backward branch (often a loop) |
| `0x9334f0` | 1214 | 2 | `shape only` | has a backward branch (often a loop), 321 ins | has a backward branch (often a loop) |
| `0x55e2c0` | 1211 | 2 | `shape only` | has a backward branch (often a loop), 237 ins | has a backward branch (often a loop) |
| `0x1a9b50` | 1190 | 2 | `strings` | basic_string::append \| before | has a backward branch (often a loop) |
| `0x8d9830` | 1189 | 2 | `shape only` | has a backward branch (often a loop), 266 ins | has a backward branch (often a loop) |
| `0x8da1b0` | 1189 | 2 | `shape only` | has a backward branch (often a loop), 266 ins | has a backward branch (often a loop) |
| `0x8d7740` | 1186 | 8 | `shape only` | has a backward branch (often a loop), 292 ins | has a backward branch (often a loop) |
| `0x5ed3d0` | 1183 | 5 | `shape only` | has a backward branch (often a loop), 241 ins | has a backward branch (often a loop) |
| `0x179db0` | 1180 | 2 | `shape only` | has a backward branch (often a loop), 286 ins | has a backward branch (often a loop) |
| `0x8b6d60` | 1179 | 2 | `shape only` | has a backward branch (often a loop), 328 ins | has a backward branch (often a loop) |
| `0x953da0` | 1171 | 2 | `shape only` | has a backward branch (often a loop), 280 ins | has a backward branch (often a loop) |
| `0x5fd100` | 1170 | 5 | `strings` | vector::reserve \| basic_string::_M_construct null not vali | has a backward branch (often a loop) |
| `0x19f1f0` | 1168 | 2 | `shape only` | has a backward branch (often a loop), 257 ins | has a backward branch (often a loop) |
| `0x24e940` | 1164 | 2 | `shape only` | has a backward branch (often a loop), 258 ins | has a backward branch (often a loop) |
| `0x8f97e0` | 1164 | 1 | `shape only` | has a backward branch (often a loop), 316 ins | has a backward branch (often a loop) |
| `0x953460` | 1160 | 2 | `shape only` | has a backward branch (often a loop), 321 ins | has a backward branch (often a loop) |
| `0x15a9e0` | 1157 | 2 | `shape only` | has a backward branch (often a loop), 290 ins | has a backward branch (often a loop) |
| `0x9787d0` | 1152 | 2 | `shape only` | has a backward branch (often a loop), 293 ins | has a backward branch (often a loop) |
| `0x5528b0` | 1151 | 4 | `shape only` | has a backward branch (often a loop), 271 ins | has a backward branch (often a loop) |
| `0x89c4c0` | 1151 | 3 | `shape only` | has a backward branch (often a loop), 318 ins | has a backward branch (often a loop) |
| `0x89c940` | 1151 | 3 | `shape only` | has a backward branch (often a loop), 318 ins | has a backward branch (often a loop) |
| `0x24efa0` | 1149 | 3 | `shape only` | has a backward branch (often a loop), 249 ins | has a backward branch (often a loop) |
| `0x8e9840` | 1138 | 2 | `shape only` | has a backward branch (often a loop), 290 ins | has a backward branch (often a loop) |
| `0x566df0` | 1135 | 2 | `shape only` | has a backward branch (often a loop), 208 ins | has a backward branch (often a loop) |
| `0x98820` | 1133 | 2 | `shape only` | has a backward branch (often a loop), 290 ins | has a backward branch (often a loop) |
| `0x259e80` | 1133 | 6 | `shape only` | has a backward branch (often a loop), 256 ins | has a backward branch (often a loop) |
| `0x1d2270` | 1132 | 2 | `shape only` | has a backward branch (often a loop), 236 ins | has a backward branch (often a loop) |
| `0x2480e0` | 1132 | 2 | `shape only` | has a backward branch (often a loop), 285 ins | has a backward branch (often a loop) |
| `0x5e8870` | 1132 | 4 | `shape only` | has a backward branch (often a loop), 264 ins | has a backward branch (often a loop) |
| `0x1837e0` | 1130 | 4 | `shape only` | has a backward branch (often a loop), 277 ins | has a backward branch (often a loop) |
| `0x1bbd90` | 1130 | 4 | `shape only` | has a backward branch (often a loop), 259 ins | has a backward branch (often a loop) |
| `0x874dd0` | 1130 | 7 | `strings` | %m/%d/%y \| %H:%M:%S | has a backward branch (often a loop) |
| `0x875640` | 1130 | 7 | `shape only` | has a backward branch (often a loop), 154 ins | has a backward branch (often a loop) |
| `0x8bbf70` | 1125 | 2 | `shape only` | has a backward branch (often a loop), 262 ins | has a backward branch (often a loop) |
| `0x1acf30` | 1121 | 3 | `strings` | ..\nesting\algos\multinesting_optimizer. \| nestings.size() == before_size | has a backward branch (often a loop) |
| `0x13e0e0` | 1120 | 4 | `shape only` | has a backward branch (often a loop), 258 ins | has a backward branch (often a loop) |
| `0x15cd60` | 1118 | 5 | `shape only` | has a backward branch (often a loop), 237 ins | has a backward branch (often a loop) |
| `0x95e660` | 1118 | 2 | `shape only` | has a backward branch (often a loop), 291 ins | has a backward branch (often a loop) |
| `0x2007d0` | 1117 | 8 | `shape only` | has a backward branch (often a loop), 293 ins | has a backward branch (often a loop) |
| `0x2b8e30` | 1112 | 5 | `strings` | ClpDefaultName | has a backward branch (often a loop) |
| `0x196c30` | 1111 | 3 | `shape only` | has a backward branch (often a loop), 269 ins | has a backward branch (often a loop) |
| `0x4e4600` | 1106 | 3 | `shape only` | has a backward branch (often a loop), 254 ins | has a backward branch (often a loop) |
| `0x870070` | 1106 | 2 | `callers` | called by 0x2ab0 LaunchLocalComputation; 0x6100 LaunchComputation | has a backward branch (often a loop) |
| `0x5271a0` | 1102 | 2 | `shape only` | has a backward branch (often a loop), 253 ins | has a backward branch (often a loop) |
| `0x961150` | 1101 | 2 | `shape only` | has a backward branch (often a loop), 253 ins | has a backward branch (often a loop) |
| `0x97b860` | 1101 | 3 | `shape only` | has a backward branch (often a loop), 235 ins | has a backward branch (often a loop) |
| `0x2517b0` | 1099 | 2 | `shape only` | has a backward branch (often a loop), 239 ins | has a backward branch (often a loop) |
| `0x906b60` | 1099 | 2 | `shape only` | has a backward branch (often a loop), 284 ins | has a backward branch (often a loop) |
| `0x98050` | 1098 | 2 | `shape only` | has a backward branch (often a loop), 280 ins | has a backward branch (often a loop) |
| `0x7c73a0` | 1095 | 3 | `shape only` | has a backward branch (often a loop), 242 ins | has a backward branch (often a loop) |
| `0x555f70` | 1089 | 2 | `shape only` | has a backward branch (often a loop), 246 ins | has a backward branch (often a loop) |
| `0x72e120` | 1089 | 3 | `shape only` | straight line / call sequence, 167 ins | straight line / call sequence |
| `0x8f8cb0` | 1087 | 2 | `shape only` | has a backward branch (often a loop), 292 ins | has a backward branch (often a loop) |
| `0x171bd0` | 1084 | 3 | `shape only` | has a backward branch (often a loop), 222 ins | has a backward branch (often a loop) |
| `0x1a3900` | 1083 | 4 | `shape only` | has a backward branch (often a loop), 214 ins | has a backward branch (often a loop) |
| `0x8dff50` | 1083 | 2 | `shape only` | has a backward branch (often a loop), 272 ins | has a backward branch (often a loop) |
| `0x146d40` | 1082 | 2 | `shape only` | has a backward branch (often a loop), 243 ins | has a backward branch (often a loop) |
| `0x54b600` | 1081 | 3 | `shape only` | has a backward branch (often a loop), 257 ins | has a backward branch (often a loop) |
| `0x589cc0` | 1081 | 6 | `shape only` | has a backward branch (often a loop), 291 ins | has a backward branch (often a loop) |
| `0x63ef0` | 1078 | 2 | `shape only` | has a backward branch (often a loop), 248 ins | has a backward branch (often a loop) |
| `0x9763c0` | 1076 | 2 | `shape only` | has a backward branch (often a loop), 257 ins | has a backward branch (often a loop) |
| `0x1ad3a0` | 1073 | 3 | `strings` | ..\nesting\algos\multinesting_optimizer. \| nestings.size() == before_size | has a backward branch (often a loop) |
| `0x1ad7e0` | 1073 | 3 | `strings` | ..\nesting\algos\multinesting_optimizer. \| nestings.size() == before_size | has a backward branch (often a loop) |
| `0x7b56c0` | 1073 | 2 | `strings` | ..\nesting\algos\bucket_manager.hpp \| slices_width.size() > 0 | has a backward branch (often a loop) |
| `0x2610e0` | 1072 | 2 | `shape only` | has a backward branch (often a loop), 244 ins | has a backward branch (often a loop) |
| `0x527bf0` | 1072 | 3 | `shape only` | has a backward branch (often a loop), 227 ins | has a backward branch (often a loop) |
| `0x3d1e0` | 1071 | 2 | `shape only` | has a backward branch (often a loop), 248 ins | has a backward branch (often a loop) |
| `0x81700` | 1071 | 2 | `shape only` | has a backward branch (often a loop), 284 ins | has a backward branch (often a loop) |
| `0x4b47e0` | 1067 | 15 | `shape only` | has a backward branch (often a loop), 286 ins | has a backward branch (often a loop) |
| `0x960210` | 1066 | 3 | `shape only` | has a backward branch (often a loop), 265 ins | has a backward branch (often a loop) |
| `0x253e0` | 1062 | 3 | `shape only` | has a backward branch (often a loop), 246 ins | has a backward branch (often a loop) |
| `0x17a250` | 1058 | 4 | `shape only` | has a backward branch (often a loop), 266 ins | has a backward branch (often a loop) |
| `0x19f8f0` | 1057 | 2 | `shape only` | has a backward branch (often a loop), 251 ins | has a backward branch (often a loop) |
| `0x524ee0` | 1054 | 23 | `strings` | @y\| | has a backward branch (often a loop) |
| `0x1a2cd0` | 1053 | 2 | `shape only` | has a backward branch (often a loop), 211 ins | has a backward branch (often a loop) |
| `0x680870` | 1052 | 2 | `shape only` | has a backward branch (often a loop), 213 ins | has a backward branch (often a loop) |
| `0x60cf60` | 1050 | 2 | `shape only` | has a backward branch (often a loop), 267 ins | has a backward branch (often a loop) |
| `0x54bfe0` | 1047 | 5 | `shape only` | has a backward branch (often a loop), 242 ins | has a backward branch (often a loop) |
| `0x4b9490` | 1046 | 2 | `shape only` | has a backward branch (often a loop), 235 ins | has a backward branch (often a loop) |
| `0x51d4c0` | 1044 | 5 | `strings` | SHEET NOT FOUND:  \| PART NOT FOUND:  | has a backward branch (often a loop) |
| `0x523a40` | 1044 | 7 | `shape only` | has a backward branch (often a loop), 264 ins | has a backward branch (often a loop) |
| `0x557240` | 1044 | 2 | `shape only` | has a backward branch (often a loop), 273 ins | has a backward branch (often a loop) |
| `0x6bb0e0` | 1043 | 2 | `shape only` | has a backward branch (often a loop), 274 ins | has a backward branch (often a loop) |
| `0x4dc640` | 1042 | 22 | `shape only` | has a backward branch (often a loop), 252 ins | has a backward branch (often a loop) |
| `0x6b1150` | 1039 | 2 | `shape only` | has a backward branch (often a loop), 258 ins | has a backward branch (often a loop) |
| `0x5f8860` | 1035 | 4 | `shape only` | has a backward branch (often a loop), 244 ins | has a backward branch (often a loop) |
| `0x8db620` | 1035 | 4 | `shape only` | has a backward branch (often a loop), 240 ins | has a backward branch (often a loop) |
| `0x52dbb0` | 1031 | 5 | `shape only` | has a backward branch (often a loop), 263 ins | has a backward branch (often a loop) |
| `0x52e3d0` | 1029 | 2 | `shape only` | has a backward branch (often a loop), 264 ins | has a backward branch (often a loop) |
| `0x1eaac0` | 1028 | 2 | `shape only` | has a backward branch (often a loop), 237 ins | has a backward branch (often a loop) |
| `0x4e54d0` | 1028 | 3 | `shape only` | has a backward branch (often a loop), 259 ins | has a backward branch (often a loop) |
| `0x951ca0` | 1027 | 2 | `shape only` | has a backward branch (often a loop), 257 ins | has a backward branch (often a loop) |
| `0x970050` | 1026 | 2 | `shape only` | has a backward branch (often a loop), 245 ins | has a backward branch (often a loop) |
| `0x61930` | 1025 | 2 | `shape only` | has a backward branch (often a loop), 228 ins | has a backward branch (often a loop) |
| `0x997f90` | 1024 | 2 | `shape only` | has a backward branch (often a loop), 242 ins | has a backward branch (often a loop) |
| `0x51f070` | 1021 | 2 | `shape only` | has a backward branch (often a loop), 210 ins | has a backward branch (often a loop) |
| `0x520a30` | 1019 | 3 | `strings` | sheet \| ..\structure\stats.cpp | has a backward branch (often a loop) |
| `0x509a40` | 1018 | 2 | `strings` | ..\structure\text_io.cpp \| common_cut | has a backward branch (often a loop) |
| `0x202aa0` | 1017 | 3 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x65df10` | 1012 | 3 | `shape only` | has a backward branch (often a loop), 284 ins | has a backward branch (often a loop) |
| `0x7c1dc0` | 1012 | 3 | `shape only` | has a backward branch (often a loop), 181 ins | has a backward branch (often a loop) |
| `0x935190` | 1011 | 2 | `shape only` | has a backward branch (often a loop), 255 ins | has a backward branch (often a loop) |
| `0x62130` | 1009 | 6 | `shape only` | has a backward branch (often a loop), 224 ins | has a backward branch (often a loop) |
| `0x5ce350` | 1008 | 2 | `shape only` | has a backward branch (often a loop), 189 ins | has a backward branch (often a loop) |
| `0x95f8d0` | 1008 | 2 | `shape only` | has a backward branch (often a loop), 263 ins | has a backward branch (often a loop) |
| `0x1e480` | 1007 | 4 | `shape only` | has a backward branch (often a loop), 244 ins | has a backward branch (often a loop) |
| `0x4ef300` | 1004 | 4 | `shape only` | straight line / call sequence, 211 ins | straight line / call sequence |
| `0x8fb140` | 1004 | 3 | `shape only` | has a backward branch (often a loop), 270 ins | has a backward branch (often a loop) |
| `0x510c90` | 1002 | 2 | `strings` | ... \| mixed  | has a backward branch (often a loop) |
| `0x4fa700` | 1001 | 4 | `shape only` | has a backward branch (often a loop), 250 ins | has a backward branch (often a loop) |
| `0x9571b0` | 999 | 2 | `shape only` | has a backward branch (often a loop), 262 ins | has a backward branch (often a loop) |
| `0x8c930` | 998 | 2 | `shape only` | has a backward branch (often a loop), 251 ins | has a backward branch (often a loop) |
| `0x162280` | 996 | 2 | `shape only` | has a backward branch (often a loop), 210 ins | has a backward branch (often a loop) |
| `0x66ffa0` | 996 | 2 | `shape only` | has a backward branch (often a loop), 280 ins | has a backward branch (often a loop) |
| `0x201d00` | 995 | 3 | `shape only` | has a backward branch (often a loop), 257 ins | has a backward branch (often a loop) |
| `0x146950` | 994 | 3 | `shape only` | has a backward branch (often a loop), 214 ins | has a backward branch (often a loop) |
| `0x775fb0` | 994 | 3 | `shape only` | has a backward branch (often a loop), 166 ins | has a backward branch (often a loop) |
| `0x520e30` | 992 | 3 | `strings` | sheet \| ..\structure\stats.cpp | has a backward branch (often a loop) |
| `0x5471a0` | 992 | 3 | `shape only` | has a backward branch (often a loop), 234 ins | has a backward branch (often a loop) |
| `0x626bf0` | 991 | 4 | `shape only` | has a backward branch (often a loop), 284 ins | has a backward branch (often a loop) |
| `0x4f1740` | 989 | 6 | `shape only` | has a backward branch (often a loop), 232 ins | has a backward branch (often a loop) |
| `0x261810` | 988 | 8 | `shape only` | has a backward branch (often a loop), 233 ins | has a backward branch (often a loop) |
| `0x718040` | 986 | 2 | `shape only` | has a backward branch (often a loop), 244 ins | has a backward branch (often a loop) |
| `0x718860` | 986 | 2 | `shape only` | has a backward branch (often a loop), 244 ins | has a backward branch (often a loop) |
| `0x8c2380` | 986 | 6 | `shape only` | has a backward branch (often a loop), 269 ins | has a backward branch (often a loop) |
| `0x8cbb70` | 986 | 3 | `shape only` | has a backward branch (often a loop), 269 ins | has a backward branch (often a loop) |
| `0x1880` | 985 | 2 | `shape only` | has a backward branch (often a loop), 271 ins | has a backward branch (often a loop) |
| `0x55b090` | 985 | 2 | `shape only` | has a backward branch (often a loop), 219 ins | has a backward branch (often a loop) |
| `0x93f280` | 983 | 4 | `shape only` | has a backward branch (often a loop), 277 ins | has a backward branch (often a loop) |
| `0x6e0de0` | 981 | 2 | `shape only` | has a backward branch (often a loop), 238 ins | has a backward branch (often a loop) |
| `0x923ff0` | 980 | 5 | `shape only` | has a backward branch (often a loop), 249 ins | has a backward branch (often a loop) |
| `0x927b10` | 980 | 5 | `shape only` | has a backward branch (often a loop), 249 ins | has a backward branch (often a loop) |
| `0x934080` | 980 | 3 | `shape only` | has a backward branch (often a loop), 249 ins | has a backward branch (often a loop) |
| `0x934db0` | 980 | 2 | `shape only` | has a backward branch (often a loop), 249 ins | has a backward branch (often a loop) |
| `0x936a40` | 980 | 5 | `shape only` | has a backward branch (often a loop), 249 ins | has a backward branch (often a loop) |
| `0x93a500` | 980 | 5 | `shape only` | has a backward branch (often a loop), 249 ins | has a backward branch (often a loop) |
| `0x93dd10` | 980 | 5 | `shape only` | has a backward branch (often a loop), 249 ins | has a backward branch (often a loop) |
| `0x763b10` | 975 | 3 | `shape only` | has a backward branch (often a loop), 189 ins | has a backward branch (often a loop) |
| `0x931830` | 975 | 3 | `shape only` | has a backward branch (often a loop), 268 ins | has a backward branch (often a loop) |
| `0x93e7b0` | 975 | 20 | `shape only` | has a backward branch (often a loop), 268 ins | has a backward branch (often a loop) |
| `0x1c8960` | 973 | 2 | `shape only` | has a backward branch (often a loop), 178 ins | has a backward branch (often a loop) |
| `0x6d3640` | 971 | 2 | `shape only` | has a backward branch (often a loop), 219 ins | has a backward branch (often a loop) |
| `0x57c540` | 970 | 3 | `shape only` | has a backward branch (often a loop), 252 ins | has a backward branch (often a loop) |
| `0x3da580` | 968 | 10 | `shape only` | straight line / call sequence, 142 ins | straight line / call sequence |
| `0x714d40` | 968 | 2 | `shape only` | has a backward branch (often a loop), 244 ins | has a backward branch (often a loop) |
| `0x4cbc50` | 967 | 3 | `shape only` | has a backward branch (often a loop), 253 ins | has a backward branch (often a loop) |
| `0x546d50` | 966 | 3 | `shape only` | has a backward branch (often a loop), 229 ins | has a backward branch (often a loop) |
| `0x6cc580` | 965 | 3 | `shape only` | has a backward branch (often a loop), 249 ins | has a backward branch (often a loop) |
| `0x180100` | 962 | 11 | `shape only` | has a backward branch (often a loop), 248 ins | has a backward branch (often a loop) |
| `0x958090` | 961 | 2 | `shape only` | has a backward branch (often a loop), 224 ins | has a backward branch (often a loop) |
| `0x4d0030` | 960 | 4 | `shape only` | has a backward branch (often a loop), 262 ins | has a backward branch (often a loop) |
| `0x65bc00` | 960 | 3 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x15bfa0` | 958 | 8 | `shape only` | has a backward branch (often a loop), 206 ins | has a backward branch (often a loop) |
| `0x22dfd0` | 957 | 2 | `shape only` | has a backward branch (often a loop), 199 ins | has a backward branch (often a loop) |
| `0x15ddc0` | 956 | 2 | `shape only` | has a backward branch (often a loop), 231 ins | has a backward branch (often a loop) |
| `0x260b60` | 956 | 2 | `shape only` | has a backward branch (often a loop), 201 ins | has a backward branch (often a loop) |
| `0x521210` | 955 | 4 | `strings` | sheet \| ..\structure\stats.cpp | has a backward branch (often a loop) |
| `0x8bc500` | 951 | 2 | `shape only` | has a backward branch (often a loop), 209 ins | has a backward branch (often a loop) |
| `0x5feb70` | 950 | 25 | `strings` | VSH \| Comments must start with / | has a backward branch (often a loop) |
| `0x1c85a0` | 947 | 4 | `shape only` | has a backward branch (often a loop), 264 ins | has a backward branch (often a loop) |
| `0x6c81d0` | 946 | 3 | `strings` | ../utils/evaluated_object.hpp \| inserted | has a backward branch (often a loop) |
| `0x14b470` | 942 | 2 | `shape only` | has a backward branch (often a loop), 249 ins | has a backward branch (often a loop) |
| `0x179820` | 941 | 12 | `shape only` | has a backward branch (often a loop), 280 ins | has a backward branch (often a loop) |
| `0x205a30` | 938 | 3 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x549fa0` | 938 | 2 | `shape only` | has a backward branch (often a loop), 249 ins | has a backward branch (often a loop) |
| `0x62c1c0` | 937 | 3 | `strings` | {default arg# \| }:: | has a backward branch (often a loop) |
| `0x53bf10` | 933 | 2 | `shape only` | has a backward branch (often a loop), 200 ins | has a backward branch (often a loop) |
| `0x57b3d0` | 931 | 2 | `shape only` | has a backward branch (often a loop), 247 ins | has a backward branch (often a loop) |
| `0x62cd50` | 930 | 2 | `strings` | ... \| (... | has a backward branch (often a loop) |
| `0x24df20` | 929 | 2 | `shape only` | has a backward branch (often a loop), 198 ins | has a backward branch (often a loop) |
| `0x5d5800` | 926 | 2 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x70ede0` | 926 | 4 | `shape only` | has a backward branch (often a loop), 192 ins | has a backward branch (often a loop) |
| `0x725440` | 920 | 3 | `shape only` | has a backward branch (often a loop), 260 ins | has a backward branch (often a loop) |
| `0x7c1090` | 919 | 5 | `shape only` | has a backward branch (often a loop), 146 ins | has a backward branch (often a loop) |
| `0x5e0d90` | 918 | 3 | `shape only` | has a backward branch (often a loop), 200 ins | has a backward branch (often a loop) |
| `0x6c5690` | 918 | 3 | `shape only` | has a backward branch (often a loop), 209 ins | has a backward branch (often a loop) |
| `0x21faf0` | 916 | 4 | `shape only` | has a backward branch (often a loop), 204 ins | has a backward branch (often a loop) |
| `0x21fe90` | 916 | 2 | `shape only` | has a backward branch (often a loop), 204 ins | has a backward branch (often a loop) |
| `0x25c640` | 915 | 5 | `shape only` | has a backward branch (often a loop), 202 ins | has a backward branch (often a loop) |
| `0x897c50` | 915 | 2 | `shape only` | has a backward branch (often a loop), 141 ins | has a backward branch (often a loop) |
| `0x20d0a0` | 914 | 3 | `shape only` | has a backward branch (often a loop), 170 ins | has a backward branch (often a loop) |
| `0x7243e0` | 914 | 2 | `shape only` | has a backward branch (often a loop), 206 ins | has a backward branch (often a loop) |
| `0x5c61f0` | 911 | 2 | `shape only` | has a backward branch (often a loop), 225 ins | has a backward branch (often a loop) |
| `0x639e30` | 910 | 4 | `shape only` | has a backward branch (often a loop), 244 ins | has a backward branch (often a loop) |
| `0x25da80` | 909 | 5 | `shape only` | has a backward branch (often a loop), 247 ins | has a backward branch (often a loop) |
| `0x93ad70` | 909 | 3 | `shape only` | has a backward branch (often a loop), 225 ins | has a backward branch (often a loop) |
| `0x5461b0` | 904 | 3 | `shape only` | has a backward branch (often a loop), 202 ins | has a backward branch (often a loop) |
| `0x66f180` | 900 | 21 | `shape only` | has a backward branch (often a loop), 263 ins | has a backward branch (often a loop) |
| `0x984a0` | 895 | 2 | `shape only` | has a backward branch (often a loop), 243 ins | has a backward branch (often a loop) |
| `0x73c990` | 895 | 2 | `shape only` | has a backward branch (often a loop), 188 ins | has a backward branch (often a loop) |
| `0x260000` | 894 | 3 | `shape only` | has a backward branch (often a loop), 209 ins | has a backward branch (often a loop) |
| `0x5393c0` | 894 | 2 | `shape only` | has a backward branch (often a loop), 215 ins | has a backward branch (often a loop) |
| `0x600300` | 894 | 5 | `shape only` | has a backward branch (often a loop), 228 ins | has a backward branch (often a loop) |
| `0x51ecf0` | 893 | 5 | `shape only` | has a backward branch (often a loop), 189 ins | has a backward branch (often a loop) |
| `0x71ffb0` | 892 | 4 | `shape only` | has a backward branch (often a loop), 223 ins | has a backward branch (often a loop) |
| `0x870960` | 892 | 3 | `shape only` | has a backward branch (often a loop), 253 ins | has a backward branch (often a loop) |
| `0x500390` | 891 | 1 | `shape only` | straight line / call sequence, 133 ins | straight line / call sequence |
| `0x5d7810` | 888 | 6 | `strings` | SEQEND | has a backward branch (often a loop) |
| `0x5f7040` | 888 | 2 | `shape only` | has a backward branch (often a loop), 213 ins | has a backward branch (often a loop) |
| `0x11a780` | 886 | 10 | `strings` | UWVSH | has a backward branch (often a loop) |
| `0x598140` | 885 | 8 | `shape only` | has a backward branch (often a loop), 218 ins | has a backward branch (often a loop) |
| `0x8b5a20` | 885 | 3 | `shape only` | has a backward branch (often a loop), 253 ins | has a backward branch (often a loop) |
| `0x687900` | 884 | 2 | `shape only` | has a backward branch (often a loop), 209 ins | has a backward branch (often a loop) |
| `0x8ba000` | 884 | 8 | `shape only` | has a backward branch (often a loop), 167 ins | has a backward branch (often a loop) |
| `0x4f4850` | 883 | 3 | `shape only` | has a backward branch (often a loop), 203 ins | has a backward branch (often a loop) |
| `0x562410` | 883 | 2 | `shape only` | has a backward branch (often a loop), 187 ins | has a backward branch (often a loop) |
| `0x73a300` | 883 | 3 | `shape only` | has a backward branch (often a loop), 187 ins | has a backward branch (often a loop) |
| `0x73bdd0` | 883 | 2 | `shape only` | has a backward branch (often a loop), 187 ins | has a backward branch (often a loop) |
| `0x5297c0` | 881 | 5 | `shape only` | has a backward branch (often a loop), 175 ins | has a backward branch (often a loop) |
| `0x619f40` | 878 | 8 | `strings` | basic_string::_M_construct null not vali \| %s: __pos (which is %zu) > this->size()  | has a backward branch (often a loop) |
| `0x9797e0` | 878 | 2 | `shape only` | has a backward branch (often a loop), 236 ins | has a backward branch (often a loop) |
| `0x98db50` | 875 | 2 | `shape only` | has a backward branch (often a loop), 227 ins | has a backward branch (often a loop) |
| `0x63a8e0` | 870 | 2 | `shape only` | has a backward branch (often a loop), 231 ins | has a backward branch (often a loop) |
| `0x57d3f0` | 869 | 2 | `shape only` | has a backward branch (often a loop), 233 ins | has a backward branch (often a loop) |
| `0x9af90` | 866 | 2 | `shape only` | has a backward branch (often a loop), 193 ins | has a backward branch (often a loop) |
| `0x1d1380` | 866 | 2 | `shape only` | has a backward branch (often a loop), 244 ins | has a backward branch (often a loop) |
| `0x7d21a0` | 860 | 6 | `shape only` | has a backward branch (often a loop), 207 ins | has a backward branch (often a loop) |
| `0x946d0` | 858 | 2 | `shape only` | has a backward branch (often a loop), 184 ins | has a backward branch (often a loop) |
| `0x8b4500` | 858 | 3 | `shape only` | has a backward branch (often a loop), 222 ins | has a backward branch (often a loop) |
| `0x4f8720` | 857 | 5 | `shape only` | has a backward branch (often a loop), 185 ins | has a backward branch (often a loop) |
| `0x545e50` | 855 | 5 | `shape only` | has a backward branch (often a loop), 191 ins | has a backward branch (often a loop) |
| `0x563a80` | 853 | 3 | `shape only` | has a backward branch (often a loop), 182 ins | has a backward branch (often a loop) |
| `0x1fb290` | 852 | 3 | `shape only` | has a backward branch (often a loop), 222 ins | has a backward branch (often a loop) |
| `0x5ffad0` | 852 | 16 | `shape only` | has a backward branch (often a loop), 217 ins | has a backward branch (often a loop) |
| `0x15c560` | 849 | 7 | `shape only` | has a backward branch (often a loop), 197 ins | has a backward branch (often a loop) |
| `0x5e73c0` | 849 | 4 | `shape only` | has a backward branch (often a loop), 188 ins | has a backward branch (often a loop) |
| `0x5d6620` | 848 | 6 | `strings` | POLYLINE | has a backward branch (often a loop) |
| `0x8c6fc0` | 848 | 3 | `shape only` | has a backward branch (often a loop), 239 ins | has a backward branch (often a loop) |
| `0x25a300` | 847 | 3 | `shape only` | has a backward branch (often a loop), 182 ins | has a backward branch (often a loop) |
| `0x6c8590` | 847 | 3 | `strings` | ../utils/evaluated_object.hpp \| inserted | has a backward branch (often a loop) |
| `0x923ca0` | 846 | 2 | `shape only` | has a backward branch (often a loop), 241 ins | has a backward branch (often a loop) |
| `0x15bc50` | 844 | 5 | `shape only` | has a backward branch (often a loop), 196 ins | has a backward branch (often a loop) |
| `0x957d40` | 842 | 3 | `shape only` | has a backward branch (often a loop), 224 ins | has a backward branch (often a loop) |
| `0x57af60` | 841 | 3 | `shape only` | has a backward branch (often a loop), 224 ins | has a backward branch (often a loop) |
| `0x96110` | 840 | 3 | `shape only` | has a backward branch (often a loop), 216 ins | has a backward branch (often a loop) |
| `0x13b0c0` | 840 | 2 | `shape only` | has a backward branch (often a loop), 231 ins | has a backward branch (often a loop) |
| `0x13b410` | 840 | 2 | `shape only` | has a backward branch (often a loop), 231 ins | has a backward branch (often a loop) |
| `0x1c6260` | 840 | 2 | `shape only` | has a backward branch (often a loop), 204 ins | has a backward branch (often a loop) |
| `0x8f63c0` | 837 | 2 | `shape only` | has a backward branch (often a loop), 242 ins | has a backward branch (often a loop) |
| `0x929380` | 836 | 2 | `shape only` | has a backward branch (often a loop), 241 ins | has a backward branch (often a loop) |
| `0x978ec0` | 836 | 2 | `shape only` | has a backward branch (often a loop), 219 ins | has a backward branch (often a loop) |
| `0x936e20` | 835 | 2 | `shape only` | has a backward branch (often a loop), 186 ins | has a backward branch (often a loop) |
| `0x967740` | 834 | 2 | `shape only` | has a backward branch (often a loop), 217 ins | has a backward branch (often a loop) |
| `0x82050` | 832 | 2 | `shape only` | has a backward branch (often a loop), 231 ins | has a backward branch (often a loop) |
| `0x871570` | 831 | 2 | `shape only` | has a backward branch (often a loop), 222 ins | has a backward branch (often a loop) |
| `0x97d940` | 831 | 2 | `shape only` | has a backward branch (often a loop), 191 ins | has a backward branch (often a loop) |
| `0x7101d0` | 830 | 4 | `shape only` | has a backward branch (often a loop), 170 ins | has a backward branch (often a loop) |
| `0x8d03e0` | 830 | 2 | `shape only` | has a backward branch (often a loop), 212 ins | has a backward branch (often a loop) |
| `0x8d1980` | 829 | 3 | `shape only` | has a backward branch (often a loop), 238 ins | has a backward branch (often a loop) |
| `0x81b30` | 828 | 2 | `shape only` | has a backward branch (often a loop), 216 ins | has a backward branch (often a loop) |
| `0x824b0` | 827 | 2 | `shape only` | has a backward branch (often a loop), 230 ins | has a backward branch (often a loop) |
| `0x302bc0` | 827 | 9 | `shape only` | has a backward branch (often a loop), 160 ins | has a backward branch (often a loop) |
| `0x559c80` | 826 | 2 | `shape only` | has a backward branch (often a loop), 199 ins | has a backward branch (often a loop) |
| `0x162e30` | 824 | 2 | `shape only` | has a backward branch (often a loop), 204 ins | has a backward branch (often a loop) |
| `0x700e80` | 824 | 15 | `shape only` | has a backward branch (often a loop), 200 ins | has a backward branch (often a loop) |
| `0x799ba0` | 824 | 8 | `strings` | basic_string::_M_construct null not vali \| basic_string::append | has a backward branch (often a loop) |
| `0x8a8f90` | 824 | 4 | `shape only` | has a backward branch (often a loop), 215 ins | has a backward branch (often a loop) |
| `0x97d10` | 822 | 2 | `shape only` | has a backward branch (often a loop), 224 ins | has a backward branch (often a loop) |
| `0x66da90` | 820 | 2 | `shape only` | has a backward branch (often a loop), 241 ins | has a backward branch (often a loop) |
| `0x1966a0` | 818 | 2 | `shape only` | has a backward branch (often a loop), 223 ins | has a backward branch (often a loop) |
| `0x5c4610` | 818 | 2 | `shape only` | has a backward branch (often a loop), 211 ins | has a backward branch (often a loop) |
| `0x561910` | 816 | 2 | `shape only` | has a backward branch (often a loop), 210 ins | has a backward branch (often a loop) |
| `0x1d3c60` | 815 | 3 | `shape only` | has a backward branch (often a loop), 202 ins | has a backward branch (often a loop) |
| `0x170290` | 814 | 2 | `shape only` | has a backward branch (often a loop), 167 ins | has a backward branch (often a loop) |
| `0x4de560` | 814 | 18 | `shape only` | has a backward branch (often a loop), 172 ins | has a backward branch (often a loop) |
| `0x539090` | 813 | 3 | `shape only` | has a backward branch (often a loop), 199 ins | has a backward branch (often a loop) |
| `0x516050` | 812 | 2 | `shape only` | has a backward branch (often a loop), 179 ins | has a backward branch (often a loop) |
| `0x72ffd0` | 811 | 2 | `shape only` | has a backward branch (often a loop), 193 ins | has a backward branch (often a loop) |
| `0x7db7d0` | 811 | 5 | `shape only` | has a backward branch (often a loop), 204 ins | has a backward branch (often a loop) |
| `0x8ae120` | 811 | 3 | `shape only` | has a backward branch (often a loop), 213 ins | has a backward branch (often a loop) |
| `0x902c30` | 809 | 2 | `shape only` | has a backward branch (often a loop), 202 ins | has a backward branch (often a loop) |
| `0x955d50` | 808 | 3 | `shape only` | has a backward branch (often a loop), 210 ins | has a backward branch (often a loop) |
| `0x96ce60` | 808 | 2 | `shape only` | has a backward branch (often a loop), 199 ins | has a backward branch (often a loop) |
| `0x3fd40` | 805 | 2 | `shape only` | has a backward branch (often a loop), 192 ins | has a backward branch (often a loop) |
| `0x1c2640` | 803 | 4 | `strings` | ..\nesting\algos\tree_db.hpp \| last_value.IsCompatible(offval) | has a backward branch (often a loop) |
| `0x55be20` | 803 | 2 | `shape only` | has a backward branch (often a loop), 213 ins | has a backward branch (often a loop) |
| `0x5cb6f0` | 803 | 6 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x966510` | 803 | 2 | `shape only` | has a backward branch (often a loop), 180 ins | has a backward branch (often a loop) |
| `0x154690` | 800 | 2 | `shape only` | has a backward branch (often a loop), 207 ins | has a backward branch (often a loop) |
| `0x5c86e0` | 800 | 5 | `shape only` | has a backward branch (often a loop), 218 ins | has a backward branch (often a loop) |
| `0x8d7bf0` | 800 | 4 | `shape only` | has a backward branch (often a loop), 194 ins | has a backward branch (often a loop) |
| `0x979b50` | 800 | 2 | `shape only` | has a backward branch (often a loop), 209 ins | has a backward branch (often a loop) |
| `0x89c1a0` | 798 | 3 | `shape only` | has a backward branch (often a loop), 209 ins | has a backward branch (often a loop) |
| `0x89cdc0` | 798 | 2 | `shape only` | has a backward branch (often a loop), 192 ins | has a backward branch (often a loop) |
| `0x1c52d0` | 797 | 2 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x14e900` | 794 | 2 | `shape only` | has a backward branch (often a loop), 208 ins | has a backward branch (often a loop) |
| `0x5d1c50` | 793 | 4 | `shape only` | has a backward branch (often a loop), 210 ins | has a backward branch (often a loop) |
| `0x61b100` | 793 | 6 | `strings` | basic_string::_M_construct null not vali \| %s: __pos (which is %zu) > this->size()  | has a backward branch (often a loop) |
| `0x96c3d0` | 793 | 2 | `shape only` | has a backward branch (often a loop), 193 ins | has a backward branch (often a loop) |
| `0x96c6f0` | 793 | 2 | `shape only` | has a backward branch (often a loop), 193 ins | has a backward branch (often a loop) |
| `0x96d190` | 793 | 2 | `shape only` | has a backward branch (often a loop), 193 ins | has a backward branch (often a loop) |
| `0x746380` | 792 | 3 | `shape only` | has a backward branch (often a loop), 194 ins | has a backward branch (often a loop) |
| `0x7751e0` | 792 | 4 | `shape only` | straight line / call sequence, 106 ins | straight line / call sequence |
| `0x92fa20` | 791 | 6 | `shape only` | has a backward branch (often a loop), 206 ins | has a backward branch (often a loop) |
| `0x934780` | 791 | 2 | `shape only` | has a backward branch (often a loop), 219 ins | has a backward branch (often a loop) |
| `0x81ccd0` | 790 | 3 | `strings` | ..\nesting\algos\bucket_manager.hpp \| surface_step >= 0 | has a backward branch (often a loop) |
| `0x25aa60` | 789 | 2 | `shape only` | has a backward branch (often a loop), 186 ins | has a backward branch (often a loop) |
| `0x87c3c0` | 787 | 2 | `shape only` | has a backward branch (often a loop), 203 ins | has a backward branch (often a loop) |
| `0x87c960` | 787 | 2 | `shape only` | has a backward branch (often a loop), 203 ins | has a backward branch (often a loop) |
| `0x9e1d0` | 786 | 2 | `shape only` | has a backward branch (often a loop), 192 ins | has a backward branch (often a loop) |
| `0x259610` | 786 | 4 | `shape only` | has a backward branch (often a loop), 166 ins | has a backward branch (often a loop) |
| `0x2aec90` | 786 | 6 | `shape only` | has a backward branch (often a loop), 146 ins | has a backward branch (often a loop) |
| `0x8aef00` | 785 | 4 | `shape only` | has a backward branch (often a loop), 235 ins | has a backward branch (often a loop) |
| `0x98e770` | 784 | 2 | `shape only` | has a backward branch (often a loop), 233 ins | has a backward branch (often a loop) |
| `0x1602d0` | 782 | 3 | `shape only` | has a backward branch (often a loop), 177 ins | has a backward branch (often a loop) |
| `0x8cdad0` | 782 | 4 | `shape only` | has a backward branch (often a loop), 204 ins | has a backward branch (often a loop) |
| `0x3ebb50` | 781 | 4 | `shape only` | has a backward branch (often a loop), 195 ins | has a backward branch (often a loop) |
| `0x86cd60` | 779 | 2 | `shape only` | has a backward branch (often a loop), 203 ins | has a backward branch (often a loop) |
| `0x89d5e0` | 779 | 6 | `shape only` | has a backward branch (often a loop), 202 ins | has a backward branch (often a loop) |
| `0x52c70` | 777 | 3 | `strings` | ..\multi\database.cpp \| nesting.multiplicity() == 1u | has a backward branch (often a loop) |
| `0x14f7b0` | 776 | 4 | `shape only` | has a backward branch (often a loop), 176 ins | has a backward branch (often a loop) |
| `0x5257d0` | 776 | 2 | `shape only` | has a backward branch (often a loop), 159 ins | has a backward branch (often a loop) |
| `0x7df160` | 776 | 3 | `shape only` | has a backward branch (often a loop), 187 ins | has a backward branch (often a loop) |
| `0x7e0240` | 776 | 3 | `shape only` | has a backward branch (often a loop), 187 ins | has a backward branch (often a loop) |
| `0x5253e0` | 775 | 11 | `shape only` | has a backward branch (often a loop), 174 ins | has a backward branch (often a loop) |
| `0x89b2b0` | 775 | 2 | `shape only` | has a backward branch (often a loop), 197 ins | has a backward branch (often a loop) |
| `0xba6f0` | 774 | 2 | `strings` | basic_string::_M_construct null not vali \| memcpy_s: buffer overflow | has a backward branch (often a loop) |
| `0x904250` | 773 | 4 | `shape only` | has a backward branch (often a loop), 219 ins | has a backward branch (often a loop) |
| `0x544ec0` | 770 | 8 | `shape only` | has a backward branch (often a loop), 168 ins | has a backward branch (often a loop) |
| `0x57c910` | 770 | 2 | `shape only` | has a backward branch (often a loop), 212 ins | has a backward branch (often a loop) |
| `0x229aa0` | 769 | 2 | `shape only` | has a backward branch (often a loop), 178 ins | has a backward branch (often a loop) |
| `0x4f3f60` | 769 | 4 | `shape only` | has a backward branch (often a loop), 168 ins | has a backward branch (often a loop) |
| `0x62c810` | 769 | 3 | `shape only` | has a backward branch (often a loop), 167 ins | has a backward branch (often a loop) |
| `0x8bc930` | 769 | 3 | `shape only` | has a backward branch (often a loop), 184 ins | has a backward branch (often a loop) |
| `0x9092f0` | 769 | 2 | `shape only` | has a backward branch (often a loop), 194 ins | has a backward branch (often a loop) |
| `0x953aa0` | 768 | 3 | `shape only` | has a backward branch (often a loop), 203 ins | has a backward branch (often a loop) |
| `0xae040` | 767 | 4 | `shape only` | has a backward branch (often a loop), 161 ins | has a backward branch (often a loop) |
| `0x1a4c90` | 765 | 2 | `shape only` | has a backward branch (often a loop), 150 ins | has a backward branch (often a loop) |
| `0x65b820` | 764 | 5 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x928bc0` | 763 | 2 | `shape only` | has a backward branch (often a loop), 198 ins | has a backward branch (often a loop) |
| `0x19da20` | 761 | 4 | `shape only` | has a backward branch (often a loop), 164 ins | has a backward branch (often a loop) |
| `0x5266a0` | 759 | 3 | `shape only` | has a backward branch (often a loop), 171 ins | has a backward branch (often a loop) |
| `0x173450` | 758 | 4 | `shape only` | has a backward branch (often a loop), 163 ins | has a backward branch (often a loop) |
| `0x526160` | 757 | 4 | `shape only` | has a backward branch (often a loop), 171 ins | has a backward branch (often a loop) |
| `0x5ed8c0` | 757 | 4 | `shape only` | has a backward branch (often a loop), 152 ins | has a backward branch (often a loop) |
| `0x8db320` | 757 | 3 | `shape only` | has a backward branch (often a loop), 166 ins | has a backward branch (often a loop) |
| `0x25f1e0` | 755 | 2 | `shape only` | has a backward branch (often a loop), 162 ins | has a backward branch (often a loop) |
| `0x926580` | 755 | 3 | `shape only` | has a backward branch (often a loop), 192 ins | has a backward branch (often a loop) |
| `0x13c5d0` | 753 | 3 | `shape only` | has a backward branch (often a loop), 179 ins | has a backward branch (often a loop) |
| `0x3fa50` | 752 | 3 | `shape only` | has a backward branch (often a loop), 176 ins | has a backward branch (often a loop) |
| `0x100180` | 752 | 4 | `shape only` | has a backward branch (often a loop), 141 ins | has a backward branch (often a loop) |
| `0x17e180` | 752 | 2 | `shape only` | has a backward branch (often a loop), 178 ins | has a backward branch (often a loop) |
| `0x4ff920` | 752 | 1 | `shape only` | has a backward branch (often a loop), 205 ins | has a backward branch (often a loop) |
| `0x4ffc50` | 752 | 3 | `shape only` | has a backward branch (often a loop), 205 ins | has a backward branch (often a loop) |
| `0x1fd3b0` | 751 | 6 | `shape only` | has a backward branch (often a loop), 169 ins | has a backward branch (often a loop) |
| `0x9098e0` | 751 | 2 | `shape only` | has a backward branch (often a loop), 194 ins | has a backward branch (often a loop) |
| `0x669e60` | 749 | 1 | `shape only` | straight line / call sequence, 136 ins | straight line / call sequence |
| `0x8e8840` | 749 | 3 | `shape only` | has a backward branch (often a loop), 212 ins | has a backward branch (often a loop) |
| `0x539e10` | 746 | 5 | `shape only` | has a backward branch (often a loop), 217 ins | has a backward branch (often a loop) |
| `0x598a30` | 745 | 2 | `shape only` | has a backward branch (often a loop), 191 ins | has a backward branch (often a loop) |
| `0x4d03f0` | 742 | 2 | `shape only` | has a backward branch (often a loop), 192 ins | has a backward branch (often a loop) |
| `0x711ad0` | 741 | 4 | `shape only` | has a backward branch (often a loop), 185 ins | has a backward branch (often a loop) |
| `0x5a3120` | 739 | 4 | `shape only` | has a backward branch (often a loop), 196 ins | has a backward branch (often a loop) |
| `0x6bcc70` | 739 | 2 | `shape only` | has a backward branch (often a loop), 188 ins | has a backward branch (often a loop) |
| `0x89d2f0` | 739 | 27 | `shape only` | has a backward branch (often a loop), 190 ins | has a backward branch (often a loop) |
| `0x9794f0` | 738 | 2 | `shape only` | has a backward branch (often a loop), 183 ins | has a backward branch (often a loop) |
| `0x896720` | 737 | 3 | `shape only` | has a backward branch (often a loop), 191 ins | has a backward branch (often a loop) |
| `0x986970` | 737 | 3 | `shape only` | has a backward branch (often a loop), 178 ins | has a backward branch (often a loop) |
| `0x524b30` | 735 | 7 | `shape only` | has a backward branch (often a loop), 169 ins | has a backward branch (often a loop) |
| `0x29c270` | 734 | 3 | `strings` | OsiDefaultName \| Unknown Solver | has a backward branch (often a loop) |
| `0x13ade0` | 731 | 2 | `shape only` | has a backward branch (often a loop), 201 ins | has a backward branch (often a loop) |
| `0x98f1c0` | 731 | 2 | `shape only` | has a backward branch (often a loop), 164 ins | has a backward branch (often a loop) |
| `0x6859f0` | 730 | 5 | `strings` | !points.empty() \| ..\exact\geom_conversion.inl | has a backward branch (often a loop) |
| `0x7b53e0` | 730 | 2 | `strings` | Buckets : empty \| %llu | has a backward branch (often a loop) |
| `0x89d8f0` | 730 | 6 | `shape only` | has a backward branch (often a loop), 189 ins | has a backward branch (often a loop) |
| `0x3e2770` | 729 | 14 | `shape only` | straight line / call sequence, 171 ins | straight line / call sequence |
| `0x57ce80` | 728 | 3 | `shape only` | has a backward branch (often a loop), 193 ins | has a backward branch (often a loop) |
| `0x5c6c30` | 728 | 20 | `shape only` | has a backward branch (often a loop), 184 ins | has a backward branch (often a loop) |
| `0xb8210` | 727 | 3 | `strings` | basic_string::substr \| %s: __pos (which is %zu) > this->size()  | has a backward branch (often a loop) |
| `0x870680` | 727 | 7 | `shape only` | has a backward branch (often a loop), 219 ins | has a backward branch (often a loop) |
| `0x13d4f0` | 726 | 6 | `shape only` | has a backward branch (often a loop), 178 ins | has a backward branch (often a loop) |
| `0x979210` | 723 | 2 | `shape only` | has a backward branch (often a loop), 189 ins | has a backward branch (often a loop) |
| `0x780570` | 722 | 11 | `strings` | basic_string::append \| NameValuePairs: type mismatch for ' | has a backward branch (often a loop) |
| `0x970d80` | 722 | 4 | `shape only` | has a backward branch (often a loop), 196 ins | has a backward branch (often a loop) |
| `0x8f6710` | 721 | 2 | `shape only` | has a backward branch (often a loop), 189 ins | has a backward branch (often a loop) |
| `0x8fb530` | 721 | 1 | `shape only` | has a backward branch (often a loop), 213 ins | has a backward branch (often a loop) |
| `0x63a2a0` | 720 | 4 | `shape only` | has a backward branch (often a loop), 209 ins | has a backward branch (often a loop) |
| `0x1d0d70` | 719 | 4 | `shape only` | has a backward branch (often a loop), 148 ins | has a backward branch (often a loop) |
| `0x199060` | 718 | 3 | `strings` | basic_string::append \| basic_string::_M_construct null not vali | has a backward branch (often a loop) |
| `0x503b0` | 717 | 3 | `shape only` | has a backward branch (often a loop), 149 ins | has a backward branch (often a loop) |
| `0x4ba4d0` | 717 | 3 | `shape only` | has a backward branch (often a loop), 148 ins | has a backward branch (often a loop) |
| `0x5e0690` | 717 | 2 | `shape only` | has a backward branch (often a loop), 166 ins | has a backward branch (often a loop) |
| `0x8e6010` | 717 | 4 | `shape only` | has a backward branch (often a loop), 193 ins | has a backward branch (often a loop) |
| `0x873750` | 716 | 3 | `shape only` | has a backward branch (often a loop), 199 ins | has a backward branch (often a loop) |
| `0x8e5a10` | 716 | 4 | `shape only` | has a backward branch (often a loop), 193 ins | has a backward branch (often a loop) |
| `0x9575a0` | 716 | 2 | `shape only` | has a backward branch (often a loop), 191 ins | has a backward branch (often a loop) |
| `0x946830` | 715 | 2 | `shape only` | has a backward branch (often a loop), 153 ins | has a backward branch (often a loop) |
| `0x1d4250` | 714 | 3 | `shape only` | has a backward branch (often a loop), 159 ins | has a backward branch (often a loop) |
| `0x6391a0` | 711 | 2 | `strings` | __powi | has a backward branch (often a loop) |
| `0x97bf10` | 709 | 2 | `shape only` | has a backward branch (often a loop), 184 ins | has a backward branch (often a loop) |
| `0x23f690` | 707 | 2 | `shape only` | has a backward branch (often a loop), 166 ins | has a backward branch (often a loop) |
| `0x54a930` | 705 | 3 | `shape only` | has a backward branch (often a loop), 155 ins | has a backward branch (often a loop) |
| `0x8ba720` | 705 | 2 | `shape only` | has a backward branch (often a loop), 186 ins | has a backward branch (often a loop) |
| `0x8ba9f0` | 705 | 2 | `shape only` | has a backward branch (often a loop), 186 ins | has a backward branch (often a loop) |
| `0x972ec0` | 701 | 2 | `shape only` | has a backward branch (often a loop), 190 ins | has a backward branch (often a loop) |
| `0x524250` | 699 | 3 | `shape only` | has a backward branch (often a loop), 176 ins | has a backward branch (often a loop) |
| `0x6ea520` | 699 | 4 | `strings` | winsock \| iocp | has a backward branch (often a loop) |
| `0x97c1e0` | 699 | 2 | `shape only` | has a backward branch (often a loop), 180 ins | has a backward branch (often a loop) |
| `0x6d6ca0` | 698 | 4 | `shape only` | has a backward branch (often a loop), 182 ins | has a backward branch (often a loop) |
| `0x4c0700` | 697 | 4 | `shape only` | has a backward branch (often a loop), 182 ins | has a backward branch (often a loop) |
| `0x5cfac0` | 696 | 2 | `shape only` | has a backward branch (often a loop), 183 ins | has a backward branch (often a loop) |
| `0x89dbd0` | 696 | 6 | `shape only` | has a backward branch (often a loop), 177 ins | has a backward branch (often a loop) |
| `0x8b3fa0` | 696 | 4 | `shape only` | has a backward branch (often a loop), 196 ins | has a backward branch (often a loop) |
| `0x711550` | 695 | 3 | `shape only` | has a backward branch (often a loop), 173 ins | has a backward branch (often a loop) |
| `0x711810` | 695 | 3 | `shape only` | has a backward branch (often a loop), 173 ins | has a backward branch (often a loop) |
| `0xa35f0` | 693 | 3 | `shape only` | has a backward branch (often a loop), 160 ins | has a backward branch (often a loop) |
| `0x16ccf0` | 693 | 4 | `shape only` | has a backward branch (often a loop), 159 ins | has a backward branch (often a loop) |
| `0x546670` | 693 | 3 | `shape only` | has a backward branch (often a loop), 195 ins | has a backward branch (often a loop) |
| `0x5cf060` | 693 | 14 | `shape only` | has a backward branch (often a loop), 149 ins | has a backward branch (often a loop) |
| `0x70d220` | 693 | 3 | `shape only` | has a backward branch (often a loop), 180 ins | has a backward branch (often a loop) |
| `0x9385e0` | 693 | 5 | `shape only` | has a backward branch (often a loop), 188 ins | has a backward branch (often a loop) |
| `0x9acd0` | 692 | 3 | `shape only` | has a backward branch (often a loop), 170 ins | has a backward branch (often a loop) |
| `0x5f4d50` | 692 | 6 | `shape only` | has a backward branch (often a loop), 154 ins | has a backward branch (often a loop) |
| `0x949480` | 691 | 2 | `shape only` | has a backward branch (often a loop), 155 ins | has a backward branch (often a loop) |
| `0x3d920` | 690 | 2 | `shape only` | has a backward branch (often a loop), 175 ins | has a backward branch (often a loop) |
| `0x8d0120` | 690 | 2 | `shape only` | has a backward branch (often a loop), 176 ins | has a backward branch (often a loop) |
| `0x8d1cc0` | 690 | 3 | `shape only` | has a backward branch (often a loop), 198 ins | has a backward branch (often a loop) |
| `0x94c560` | 690 | 2 | `shape only` | has a backward branch (often a loop), 168 ins | has a backward branch (often a loop) |
| `0xacf0` | 689 | 2 | `shape only` | has a backward branch (often a loop), 171 ins | has a backward branch (often a loop) |
| `0x92bf90` | 688 | 3 | `shape only` | has a backward branch (often a loop), 179 ins | has a backward branch (often a loop) |
| `0x5c4e90` | 687 | 4 | `shape only` | has a backward branch (often a loop), 155 ins | has a backward branch (often a loop) |
| `0x76df60` | 686 | 12 | `shape only` | has a backward branch (often a loop), 145 ins | has a backward branch (often a loop) |
| `0x92c810` | 686 | 2 | `shape only` | has a backward branch (often a loop), 189 ins | has a backward branch (often a loop) |
| `0xb4a70` | 684 | 3 | `strings` | AUATUWVSH | has a backward branch (often a loop) |
| `0x958e60` | 684 | 2 | `shape only` | has a backward branch (often a loop), 173 ins | has a backward branch (often a loop) |
| `0x5ede60` | 682 | 4 | `shape only` | has a backward branch (often a loop), 148 ins | has a backward branch (often a loop) |
| `0x901160` | 680 | 2 | `shape only` | has a backward branch (often a loop), 168 ins | has a backward branch (often a loop) |
| `0x136df0` | 679 | 8 | `shape only` | has a backward branch (often a loop), 159 ins | has a backward branch (often a loop) |
| `0x53c0` | 677 | 5 | `shape only` | has a backward branch (often a loop), 159 ins | has a backward branch (often a loop) |
| `0x19dd20` | 677 | 2 | `shape only` | has a backward branch (often a loop), 160 ins | has a backward branch (often a loop) |
| `0x1d76b0` | 676 | 3 | `shape only` | has a backward branch (often a loop), 152 ins | has a backward branch (often a loop) |
| `0x896a10` | 675 | 3 | `shape only` | has a backward branch (often a loop), 172 ins | has a backward branch (often a loop) |
| `0x1c2310` | 674 | 4 | `shape only` | has a backward branch (often a loop), 181 ins | has a backward branch (often a loop) |
| `0x1c65b0` | 673 | 3 | `shape only` | has a backward branch (often a loop), 160 ins | has a backward branch (often a loop) |
| `0x5f8220` | 671 | 3 | `shape only` | has a backward branch (often a loop), 126 ins | has a backward branch (often a loop) |
| `0x7384e0` | 671 | 5 | `shape only` | has a backward branch (often a loop), 165 ins | has a backward branch (often a loop) |
| `0x7c21c0` | 671 | 5 | `shape only` | has a backward branch (often a loop), 152 ins | has a backward branch (often a loop) |
| `0x62c570` | 670 | 3 | `shape only` | has a backward branch (often a loop), 153 ins | has a backward branch (often a loop) |
| `0x13de40` | 669 | 2 | `shape only` | has a backward branch (often a loop), 174 ins | has a backward branch (often a loop) |
| `0x5232e0` | 669 | 2 | `shape only` | has a backward branch (often a loop), 166 ins | has a backward branch (often a loop) |
| `0x907f60` | 669 | 2 | `shape only` | has a backward branch (often a loop), 187 ins | has a backward branch (often a loop) |
| `0x4f31e0` | 667 | 3 | `shape only` | has a backward branch (often a loop), 142 ins | has a backward branch (often a loop) |
| `0x5e78d0` | 667 | 10 | `shape only` | has a backward branch (often a loop), 179 ins | has a backward branch (often a loop) |
| `0x5860` | 666 | 2 | `shape only` | has a backward branch (often a loop), 166 ins | has a backward branch (often a loop) |
| `0x96a0f0` | 666 | 2 | `shape only` | has a backward branch (often a loop), 151 ins | has a backward branch (often a loop) |
| `0x5c6f10` | 664 | 5 | `shape only` | has a backward branch (often a loop), 181 ins | has a backward branch (often a loop) |
| `0x5edbc0` | 664 | 4 | `shape only` | has a backward branch (often a loop), 148 ins | has a backward branch (often a loop) |
| `0x8bdec0` | 663 | 2 | `shape only` | has a backward branch (often a loop), 170 ins | has a backward branch (often a loop) |
| `0x11b880` | 661 | 8 | `strings` | HashTransformation: can't truncate a  \|  byte digest to  | has a backward branch (often a loop) |
| `0x8b6ac0` | 661 | 3 | `shape only` | has a backward branch (often a loop), 163 ins | has a backward branch (often a loop) |
| `0x9051f0` | 661 | 4 | `shape only` | has a backward branch (often a loop), 176 ins | has a backward branch (often a loop) |
| `0x546ab0` | 660 | 3 | `shape only` | has a backward branch (often a loop), 168 ins | has a backward branch (often a loop) |
| `0x5018c0` | 659 | 6 | `shape only` | has a backward branch (often a loop), 181 ins | has a backward branch (often a loop) |
| `0x64b6c0` | 659 | 2 | `strings` | ->  | has a backward branch (often a loop) |
| `0x93b400` | 659 | 9 | `shape only` | has a backward branch (often a loop), 178 ins | has a backward branch (often a loop) |
| `0x98c390` | 659 | 2 | `shape only` | has a backward branch (often a loop), 131 ins | has a backward branch (often a loop) |
| `0x977a0` | 658 | 2 | `shape only` | has a backward branch (often a loop), 172 ins | has a backward branch (often a loop) |
| `0x1bc200` | 658 | 3 | `shape only` | has a backward branch (often a loop), 163 ins | has a backward branch (often a loop) |
| `0x1beed0` | 658 | 2 | `shape only` | has a backward branch (often a loop), 146 ins | has a backward branch (often a loop) |
| `0x8d3450` | 658 | 4 | `shape only` | has a backward branch (often a loop), 171 ins | has a backward branch (often a loop) |
| `0x9985d0` | 657 | 2 | `strings` | ..\nesting\algos\algo_helpers.hpp \| n1.Valid() | has a backward branch (often a loop) |
| `0x203ab0` | 656 | 8 | `shape only` | has a backward branch (often a loop), 138 ins | has a backward branch (often a loop) |
| `0x2204a0` | 654 | 2 | `shape only` | has a backward branch (often a loop), 153 ins | has a backward branch (often a loop) |
| `0x92a8e0` | 654 | 2 | `shape only` | has a backward branch (often a loop), 196 ins | has a backward branch (often a loop) |
| `0x9392b0` | 654 | 3 | `shape only` | has a backward branch (often a loop), 196 ins | has a backward branch (often a loop) |
| `0x93eb80` | 654 | 2 | `shape only` | has a backward branch (often a loop), 196 ins | has a backward branch (often a loop) |
| `0x1eaed0` | 653 | 2 | `shape only` | has a backward branch (often a loop), 155 ins | has a backward branch (often a loop) |
| `0x954600` | 652 | 2 | `shape only` | has a backward branch (often a loop), 169 ins | has a backward branch (often a loop) |
| `0x954890` | 652 | 2 | `shape only` | has a backward branch (often a loop), 169 ins | has a backward branch (often a loop) |
| `0x4d4d30` | 651 | 5 | `strings` |  -> boost  | has a backward branch (often a loop) |
| `0x4dcf90` | 650 | 3 | `shape only` | has a backward branch (often a loop), 183 ins | has a backward branch (often a loop) |
| `0x87ba80` | 650 | 2 | `shape only` | has a backward branch (often a loop), 173 ins | has a backward branch (often a loop) |
| `0x87bf20` | 650 | 2 | `shape only` | has a backward branch (often a loop), 173 ins | has a backward branch (often a loop) |
| `0x7deed0` | 649 | 2 | `shape only` | has a backward branch (often a loop), 160 ins | has a backward branch (often a loop) |
| `0x7dffb0` | 649 | 2 | `shape only` | has a backward branch (often a loop), 160 ins | has a backward branch (often a loop) |
| `0x870ce0` | 648 | 2 | `shape only` | has a backward branch (often a loop), 191 ins | has a backward branch (often a loop) |
| `0x8b7200` | 648 | 2 | `shape only` | has a backward branch (often a loop), 181 ins | has a backward branch (often a loop) |
| `0x8c0570` | 648 | 2 | `shape only` | has a backward branch (often a loop), 181 ins | has a backward branch (often a loop) |
| `0x1fb810` | 647 | 6 | `strings` | ..\nesting\ios\log_ios.cpp \| !m_all_tries.empty() | has a backward branch (often a loop) |
| `0x5a61f0` | 647 | 4 | `shape only` | has a backward branch (often a loop), 173 ins | has a backward branch (often a loop) |
| `0x1617a0` | 644 | 2 | `shape only` | has a backward branch (often a loop), 165 ins | has a backward branch (often a loop) |
| `0x5d1580` | 644 | 1 | `shape only` | has a backward branch (often a loop), 165 ins | has a backward branch (often a loop) |
| `0x8a07d0` | 644 | 2 | `shape only` | has a backward branch (often a loop), 169 ins | has a backward branch (often a loop) |
| `0x5d06e0` | 643 | 3 | `shape only` | has a backward branch (often a loop), 174 ins | has a backward branch (often a loop) |
| `0x8fb810` | 641 | 2 | `shape only` | has a backward branch (often a loop), 177 ins | has a backward branch (often a loop) |
| `0x8e6af0` | 640 | 2 | `shape only` | has a backward branch (often a loop), 173 ins | has a backward branch (often a loop) |
| `0x8e95c0` | 640 | 3 | `shape only` | has a backward branch (often a loop), 173 ins | has a backward branch (often a loop) |
| `0x9531e0` | 640 | 2 | `shape only` | has a backward branch (often a loop), 182 ins | has a backward branch (often a loop) |
| `0x3c110` | 639 | 2 | `strings` | basic_string::append \| enlarged_ | has a backward branch (often a loop) |
| `0x563de0` | 639 | 2 | `shape only` | has a backward branch (often a loop), 137 ins | has a backward branch (often a loop) |
| `0x57f540` | 639 | 11 | `strings` | AUATUWVSH \| AVAUATUWVSH | has a backward branch (often a loop) |
| `0x7c7120` | 639 | 2 | `shape only` | straight line / call sequence, 85 ins | straight line / call sequence |
| `0x904560` | 639 | 2 | `shape only` | has a backward branch (often a loop), 174 ins | has a backward branch (often a loop) |
| `0x1d28b0` | 638 | 3 | `shape only` | has a backward branch (often a loop), 171 ins | has a backward branch (often a loop) |
| `0x263760` | 638 | 4 | `shape only` | has a backward branch (often a loop), 150 ins | has a backward branch (often a loop) |
| `0x684b60` | 638 | 8 | `shape only` | has a backward branch (often a loop), 143 ins | has a backward branch (often a loop) |
| `0x93c180` | 638 | 9 | `shape only` | has a backward branch (often a loop), 170 ins | has a backward branch (often a loop) |
| `0x20b390` | 637 | 2 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x600960` | 637 | 4 | `strings` | %#.16g | has a backward branch (often a loop) |
| `0x12a710` | 636 | 2 | `shape only` | has a backward branch (often a loop), 139 ins | has a backward branch (often a loop) |
| `0x5275f0` | 636 | 8 | `shape only` | has a backward branch (often a loop), 154 ins | has a backward branch (often a loop) |
| `0x94450` | 635 | 3 | `shape only` | has a backward branch (often a loop), 150 ins | has a backward branch (often a loop) |
| `0x547730` | 633 | 7 | `shape only` | has a backward branch (often a loop), 156 ins | has a backward branch (often a loop) |
| `0x57c1f0` | 633 | 2 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x67eca0` | 633 | 2 | `shape only` | has a backward branch (often a loop), 170 ins | has a backward branch (often a loop) |
| `0x589a40` | 632 | 2 | `shape only` | has a backward branch (often a loop), 157 ins | has a backward branch (often a loop) |
| `0x87c6e0` | 632 | 2 | `shape only` | has a backward branch (often a loop), 175 ins | has a backward branch (often a loop) |
| `0x87cc80` | 632 | 2 | `shape only` | has a backward branch (often a loop), 175 ins | has a backward branch (often a loop) |
| `0x20fc10` | 631 | 2 | `shape only` | has a backward branch (often a loop), 172 ins | has a backward branch (often a loop) |
| `0x212830` | 631 | 2 | `shape only` | has a backward branch (often a loop), 172 ins | has a backward branch (often a loop) |
| `0x212ab0` | 631 | 2 | `shape only` | has a backward branch (often a loop), 172 ins | has a backward branch (often a loop) |
| `0x5734c0` | 631 | 8 | `shape only` | has a backward branch (often a loop), 177 ins | has a backward branch (often a loop) |
| `0x57fb20` | 630 | 3 | `shape only` | has a backward branch (often a loop), 166 ins | has a backward branch (often a loop) |
| `0x6b8690` | 630 | 4 | `shape only` | has a backward branch (often a loop), 169 ins | has a backward branch (often a loop) |
| `0x8ae730` | 630 | 2 | `shape only` | has a backward branch (often a loop), 170 ins | has a backward branch (often a loop) |
| `0x18e020` | 629 | 3 | `shape only` | has a backward branch (often a loop), 159 ins | has a backward branch (often a loop) |
| `0x5433f0` | 627 | 3 | `shape only` | has a backward branch (often a loop), 144 ins | has a backward branch (often a loop) |
| `0x64bb20` | 627 | 2 | `strings` | ->  | has a backward branch (often a loop) |
| `0x4dba70` | 626 | 3 | `shape only` | has a backward branch (often a loop), 161 ins | has a backward branch (often a loop) |
| `0x70f960` | 626 | 3 | `shape only` | has a backward branch (often a loop), 150 ins | has a backward branch (often a loop) |
| `0x710ce0` | 626 | 3 | `shape only` | has a backward branch (often a loop), 150 ins | has a backward branch (often a loop) |
| `0x8d7260` | 626 | 2 | `shape only` | has a backward branch (often a loop), 167 ins | has a backward branch (often a loop) |
| `0x5c5c0` | 624 | 2 | `shape only` | has a backward branch (often a loop), 142 ins | has a backward branch (often a loop) |
| `0x4d06e0` | 624 | 3 | `shape only` | has a backward branch (often a loop), 150 ins | has a backward branch (often a loop) |
| `0x5eb200` | 624 | 2 | `shape only` | has a backward branch (often a loop), 179 ins | has a backward branch (often a loop) |
| `0x94c820` | 624 | 2 | `shape only` | has a backward branch (often a loop), 160 ins | has a backward branch (often a loop) |
| `0x9273c0` | 623 | 5 | `shape only` | has a backward branch (often a loop), 159 ins | has a backward branch (often a loop) |
| `0x16ef80` | 622 | 3 | `shape only` | has a backward branch (often a loop), 154 ins | has a backward branch (often a loop) |
| `0x52fae0` | 622 | 3 | `shape only` | has a backward branch (often a loop), 150 ins | has a backward branch (often a loop) |
| `0x96a820` | 622 | 3 | `shape only` | has a backward branch (often a loop), 152 ins | has a backward branch (often a loop) |
| `0x5b3230` | 621 | 1 | `shape only` | has a backward branch (often a loop), 136 ins | has a backward branch (often a loop) |
| `0x7e1200` | 621 | 3 | `shape only` | has a backward branch (often a loop), 133 ins | has a backward branch (often a loop) |
| `0x8c49f0` | 621 | 13 | `shape only` | has a backward branch (often a loop), 158 ins | has a backward branch (often a loop) |
| `0x8e92b0` | 621 | 2 | `shape only` | has a backward branch (often a loop), 158 ins | has a backward branch (often a loop) |
| `0x19f680` | 620 | 2 | `shape only` | has a backward branch (often a loop), 157 ins | has a backward branch (often a loop) |
| `0x218810` | 620 | 2 | `shape only` | has a backward branch (often a loop), 180 ins | has a backward branch (often a loop) |
| `0x4e58e0` | 620 | 4 | `shape only` | has a backward branch (often a loop), 146 ins | has a backward branch (often a loop) |
| `0x5ba360` | 620 | 2 | `shape only` | has a backward branch (often a loop), 167 ins | has a backward branch (often a loop) |
| `0x4f3a40` | 617 | 2 | `shape only` | has a backward branch (often a loop), 156 ins | has a backward branch (often a loop) |
| `0x525ef0` | 617 | 4 | `strings` | ..\structure\stats.cpp \| nesting.sheet() | has a backward branch (often a loop) |
| `0x928ec0` | 617 | 2 | `shape only` | has a backward branch (often a loop), 156 ins | has a backward branch (often a loop) |
| `0x8c6870` | 616 | 3 | `shape only` | has a backward branch (often a loop), 172 ins | has a backward branch (often a loop) |
| `0x4fd2e0` | 614 | 2 | `shape only` | has a backward branch (often a loop), 167 ins | has a backward branch (often a loop) |
| `0x19dfe0` | 613 | 2 | `shape only` | has a backward branch (often a loop), 165 ins | has a backward branch (often a loop) |
| `0x5621a0` | 612 | 2 | `shape only` | has a backward branch (often a loop), 142 ins | has a backward branch (often a loop) |
| `0x951570` | 612 | 2 | `shape only` | has a backward branch (often a loop), 157 ins | has a backward branch (often a loop) |
| `0x969e80` | 612 | 3 | `shape only` | has a backward branch (often a loop), 137 ins | has a backward branch (often a loop) |
| `0xf1b20` | 610 | 5 | `shape only` | has a backward branch (often a loop), 178 ins | has a backward branch (often a loop) |
| `0x8b8f30` | 609 | 2 | `shape only` | has a backward branch (often a loop), 169 ins | has a backward branch (often a loop) |
| `0x8c1e30` | 609 | 10 | `shape only` | has a backward branch (often a loop), 165 ins | has a backward branch (often a loop) |
| `0x8cb6f0` | 609 | 9 | `shape only` | has a backward branch (often a loop), 165 ins | has a backward branch (often a loop) |
| `0x967e40` | 609 | 2 | `shape only` | has a backward branch (often a loop), 169 ins | has a backward branch (often a loop) |
| `0x552e30` | 608 | 3 | `strings` | !nesteds.empty() \| ..\structure\automatic_cluster.cpp | has a backward branch (often a loop) |
| `0x24d6f0` | 607 | 2 | `shape only` | has a backward branch (often a loop), 152 ins | has a backward branch (often a loop) |
| `0x5483d0` | 607 | 2 | `shape only` | has a backward branch (often a loop), 160 ins | has a backward branch (often a loop) |
| `0x5d7270` | 607 | 3 | `strings` |   0 \| ENDSEC | has a backward branch (often a loop) |
| `0x739c20` | 607 | 2 | `shape only` | has a backward branch (often a loop), 157 ins | has a backward branch (often a loop) |
| `0x73b6f0` | 607 | 2 | `shape only` | has a backward branch (often a loop), 157 ins | has a backward branch (often a loop) |
| `0x4f6d80` | 606 | 3 | `shape only` | has a backward branch (often a loop), 168 ins | has a backward branch (often a loop) |
| `0x9308c0` | 605 | 16 | `callers` | called by 0x2ab0 LaunchLocalComputation; 0x6100 LaunchComputation | has a backward branch (often a loop) |
| `0x930da0` | 605 | 3 | `shape only` | has a backward branch (often a loop), 159 ins | has a backward branch (often a loop) |
| `0x935910` | 605 | 2 | `shape only` | has a backward branch (often a loop), 159 ins | has a backward branch (often a loop) |
| `0x9321c0` | 604 | 2 | `shape only` | has a backward branch (often a loop), 159 ins | has a backward branch (often a loop) |
| `0x86c740` | 603 | 2 | `shape only` | has a backward branch (often a loop), 166 ins | has a backward branch (often a loop) |
| `0x532490` | 602 | 2 | `shape only` | has a backward branch (often a loop), 157 ins | has a backward branch (often a loop) |
| `0x93be70` | 602 | 2 | `shape only` | has a backward branch (often a loop), 152 ins | has a backward branch (often a loop) |
| `0x96b740` | 602 | 4 | `shape only` | has a backward branch (often a loop), 125 ins | has a backward branch (often a loop) |
| `0x9517e0` | 601 | 2 | `shape only` | has a backward branch (often a loop), 149 ins | has a backward branch (often a loop) |
| `0x951a40` | 601 | 2 | `shape only` | has a backward branch (often a loop), 151 ins | has a backward branch (often a loop) |
| `0x97dda0` | 601 | 2 | `shape only` | has a backward branch (often a loop), 164 ins | has a backward branch (often a loop) |
| `0x1608f0` | 600 | 3 | `shape only` | has a backward branch (often a loop), 165 ins | has a backward branch (often a loop) |
| `0x5ba100` | 600 | 2 | `shape only` | has a backward branch (often a loop), 173 ins | has a backward branch (often a loop) |
| `0x505ce0` | 599 | 2 | `strings` | v.isArray() \| ..\structure\text_io.cpp | has a backward branch (often a loop) |
| `0x69a110` | 598 | 2 | `shape only` | has a backward branch (often a loop), 171 ins | has a backward branch (often a loop) |
| `0x8cf9e0` | 598 | 3 | `shape only` | has a backward branch (often a loop), 154 ins | has a backward branch (often a loop) |
| `0x9030d0` | 598 | 3 | `shape only` | has a backward branch (often a loop), 150 ins | has a backward branch (often a loop) |
| `0x20ddc0` | 597 | 4 | `shape only` | has a backward branch (often a loop), 137 ins | has a backward branch (often a loop) |
| `0x7478d0` | 597 | 2 | `shape only` | has a backward branch (often a loop), 108 ins | has a backward branch (often a loop) |
| `0x904cd0` | 597 | 2 | `shape only` | has a backward branch (often a loop), 172 ins | has a backward branch (often a loop) |
| `0x96aa90` | 597 | 2 | `shape only` | has a backward branch (often a loop), 145 ins | has a backward branch (often a loop) |
| `0x814a0` | 596 | 2 | `shape only` | has a backward branch (often a loop), 166 ins | has a backward branch (often a loop) |
| `0x4db810` | 596 | 2 | `shape only` | has a backward branch (often a loop), 157 ins | has a backward branch (often a loop) |
| `0x8e7c50` | 595 | 2 | `shape only` | has a backward branch (often a loop), 162 ins | has a backward branch (often a loop) |
| `0xf2700` | 593 | 6 | `shape only` | has a backward branch (often a loop), 145 ins | has a backward branch (often a loop) |
| `0x141bf0` | 593 | 2 | `shape only` | has a backward branch (often a loop), 145 ins | has a backward branch (often a loop) |
| `0x501660` | 593 | 5 | `shape only` | has a backward branch (often a loop), 164 ins | has a backward branch (often a loop) |
| `0x1a8780` | 592 | 3 | `shape only` | has a backward branch (often a loop), 160 ins | has a backward branch (often a loop) |
| `0x8ae450` | 592 | 4 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x7917f0` | 591 | 2 | `strings` | : Missing required parameter ' \| N8CryptoPP11RSAFunctionE | has a backward branch (often a loop) |
| `0x960f00` | 591 | 2 | `shape only` | has a backward branch (often a loop), 168 ins | has a backward branch (often a loop) |
| `0x1fe4e0` | 590 | 4 | `shape only` | has a backward branch (often a loop), 136 ins | has a backward branch (often a loop) |
| `0x5eaaf0` | 590 | 3 | `shape only` | has a backward branch (often a loop), 165 ins | has a backward branch (often a loop) |
| `0x9339b0` | 590 | 4 | `shape only` | has a backward branch (often a loop), 156 ins | has a backward branch (often a loop) |
| `0x9356c0` | 590 | 2 | `shape only` | has a backward branch (often a loop), 156 ins | has a backward branch (often a loop) |
| `0x938d80` | 590 | 2 | `shape only` | has a backward branch (often a loop), 156 ins | has a backward branch (often a loop) |
| `0x93b100` | 590 | 17 | `shape only` | has a backward branch (often a loop), 156 ins | has a backward branch (often a loop) |
| `0x93ee10` | 590 | 2 | `shape only` | has a backward branch (often a loop), 156 ins | has a backward branch (often a loop) |
| `0x93f660` | 590 | 8 | `shape only` | has a backward branch (often a loop), 156 ins | has a backward branch (often a loop) |
| `0x4b320` | 589 | 2 | `shape only` | has a backward branch (often a loop), 172 ins | has a backward branch (often a loop) |
| `0x521f90` | 589 | 7 | `shape only` | has a backward branch (often a loop), 137 ins | has a backward branch (often a loop) |
| `0x534610` | 588 | 3 | `shape only` | has a backward branch (often a loop), 153 ins | has a backward branch (often a loop) |
| `0x57cc20` | 588 | 3 | `shape only` | has a backward branch (often a loop), 178 ins | has a backward branch (often a loop) |
| `0x8e77c0` | 588 | 2 | `shape only` | has a backward branch (often a loop), 163 ins | has a backward branch (often a loop) |
| `0x956f60` | 587 | 2 | `shape only` | has a backward branch (often a loop), 147 ins | has a backward branch (often a loop) |
| `0x154230` | 586 | 2 | `shape only` | has a backward branch (often a loop), 175 ins | has a backward branch (often a loop) |
| `0x258430` | 586 | 2 | `shape only` | has a backward branch (often a loop), 152 ins | has a backward branch (often a loop) |
| `0x2587b0` | 586 | 3 | `shape only` | has a backward branch (often a loop), 175 ins | has a backward branch (often a loop) |
| `0x6cbc30` | 586 | 3 | `shape only` | has a backward branch (often a loop), 156 ins | has a backward branch (often a loop) |
| `0x7794a0` | 586 | 4 | `shape only` | has a backward branch (often a loop), 148 ins | has a backward branch (often a loop) |
| `0x25fdb0` | 585 | 2 | `shape only` | has a backward branch (often a loop), 149 ins | has a backward branch (often a loop) |
| `0x1d3810` | 584 | 6 | `shape only` | has a backward branch (often a loop), 161 ins | has a backward branch (often a loop) |
| `0x908640` | 583 | 5 | `shape only` | has a backward branch (often a loop), 168 ins | has a backward branch (often a loop) |
| `0x1de600` | 581 | 2 | `shape only` | has a backward branch (often a loop), 132 ins | has a backward branch (often a loop) |
| `0x8b8820` | 581 | 2 | `shape only` | has a backward branch (often a loop), 144 ins | has a backward branch (often a loop) |
| `0x8d0840` | 581 | 2 | `shape only` | has a backward branch (often a loop), 153 ins | has a backward branch (often a loop) |
| `0x8d0d30` | 581 | 2 | `shape only` | has a backward branch (often a loop), 153 ins | has a backward branch (often a loop) |
| `0x8d1220` | 581 | 2 | `shape only` | has a backward branch (often a loop), 153 ins | has a backward branch (often a loop) |
| `0x8d20a0` | 581 | 3 | `shape only` | has a backward branch (often a loop), 168 ins | has a backward branch (often a loop) |
| `0x95f430` | 580 | 2 | `shape only` | has a backward branch (often a loop), 143 ins | has a backward branch (often a loop) |
| `0x95f680` | 580 | 2 | `shape only` | has a backward branch (often a loop), 143 ins | has a backward branch (often a loop) |
| `0x95fcc0` | 580 | 2 | `shape only` | has a backward branch (often a loop), 143 ins | has a backward branch (often a loop) |
| `0xadad0` | 579 | 3 | `shape only` | has a backward branch (often a loop), 139 ins | has a backward branch (often a loop) |
| `0xc18d0` | 578 | 7 | `shape only` | has a backward branch (often a loop), 142 ins | has a backward branch (often a loop) |
| `0x1628b0` | 578 | 2 | `shape only` | has a backward branch (often a loop), 137 ins | has a backward branch (often a loop) |
| `0x261510` | 578 | 4 | `shape only` | has a backward branch (often a loop), 152 ins | has a backward branch (often a loop) |
| `0xaddf0` | 577 | 8 | `shape only` | has a backward branch (often a loop), 119 ins | has a backward branch (often a loop) |
| `0xf6dc0` | 577 | 4 | `shape only` | has a backward branch (often a loop), 165 ins | has a backward branch (often a loop) |
| `0xf7010` | 577 | 6 | `shape only` | has a backward branch (often a loop), 165 ins | has a backward branch (often a loop) |
| `0x1aaca0` | 577 | 4 | `shape only` | has a backward branch (often a loop), 123 ins | has a backward branch (often a loop) |
| `0x542480` | 576 | 2 | `shape only` | has a backward branch (often a loop), 158 ins | has a backward branch (often a loop) |
| `0x937240` | 576 | 2 | `shape only` | has a backward branch (often a loop), 163 ins | has a backward branch (often a loop) |
| `0x95a3b0` | 576 | 2 | `shape only` | has a backward branch (often a loop), 159 ins | has a backward branch (often a loop) |
| `0x251560` | 573 | 2 | `shape only` | has a backward branch (often a loop), 139 ins | has a backward branch (often a loop) |
| `0x7391c0` | 573 | 13 | `shape only` | has a backward branch (often a loop), 145 ins | has a backward branch (often a loop) |
| `0x739400` | 573 | 5 | `shape only` | has a backward branch (often a loop), 145 ins | has a backward branch (often a loop) |
| `0x162670` | 572 | 2 | `shape only` | has a backward branch (often a loop), 135 ins | has a backward branch (often a loop) |
| `0x1b7d40` | 572 | 3 | `shape only` | has a backward branch (often a loop), 141 ins | has a backward branch (often a loop) |
| `0x8b3d60` | 572 | 2 | `shape only` | has a backward branch (often a loop), 149 ins | has a backward branch (often a loop) |
| `0x7c7e70` | 571 | 4 | `strings` | cns_no_fit.cpp \| it != m_sheet_number.end() | has a backward branch (often a loop) |
| `0x14ae20` | 570 | 2 | `shape only` | has a backward branch (often a loop), 136 ins | has a backward branch (often a loop) |
| `0x7dc360` | 569 | 5 | `shape only` | has a backward branch (often a loop), 149 ins | has a backward branch (often a loop) |
| `0x8bf680` | 569 | 6 | `shape only` | has a backward branch (often a loop), 151 ins | has a backward branch (often a loop) |
| `0x93ab30` | 569 | 2 | `shape only` | has a backward branch (often a loop), 157 ins | has a backward branch (often a loop) |
| `0x8c040` | 567 | 2 | `shape only` | has a backward branch (often a loop), 150 ins | has a backward branch (often a loop) |
| `0xbb070` | 567 | 2 | `shape only` | has a backward branch (often a loop), 134 ins | has a backward branch (often a loop) |
| `0x10efa0` | 567 | 2 | `strings` | ValueNames \| basic_string::append | has a backward branch (often a loop) |
| `0x1a3670` | 567 | 4 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x60cd20` | 567 | 2 | `shape only` | has a backward branch (often a loop), 163 ins | has a backward branch (often a loop) |
| `0x19a00` | 565 | 4 | `shape only` | has a backward branch (often a loop), 169 ins | has a backward branch (often a loop) |
| `0x1c55f0` | 565 | 4 | `shape only` | has a backward branch (often a loop), 166 ins | has a backward branch (often a loop) |
| `0x4fc6f0` | 565 | 5 | `strings` | ..\structure\problem.cpp \| number < GetNumberOfParts() | has a backward branch (often a loop) |
| `0x8d0a90` | 565 | 2 | `shape only` | has a backward branch (often a loop), 151 ins | has a backward branch (often a loop) |
| `0x8d0f80` | 565 | 2 | `shape only` | has a backward branch (often a loop), 151 ins | has a backward branch (often a loop) |
| `0x8d1470` | 565 | 2 | `shape only` | has a backward branch (often a loop), 151 ins | has a backward branch (often a loop) |
| `0x12a990` | 564 | 2 | `shape only` | has a backward branch (often a loop), 120 ins | has a backward branch (often a loop) |
| `0x925ab0` | 564 | 4 | `shape only` | has a backward branch (often a loop), 160 ins | has a backward branch (often a loop) |
| `0x64b480` | 563 | 2 | `strings` | ->  | has a backward branch (often a loop) |
| `0x8ad9c0` | 563 | 6 | `shape only` | has a backward branch (often a loop), 141 ins | has a backward branch (often a loop) |
| `0x902440` | 563 | 2 | `shape only` | has a backward branch (often a loop), 139 ins | has a backward branch (often a loop) |
| `0x95d800` | 562 | 2 | `shape only` | has a backward branch (often a loop), 129 ins | has a backward branch (often a loop) |
| `0x95da40` | 562 | 2 | `shape only` | has a backward branch (often a loop), 129 ins | has a backward branch (often a loop) |
| `0x15a5d0` | 561 | 2 | `shape only` | has a backward branch (often a loop), 133 ins | has a backward branch (often a loop) |
| `0x527870` | 561 | 2 | `strings` | sheet \| ..\structure\stats.cpp | has a backward branch (often a loop) |
| `0x5e7110` | 561 | 3 | `shape only` | has a backward branch (often a loop), 153 ins | has a backward branch (often a loop) |
| `0x798070` | 561 | 5 | `strings` | basic_string::_M_construct null not vali \| basic_string::append | has a backward branch (often a loop) |
| `0x1174a0` | 560 | 5 | `strings` | WVSH | has a backward branch (often a loop) |
| `0x1de3d0` | 560 | 3 | `shape only` | has a backward branch (often a loop), 126 ins | has a backward branch (often a loop) |
| `0x5cdc60` | 560 | 2 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x5e7c40` | 560 | 4 | `shape only` | has a backward branch (often a loop), 151 ins | has a backward branch (often a loop) |
| `0x624490` | 560 | 3 | `shape only` | has a backward branch (often a loop), 164 ins | has a backward branch (often a loop) |
| `0x67ef20` | 560 | 3 | `shape only` | has a backward branch (often a loop), 145 ins | has a backward branch (often a loop) |
| `0x89ef70` | 560 | 5 | `shape only` | has a backward branch (often a loop), 156 ins | has a backward branch (often a loop) |
| `0x61b420` | 557 | 2 | `shape only` | has a backward branch (often a loop), 155 ins | has a backward branch (often a loop) |
| `0x8a5370` | 556 | 2 | `shape only` | has a backward branch (often a loop), 153 ins | has a backward branch (often a loop) |
| `0x8a7b30` | 556 | 2 | `shape only` | has a backward branch (often a loop), 153 ins | has a backward branch (often a loop) |
| `0x522b30` | 555 | 4 | `shape only` | has a backward branch (often a loop), 129 ins | has a backward branch (often a loop) |
| `0x526460` | 555 | 8 | `shape only` | has a backward branch (often a loop), 133 ins | has a backward branch (often a loop) |
| `0x5269a0` | 555 | 11 | `shape only` | has a backward branch (often a loop), 133 ins | has a backward branch (often a loop) |
| `0x154bc0` | 554 | 3 | `shape only` | has a backward branch (often a loop), 129 ins | has a backward branch (often a loop) |
| `0x418fe0` | 554 | 3 | `shape only` | has a backward branch (often a loop), 161 ins | has a backward branch (often a loop) |
| `0x8f2d00` | 554 | 11 | `shape only` | has a backward branch (often a loop), 169 ins | has a backward branch (often a loop) |
| `0x4f3810` | 553 | 2 | `shape only` | has a backward branch (often a loop), 139 ins | has a backward branch (often a loop) |
| `0x65f120` | 553 | 3 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x6db910` | 553 | 2 | `shape only` | has a backward branch (often a loop), 127 ins | has a backward branch (often a loop) |
| `0xaeaf0` | 552 | 3 | `shape only` | has a backward branch (often a loop), 159 ins | has a backward branch (often a loop) |
| `0x54cc00` | 552 | 2 | `shape only` | has a backward branch (often a loop), 122 ins | has a backward branch (often a loop) |
| `0x54cea0` | 552 | 3 | `shape only` | has a backward branch (often a loop), 122 ins | has a backward branch (often a loop) |
| `0x87b6a0` | 552 | 2 | `shape only` | has a backward branch (often a loop), 147 ins | has a backward branch (often a loop) |
| `0x8e6f30` | 552 | 3 | `shape only` | has a backward branch (often a loop), 158 ins | has a backward branch (often a loop) |
| `0x1fd180` | 551 | 6 | `shape only` | straight line / call sequence, 78 ins | straight line / call sequence |
| `0x4e81b0` | 551 | 3 | `shape only` | has a backward branch (often a loop), 127 ins | has a backward branch (often a loop) |
| `0x533fa0` | 551 | 4 | `shape only` | has a backward branch (often a loop), 161 ins | has a backward branch (often a loop) |
| `0x8c360` | 550 | 2 | `shape only` | has a backward branch (often a loop), 123 ins | has a backward branch (often a loop) |
| `0x707830` | 550 | 3 | `shape only` | has a backward branch (often a loop), 101 ins | has a backward branch (often a loop) |
| `0x5cf480` | 549 | 5 | `shape only` | straight line / call sequence, 120 ins | straight line / call sequence |
| `0x4ba970` | 548 | 2 | `shape only` | has a backward branch (often a loop), 118 ins | has a backward branch (often a loop) |
| `0x555d40` | 548 | 3 | `shape only` | has a backward branch (often a loop), 156 ins | has a backward branch (often a loop) |
| `0x9863e0` | 548 | 2 | `shape only` | has a backward branch (often a loop), 139 ins | has a backward branch (often a loop) |
| `0x64c480` | 547 | 2 | `strings` | ->  | has a backward branch (often a loop) |
| `0x64e200` | 547 | 2 | `shape only` | has a backward branch (often a loop), 130 ins | has a backward branch (often a loop) |
| `0x72d5b0` | 546 | 3 | `shape only` | has a backward branch (often a loop), 132 ins | has a backward branch (often a loop) |
| `0x868490` | 545 | 57 | `callers` | called by 0x9330 NewNoFitNesting; 0x9af0 NewNoFitContext | has a backward branch (often a loop) |
| `0x868d40` | 545 | 5 | `shape only` | has a backward branch (often a loop), 149 ins | has a backward branch (often a loop) |
| `0x16c4c0` | 544 | 5 | `shape only` | has a backward branch (often a loop), 121 ins | has a backward branch (often a loop) |
| `0x598760` | 544 | 6 | `shape only` | has a backward branch (often a loop), 148 ins | has a backward branch (often a loop) |
| `0x7de1b0` | 544 | 7 | `shape only` | has a backward branch (often a loop), 140 ins | has a backward branch (often a loop) |
| `0x1c3200` | 543 | 2 | `strings` | mm Final # | has a backward branch (often a loop) |
| `0x24f420` | 543 | 2 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x66fd80` | 543 | 3 | `shape only` | has a backward branch (often a loop), 166 ins | has a backward branch (often a loop) |
| `0x89e2b0` | 541 | 1 | `shape only` | has a backward branch (often a loop), 160 ins | has a backward branch (often a loop) |
| `0x4f9c60` | 540 | 7 | `shape only` | has a backward branch (often a loop), 122 ins | has a backward branch (often a loop) |
| `0x506780` | 540 | 2 | `strings` | border_property \| geometry | has a backward branch (often a loop) |
| `0x6dd270` | 540 | 2 | `shape only` | has a backward branch (often a loop), 123 ins | has a backward branch (often a loop) |
| `0x8d3230` | 540 | 2 | `shape only` | has a backward branch (often a loop), 145 ins | has a backward branch (often a loop) |
| `0x968b50` | 540 | 2 | `shape only` | has a backward branch (often a loop), 130 ins | has a backward branch (often a loop) |
| `0x968d70` | 540 | 2 | `shape only` | has a backward branch (often a loop), 130 ins | has a backward branch (often a loop) |
| `0x5f4560` | 539 | 4 | `strings` | Po\| | has a backward branch (often a loop) |
| `0x8686c0` | 538 | 11 | `shape only` | has a backward branch (often a loop), 149 ins | has a backward branch (often a loop) |
| `0x9c060` | 537 | 2 | `shape only` | has a backward branch (often a loop), 118 ins | has a backward branch (often a loop) |
| `0x6846c0` | 537 | 11 | `shape only` | has a backward branch (often a loop), 120 ins | has a backward branch (often a loop) |
| `0x902220` | 535 | 2 | `shape only` | has a backward branch (often a loop), 153 ins | has a backward branch (often a loop) |
| `0x8971e0` | 533 | 2 | `shape only` | has a backward branch (often a loop), 141 ins | has a backward branch (often a loop) |
| `0x64d0f0` | 532 | 3 | `strings` | ->  | has a backward branch (often a loop) |
| `0x64d5a0` | 532 | 2 | `strings` | ->  | has a backward branch (often a loop) |
| `0x202ea0` | 531 | 2 | `shape only` | has a backward branch (often a loop), 118 ins | has a backward branch (often a loop) |
| `0x5d1360` | 531 | 4 | `shape only` | has a backward branch (often a loop), 130 ins | has a backward branch (often a loop) |
| `0x64c070` | 531 | 2 | `strings` | ->  | has a backward branch (often a loop) |
| `0x64dd40` | 531 | 2 | `strings` | ->  | has a backward branch (often a loop) |
| `0x4f73e0` | 530 | 13 | `shape only` | has a backward branch (often a loop), 123 ins | has a backward branch (often a loop) |
| `0x25de10` | 528 | 2 | `shape only` | has a backward branch (often a loop), 136 ins | has a backward branch (often a loop) |
| `0x522d60` | 528 | 6 | `shape only` | has a backward branch (often a loop), 126 ins | has a backward branch (often a loop) |
| `0x5cd5c0` | 528 | 16 | `shape only` | has a backward branch (often a loop), 125 ins | has a backward branch (often a loop) |
| `0x873470` | 528 | 6 | `shape only` | has a backward branch (often a loop), 158 ins | has a backward branch (often a loop) |
| `0x89d0e0` | 527 | 3 | `shape only` | has a backward branch (often a loop), 151 ins | has a backward branch (often a loop) |
| `0x57e580` | 526 | 2 | `shape only` | has a backward branch (often a loop), 145 ins | has a backward branch (often a loop) |
| `0x87bd10` | 522 | 2 | `shape only` | has a backward branch (often a loop), 152 ins | has a backward branch (often a loop) |
| `0x87c1b0` | 522 | 2 | `shape only` | has a backward branch (often a loop), 152 ins | has a backward branch (often a loop) |
| `0x8f9f10` | 522 | 2 | `shape only` | has a backward branch (often a loop), 139 ins | has a backward branch (often a loop) |
| `0x900db0` | 522 | 2 | `shape only` | has a backward branch (often a loop), 142 ins | has a backward branch (often a loop) |
| `0x5d1f70` | 521 | 2 | `shape only` | has a backward branch (often a loop), 143 ins | has a backward branch (often a loop) |
| `0x4e3120` | 520 | 3 | `shape only` | has a backward branch (often a loop), 123 ins | has a backward branch (often a loop) |
| `0x780290` | 520 | 13 | `strings` | memcpy_s: buffer overflow | has a backward branch (often a loop) |
| `0x8e2b40` | 520 | 2 | `shape only` | has a backward branch (often a loop), 141 ins | has a backward branch (often a loop) |
| `0x935b70` | 520 | 2 | `shape only` | has a backward branch (often a loop), 143 ins | has a backward branch (often a loop) |
| `0x92a6d0` | 519 | 3 | `shape only` | has a backward branch (often a loop), 132 ins | has a backward branch (often a loop) |
| `0x8f790` | 516 | 2 | `shape only` | has a backward branch (often a loop), 128 ins | has a backward branch (often a loop) |
| `0x583600` | 515 | 2 | `shape only` | has a backward branch (often a loop), 135 ins | has a backward branch (often a loop) |
| `0x64cd90` | 515 | 2 | `strings` | ->  | has a backward branch (often a loop) |
| `0x721de0` | 515 | 2 | `shape only` | has a backward branch (often a loop), 127 ins | has a backward branch (often a loop) |
| `0x723910` | 515 | 2 | `shape only` | has a backward branch (often a loop), 127 ins | has a backward branch (often a loop) |
| `0x154480` | 514 | 2 | `strings` | GetPartsContribution \| :   | has a backward branch (often a loop) |
| `0x8c720` | 513 | 2 | `shape only` | has a backward branch (often a loop), 119 ins | has a backward branch (often a loop) |
| `0x4f8d70` | 513 | 5 | `shape only` | has a backward branch (often a loop), 117 ins | has a backward branch (often a loop) |
| `0x4fca80` | 513 | 8 | `strings` | ..\structure\problem.cpp \| it != m_implementation->parts.end() | has a backward branch (often a loop) |
| `0x8d49d0` | 513 | 4 | `shape only` | has a backward branch (often a loop), 135 ins | has a backward branch (often a loop) |
| `0x25a20` | 512 | 2 | `shape only` | has a backward branch (often a loop), 129 ins | has a backward branch (often a loop) |
| `0x510a90` | 512 | 2 | `strings` | ..\structure\svg_io.cpp \| s && "can not find sheet." | has a backward branch (often a loop) |
| `0x96b060` | 511 | 2 | `shape only` | has a backward branch (often a loop), 141 ins | has a backward branch (often a loop) |
| `0x89ed70` | 510 | 5 | `shape only` | has a backward branch (often a loop), 137 ins | has a backward branch (often a loop) |
| `0x25ad80` | 509 | 2 | `shape only` | has a backward branch (often a loop), 149 ins | has a backward branch (often a loop) |
| `0x418bd0` | 509 | 26 | `shape only` | has a backward branch (often a loop), 144 ins | has a backward branch (often a loop) |
| `0x97ecc0` | 509 | 2 | `shape only` | has a backward branch (often a loop), 142 ins | has a backward branch (often a loop) |
| `0x15fcb0` | 508 | 5 | `shape only` | has a backward branch (often a loop), 124 ins | has a backward branch (often a loop) |
| `0x61f30` | 507 | 2 | `shape only` | has a backward branch (often a loop), 119 ins | has a backward branch (often a loop) |
| `0x5865c0` | 507 | 17 | `shape only` | has a backward branch (often a loop), 151 ins | has a backward branch (often a loop) |
| `0x5d7070` | 507 | 7 | `shape only` | has a backward branch (often a loop), 123 ins | has a backward branch (often a loop) |
| `0x89a240` | 506 | 1 | `shape only` | has a backward branch (often a loop), 91 ins | has a backward branch (often a loop) |
| `0x4dcd90` | 502 | 3 | `shape only` | has a backward branch (often a loop), 117 ins | has a backward branch (often a loop) |
| `0x6dbb40` | 501 | 2 | `shape only` | has a backward branch (often a loop), 128 ins | has a backward branch (often a loop) |
| `0x8e1bd0` | 501 | 2 | `shape only` | has a backward branch (often a loop), 136 ins | has a backward branch (often a loop) |
| `0x8e2d50` | 501 | 3 | `shape only` | has a backward branch (often a loop), 136 ins | has a backward branch (often a loop) |
| `0x160c90` | 500 | 4 | `shape only` | has a backward branch (often a loop), 140 ins | has a backward branch (often a loop) |
| `0x966840` | 500 | 2 | `shape only` | has a backward branch (often a loop), 120 ins | has a backward branch (often a loop) |
| `0x64e430` | 499 | 3 | `shape only` | has a backward branch (often a loop), 131 ins | has a backward branch (often a loop) |
| `0x8a0de0` | 499 | 4 | `shape only` | has a backward branch (often a loop), 138 ins | has a backward branch (often a loop) |
| `0x13a820` | 498 | 2 | `shape only` | has a backward branch (often a loop), 143 ins | has a backward branch (often a loop) |
| `0x13aa20` | 498 | 2 | `shape only` | has a backward branch (often a loop), 143 ins | has a backward branch (often a loop) |
| `0x51d0f0` | 498 | 12 | `shape only` | has a backward branch (often a loop), 117 ins | has a backward branch (often a loop) |
| `0x51c260` | 496 | 12 | `shape only` | has a backward branch (often a loop), 116 ins | has a backward branch (often a loop) |
| `0x5524b0` | 496 | 2 | `strings` | [Cluster : time= \|  nb_parsed= | has a backward branch (often a loop) |
| `0x966a40` | 496 | 2 | `shape only` | has a backward branch (often a loop), 118 ins | has a backward branch (often a loop) |
| `0x7bbcd0` | 495 | 3 | `shape only` | has a backward branch (often a loop), 130 ins | has a backward branch (often a loop) |
| `0x909e40` | 495 | 2 | `shape only` | has a backward branch (often a loop), 144 ins | has a backward branch (often a loop) |
| `0x9681c0` | 495 | 3 | `shape only` | has a backward branch (often a loop), 124 ins | has a backward branch (often a loop) |
| `0x11a340` | 494 | 11 | `shape only` | has a backward branch (often a loop), 143 ins | has a backward branch (often a loop) |
| `0x1f0700` | 494 | 3 | `shape only` | has a backward branch (often a loop), 144 ins | has a backward branch (often a loop) |
| `0x98e580` | 494 | 2 | `shape only` | has a backward branch (often a loop), 163 ins | has a backward branch (often a loop) |
| `0x5670` | 493 | 2 | `shape only` | has a backward branch (often a loop), 126 ins | has a backward branch (often a loop) |
| `0x61d40` | 492 | 2 | `shape only` | has a backward branch (often a loop), 116 ins | has a backward branch (often a loop) |
| `0x266e00` | 492 | 4 | `shape only` | has a backward branch (often a loop), 134 ins | has a backward branch (often a loop) |
| `0x598dd0` | 492 | 2 | `shape only` | has a backward branch (often a loop), 119 ins | has a backward branch (often a loop) |
| `0x701c90` | 492 | 2 | `shape only` | has a backward branch (often a loop), 131 ins | has a backward branch (often a loop) |
| `0x8d4d90` | 492 | 2 | `shape only` | has a backward branch (often a loop), 135 ins | has a backward branch (often a loop) |
| `0x89b5c0` | 491 | 2 | `shape only` | has a backward branch (often a loop), 134 ins | has a backward branch (often a loop) |
| `0x2304d0` | 490 | 4 | `shape only` | has a backward branch (often a loop), 122 ins | has a backward branch (often a loop) |
| `0x580a00` | 489 | 4 | `shape only` | has a backward branch (often a loop), 137 ins | has a backward branch (often a loop) |
| `0x4f7070` | 488 | 8 | `shape only` | has a backward branch (often a loop), 114 ins | has a backward branch (often a loop) |
| `0x6d6680` | 488 | 5 | `shape only` | has a backward branch (often a loop), 126 ins | has a backward branch (often a loop) |
| `0x138f20` | 487 | 2 | `shape only` | has a backward branch (often a loop), 128 ins | has a backward branch (often a loop) |
| `0x8ab960` | 487 | 9 | `shape only` | has a backward branch (often a loop), 141 ins | has a backward branch (often a loop) |
| `0x8c1050` | 487 | 3 | `shape only` | has a backward branch (often a loop), 141 ins | has a backward branch (often a loop) |
| `0x14fb10` | 486 | 2 | `shape only` | has a backward branch (often a loop), 120 ins | has a backward branch (often a loop) |
| `0x5fd870` | 486 | 4 | `strings` | VSH \| Comments must start with / | has a backward branch (often a loop) |
| `0x8f5d50` | 486 | 8 | `shape only` | has a backward branch (often a loop), 133 ins | has a backward branch (often a loop) |
| `0x95c9d0` | 485 | 2 | `shape only` | has a backward branch (often a loop), 137 ins | has a backward branch (often a loop) |
| `0x14b130` | 484 | 2 | `shape only` | has a backward branch (often a loop), 141 ins | has a backward branch (often a loop) |
| `0x549c70` | 484 | 2 | `shape only` | has a backward branch (often a loop), 141 ins | has a backward branch (often a loop) |
| `0x5ccf20` | 484 | 5 | `shape only` | has a backward branch (often a loop), 120 ins | has a backward branch (often a loop) |
| `0x89fed0` | 484 | 2 | `shape only` | has a backward branch (often a loop), 129 ins | has a backward branch (often a loop) |
| `0x8a0350` | 484 | 2 | `shape only` | has a backward branch (often a loop), 129 ins | has a backward branch (often a loop) |
| `0x92dcf0` | 484 | 4 | `shape only` | has a backward branch (often a loop), 130 ins | has a backward branch (often a loop) |
| `0x5a45c0` | 483 | 2 | `shape only` | has a backward branch (often a loop), 142 ins | has a backward branch (often a loop) |
| `0x64c290` | 483 | 2 | `strings` | ->  | has a backward branch (often a loop) |
| `0x8ec7b0` | 483 | 3 | `shape only` | has a backward branch (often a loop), 132 ins | has a backward branch (often a loop) |
| `0x9876d0` | 483 | 2 | `shape only` | has a backward branch (often a loop), 132 ins | has a backward branch (often a loop) |
| `0xf0fb0` | 482 | 145 | `strings` | UWVSH \| AllocatorBase: requested size would caus | has a backward branch (often a loop) |
| `0x1c7780` | 482 | 2 | `shape only` | has a backward branch (often a loop), 121 ins | has a backward branch (often a loop) |
| `0x8e1170` | 482 | 2 | `shape only` | has a backward branch (often a loop), 129 ins | has a backward branch (often a loop) |
| `0x8fbef0` | 482 | 5 | `shape only` | has a backward branch (often a loop), 122 ins | has a backward branch (often a loop) |
| `0x1331b0` | 481 | 18 | `shape only` | has a backward branch (often a loop), 112 ins | has a backward branch (often a loop) |
| `0x95c40` | 480 | 3 | `shape only` | has a backward branch (often a loop), 141 ins | has a backward branch (often a loop) |
| `0xad630` | 478 | 6 | `shape only` | has a backward branch (often a loop), 116 ins | has a backward branch (often a loop) |
| `0x8f7e30` | 478 | 4 | `shape only` | has a backward branch (often a loop), 140 ins | has a backward branch (often a loop) |
| `0x96f710` | 478 | 8 | `shape only` | has a backward branch (often a loop), 142 ins | has a backward branch (often a loop) |
| `0x162b00` | 477 | 3 | `shape only` | has a backward branch (often a loop), 103 ins | has a backward branch (often a loop) |
| `0x5d0500` | 477 | 5 | `shape only` | has a backward branch (often a loop), 120 ins | has a backward branch (often a loop) |
| `0x707df0` | 477 | 3 | `shape only` | has a backward branch (often a loop), 120 ins | has a backward branch (often a loop) |
| `0x63b70` | 475 | 2 | `shape only` | has a backward branch (often a loop), 125 ins | has a backward branch (often a loop) |
| `0x5e8100` | 475 | 1 | `shape only` | straight line / call sequence, 79 ins | straight line / call sequence |
| `0x89f580` | 475 | 3 | `shape only` | has a backward branch (often a loop), 137 ins | has a backward branch (often a loop) |
| `0x14e720` | 474 | 2 | `shape only` | has a backward branch (often a loop), 130 ins | has a backward branch (often a loop) |
| `0x5e9df0` | 474 | 2 | `shape only` | has a backward branch (often a loop), 130 ins | has a backward branch (often a loop) |
| `0x8e1dd0` | 474 | 4 | `shape only` | has a backward branch (often a loop), 133 ins | has a backward branch (often a loop) |
| `0x95f250` | 474 | 2 | `shape only` | has a backward branch (often a loop), 117 ins | has a backward branch (often a loop) |
| `0x7469b0` | 473 | 3 | `shape only` | has a backward branch (often a loop), 126 ins | has a backward branch (often a loop) |
| `0x86d430` | 473 | 2 | `shape only` | has a backward branch (often a loop), 132 ins | has a backward branch (often a loop) |
| `0x60bf30` | 471 | 2 | `shape only` | has a backward branch (often a loop), 110 ins | has a backward branch (often a loop) |
| `0xf17c0` | 470 | 18 | `strings` | UWVSH \| AllocatorBase: requested size would caus | has a backward branch (often a loop) |
| `0x1a5070` | 470 | 2 | `strings` | RECTANGLE \| LOSANGE | has a backward branch (often a loop) |
| `0x54c460` | 470 | 2 | `shape only` | has a backward branch (often a loop), 133 ins | has a backward branch (often a loop) |
| `0x8cfee0` | 470 | 2 | `shape only` | has a backward branch (often a loop), 127 ins | has a backward branch (often a loop) |
| `0x1cdfe0` | 469 | 2 | `shape only` | has a backward branch (often a loop), 134 ins | has a backward branch (often a loop) |
| `0x52bc70` | 469 | 2 | `shape only` | has a backward branch (often a loop), 134 ins | has a backward branch (often a loop) |
| `0x62f580` | 469 | 2 | `shape only` | has a backward branch (often a loop), 125 ins | has a backward branch (often a loop) |
| `0x681c60` | 468 | 4 | `shape only` | has a backward branch (often a loop), 130 ins | has a backward branch (often a loop) |
| `0x954240` | 468 | 2 | `shape only` | has a backward branch (often a loop), 133 ins | has a backward branch (often a loop) |
| `0x12abd0` | 467 | 2 | `strings` | GetOd \| _GetOd@4 | has a backward branch (often a loop) |
| `0x179bd0` | 467 | 6 | `shape only` | has a backward branch (often a loop), 140 ins | has a backward branch (often a loop) |
| `0x8d47f0` | 466 | 1 | `shape only` | has a backward branch (often a loop), 142 ins | has a backward branch (often a loop) |
| `0x8f10d0` | 466 | 2 | `shape only` | has a backward branch (often a loop), 142 ins | has a backward branch (often a loop) |
| `0x1d16f0` | 465 | 5 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x594ac0` | 465 | 2 | `shape only` | has a backward branch (often a loop), 130 ins | has a backward branch (often a loop) |
| `0x8c6ae0` | 465 | 2 | `shape only` | has a backward branch (often a loop), 127 ins | has a backward branch (often a loop) |
| `0x15a810` | 464 | 2 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x9513a0` | 464 | 2 | `shape only` | has a backward branch (often a loop), 131 ins | has a backward branch (often a loop) |
| `0x17ba00` | 463 | 3 | `shape only` | has a backward branch (often a loop), 134 ins | has a backward branch (often a loop) |
| `0x6d2ea0` | 463 | 6 | `shape only` | has a backward branch (often a loop), 142 ins | has a backward branch (often a loop) |
| `0x6d3070` | 463 | 4 | `shape only` | has a backward branch (often a loop), 142 ins | has a backward branch (often a loop) |
| `0x90a030` | 463 | 2 | `shape only` | has a backward branch (often a loop), 135 ins | has a backward branch (often a loop) |
| `0x90a200` | 463 | 2 | `shape only` | has a backward branch (often a loop), 138 ins | has a backward branch (often a loop) |
| `0x959110` | 463 | 2 | `shape only` | has a backward branch (often a loop), 134 ins | has a backward branch (often a loop) |
| `0x21c770` | 462 | 3 | `shape only` | has a backward branch (often a loop), 119 ins | has a backward branch (often a loop) |
| `0x5e8340` | 462 | 2 | `shape only` | straight line / call sequence, 74 ins | straight line / call sequence |
| `0x5cc8a0` | 461 | 30 | `shape only` | has a backward branch (often a loop), 109 ins | has a backward branch (often a loop) |
| `0x8ba550` | 461 | 11 | `shape only` | has a backward branch (often a loop), 133 ins | has a backward branch (often a loop) |
| `0x4b99b0` | 460 | 2 | `shape only` | has a backward branch (often a loop), 118 ins | has a backward branch (often a loop) |
| `0x896f30` | 460 | 3 | `shape only` | has a backward branch (often a loop), 125 ins | has a backward branch (often a loop) |
| `0x5c3f0` | 459 | 2 | `shape only` | has a backward branch (often a loop), 124 ins | has a backward branch (often a loop) |
| `0x5c1790` | 459 | 7 | `shape only` | has a backward branch (often a loop), 127 ins | has a backward branch (often a loop) |
| `0x8b8250` | 458 | 2 | `shape only` | has a backward branch (often a loop), 132 ins | has a backward branch (often a loop) |
| `0x97eec0` | 458 | 2 | `shape only` | has a backward branch (often a loop), 131 ins | has a backward branch (often a loop) |
| `0x1ec80` | 457 | 2 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x209610` | 457 | 2 | `shape only` | has a backward branch (often a loop), 112 ins | has a backward branch (often a loop) |
| `0x4dca60` | 456 | 5 | `shape only` | has a backward branch (often a loop), 104 ins | has a backward branch (often a loop) |
| `0x57f370` | 456 | 3 | `shape only` | has a backward branch (often a loop), 120 ins | has a backward branch (often a loop) |
| `0x8b8420` | 456 | 5 | `shape only` | has a backward branch (often a loop), 128 ins | has a backward branch (often a loop) |
| `0x8c7f90` | 456 | 2 | `shape only` | has a backward branch (often a loop), 119 ins | has a backward branch (often a loop) |
| `0x8c8160` | 456 | 3 | `shape only` | has a backward branch (often a loop), 119 ins | has a backward branch (often a loop) |
| `0x8dbb70` | 456 | 3 | `shape only` | has a backward branch (often a loop), 122 ins | has a backward branch (often a loop) |
| `0x1346c0` | 455 | 2 | `shape only` | has a backward branch (often a loop), 122 ins | has a backward branch (often a loop) |
| `0x185d20` | 455 | 4 | `shape only` | has a backward branch (often a loop), 129 ins | has a backward branch (often a loop) |
| `0x4ddac0` | 455 | 6 | `shape only` | has a backward branch (often a loop), 91 ins | has a backward branch (often a loop) |
| `0x78f740` | 455 | 32 | `strings` | AllocatorBase: requested size would caus | has a backward branch (often a loop) |
| `0x1d26e0` | 454 | 1 | `shape only` | has a backward branch (often a loop), 111 ins | has a backward branch (often a loop) |
| `0x8b8650` | 454 | 2 | `shape only` | has a backward branch (often a loop), 127 ins | has a backward branch (often a loop) |
| `0x561740` | 453 | 3 | `shape only` | has a backward branch (often a loop), 128 ins | has a backward branch (often a loop) |
| `0x183c50` | 452 | 2 | `shape only` | has a backward branch (often a loop), 123 ins | has a backward branch (often a loop) |
| `0x24edd0` | 452 | 2 | `shape only` | has a backward branch (often a loop), 116 ins | has a backward branch (often a loop) |
| `0x5cbf00` | 452 | 5 | `shape only` | has a backward branch (often a loop), 110 ins | has a backward branch (often a loop) |
| `0x81e80` | 450 | 2 | `shape only` | has a backward branch (often a loop), 137 ins | has a backward branch (often a loop) |
| `0x8d23a0` | 450 | 4 | `shape only` | has a backward branch (often a loop), 122 ins | has a backward branch (often a loop) |
| `0x8d9600` | 450 | 2 | `shape only` | has a backward branch (often a loop), 121 ins | has a backward branch (often a loop) |
| `0x97c4a0` | 450 | 2 | `shape only` | has a backward branch (often a loop), 122 ins | has a backward branch (often a loop) |
| `0x1fbaa0` | 449 | 4 | `shape only` | has a backward branch (often a loop), 122 ins | has a backward branch (often a loop) |
| `0x2248d0` | 449 | 2 | `shape only` | has a backward branch (often a loop), 132 ins | has a backward branch (often a loop) |
| `0x4f8a80` | 449 | 2 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x8f8610` | 449 | 2 | `shape only` | has a backward branch (often a loop), 132 ins | has a backward branch (often a loop) |
| `0x8f87e0` | 449 | 2 | `shape only` | has a backward branch (often a loop), 129 ins | has a backward branch (often a loop) |
| `0x597a0` | 448 | 2 | `shape only` | has a backward branch (often a loop), 116 ins | has a backward branch (often a loop) |
| `0x24b280` | 448 | 8 | `shape only` | straight line / call sequence, 94 ins | straight line / call sequence |
| `0x8adc00` | 448 | 8 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x99910` | 447 | 2 | `shape only` | has a backward branch (often a loop), 119 ins | has a backward branch (often a loop) |
| `0x1d11c0` | 447 | 2 | `shape only` | has a backward branch (often a loop), 137 ins | has a backward branch (often a loop) |
| `0x2337d0` | 447 | 3 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x547dc0` | 447 | 5 | `shape only` | has a backward branch (often a loop), 103 ins | has a backward branch (often a loop) |
| `0x5afdc0` | 447 | 2 | `shape only` | has a backward branch (often a loop), 94 ins | has a backward branch (often a loop) |
| `0x97e530` | 447 | 2 | `shape only` | has a backward branch (often a loop), 129 ins | has a backward branch (often a loop) |
| `0x6d41a0` | 445 | 2 | `shape only` | has a backward branch (often a loop), 91 ins | has a backward branch (often a loop) |
| `0x6f07e0` | 445 | 3 | `shape only` | has a backward branch (often a loop), 124 ins | has a backward branch (often a loop) |
| `0x95b7a0` | 445 | 2 | `shape only` | has a backward branch (often a loop), 136 ins | has a backward branch (often a loop) |
| `0x57bb00` | 443 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x7d10e0` | 443 | 2 | `shape only` | has a backward branch (often a loop), 119 ins | has a backward branch (often a loop) |
| `0x8f1e20` | 443 | 28 | `shape only` | has a backward branch (often a loop), 134 ins | has a backward branch (often a loop) |
| `0x9592e0` | 443 | 3 | `shape only` | has a backward branch (often a loop), 129 ins | has a backward branch (often a loop) |
| `0x9594a0` | 443 | 2 | `shape only` | has a backward branch (often a loop), 129 ins | has a backward branch (often a loop) |
| `0x4da560` | 442 | 2 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x57d160` | 442 | 2 | `shape only` | has a backward branch (often a loop), 142 ins | has a backward branch (often a loop) |
| `0x8c8450` | 442 | 6 | `shape only` | has a backward branch (often a loop), 131 ins | has a backward branch (often a loop) |
| `0x13ac20` | 441 | 2 | `shape only` | has a backward branch (often a loop), 119 ins | has a backward branch (often a loop) |
| `0x64df60` | 441 | 1 | `strings` | ->  | straight line / call sequence |
| `0x41a5a0` | 440 | 6 | `strings` | Unk | straight line / call sequence |
| `0x5cf900` | 440 | 2 | `shape only` | has a backward branch (often a loop), 112 ins | has a backward branch (often a loop) |
| `0x4f3650` | 439 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x956a80` | 439 | 2 | `shape only` | has a backward branch (often a loop), 129 ins | has a backward branch (often a loop) |
| `0x4d9c0` | 438 | 3 | `shape only` | has a backward branch (often a loop), 127 ins | has a backward branch (often a loop) |
| `0x717100` | 438 | 3 | `shape only` | has a backward branch (often a loop), 116 ins | has a backward branch (often a loop) |
| `0x8bf4c0` | 438 | 2 | `shape only` | has a backward branch (often a loop), 122 ins | has a backward branch (often a loop) |
| `0x13b960` | 437 | 2 | `shape only` | has a backward branch (often a loop), 128 ins | has a backward branch (often a loop) |
| `0x17ff40` | 437 | 18 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x56a0b0` | 437 | 3 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x6e8e90` | 437 | 3 | `shape only` | has a backward branch (often a loop), 99 ins | has a backward branch (often a loop) |
| `0x64b2c0` | 435 | 3 | `strings` | ->  | has a backward branch (often a loop) |
| `0x64b960` | 435 | 3 | `strings` | ->  | has a backward branch (often a loop) |
| `0x64beb0` | 435 | 4 | `strings` | ->  | has a backward branch (often a loop) |
| `0x9252b0` | 435 | 2 | `shape only` | has a backward branch (often a loop), 136 ins | has a backward branch (often a loop) |
| `0x4f9200` | 434 | 22 | `shape only` | has a backward branch (often a loop), 97 ins | has a backward branch (often a loop) |
| `0x5ceb90` | 434 | 1 | `shape only` | straight line / call sequence, 88 ins | straight line / call sequence |
| `0x29c550` | 433 | 6 | `shape only` | has a backward branch (often a loop), 120 ins | has a backward branch (often a loop) |
| `0x419300` | 433 | 3 | `shape only` | has a backward branch (often a loop), 127 ins | has a backward branch (often a loop) |
| `0x6451c0` | 433 | 3 | `shape only` | has a backward branch (often a loop), 121 ins | has a backward branch (often a loop) |
| `0x4fb400` | 432 | 2 | `shape only` | has a backward branch (often a loop), 109 ins | has a backward branch (often a loop) |
| `0x87b380` | 432 | 2 | `shape only` | has a backward branch (often a loop), 122 ins | has a backward branch (often a loop) |
| `0x8d4be0` | 432 | 18 | `shape only` | has a backward branch (often a loop), 125 ins | has a backward branch (often a loop) |
| `0x935d80` | 432 | 2 | `shape only` | has a backward branch (often a loop), 137 ins | has a backward branch (often a loop) |
| `0x9538f0` | 432 | 2 | `shape only` | has a backward branch (often a loop), 133 ins | has a backward branch (often a loop) |
| `0x240d0` | 431 | 2 | `shape only` | has a backward branch (often a loop), 118 ins | has a backward branch (often a loop) |
| `0x599870` | 431 | 3 | `shape only` | has a backward branch (often a loop), 128 ins | has a backward branch (often a loop) |
| `0x5cfe60` | 431 | 1 | `shape only` | straight line / call sequence, 101 ins | straight line / call sequence |
| `0x8761e0` | 431 | 1 | `shape only` | has a backward branch (often a loop), 126 ins | has a backward branch (often a loop) |
| `0x876390` | 431 | 2 | `shape only` | has a backward branch (often a loop), 126 ins | has a backward branch (often a loop) |
| `0xf4830` | 430 | 5 | `shape only` | has a backward branch (often a loop), 125 ins | has a backward branch (often a loop) |
| `0x239c80` | 430 | 2 | `shape only` | has a backward branch (often a loop), 119 ins | has a backward branch (often a loop) |
| `0x9243d0` | 430 | 2 | `shape only` | has a backward branch (often a loop), 124 ins | has a backward branch (often a loop) |
| `0x97b60` | 429 | 2 | `shape only` | has a backward branch (often a loop), 120 ins | has a backward branch (often a loop) |
| `0x4fd130` | 429 | 2 | `shape only` | has a backward branch (often a loop), 99 ins | has a backward branch (often a loop) |
| `0x892830` | 429 | 2 | `shape only` | has a backward branch (often a loop), 115 ins | has a backward branch (often a loop) |
| `0x5b3e20` | 428 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x95b5f0` | 428 | 2 | `shape only` | has a backward branch (often a loop), 129 ins | has a backward branch (often a loop) |
| `0x1cc0` | 427 | 2 | `strings` | // LocalCancel waiting for threads termi | has a backward branch (often a loop) |
| `0x5d90` | 427 | 2 | `strings` | // LocalTerminate waiting for threads te | has a backward branch (often a loop) |
| `0x547c10` | 427 | 3 | `shape only` | has a backward branch (often a loop), 106 ins | has a backward branch (often a loop) |
| `0x86cad0` | 426 | 3 | `shape only` | has a backward branch (often a loop), 117 ins | has a backward branch (often a loop) |
| `0x86d1a0` | 426 | 3 | `shape only` | has a backward branch (often a loop), 117 ins | has a backward branch (often a loop) |
| `0x86d740` | 426 | 3 | `shape only` | has a backward branch (often a loop), 117 ins | has a backward branch (often a loop) |
| `0x87b8d0` | 426 | 2 | `shape only` | has a backward branch (often a loop), 118 ins | has a backward branch (often a loop) |
| `0x172190` | 425 | 9 | `shape only` | has a backward branch (often a loop), 116 ins | has a backward branch (often a loop) |
| `0x1c0bf0` | 425 | 8 | `shape only` | has a backward branch (often a loop), 123 ins | has a backward branch (often a loop) |
| `0x3dad30` | 425 | 5 | `shape only` | straight line / call sequence, 75 ins | straight line / call sequence |
| `0x4f1590` | 425 | 3 | `shape only` | has a backward branch (often a loop), 112 ins | has a backward branch (often a loop) |
| `0x505430` | 424 | 2 | `strings` | authorizations | has a backward branch (often a loop) |
| `0x5e7e70` | 424 | 3 | `shape only` | has a backward branch (often a loop), 118 ins | has a backward branch (often a loop) |
| `0x97e140` | 424 | 2 | `shape only` | has a backward branch (often a loop), 124 ins | has a backward branch (often a loop) |
| `0x23f440` | 423 | 3 | `shape only` | has a backward branch (often a loop), 126 ins | has a backward branch (often a loop) |
| `0x6e8600` | 423 | 3 | `shape only` | has a backward branch (often a loop), 118 ins | has a backward branch (often a loop) |
| `0x6e8b00` | 423 | 3 | `shape only` | has a backward branch (often a loop), 118 ins | has a backward branch (often a loop) |
| `0x8be780` | 423 | 2 | `shape only` | has a backward branch (often a loop), 125 ins | has a backward branch (often a loop) |
| `0x8c0230` | 423 | 7 | `shape only` | has a backward branch (often a loop), 125 ins | has a backward branch (often a loop) |
| `0x8d2fe0` | 423 | 6 | `shape only` | has a backward branch (often a loop), 125 ins | has a backward branch (often a loop) |
| `0x8f0f20` | 423 | 2 | `shape only` | has a backward branch (often a loop), 125 ins | has a backward branch (often a loop) |
| `0x57f7c0` | 422 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x6e8450` | 422 | 3 | `shape only` | has a backward branch (often a loop), 118 ins | has a backward branch (often a loop) |
| `0x202590` | 420 | 4 | `shape only` | has a backward branch (often a loop), 117 ins | has a backward branch (often a loop) |
| `0x29ed80` | 419 | 4 | `shape only` | has a backward branch (often a loop), 78 ins | has a backward branch (often a loop) |
| `0x89f1a0` | 419 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x89fb20` | 419 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x8a55a0` | 419 | 4 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x8a7d60` | 419 | 4 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x5326f0` | 418 | 2 | `shape only` | has a backward branch (often a loop), 127 ins | has a backward branch (often a loop) |
| `0x5b3a40` | 418 | 4 | `shape only` | has a backward branch (often a loop), 127 ins | has a backward branch (often a loop) |
| `0x8b91a0` | 418 | 3 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x8cb960` | 418 | 11 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x8d1710` | 418 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x8f5fd0` | 418 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x908200` | 418 | 3 | `shape only` | has a backward branch (often a loop), 120 ins | has a backward branch (often a loop) |
| `0x1a2ab0` | 417 | 23 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x8aeb30` | 416 | 3 | `shape only` | has a backward branch (often a loop), 128 ins | has a backward branch (often a loop) |
| `0x8aecd0` | 416 | 3 | `shape only` | has a backward branch (often a loop), 128 ins | has a backward branch (often a loop) |
| `0x9a01e0` | 416 | 2 | `shape only` | has a backward branch (often a loop), 106 ins | has a backward branch (often a loop) |
| `0x4ed2e0` | 414 | 3 | `shape only` | has a backward branch (often a loop), 104 ins | has a backward branch (often a loop) |
| `0x549ac0` | 414 | 3 | `shape only` | has a backward branch (often a loop), 93 ins | has a backward branch (often a loop) |
| `0x65c320` | 414 | 2 | `strings` | Expected_time  \|  real_time  | straight line / call sequence |
| `0x8a9370` | 414 | 2 | `shape only` | has a backward branch (often a loop), 108 ins | has a backward branch (often a loop) |
| `0x6471e0` | 413 | 2 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x785bc0` | 413 | 5 | `strings` | basic_string::_M_construct null not vali \| basic_string::append | has a backward branch (often a loop) |
| `0x8b93b0` | 413 | 2 | `shape only` | has a backward branch (often a loop), 131 ins | has a backward branch (often a loop) |
| `0x8668d0` | 412 | 38 | `shape only` | has a backward branch (often a loop), 121 ins | has a backward branch (often a loop) |
| `0x901dc0` | 412 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x452f0` | 411 | 16 | `shape only` | has a backward branch (often a loop), 115 ins | has a backward branch (often a loop) |
| `0x900fc0` | 411 | 2 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x14b820` | 410 | 3 | `shape only` | has a backward branch (often a loop), 127 ins | has a backward branch (often a loop) |
| `0x901c20` | 410 | 2 | `shape only` | has a backward branch (often a loop), 111 ins | has a backward branch (often a loop) |
| `0x901f60` | 410 | 3 | `shape only` | has a backward branch (often a loop), 111 ins | has a backward branch (often a loop) |
| `0x905b60` | 410 | 2 | `shape only` | has a backward branch (often a loop), 111 ins | has a backward branch (often a loop) |
| `0x5fe060` | 409 | 48 | `shape only` | has a backward branch (often a loop), 119 ins | has a backward branch (often a loop) |
| `0x626980` | 409 | 4 | `shape only` | has a backward branch (often a loop), 122 ins | has a backward branch (often a loop) |
| `0x6e8960` | 409 | 3 | `shape only` | has a backward branch (often a loop), 115 ins | has a backward branch (often a loop) |
| `0x1e140` | 408 | 3 | `shape only` | has a backward branch (often a loop), 116 ins | has a backward branch (often a loop) |
| `0x1e2e0` | 408 | 3 | `shape only` | has a backward branch (often a loop), 116 ins | has a backward branch (often a loop) |
| `0x716da0` | 408 | 2 | `shape only` | has a backward branch (often a loop), 110 ins | has a backward branch (often a loop) |
| `0x923110` | 408 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x923480` | 408 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x9237f0` | 408 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x925f30` | 408 | 4 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x92ab70` | 408 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x9314f0` | 408 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x931e50` | 408 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x932b80` | 408 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x933350` | 408 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x934460` | 408 | 4 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x934aa0` | 408 | 4 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x9378d0` | 408 | 9 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x9388a0` | 408 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x939110` | 408 | 5 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x93cef0` | 408 | 5 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x93d090` | 408 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x93d5b0` | 408 | 15 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x93f960` | 408 | 4 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x93fbb0` | 408 | 3 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x9425e0` | 408 | 4 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x942890` | 408 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x942a30` | 408 | 7 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x63d50` | 407 | 2 | `shape only` | has a backward branch (often a loop), 101 ins | has a backward branch (often a loop) |
| `0x260f20` | 407 | 3 | `shape only` | has a backward branch (often a loop), 98 ins | has a backward branch (often a loop) |
| `0x7bbb30` | 406 | 12 | `shape only` | straight line / call sequence, 88 ins | straight line / call sequence |
| `0x906fb0` | 405 | 2 | `shape only` | has a backward branch (often a loop), 112 ins | has a backward branch (often a loop) |
| `0x94b800` | 405 | 2 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x938b20` | 404 | 2 | `shape only` | has a backward branch (often a loop), 135 ins | has a backward branch (often a loop) |
| `0x95a210` | 404 | 2 | `shape only` | has a backward branch (often a loop), 126 ins | has a backward branch (often a loop) |
| `0x5055e0` | 403 | 2 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x7172c0` | 403 | 3 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x5f60` | 402 | 2 | `callers` | called by 0x6100 LaunchComputation | has a backward branch (often a loop) |
| `0x1c0a50` | 402 | 2 | `shape only` | has a backward branch (often a loop), 116 ins | has a backward branch (often a loop) |
| `0x4f4360` | 402 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x5f4bb0` | 402 | 9 | `shape only` | has a backward branch (often a loop), 109 ins | has a backward branch (often a loop) |
| `0x606170` | 402 | 2 | `shape only` | has a backward branch (often a loop), 116 ins | has a backward branch (often a loop) |
| `0x51c4b0` | 401 | 1 | `shape only` | has a backward branch (often a loop), 91 ins | has a backward branch (often a loop) |
| `0x531d10` | 401 | 2 | `shape only` | has a backward branch (often a loop), 127 ins | has a backward branch (often a loop) |
| `0x5ccd80` | 401 | 1 | `shape only` | has a backward branch (often a loop), 103 ins | has a backward branch (often a loop) |
| `0x6276b0` | 401 | 4 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x8c66d0` | 401 | 3 | `shape only` | has a backward branch (often a loop), 115 ins | has a backward branch (often a loop) |
| `0x8cf660` | 401 | 2 | `shape only` | has a backward branch (often a loop), 109 ins | has a backward branch (often a loop) |
| `0x8e0b90` | 401 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x8f8010` | 401 | 2 | `shape only` | has a backward branch (often a loop), 115 ins | has a backward branch (often a loop) |
| `0x8f8240` | 401 | 2 | `shape only` | has a backward branch (often a loop), 118 ins | has a backward branch (often a loop) |
| `0x8f83e0` | 401 | 3 | `shape only` | has a backward branch (often a loop), 115 ins | has a backward branch (often a loop) |
| `0x8f8a80` | 401 | 3 | `shape only` | has a backward branch (often a loop), 118 ins | has a backward branch (often a loop) |
| `0x1f8d90` | 399 | 3 | `strings` |  :  \|  =>  | has a backward branch (often a loop) |
| `0x724b20` | 399 | 3 | `shape only` | has a backward branch (often a loop), 108 ins | has a backward branch (often a loop) |
| `0x1aa890` | 398 | 3 | `shape only` | has a backward branch (often a loop), 112 ins | has a backward branch (often a loop) |
| `0x6d2b10` | 398 | 9 | `shape only` | has a backward branch (often a loop), 128 ins | has a backward branch (often a loop) |
| `0x3ff600` | 397 | 8 | `shape only` | has a backward branch (often a loop), 130 ins | has a backward branch (often a loop) |
| `0x8926a0` | 397 | 2 | `shape only` | has a backward branch (often a loop), 111 ins | has a backward branch (often a loop) |
| `0x13bb20` | 396 | 2 | `shape only` | has a backward branch (often a loop), 124 ins | has a backward branch (often a loop) |
| `0xf5020` | 394 | 10 | `shape only` | has a backward branch (often a loop), 115 ins | has a backward branch (often a loop) |
| `0x259280` | 394 | 5 | `shape only` | has a backward branch (often a loop), 106 ins | has a backward branch (often a loop) |
| `0x8e7510` | 394 | 2 | `shape only` | has a backward branch (often a loop), 110 ins | has a backward branch (often a loop) |
| `0x9527e0` | 394 | 2 | `shape only` | has a backward branch (often a loop), 127 ins | has a backward branch (often a loop) |
| `0xf3ab0` | 393 | 20 | `shape only` | has a backward branch (often a loop), 114 ins | has a backward branch (often a loop) |
| `0x3ed50` | 392 | 2 | `shape only` | has a backward branch (often a loop), 111 ins | has a backward branch (often a loop) |
| `0x3eee0` | 392 | 2 | `shape only` | has a backward branch (often a loop), 111 ins | has a backward branch (often a loop) |
| `0x5069a0` | 392 | 2 | `strings` | quality_zone_enable \| quality_zone_interactions | has a backward branch (often a loop) |
| `0x63a750` | 390 | 2 | `shape only` | has a backward branch (often a loop), 104 ins | has a backward branch (often a loop) |
| `0x9302c0` | 390 | 6 | `shape only` | has a backward branch (often a loop), 109 ins | has a backward branch (often a loop) |
| `0x60c5c0` | 389 | 6 | `strings` | failed to read from file | has a backward branch (often a loop) |
| `0x775a70` | 389 | 6 | `shape only` | straight line / call sequence, 62 ins | straight line / call sequence |
| `0x8fbaa0` | 389 | 1 | `shape only` | has a backward branch (often a loop), 122 ins | has a backward branch (often a loop) |
| `0x9368b0` | 388 | 2 | `shape only` | has a backward branch (often a loop), 130 ins | has a backward branch (often a loop) |
| `0x8c590` | 387 | 3 | `shape only` | has a backward branch (often a loop), 99 ins | has a backward branch (often a loop) |
| `0x5bea50` | 387 | 3 | `shape only` | has a backward branch (often a loop), 101 ins | has a backward branch (often a loop) |
| `0x8e0890` | 386 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x52fc0` | 385 | 6 | `shape only` | has a backward branch (often a loop), 114 ins | has a backward branch (often a loop) |
| `0x60b510` | 385 | 2 | `strings` |  ]\ | has a backward branch (often a loop) |
| `0x64c7b0` | 385 | 2 | `strings` | ->  | straight line / call sequence |
| `0x8c03e0` | 385 | 4 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x8cab00` | 385 | 3 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x8e0e70` | 385 | 3 | `shape only` | has a backward branch (often a loop), 108 ins | has a backward branch (often a loop) |
| `0x902880` | 385 | 3 | `shape only` | has a backward branch (often a loop), 108 ins | has a backward branch (often a loop) |
| `0x908890` | 385 | 2 | `shape only` | has a backward branch (often a loop), 108 ins | has a backward branch (often a loop) |
| `0x966c30` | 385 | 2 | `shape only` | has a backward branch (often a loop), 102 ins | has a backward branch (often a loop) |
| `0x13bce0` | 384 | 2 | `shape only` | has a backward branch (often a loop), 109 ins | has a backward branch (often a loop) |
| `0x142510` | 384 | 2 | `shape only` | has a backward branch (often a loop), 90 ins | has a backward branch (often a loop) |
| `0x724e40` | 384 | 2 | `shape only` | has a backward branch (often a loop), 101 ins | has a backward branch (often a loop) |
| `0x725140` | 384 | 3 | `shape only` | has a backward branch (often a loop), 103 ins | has a backward branch (often a loop) |
| `0x853e90` | 384 | 10 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x930c20` | 384 | 3 | `shape only` | has a backward branch (often a loop), 117 ins | has a backward branch (often a loop) |
| `0x1a61a0` | 382 | 2 | `shape only` | has a backward branch (often a loop), 98 ins | has a backward branch (often a loop) |
| `0x4f3de0` | 382 | 4 | `shape only` | has a backward branch (often a loop), 103 ins | has a backward branch (often a loop) |
| `0x1a8ee0` | 381 | 11 | `shape only` | has a backward branch (often a loop), 101 ins | has a backward branch (often a loop) |
| `0x64d420` | 381 | 1 | `strings` | ->  | straight line / call sequence |
| `0x8bec40` | 381 | 2 | `shape only` | has a backward branch (often a loop), 109 ins | has a backward branch (often a loop) |
| `0x172010` | 380 | 4 | `shape only` | has a backward branch (often a loop), 95 ins | has a backward branch (often a loop) |
| `0x62ff90` | 380 | 4 | `shape only` | has a backward branch (often a loop), 97 ins | has a backward branch (often a loop) |
| `0x64b040` | 380 | 6 | `strings` | ->  | has a backward branch (often a loop) |
| `0x6de430` | 379 | 24 | `shape only` | has a backward branch (often a loop), 102 ins | has a backward branch (often a loop) |
| `0x934600` | 378 | 4 | `shape only` | has a backward branch (often a loop), 110 ins | has a backward branch (often a loop) |
| `0x870500` | 377 | 2 | `shape only` | has a backward branch (often a loop), 118 ins | has a backward branch (often a loop) |
| `0x159300` | 376 | 3 | `shape only` | has a backward branch (often a loop), 109 ins | has a backward branch (often a loop) |
| `0x1aaa20` | 376 | 2 | `shape only` | has a backward branch (often a loop), 109 ins | has a backward branch (often a loop) |
| `0x1f3520` | 376 | 3 | `shape only` | has a backward branch (often a loop), 109 ins | has a backward branch (often a loop) |
| `0x5e86f0` | 376 | 3 | `shape only` | has a backward branch (often a loop), 109 ins | has a backward branch (often a loop) |
| `0x8d8a80` | 376 | 5 | `shape only` | has a backward branch (often a loop), 102 ins | has a backward branch (often a loop) |
| `0x94b9a0` | 376 | 2 | `shape only` | has a backward branch (often a loop), 97 ins | has a backward branch (often a loop) |
| `0x9552d0` | 375 | 2 | `shape only` | has a backward branch (often a loop), 106 ins | has a backward branch (often a loop) |
| `0x6de2b0` | 374 | 3 | `shape only` | has a backward branch (often a loop), 101 ins | has a backward branch (often a loop) |
| `0x1fbd80` | 373 | 2 | `shape only` | has a backward branch (often a loop), 101 ins | has a backward branch (often a loop) |
| `0x7c4720` | 373 | 1 | `shape only` | straight line / call sequence, 73 ins | straight line / call sequence |
| `0x93d430` | 373 | 2 | `shape only` | has a backward branch (often a loop), 120 ins | has a backward branch (often a loop) |
| `0x942dd0` | 373 | 3 | `shape only` | has a backward branch (often a loop), 120 ins | has a backward branch (often a loop) |
| `0x97f400` | 373 | 2 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x17e470` | 371 | 3 | `shape only` | has a backward branch (often a loop), 98 ins | has a backward branch (often a loop) |
| `0x4f5280` | 371 | 1 | `shape only` | has a backward branch (often a loop), 97 ins | has a backward branch (often a loop) |
| `0x4da3e0` | 370 | 2 | `shape only` | has a backward branch (often a loop), 101 ins | has a backward branch (often a loop) |
| `0x1f88f0` | 369 | 3 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x5da270` | 369 | 2 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x6f25e0` | 369 | 6 | `shape only` | has a backward branch (often a loop), 109 ins | has a backward branch (often a loop) |
| `0x8ae9b0` | 369 | 3 | `shape only` | has a backward branch (often a loop), 114 ins | has a backward branch (often a loop) |
| `0x5bee40` | 368 | 2 | `shape only` | has a backward branch (often a loop), 103 ins | has a backward branch (often a loop) |
| `0x5cc730` | 368 | 5 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0x8bad20` | 368 | 4 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x8ca320` | 368 | 2 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x8cac90` | 368 | 2 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x8cf4f0` | 368 | 4 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x8e0a20` | 368 | 2 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x8e1000` | 368 | 2 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x8e7f10` | 368 | 2 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x2582c0` | 367 | 2 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x5fc7f0` | 367 | 9 | `strings` | true \| false | has a backward branch (often a loop) |
| `0xd2370` | 366 | 5 | `shape only` | has a backward branch (often a loop), 95 ins | has a backward branch (often a loop) |
| `0x1aa000` | 366 | 5 | `shape only` | has a backward branch (often a loop), 85 ins | has a backward branch (often a loop) |
| `0x76e210` | 366 | 2 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0xb5ba0` | 364 | 2 | `shape only` | has a backward branch (often a loop), 102 ins | has a backward branch (often a loop) |
| `0x20dc50` | 364 | 5 | `shape only` | has a backward branch (often a loop), 85 ins | has a backward branch (often a loop) |
| `0x57dbc0` | 364 | 3 | `shape only` | has a backward branch (often a loop), 97 ins | has a backward branch (often a loop) |
| `0x6d6510` | 364 | 6 | `strings` | !m_elements.empty() \| ../utils/evaluated_object.hpp | has a backward branch (often a loop) |
| `0x60c430` | 363 | 2 | `strings` | bad stream cursor position specified \| failed to move stream cursor | has a backward branch (often a loop) |
| `0x8f4320` | 363 | 2 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x96ca10` | 362 | 2 | `shape only` | has a backward branch (often a loop), 94 ins | has a backward branch (often a loop) |
| `0x1549b0` | 361 | 5 | `shape only` | has a backward branch (often a loop), 112 ins | has a backward branch (often a loop) |
| `0x529c40` | 360 | 3 | `shape only` | has a backward branch (often a loop), 104 ins | has a backward branch (often a loop) |
| `0x7460b0` | 360 | 2 | `shape only` | has a backward branch (often a loop), 97 ins | has a backward branch (often a loop) |
| `0x95a7f0` | 360 | 2 | `shape only` | has a backward branch (often a loop), 103 ins | has a backward branch (often a loop) |
| `0x934c40` | 359 | 5 | `shape only` | has a backward branch (often a loop), 104 ins | has a backward branch (often a loop) |
| `0x8cf220` | 358 | 2 | `shape only` | has a backward branch (often a loop), 106 ins | has a backward branch (often a loop) |
| `0x5c90a0` | 357 | 6 | `shape only` | has a backward branch (often a loop), 85 ins | has a backward branch (often a loop) |
| `0x17fc20` | 356 | 2 | `shape only` | has a backward branch (often a loop), 103 ins | has a backward branch (often a loop) |
| `0x1ee910` | 356 | 4 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0x60c160` | 356 | 2 | `strings` | failed to open file \| failed to get file size | has a backward branch (often a loop) |
| `0x87b530` | 356 | 2 | `shape only` | has a backward branch (often a loop), 102 ins | has a backward branch (often a loop) |
| `0x220230` | 355 | 2 | `shape only` | has a backward branch (often a loop), 94 ins | has a backward branch (often a loop) |
| `0x65000` | 354 | 4 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x12ba20` | 354 | 2 | `strings` | sntl_admin_context_new \| sntl_admin_get | has a backward branch (often a loop) |
| `0x1aa2f0` | 354 | 2 | `strings` | #################### Map Stats ######### \|  Nestables  | has a backward branch (often a loop) |
| `0x1aa460` | 354 | 3 | `strings` | #################### Map Stats ######### \|  Nestables  | has a backward branch (often a loop) |
| `0x4b9b80` | 354 | 3 | `shape only` | has a backward branch (often a loop), 110 ins | has a backward branch (often a loop) |
| `0x5eb090` | 354 | 2 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x69bd10` | 354 | 2 | `shape only` | has a backward branch (often a loop), 106 ins | has a backward branch (often a loop) |
| `0x8894b0` | 354 | 2 | `shape only` | has a backward branch (often a loop), 90 ins | has a backward branch (often a loop) |
| `0x902f60` | 354 | 2 | `shape only` | has a backward branch (often a loop), 95 ins | has a backward branch (often a loop) |
| `0x906670` | 354 | 2 | `shape only` | has a backward branch (often a loop), 109 ins | has a backward branch (often a loop) |
| `0x9067e0` | 354 | 2 | `shape only` | has a backward branch (often a loop), 108 ins | has a backward branch (often a loop) |
| `0x27b870` | 353 | 3 | `shape only` | straight line / call sequence, 79 ins | straight line / call sequence |
| `0x671210` | 353 | 10 | `shape only` | has a backward branch (often a loop), 113 ins | has a backward branch (often a loop) |
| `0x8ca490` | 353 | 2 | `shape only` | has a backward branch (often a loop), 104 ins | has a backward branch (often a loop) |
| `0x17b740` | 352 | 1 | `shape only` | has a backward branch (often a loop), 109 ins | has a backward branch (often a loop) |
| `0x96b9a0` | 352 | 3 | `shape only` | has a backward branch (often a loop), 92 ins | has a backward branch (often a loop) |
| `0x1a8620` | 351 | 3 | `strings` |  =  | has a backward branch (often a loop) |
| `0x62cbf0` | 351 | 3 | `shape only` | has a backward branch (often a loop), 78 ins | has a backward branch (often a loop) |
| `0x7179a0` | 351 | 4 | `shape only` | has a backward branch (often a loop), 104 ins | has a backward branch (often a loop) |
| `0x87edf0` | 351 | 35 | `callers` | called by 0x2ab0 LaunchLocalComputation; 0x6100 LaunchComputation | straight line / call sequence |
| `0x98d800` | 351 | 8 | `shape only` | has a backward branch (often a loop), 99 ins | has a backward branch (often a loop) |
| `0x1a07e0` | 350 | 2 | `shape only` | has a backward branch (often a loop), 78 ins | has a backward branch (often a loop) |
| `0x4fb790` | 350 | 4 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x573740` | 350 | 2 | `shape only` | has a backward branch (often a loop), 97 ins | has a backward branch (often a loop) |
| `0x64f850` | 350 | 2 | `strings` | ->  | has a backward branch (often a loop) |
| `0x677af0` | 350 | 1 | `shape only` | has a backward branch (often a loop), 106 ins | has a backward branch (often a loop) |
| `0x951240` | 350 | 2 | `shape only` | has a backward branch (often a loop), 107 ins | has a backward branch (often a loop) |
| `0x14ec20` | 349 | 2 | `shape only` | has a backward branch (often a loop), 94 ins | has a backward branch (often a loop) |
| `0x586300` | 349 | 6 | `shape only` | has a backward branch (often a loop), 107 ins | has a backward branch (often a loop) |
| `0x586460` | 349 | 12 | `shape only` | has a backward branch (often a loop), 107 ins | has a backward branch (often a loop) |
| `0x5ea310` | 349 | 2 | `shape only` | has a backward branch (often a loop), 94 ins | has a backward branch (often a loop) |
| `0x50250` | 347 | 2 | `shape only` | has a backward branch (often a loop), 107 ins | has a backward branch (often a loop) |
| `0x16f1f0` | 347 | 1 | `shape only` | has a backward branch (often a loop), 98 ins | has a backward branch (often a loop) |
| `0x6f2e30` | 347 | 5 | `shape only` | has a backward branch (often a loop), 114 ins | has a backward branch (often a loop) |
| `0x10f8c0` | 346 | 20 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x4c1f30` | 346 | 6 | `shape only` | has a backward branch (often a loop), 97 ins | has a backward branch (often a loop) |
| `0x4bac30` | 345 | 1 | `shape only` | has a backward branch (often a loop), 94 ins | has a backward branch (often a loop) |
| `0x5c3060` | 344 | 2 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x5cf320` | 344 | 1 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0x60b7a0` | 344 | 2 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x98ef50` | 344 | 2 | `shape only` | has a backward branch (often a loop), 106 ins | has a backward branch (often a loop) |
| `0x1fd6c0` | 343 | 7 | `shape only` | straight line / call sequence, 45 ins | straight line / call sequence |
| `0x262740` | 343 | 3 | `shape only` | has a backward branch (often a loop), 94 ins | has a backward branch (often a loop) |
| `0x773c90` | 343 | 2 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x900820` | 342 | 4 | `shape only` | has a backward branch (often a loop), 101 ins | has a backward branch (often a loop) |
| `0x900980` | 342 | 2 | `shape only` | has a backward branch (often a loop), 101 ins | has a backward branch (often a loop) |
| `0x6eb020` | 341 | 3 | `shape only` | has a backward branch (often a loop), 92 ins | has a backward branch (often a loop) |
| `0x90e520` | 341 | 13 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x90e8d0` | 341 | 13 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x545cf0` | 340 | 7 | `strings` | @w\| | has a backward branch (often a loop) |
| `0x5d7b90` | 340 | 3 | `shape only` | has a backward branch (often a loop), 75 ins | has a backward branch (often a loop) |
| `0x64cc30` | 340 | 1 | `strings` | ->  | straight line / call sequence |
| `0x601dc0` | 339 | 7 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x8e6dd0` | 339 | 2 | `shape only` | has a backward branch (often a loop), 103 ins | has a backward branch (often a loop) |
| `0x170760` | 338 | 3 | `shape only` | has a backward branch (often a loop), 110 ins | has a backward branch (often a loop) |
| `0x19fd30` | 338 | 2 | `shape only` | has a backward branch (often a loop), 110 ins | has a backward branch (often a loop) |
| `0x619630` | 338 | 4 | `shape only` | has a backward branch (often a loop), 98 ins | has a backward branch (often a loop) |
| `0x8f3e40` | 338 | 4 | `shape only` | has a backward branch (often a loop), 104 ins | has a backward branch (often a loop) |
| `0x8f7b80` | 338 | 2 | `shape only` | has a backward branch (often a loop), 98 ins | has a backward branch (often a loop) |
| `0x90cc70` | 338 | 14 | `shape only` | has a backward branch (often a loop), 104 ins | has a backward branch (often a loop) |
| `0x90dcc0` | 338 | 3 | `shape only` | has a backward branch (often a loop), 104 ins | has a backward branch (often a loop) |
| `0x933f20` | 338 | 2 | `shape only` | has a backward branch (often a loop), 102 ins | has a backward branch (often a loop) |
| `0x86f810` | 337 | 14 | `shape only` | has a backward branch (often a loop), 68 ins | has a backward branch (often a loop) |
| `0x86fbc0` | 337 | 14 | `shape only` | has a backward branch (often a loop), 68 ins | has a backward branch (often a loop) |
| `0x8ab5d0` | 337 | 29 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x8c0c30` | 337 | 4 | `shape only` | has a backward branch (often a loop), 98 ins | has a backward branch (often a loop) |
| `0x8c0d90` | 337 | 8 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x8c3bd0` | 337 | 7 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x8cf390` | 337 | 2 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x8d3880` | 337 | 2 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x8f7a20` | 337 | 5 | `shape only` | has a backward branch (often a loop), 102 ins | has a backward branch (often a loop) |
| `0x97e6f0` | 337 | 2 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x8be2f0` | 335 | 8 | `shape only` | has a backward branch (often a loop), 108 ins | has a backward branch (often a loop) |
| `0x8bf100` | 335 | 2 | `shape only` | has a backward branch (often a loop), 108 ins | has a backward branch (often a loop) |
| `0x8c37f0` | 335 | 17 | `shape only` | has a backward branch (often a loop), 108 ins | has a backward branch (often a loop) |
| `0x8c8ca0` | 335 | 6 | `shape only` | has a backward branch (often a loop), 108 ins | has a backward branch (often a loop) |
| `0x24c40` | 334 | 2 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x69a8f0` | 334 | 2 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x91f6f0` | 334 | 17 | `shape only` | has a backward branch (often a loop), 73 ins | has a backward branch (often a loop) |
| `0x6d6270` | 333 | 3 | `strings` | !m_elements.empty() \| ../utils/evaluated_object.hpp | has a backward branch (often a loop) |
| `0x6d63c0` | 333 | 3 | `strings` | !m_elements.empty() \| ../utils/evaluated_object.hpp | has a backward branch (often a loop) |
| `0x6d6a00` | 333 | 2 | `strings` | !m_elements.empty() \| ../utils/evaluated_object.hpp | has a backward branch (often a loop) |
| `0x6d6b50` | 333 | 2 | `strings` | !m_elements.empty() \| ../utils/evaluated_object.hpp | has a backward branch (often a loop) |
| `0x6d6f60` | 333 | 2 | `strings` | !m_elements.empty() \| ../utils/evaluated_object.hpp | has a backward branch (often a loop) |
| `0x6d70b0` | 333 | 2 | `strings` | !m_elements.empty() \| ../utils/evaluated_object.hpp | has a backward branch (often a loop) |
| `0x873ab0` | 333 | 3 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x4fcf90` | 332 | 2 | `strings` | ..\structure\problem.cpp \| m_implementation->common_cut_computer.ge | has a backward branch (often a loop) |
| `0x5ca550` | 332 | 5 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x164190` | 331 | 4 | `shape only` | has a backward branch (often a loop), 92 ins | has a backward branch (often a loop) |
| `0x4da8e0` | 331 | 6 | `shape only` | has a backward branch (often a loop), 90 ins | has a backward branch (often a loop) |
| `0x88b840` | 331 | 10 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x1c8ec0` | 330 | 2 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x88b6f0` | 330 | 7 | `callers` | called by 0x104d0 WaitComputationTermination; 0x10650 WaitNextSolution | has a backward branch (often a loop) |
| `0x8c20a0` | 330 | 2 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x8e8690` | 330 | 3 | `shape only` | has a backward branch (often a loop), 92 ins | has a backward branch (often a loop) |
| `0x51e060` | 329 | 3 | `shape only` | has a backward branch (often a loop), 74 ins | has a backward branch (often a loop) |
| `0x13a580` | 328 | 2 | `shape only` | has a backward branch (often a loop), 95 ins | has a backward branch (often a loop) |
| `0x13a6d0` | 328 | 2 | `shape only` | has a backward branch (often a loop), 95 ins | has a backward branch (often a loop) |
| `0x161b80` | 328 | 2 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0x1fb5f0` | 328 | 4 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x8b7f20` | 328 | 4 | `shape only` | has a backward branch (often a loop), 102 ins | has a backward branch (often a loop) |
| `0x522250` | 327 | 3 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x96b260` | 327 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x7bb9a0` | 326 | 8 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x71b540` | 325 | 2 | `shape only` | has a backward branch (often a loop), 79 ins | has a backward branch (often a loop) |
| `0x8f9c70` | 325 | 2 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x92daa0` | 325 | 2 | `shape only` | has a backward branch (often a loop), 93 ins | has a backward branch (often a loop) |
| `0x986150` | 325 | 3 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x523d0` | 324 | 2 | `shape only` | has a backward branch (often a loop), 91 ins | has a backward branch (often a loop) |
| `0x14b320` | 324 | 2 | `shape only` | has a backward branch (often a loop), 99 ins | has a backward branch (often a loop) |
| `0x1c3f30` | 324 | 4 | `shape only` | has a backward branch (often a loop), 103 ins | has a backward branch (often a loop) |
| `0x64cfa0` | 324 | 1 | `strings` | ->  | straight line / call sequence |
| `0x81350` | 323 | 2 | `shape only` | has a backward branch (often a loop), 103 ins | has a backward branch (often a loop) |
| `0x220730` | 323 | 3 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x1c110` | 322 | 9 | `shape only` | has a backward branch (often a loop), 90 ins | has a backward branch (often a loop) |
| `0x131ef0` | 322 | 6 | `shape only` | has a backward branch (often a loop), 93 ins | has a backward branch (often a loop) |
| `0x8f9dc0` | 322 | 2 | `shape only` | has a backward branch (often a loop), 97 ins | has a backward branch (often a loop) |
| `0x9069b0` | 322 | 5 | `shape only` | has a backward branch (often a loop), 98 ins | has a backward branch (often a loop) |
| `0x92a580` | 322 | 2 | `shape only` | has a backward branch (often a loop), 98 ins | has a backward branch (often a loop) |
| `0xf3460` | 321 | 163 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x7bb850` | 321 | 8 | `shape only` | straight line / call sequence, 63 ins | straight line / call sequence |
| `0x8b4260` | 321 | 2 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x8f5840` | 321 | 2 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x94c410` | 321 | 4 | `shape only` | has a backward branch (often a loop), 93 ins | has a backward branch (often a loop) |
| `0x141e50` | 319 | 2 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x62d640` | 319 | 4 | `strings` | UWVSH | has a backward branch (often a loop) |
| `0x88f5c0` | 319 | 2 | `shape only` | has a backward branch (often a loop), 97 ins | has a backward branch (often a loop) |
| `0x94b550` | 319 | 2 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0xf4ee0` | 318 | 1 | `shape only` | straight line / call sequence, 98 ins | straight line / call sequence |
| `0x5d74f0` | 318 | 4 | `strings` | SEQEND | has a backward branch (often a loop) |
| `0x611fa0` | 318 | 6 | `strings` | VSH \| boost::filesystem::status | straight line / call sequence |
| `0x6242f0` | 318 | 5 | `strings` | _GLOBAL_ \| (anonymous namespace) | has a backward branch (often a loop) |
| `0x6533b0` | 318 | 4 | `shape only` | has a backward branch (often a loop), 94 ins | has a backward branch (often a loop) |
| `0x746830` | 318 | 3 | `shape only` | has a backward branch (often a loop), 98 ins | has a backward branch (often a loop) |
| `0x967d00` | 318 | 2 | `shape only` | has a backward branch (often a loop), 102 ins | has a backward branch (often a loop) |
| `0x46190` | 317 | 2 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x547ad0` | 317 | 3 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x6efb10` | 317 | 4 | `strings` | 0'6 | has a backward branch (often a loop) |
| `0x97e000` | 317 | 2 | `shape only` | has a backward branch (often a loop), 90 ins | has a backward branch (often a loop) |
| `0x65c0f0` | 316 | 2 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0x8268e0` | 316 | 1 | `strings` | space \| print | has a backward branch (often a loop) |
| `0x8f2780` | 316 | 13 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x9862a0` | 316 | 4 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x51bd80` | 315 | 3 | `shape only` | has a backward branch (often a loop), 74 ins | has a backward branch (often a loop) |
| `0x5bed00` | 315 | 4 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0x5e0960` | 315 | 10 | `shape only` | has a backward branch (often a loop), 85 ins | has a backward branch (often a loop) |
| `0x60b910` | 315 | 6 | `strings` | dbghelp.dll \| SymInitialize | straight line / call sequence |
| `0x73ad80` | 313 | 2 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x73c850` | 313 | 2 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x8afc70` | 313 | 4 | `shape only` | has a backward branch (often a loop), 106 ins | has a backward branch (often a loop) |
| `0x8e8b30` | 313 | 3 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x8e8c70` | 313 | 2 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x925cf0` | 313 | 5 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0x92be50` | 313 | 2 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x92f170` | 313 | 2 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x92f8e0` | 313 | 2 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x2b9290` | 312 | 17 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x371e90` | 312 | 7 | `shape only` | straight line / call sequence, 46 ins | straight line / call sequence |
| `0x549e60` | 312 | 2 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x873c00` | 312 | 4 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x8c2760` | 312 | 2 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0x98df60` | 311 | 10 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x98e1b0` | 311 | 2 | `shape only` | has a backward branch (often a loop), 105 ins | has a backward branch (often a loop) |
| `0x531bd0` | 310 | 6 | `shape only` | has a backward branch (often a loop), 92 ins | has a backward branch (often a loop) |
| `0x9688d0` | 310 | 4 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x1c5830` | 309 | 2 | `shape only` | has a backward branch (often a loop), 92 ins | has a backward branch (often a loop) |
| `0x6b80e0` | 309 | 2 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x900c00` | 309 | 3 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x4d9b90` | 308 | 2 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x8fc0e0` | 308 | 2 | `shape only` | has a backward branch (often a loop), 94 ins | has a backward branch (often a loop) |
| `0x8fc570` | 308 | 2 | `shape only` | has a backward branch (often a loop), 94 ins | has a backward branch (often a loop) |
| `0x941ce0` | 308 | 2 | `shape only` | has a backward branch (often a loop), 91 ins | has a backward branch (often a loop) |
| `0x5d24f0` | 307 | 1 | `shape only` | has a backward branch (often a loop), 90 ins | has a backward branch (often a loop) |
| `0x60c2f0` | 307 | 2 | `strings` | bad stream cursor position specified \| failed to move stream cursor | has a backward branch (often a loop) |
| `0x65c5c0` | 307 | 3 | `shape only` | has a backward branch (often a loop), 79 ins | has a backward branch (often a loop) |
| `0x6790b0` | 307 | 1 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x8ff2a0` | 307 | 2 | `shape only` | has a backward branch (often a loop), 91 ins | has a backward branch (often a loop) |
| `0x8ff3e0` | 307 | 2 | `shape only` | has a backward branch (often a loop), 91 ins | has a backward branch (often a loop) |
| `0x1fc320` | 306 | 16 | `shape only` | has a backward branch (often a loop), 79 ins | has a backward branch (often a loop) |
| `0x5d87b0` | 306 | 6 | `shape only` | has a backward branch (often a loop), 85 ins | has a backward branch (often a loop) |
| `0x5e3760` | 306 | 3 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x658250` | 306 | 2 | `shape only` | has a backward branch (often a loop), 99 ins | has a backward branch (often a loop) |
| `0x6e9050` | 305 | 2 | `shape only` | has a backward branch (often a loop), 68 ins | has a backward branch (often a loop) |
| `0x8aa690` | 305 | 5 | `shape only` | has a backward branch (often a loop), 93 ins | has a backward branch (often a loop) |
| `0x8be640` | 305 | 8 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x8bfd30` | 305 | 8 | `shape only` | has a backward branch (often a loop), 93 ins | has a backward branch (often a loop) |
| `0x8bfe70` | 305 | 3 | `shape only` | has a backward branch (often a loop), 93 ins | has a backward branch (often a loop) |
| `0x8bffb0` | 305 | 2 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x8c00f0` | 305 | 2 | `shape only` | has a backward branch (often a loop), 94 ins | has a backward branch (often a loop) |
| `0x8c6e80` | 305 | 3 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x8d2e60` | 305 | 2 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x8e0d30` | 305 | 3 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x8ea5e0` | 305 | 2 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x8f0de0` | 305 | 3 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x9057a0` | 305 | 2 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x9058e0` | 305 | 2 | `shape only` | has a backward branch (often a loop), 91 ins | has a backward branch (often a loop) |
| `0x905a20` | 305 | 2 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x4daad0` | 304 | 6 | `shape only` | has a backward branch (often a loop), 97 ins | has a backward branch (often a loop) |
| `0x5c85b0` | 304 | 6 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x65dbf0` | 304 | 2 | `shape only` | has a backward branch (often a loop), 106 ins | has a backward branch (often a loop) |
| `0x70d4e0` | 304 | 4 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x111630` | 303 | 19 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x4f3cb0` | 303 | 2 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x8ceac0` | 303 | 2 | `shape only` | has a backward branch (often a loop), 92 ins | has a backward branch (often a loop) |
| `0x618610` | 302 | 5 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x716a10` | 301 | 5 | `shape only` | has a backward branch (often a loop), 91 ins | has a backward branch (often a loop) |
| `0x897400` | 301 | 2 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x90de20` | 301 | 13 | `shape only` | has a backward branch (often a loop), 63 ins | has a backward branch (often a loop) |
| `0x90e1a0` | 301 | 13 | `shape only` | has a backward branch (often a loop), 63 ins | has a backward branch (often a loop) |
| `0x90f770` | 301 | 12 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x97e850` | 301 | 1 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x55a0f0` | 300 | 6 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x8c21f0` | 300 | 5 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x97e2f0` | 300 | 2 | `shape only` | has a backward branch (often a loop), 85 ins | has a backward branch (often a loop) |
| `0x2c72f0` | 299 | 11 | `shape only` | has a backward branch (often a loop), 94 ins | has a backward branch (often a loop) |
| `0x55fb40` | 299 | 6 | `shape only` | has a backward branch (often a loop), 95 ins | has a backward branch (often a loop) |
| `0x910c20` | 299 | 44 | `shape only` | has a backward branch (often a loop), 92 ins | has a backward branch (often a loop) |
| `0x913710` | 299 | 17 | `shape only` | has a backward branch (often a loop), 92 ins | has a backward branch (often a loop) |
| `0x922020` | 299 | 13 | `shape only` | has a backward branch (often a loop), 61 ins | has a backward branch (often a loop) |
| `0x86f110` | 297 | 14 | `shape only` | has a backward branch (often a loop), 62 ins | has a backward branch (often a loop) |
| `0x86f490` | 297 | 14 | `shape only` | has a backward branch (often a loop), 62 ins | has a backward branch (often a loop) |
| `0x951110` | 297 | 2 | `shape only` | has a backward branch (often a loop), 95 ins | has a backward branch (often a loop) |
| `0x5c9330` | 296 | 7 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x623ec0` | 296 | 3 | `shape only` | has a backward branch (often a loop), 104 ins | has a backward branch (often a loop) |
| `0x63a570` | 296 | 3 | `strings` | PRINTF_EXPONENT_DIGITS | has a backward branch (often a loop) |
| `0x935590` | 296 | 2 | `shape only` | has a backward branch (often a loop), 99 ins | has a backward branch (often a loop) |
| `0x6199c0` | 295 | 7 | `shape only` | has a backward branch (often a loop), 65 ins | has a backward branch (often a loop) |
| `0x70c810` | 295 | 14 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0x871440` | 295 | 2 | `shape only` | has a backward branch (often a loop), 74 ins | has a backward branch (often a loop) |
| `0x944d40` | 295 | 14 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x98c260` | 295 | 4 | `shape only` | straight line / call sequence, 85 ins | straight line / call sequence |
| `0x13a450` | 294 | 2 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x225330` | 294 | 3 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x2303a0` | 294 | 1 | `shape only` | straight line / call sequence, 75 ins | straight line / call sequence |
| `0x520840` | 294 | 5 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x570610` | 294 | 2 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x604170` | 294 | 2 | `shape only` | has a backward branch (often a loop), 97 ins | has a backward branch (often a loop) |
| `0x1f33f0` | 293 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x8740f0` | 293 | 16 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x8fbc30` | 293 | 3 | `shape only` | has a backward branch (often a loop), 90 ins | has a backward branch (often a loop) |
| `0x8fc220` | 293 | 4 | `shape only` | has a backward branch (often a loop), 90 ins | has a backward branch (often a loop) |
| `0x8fc3e0` | 293 | 6 | `shape only` | has a backward branch (often a loop), 90 ins | has a backward branch (often a loop) |
| `0x897650` | 292 | 1 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x8f90f0` | 292 | 2 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0x8fde10` | 292 | 2 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0x8fe290` | 292 | 5 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0x96d7f0` | 292 | 2 | `shape only` | has a backward branch (often a loop), 92 ins | has a backward branch (often a loop) |
| `0x86c000` | 291 | 2 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x86c250` | 291 | 2 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x86e810` | 291 | 2 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x86eae0` | 291 | 2 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x86edf0` | 291 | 2 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x873f70` | 291 | 2 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x874270` | 291 | 1 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x8c5e70` | 291 | 4 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x8cebf0` | 291 | 3 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x1a8af0` | 290 | 2 | `strings` | ..\nesting\algos\algo_parameters.cpp \| parameters.m_offset_manager | has a backward branch (often a loop) |
| `0x657fb0` | 290 | 4 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x66e830` | 290 | 4 | `shape only` | has a backward branch (often a loop), 63 ins | has a backward branch (often a loop) |
| `0x8a2750` | 290 | 2 | `shape only` | has a backward branch (often a loop), 71 ins | has a backward branch (often a loop) |
| `0x8fdce0` | 290 | 2 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0x8fe160` | 290 | 5 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0x1c1e00` | 289 | 3 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x6ca390` | 289 | 5 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x738280` | 289 | 5 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x909d10` | 289 | 4 | `shape only` | has a backward branch (often a loop), 85 ins | has a backward branch (often a loop) |
| `0x59b290` | 288 | 2 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x6d2980` | 288 | 3 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x922ff0` | 288 | 2 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x923360` | 288 | 2 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x9236d0` | 288 | 2 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x9313d0` | 288 | 2 | `shape only` | has a backward branch (often a loop), 98 ins | has a backward branch (often a loop) |
| `0x932a60` | 288 | 2 | `shape only` | has a backward branch (often a loop), 98 ins | has a backward branch (often a loop) |
| `0x93e1a0` | 288 | 3 | `shape only` | has a backward branch (often a loop), 100 ins | has a backward branch (often a loop) |
| `0x161a60` | 287 | 3 | `shape only` | has a backward branch (often a loop), 79 ins | has a backward branch (often a loop) |
| `0x5e8570` | 287 | 2 | `shape only` | straight line / call sequence, 52 ins | straight line / call sequence |
| `0x674360` | 287 | 3 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x9040d0` | 287 | 2 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x6ca4c0` | 285 | 2 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x98c770` | 285 | 2 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x65e310` | 284 | 2 | `strings` | ..\nesting\algos\../nesting.hpp \| m_left >= s_min && m_right <= s_max | has a backward branch (often a loop) |
| `0x74b430` | 284 | 3 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x74b700` | 284 | 26 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x92ce40` | 284 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x92cf60` | 284 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x92d080` | 284 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x92d1a0` | 284 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x92d2c0` | 284 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x92d3e0` | 284 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x92d500` | 284 | 3 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x92d620` | 284 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x92d740` | 284 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x92d860` | 284 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x92d980` | 284 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x183e20` | 283 | 13 | `shape only` | has a backward branch (often a loop), 79 ins | has a backward branch (often a loop) |
| `0x258680` | 283 | 2 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x545480` | 283 | 2 | `shape only` | has a backward branch (often a loop), 76 ins | has a backward branch (often a loop) |
| `0x5fb230` | 283 | 8 | `strings` | VSH \| VSH | has a backward branch (often a loop) |
| `0x8929e0` | 283 | 4 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x643b0` | 282 | 2 | `shape only` | straight line / call sequence, 83 ins | straight line / call sequence |
| `0x6257d0` | 282 | 5 | `shape only` | has a backward branch (often a loop), 91 ins | has a backward branch (often a loop) |
| `0x94b430` | 282 | 2 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x97eba0` | 282 | 1 | `shape only` | has a backward branch (often a loop), 93 ins | has a backward branch (often a loop) |
| `0x180500` | 281 | 9 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x65a7a0` | 281 | 3 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x8bc3e0` | 281 | 4 | `shape only` | has a backward branch (often a loop), 96 ins | has a backward branch (often a loop) |
| `0x9320a0` | 281 | 7 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x9377b0` | 281 | 3 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x93dbf0` | 281 | 6 | `shape only` | has a backward branch (often a loop), 90 ins | has a backward branch (often a loop) |
| `0x13f980` | 280 | 2 | `shape only` | has a backward branch (often a loop), 70 ins | has a backward branch (often a loop) |
| `0x4f3490` | 280 | 6 | `shape only` | straight line / call sequence, 61 ins | straight line / call sequence |
| `0x5bebe0` | 280 | 3 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x865960` | 280 | 4 | `shape only` | has a backward branch (often a loop), 75 ins | has a backward branch (often a loop) |
| `0x8d0720` | 280 | 2 | `shape only` | has a backward branch (often a loop), 95 ins | has a backward branch (often a loop) |
| `0x902100` | 280 | 2 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x97a40` | 279 | 3 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x2caee0` | 279 | 5 | `shape only` | straight line / call sequence, 34 ins | straight line / call sequence |
| `0x6ca720` | 279 | 2 | `strings` | 10BeamValues | has a backward branch (often a loop) |
| `0x6ca840` | 279 | 2 | `strings` | 10Off2Weight | has a backward branch (often a loop) |
| `0x6ca960` | 279 | 2 | `strings` | 10PartRatios | has a backward branch (often a loop) |
| `0x6caa80` | 279 | 2 | `strings` | 11RepeatSheet | has a backward branch (often a loop) |
| `0x6caba0` | 279 | 2 | `strings` | 11TilingLimit | has a backward branch (often a loop) |
| `0x6cacc0` | 279 | 2 | `strings` | 13ODescriptions | has a backward branch (often a loop) |
| `0x6cade0` | 279 | 2 | `strings` | 13PosDirections | has a backward branch (often a loop) |
| `0x6caf00` | 279 | 2 | `strings` | 14ODescriptions2 | has a backward branch (often a loop) |
| `0x6cb020` | 279 | 2 | `strings` | 6UseMap | has a backward branch (often a loop) |
| `0x6cb140` | 279 | 2 | `strings` | 7OPricer | has a backward branch (often a loop) |
| `0x6cb260` | 279 | 2 | `strings` | 7ZfSizes | has a backward branch (often a loop) |
| `0x6cb380` | 279 | 2 | `strings` | 8DegSteps | has a backward branch (often a loop) |
| `0x7d7c00` | 279 | 4 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x86e9c0` | 279 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x86ecd0` | 279 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x900ae0` | 279 | 10 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x1b910` | 278 | 3 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x82390` | 278 | 2 | `shape only` | has a backward branch (often a loop), 93 ins | has a backward branch (often a loop) |
| `0x97dc80` | 278 | 2 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x4ef910` | 277 | 1 | `shape only` | straight line / call sequence, 63 ins | straight line / call sequence |
| `0x962c60` | 277 | 2 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x1c9170` | 276 | 3 | `shape only` | has a backward branch (often a loop), 73 ins | has a backward branch (often a loop) |
| `0x523630` | 276 | 14 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x653550` | 276 | 4 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x13b760` | 275 | 2 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x528bf0` | 275 | 6 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0x768a60` | 275 | 2 | `shape only` | has a backward branch (often a loop), 78 ins | has a backward branch (often a loop) |
| `0x7b7080` | 275 | 4 | `shape only` | has a backward branch (often a loop), 92 ins | has a backward branch (often a loop) |
| `0x61b650` | 274 | 6 | `shape only` | straight line / call sequence, 66 ins | straight line / call sequence |
| `0x5fc960` | 273 | 15 | `strings` | integer out of signed integer range \| Real out of signed integer range | has a backward branch (often a loop) |
| `0x8be1d0` | 273 | 2 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x8c33b0` | 273 | 2 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x8c35d0` | 273 | 2 | `shape only` | has a backward branch (often a loop), 85 ins | has a backward branch (often a loop) |
| `0x8cf100` | 273 | 3 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x8d6460` | 273 | 4 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x905e10` | 273 | 5 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x9071b0` | 273 | 2 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x9072d0` | 273 | 2 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x9074f0` | 273 | 2 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x908a20` | 273 | 2 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x926880` | 273 | 2 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0xb5930` | 272 | 1 | `shape only` | straight line / call sequence, 76 ins | straight line / call sequence |
| `0x4dd870` | 272 | 4 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x545370` | 272 | 3 | `shape only` | has a backward branch (often a loop), 72 ins | has a backward branch (often a loop) |
| `0x72dac0` | 272 | 12 | `shape only` | has a backward branch (often a loop), 61 ins | has a backward branch (often a loop) |
| `0x77a460` | 272 | 7 | `strings` | InputBuffer | has a backward branch (often a loop) |
| `0x9325c0` | 272 | 2 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x93c930` | 272 | 3 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x943090` | 271 | 1 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x50fd40` | 270 | 4 | `shape only` | has a backward branch (often a loop), 73 ins | has a backward branch (often a loop) |
| `0x8b7490` | 270 | 2 | `shape only` | has a backward branch (often a loop), 78 ins | has a backward branch (often a loop) |
| `0x1dd950` | 269 | 1 | `shape only` | straight line / call sequence, 65 ins | straight line / call sequence |
| `0x5cea80` | 269 | 9 | `callers` | called by 0x8ac0 GetNoFitMap | straight line / call sequence |
| `0x921cc0` | 269 | 13 | `strings` | true \| false | has a backward branch (often a loop) |
| `0x962e00` | 269 | 2 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x1b690` | 268 | 4 | `shape only` | has a backward branch (often a loop), 72 ins | has a backward branch (often a loop) |
| `0x15ec30` | 268 | 3 | `shape only` | has a backward branch (often a loop), 72 ins | has a backward branch (often a loop) |
| `0x520660` | 268 | 3 | `shape only` | has a backward branch (often a loop), 93 ins | has a backward branch (often a loop) |
| `0x196b20` | 267 | 2 | `shape only` | has a backward branch (often a loop), 73 ins | has a backward branch (often a loop) |
| `0x5befb0` | 267 | 2 | `shape only` | has a backward branch (often a loop), 73 ins | has a backward branch (often a loop) |
| `0x65dae0` | 267 | 2 | `shape only` | has a backward branch (often a loop), 85 ins | has a backward branch (often a loop) |
| `0x97e980` | 267 | 2 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x97ea90` | 267 | 1 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x9990e0` | 267 | 170 | `shape only` | has a backward branch (often a loop), 78 ins | has a backward branch (often a loop) |
| `0x1a3560` | 266 | 1 | `shape only` | has a backward branch (often a loop), 66 ins | has a backward branch (often a loop) |
| `0x54d650` | 266 | 2 | `shape only` | has a backward branch (often a loop), 98 ins | has a backward branch (often a loop) |
| `0x618740` | 266 | 3 | `shape only` | has a backward branch (often a loop), 79 ins | has a backward branch (often a loop) |
| `0x98d960` | 266 | 2 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x98e470` | 266 | 2 | `shape only` | has a backward branch (often a loop), 98 ins | has a backward branch (often a loop) |
| `0x98f0b0` | 266 | 2 | `shape only` | has a backward branch (often a loop), 98 ins | has a backward branch (often a loop) |
| `0x64bda0` | 265 | 1 | `strings` | ->  | straight line / call sequence |
| `0x64c940` | 265 | 11 | `strings` | ->  | straight line / call sequence |
| `0x64d310` | 265 | 6 | `strings` | ->  | straight line / call sequence |
| `0x9449e0` | 265 | 14 | `strings` | true \| false | has a backward branch (often a loop) |
| `0x9680b0` | 265 | 3 | `shape only` | has a backward branch (often a loop), 85 ins | has a backward branch (often a loop) |
| `0x5d1b40` | 264 | 1 | `shape only` | has a backward branch (often a loop), 75 ins | has a backward branch (often a loop) |
| `0x65c700` | 264 | 3 | `shape only` | has a backward branch (often a loop), 73 ins | has a backward branch (often a loop) |
| `0x8e4460` | 264 | 5 | `shape only` | has a backward branch (often a loop), 89 ins | has a backward branch (often a loop) |
| `0x1cded0` | 263 | 1 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x95abe0` | 263 | 2 | `shape only` | has a backward branch (often a loop), 85 ins | has a backward branch (often a loop) |
| `0x3ef3d0` | 262 | 12 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x639a40` | 262 | 4 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x932d20` | 262 | 2 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x942780` | 262 | 2 | `shape only` | has a backward branch (often a loop), 84 ins | has a backward branch (often a loop) |
| `0x4d6110` | 261 | 16 | `shape only` | has a backward branch (often a loop), 64 ins | has a backward branch (often a loop) |
| `0x97e420` | 261 | 2 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x56f990` | 260 | 2 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x580e70` | 260 | 1 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x5d5ba0` | 260 | 1 | `shape only` | has a backward branch (often a loop), 74 ins | has a backward branch (often a loop) |
| `0x905d00` | 260 | 5 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x98e0a0` | 260 | 8 | `shape only` | has a backward branch (often a loop), 79 ins | has a backward branch (often a loop) |
| `0x5d9e90` | 259 | 2 | `shape only` | straight line / call sequence, 47 ins | straight line / call sequence |
| `0x55e190` | 258 | 3 | `shape only` | straight line / call sequence, 65 ins | straight line / call sequence |
| `0x57e470` | 258 | 2 | `shape only` | has a backward branch (often a loop), 72 ins | has a backward branch (often a loop) |
| `0x5c72a0` | 258 | 5 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x896cc0` | 258 | 2 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x986860` | 258 | 4 | `shape only` | has a backward branch (often a loop), 68 ins | has a backward branch (often a loop) |
| `0x1bf1a0` | 257 | 3 | `shape only` | has a backward branch (often a loop), 62 ins | has a backward branch (often a loop) |
| `0x528ae0` | 257 | 1 | `shape only` | straight line / call sequence, 55 ins | straight line / call sequence |
| `0x5fca80` | 257 | 9 | `strings` | Negative integer can not be converted to \| Real out of unsigned integer range | has a backward branch (often a loop) |
| `0x8f29e0` | 257 | 1 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x967630` | 257 | 2 | `shape only` | has a backward branch (often a loop), 87 ins | has a backward branch (often a loop) |
| `0x1aaba0` | 256 | 4 | `shape only` | has a backward branch (often a loop), 72 ins | has a backward branch (often a loop) |
| `0x64cb30` | 256 | 1 | `strings` | ->  | straight line / call sequence |
| `0x652f60` | 256 | 2 | `shape only` | has a backward branch (often a loop), 71 ins | has a backward branch (often a loop) |
| `0x8bb0a0` | 256 | 2 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x8be440` | 256 | 5 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x8bedc0` | 256 | 4 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x8c3ad0` | 256 | 3 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x8c8ba0` | 256 | 16 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x8c9d20` | 256 | 3 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x8cee00` | 256 | 2 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x8cf000` | 256 | 3 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x8d2d60` | 256 | 2 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x8d3780` | 256 | 6 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x906570` | 256 | 2 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x908f60` | 256 | 2 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x96acf0` | 256 | 2 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x119010` | 255 | 5 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x15e5a0` | 255 | 8 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x50ffd0` | 255 | 2 | `shape only` | has a backward branch (often a loop), 74 ins | has a backward branch (often a loop) |
| `0x533ea0` | 255 | 2 | `shape only` | has a backward branch (often a loop), 88 ins | has a backward branch (often a loop) |
| `0x5479d0` | 255 | 8 | `shape only` | has a backward branch (often a loop), 74 ins | has a backward branch (often a loop) |
| `0x5f8760` | 255 | 2 | `shape only` | has a backward branch (often a loop), 78 ins | has a backward branch (often a loop) |
| `0x92dbf0` | 255 | 19 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x930b20` | 255 | 2 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x1be560` | 254 | 2 | `shape only` | has a backward branch (often a loop), 66 ins | has a backward branch (often a loop) |
| `0x4db0d0` | 254 | 4 | `shape only` | has a backward branch (often a loop), 71 ins | has a backward branch (often a loop) |
| `0x4db1d0` | 254 | 2 | `shape only` | has a backward branch (often a loop), 71 ins | has a backward branch (often a loop) |
| `0x5ccb10` | 254 | 3 | `shape only` | has a backward branch (often a loop), 64 ins | has a backward branch (often a loop) |
| `0x8adf30` | 254 | 7 | `shape only` | has a backward branch (often a loop), 74 ins | has a backward branch (often a loop) |
| `0x5c5ff0` | 253 | 11 | `shape only` | has a backward branch (often a loop), 76 ins | has a backward branch (often a loop) |
| `0x60f680` | 253 | 7 | `strings` | `Q] | has a backward branch (often a loop) |
| `0x6eaf20` | 253 | 2 | `strings` | VSH | straight line / call sequence |
| `0x8b7d20` | 253 | 10 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x8b7e20` | 253 | 5 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x8f12b0` | 253 | 3 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x8ff520` | 253 | 2 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x8ff620` | 253 | 2 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x908440` | 253 | 3 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x908540` | 253 | 2 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x908c60` | 253 | 3 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x908e60` | 253 | 3 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x1ea9c0` | 252 | 8 | `shape only` | has a backward branch (often a loop), 66 ins | has a backward branch (often a loop) |
| `0x7c3a70` | 252 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x87d270` | 252 | 4 | `shape only` | has a backward branch (often a loop), 79 ins | has a backward branch (often a loop) |
| `0x95aae0` | 252 | 2 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x5e6360` | 251 | 3 | `shape only` | straight line / call sequence, 51 ins | straight line / call sequence |
| `0x64b1c0` | 251 | 1 | `strings` | ->  | straight line / call sequence |
| `0x64c6b0` | 251 | 4 | `strings` | ->  | straight line / call sequence |
| `0x775500` | 251 | 25 | `shape only` | straight line / call sequence, 42 ins | straight line / call sequence |
| `0x7bb330` | 251 | 2 | `shape only` | has a backward branch (often a loop), 76 ins | has a backward branch (often a loop) |
| `0x866080` | 251 | 5 | `shape only` | has a backward branch (often a loop), 68 ins | has a backward branch (often a loop) |
| `0x20f490` | 250 | 2 | `shape only` | has a backward branch (often a loop), 68 ins | has a backward branch (often a loop) |
| `0x5065f0` | 250 | 2 | `shape only` | has a backward branch (often a loop), 73 ins | has a backward branch (often a loop) |
| `0x942bd0` | 250 | 5 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x942cd0` | 250 | 6 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x1d770` | 249 | 3 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x6eba90` | 249 | 3 | `shape only` | has a backward branch (often a loop), 61 ins | has a backward branch (often a loop) |
| `0x86bf00` | 249 | 4 | `shape only` | has a backward branch (often a loop), 75 ins | has a backward branch (often a loop) |
| `0x89fcd0` | 249 | 3 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x8a0a60` | 249 | 4 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x87d8e0` | 248 | 54 | `callers` | called by 0x2ab0 LaunchLocalComputation; 0x6100 LaunchComputation; 0x104d0 WaitComputationTermination | has a backward branch (often a loop) |
| `0x22d8e0` | 247 | 4 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x5b3890` | 247 | 2 | `shape only` | has a backward branch (often a loop), 76 ins | has a backward branch (often a loop) |
| `0x5bf0c0` | 247 | 2 | `shape only` | has a backward branch (often a loop), 68 ins | has a backward branch (often a loop) |
| `0x896210` | 247 | 3 | `shape only` | has a backward branch (often a loop), 75 ins | has a backward branch (often a loop) |
| `0x93cdf0` | 247 | 2 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x93d230` | 247 | 7 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x93d330` | 247 | 2 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x941a40` | 247 | 3 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x95b960` | 247 | 5 | `shape only` | has a backward branch (often a loop), 76 ins | has a backward branch (often a loop) |
| `0x96cb80` | 247 | 2 | `shape only` | has a backward branch (often a loop), 71 ins | has a backward branch (often a loop) |
| `0x23bf0` | 246 | 27 | `shape only` | has a backward branch (often a loop), 65 ins | has a backward branch (often a loop) |
| `0x557140` | 246 | 2 | `shape only` | has a backward branch (often a loop), 72 ins | has a backward branch (often a loop) |
| `0x597920` | 246 | 8 | `shape only` | has a backward branch (often a loop), 72 ins | has a backward branch (often a loop) |
| `0x8ab730` | 246 | 16 | `strings` | vector::reserve | has a backward branch (often a loop) |
| `0x4defa0` | 245 | 1 | `shape only` | straight line / call sequence, 60 ins | straight line / call sequence |
| `0x97f750` | 245 | 2 | `shape only` | has a backward branch (often a loop), 73 ins | has a backward branch (often a loop) |
| `0x986760` | 245 | 3 | `shape only` | has a backward branch (often a loop), 71 ins | has a backward branch (often a loop) |
| `0x2203a0` | 244 | 3 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x4f4500` | 244 | 2 | `shape only` | has a backward branch (often a loop), 70 ins | has a backward branch (often a loop) |
| `0x618500` | 244 | 6 | `shape only` | has a backward branch (often a loop), 72 ins | has a backward branch (often a loop) |
| `0x6398e0` | 244 | 4 | `shape only` | has a backward branch (often a loop), 58 ins | has a backward branch (often a loop) |
| `0x65e430` | 244 | 6 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x7db4e0` | 244 | 4 | `shape only` | has a backward branch (often a loop), 93 ins | has a backward branch (often a loop) |
| `0x7db5e0` | 244 | 7 | `shape only` | has a backward branch (often a loop), 91 ins | has a backward branch (often a loop) |
| `0x8d6360` | 244 | 5 | `shape only` | has a backward branch (often a loop), 78 ins | has a backward branch (often a loop) |
| `0x966410` | 244 | 2 | `shape only` | has a backward branch (often a loop), 76 ins | has a backward branch (often a loop) |
| `0xf4de0` | 243 | 17 | `shape only` | has a backward branch (often a loop), 76 ins | has a backward branch (often a loop) |
| `0x20b000` | 242 | 11 | `shape only` | has a backward branch (often a loop), 74 ins | has a backward branch (often a loop) |
| `0x4d6da0` | 242 | 3 | `shape only` | straight line / call sequence, 59 ins | straight line / call sequence |
| `0x530010` | 242 | 11 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x60bca0` | 242 | 1 | `shape only` | has a backward branch (often a loop), 66 ins | has a backward branch (often a loop) |
| `0x639b50` | 242 | 4 | `shape only` | has a backward branch (often a loop), 72 ins | has a backward branch (often a loop) |
| `0x8db50` | 241 | 2 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0x4cc540` | 241 | 1 | `shape only` | has a backward branch (often a loop), 73 ins | has a backward branch (often a loop) |
| `0x419210` | 240 | 3 | `shape only` | has a backward branch (often a loop), 70 ins | has a backward branch (often a loop) |
| `0x5d9a10` | 240 | 4 | `shape only` | straight line / call sequence, 45 ins | straight line / call sequence |
| `0x653190` | 240 | 3 | `shape only` | has a backward branch (often a loop), 76 ins | has a backward branch (often a loop) |
| `0x707fd0` | 240 | 12 | `shape only` | has a backward branch (often a loop), 78 ins | has a backward branch (often a loop) |
| `0x86c440` | 240 | 2 | `shape only` | has a backward branch (often a loop), 70 ins | has a backward branch (often a loop) |
| `0x1c3420` | 239 | 2 | `shape only` | straight line / call sequence, 83 ins | straight line / call sequence |
| `0x4fcc90` | 239 | 2 | `shape only` | has a backward branch (often a loop), 86 ins | has a backward branch (often a loop) |
| `0x54fbc0` | 239 | 2 | `shape only` | has a backward branch (often a loop), 82 ins | has a backward branch (often a loop) |
| `0x24dd40` | 238 | 1 | `shape only` | straight line / call sequence, 50 ins | straight line / call sequence |
| `0x9879a0` | 238 | 2 | `shape only` | has a backward branch (often a loop), 78 ins | has a backward branch (often a loop) |
| `0x56ab0` | 237 | 1 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x17bbd0` | 237 | 2 | `shape only` | has a backward branch (often a loop), 62 ins | has a backward branch (often a loop) |
| `0x1a9060` | 237 | 2 | `shape only` | has a backward branch (often a loop), 58 ins | has a backward branch (often a loop) |
| `0x24c4a0` | 237 | 5 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x5c3d90` | 237 | 7 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x4b82f0` | 236 | 7 | `shape only` | has a backward branch (often a loop), 80 ins | has a backward branch (often a loop) |
| `0x542f30` | 236 | 2 | `shape only` | has a backward branch (often a loop), 66 ins | has a backward branch (often a loop) |
| `0x639d40` | 236 | 3 | `shape only` | has a backward branch (often a loop), 75 ins | has a backward branch (often a loop) |
| `0x94c320` | 236 | 3 | `shape only` | has a backward branch (often a loop), 70 ins | has a backward branch (often a loop) |
| `0x820940` | 235 | 3 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x83cd0` | 234 | 2 | `shape only` | has a backward branch (often a loop), 64 ins | has a backward branch (often a loop) |
| `0x518fc0` | 234 | 1 | `shape only` | straight line / call sequence, 56 ins | straight line / call sequence |
| `0x86be10` | 234 | 2 | `shape only` | has a backward branch (often a loop), 70 ins | has a backward branch (often a loop) |
| `0x86c160` | 234 | 2 | `shape only` | has a backward branch (often a loop), 70 ins | has a backward branch (often a loop) |
| `0x899dc0` | 234 | 3 | `shape only` | has a backward branch (often a loop), 83 ins | has a backward branch (often a loop) |
| `0x97f660` | 234 | 2 | `shape only` | has a backward branch (often a loop), 71 ins | has a backward branch (often a loop) |
| `0x14f5f0` | 233 | 1 | `shape only` | straight line / call sequence, 63 ins | straight line / call sequence |
| `0x1a60b0` | 233 | 4 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x271460` | 233 | 17 | `shape only` | has a backward branch (often a loop), 51 ins | has a backward branch (often a loop) |
| `0x5d9b00` | 233 | 7 | `shape only` | straight line / call sequence, 44 ins | straight line / call sequence |
| `0x65cb60` | 233 | 2 | `shape only` | straight line / call sequence, 78 ins | straight line / call sequence |
| `0x86d8f0` | 233 | 2 | `shape only` | has a backward branch (often a loop), 70 ins | has a backward branch (often a loop) |
| `0x98ee60` | 233 | 2 | `shape only` | has a backward branch (often a loop), 91 ins | has a backward branch (often a loop) |
| `0x5c14d0` | 232 | 1 | `shape only` | straight line / call sequence, 58 ins | straight line / call sequence |
| `0x8fd3c0` | 232 | 3 | `shape only` | has a backward branch (often a loop), 81 ins | has a backward branch (often a loop) |
| `0x65c230` | 231 | 3 | `strings` | => ##################### Section start  | has a backward branch (often a loop) |
| `0x9431a0` | 231 | 2 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x236ad0` | 230 | 4 | `shape only` | has a backward branch (often a loop), 76 ins | has a backward branch (often a loop) |
| `0x592780` | 230 | 5 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x92f2b0` | 230 | 3 | `shape only` | has a backward branch (often a loop), 73 ins | has a backward branch (often a loop) |
| `0x998a60` | 230 | 26 | `shape only` | straight line / call sequence, 60 ins | straight line / call sequence |
| `0x1aaef0` | 229 | 3 | `strings` | new | has a backward branch (often a loop) |
| `0x8ae030` | 229 | 2 | `shape only` | straight line / call sequence, 59 ins | straight line / call sequence |
| `0x96cc80` | 229 | 3 | `shape only` | has a backward branch (often a loop), 68 ins | has a backward branch (often a loop) |
| `0x96cd70` | 229 | 2 | `shape only` | has a backward branch (often a loop), 68 ins | has a backward branch (often a loop) |
| `0x1783e0` | 228 | 3 | `shape only` | has a backward branch (often a loop), 73 ins | has a backward branch (often a loop) |
| `0x6ea3e0` | 228 | 5 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x853b00` | 228 | 6 | `shape only` | has a backward branch (often a loop), 72 ins | has a backward branch (often a loop) |
| `0x62f7a0` | 227 | 6 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0x65c810` | 227 | 2 | `strings` | a+b \| r+b | has a backward branch (often a loop) |
| `0x678e50` | 227 | 4 | `shape only` | has a backward branch (often a loop), 78 ins | has a backward branch (often a loop) |
| `0x67db10` | 227 | 21 | `shape only` | has a backward branch (often a loop), 78 ins | has a backward branch (often a loop) |
| `0x6f4bb0` | 227 | 3 | `shape only` | has a backward branch (often a loop), 63 ins | has a backward branch (often a loop) |
| `0x701e80` | 227 | 6 | `strings` | Boost.Geometry Turn exception:  | has a backward branch (often a loop) |
| `0x853bf0` | 227 | 2 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x5d9da0` | 226 | 2 | `shape only` | straight line / call sequence, 43 ins | straight line / call sequence |
| `0x89f350` | 226 | 5 | `shape only` | has a backward branch (often a loop), 78 ins | has a backward branch (often a loop) |
| `0x9367c0` | 226 | 1 | `shape only` | has a backward branch (often a loop), 73 ins | has a backward branch (often a loop) |
| `0xeeee0` | 225 | 17 | `strings` | SE1 \| WVSE1 | straight line / call sequence |
| `0x58a100` | 225 | 1 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x7763a0` | 225 | 11 | `shape only` | straight line / call sequence, 41 ins | straight line / call sequence |
| `0x925970` | 225 | 2 | `shape only` | has a backward branch (often a loop), 72 ins | has a backward branch (often a loop) |
| `0x62fbd0` | 224 | 6 | `shape only` | has a backward branch (often a loop), 50 ins | has a backward branch (often a loop) |
| `0x62fcb0` | 224 | 2 | `shape only` | has a backward branch (often a loop), 50 ins | has a backward branch (often a loop) |
| `0x938a40` | 224 | 1 | `shape only` | has a backward branch (often a loop), 72 ins | has a backward branch (often a loop) |
| `0x40bf0` | 223 | 2 | `shape only` | has a backward branch (often a loop), 76 ins | has a backward branch (often a loop) |
| `0x40cd0` | 223 | 2 | `shape only` | has a backward branch (often a loop), 75 ins | has a backward branch (often a loop) |
| `0x5b37b0` | 223 | 5 | `shape only` | has a backward branch (often a loop), 68 ins | has a backward branch (often a loop) |
| `0x9376d0` | 223 | 1 | `shape only` | has a backward branch (often a loop), 72 ins | has a backward branch (often a loop) |
| `0x924d80` | 221 | 2 | `shape only` | has a backward branch (often a loop), 74 ins | has a backward branch (often a loop) |
| `0x924ea0` | 221 | 2 | `shape only` | has a backward branch (often a loop), 74 ins | has a backward branch (often a loop) |
| `0x924fd0` | 221 | 2 | `shape only` | has a backward branch (often a loop), 74 ins | has a backward branch (often a loop) |
| `0x9251d0` | 221 | 2 | `shape only` | has a backward branch (often a loop), 74 ins | has a backward branch (often a loop) |
| `0x9257b0` | 221 | 2 | `shape only` | has a backward branch (often a loop), 74 ins | has a backward branch (often a loop) |
| `0x546930` | 220 | 4 | `shape only` | has a backward branch (often a loop), 74 ins | has a backward branch (often a loop) |
| `0x55e7e0` | 220 | 5 | `shape only` | straight line / call sequence, 48 ins | straight line / call sequence |
| `0x8f2f30` | 220 | 3 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x8f3010` | 220 | 2 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x8f30f0` | 220 | 3 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x8f31d0` | 220 | 4 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x8f32b0` | 220 | 3 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x8f3390` | 220 | 3 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x8f39d0` | 220 | 4 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x8f3d60` | 220 | 2 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x8f3fa0` | 220 | 3 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x8f4080` | 220 | 2 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x8f4740` | 220 | 2 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x8f4820` | 220 | 5 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x8f49e0` | 220 | 3 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x8f4ac0` | 220 | 2 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x8f4c80` | 220 | 2 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x8f4e40` | 220 | 2 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x90be10` | 220 | 10 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x90dbe0` | 220 | 4 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x97f1d0` | 220 | 2 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x98a6f0` | 220 | 1 | `shape only` | straight line / call sequence, 56 ins | straight line / call sequence |
| `0x98da70` | 220 | 2 | `shape only` | has a backward branch (often a loop), 77 ins | has a backward branch (often a loop) |
| `0x1d10e0` | 219 | 2 | `shape only` | has a backward branch (often a loop), 70 ins | has a backward branch (often a loop) |
| `0x6248f0` | 219 | 2 | `shape only` | has a backward branch (often a loop), 63 ins | has a backward branch (often a loop) |
| `0x8cf900` | 219 | 3 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x8e7a10` | 219 | 2 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x523100` | 218 | 4 | `shape only` | has a backward branch (often a loop), 76 ins | has a backward branch (often a loop) |
| `0x8ab880` | 218 | 27 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x1a9170` | 217 | 2 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x6f8220` | 217 | 3 | `shape only` | straight line / call sequence, 60 ins | straight line / call sequence |
| `0x8e2a60` | 217 | 1 | `shape only` | has a backward branch (often a loop), 76 ins | has a backward branch (often a loop) |
| `0x1a5500` | 216 | 2 | `shape only` | has a backward branch (often a loop), 57 ins | has a backward branch (often a loop) |
| `0x4184e0` | 216 | 15 | `shape only` | has a backward branch (often a loop), 61 ins | has a backward branch (often a loop) |
| `0x8bafc0` | 216 | 2 | `shape only` | has a backward branch (often a loop), 70 ins | has a backward branch (often a loop) |
| `0x72dbd0` | 215 | 5 | `shape only` | has a backward branch (often a loop), 58 ins | has a backward branch (often a loop) |
| `0x77f2d0` | 215 | 44 | `strings` | BER decode error | has a backward branch (often a loop) |
| `0x78f660` | 215 | 17 | `shape only` | has a backward branch (often a loop), 74 ins | has a backward branch (often a loop) |
| `0x7bb620` | 215 | 5 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x55aa90` | 213 | 7 | `shape only` | straight line / call sequence, 51 ins | straight line / call sequence |
| `0x55b470` | 213 | 5 | `shape only` | has a backward branch (often a loop), 64 ins | has a backward branch (often a loop) |
| `0x13b880` | 212 | 2 | `shape only` | has a backward branch (often a loop), 61 ins | has a backward branch (often a loop) |
| `0x1a5970` | 212 | 2 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x3bc140` | 212 | 3 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x5ffe30` | 212 | 15 | `shape only` | has a backward branch (often a loop), 62 ins | has a backward branch (often a loop) |
| `0x5fbb10` | 211 | 9 | `strings` | VSH | has a backward branch (often a loop) |
| `0x5c2370` | 210 | 5 | `shape only` | has a backward branch (often a loop), 52 ins | has a backward branch (often a loop) |
| `0x7c68d0` | 210 | 2 | `shape only` | has a backward branch (often a loop), 63 ins | has a backward branch (often a loop) |
| `0x24fd0` | 209 | 1 | `shape only` | straight line / call sequence, 53 ins | straight line / call sequence |
| `0x5335d0` | 209 | 4 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x553150` | 209 | 6 | `shape only` | has a backward branch (often a loop), 70 ins | has a backward branch (often a loop) |
| `0x5afc00` | 209 | 3 | `shape only` | has a backward branch (often a loop), 70 ins | has a backward branch (often a loop) |
| `0x5d0280` | 209 | 2 | `shape only` | has a backward branch (often a loop), 52 ins | has a backward branch (often a loop) |
| `0x5e8020` | 209 | 13 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x5e8ce0` | 209 | 8 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x63a1c0` | 209 | 2 | `shape only` | has a backward branch (often a loop), 58 ins | has a backward branch (often a loop) |
| `0x8bb1a0` | 209 | 6 | `shape only` | has a backward branch (often a loop), 66 ins | has a backward branch (often a loop) |
| `0x90ca10` | 209 | 10 | `shape only` | has a backward branch (often a loop), 66 ins | has a backward branch (often a loop) |
| `0x90d6b0` | 209 | 24 | `shape only` | has a backward branch (often a loop), 66 ins | has a backward branch (often a loop) |
| `0x90d790` | 209 | 25 | `shape only` | has a backward branch (often a loop), 66 ins | has a backward branch (often a loop) |
| `0x15a500` | 208 | 2 | `shape only` | has a backward branch (often a loop), 57 ins | has a backward branch (often a loop) |
| `0x5e5cd0` | 208 | 3 | `shape only` | has a backward branch (often a loop), 55 ins | has a backward branch (often a loop) |
| `0x8b7ad0` | 208 | 5 | `shape only` | has a backward branch (often a loop), 68 ins | has a backward branch (often a loop) |
| `0x678f40` | 207 | 6 | `shape only` | straight line / call sequence, 61 ins | straight line / call sequence |
| `0x5da160` | 206 | 7 | `shape only` | has a backward branch (often a loop), 61 ins | has a backward branch (often a loop) |
| `0x5c2200` | 205 | 2 | `shape only` | has a backward branch (often a loop), 43 ins | has a backward branch (often a loop) |
| `0x621de0` | 205 | 3 | `shape only` | has a backward branch (often a loop), 70 ins | has a backward branch (often a loop) |
| `0x7bbf30` | 205 | 2 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x159ba0` | 204 | 2 | `shape only` | straight line / call sequence, 54 ins | straight line / call sequence |
| `0x527b20` | 204 | 4 | `shape only` | has a backward branch (often a loop), 62 ins | has a backward branch (often a loop) |
| `0x63e310` | 204 | 4 | `shape only` | has a backward branch (often a loop), 52 ins | has a backward branch (often a loop) |
| `0x1b840` | 203 | 2 | `shape only` | has a backward branch (often a loop), 53 ins | has a backward branch (often a loop) |
| `0xc33f0` | 203 | 21 | `shape only` | has a backward branch (often a loop), 48 ins | has a backward branch (often a loop) |
| `0x4b8220` | 203 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x62cb20` | 203 | 3 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x656040` | 203 | 10 | `shape only` | straight line / call sequence, 62 ins | straight line / call sequence |
| `0x937170` | 203 | 4 | `shape only` | has a backward branch (often a loop), 61 ins | has a backward branch (often a loop) |
| `0x1dd870` | 202 | 2 | `shape only` | straight line / call sequence, 48 ins | straight line / call sequence |
| `0x580c00` | 202 | 9 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x634f90` | 202 | 2 | `shape only` | straight line / call sequence, 53 ins | straight line / call sequence |
| `0x656110` | 202 | 3 | `strings` | WVSH | has a backward branch (often a loop) |
| `0x6d6870` | 202 | 1 | `shape only` | has a backward branch (often a loop), 65 ins | has a backward branch (often a loop) |
| `0x7862d0` | 202 | 2 | `shape only` | has a backward branch (often a loop), 68 ins | has a backward branch (often a loop) |
| `0x79c8d0` | 202 | 8 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x8aaa10` | 202 | 3 | `shape only` | straight line / call sequence, 59 ins | straight line / call sequence |
| `0x915080` | 202 | 37 | `shape only` | has a backward branch (often a loop), 55 ins | has a backward branch (often a loop) |
| `0x4f50f0` | 201 | 1 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0x505780` | 201 | 2 | `strings` | clustered_parts | has a backward branch (often a loop) |
| `0x5fda80` | 201 | 6 | `shape only` | has a backward branch (often a loop), 69 ins | has a backward branch (often a loop) |
| `0x60b260` | 201 | 2 | `strings` | [no call frames available] | has a backward branch (often a loop) |
| `0x873680` | 201 | 2 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x90d490` | 201 | 5 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x998cd0` | 201 | 37 | `shape only` | has a backward branch (often a loop), 49 ins | has a backward branch (often a loop) |
| `0x1a5390` | 200 | 2 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x896e60` | 200 | 2 | `shape only` | has a backward branch (often a loop), 64 ins | has a backward branch (often a loop) |
| `0x1ba30` | 198 | 14 | `shape only` | has a backward branch (often a loop), 50 ins | has a backward branch (often a loop) |
| `0x626b20` | 198 | 3 | `shape only` | has a backward branch (often a loop), 66 ins | has a backward branch (often a loop) |
| `0x97afc0` | 198 | 2 | `shape only` | straight line / call sequence, 64 ins | straight line / call sequence |
| `0x5452a0` | 197 | 4 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x96d4b0` | 197 | 2 | `shape only` | has a backward branch (often a loop), 65 ins | has a backward branch (often a loop) |
| `0x5e7b70` | 196 | 2 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x8ac550` | 196 | 1 | `shape only` | has a backward branch (often a loop), 72 ins | has a backward branch (often a loop) |
| `0x8f89b0` | 196 | 3 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x17f3e0` | 195 | 6 | `shape only` | has a backward branch (often a loop), 61 ins | has a backward branch (often a loop) |
| `0x1fb740` | 195 | 3 | `shape only` | has a backward branch (often a loop), 62 ins | has a backward branch (often a loop) |
| `0x544790` | 195 | 2 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x76f270` | 194 | 2 | `shape only` | has a backward branch (often a loop), 62 ins | has a backward branch (often a loop) |
| `0x8f5460` | 194 | 2 | `shape only` | has a backward branch (often a loop), 70 ins | has a backward branch (often a loop) |
| `0x4fbca0` | 193 | 3 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x523e60` | 193 | 6 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x523fe0` | 193 | 5 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x7c30c0` | 193 | 5 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x1e010` | 192 | 3 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0x24b80` | 192 | 1 | `shape only` | straight line / call sequence, 50 ins | straight line / call sequence |
| `0x2e590` | 192 | 1 | `shape only` | has a backward branch (often a loop), 62 ins | has a backward branch (often a loop) |
| `0x2fb50` | 192 | 2 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0x77d80` | 192 | 4 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0x197730` | 192 | 7 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0x5d8f10` | 192 | 3 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0x6d6940` | 192 | 3 | `shape only` | has a backward branch (often a loop), 62 ins | has a backward branch (often a loop) |
| `0x7f41c0` | 192 | 5 | `shape only` | has a backward branch (often a loop), 37 ins | has a backward branch (often a loop) |
| `0x82b1b0` | 192 | 3 | `shape only` | has a backward branch (often a loop), 62 ins | has a backward branch (often a loop) |
| `0x24e50` | 191 | 1 | `strings` | `HNk \|  GNk | straight line / call sequence |
| `0x24f10` | 191 | 1 | `shape only` | straight line / call sequence, 49 ins | straight line / call sequence |
| `0x172360` | 191 | 1 | `strings` |  $ck | straight line / call sequence |
| `0x57c470` | 191 | 1 | `shape only` | has a backward branch (often a loop), 62 ins | has a backward branch (often a loop) |
| `0x24ab0` | 190 | 3 | `shape only` | straight line / call sequence, 48 ins | straight line / call sequence |
| `0xf49e0` | 190 | 34 | `shape only` | straight line / call sequence, 64 ins | straight line / call sequence |
| `0x16c2f0` | 190 | 25 | `shape only` | has a backward branch (often a loop), 51 ins | has a backward branch (often a loop) |
| `0x17bcc0` | 190 | 1 | `shape only` | straight line / call sequence, 47 ins | straight line / call sequence |
| `0x5a39e0` | 190 | 2 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x8d1fe0` | 190 | 2 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0x95ffc0` | 190 | 4 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x17fb60` | 189 | 1 | `shape only` | straight line / call sequence, 48 ins | straight line / call sequence |
| `0x1a7580` | 189 | 2 | `shape only` | straight line / call sequence, 51 ins | straight line / call sequence |
| `0x72e060` | 189 | 11 | `shape only` | has a backward branch (often a loop), 63 ins | has a backward branch (often a loop) |
| `0x1b8140` | 188 | 1 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0x6d33a0` | 188 | 1 | `shape only` | straight line / call sequence, 58 ins | straight line / call sequence |
| `0x925e70` | 188 | 2 | `shape only` | has a backward branch (often a loop), 67 ins | has a backward branch (often a loop) |
| `0x932780` | 188 | 4 | `shape only` | has a backward branch (often a loop), 63 ins | has a backward branch (often a loop) |
| `0x9328f0` | 188 | 4 | `shape only` | has a backward branch (often a loop), 63 ins | has a backward branch (often a loop) |
| `0x2c3e20` | 187 | 5 | `shape only` | straight line / call sequence, 56 ins | straight line / call sequence |
| `0x523980` | 187 | 5 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x86c380` | 187 | 2 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0x25af80` | 185 | 6 | `shape only` | has a backward branch (often a loop), 58 ins | has a backward branch (often a loop) |
| `0x51f970` | 185 | 4 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x7ba5f0` | 185 | 2 | `shape only` | has a backward branch (often a loop), 66 ins | has a backward branch (often a loop) |
| `0x8733b0` | 185 | 2 | `shape only` | has a backward branch (often a loop), 58 ins | has a backward branch (often a loop) |
| `0x8e76a0` | 185 | 2 | `shape only` | has a backward branch (often a loop), 57 ins | has a backward branch (often a loop) |
| `0x15a410` | 184 | 8 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x20cfe0` | 184 | 4 | `shape only` | has a backward branch (often a loop), 57 ins | has a backward branch (often a loop) |
| `0x89dfe0` | 184 | 3 | `shape only` | has a backward branch (often a loop), 50 ins | has a backward branch (often a loop) |
| `0x93f110` | 184 | 2 | `shape only` | has a backward branch (often a loop), 61 ins | has a backward branch (often a loop) |
| `0xf1340` | 183 | 7 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x1a4920` | 183 | 9 | `shape only` | straight line / call sequence, 40 ins | straight line / call sequence |
| `0x51f8b0` | 182 | 2 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x77a2c0` | 182 | 6 | `shape only` | straight line / call sequence, 51 ins | straight line / call sequence |
| `0x86ec10` | 182 | 2 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0x86ef20` | 182 | 3 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0x2fa90` | 181 | 5 | `shape only` | has a backward branch (often a loop), 55 ins | has a backward branch (often a loop) |
| `0x52520` | 181 | 2 | `shape only` | has a backward branch (often a loop), 55 ins | has a backward branch (often a loop) |
| `0x538fd0` | 181 | 2 | `shape only` | has a backward branch (often a loop), 55 ins | has a backward branch (often a loop) |
| `0x5c2fa0` | 181 | 1 | `shape only` | has a backward branch (often a loop), 44 ins | has a backward branch (often a loop) |
| `0x1c1d40` | 180 | 8 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x1aa170` | 178 | 1 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x1b7c80` | 178 | 4 | `shape only` | has a backward branch (often a loop), 49 ins | has a backward branch (often a loop) |
| `0x57d920` | 178 | 7 | `shape only` | has a backward branch (often a loop), 46 ins | has a backward branch (often a loop) |
| `0x5c8f30` | 178 | 10 | `shape only` | has a backward branch (often a loop), 51 ins | has a backward branch (often a loop) |
| `0x5e5ee0` | 178 | 6 | `shape only` | straight line / call sequence, 45 ins | straight line / call sequence |
| `0x5fcb90` | 178 | 11 | `strings` | Type is not convertible to double | has a backward branch (often a loop) |
| `0x799f60` | 178 | 28 | `shape only` | has a backward branch (often a loop), 55 ins | has a backward branch (often a loop) |
| `0x7b7910` | 178 | 3 | `shape only` | has a backward branch (often a loop), 53 ins | has a backward branch (often a loop) |
| `0x8c3730` | 178 | 12 | `shape only` | has a backward branch (often a loop), 53 ins | has a backward branch (often a loop) |
| `0x16c0` | 177 | 3 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x2f9d0` | 177 | 4 | `shape only` | straight line / call sequence, 60 ins | straight line / call sequence |
| `0x52310` | 177 | 7 | `shape only` | straight line / call sequence, 60 ins | straight line / call sequence |
| `0x5ec80` | 177 | 3 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x84ac0` | 177 | 5 | `shape only` | straight line / call sequence, 60 ins | straight line / call sequence |
| `0x9e510` | 177 | 2 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x157c90` | 177 | 2 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x1c0f50` | 177 | 6 | `shape only` | straight line / call sequence, 60 ins | straight line / call sequence |
| `0x1d70a0` | 177 | 1 | `shape only` | straight line / call sequence, 60 ins | straight line / call sequence |
| `0x20bfc0` | 177 | 4 | `shape only` | straight line / call sequence, 60 ins | straight line / call sequence |
| `0x2662f0` | 177 | 2 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x4c4b30` | 177 | 2 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x5523b0` | 177 | 8 | `shape only` | straight line / call sequence, 60 ins | straight line / call sequence |
| `0x5d8df0` | 177 | 14 | `shape only` | straight line / call sequence, 60 ins | straight line / call sequence |
| `0x97b090` | 177 | 2 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0xf0f00` | 176 | 12 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x4efa30` | 176 | 1 | `shape only` | straight line / call sequence, 38 ins | straight line / call sequence |
| `0x5fa940` | 176 | 2 | `shape only` | straight line / call sequence, 50 ins | straight line / call sequence |
| `0x1a9250` | 175 | 3 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x203db0` | 175 | 3 | `shape only` | has a backward branch (often a loop), 57 ins | has a backward branch (often a loop) |
| `0x261e60` | 175 | 5 | `shape only` | has a backward branch (often a loop), 53 ins | has a backward branch (often a loop) |
| `0x5522b0` | 175 | 1 | `shape only` | straight line / call sequence, 52 ins | straight line / call sequence |
| `0x63a6a0` | 175 | 2 | `shape only` | has a backward branch (often a loop), 51 ins | has a backward branch (often a loop) |
| `0x2e650` | 174 | 3 | `shape only` | has a backward branch (often a loop), 58 ins | has a backward branch (often a loop) |
| `0x65e820` | 174 | 3 | `shape only` | straight line / call sequence, 40 ins | straight line / call sequence |
| `0x897a10` | 174 | 3 | `shape only` | has a backward branch (often a loop), 52 ins | has a backward branch (often a loop) |
| `0x51c6e0` | 173 | 3 | `shape only` | has a backward branch (often a loop), 51 ins | has a backward branch (often a loop) |
| `0x5fb860` | 173 | 21 | `shape only` | has a backward branch (often a loop), 46 ins | has a backward branch (often a loop) |
| `0x62d7b0` | 173 | 1 | `shape only` | straight line / call sequence, 41 ins | straight line / call sequence |
| `0x72d7e0` | 173 | 3 | `shape only` | straight line / call sequence, 31 ins | straight line / call sequence |
| `0x20bec0` | 172 | 4 | `shape only` | has a backward branch (often a loop), 52 ins | has a backward branch (often a loop) |
| `0x8f7d20` | 172 | 7 | `shape only` | has a backward branch (often a loop), 50 ins | has a backward branch (often a loop) |
| `0x98c1b0` | 172 | 1 | `shape only` | straight line / call sequence, 45 ins | straight line / call sequence |
| `0x15eb80` | 171 | 2 | `shape only` | has a backward branch (often a loop), 49 ins | has a backward branch (often a loop) |
| `0x523f30` | 171 | 4 | `shape only` | has a backward branch (often a loop), 52 ins | has a backward branch (often a loop) |
| `0x2c6f30` | 170 | 3 | `strings` | 0oxk | straight line / call sequence |
| `0x5fac70` | 170 | 9 | `shape only` | has a backward branch (often a loop), 61 ins | has a backward branch (often a loop) |
| `0x6742b0` | 169 | 3 | `shape only` | straight line / call sequence, 29 ins | straight line / call sequence |
| `0x746220` | 169 | 2 | `shape only` | straight line / call sequence, 28 ins | straight line / call sequence |
| `0x922f40` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x9232b0` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x923620` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x931320` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x931da0` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x931ff0` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x9326d0` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x932840` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x9329b0` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x9332a0` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x93b350` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x93c0d0` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x93ca40` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x93e0f0` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x93f060` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x93f1d0` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x93f8b0` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x93fb00` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x942400` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x942530` | 169 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x945370` | 169 | 42 | `shape only` | has a backward branch (often a loop), 46 ins | has a backward branch (often a loop) |
| `0x1ae8e0` | 168 | 1 | `shape only` | straight line / call sequence, 39 ins | straight line / call sequence |
| `0x4efae0` | 168 | 1 | `shape only` | straight line / call sequence, 35 ins | straight line / call sequence |
| `0x547680` | 168 | 3 | `shape only` | has a backward branch (often a loop), 60 ins | has a backward branch (often a loop) |
| `0x6aab10` | 168 | 2 | `shape only` | has a backward branch (often a loop), 55 ins | has a backward branch (often a loop) |
| `0x6ebf50` | 168 | 3 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x6efa30` | 168 | 1 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x7c4ae0` | 168 | 1 | `shape only` | straight line / call sequence, 60 ins | straight line / call sequence |
| `0x871270` | 168 | 5 | `shape only` | has a backward branch (often a loop), 55 ins | has a backward branch (often a loop) |
| `0x1c2970` | 167 | 6 | `shape only` | has a backward branch (often a loop), 57 ins | has a backward branch (often a loop) |
| `0x598d20` | 167 | 2 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x8f7330` | 167 | 4 | `shape only` | has a backward branch (often a loop), 55 ins | has a backward branch (often a loop) |
| `0x5ec430` | 166 | 2 | `shape only` | has a backward branch (often a loop), 49 ins | has a backward branch (often a loop) |
| `0x8ba440` | 166 | 8 | `shape only` | straight line / call sequence, 46 ins | straight line / call sequence |
| `0x8e62e0` | 166 | 2 | `shape only` | straight line / call sequence, 46 ins | straight line / call sequence |
| `0xf1f50` | 165 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x5d2370` | 165 | 3 | `shape only` | has a backward branch (often a loop), 48 ins | has a backward branch (often a loop) |
| `0x51f6a0` | 164 | 2 | `shape only` | has a backward branch (often a loop), 35 ins | has a backward branch (often a loop) |
| `0x8d22f0` | 164 | 4 | `shape only` | has a backward branch (often a loop), 57 ins | has a backward branch (often a loop) |
| `0x170b00` | 163 | 3 | `shape only` | straight line / call sequence, 44 ins | straight line / call sequence |
| `0x89e150` | 163 | 1 | `shape only` | has a backward branch (often a loop), 59 ins | has a backward branch (often a loop) |
| `0x89e200` | 163 | 3 | `shape only` | has a backward branch (often a loop), 51 ins | has a backward branch (often a loop) |
| `0x991f80` | 163 | 7 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x1a2a00` | 162 | 6 | `shape only` | has a backward branch (often a loop), 51 ins | has a backward branch (often a loop) |
| `0x4dde80` | 162 | 1 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x4f51c0` | 162 | 1 | `shape only` | has a backward branch (often a loop), 50 ins | has a backward branch (often a loop) |
| `0x5a9be0` | 162 | 1 | `shape only` | straight line / call sequence, 47 ins | straight line / call sequence |
| `0x51f750` | 160 | 2 | `shape only` | has a backward branch (often a loop), 36 ins | has a backward branch (often a loop) |
| `0x5cfdc0` | 160 | 3 | `shape only` | straight line / call sequence, 37 ins | straight line / call sequence |
| `0x76dec0` | 160 | 19 | `shape only` | has a backward branch (often a loop), 50 ins | has a backward branch (often a loop) |
| `0x717460` | 159 | 4 | `shape only` | has a backward branch (often a loop), 51 ins | has a backward branch (often a loop) |
| `0x15ea80` | 158 | 1 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x5c7200` | 158 | 6 | `shape only` | straight line / call sequence, 47 ins | straight line / call sequence |
| `0x20e020` | 157 | 2 | `shape only` | straight line / call sequence, 41 ins | straight line / call sequence |
| `0x20e0c0` | 157 | 2 | `shape only` | straight line / call sequence, 41 ins | straight line / call sequence |
| `0x20e160` | 157 | 2 | `shape only` | straight line / call sequence, 41 ins | straight line / call sequence |
| `0x52b10` | 156 | 5 | `shape only` | straight line / call sequence, 41 ins | straight line / call sequence |
| `0x1fb1f0` | 156 | 3 | `shape only` | straight line / call sequence, 36 ins | straight line / call sequence |
| `0x4f2870` | 156 | 4 | `shape only` | straight line / call sequence, 41 ins | straight line / call sequence |
| `0x74b390` | 156 | 1 | `shape only` | straight line / call sequence, 34 ins | straight line / call sequence |
| `0x74b660` | 156 | 1 | `shape only` | straight line / call sequence, 34 ins | straight line / call sequence |
| `0x8cfc40` | 156 | 3 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x635250` | 155 | 1 | `shape only` | straight line / call sequence, 45 ins | straight line / call sequence |
| `0x870f70` | 155 | 5 | `shape only` | has a backward branch (often a loop), 57 ins | has a backward branch (often a loop) |
| `0x8f5990` | 155 | 1 | `shape only` | has a backward branch (often a loop), 56 ins | has a backward branch (often a loop) |
| `0x90c000` | 155 | 3 | `shape only` | straight line / call sequence, 46 ins | straight line / call sequence |
| `0x90cbd0` | 155 | 8 | `shape only` | straight line / call sequence, 46 ins | straight line / call sequence |
| `0x90d910` | 155 | 7 | `shape only` | straight line / call sequence, 46 ins | straight line / call sequence |
| `0x2a740` | 154 | 4 | `strings` | 0'6 | has a backward branch (often a loop) |
| `0x4df0a0` | 154 | 2 | `shape only` | straight line / call sequence, 40 ins | straight line / call sequence |
| `0x5e7790` | 154 | 3 | `shape only` | has a backward branch (often a loop), 44 ins | has a backward branch (often a loop) |
| `0x639ca0` | 154 | 5 | `shape only` | has a backward branch (often a loop), 40 ins | has a backward branch (often a loop) |
| `0x704400` | 154 | 19 | `shape only` | has a backward branch (often a loop), 42 ins | has a backward branch (often a loop) |
| `0x897100` | 154 | 3 | `shape only` | has a backward branch (often a loop), 52 ins | has a backward branch (often a loop) |
| `0x911470` | 154 | 22 | `shape only` | has a backward branch (often a loop), 44 ins | has a backward branch (often a loop) |
| `0x6d3300` | 153 | 1 | `shape only` | straight line / call sequence, 36 ins | straight line / call sequence |
| `0x81c080` | 153 | 11 | `shape only` | has a backward branch (often a loop), 36 ins | has a backward branch (often a loop) |
| `0x8642d0` | 153 | 1 | `shape only` | straight line / call sequence, 43 ins | straight line / call sequence |
| `0xf7260` | 152 | 21 | `strings` | UWVSH | has a backward branch (often a loop) |
| `0x538f30` | 152 | 2 | `shape only` | has a backward branch (often a loop), 45 ins | has a backward branch (often a loop) |
| `0x6d2ca0` | 152 | 3 | `shape only` | has a backward branch (often a loop), 51 ins | has a backward branch (often a loop) |
| `0x8bb6f0` | 152 | 4 | `shape only` | has a backward branch (often a loop), 46 ins | has a backward branch (often a loop) |
| `0x98dec0` | 152 | 2 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x992c0` | 151 | 2 | `shape only` | has a backward branch (often a loop), 52 ins | has a backward branch (often a loop) |
| `0x3be020` | 151 | 18 | `shape only` | straight line / call sequence, 44 ins | straight line / call sequence |
| `0x505320` | 151 | 2 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x5ccc10` | 151 | 2 | `shape only` | has a backward branch (often a loop), 39 ins | has a backward branch (often a loop) |
| `0x8d3190` | 151 | 5 | `shape only` | straight line / call sequence, 39 ins | straight line / call sequence |
| `0x1bb10` | 150 | 1 | `shape only` | has a backward branch (often a loop), 35 ins | has a backward branch (often a loop) |
| `0xbafd0` | 150 | 3 | `strings` | PK_MessageEncodingMethod: this signature | has a backward branch (often a loop) |
| `0x1a5250` | 150 | 2 | `shape only` | has a backward branch (often a loop), 44 ins | has a backward branch (often a loop) |
| `0x1a52f0` | 150 | 2 | `shape only` | has a backward branch (often a loop), 44 ins | has a backward branch (often a loop) |
| `0x240300` | 150 | 2 | `shape only` | has a backward branch (often a loop), 43 ins | has a backward branch (often a loop) |
| `0x5eaff0` | 150 | 13 | `shape only` | has a backward branch (often a loop), 46 ins | has a backward branch (often a loop) |
| `0x6de8a0` | 150 | 17 | `shape only` | straight line / call sequence, 45 ins | straight line / call sequence |
| `0x70ca50` | 150 | 3 | `shape only` | straight line / call sequence, 36 ins | straight line / call sequence |
| `0x89eba0` | 150 | 4 | `shape only` | has a backward branch (often a loop), 45 ins | has a backward branch (often a loop) |
| `0x1a5460` | 149 | 2 | `shape only` | has a backward branch (often a loop), 44 ins | has a backward branch (often a loop) |
| `0x546540` | 149 | 2 | `shape only` | has a backward branch (often a loop), 46 ins | has a backward branch (often a loop) |
| `0x660550` | 149 | 4 | `shape only` | has a backward branch (often a loop), 50 ins | has a backward branch (often a loop) |
| `0x754e70` | 149 | 11 | `shape only` | has a backward branch (often a loop), 40 ins | has a backward branch (often a loop) |
| `0x754f10` | 149 | 7 | `shape only` | has a backward branch (often a loop), 40 ins | has a backward branch (often a loop) |
| `0x1c2a20` | 148 | 2 | `shape only` | has a backward branch (often a loop), 46 ins | has a backward branch (often a loop) |
| `0x1c020` | 147 | 1 | `shape only` | straight line / call sequence, 41 ins | straight line / call sequence |
| `0x5cc190` | 147 | 1 | `shape only` | straight line / call sequence, 44 ins | straight line / call sequence |
| `0x8539c0` | 147 | 3 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x853a60` | 147 | 6 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x8ce510` | 147 | 36 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x8e9520` | 147 | 2 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x9250b0` | 147 | 6 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x925890` | 147 | 6 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x5d790` | 146 | 1 | `shape only` | has a backward branch (often a loop), 46 ins | has a backward branch (often a loop) |
| `0x51e700` | 146 | 1 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x5fcf60` | 146 | 14 | `shape only` | has a backward branch (often a loop), 54 ins | has a backward branch (often a loop) |
| `0x15b800` | 145 | 4 | `shape only` | straight line / call sequence, 42 ins | straight line / call sequence |
| `0x4daa30` | 145 | 2 | `shape only` | has a backward branch (often a loop), 37 ins | has a backward branch (often a loop) |
| `0x3ef590` | 144 | 1 | `shape only` | straight line / call sequence, 19 ins | straight line / call sequence |
| `0x6f4b20` | 144 | 9 | `shape only` | has a backward branch (often a loop), 40 ins | has a backward branch (often a loop) |
| `0x60be30` | 143 | 2 | `shape only` | has a backward branch (often a loop), 40 ins | has a backward branch (often a loop) |
| `0x4baba0` | 142 | 2 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x1be470` | 141 | 7 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x7f40b0` | 141 | 3 | `shape only` | has a backward branch (often a loop), 49 ins | has a backward branch (often a loop) |
| `0x6ef370` | 140 | 2 | `shape only` | straight line / call sequence, 37 ins | straight line / call sequence |
| `0x6ef9a0` | 140 | 2 | `shape only` | straight line / call sequence, 37 ins | straight line / call sequence |
| `0x6f83f0` | 140 | 2 | `shape only` | has a backward branch (often a loop), 44 ins | has a backward branch (often a loop) |
| `0x1f8410` | 139 | 2 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x57b340` | 139 | 1 | `shape only` | straight line / call sequence, 39 ins | straight line / call sequence |
| `0x896560` | 139 | 4 | `shape only` | has a backward branch (often a loop), 45 ins | has a backward branch (often a loop) |
| `0x896dd0` | 139 | 3 | `shape only` | has a backward branch (often a loop), 45 ins | has a backward branch (often a loop) |
| `0x897530` | 139 | 2 | `shape only` | has a backward branch (often a loop), 45 ins | has a backward branch (often a loop) |
| `0x1e870` | 138 | 3 | `shape only` | straight line / call sequence, 37 ins | straight line / call sequence |
| `0x24c610` | 138 | 4 | `shape only` | straight line / call sequence, 39 ins | straight line / call sequence |
| `0x62fd90` | 138 | 18 | `shape only` | straight line / call sequence, 29 ins | straight line / call sequence |
| `0x889d00` | 138 | 9 | `shape only` | straight line / call sequence, 28 ins | straight line / call sequence |
| `0x60b090` | 137 | 1 | `shape only` | straight line / call sequence, 35 ins | straight line / call sequence |
| `0x6240d0` | 137 | 2 | `shape only` | has a backward branch (often a loop), 39 ins | has a backward branch (often a loop) |
| `0x8ae6a0` | 137 | 4 | `shape only` | has a backward branch (often a loop), 48 ins | has a backward branch (often a loop) |
| `0x8aee70` | 137 | 2 | `shape only` | has a backward branch (often a loop), 49 ins | has a backward branch (often a loop) |
| `0x8b9550` | 137 | 2 | `shape only` | has a backward branch (often a loop), 49 ins | has a backward branch (often a loop) |
| `0x8f5f40` | 137 | 5 | `shape only` | has a backward branch (often a loop), 51 ins | has a backward branch (often a loop) |
| `0x8f81b0` | 137 | 5 | `shape only` | has a backward branch (often a loop), 49 ins | has a backward branch (often a loop) |
| `0x8f8580` | 137 | 3 | `shape only` | has a backward branch (often a loop), 49 ins | has a backward branch (often a loop) |
| `0x9083b0` | 137 | 4 | `shape only` | has a backward branch (often a loop), 49 ins | has a backward branch (often a loop) |
| `0x4ba3e0` | 136 | 1 | `shape only` | straight line / call sequence, 38 ins | straight line / call sequence |
| `0x5e5dd0` | 136 | 2 | `shape only` | has a backward branch (often a loop), 35 ins | has a backward branch (often a loop) |
| `0x7befc0` | 136 | 8 | `shape only` | has a backward branch (often a loop), 44 ins | has a backward branch (often a loop) |
| `0x913540` | 136 | 24 | `shape only` | has a backward branch (often a loop), 45 ins | has a backward branch (often a loop) |
| `0x544e10` | 135 | 1 | `shape only` | straight line / call sequence, 44 ins | straight line / call sequence |
| `0x73d1c0` | 135 | 6 | `shape only` | has a backward branch (often a loop), 42 ins | has a backward branch (often a loop) |
| `0x99f470` | 135 | 2 | `shape only` | has a backward branch (often a loop), 46 ins | has a backward branch (often a loop) |
| `0x1c1220` | 134 | 15 | `shape only` | straight line / call sequence, 37 ins | straight line / call sequence |
| `0x7001c0` | 134 | 3 | `shape only` | has a backward branch (often a loop), 29 ins | has a backward branch (often a loop) |
| `0x8975c0` | 134 | 5 | `shape only` | has a backward branch (often a loop), 43 ins | has a backward branch (often a loop) |
| `0x6beb0` | 133 | 5 | `shape only` | straight line / call sequence, 34 ins | straight line / call sequence |
| `0x17fd90` | 133 | 13 | `shape only` | has a backward branch (often a loop), 51 ins | has a backward branch (often a loop) |
| `0x234840` | 133 | 3 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x6530a0` | 133 | 3 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x1f8350` | 132 | 9 | `shape only` | has a backward branch (often a loop), 33 ins | has a backward branch (often a loop) |
| `0x418920` | 132 | 13 | `shape only` | straight line / call sequence, 34 ins | straight line / call sequence |
| `0x63def0` | 132 | 2 | `strings` | ABCDEF \| abcdef | has a backward branch (often a loop) |
| `0x1994e0` | 131 | 32 | `shape only` | has a backward branch (often a loop), 25 ins | has a backward branch (often a loop) |
| `0x505850` | 131 | 2 | `shape only` | has a backward branch (often a loop), 42 ins | has a backward branch (often a loop) |
| `0x5066f0` | 131 | 2 | `shape only` | has a backward branch (often a loop), 42 ins | has a backward branch (often a loop) |
| `0x623e30` | 131 | 16 | `shape only` | has a backward branch (often a loop), 39 ins | has a backward branch (often a loop) |
| `0x8d2570` | 131 | 4 | `shape only` | has a backward branch (often a loop), 48 ins | has a backward branch (often a loop) |
| `0x8d36f0` | 131 | 5 | `shape only` | has a backward branch (often a loop), 50 ins | has a backward branch (often a loop) |
| `0x23dc0` | 130 | 1 | `shape only` | has a backward branch (often a loop), 43 ins | has a backward branch (often a loop) |
| `0x1f8860` | 130 | 2 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x6f0750` | 130 | 6 | `shape only` | straight line / call sequence, 36 ins | straight line / call sequence |
| `0x700250` | 130 | 5 | `shape only` | has a backward branch (often a loop), 29 ins | has a backward branch (often a loop) |
| `0x88f530` | 130 | 2 | `shape only` | has a backward branch (often a loop), 48 ins | has a backward branch (often a loop) |
| `0x8964d0` | 130 | 3 | `shape only` | has a backward branch (often a loop), 45 ins | has a backward branch (often a loop) |
| `0x89f7b0` | 130 | 6 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x8a0b60` | 130 | 1 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x992840` | 130 | 9 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x99bcd0` | 130 | 3 | `shape only` | has a backward branch (often a loop), 49 ins | has a backward branch (often a loop) |
| `0xaf510` | 129 | 4 | `shape only` | has a backward branch (often a loop), 33 ins | has a backward branch (often a loop) |
| `0x1c1110` | 129 | 2 | `shape only` | straight line / call sequence, 26 ins | straight line / call sequence |
| `0x5e6060` | 129 | 49 | `shape only` | straight line / call sequence, 33 ins | straight line / call sequence |
| `0x92efd0` | 129 | 3 | `shape only` | has a backward branch (often a loop), 37 ins | has a backward branch (often a loop) |
| `0x4b9cf0` | 128 | 1 | `shape only` | straight line / call sequence, 36 ins | straight line / call sequence |
| `0x4b9d70` | 128 | 3 | `shape only` | straight line / call sequence, 36 ins | straight line / call sequence |
| `0x653280` | 128 | 2 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x7003e0` | 128 | 2 | `shape only` | straight line / call sequence, 31 ins | straight line / call sequence |
| `0x1850c0` | 127 | 2 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x1a93d0` | 127 | 2 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x5231e0` | 127 | 4 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x523260` | 127 | 8 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x630d20` | 127 | 2 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x111b50` | 126 | 21 | `shape only` | straight line / call sequence, 32 ins | straight line / call sequence |
| `0x2f10d0` | 126 | 9 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x60bbb0` | 126 | 2 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x6247a0` | 126 | 2 | `shape only` | has a backward branch (often a loop), 44 ins | has a backward branch (often a loop) |
| `0x669cf0` | 126 | 3 | `shape only` | has a backward branch (often a loop), 42 ins | has a backward branch (often a loop) |
| `0x6ec060` | 126 | 8 | `shape only` | straight line / call sequence, 36 ins | straight line / call sequence |
| `0x6f0ac0` | 126 | 3 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x89ea40` | 126 | 2 | `shape only` | straight line / call sequence, 32 ins | straight line / call sequence |
| `0x8fd850` | 126 | 2 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x8fdaa0` | 126 | 2 | `shape only` | has a backward branch (often a loop), 47 ins | has a backward branch (often a loop) |
| `0x5d29c0` | 125 | 3 | `shape only` | has a backward branch (often a loop), 26 ins | has a backward branch (often a loop) |
| `0x6246c0` | 125 | 2 | `shape only` | has a backward branch (often a loop), 42 ins | has a backward branch (often a loop) |
| `0x6e9bb0` | 125 | 2 | `shape only` | straight line / call sequence, 37 ins | straight line / call sequence |
| `0x74b9b0` | 125 | 4 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x925150` | 125 | 11 | `shape only` | has a backward branch (often a loop), 43 ins | has a backward branch (often a loop) |
| `0x9424b0` | 125 | 6 | `shape only` | has a backward branch (often a loop), 43 ins | has a backward branch (often a loop) |
| `0x4dddd0` | 124 | 7 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x624050` | 124 | 2 | `shape only` | has a backward branch (often a loop), 43 ins | has a backward branch (often a loop) |
| `0x6e9e90` | 124 | 2 | `shape only` | straight line / call sequence, 35 ins | straight line / call sequence |
| `0x6ea240` | 124 | 2 | `shape only` | straight line / call sequence, 35 ins | straight line / call sequence |
| `0x824b40` | 124 | 31 | `shape only` | has a backward branch (often a loop), 35 ins | has a backward branch (often a loop) |
| `0x23f600` | 123 | 1 | `shape only` | straight line / call sequence, 32 ins | straight line / call sequence |
| `0x54e1f0` | 123 | 2 | `shape only` | straight line / call sequence, 44 ins | straight line / call sequence |
| `0x5ca6a0` | 123 | 3 | `shape only` | straight line / call sequence, 34 ins | straight line / call sequence |
| `0x65c4c0` | 123 | 2 | `shape only` | has a backward branch (often a loop), 31 ins | has a backward branch (often a loop) |
| `0x7602b0` | 123 | 15 | `shape only` | has a backward branch (often a loop), 42 ins | has a backward branch (often a loop) |
| `0x897ff0` | 123 | 3 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8981a0` | 123 | 1 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x898220` | 123 | 2 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x962be0` | 123 | 3 | `shape only` | has a backward branch (often a loop), 43 ins | has a backward branch (often a loop) |
| `0x962d80` | 123 | 3 | `shape only` | has a backward branch (often a loop), 43 ins | has a backward branch (often a loop) |
| `0x1a8e10` | 122 | 2 | `shape only` | straight line / call sequence, 34 ins | straight line / call sequence |
| `0x24c590` | 122 | 2 | `shape only` | straight line / call sequence, 36 ins | straight line / call sequence |
| `0x60ba50` | 122 | 2 | `shape only` | has a backward branch (often a loop), 37 ins | has a backward branch (often a loop) |
| `0x7db6e0` | 122 | 4 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x82a270` | 122 | 6 | `shape only` | has a backward branch (often a loop), 45 ins | has a backward branch (often a loop) |
| `0xf19e0` | 121 | 51 | `shape only` | has a backward branch (often a loop), 42 ins | has a backward branch (often a loop) |
| `0x468110` | 121 | 38 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x63f0c0` | 121 | 3 | `shape only` | has a backward branch (often a loop), 42 ins | has a backward branch (often a loop) |
| `0x6f86b0` | 121 | 3 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x999eb0` | 121 | 2 | `shape only` | has a backward branch (often a loop), 42 ins | has a backward branch (often a loop) |
| `0x24e370` | 120 | 1 | `shape only` | has a backward branch (often a loop), 42 ins | has a backward branch (often a loop) |
| `0x262900` | 120 | 1 | `shape only` | has a backward branch (often a loop), 40 ins | has a backward branch (often a loop) |
| `0x5465e0` | 120 | 1 | `shape only` | straight line / call sequence, 37 ins | straight line / call sequence |
| `0x5d8a70` | 120 | 2 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x67f170` | 120 | 2 | `shape only` | has a backward branch (often a loop), 36 ins | has a backward branch (often a loop) |
| `0x8ba380` | 120 | 3 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x8ea1b0` | 120 | 4 | `shape only` | has a backward branch (often a loop), 40 ins | has a backward branch (often a loop) |
| `0x8fd160` | 120 | 2 | `shape only` | has a backward branch (often a loop), 45 ins | has a backward branch (often a loop) |
| `0xaea70` | 119 | 3 | `shape only` | has a backward branch (often a loop), 35 ins | has a backward branch (often a loop) |
| `0xf1aa0` | 119 | 56 | `shape only` | has a backward branch (often a loop), 43 ins | has a backward branch (often a loop) |
| `0x624160` | 119 | 9 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x630ef0` | 119 | 4 | `shape only` | has a backward branch (often a loop), 26 ins | has a backward branch (often a loop) |
| `0x7c39f0` | 119 | 2 | `shape only` | has a backward branch (often a loop), 37 ins | has a backward branch (often a loop) |
| `0xd1750` | 118 | 13 | `shape only` | straight line / call sequence, 34 ins | straight line / call sequence |
| `0x179710` | 118 | 13 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x207930` | 118 | 1 | `shape only` | has a backward branch (often a loop), 35 ins | has a backward branch (often a loop) |
| `0x4f79d0` | 118 | 1 | `shape only` | straight line / call sequence, 36 ins | straight line / call sequence |
| `0x52c4c0` | 118 | 1 | `shape only` | straight line / call sequence, 33 ins | straight line / call sequence |
| `0x52c540` | 118 | 1 | `shape only` | straight line / call sequence, 33 ins | straight line / call sequence |
| `0x6dd680` | 118 | 7 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x6dd700` | 118 | 2 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x6dd780` | 118 | 5 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x6dd800` | 118 | 4 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x8890e0` | 118 | 2 | `shape only` | straight line / call sequence, 32 ins | straight line / call sequence |
| `0x4f72b0` | 117 | 3 | `shape only` | straight line / call sequence, 32 ins | straight line / call sequence |
| `0x704260` | 117 | 7 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x746b90` | 117 | 2 | `shape only` | has a backward branch (often a loop), 36 ins | has a backward branch (often a loop) |
| `0x2abd0` | 116 | 5 | `shape only` | straight line / call sequence, 29 ins | straight line / call sequence |
| `0x1a1780` | 116 | 3 | `shape only` | has a backward branch (often a loop), 30 ins | has a backward branch (often a loop) |
| `0x4dda10` | 116 | 23 | `shape only` | straight line / call sequence, 23 ins | straight line / call sequence |
| `0x5c3e80` | 116 | 1 | `shape only` | straight line / call sequence, 28 ins | straight line / call sequence |
| `0x60c9b0` | 116 | 2 | `shape only` | has a backward branch (often a loop), 42 ins | has a backward branch (often a loop) |
| `0x97a7b0` | 116 | 11 | `shape only` | straight line / call sequence, 30 ins | straight line / call sequence |
| `0x5c5f70` | 115 | 2 | `shape only` | has a backward branch (often a loop), 43 ins | has a backward branch (often a loop) |
| `0x86e940` | 115 | 5 | `shape only` | has a backward branch (often a loop), 37 ins | has a backward branch (often a loop) |
| `0xef140` | 114 | 5 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0xef280` | 114 | 18 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0xf51b0` | 114 | 15 | `shape only` | straight line / call sequence, 31 ins | straight line / call sequence |
| `0x137f60` | 114 | 6 | `shape only` | has a backward branch (often a loop), 41 ins | has a backward branch (often a loop) |
| `0x1a9350` | 114 | 15 | `shape only` | straight line / call sequence, 26 ins | straight line / call sequence |
| `0x1c1660` | 114 | 1 | `shape only` | has a backward branch (often a loop), 28 ins | has a backward branch (often a loop) |
| `0x4bad90` | 114 | 1 | `shape only` | straight line / call sequence, 26 ins | straight line / call sequence |
| `0x5051a0` | 114 | 2 | `shape only` | straight line / call sequence, 36 ins | straight line / call sequence |
| `0x522920` | 114 | 4 | `shape only` | has a backward branch (often a loop), 37 ins | has a backward branch (often a loop) |
| `0x5c8a10` | 114 | 16 | `shape only` | straight line / call sequence, 31 ins | straight line / call sequence |
| `0x5cda70` | 114 | 1 | `shape only` | has a backward branch (often a loop), 35 ins | has a backward branch (often a loop) |
| `0x5e5bf0` | 114 | 3 | `shape only` | has a backward branch (often a loop), 27 ins | has a backward branch (often a loop) |
| `0xf12c0` | 113 | 65 | `strings` | UWVSH | has a backward branch (often a loop) |
| `0x67d990` | 113 | 2 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x6cc950` | 113 | 1 | `shape only` | straight line / call sequence, 37 ins | straight line / call sequence |
| `0x42f30` | 112 | 1 | `shape only` | straight line / call sequence, 33 ins | straight line / call sequence |
| `0x22da00` | 112 | 5 | `shape only` | has a backward branch (often a loop), 40 ins | has a backward branch (often a loop) |
| `0x4188a0` | 112 | 2 | `shape only` | straight line / call sequence, 41 ins | straight line / call sequence |
| `0x51bd10` | 112 | 4 | `callers` | called by 0x104d0 WaitComputationTermination; 0x10650 WaitNextSolution | has a backward branch (often a loop) |
| `0x597b50` | 112 | 3 | `shape only` | has a backward branch (often a loop), 37 ins | has a backward branch (often a loop) |
| `0x5e6200` | 112 | 4 | `shape only` | has a backward branch (often a loop), 29 ins | has a backward branch (often a loop) |
| `0x5f47c0` | 112 | 2 | `shape only` | straight line / call sequence, 29 ins | straight line / call sequence |
| `0x72b6f0` | 112 | 4 | `shape only` | has a backward branch (often a loop), 24 ins | has a backward branch (often a loop) |
| `0x89a440` | 112 | 1 | `shape only` | has a backward branch (often a loop), 39 ins | has a backward branch (often a loop) |
| `0x9878c0` | 112 | 67 | `shape only` | has a backward branch (often a loop), 34 ins | has a backward branch (often a loop) |
| `0xef300` | 111 | 15 | `shape only` | has a backward branch (often a loop), 40 ins | has a backward branch (often a loop) |
| `0x5e60f0` | 111 | 2 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x5fef30` | 111 | 20 | `shape only` | straight line / call sequence, 34 ins | straight line / call sequence |
| `0x6dde50` | 111 | 5 | `shape only` | has a backward branch (often a loop), 39 ins | has a backward branch (often a loop) |
| `0x6fc3b0` | 111 | 7 | `shape only` | has a backward branch (often a loop), 34 ins | has a backward branch (often a loop) |
| `0x81f210` | 111 | 6 | `strings` | %s: __pos (which is %zu) > this->size()  \| basic_string::copy | straight line / call sequence |
| `0x82ad80` | 111 | 3 | `strings` | %s: __pos (which is %zu) > this->size()  \| basic_string::copy | straight line / call sequence |
| `0x86a370` | 111 | 7 | `shape only` | has a backward branch (often a loop), 34 ins | has a backward branch (often a loop) |
| `0x553090` | 110 | 2 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x6d5980` | 110 | 12 | `strings` | basic_string::substr \| %s: __pos (which is %zu) > this->size()  | straight line / call sequence |
| `0x6ea140` | 110 | 2 | `shape only` | straight line / call sequence, 32 ins | straight line / call sequence |
| `0x302b50` | 109 | 32 | `shape only` | has a backward branch (often a loop), 29 ins | has a backward branch (often a loop) |
| `0x4f4270` | 109 | 1 | `shape only` | straight line / call sequence, 36 ins | straight line / call sequence |
| `0x525760` | 109 | 3 | `shape only` | straight line / call sequence, 23 ins | straight line / call sequence |
| `0x8bc8c0` | 109 | 1 | `shape only` | has a backward branch (often a loop), 35 ins | has a backward branch (often a loop) |
| `0x137410` | 108 | 7 | `shape only` | straight line / call sequence, 32 ins | straight line / call sequence |
| `0x16c0d0` | 108 | 11 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x4189b0` | 108 | 58 | `shape only` | has a backward branch (often a loop), 42 ins | has a backward branch (often a loop) |
| `0x4f1dc0` | 108 | 1 | `shape only` | straight line / call sequence, 34 ins | straight line / call sequence |
| `0x5fcc50` | 108 | 6 | `shape only` | has a backward branch (often a loop), 34 ins | has a backward branch (often a loop) |
| `0x653300` | 108 | 2 | `shape only` | has a backward branch (often a loop), 35 ins | has a backward branch (often a loop) |
| `0x6de010` | 108 | 6 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x6e99f0` | 108 | 2 | `shape only` | straight line / call sequence, 28 ins | straight line / call sequence |
| `0x6e9ad0` | 108 | 1 | `shape only` | straight line / call sequence, 28 ins | straight line / call sequence |
| `0x6e9b40` | 108 | 2 | `shape only` | straight line / call sequence, 28 ins | straight line / call sequence |
| `0x8200f0` | 108 | 12 | `strings` | %s: __pos (which is %zu) > this->size()  \| basic_string::copy | straight line / call sequence |
| `0x9007b0` | 108 | 7 | `shape only` | straight line / call sequence, 35 ins | straight line / call sequence |
| `0x240290` | 107 | 4 | `shape only` | has a backward branch (often a loop), 36 ins | has a backward branch (often a loop) |
| `0x4dac00` | 107 | 2 | `shape only` | straight line / call sequence, 39 ins | straight line / call sequence |
| `0x5053c0` | 107 | 2 | `strings` | extra_infos | straight line / call sequence |
| `0x525300` | 107 | 3 | `shape only` | has a backward branch (often a loop), 34 ins | has a backward branch (often a loop) |
| `0x545220` | 107 | 2 | `shape only` | straight line / call sequence, 29 ins | straight line / call sequence |
| `0x57a610` | 107 | 5 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x5b3670` | 107 | 1 | `shape only` | has a backward branch (often a loop), 26 ins | has a backward branch (often a loop) |
| `0x60bb40` | 107 | 2 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x687890` | 107 | 1 | `shape only` | straight line / call sequence, 28 ins | straight line / call sequence |
| `0x6ddec0` | 107 | 3 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x6ddf30` | 107 | 1 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x6ddfa0` | 107 | 2 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x6de160` | 107 | 4 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x6de1d0` | 107 | 4 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x87d4e0` | 107 | 2 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x12def0` | 106 | 3 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x20c0c0` | 106 | 3 | `shape only` | straight line / call sequence, 30 ins | straight line / call sequence |
| `0x5436c0` | 106 | 2 | `shape only` | has a backward branch (often a loop), 29 ins | has a backward branch (often a loop) |
| `0x5c4d60` | 106 | 3 | `shape only` | has a backward branch (often a loop), 26 ins | has a backward branch (often a loop) |
| `0x627040` | 106 | 2 | `shape only` | has a backward branch (often a loop), 33 ins | has a backward branch (often a loop) |
| `0x6de080` | 106 | 3 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x6de0f0` | 106 | 3 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x6f8ec0` | 106 | 4 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x900d40` | 106 | 18 | `shape only` | has a backward branch (often a loop), 35 ins | has a backward branch (often a loop) |
| `0x522f70` | 105 | 1 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x5d9350` | 105 | 1 | `shape only` | straight line / call sequence, 25 ins | straight line / call sequence |
| `0x624280` | 105 | 4 | `shape only` | has a backward branch (often a loop), 35 ins | has a backward branch (often a loop) |
| `0x1e0d0` | 104 | 2 | `shape only` | has a backward branch (often a loop), 28 ins | has a backward branch (often a loop) |
| `0xaa9d0` | 104 | 1 | `shape only` | has a backward branch (often a loop), 40 ins | has a backward branch (often a loop) |
| `0x1c8300` | 104 | 12 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x687480` | 104 | 25 | `shape only` | has a backward branch (often a loop), 36 ins | has a backward branch (often a loop) |
| `0x6dd5a0` | 104 | 3 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x6dd610` | 104 | 2 | `shape only` | has a backward branch (often a loop), 38 ins | has a backward branch (often a loop) |
| `0x7bbec0` | 104 | 3 | `shape only` | has a backward branch (often a loop), 36 ins | has a backward branch (often a loop) |
| `0x829fe0` | 104 | 6 | `strings` | %s: __pos (which is %zu) > this->size()  \| basic_string::copy | straight line / call sequence |
| `0x8f17b0` | 104 | 27 | `shape only` | has a backward branch (often a loop), 29 ins | has a backward branch (often a loop) |
| `0x309c0` | 103 | 4 | `shape only` | straight line / call sequence, 31 ins | straight line / call sequence |
| `0x12df60` | 103 | 3 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x16c030` | 103 | 2 | `shape only` | straight line / call sequence, 32 ins | straight line / call sequence |
| `0x4f4770` | 103 | 1 | `shape only` | straight line / call sequence, 33 ins | straight line / call sequence |
| `0x580fe0` | 103 | 5 | `shape only` | has a backward branch (often a loop), 43 ins | has a backward branch (often a loop) |
| `0x6d2aa0` | 103 | 8 | `shape only` | straight line / call sequence, 30 ins | straight line / call sequence |
| `0x6f4ca0` | 103 | 10 | `strings` | pqcs \| p`\ | has a backward branch (often a loop) |
| `0x70c480` | 103 | 1 | `shape only` | straight line / call sequence, 25 ins | straight line / call sequence |
| `0x3713e0` | 102 | 7 | `shape only` | straight line / call sequence, 17 ins | straight line / call sequence |
| `0x570e70` | 102 | 1 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x5b39d0` | 102 | 4 | `shape only` | has a backward branch (often a loop), 36 ins | has a backward branch (often a loop) |
| `0x60bec0` | 102 | 1 | `shape only` | has a backward branch (often a loop), 27 ins | has a backward branch (often a loop) |
| `0x669df0` | 102 | 3 | `shape only` | straight line / call sequence, 29 ins | straight line / call sequence |
| `0x870000` | 102 | 3 | `shape only` | straight line / call sequence, 29 ins | straight line / call sequence |
| `0x89de90` | 102 | 2 | `shape only` | has a backward branch (often a loop), 31 ins | has a backward branch (often a loop) |
| `0x89df00` | 102 | 4 | `shape only` | has a backward branch (often a loop), 31 ins | has a backward branch (often a loop) |
| `0x1be400` | 101 | 4 | `shape only` | has a backward branch (often a loop), 28 ins | has a backward branch (often a loop) |
| `0x24b790` | 101 | 1 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x4ddf30` | 101 | 3 | `shape only` | has a backward branch (often a loop), 28 ins | has a backward branch (often a loop) |
| `0x8771c0` | 101 | 3 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x24dcd0` | 100 | 1 | `shape only` | has a backward branch (often a loop), 31 ins | has a backward branch (often a loop) |
| `0x4d8d40` | 100 | 1 | `shape only` | straight line / call sequence, 30 ins | straight line / call sequence |
| `0x8682a0` | 100 | 13 | `shape only` | straight line / call sequence, 35 ins | straight line / call sequence |
| `0x10f220` | 99 | 21 | `shape only` | straight line / call sequence, 30 ins | straight line / call sequence |
| `0x2a9610` | 99 | 6 | `strings` |  \|vk | straight line / call sequence |
| `0xf0e90` | 98 | 146 | `strings` | UWVSH | has a backward branch (often a loop) |
| `0x159480` | 98 | 4 | `shape only` | straight line / call sequence, 32 ins | straight line / call sequence |
| `0x5e7350` | 98 | 3 | `shape only` | has a backward branch (often a loop), 28 ins | has a backward branch (often a loop) |
| `0x60bad0` | 98 | 2 | `shape only` | has a backward branch (often a loop), 29 ins | has a backward branch (often a loop) |
| `0x61ef80` | 98 | 2 | `shape only` | has a backward branch (often a loop), 21 ins | has a backward branch (often a loop) |
| `0x1a5000` | 97 | 4 | `shape only` | has a backward branch (often a loop), 39 ins | has a backward branch (often a loop) |
| `0x203d40` | 97 | 10 | `shape only` | has a backward branch (often a loop), 35 ins | has a backward branch (often a loop) |
| `0x5185f0` | 97 | 3 | `shape only` | straight line / call sequence, 17 ins | straight line / call sequence |
| `0x527ab0` | 97 | 1 | `shape only` | has a backward branch (often a loop), 30 ins | has a backward branch (often a loop) |
| `0x626fd0` | 97 | 2 | `shape only` | has a backward branch (often a loop), 35 ins | has a backward branch (often a loop) |
| `0x6de240` | 97 | 7 | `shape only` | has a backward branch (often a loop), 37 ins | has a backward branch (often a loop) |
| `0x3c390` | 96 | 2 | `shape only` | has a backward branch (often a loop), 31 ins | has a backward branch (often a loop) |
| `0x1784f0` | 96 | 2 | `shape only` | has a backward branch (often a loop), 30 ins | has a backward branch (often a loop) |
| `0x5ca7e0` | 96 | 6 | `shape only` | straight line / call sequence, 30 ins | straight line / call sequence |
| `0x630f70` | 96 | 2 | `strings` | alnum | has a backward branch (often a loop) |
| `0x868380` | 96 | 13 | `shape only` | straight line / call sequence, 33 ins | straight line / call sequence |
| `0x9983e0` | 96 | 1 | `shape only` | straight line / call sequence, 23 ins | straight line / call sequence |
| `0x505140` | 95 | 1 | `shape only` | straight line / call sequence, 32 ins | straight line / call sequence |
| `0x5240b0` | 95 | 3 | `shape only` | has a backward branch (often a loop), 36 ins | has a backward branch (often a loop) |
| `0x547140` | 95 | 1 | `shape only` | straight line / call sequence, 29 ins | straight line / call sequence |
| `0x9109e0` | 95 | 25 | `shape only` | has a backward branch (often a loop), 33 ins | has a backward branch (often a loop) |
| `0x4ba470` | 94 | 1 | `shape only` | straight line / call sequence, 20 ins | straight line / call sequence |
| `0x624430` | 94 | 2 | `shape only` | has a backward branch (often a loop), 31 ins | has a backward branch (often a loop) |
| `0x82a860` | 94 | 6 | `shape only` | has a backward branch (often a loop), 28 ins | has a backward branch (often a loop) |
| `0x92c7b0` | 94 | 13 | `shape only` | has a backward branch (often a loop), 29 ins | has a backward branch (often a loop) |
| `0x5050e0` | 93 | 1 | `shape only` | straight line / call sequence, 32 ins | straight line / call sequence |
| `0x5c6170` | 93 | 2 | `shape only` | has a backward branch (often a loop), 40 ins | has a backward branch (often a loop) |
| `0x60b200` | 93 | 1 | `shape only` | straight line / call sequence, 28 ins | straight line / call sequence |
| `0x60ca30` | 93 | 1 | `shape only` | straight line / call sequence, 25 ins | straight line / call sequence |
| `0x653130` | 93 | 2 | `shape only` | straight line / call sequence, 32 ins | straight line / call sequence |
| `0x6f8e60` | 93 | 23 | `shape only` | has a backward branch (often a loop), 29 ins | has a backward branch (often a loop) |
| `0x873a50` | 93 | 3 | `shape only` | has a backward branch (often a loop), 35 ins | has a backward branch (often a loop) |
| `0x1b4a0` | 92 | 2 | `shape only` | has a backward branch (often a loop), 24 ins | has a backward branch (often a loop) |
| `0x1b500` | 92 | 2 | `shape only` | has a backward branch (often a loop), 24 ins | has a backward branch (often a loop) |
| `0x4dc330` | 92 | 9 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x4f5090` | 92 | 2 | `shape only` | straight line / call sequence, 31 ins | straight line / call sequence |
| `0x634be0` | 92 | 70 | `shape only` | straight line / call sequence, 33 ins | straight line / call sequence |
| `0x66d9d0` | 92 | 1 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x8d1920` | 92 | 2 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8da660` | 92 | 2 | `shape only` | has a backward branch (often a loop), 31 ins | has a backward branch (often a loop) |
| `0x5cc0d0` | 91 | 2 | `shape only` | straight line / call sequence, 28 ins | straight line / call sequence |
| `0x5d19d0` | 91 | 2 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x65c090` | 91 | 9 | `shape only` | has a backward branch (often a loop), 31 ins | has a backward branch (often a loop) |
| `0x6ec810` | 91 | 19 | `shape only` | has a backward branch (often a loop), 30 ins | has a backward branch (often a loop) |
| `0x89ec90` | 91 | 2 | `shape only` | has a backward branch (often a loop), 27 ins | has a backward branch (often a loop) |
| `0x8a81c0` | 91 | 3 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x1a8db0` | 90 | 6 | `shape only` | straight line / call sequence, 30 ins | straight line / call sequence |
| `0x20c130` | 90 | 8 | `shape only` | straight line / call sequence, 30 ins | straight line / call sequence |
| `0x239a10` | 90 | 3 | `shape only` | straight line / call sequence, 30 ins | straight line / call sequence |
| `0x2aa450` | 90 | 9 | `shape only` | has a backward branch (often a loop), 31 ins | has a backward branch (often a loop) |
| `0x4f9e80` | 90 | 4 | `shape only` | has a backward branch (often a loop), 30 ins | has a backward branch (often a loop) |
| `0x5b9d20` | 90 | 3 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x5e82e0` | 90 | 5 | `shape only` | has a backward branch (often a loop), 29 ins | has a backward branch (often a loop) |
| `0x5e8510` | 90 | 8 | `shape only` | has a backward branch (often a loop), 29 ins | has a backward branch (often a loop) |
| `0x5e8690` | 90 | 6 | `shape only` | has a backward branch (often a loop), 29 ins | has a backward branch (often a loop) |
| `0x6dedc0` | 90 | 3 | `shape only` | straight line / call sequence, 28 ins | straight line / call sequence |
| `0x82a450` | 90 | 20 | `shape only` | has a backward branch (often a loop), 30 ins | has a backward branch (often a loop) |
| `0x4fc010` | 89 | 3 | `shape only` | straight line / call sequence, 18 ins | straight line / call sequence |
| `0x5a4550` | 89 | 2 | `shape only` | straight line / call sequence, 29 ins | straight line / call sequence |
| `0x6019e0` | 89 | 3 | `shape only` | straight line / call sequence, 16 ins | straight line / call sequence |
| `0x623ff0` | 89 | 2 | `shape only` | has a backward branch (often a loop), 25 ins | has a backward branch (often a loop) |
| `0x65c940` | 89 | 3 | `shape only` | has a backward branch (often a loop), 36 ins | has a backward branch (often a loop) |
| `0x8d0cd0` | 89 | 2 | `shape only` | has a backward branch (often a loop), 31 ins | has a backward branch (often a loop) |
| `0x8d11c0` | 89 | 2 | `shape only` | has a backward branch (often a loop), 31 ins | has a backward branch (often a loop) |
| `0x8d16b0` | 89 | 2 | `shape only` | has a backward branch (often a loop), 31 ins | has a backward branch (often a loop) |
| `0x8d1f80` | 89 | 2 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8f2ca0` | 89 | 51 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x9041f0` | 89 | 3 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x225a10` | 88 | 1 | `shape only` | straight line / call sequence, 28 ins | straight line / call sequence |
| `0x2aa000` | 88 | 5 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x8b1dd0` | 88 | 2 | `shape only` | has a backward branch (often a loop), 30 ins | has a backward branch (often a loop) |
| `0x8b6300` | 88 | 3 | `shape only` | has a backward branch (often a loop), 31 ins | has a backward branch (often a loop) |
| `0x8b9350` | 88 | 6 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8bacc0` | 88 | 2 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8c2320` | 88 | 17 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8cbb10` | 88 | 16 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8d00c0` | 88 | 2 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8d97d0` | 88 | 6 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8e6d70` | 88 | 2 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8e7760` | 88 | 8 | `shape only` | has a backward branch (often a loop), 30 ins | has a backward branch (often a loop) |
| `0x8e7eb0` | 88 | 1 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8f69f0` | 88 | 1 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8f73e0` | 88 | 2 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8f7dd0` | 88 | 22 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8fbd60` | 88 | 4 | `shape only` | has a backward branch (often a loop), 33 ins | has a backward branch (often a loop) |
| `0x8fc350` | 88 | 1 | `shape only` | has a backward branch (often a loop), 33 ins | has a backward branch (often a loop) |
| `0x8fcf20` | 88 | 1 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8fdf40` | 88 | 3 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8fe3c0` | 88 | 8 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8fe5e0` | 88 | 3 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8fe800` | 88 | 3 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8febe0` | 88 | 2 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8fee00` | 88 | 5 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x8ff240` | 88 | 5 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x906950` | 88 | 2 | `shape only` | has a backward branch (often a loop), 33 ins | has a backward branch (often a loop) |
| `0x906b00` | 88 | 3 | `shape only` | has a backward branch (often a loop), 33 ins | has a backward branch (often a loop) |
| `0x907150` | 88 | 2 | `shape only` | has a backward branch (often a loop), 32 ins | has a backward branch (often a loop) |
| `0x156610` | 87 | 2 | `shape only` | straight line / call sequence, 30 ins | straight line / call sequence |
| `0x1a29a0` | 87 | 1 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x5d8eb0` | 87 | 1 | `shape only` | has a backward branch (often a loop), 26 ins | has a backward branch (often a loop) |
| `0x6399e0` | 87 | 11 | `shape only` | straight line / call sequence, 29 ins | straight line / call sequence |
| `0x1a2940` | 86 | 6 | `shape only` | has a backward branch (often a loop), 28 ins | has a backward branch (often a loop) |
| `0x1c25c0` | 86 | 4 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x261e00` | 86 | 2 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x465de0` | 86 | 46 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x4f9f40` | 86 | 2 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x634b20` | 86 | 4 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x65cac0` | 86 | 3 | `shape only` | straight line / call sequence, 26 ins | straight line / call sequence |
| `0x65deb0` | 86 | 3 | `shape only` | straight line / call sequence, 25 ins | straight line / call sequence |
| `0x874430` | 86 | 3 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x9916e0` | 86 | 49 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x9917a0` | 86 | 3 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x991800` | 86 | 5 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x991920` | 86 | 1 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x9919e0` | 86 | 1 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x5cac70` | 85 | 5 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x62eed0` | 85 | 2 | `shape only` | straight line / call sequence, 19 ins | straight line / call sequence |
| `0x2a940` | 84 | 2 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x3b590` | 84 | 1 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x1c10b0` | 84 | 2 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x5fcef0` | 84 | 1 | `shape only` | has a backward branch (often a loop), 28 ins | has a backward branch (often a loop) |
| `0x8aabf0` | 84 | 35 | `shape only` | straight line / call sequence, 26 ins | straight line / call sequence |
| `0x9437a0` | 84 | 5 | `shape only` | has a backward branch (often a loop), 31 ins | has a backward branch (often a loop) |
| `0x999af0` | 84 | 2 | `shape only` | has a backward branch (often a loop), 26 ins | has a backward branch (often a loop) |
| `0x5b1f0` | 83 | 1 | `shape only` | straight line / call sequence, 23 ins | straight line / call sequence |
| `0x4f77d0` | 83 | 5 | `shape only` | has a backward branch (often a loop), 22 ins | has a backward branch (often a loop) |
| `0x580f80` | 83 | 4 | `shape only` | has a backward branch (often a loop), 30 ins | has a backward branch (often a loop) |
| `0x9a0040` | 83 | 6 | `shape only` | has a backward branch (often a loop), 21 ins | has a backward branch (often a loop) |
| `0x2b3990` | 82 | 8 | `shape only` | straight line / call sequence, 15 ins | straight line / call sequence |
| `0x82a970` | 82 | 6 | `shape only` | has a backward branch (often a loop), 26 ins | has a backward branch (often a loop) |
| `0x991f20` | 82 | 3 | `shape only` | has a backward branch (often a loop), 30 ins | has a backward branch (often a loop) |
| `0x15e3b0` | 81 | 2 | `shape only` | straight line / call sequence, 17 ins | straight line / call sequence |
| `0x16c140` | 81 | 9 | `shape only` | straight line / call sequence, 21 ins | straight line / call sequence |
| `0x16c1a0` | 81 | 5 | `shape only` | straight line / call sequence, 21 ins | straight line / call sequence |
| `0x624740` | 81 | 3 | `shape only` | has a backward branch (often a loop), 27 ins | has a backward branch (often a loop) |
| `0x7b10c0` | 81 | 5 | `shape only` | straight line / call sequence, 25 ins | straight line / call sequence |
| `0x875240` | 81 | 1 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x875ab0` | 81 | 1 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x990540` | 81 | 1 | `shape only` | straight line / call sequence, 23 ins | straight line / call sequence |
| `0x990600` | 81 | 3 | `shape only` | straight line / call sequence, 23 ins | straight line / call sequence |
| `0x990780` | 81 | 1 | `shape only` | straight line / call sequence, 23 ins | straight line / call sequence |
| `0x990840` | 81 | 1 | `shape only` | straight line / call sequence, 23 ins | straight line / call sequence |
| `0x1b170` | 80 | 2 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x45490` | 80 | 4 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x454e0` | 80 | 2 | `shape only` | straight line / call sequence, 26 ins | straight line / call sequence |
| `0x1d1090` | 80 | 3 | `shape only` | has a backward branch (often a loop), 25 ins | has a backward branch (often a loop) |
| `0x21f9f0` | 80 | 3 | `shape only` | straight line / call sequence, 19 ins | straight line / call sequence |
| `0x4fc140` | 80 | 5 | `shape only` | straight line / call sequence, 16 ins | straight line / call sequence |
| `0x5fcea0` | 80 | 20 | `shape only` | has a backward branch (often a loop), 25 ins | has a backward branch (often a loop) |
| `0x62ff40` | 80 | 1 | `shape only` | straight line / call sequence, 18 ins | straight line / call sequence |
| `0x7b1f20` | 80 | 26 | `shape only` | straight line / call sequence, 26 ins | straight line / call sequence |
| `0x875fd0` | 80 | 11 | `shape only` | straight line / call sequence, 25 ins | straight line / call sequence |
| `0x877160` | 80 | 2 | `shape only` | has a backward branch (often a loop), 26 ins | has a backward branch (often a loop) |
| `0x889070` | 80 | 37 | `shape only` | straight line / call sequence, 25 ins | straight line / call sequence |
| `0x9227c0` | 80 | 7 | `shape only` | straight line / call sequence, 25 ins | straight line / call sequence |
| `0x9228d0` | 80 | 10 | `shape only` | straight line / call sequence, 25 ins | straight line / call sequence |
| `0x990de0` | 80 | 3 | `shape only` | straight line / call sequence, 23 ins | straight line / call sequence |
| `0x1a9300` | 79 | 2 | `strings` | TOTAL CURRENT =  | straight line / call sequence |
| `0x20b2d0` | 79 | 1 | `shape only` | straight line / call sequence, 20 ins | straight line / call sequence |
| `0x523580` | 79 | 3 | `shape only` | has a backward branch (often a loop), 30 ins | has a backward branch (often a loop) |
| `0x60b720` | 79 | 2 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x624230` | 79 | 6 | `shape only` | has a backward branch (often a loop), 28 ins | has a backward branch (often a loop) |
| `0x684670` | 79 | 1 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x6859a0` | 79 | 1 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x943840` | 79 | 3 | `shape only` | has a backward branch (often a loop), 27 ins | has a backward branch (often a loop) |
| `0x4b81d0` | 78 | 4 | `shape only` | straight line / call sequence, 18 ins | straight line / call sequence |
| `0x5451d0` | 78 | 5 | `shape only` | has a backward branch (often a loop), 23 ins | has a backward branch (often a loop) |
| `0x5ed870` | 78 | 2 | `shape only` | straight line / call sequence, 16 ins | straight line / call sequence |
| `0x6d7200` | 78 | 2 | `shape only` | straight line / call sequence, 31 ins | straight line / call sequence |
| `0x6241e0` | 77 | 2 | `shape only` | straight line / call sequence, 26 ins | straight line / call sequence |
| `0x7b2fc0` | 77 | 5 | `shape only` | has a backward branch (often a loop), 27 ins | has a backward branch (often a loop) |
| `0x8286f0` | 77 | 2 | `shape only` | straight line / call sequence, 21 ins | straight line / call sequence |
| `0x9920c0` | 77 | 42 | `shape only` | straight line / call sequence, 28 ins | straight line / call sequence |
| `0x24900` | 76 | 2 | `strings` | `HNk | has a backward branch (often a loop) |
| `0x24950` | 76 | 2 | `shape only` | has a backward branch (often a loop), 25 ins | has a backward branch (often a loop) |
| `0x510a40` | 76 | 1 | `shape only` | straight line / call sequence, 25 ins | straight line / call sequence |
| `0x6f8e10` | 76 | 3 | `strings` | mutex \| p`\ | has a backward branch (often a loop) |
| `0x7043b0` | 76 | 6 | `shape only` | straight line / call sequence, 17 ins | straight line / call sequence |
| `0x8a00c0` | 76 | 1 | `shape only` | has a backward branch (often a loop), 22 ins | has a backward branch (often a loop) |
| `0x8a0540` | 76 | 4 | `shape only` | has a backward branch (often a loop), 22 ins | has a backward branch (often a loop) |
| `0x944160` | 76 | 2 | `shape only` | straight line / call sequence, 20 ins | straight line / call sequence |
| `0x524e10` | 75 | 3 | `shape only` | has a backward branch (often a loop), 27 ins | has a backward branch (often a loop) |
| `0x553100` | 75 | 1 | `shape only` | straight line / call sequence, 17 ins | straight line / call sequence |
| `0x5a6530` | 75 | 2 | `shape only` | has a backward branch (often a loop), 27 ins | has a backward branch (often a loop) |
| `0x72b6a0` | 75 | 18 | `shape only` | has a backward branch (often a loop), 25 ins | has a backward branch (often a loop) |
| `0x873d40` | 75 | 3 | `shape only` | has a backward branch (often a loop), 29 ins | has a backward branch (often a loop) |
| `0x8740a0` | 75 | 2 | `shape only` | has a backward branch (often a loop), 29 ins | has a backward branch (often a loop) |
| `0x8743a0` | 75 | 1 | `shape only` | has a backward branch (often a loop), 29 ins | has a backward branch (often a loop) |
| `0x924f80` | 75 | 10 | `shape only` | has a backward branch (often a loop), 26 ins | has a backward branch (often a loop) |
| `0x97aba0` | 75 | 5 | `shape only` | straight line / call sequence, 20 ins | straight line / call sequence |
| `0x983c50` | 75 | 3 | `shape only` | straight line / call sequence, 20 ins | straight line / call sequence |
| `0xb5d10` | 74 | 1 | `shape only` | straight line / call sequence, 19 ins | straight line / call sequence |
| `0xf2000` | 74 | 66 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x111a50` | 74 | 19 | `shape only` | has a backward branch (often a loop), 20 ins | has a backward branch (often a loop) |
| `0x5afb80` | 73 | 3 | `shape only` | straight line / call sequence, 19 ins | straight line / call sequence |
| `0x5c6120` | 73 | 4 | `shape only` | has a backward branch (often a loop), 27 ins | has a backward branch (often a loop) |
| `0x5f3bd0` | 73 | 16 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x2252d0` | 72 | 1 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x543670` | 72 | 2 | `shape only` | has a backward branch (often a loop), 22 ins | has a backward branch (often a loop) |
| `0x60c110` | 72 | 2 | `strings` | [unknown module] \| [unknown function] | has a backward branch (often a loop) |
| `0x86f440` | 72 | 11 | `shape only` | straight line / call sequence, 23 ins | straight line / call sequence |
| `0x86f7c0` | 72 | 11 | `shape only` | straight line / call sequence, 23 ins | straight line / call sequence |
| `0x86fb70` | 72 | 11 | `shape only` | straight line / call sequence, 23 ins | straight line / call sequence |
| `0x86ff20` | 72 | 11 | `shape only` | straight line / call sequence, 23 ins | straight line / call sequence |
| `0x925470` | 72 | 4 | `shape only` | has a backward branch (often a loop), 26 ins | has a backward branch (often a loop) |
| `0x925a60` | 72 | 6 | `shape only` | has a backward branch (often a loop), 26 ins | has a backward branch (often a loop) |
| `0x93caf0` | 72 | 3 | `shape only` | has a backward branch (often a loop), 26 ins | has a backward branch (often a loop) |
| `0x944470` | 72 | 1 | `shape only` | straight line / call sequence, 25 ins | straight line / call sequence |
| `0x944cf0` | 72 | 11 | `shape only` | has a backward branch (often a loop), 23 ins | has a backward branch (often a loop) |
| `0x945070` | 72 | 11 | `shape only` | has a backward branch (often a loop), 23 ins | has a backward branch (often a loop) |
| `0xfe1f0` | 71 | 121 | `shape only` | has a backward branch (often a loop), 24 ins | has a backward branch (often a loop) |
| `0x1a38b0` | 71 | 1 | `shape only` | straight line / call sequence, 20 ins | straight line / call sequence |
| `0x261f60` | 71 | 13 | `shape only` | straight line / call sequence, 20 ins | straight line / call sequence |
| `0x266400` | 71 | 1 | `shape only` | straight line / call sequence, 23 ins | straight line / call sequence |
| `0x2acf90` | 71 | 6 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x3ff3a0` | 71 | 9 | `shape only` | straight line / call sequence, 25 ins | straight line / call sequence |
| `0x639c50` | 71 | 2 | `strings` | (null) | has a backward branch (often a loop) |
| `0x910760` | 71 | 2 | `strings` | %s: __pos (which is %zu) > this->size()  \| basic_string::replace | has a backward branch (often a loop) |
| `0x1a8e90` | 70 | 2 | `shape only` | has a backward branch (often a loop), 24 ins | has a backward branch (often a loop) |
| `0x1b7be0` | 70 | 3 | `shape only` | straight line / call sequence, 16 ins | straight line / call sequence |
| `0x1c0a00` | 70 | 10 | `shape only` | has a backward branch (often a loop), 25 ins | has a backward branch (often a loop) |
| `0x60c8d0` | 70 | 1 | `shape only` | straight line / call sequence, 21 ins | straight line / call sequence |
| `0x6eb810` | 70 | 2 | `shape only` | straight line / call sequence, 19 ins | straight line / call sequence |
| `0x7bf070` | 70 | 3 | `shape only` | straight line / call sequence, 21 ins | straight line / call sequence |
| `0x7d0fb0` | 70 | 6 | `shape only` | has a backward branch (often a loop), 26 ins | has a backward branch (often a loop) |
| `0x86b750` | 70 | 12 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x99fed0` | 70 | 4 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x1c09b0` | 69 | 9 | `shape only` | has a backward branch (often a loop), 23 ins | has a backward branch (often a loop) |
| `0x21fa40` | 69 | 1 | `shape only` | straight line / call sequence, 27 ins | straight line / call sequence |
| `0x5229a0` | 69 | 1 | `shape only` | has a backward branch (often a loop), 25 ins | has a backward branch (often a loop) |
| `0x5229f0` | 69 | 1 | `shape only` | has a backward branch (often a loop), 25 ins | has a backward branch (often a loop) |
| `0x544530` | 69 | 1 | `shape only` | has a backward branch (often a loop), 21 ins | has a backward branch (often a loop) |
| `0x621d80` | 69 | 2 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x8ab830` | 69 | 20 | `shape only` | has a backward branch (often a loop), 20 ins | has a backward branch (often a loop) |
| `0xaf5a0` | 68 | 2 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x4fc0b0` | 68 | 3 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x5dee60` | 68 | 5 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x630da0` | 68 | 3 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x9a0700` | 68 | 3 | `shape only` | straight line / call sequence, 16 ins | straight line / call sequence |
| `0xf1580` | 67 | 45 | `shape only` | has a backward branch (often a loop), 23 ins | has a backward branch (often a loop) |
| `0x2663b0` | 67 | 4 | `shape only` | straight line / call sequence, 21 ins | straight line / call sequence |
| `0x86b6b0` | 67 | 37 | `shape only` | straight line / call sequence, 21 ins | straight line / call sequence |
| `0x888fa0` | 67 | 7 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x910030` | 67 | 9 | `shape only` | straight line / call sequence, 21 ins | straight line / call sequence |
| `0xd15e0` | 66 | 13 | `shape only` | straight line / call sequence, 18 ins | straight line / call sequence |
| `0x12dfd0` | 66 | 2 | `shape only` | has a backward branch (often a loop), 24 ins | has a backward branch (often a loop) |
| `0x1a6650` | 66 | 5 | `shape only` | straight line / call sequence, 24 ins | straight line / call sequence |
| `0x4dd980` | 66 | 2 | `shape only` | straight line / call sequence, 19 ins | straight line / call sequence |
| `0x4f7a50` | 66 | 1 | `shape only` | straight line / call sequence, 19 ins | straight line / call sequence |
| `0x57d9e0` | 66 | 3 | `shape only` | has a backward branch (often a loop), 20 ins | has a backward branch (often a loop) |
| `0x5cd310` | 66 | 4 | `shape only` | straight line / call sequence, 20 ins | straight line / call sequence |
| `0x89f760` | 66 | 2 | `shape only` | has a backward branch (often a loop), 21 ins | has a backward branch (often a loop) |
| `0x921970` | 66 | 1 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x921a10` | 66 | 3 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x921b40` | 66 | 1 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x921be0` | 66 | 3 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x944690` | 66 | 1 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x944730` | 66 | 3 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x944860` | 66 | 1 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x944900` | 66 | 3 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x69f90` | 65 | 4 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x11a670` | 65 | 1 | `shape only` | straight line / call sequence, 16 ins | straight line / call sequence |
| `0x1a2c80` | 65 | 4 | `shape only` | straight line / call sequence, 19 ins | straight line / call sequence |
| `0x4dc450` | 65 | 11 | `shape only` | straight line / call sequence, 19 ins | straight line / call sequence |
| `0x62f230` | 65 | 3 | `shape only` | straight line / call sequence, 18 ins | straight line / call sequence |
| `0x63fa50` | 65 | 7 | `shape only` | straight line / call sequence, 15 ins | straight line / call sequence |
| `0x82b0b0` | 65 | 6 | `shape only` | has a backward branch (often a loop), 20 ins | has a backward branch (often a loop) |
| `0x888f50` | 65 | 19 | `shape only` | straight line / call sequence, 21 ins | straight line / call sequence |
| `0x111ad0` | 64 | 21 | `shape only` | straight line / call sequence, 21 ins | straight line / call sequence |
| `0x5cfd80` | 64 | 4 | `shape only` | straight line / call sequence, 15 ins | straight line / call sequence |
| `0x170a90` | 63 | 2 | `shape only` | straight line / call sequence, 15 ins | straight line / call sequence |
| `0x266450` | 63 | 1 | `shape only` | straight line / call sequence, 16 ins | straight line / call sequence |
| `0x400650` | 63 | 1 | `shape only` | straight line / call sequence, 18 ins | straight line / call sequence |
| `0x4dc5d0` | 63 | 1 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x4f9fa0` | 62 | 2 | `shape only` | straight line / call sequence, 18 ins | straight line / call sequence |
| `0x522540` | 62 | 3 | `shape only` | has a backward branch (often a loop), 24 ins | has a backward branch (often a loop) |
| `0x5ee110` | 62 | 2 | `shape only` | straight line / call sequence, 18 ins | straight line / call sequence |
| `0x5ee150` | 62 | 2 | `shape only` | straight line / call sequence, 18 ins | straight line / call sequence |
| `0x8ba400` | 62 | 3 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x31d70` | 61 | 1 | `shape only` | straight line / call sequence, 17 ins | straight line / call sequence |
| `0x24b440` | 61 | 2 | `shape only` | straight line / call sequence, 15 ins | straight line / call sequence |
| `0x5702a0` | 61 | 1 | `shape only` | straight line / call sequence, 19 ins | straight line / call sequence |
| `0x6f4e70` | 61 | 2 | `shape only` | has a backward branch (often a loop), 18 ins | has a backward branch (often a loop) |
| `0x8971a0` | 61 | 2 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x89dfa0` | 61 | 5 | `shape only` | has a backward branch (often a loop), 18 ins | has a backward branch (often a loop) |
| `0x8ec9a0` | 61 | 2 | `shape only` | has a backward branch (often a loop), 20 ins | has a backward branch (often a loop) |
| `0xac50` | 60 | 15 | `callers` | called by 0xd710 GetNumberOfCommonCuts; 0x104d0 WaitComputationTermination; 0x10650 WaitNextSolution | has a backward branch (often a loop) |
| `0x1b130` | 60 | 7 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x2a8a0` | 60 | 4 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x2fc50` | 60 | 6 | `shape only` | straight line / call sequence, 20 ins | straight line / call sequence |
| `0x3b2b0` | 60 | 23 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0xc7290` | 60 | 10 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0xd0670` | 60 | 24 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x15c8c0` | 60 | 1 | `shape only` | has a backward branch (often a loop), 21 ins | has a backward branch (often a loop) |
| `0x1a2900` | 60 | 11 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x1a8d70` | 60 | 29 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x1f8580` | 60 | 4 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x20c080` | 60 | 32 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x2399d0` | 60 | 9 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x4b9970` | 60 | 6 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x5050a0` | 60 | 8 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x548640` | 60 | 5 | `shape only` | has a backward branch (often a loop), 21 ins | has a backward branch (often a loop) |
| `0x552470` | 60 | 1 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0x62b910` | 60 | 3 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x87f2a0` | 60 | 35 | `callers` | called by 0x2ab0 LaunchLocalComputation; 0x6100 LaunchComputation | straight line / call sequence |
| `0x21fab0` | 59 | 2 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x3f9090` | 59 | 32 | `shape only` | straight line / call sequence, 20 ins | straight line / call sequence |
| `0x4f9ee0` | 59 | 1 | `shape only` | has a backward branch (often a loop), 16 ins | has a backward branch (often a loop) |
| `0x531ee0` | 59 | 2 | `shape only` | straight line / call sequence, 20 ins | straight line / call sequence |
| `0x5c71c0` | 59 | 4 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x5f3c70` | 59 | 4 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x6f0cb0` | 59 | 2 | `shape only` | straight line / call sequence, 16 ins | straight line / call sequence |
| `0x6f0df0` | 59 | 2 | `shape only` | straight line / call sequence, 16 ins | straight line / call sequence |
| `0x74c400` | 59 | 5 | `shape only` | has a backward branch (often a loop), 19 ins | has a backward branch (often a loop) |
| `0xb5b10` | 58 | 1 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x4fc100` | 58 | 3 | `shape only` | straight line / call sequence, 12 ins | straight line / call sequence |
| `0x5d5780` | 58 | 7 | `shape only` | straight line / call sequence, 20 ins | straight line / call sequence |
| `0x5d57c0` | 58 | 2 | `shape only` | straight line / call sequence, 20 ins | straight line / call sequence |
| `0x924e60` | 58 | 7 | `shape only` | has a backward branch (often a loop), 22 ins | has a backward branch (often a loop) |
| `0x925930` | 58 | 11 | `shape only` | has a backward branch (often a loop), 22 ins | has a backward branch (often a loop) |
| `0x925e30` | 58 | 7 | `shape only` | has a backward branch (often a loop), 22 ins | has a backward branch (often a loop) |
| `0x942f50` | 58 | 12 | `shape only` | has a backward branch (often a loop), 22 ins | has a backward branch (often a loop) |
| `0x9a03b0` | 58 | 5 | `strings` | failed to read from file | straight line / call sequence |
| `0x170250` | 57 | 28 | `shape only` | straight line / call sequence, 12 ins | straight line / call sequence |
| `0x219690` | 57 | 3 | `shape only` | straight line / call sequence, 18 ins | straight line / call sequence |
| `0x505280` | 57 | 11 | `shape only` | straight line / call sequence, 22 ins | straight line / call sequence |
| `0x5052c0` | 57 | 9 | `shape only` | straight line / call sequence, 21 ins | straight line / call sequence |
| `0x592740` | 57 | 1 | `shape only` | has a backward branch (often a loop), 17 ins | has a backward branch (often a loop) |
| `0x656260` | 57 | 5 | `shape only` | straight line / call sequence, 17 ins | straight line / call sequence |
| `0x8743f0` | 57 | 1 | `shape only` | has a backward branch (often a loop), 14 ins | has a backward branch (often a loop) |
| `0x8f7ce0` | 57 | 1 | `shape only` | has a backward branch (often a loop), 17 ins | has a backward branch (often a loop) |
| `0x4f0c60` | 56 | 1 | `shape only` | straight line / call sequence, 9 ins | straight line / call sequence |
| `0x4f9be0` | 56 | 2 | `shape only` | straight line / call sequence, 12 ins | straight line / call sequence |
| `0x57a860` | 56 | 1 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x889010` | 56 | 4 | `shape only` | straight line / call sequence, 19 ins | straight line / call sequence |
| `0x889160` | 56 | 7 | `shape only` | straight line / call sequence, 21 ins | straight line / call sequence |
| `0x8ab100` | 56 | 11 | `shape only` | has a backward branch (often a loop), 18 ins | has a backward branch (often a loop) |
| `0x4194c0` | 55 | 2 | `shape only` | straight line / call sequence, 20 ins | straight line / call sequence |
| `0x51e020` | 55 | 1 | `shape only` | straight line / call sequence, 13 ins | straight line / call sequence |
| `0x619310` | 55 | 3 | `shape only` | has a backward branch (often a loop), 18 ins | has a backward branch (often a loop) |
| `0x6ee1f0` | 55 | 2 | `shape only` | straight line / call sequence, 18 ins | straight line / call sequence |
| `0x2fc90` | 54 | 5 | `shape only` | straight line / call sequence, 17 ins | straight line / call sequence |
| `0x4da8a0` | 54 | 2 | `shape only` | has a backward branch (often a loop), 15 ins | has a backward branch (often a loop) |
| `0x656000` | 54 | 22 | `shape only` | straight line / call sequence, 17 ins | straight line / call sequence |
| `0x6561e0` | 54 | 10 | `shape only` | straight line / call sequence, 17 ins | straight line / call sequence |
| `0x656220` | 54 | 3 | `shape only` | straight line / call sequence, 17 ins | straight line / call sequence |
| `0x679280` | 54 | 1 | `shape only` | straight line / call sequence, 17 ins | straight line / call sequence |
| `0x746970` | 54 | 2 | `shape only` | straight line / call sequence, 17 ins | straight line / call sequence |
| `0x7b3090` | 54 | 3 | `shape only` | straight line / call sequence, 17 ins | straight line / call sequence |
| `0x89e0d0` | 54 | 12 | `shape only` | straight line / call sequence, 18 ins | straight line / call sequence |
| `0x89e4d0` | 54 | 14 | `shape only` | straight line / call sequence, 18 ins | straight line / call sequence |
| `0x136c50` | 53 | 1 | `shape only` | has a backward branch (often a loop), 14 ins | has a backward branch (often a loop) |
| `0x15e560` | 53 | 3 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x259df0` | 53 | 6 | `shape only` | has a backward branch (often a loop), 16 ins | has a backward branch (often a loop) |
| `0x52fd50` | 53 | 2 | `shape only` | straight line / call sequence, 16 ins | straight line / call sequence |
| `0x5ce2d0` | 53 | 6 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x5ce310` | 53 | 2 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x5ce740` | 53 | 4 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x8c36f0` | 53 | 7 | `shape only` | has a backward branch (often a loop), 14 ins | has a backward branch (often a loop) |
| `0x8d2fa0` | 53 | 3 | `shape only` | has a backward branch (often a loop), 16 ins | has a backward branch (often a loop) |
| `0x24b050` | 52 | 2 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x4f76e0` | 52 | 6 | `shape only` | straight line / call sequence, 17 ins | straight line / call sequence |
| `0x992030` | 52 | 1 | `shape only` | has a backward branch (often a loop), 17 ins | has a backward branch (often a loop) |
| `0x60bf0` | 51 | 1 | `shape only` | straight line / call sequence, 13 ins | straight line / call sequence |
| `0x201cc0` | 51 | 6 | `shape only` | straight line / call sequence, 8 ins | straight line / call sequence |
| `0x552230` | 51 | 2 | `shape only` | straight line / call sequence, 15 ins | straight line / call sequence |
| `0x74b930` | 51 | 6 | `shape only` | straight line / call sequence, 16 ins | straight line / call sequence |
| `0x983d40` | 51 | 1 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x998920` | 51 | 44 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x9990a0` | 51 | 449 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x99af80` | 51 | 2 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x1bc20` | 50 | 1 | `shape only` | straight line / call sequence, 13 ins | straight line / call sequence |
| `0x2a700` | 50 | 2 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x12d9d0` | 50 | 2 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x1c0f10` | 50 | 1 | `shape only` | has a backward branch (often a loop), 17 ins | has a backward branch (often a loop) |
| `0x1c1070` | 50 | 3 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x1f8620` | 50 | 3 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x20bf80` | 50 | 1 | `shape only` | has a backward branch (often a loop), 17 ins | has a backward branch (often a loop) |
| `0x552370` | 50 | 2 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x2fc10` | 49 | 1 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x4f8d30` | 49 | 31 | `shape only` | straight line / call sequence, 12 ins | straight line / call sequence |
| `0x5c4100` | 49 | 7 | `shape only` | has a backward branch (often a loop), 20 ins | has a backward branch (often a loop) |
| `0x7bbaf0` | 49 | 14 | `shape only` | straight line / call sequence, 15 ins | straight line / call sequence |
| `0x50210` | 48 | 1 | `shape only` | straight line / call sequence, 13 ins | straight line / call sequence |
| `0x1bf170` | 48 | 30 | `shape only` | straight line / call sequence, 13 ins | straight line / call sequence |
| `0x4b6d80` | 48 | 18 | `shape only` | straight line / call sequence, 8 ins | straight line / call sequence |
| `0x5e62d0` | 48 | 6 | `shape only` | straight line / call sequence, 16 ins | straight line / call sequence |
| `0x60c980` | 48 | 1 | `shape only` | straight line / call sequence, 7 ins | straight line / call sequence |
| `0x8761b0` | 48 | 98 | `callers` | called by 0x2ab0 LaunchLocalComputation; 0x9330 NewNoFitNesting; 0x9af0 NewNoFitContext | straight line / call sequence |
| `0x24c470` | 47 | 1 | `shape only` | has a backward branch (often a loop), 14 ins | has a backward branch (often a loop) |
| `0x5c4d30` | 47 | 39 | `shape only` | straight line / call sequence, 15 ins | straight line / call sequence |
| `0x7c4a80` | 47 | 7 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x7c4ab0` | 47 | 2 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x99fe70` | 47 | 3 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x4f35d0` | 46 | 5 | `shape only` | has a backward branch (often a loop), 15 ins | has a backward branch (often a loop) |
| `0x4f8ce0` | 46 | 4 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x5ce270` | 46 | 1 | `shape only` | straight line / call sequence, 13 ins | straight line / call sequence |
| `0x7db490` | 46 | 12 | `shape only` | has a backward branch (often a loop), 15 ins | has a backward branch (often a loop) |
| `0x1f83e0` | 45 | 2 | `shape only` | has a backward branch (often a loop), 13 ins | has a backward branch (often a loop) |
| `0x516020` | 45 | 1 | `shape only` | has a backward branch (often a loop), 15 ins | has a backward branch (often a loop) |
| `0x5cb400` | 45 | 6 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x5ce2a0` | 45 | 9 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x634c40` | 45 | 19 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x89e0a0` | 45 | 1 | `shape only` | has a backward branch (often a loop), 12 ins | has a backward branch (often a loop) |
| `0x5f000` | 44 | 2 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x20c850` | 44 | 2 | `shape only` | straight line / call sequence, 13 ins | straight line / call sequence |
| `0x53a450` | 44 | 1 | `shape only` | straight line / call sequence, 12 ins | straight line / call sequence |
| `0x57d8f0` | 44 | 4 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x60b4e0` | 44 | 1 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x898780` | 44 | 1 | `shape only` | straight line / call sequence, 13 ins | straight line / call sequence |
| `0x898a80` | 44 | 1 | `shape only` | straight line / call sequence, 13 ins | straight line / call sequence |
| `0x8991c0` | 44 | 1 | `shape only` | straight line / call sequence, 13 ins | straight line / call sequence |
| `0x899690` | 44 | 1 | `shape only` | straight line / call sequence, 13 ins | straight line / call sequence |
| `0x899710` | 44 | 1 | `shape only` | straight line / call sequence, 13 ins | straight line / call sequence |
| `0x8997d0` | 44 | 1 | `shape only` | straight line / call sequence, 13 ins | straight line / call sequence |
| `0xb4da0` | 43 | 7 | `shape only` | straight line / call sequence, 9 ins | straight line / call sequence |
| `0x4dc3f0` | 43 | 12 | `shape only` | straight line / call sequence, 12 ins | straight line / call sequence |
| `0x5c5bc0` | 43 | 10 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x679f40` | 43 | 1 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x67d680` | 43 | 1 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x6de940` | 43 | 21 | `shape only` | straight line / call sequence, 15 ins | straight line / call sequence |
| `0x4de020` | 42 | 5 | `shape only` | has a backward branch (often a loop), 14 ins | has a backward branch (often a loop) |
| `0x5b3fd0` | 42 | 1 | `shape only` | has a backward branch (often a loop), 14 ins | has a backward branch (often a loop) |
| `0x5ba5d0` | 42 | 2 | `shape only` | has a backward branch (often a loop), 14 ins | has a backward branch (often a loop) |
| `0x4dde50` | 41 | 1 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x5f4870` | 41 | 1 | `strings` | %lf | straight line / call sequence |
| `0x600740` | 41 | 1 | `strings` | %#.16g | straight line / call sequence |
| `0x63f140` | 41 | 2 | `shape only` | has a backward branch (often a loop), 18 ins | has a backward branch (often a loop) |
| `0x86c130` | 41 | 2 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x3ba30` | 40 | 3 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x17ee30` | 40 | 2 | `shape only` | straight line / call sequence, 8 ins | straight line / call sequence |
| `0x4e83e0` | 40 | 1 | `shape only` | straight line / call sequence, 12 ins | straight line / call sequence |
| `0x60b770` | 40 | 2 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x8704d0` | 40 | 3 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x873380` | 40 | 31 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x873a20` | 40 | 4 | `shape only` | straight line / call sequence, 14 ins | straight line / call sequence |
| `0x60c750` | 39 | 1 | `shape only` | straight line / call sequence, 8 ins | straight line / call sequence |
| `0x178590` | 38 | 1 | `shape only` | straight line / call sequence, 9 ins | straight line / call sequence |
| `0x1785c0` | 38 | 1 | `shape only` | straight line / call sequence, 9 ins | straight line / call sequence |
| `0x86b700` | 38 | 8 | `shape only` | straight line / call sequence, 13 ins | straight line / call sequence |
| `0x877120` | 38 | 7 | `shape only` | straight line / call sequence, 12 ins | straight line / call sequence |
| `0x8772a0` | 38 | 4 | `shape only` | has a backward branch (often a loop), 11 ins | has a backward branch (often a loop) |
| `0x8a8190` | 38 | 14 | `shape only` | straight line / call sequence, 9 ins | straight line / call sequence |
| `0xc3a40` | 37 | 15 | `shape only` | has a backward branch (often a loop), 12 ins | has a backward branch (often a loop) |
| `0x52f950` | 37 | 3 | `shape only` | straight line / call sequence, 9 ins | straight line / call sequence |
| `0x52f980` | 37 | 1 | `shape only` | straight line / call sequence, 9 ins | straight line / call sequence |
| `0x52f9e0` | 37 | 1 | `shape only` | straight line / call sequence, 9 ins | straight line / call sequence |
| `0x52fa10` | 37 | 1 | `shape only` | straight line / call sequence, 9 ins | straight line / call sequence |
| `0x52fa40` | 37 | 3 | `shape only` | straight line / call sequence, 9 ins | straight line / call sequence |
| `0x52fa70` | 37 | 1 | `shape only` | straight line / call sequence, 9 ins | straight line / call sequence |
| `0x52faa0` | 37 | 1 | `shape only` | straight line / call sequence, 9 ins | straight line / call sequence |
| `0x60c780` | 37 | 1 | `shape only` | straight line / call sequence, 8 ins | straight line / call sequence |
| `0x60c7b0` | 37 | 1 | `shape only` | straight line / call sequence, 9 ins | straight line / call sequence |
| `0x90bfd0` | 37 | 1 | `shape only` | has a backward branch (often a loop), 11 ins | has a backward branch (often a loop) |
| `0x172430` | 36 | 1 | `strings` |  $ck | straight line / call sequence |
| `0x4fc080` | 36 | 4 | `shape only` | straight line / call sequence, 8 ins | straight line / call sequence |
| `0x4fc190` | 36 | 4 | `shape only` | straight line / call sequence, 8 ins | straight line / call sequence |
| `0x5cd590` | 36 | 7 | `shape only` | straight line / call sequence, 12 ins | straight line / call sequence |
| `0xcca40` | 35 | 11 | `shape only` | straight line / call sequence, 6 ins | straight line / call sequence |
| `0x1c82d0` | 35 | 2 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x544890` | 35 | 2 | `shape only` | straight line / call sequence, 12 ins | straight line / call sequence |
| `0x5fd0a0` | 35 | 10 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x60c7e0` | 35 | 1 | `shape only` | straight line / call sequence, 8 ins | straight line / call sequence |
| `0x6258f0` | 35 | 4 | `shape only` | has a backward branch (often a loop), 11 ins | has a backward branch (often a loop) |
| `0x63f170` | 35 | 2 | `shape only` | has a backward branch (often a loop), 15 ins | has a backward branch (often a loop) |
| `0x89e5f0` | 35 | 2 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x8aa7e0` | 35 | 65 | `shape only` | straight line / call sequence, 7 ins | straight line / call sequence |
| `0x16c270` | 34 | 19 | `shape only` | straight line / call sequence, 8 ins | straight line / call sequence |
| `0x1a8c80` | 34 | 7 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x1b7750` | 34 | 1 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x52f850` | 34 | 3 | `shape only` | straight line / call sequence, 8 ins | straight line / call sequence |
| `0x6791f0` | 34 | 2 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x826c60` | 34 | 104 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0xb4dd0` | 33 | 16 | `shape only` | straight line / call sequence, 9 ins | straight line / call sequence |
| `0x16c0a0` | 33 | 10 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x21a0c0` | 33 | 1 | `shape only` | straight line / call sequence, 12 ins | straight line / call sequence |
| `0x25ca00` | 33 | 1 | `shape only` | straight line / call sequence, 11 ins | straight line / call sequence |
| `0x3ff5d0` | 33 | 15 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x4b32f0` | 33 | 23 | `shape only` | straight line / call sequence, 8 ins | straight line / call sequence |
| `0x4dc610` | 33 | 1 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x5c3d30` | 33 | 2 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x876040` | 33 | 3 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x877a20` | 33 | 4 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x877b20` | 33 | 2 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x877be0` | 33 | 2 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x88db50` | 33 | 3 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x88db80` | 33 | 1 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x8925e0` | 33 | 1 | `shape only` | straight line / call sequence, 10 ins | straight line / call sequence |
| `0x626e0` | 32 | 1 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0xb5af0` | 32 | 1 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x570200` | 32 | 1 | `shape only` | has a backward branch (often a loop), 11 ins | has a backward branch (often a loop) |
| `0x570220` | 32 | 1 | `shape only` | has a backward branch (often a loop), 11 ins | has a backward branch (often a loop) |
| `0x583810` | 32 | 2 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x5984c0` | 32 | 4 | `shape only` | tiny helper, 10 ins | tiny helper |
| `0x5984e0` | 32 | 1 | `shape only` | tiny helper, 10 ins | tiny helper |
| `0x592310` | 31 | 1 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x1a27c0` | 30 | 2 | `shape only` | tiny helper, 10 ins | tiny helper |
| `0x1a2820` | 30 | 3 | `shape only` | tiny helper, 10 ins | tiny helper |
| `0x25c9e0` | 30 | 3 | `shape only` | tiny helper, 10 ins | tiny helper |
| `0x261f40` | 30 | 13 | `shape only` | tiny helper, 10 ins | tiny helper |
| `0x2f0830` | 30 | 4 | `shape only` | tiny helper, 6 ins | tiny helper |
| `0x544770` | 30 | 2 | `shape only` | tiny helper, 10 ins | tiny helper |
| `0x33a00` | 29 | 1 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x15d1d0` | 29 | 5 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x53a100` | 29 | 1 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0x5a61d0` | 29 | 1 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0xaf6a0` | 28 | 3 | `shape only` | tiny helper, 10 ins | tiny helper |
| `0x5c4cf0` | 28 | 15 | `shape only` | tiny helper, 10 ins | tiny helper |
| `0x5c4d10` | 28 | 6 | `shape only` | tiny helper, 10 ins | tiny helper |
| `0x605660` | 28 | 2 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x62f330` | 28 | 2 | `shape only` | has a backward branch (often a loop), 7 ins | has a backward branch (often a loop) |
| `0x63bd80` | 28 | 3 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x339e0` | 27 | 1 | `shape only` | tiny helper, 6 ins | tiny helper |
| `0x170900` | 27 | 11 | `shape only` | tiny helper, 10 ins | tiny helper |
| `0x1a1730` | 27 | 1 | `shape only` | has a backward branch (often a loop), 7 ins | has a backward branch (often a loop) |
| `0x1a9150` | 27 | 1 | `shape only` | tiny helper, 6 ins | tiny helper |
| `0x2348e0` | 27 | 1 | `shape only` | tiny helper, 5 ins | tiny helper |
| `0x259b50` | 27 | 1 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0x520420` | 27 | 1 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x5da140` | 27 | 1 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0x5e5c90` | 27 | 12 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x875f50` | 27 | 14 | `shape only` | has a backward branch (often a loop), 6 ins | has a backward branch (often a loop) |
| `0x888ff0` | 27 | 21 | `shape only` | has a backward branch (often a loop), 6 ins | has a backward branch (often a loop) |
| `0x895f60` | 27 | 1 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x172340` | 26 | 1 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x1b7940` | 26 | 4 | `shape only` | tiny helper, 6 ins | tiny helper |
| `0x1fd6a0` | 26 | 1 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x229550` | 26 | 3 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x2a7270` | 26 | 4 | `shape only` | tiny helper, 5 ins | tiny helper |
| `0x54e1c0` | 26 | 1 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x60bdb0` | 26 | 1 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x1ee8f0` | 25 | 1 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x2610c0` | 25 | 6 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x4f6fe0` | 25 | 1 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x4f7000` | 25 | 1 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x4fd100` | 25 | 4 | `shape only` | tiny helper, 6 ins | tiny helper |
| `0x54e1a0` | 25 | 1 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x5f0480` | 25 | 1 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x60be00` | 25 | 1 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x60c5a0` | 25 | 1 | `shape only` | tiny helper, 6 ins | tiny helper |
| `0x62d860` | 25 | 520 | `callers` | called by 0x2ab0 LaunchLocalComputation; 0x9330 NewNoFitNesting; 0x9af0 NewNoFitContext | tiny helper |
| `0xb5b50` | 24 | 2 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0xb5b70` | 24 | 1 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0x57d7f0` | 24 | 1 | `shape only` | tiny helper, 4 ins | tiny helper |
| `0x5c5180` | 24 | 12 | `shape only` | tiny helper, 4 ins | tiny helper |
| `0x5c6100` | 24 | 57 | `shape only` | tiny helper, 4 ins | tiny helper |
| `0x5fd080` | 24 | 4 | `shape only` | has a backward branch (often a loop), 7 ins | has a backward branch (often a loop) |
| `0x5fda60` | 24 | 7 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x8ab0e0` | 24 | 5 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0x339c0` | 23 | 1 | `shape only` | tiny helper, 6 ins | tiny helper |
| `0x10f200` | 23 | 20 | `shape only` | tiny helper, 5 ins | tiny helper |
| `0x16c4a0` | 23 | 14 | `shape only` | tiny helper, 6 ins | tiny helper |
| `0x8285a0` | 23 | 2 | `shape only` | tiny helper, 6 ins | tiny helper |
| `0x304e0` | 22 | 2 | `shape only` | tiny helper, 4 ins | tiny helper |
| `0x4aa70` | 22 | 1 | `shape only` | tiny helper, 5 ins | tiny helper |
| `0x170940` | 22 | 3 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x1c12b0` | 22 | 3 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x229570` | 22 | 2 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x266db0` | 22 | 9 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x266dd0` | 22 | 9 | `shape only` | tiny helper, 9 ins | tiny helper |
| `0x4d29b0` | 22 | 1 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x4d3a40` | 22 | 1 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x5e5bd0` | 22 | 20 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0x60b060` | 22 | 1 | `strings` | *** INTERNAL ERROR *** | tiny helper |
| `0x97a6d0` | 22 | 36 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0x200c90` | 21 | 2 | `shape only` | tiny helper, 5 ins | tiny helper |
| `0x2664c0` | 21 | 3 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0x5fd060` | 21 | 12 | `shape only` | has a backward branch (often a loop), 6 ins | has a backward branch (often a loop) |
| `0x62f380` | 21 | 1 | `shape only` | has a backward branch (often a loop), 7 ins | has a backward branch (often a loop) |
| `0x862030` | 21 | 20 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0x86a2c0` | 21 | 61 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0x33ce0` | 20 | 2 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0x266d90` | 20 | 9 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x877530` | 20 | 4 | `shape only` | tiny helper, 6 ins | tiny helper |
| `0x22d9e0` | 19 | 4 | `shape only` | tiny helper, 5 ins | tiny helper |
| `0x261f20` | 19 | 11 | `shape only` | tiny helper, 6 ins | tiny helper |
| `0x266d70` | 19 | 9 | `shape only` | tiny helper, 8 ins | tiny helper |
| `0x4f3630` | 19 | 2 | `shape only` | tiny helper, 5 ins | tiny helper |
| `0x4f9c40` | 19 | 6 | `shape only` | accessor (load and return), 4 ins | accessor (load and return) |
| `0x200cf0` | 18 | 2 | `shape only` | tiny helper, 5 ins | tiny helper |
| `0x4dc3d0` | 18 | 8 | `shape only` | tiny helper, 5 ins | tiny helper |
| `0x4fc360` | 18 | 3 | `shape only` | accessor (load and return), 4 ins | accessor (load and return) |
| `0x549a90` | 18 | 2 | `shape only` | tiny helper, 5 ins | tiny helper |
| `0x57d760` | 18 | 2 | `shape only` | tiny helper, 6 ins | tiny helper |
| `0x5fd640` | 18 | 9 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0x5fd660` | 18 | 3 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0x4ebe0` | 17 | 1 | `shape only` | tiny helper, 5 ins | tiny helper |
| `0x266ff0` | 17 | 7 | `shape only` | tiny helper, 7 ins | tiny helper |
| `0x531eb0` | 17 | 3 | `shape only` | tiny helper, 4 ins | tiny helper |
| `0x5da250` | 17 | 2 | `shape only` | accessor (load and return), 4 ins | accessor (load and return) |
| `0x5fb930` | 17 | 9 | `shape only` | tiny helper, 4 ins | tiny helper |
| `0x60bdd0` | 17 | 2 | `shape only` | tiny helper, 6 ins | tiny helper |
| `0x877ce0` | 17 | 5 | `shape only` | tiny helper, 6 ins | tiny helper |
| `0x157db0` | 16 | 1 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x183f50` | 16 | 5 | `shape only` | accessor (load and return), 4 ins | accessor (load and return) |
| `0x4f8c50` | 16 | 3 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x3b7a0` | 15 | 4 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x157dc0` | 15 | 1 | `shape only` | tiny helper, 5 ins | tiny helper |
| `0x2a0f70` | 15 | 2 | `shape only` | accessor (load and return), 4 ins | accessor (load and return) |
| `0x2a9f10` | 15 | 1 | `shape only` | accessor (load and return), 4 ins | accessor (load and return) |
| `0x2a9f70` | 15 | 6 | `shape only` | accessor (load and return), 4 ins | accessor (load and return) |
| `0x4fd120` | 15 | 4 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x5fb910` | 15 | 9 | `shape only` | tiny helper, 4 ins | tiny helper |
| `0x5fb920` | 15 | 7 | `shape only` | tiny helper, 4 ins | tiny helper |
| `0x5fbc10` | 15 | 6 | `shape only` | tiny helper, 4 ins | tiny helper |
| `0x62efc0` | 15 | 2 | `shape only` | tiny helper, 5 ins | tiny helper |
| `0x8760f0` | 15 | 9 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x877ad0` | 15 | 12 | `shape only` | has a backward branch (often a loop), 3 ins | has a backward branch (often a loop) |
| `0x877bd0` | 15 | 8 | `shape only` | has a backward branch (often a loop), 3 ins | has a backward branch (often a loop) |
| `0x88dc00` | 15 | 10 | `shape only` | has a backward branch (often a loop), 3 ins | has a backward branch (often a loop) |
| `0x15a4d0` | 14 | 1 | `shape only` | accessor (load and return), 4 ins | accessor (load and return) |
| `0x1c8370` | 14 | 1 | `shape only` | accessor (load and return), 4 ins | accessor (load and return) |
| `0x21fa90` | 13 | 1 | `shape only` | has a backward branch (often a loop), 3 ins | has a backward branch (often a loop) |
| `0x4d3ef0` | 13 | 6 | `shape only` | accessor (load and return), 4 ins | accessor (load and return) |
| `0x549ab0` | 13 | 1 | `shape only` | tiny helper, 4 ins | tiny helper |
| `0x54ce70` | 13 | 2 | `shape only` | tiny helper, 6 ins | tiny helper |
| `0x60be20` | 13 | 1 | `shape only` | tiny helper, 5 ins | tiny helper |
| `0x45530` | 12 | 1 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x62640` | 12 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x62650` | 12 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x62660` | 12 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x62670` | 12 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x62680` | 12 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x62690` | 12 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x626a0` | 12 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x626b0` | 12 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x626c0` | 12 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x626d0` | 12 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x178550` | 12 | 2 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x178580` | 12 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x178660` | 12 | 5 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x267010` | 12 | 1 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x4fbe60` | 12 | 3 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x4fbe70` | 12 | 3 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x4fbe80` | 12 | 4 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x4fc070` | 12 | 4 | `shape only` | accessor (load and return), 4 ins | accessor (load and return) |
| `0x4fc220` | 12 | 2 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x4fc230` | 12 | 9 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x545290` | 12 | 1 | `strings` | @w\| | tiny helper |
| `0x5479c0` | 12 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x6562a0` | 12 | 2 | `shape only` | tiny helper, 4 ins | tiny helper |
| `0x8774e0` | 12 | 4 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x998cb0` | 12 | 9 | `shape only` | has a backward branch (often a loop), 2 ins | has a backward branch (often a loop) |
| `0x157d60` | 11 | 2 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x157d70` | 11 | 1 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x157d80` | 11 | 1 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x157d90` | 11 | 1 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x157da0` | 11 | 1 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x16c260` | 11 | 1 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x18e830` | 11 | 7 | `shape only` | accessor (load and return), 4 ins | accessor (load and return) |
| `0x1c8380` | 11 | 1 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x4dae90` | 11 | 1 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x4fbe50` | 11 | 9 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x52f8c0` | 11 | 4 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x600690` | 11 | 2 | `shape only` | has a backward branch (often a loop), 3 ins | has a backward branch (often a loop) |
| `0x8aaaf0` | 11 | 53 | `shape only` | accessor (load and return), 4 ins | accessor (load and return) |
| `0x962f10` | 11 | 2 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x963560` | 11 | 2 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x9635f0` | 11 | 2 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x33a30` | 10 | 1 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x3b890` | 10 | 1 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0xaef20` | 10 | 4 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0xaef30` | 10 | 2 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x21f9d0` | 10 | 3 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x3e2a50` | 10 | 3 | `shape only` | has a backward branch (often a loop), 2 ins | has a backward branch (often a loop) |
| `0x4f4ec0` | 10 | 3 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x4fbe40` | 10 | 4 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x4fbe90` | 10 | 4 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x4fbea0` | 10 | 4 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x4fc1c0` | 10 | 7 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x4fc240` | 10 | 7 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x4fc330` | 10 | 3 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x4fc390` | 10 | 8 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x4fd0f0` | 10 | 1 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x52f830` | 10 | 4 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x54cbc0` | 10 | 14 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x5da240` | 10 | 2 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x60c2d0` | 10 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x159b90` | 9 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x17b9e0` | 9 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x17b9f0` | 9 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x2664a0` | 9 | 3 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x419610` | 9 | 27 | `shape only` | tiny helper, 4 ins | tiny helper |
| `0x4dc3c0` | 9 | 6 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4ddd20` | 9 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f7610` | 9 | 3 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f7620` | 9 | 3 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f7640` | 9 | 15 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f7650` | 9 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f7660` | 9 | 9 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f7670` | 9 | 3 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f8d10` | 9 | 4 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x4f8d20` | 9 | 2 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x51c250` | 9 | 5 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x51d8e0` | 9 | 5 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x520810` | 9 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x62f010` | 9 | 1 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x33a20` | 8 | 2 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x33a50` | 8 | 1 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x3f740` | 8 | 4 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x59ab0` | 8 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x5a290` | 8 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x1333b0` | 8 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x15a4f0` | 8 | 1 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x1708f0` | 8 | 8 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x170a10` | 8 | 4 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x173750` | 8 | 1 | `shape only` | has a backward branch (often a loop), 2 ins | has a backward branch (often a loop) |
| `0x178570` | 8 | 12 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x178640` | 8 | 8 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x178650` | 8 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x252b20` | 8 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x252b30` | 8 | 3 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x252b50` | 8 | 3 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4dc3a0` | 8 | 3 | `shape only` | has a backward branch (often a loop), 2 ins | has a backward branch (often a loop) |
| `0x4f7370` | 8 | 4 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x4f77c0` | 8 | 6 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4fc1e0` | 8 | 14 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x4fc1f0` | 8 | 3 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x51dd70` | 8 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x54ce30` | 8 | 14 | `shape only` | tiny helper, 4 ins | tiny helper |
| `0x54ce40` | 8 | 8 | `shape only` | tiny helper, 4 ins | tiny helper |
| `0x54ce50` | 8 | 4 | `shape only` | tiny helper, 4 ins | tiny helper |
| `0x600680` | 8 | 19 | `shape only` | has a backward branch (often a loop), 2 ins | has a backward branch (often a loop) |
| `0x60bdf0` | 8 | 1 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x822590` | 8 | 36 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x895f80` | 8 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x89a730` | 8 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x8aa7d0` | 8 | 17 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x8aa880` | 8 | 153 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x9635e0` | 8 | 2 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0xd5990` | 7 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x1333a0` | 7 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4dd9f0` | 7 | 4 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4dda00` | 7 | 8 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f7390` | 7 | 4 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f73b0` | 7 | 5 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x51cfe0` | 7 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x526690` | 7 | 9 | `shape only` | has a backward branch (often a loop), 2 ins | has a backward branch (often a loop) |
| `0x5433e0` | 7 | 4 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x5d74d0` | 7 | 3 | `shape only` | accessor (load and return), 3 ins | accessor (load and return) |
| `0x63f5d0` | 7 | 1 | `shape only` | thunk (jmp), 1 ins | thunk (jmp) |
| `0x23e60` | 6 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x6c0f0` | 6 | 4 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0xb5b90` | 6 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x252b40` | 6 | 3 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4dc4a0` | 6 | 6 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4dc4b0` | 6 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4ddcf0` | 6 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4ddd00` | 6 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f4f20` | 6 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f7330` | 6 | 3 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f7340` | 6 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f8c90` | 6 | 5 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f8ca0` | 6 | 6 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f8cb0` | 6 | 5 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f9c20` | 6 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x52f8b0` | 6 | 4 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x52f8f0` | 6 | 9 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x547630` | 6 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x547640` | 6 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x547650` | 6 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x547660` | 6 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x1be60` | 5 | 1 | `callers` | called by 0x10650 WaitNextSolution | thunk (jmp) |
| `0xf1550` | 5 | 26 | `shape only` | thunk (jmp), 1 ins | thunk (jmp) |
| `0xfe240` | 5 | 740 | `shape only` | thunk (jmp), 1 ins | thunk (jmp) |
| `0x134f80` | 5 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x17b9a0` | 5 | 4 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x17b9b0` | 5 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x17b9c0` | 5 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x17b9d0` | 5 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x1804d0` | 5 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x1804e0` | 5 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x23f680` | 5 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x252b10` | 5 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x2664b0` | 5 | 3 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x2713d0` | 5 | 2 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x2af090` | 5 | 6 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4daea0` | 5 | 16 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4daeb0` | 5 | 17 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4db7d0` | 5 | 2 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x4db800` | 5 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4dc3b0` | 5 | 18 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4dd9e0` | 5 | 7 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4ddca0` | 5 | 6 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4ddcb0` | 5 | 6 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4ddcc0` | 5 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4ddd10` | 5 | 18 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f35c0` | 5 | 4 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f4f10` | 5 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f7350` | 5 | 5 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f7360` | 5 | 4 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f73c0` | 5 | 10 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f73d0` | 5 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x51d0e0` | 5 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x520630` | 5 | 8 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x52f8a0` | 5 | 7 | `shape only` | tiny helper, 3 ins | tiny helper |
| `0x52f940` | 5 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x547620` | 5 | 4 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x5479b0` | 5 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x5483a0` | 5 | 6 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x5483b0` | 5 | 7 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x5483c0` | 5 | 9 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x56a280` | 5 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x5fbc70` | 5 | 3 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x630fd0` | 5 | 1 | `shape only` | thunk (jmp), 1 ins | thunk (jmp) |
| `0x862020` | 5 | 10 | `shape only` | thunk (jmp), 1 ins | thunk (jmp) |
| `0x86a2b0` | 5 | 27 | `shape only` | thunk (jmp), 1 ins | thunk (jmp) |
| `0x8774f0` | 5 | 67 | `callers` | called by 0x2ab0 LaunchLocalComputation; 0x6100 LaunchComputation; 0x104d0 WaitComputationTermination | thunk (jmp) |
| `0x895f90` | 5 | 7 | `callers` | called by 0x2ab0 LaunchLocalComputation; 0x6100 LaunchComputation | thunk (jmp) |
| `0x979fd0` | 5 | 10 | `shape only` | thunk (jmp), 1 ins | thunk (jmp) |
| `0x998cc0` | 5 | 2 | `shape only` | thunk (jmp), 1 ins | thunk (jmp) |
| `0x15a4e0` | 4 | 1 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x178560` | 4 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x17ff30` | 4 | 5 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x266490` | 4 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x2664e0` | 4 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4dac80` | 4 | 5 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4dc390` | 4 | 19 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x4dd9d0` | 4 | 12 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x4ddc90` | 4 | 3 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x4f35b0` | 4 | 5 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x4f7060` | 4 | 5 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f7290` | 4 | 4 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f7380` | 4 | 4 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f76b0` | 4 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f76c0` | 4 | 5 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f8350` | 4 | 11 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x4f8c70` | 4 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f8cc0` | 4 | 4 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4f8cd0` | 4 | 9 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x4fc1d0` | 4 | 13 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x4fc200` | 4 | 1 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x51c010` | 4 | 21 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x51c020` | 4 | 33 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x51d300` | 4 | 18 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x520640` | 4 | 6 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x52dba0` | 4 | 4 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x52f8d0` | 4 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x52f8e0` | 4 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x548380` | 4 | 5 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x548390` | 4 | 4 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x548630` | 4 | 12 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x55e8c0` | 4 | 1 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x570280` | 4 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x570290` | 4 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x5c61e0` | 4 | 12 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x5fc7e0` | 4 | 3 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x62dbe0` | 4 | 2 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x62dbf0` | 4 | 2 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0x67db00` | 4 | 2 | `shape only` | accessor (load and return), 2 ins | accessor (load and return) |
| `0xd5970` | 3 | 7 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0xd59a0` | 3 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x133180` | 3 | 3 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x54d110` | 3 | 2 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x559fd0` | 3 | 6 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0x62f000` | 3 | 1 | `shape only` | tiny helper, 2 ins | tiny helper |
| `0xb4490` | 1 | 15 | `shape only` | tiny helper, 1 ins | tiny helper |
| `0x2b3a50` | 1 | 19 | `shape only` | tiny helper, 1 ins | tiny helper |
| `0x3715e0` | 1 | 11 | `shape only` | tiny helper, 1 ins | tiny helper |
| `0x371fd0` | 1 | 12 | `shape only` | tiny helper, 1 ins | tiny helper |
| `0x418810` | 1 | 2 | `shape only` | tiny helper, 1 ins | tiny helper |
| `0x601980` | 1 | 2 | `shape only` | tiny helper, 1 ins | tiny helper |
| `0x8ab150` | 1 | 16 | `shape only` | tiny helper, 1 ins | tiny helper |
| `0x9465c0` | 1 | 164 | `shape only` | tiny helper, 1 ins | tiny helper |
