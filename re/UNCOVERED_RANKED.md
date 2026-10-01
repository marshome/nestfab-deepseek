# 未覆盖函数清单（按体积排序，来自 `re/g_coverage.py`）

口径：**分母** = 从导出表出发沿 `callees` 可达的全部函数（库真正能跑到的代码）；
**分子** = 其入口地址在 `re/*.md` 或 `lcns/**` 中被引用过的函数。
这是**代理指标**：被引用只说明"看过并写下了它是什么"，不等于逐指令复现（后者由 `include/lcns/recovery.hpp` 的登记表跟踪）。

- 可达函数：**6181**（4670042 字节）
- 已被引用：**2896**（2849917 字节）= **61.0%**
- 导出条目中有被引用入口的：**168 / 168**
- 未引用：**3285** 个函数、**1820125** 字节（39.0%）

其中：**第三方/工具链** 722 个函数、334954 字节（7.2% of reachable，无需逆向）；**lcns 领域代码** 2563 个函数、1485171 字节（**31.8%**，这才是真正剩下的工作）

## 未引用里最大的 120 个

| RVA | 字节 | 调用者数 | 指令数 | 线索 |
|---|---:|---:|---:|---|
| `0x9640d0` | 9021 | 3 | 1469 | data@0x88dc80 |
| `0x983e30` | 8990 | 4 | 1461 | data@0x88dc80 |
| `0x987c50` | 8874 | 2 | 1442 | data@0x88dc80 |
| `0x7e9580` | 7580 | 3 | 1494 | data@0x9da280 |
| `0x2403a0` | 7543 | 3 | 1661 | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x8a2c90` | 7436 | 2 | 1931 |  |
| `0xa85d0` | 7292 | 2 | 1382 | basic_string::_M_construct null not valid |
| `0xa6950` | 7292 | 2 | 1382 | basic_string::_M_construct null not valid |
| `0x248550` | 7274 | 2 | 1544 | data@0x7b3020 |
| `0x760d90` | 7023 | 2 | 1501 | data@0x9da2d0 |
| `0x7d5790` | 6754 | 3 | 1311 | data@0x88dc80 |
| `0x8a5980` | 6582 | 2 | 1708 |  |
| `0x982410` | 6194 | 2 | 1416 |  |
| `0x976800` | 6159 | 2 | 1486 |  |
| `0x949740` | 5930 | 2 | 946 | data@0x88dc80 |
| `0x140540` | 5671 | 3 | 1150 | basic_string::_M_construct null not valid |
| `0xa3e10` | 5521 | 3 | 1108 | basic_string::_M_construct null not valid |
| `0xa53b0` | 5521 | 3 | 1108 | basic_string::_M_construct null not valid |
| `0x753000` | 5250 | 2 | 1007 | basic_string::_M_construct null not valid |
| `0x76b450` | 5244 | 2 | 947 | basic_string::_M_construct null not valid |
| `0x54e270` | 4954 | 4 | 1150 | data@0x9dc0a0 |
| `0x56e6b0` | 4827 | 2 | 1039 | data@0x88dc80 |
| `0x97c670` | 4801 | 2 | 1115 |  |
| `0x1eec00` | 4688 | 3 | 813 | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x76c8d0` | 4669 | 3 | 816 | basic_string::_M_construct null not valid |
| `0xcca70` | 4614 | 1 | 1360 |  |
| `0x698f10` | 4599 | 3 | 936 | data@0x9b1df0 |
| `0x96e520` | 4578 | 3 | 789 | data@0x88dc80 |
| `0x5f2790` | 4440 | 2 | 803 | data@0x9dfe60 |
| `0x98a7d0` | 4430 | 2 | 760 |  |
| `0x559d0` | 4316 | 2 | 723 |  |
| `0x67dc00` | 4249 | 8 | 1006 | data@0x9dfbd8 |
| `0x726550` | 4232 | 2 | 716 | data@0x9dfbd8 |
| `0x52e7e0` | 4135 | 6 | 885 | basic_string::_M_construct null not valid |
| `0x7f3090` | 4122 | 2 | 889 | data@0x9d9368 |
| `0x762900` | 4061 | 2 | 848 | data@0x9da2d8 |
| `0x5ee1a0` | 4039 | 3 | 732 | data@0x9dfdc8 |
| `0x4cf000` | 4021 | 2 | 839 | basic_string::_M_construct null not valid |
| `0x4efc80` | 3996 | 3 | 744 | basic_string::_M_construct null not valid |
| `0x5c830` | 3923 | 2 | 809 | data@0x9b0900 |
| `0x5eb470` | 3831 | 4 | 817 | vector::reserve |
| `0x251c00` | 3807 | 2 | 727 | data@0x24b790 |
| `0x6fe060` | 3751 | 4 | 746 |  |
| `0x174be0` | 3710 | 3 | 885 | vector::reserve |
| `0x5aa750` | 3691 | 2 | 656 |  |
| `0x565f80` | 3681 | 3 | 742 | data@0x88dc80 |
| `0x557660` | 3659 | 2 | 792 | vector::_M_default_append |
| `0x7b6260` | 3610 | 5 | 702 | data@0xa02910 |
| `0x577310` | 3568 | 2 | 725 | data@0x88dc80 |
| `0x8bccb0` | 3507 | 2 | 815 | basic_string::_M_construct null not valid |
| `0x8eb110` | 3500 | 2 | 789 |  |
| `0x7257e0` | 3439 | 2 | 584 | data@0x9dfbd8 |
| `0x14bb60` | 3418 | 2 | 676 | data@0x9bd160 |
| `0x9b300` | 3413 | 2 | 735 |  |
| `0x8b1080` | 3408 | 2 | 620 | data@0x88dc80 |
| `0x565230` | 3398 | 2 | 653 | data@0x88dc80 |
| `0x148e00` | 3379 | 2 | 658 | data@0x9bd130 |
| `0x57f20` | 3368 | 2 | 522 |  |
| `0x5328a0` | 3363 | 5 | 716 | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x8cc0b0` | 3342 | 2 | 769 | vector::_M_range_insert |
| `0x8ccdc0` | 3342 | 2 | 769 | vector::_M_range_insert |
| `0x5aff80` | 3314 | 2 | 716 |  |
| `0x228880` | 3268 | 3 | 820 | vector::reserve |
| `0x562790` | 3266 | 3 | 797 | data@0x9dc3d8 |
| `0x53e020` | 3193 | 2 | 756 | data@0x9dbe90 |
| `0x5645b0` | 3192 | 2 | 646 |  |
| `0x53eca0` | 3178 | 2 | 709 |  |
| `0x52c5e0` | 3177 | 2 | 740 | data@0x9dbc40 |
| `0x7f0f00` | 3145 | 4 | 629 | basic_string::_M_construct null not valid |
| `0x206690` | 3137 | 5 | 635 |  |
| `0x571820` | 3130 | 3 | 636 |  |
| `0x13c8d0` | 3096 | 3 | 597 | data@0x9bd078 |
| `0x95010` | 3058 | 2 | 670 |  |
| `0x225d30` | 3047 | 2 | 661 | vector::reserve |
| `0x25ca30` | 3040 | 2 | 588 |  |
| `0x684de0` | 3005 | 2 | 684 |  |
| `0x99ad0` | 2938 | 4 | 663 | AUATUWVSH |
| `0x6706a0` | 2914 | 10 | 637 |  |
| `0x58c50` | 2895 | 2 | 445 |  |
| `0x671b60` | 2882 | 2 | 656 | data@0x9c1b78 |
| `0x25e020` | 2878 | 5 | 580 | data@0x9c2bf0 |
| `0x178c00` | 2830 | 2 | 568 | vector::reserve |
| `0x657210` | 2830 | 3 | 755 | data@0x88dc80 |
| `0x599d60` | 2829 | 2 | 648 |  |
| `0x560c30` | 2828 | 2 | 560 | data@0x9dc388 |
| `0x4f5ce0` | 2806 | 2 | 777 |  |
| `0x4eaea0` | 2765 | 3 | 496 | data@0x88dc80 |
| `0x59b930` | 2759 | 2 | 643 |  |
| `0x8ac620` | 2756 | 2 | 674 |  |
| `0x175fb0` | 2734 | 2 | 669 | vector::reserve |
| `0x13faa0` | 2705 | 2 | 580 | basic_string::_M_construct null not valid |
| `0x8da6c0` | 2662 | 2 | 598 |  |
| `0x72b7d0` | 2658 | 3 | 623 | data@0x9dfbd0 |
| `0x760330` | 2642 | 2 | 627 | data@0x9da2d0 |
| `0x1ba4c0` | 2642 | 2 | 559 |  |
| `0x8af220` | 2640 | 2 | 632 |  |
| `0x182d90` | 2638 | 2 | 617 | data@0xa55d40 |
| `0x772d40` | 2622 | 3 | 552 | data@0x9bd1c0 |
| `0x54d760` | 2622 | 3 | 613 |  |
| `0x163170` | 2614 | 4 | 537 |  |
| `0x95cdc0` | 2610 | 3 | 491 | data@0x88dc80 |
| `0x139800` | 2586 | 4 | 542 |  |
| `0x4d7720` | 2563 | 3 | 513 |  |
| `0x54ac00` | 2555 | 3 | 579 |  |
| `0x8abb50` | 2549 | 2 | 606 |  |
| `0x8d8c00` | 2547 | 3 | 657 | vector::_M_range_insert |
| `0x89b7b0` | 2542 | 3 | 570 |  |
| `0x722a0` | 2528 | 3 | 553 | data@0x9b1648 |
| `0x95dc80` | 2528 | 2 | 602 |  |
| `0x65f640` | 2512 | 8 | 377 |  |
| `0x6c4cc0` | 2510 | 2 | 500 |  |
| `0x8a49a0` | 2503 | 2 | 672 |  |
| `0x5215d0` | 2485 | 3 | 480 | data@0x9dbbf0 |
| `0x903330` | 2468 | 2 | 593 |  |
| `0x172ac0` | 2445 | 2 | 556 | data@0xa37310 |
| `0x1b9650` | 2423 | 2 | 521 |  |
| `0x681040` | 2419 | 3 | 494 | data@0x5d8dd0 |
| `0x581fd0` | 2416 | 2 | 523 |  |
| `0x1dda60` | 2414 | 2 | 520 | data@0x9c05b0 |
| `0x548680` | 2413 | 3 | 569 | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
