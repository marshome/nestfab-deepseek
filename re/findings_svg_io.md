# `..\structure\svg_io.cpp` —— SVG / HTML 报表 TU 的逆向记录

目标轮次：goal round 1。本节记录**已证实**的部分与**尚未逆向**的部分，两者不混。

## 0. 该 TU 的规模与入口

* TU 归属依据：`direct` 标注（`0x5100D0`、`0x510560` 自身引用 `..\structure\svg_io.cpp`）+ 传播。
* 规模：**218 个函数 / 224,234 字节**（其中本轮开始前已引用 61,548 字节 = 27.4%）。
* 导出入口（`trace` 名来自导出表）：

| ordinal | RVA | 名字 | 作用 |
|---:|---|---|---|
| 326 | `0x9550` | `NoFitGenerateSvgNesting` | 输出**排样结果**的 SVG（主路径） |
| 328 | `0x9790` | `NoFitGenerateSvgGeometry` | 输出**几何**的 SVG（`<use>`/`<defs>` 实例化变体） |

主写出器：**`0x7CCDF0`（16,831 字节）**。

## 1. 文档骨架（从 `0x7CCDF0` 的字符串按地址顺序读出）**[已证实]**

```
<?xml ...>
<svg width="<W>px" height="<H>px" viewBox="0 0 <W> <H>"
     xmlns="http://www.w3.org/2000/svg" version="1.1"
     xmlns:xlink="http://www.w3.org/1999/xlink">
  <defs><pattern id="diagonalHatch<N>" patternUnits="userSpaceOnUse"
                 width="<p>" height="<p>">
      <path d="M-1,1 l2,-2 M0,<p> l<p>,-<p> M3,5 l2,-2"
            style="stroke:rgb(...); stroke-width:0.1%; fill-opacity:0.7; stroke-opacity:0.7" />
  </pattern></defs>
  <g transform="scale(1,-1)">                 <-- 一次性地把布局 y 向上翻成 SVG y 向下
      <g transform="translate(<x>,<y>)"> ... </g>
      <g><path d="..."/></g>
      <g fill-rule="evenodd"><path d="..."/></g>
      <polyline points="..."/>
      <circle cx="..." cy="..." r="0.5%"/>
      <text style="...">...</text>
  </g>                                        <-- '</g></g>'
</svg>
```

逐条对应的字符串（均落在 `0x7CCDF0`）：

| 字符串 | 说明 |
|---|---|
| `'<svg width="'` / `'px" height="'` / `'px" viewBox="'` | 头，尺寸带 `px` 后缀 |
| `' xmlns="http://www.w3.org/2000/svg"'` `' version="1.1" '` `' xmlns:xlink="http://www.w3.org/1999/xlink">'` | 三个固定属性 |
| `'defs'` / `'<pattern id="diagonalHatch'` / `'" patternUnits="userSpaceOnUse" width="'` / `'" height="'` | 斜线填充图案 |
| `'"> <path d="M-1,1 l2,-2 M0,'` / `' l2,-2" style="stroke:rgb('` / `'); stroke-width:0.1%; fill-opacity:0.7; stroke-opacity:0.7'` / `'" /> </pattern>'` | 图案本体 |
| `'<g transform="scale(1,-1)">'` | y 翻转 |
| `'<g transform="translate('` / `'"/></g>'` | 逐件定位组 |
| `'<g><path d="'` / `'<g fill-rule="evenodd"><path d="'` / `';fill:none"/>'` | 轮廓/带孔轮廓 |
| `'<polyline points="'` / `'<circle cx="'` / `'" r="0.5%"'` / `'cy="'` / `'x="'` / `'y="'` | 其它图元；**mark 半径是百分比** |
| `'<text style="'` / `'</text>'` / `'transform="rotate(180, '` | 文本与旋转 |
| `'</g></g>'` / `'</svg>'` | 收尾 |

## 2. 样式词表（各风格助手，均为 4–8 条指令的字符串拼接器）**[已证实]**

| RVA | 片段 | 用途推断（依片段自身） |
|---|---|---|
| `0x5DAEB0` | `fill:none;stroke:black;stroke-width:0.1%` | 空心描边 |
| `0x5DDDD0` | `;fill:rgb(` … `);stroke:rgb(0, 0, 0);stroke-width:0.1%` | 实体填充 + 黑细边 |
| `0x5DC9D0` | `);stroke:rgb(0, 0, 0);stroke-width:0.2%` | 稍粗黑边（板材轮廓） |
| `0x5DC530` | `fill-opacity:0.8;fill:rgb(` … `);stroke:none` | 半透明无描边 |
| `0x5DE320` | `;fill:rgb(` … `);stroke:rgb(192, 0, 0);stroke-width:0.1%` | **标记用暗红** |
| `0x5DCE70` | `fill: url(#diagonalHatch` … `) ;stroke:rgb(` … `); stroke-width:0.1%; fill-opacity:0.7; stroke-opacity:0.7` | **斜线填充**（缺陷/不可用区） |
| `0x5D9BF0` | `;stroke-opacity:0.4;fill:rgb(128,128,128);stroke:rgb(0,0,0);` + `fill-opacity:` | **灰色半透明**（余料/offcut） |
| `0x516380` | `fill:white` / `fill-opacity:0.8;fill:black;stroke:black;stroke-width:0.1%` | 板材底色 / 深色叠加 |

## 3. HTML 报表侧（同一 TU）**[已证实存在，语义未逐一追]**

`0x5100D0` 与 `0x5190B0`/`0x51B560` 拼的是 HTML 片段：
`'<p>'`、`'</p>'`、`'<br>'`、`'multiplicity: '`、`'height: '`、`'fill-ratio: '`；
另有 `'<LINK rel=stylesheet type="text/css" href="'`（`0x6C6B20`）——对应工程里那个
`cns_solution.css` 资产。`0x24A1C0` 的 `'BEST='`/`'Checked='`/`' current='`/`' dp='`/`' dt='`/`'obj='`
是**跟踪/日志行**格式，不是 SVG。

## 4. 本轮落到工程的部分

`lcns::toSvg`（`src/engine.cpp`）由**我自创的格式**（`<polygon class="...">` + 自编 CSS）
改为**按上表恢复的格式**：

* 头：`px` + `viewBox` + `version="1.1"` + `xmlns:xlink`；
* `<defs><pattern id="diagonalHatch0" patternUnits="userSpaceOnUse">`（图案间距在二进制里是运行期数值 ⇒ 工程用 `kHatchPitch` 并在注释里标明"这是我们的取值"）；
* 外层 `<g transform="scale(1,-1)">`，逐板材 `translate` 组（翻转换算：`ty = -(yOffset + sb.max.y)`）；
* 零件用 `<g transform="translate(np.x,np.y)">` + `fill-rule="evenodd"` 路径（外环 + 内孔），与原库的
  "平移组 + 局部几何"一致；
* 板材 `fill:white` + `stroke-width:0.2%`；缺陷用 `fill: url(#diagonalHatch0)`；
* 标记 `<circle r="0.5%">` + `stroke:rgb(192, 0, 0);stroke-width:0.1%`
  —— 注意**半径是百分比**，所以 `Order::markSize` **不是**原库的半径来源（已在注释里写明）；
* 样式片段以 `kSvgPartFill`/`kSvgStrokeBlack`/`kSvgMarkStyle`/`kSvgHatchFill` 常量入库，每条注明 RVA。

测试：`tests/test_nester.cpp` 的 SVG 断言由"只查 `<svg>`"升级为逐项核对上表
（`px" height="`、`version="1.1"`、`xmlns:xlink`、`pattern id="diagonalHatch`、`userSpaceOnUse`、
`scale(1,-1)`、`translate(`、`fill-rule="evenodd"`、`stroke-width:0.1%`、`fill:white`）。

## 5. **尚未逆向**（本 TU 剩余约 169 KB）

| 项 | 地址/线索 | 状态 |
|---|---|---|
| `<use>` / `<defs>` 几何实例化变体 | 导出 328 `0x9790`；`0x7CB780` 含 `'use'`/`'xlink:href'`/`'transform'`/`'style'` | 未译 |
| HTML 报表的完整模板与统计口径 | `0x5100D0`、`0x5190B0`、`0x51B560` | 仅知片段 |
| 主写出器 `0x7CCDF0` 的控制流（16.8 KB / 3126 条指令） | 仅读出字符串顺序与调用面 | 未逐条转写 |
| 几何序列化细节（数值格式、`<polyline>`/`<text>` 的使用条件） | `0x7CCDF0` | 未译 |
| 该 TU 中标注为 `graph-*`（**假设**，非确证）的成员 | `0x6CC9D0`(18 KB, 疑为 libstdc++/反射)、`0x627850`(16.5 KB, `[abi:`) | 疑为传播串味，需复核 |

> 置信度提醒：本 TU 的成员来自 `direct`（确证）+ 传播（**假设**）。上表最后一行就是传播可能出错的例子，
> 复核方式是对该函数单独看其调用者是否真的落在 SVG 路径上。
