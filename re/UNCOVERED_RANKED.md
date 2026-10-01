# 未覆盖函数清单（按体积排序，来自 `re/g_coverage.py`）

口径：**分母** = 从导出表出发沿 `callees` 可达的全部函数（库真正能跑到的代码）；
**分子** = 其入口地址在 `re/*.md` 或 `lcns/**` 中被引用过的函数。
这是**代理指标**：被引用只说明"看过并写下了它是什么"，不等于逐指令复现（后者由 `include/lcns/recovery.hpp` 的登记表跟踪）。

- 可达函数：**6181**（4670042 字节）
- 已被引用：**901**（1326328 字节）= **28.4%**
- 导出条目中有被引用入口的：**168 / 168**
- 未引用：**5280** 个函数、**3343714** 字节（71.6%）

其中：**第三方/工具链** 374 个函数、576282 字节（12.3% of reachable，无需逆向）；**lcns 领域代码** 4906 个函数、2767432 字节（**59.3%**，这才是真正剩下的工作）

## 未引用里最大的 120 个

| RVA | 字节 | 调用者数 | 指令数 | 线索 |
|---|---:|---:|---:|---|
| `0x7e1480` | 17034 | 8 | 3386 |  |
| `0x68f750` | 15812 | 3 | 3128 | part_number < m_reduced_problem.GetNumberOfParts() |
| `0x5ac040` | 15111 | 4 | 2761 | data@0x7d7d20 |
| `0x5ba600` | 14064 | 2 | 2885 |  |
| `0x4c8670` | 13786 | 2 | 2784 | basic_string::_M_construct null not valid |
| `0x6b4160` | 13438 | 2 | 3034 |  |
| `0x6f8f30` | 13410 | 2 | 3214 | sha1 too many bytes |
| `0x501b60` | 13199 | 2 | 2762 | basic_string::_M_construct null not valid |
| `0x142690` | 13008 | 2 | 2477 | basic_string::_M_construct null not valid |
| `0x631890` | 12852 | 3 | 2860 | data@0xa06bc1 |
| `0x5b48d0` | 12545 | 3 | 2401 | data@0x9de5a8 |
| `0x6d7250` | 12157 | 2 | 2552 |  |
| `0x255390` | 12065 | 5 | 2751 |  |
| `0x88380` | 12013 | 2 | 2948 |  |
| `0x215720` | 11929 | 8 | 2221 | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x6d470` | 11478 | 2 | 2116 | sheet |
| `0x7bc340` | 11359 | 2 | 2241 | data@0x9dbca0 |
| `0x6b1560` | 11250 | 2 | 2767 |  |
| `0x12f460` | 10885 | 2 | 2263 | UWVSH |
| `0x212d30` | 10728 | 2 | 2012 | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x4cc640` | 10685 | 3 | 2005 | false |
| `0x20fe90` | 10648 | 2 | 1999 | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x1d7960` | 10072 | 2 | 2144 | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x5679f0` | 9918 | 2 | 1856 | data@0x88dc80 |
| `0x151ba0` | 9869 | 2 | 1849 |  |
| `0x58fc60` | 9654 | 2 | 1877 |  |
| `0x1f5c20` | 9576 | 2 | 1850 | basic_string::append |
| `0x578100` | 9462 | 2 | 1496 | data@0x88dc80 |
| `0x6c0fc0` | 9141 | 4 | 2175 |  |
| `0x6ad580` | 8964 | 2 | 2142 |  |
| `0x5b7a90` | 8833 | 2 | 1741 |  |
| `0x53790` | 8763 | 2 | 1467 |  |
| `0x592870` | 8756 | 5 | 1560 | C:\Users\renaud\nest\external\boost_1_63_0/boost/multiprecision/ration |
| `0x70150` | 8524 | 2 | 1659 | basic_string::_M_construct null not valid |
| `0x7eedb0` | 8514 | 2 | 1594 | basic_string::_M_construct null not valid |
| `0x21d040` | 8462 | 3 | 1432 | WVSA |
| `0x74f820` | 8400 | 2 | 1503 |  |
| `0x681fa0` | 7633 | 1 | 1891 | AWAVAUATUWVSH |
| `0x56c9a0` | 7435 | 2 | 1513 | data@0x88dc80 |
| `0x8ef0e0` | 7416 | 13 | 1591 | basic_string::_M_construct null not valid |
| `0x147180` | 7237 | 2 | 1354 |  |
| `0x635fc0` | 7120 | 4 | 1499 | inity |
| `0x530110` | 6835 | 4 | 1269 | data@0x9dbca0 |
| `0x4e1670` | 6819 | 2 | 1374 | basic_string::_M_construct null not valid |
| `0x22e960` | 6710 | 3 | 1363 | ..\nesting\algos\../nesting.hpp |
| `0x226e10` | 6607 | 3 | 1460 | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x4fdfe0` | 6439 | 5 | 1326 | ..\structure\problem.cpp |
| `0x513880` | 6150 | 2 | 1221 | basic_string::append |
| `0x264af0` | 6107 | 4 | 1128 | data@0x9c2cc0 |
| `0x553e00` | 5858 | 2 | 1397 |  |
| `0x58e600` | 5724 | 2 | 1181 |  |
| `0x140540` | 5671 | 3 | 1150 | basic_string::_M_construct null not valid |
| `0x41920` | 5640 | 8 | 1133 | ..\multi\nesting_context.cpp |
| `0x191e80` | 5521 | 2 | 1014 | (assert_aux1 == assert_aux2) |
| `0xa3e10` | 5521 | 3 | 1108 | basic_string::_M_construct null not valid |
| `0x63bf20` | 5521 | 2 | 1273 | Infinity |
| `0xa53b0` | 5521 | 3 | 1108 | basic_string::_M_construct null not valid |
| `0x751aa0` | 5463 | 2 | 1025 | data@0xa57ea0 |
| `0x1f36a0` | 5373 | 2 | 1103 |  |
| `0x4c0a50` | 5334 | 2 | 908 | data@0x9d946e |
| `0x8e4570` | 5265 | 2 | 1174 | data@0x88dc80 |
| `0x753000` | 5250 | 2 | 1007 | basic_string::_M_construct null not valid |
| `0x76b450` | 5244 | 2 | 947 | basic_string::_M_construct null not valid |
| `0x8ff70` | 5226 | 2 | 1029 | basic_string::_M_construct null not valid |
| `0x5a4d70` | 5209 | 4 | 1034 |  |
| `0x56ba0` | 4992 | 3 | 864 |  |
| `0x6afe10` | 4918 | 2 | 1115 |  |
| `0xabec0` | 4882 | 3 | 1049 | basic_string::append |
| `0x8afdb0` | 4805 | 2 | 1174 |  |
| `0x69aa40` | 4801 | 2 | 970 | ..\multi\nesting_context.cpp |
| `0x22ad80` | 4689 | 2 | 1083 | vector::reserve |
| `0x239e30` | 4684 | 2 | 930 |  |
| `0x79da0` | 4611 | 2 | 928 | basic_string::_M_construct null not valid |
| `0x697270` | 4602 | 2 | 1136 |  |
| `0x56b7d0` | 4548 | 2 | 953 | data@0x88dc80 |
| `0x71a370` | 4546 | 2 | 813 | data@0x7043a0 |
| `0x5bf1d0` | 4535 | 3 | 921 | test tools require to set DATA variable to a valid directory |
| `0x8a9510` | 4479 | 3 | 654 | .,-+xX0123456789abcdef0123456789ABCDEF-+xX0123456789abcdefABCDEF |
| `0x559d0` | 4316 | 2 | 723 |  |
| `0x6e50a0` | 4219 | 2 | 972 | Integer Division by zero. |
| `0x4d29d0` | 4203 | 2 | 883 | basic_string::_M_construct null not valid |
| `0x4d1950` | 4190 | 2 | 883 | basic_string::_M_construct null not valid |
| `0x693950` | 4157 | 3 | 770 | ..\multi\tiling_nester.cpp |
| `0x1192c0` | 4152 | 1 | 884 | UWVSH |
| `0x7f3090` | 4122 | 2 | 889 | data@0x9d9368 |
| `0x762900` | 4061 | 2 | 848 | data@0x9da2d8 |
| `0x1bd410` | 4054 | 3 | 866 | vector::reserve |
| `0x4cf000` | 4021 | 2 | 839 | basic_string::_M_construct null not valid |
| `0x4efc80` | 3996 | 3 | 744 | basic_string::_M_construct null not valid |
| `0x6585a0` | 3986 | 2 | 879 | data@0x7c2460 |
| `0x659540` | 3986 | 2 | 879 | data@0x7c2460 |
| `0x7f1b50` | 3983 | 4 | 755 | data@0x7d7d20 |
| `0x1bc4a0` | 3945 | 5 | 861 | vector::reserve |
| `0x65a8c0` | 3926 | 16 | 954 | map::at |
| `0x5c830` | 3923 | 2 | 809 | data@0x9b0900 |
| `0x173760` | 3892 | 5 | 900 | `$ck |
| `0x712740` | 3850 | 2 | 744 | data@0x701fc0 |
| `0x181e80` | 3842 | 4 | 926 | data@0x9bdf80 |
| `0x5a6be0` | 3840 | 2 | 700 |  |
| `0x5584b0` | 3833 | 4 | 756 | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x5eb470` | 3831 | 4 | 817 | vector::reserve |
| `0x16f350` | 3829 | 2 | 751 | basic_string::_M_construct null not valid |
| `0x251c00` | 3807 | 2 | 727 | data@0x24b790 |
| `0x74c9c0` | 3796 | 4 | 721 |  |
| `0x176a60` | 3764 | 2 | 882 | vector::reserve |
| `0x7d12a0` | 3762 | 3 | 801 | basic_string::_M_construct null not valid |
| `0x6fe060` | 3751 | 4 | 746 |  |
| `0x608f60` | 3745 | 2 | 829 | basic_string::_M_construct null not valid |
| `0x65cc50` | 3715 | 2 | 882 | ..\nesting\algos\tree_db.cpp |
| `0x174be0` | 3710 | 3 | 885 | vector::reserve |
| `0x5aa750` | 3691 | 2 | 656 |  |
| `0x565f80` | 3681 | 3 | 742 | data@0x88dc80 |
| `0x786e0` | 3676 | 2 | 819 | basic_string::_M_construct null not valid |
| `0x557660` | 3659 | 2 | 792 | vector::_M_default_append |
| `0x236bc0` | 3646 | 4 | 901 | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x16e140` | 3645 | 7 | 698 | basic_string::_M_construct null not valid |
| `0x86d9e0` | 3624 | 2 | 792 | data@0xa08320 |
| `0x7b6260` | 3610 | 5 | 702 | data@0xa02910 |
| `0x7ec9a0` | 3602 | 3 | 682 | data@0x7d7d20 |
| `0x6d4ad0` | 3574 | 3 | 795 | basic_string::_M_construct null not valid |
