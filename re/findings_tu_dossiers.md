
## TU 档案：`..\structure\stats.cpp`（goal round 95）**[逐函数带证据]**

本 TU 在**未引用领域**里有 **5** 个函数 / **8586** 字节。下表每行是一个函数及它**自己的证据**（字节数、指令数、被调用者数、调用者数、它自带的断言文本）。

| 函数 | 字节 | 指令 | 被调用者 | 调用者 | 自带文本 |
|---|---:|---:|---:|---:|---|
| `0x528020` | 2621 | 500 | 33 | 4 | `biggest`、`UsedSurfaceAux` |
| `0x528d10` | 2493 | 477 | 30 | 5 | `biggest`、`UsedSurfaceAux` |
| `0x52aad0` | 2294 | 498 | 34 | 2 | `sheet` |
| `0x525ef0` | 617 | 132 | 15 | 4 | `nesting.sheet()`、`FillRatio` |
| `0x527870` | 561 | 128 | 14 | 2 | `sheet`、`UsedSurfaceWithStairs` |

**口径**：TU 归属依据是函数**自带的字符串**；每行的其余列是该函数自身的结构事实。

## 调用图传播 TU 标签（goal round 96）**[推论，三类证据分开计数]**

种子：**自带 TU 路径**的可达函数 **151** 个（涉 **36** 个 TU）—— 这是**身份级**证据。

传播结果：**474** 个未引用函数 / **558015** 字节获得了标签，按证据分：

| 证据 | 函数 | 字节 |
|---|---:|---:|
| a | 190 | 105318 |
| b | 246 | 425036 |
| c | 38 | 27661 |

到达最多的 TU：`..\multi\nesting_context.cpp`(54)、`..\verify\equivalent.cpp`(47)、`internal.cpp`(43)、`..\nesting\algos\bucket_manager.hpp`(42)、`..\structure\svg_io.cpp`(26)、`..\structure\automatic_cluster.cpp`(21)

**口径**：这些标签是**推论**（调用图证据），**不等同**于“自带 TU 路径”的身份级证据；每个标签都带它的证据类型，存在 `re/tu_propagation.json`（生成物，不计入引用）。
