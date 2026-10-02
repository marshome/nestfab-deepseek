# re/DECISIONS.md -- every decision and every requirement, with the round it was made

## Why this file exists

The human asked how to stop repeating themselves, and the honest answer has two halves. A transcript is worth keeping, but a
transcript is not what stops the repetition: what stops it is that each requirement and each decision becomes a line here, in a
file a fresh session reads, with the round it was given so a new instruction is visibly new and an old one is visibly old.

So this file is append-only and short. One line per decision, one line per requirement, and the round. `re/g_note.py` appends
to it and to `re/RULES.md` when a requirement arrives, so recording is a command rather than an intention.

## The requirements, in the human's words, with the round they were given
| 548 | 本地打包备份，不 push：用 git bundle 加输入归档，origin 保持不动 |
| 548 | 授权连续推进，只在每 30 轮或遇到阻塞时汇报 |



| round | requirement |
|---|---|
| start | 继续逆向。先读 re/RESUME.md，用 re/ 下的工具，连续推进 |
| start | 门禁保持全绿 |
| start | 本地提交、不要 push |
| start | 当前目标见 re/LAUNCH_LOCAL_COMPUTATION.md |
| 529 | sub_6BACA620 是基础的报错函数，参数里可能有 file_name、method_name，能帮助解出大量函数 |
| 530 | 相关的引用的命名全部处理掉，顺藤摸瓜，一路处理下去 |
| 532 | 怎么全是 slot000 这种字段名称？找出这些结构体的字段名，从 html、json 或别的序列化代码里找线索 |
| 533 | 不要局限于一个导出函数，广泛地从各个方面找线索推进 |
| 538 | 每 30 轮和我同步一次 |
| 539 | 有的大结构体里可能直接包含其他小结构体，也可以发现出来，独立定义结构体 |
| 540 | 已经识别出结构体的，那些读写的地方就不要还用偏移值了 |
| 544 | 怎么能让你记住我说的各种要求，不需要每次都提醒 |
| 544 | 怎么能让你持续从各个角度寻找蛛丝马迹，推进函数、结构体、字段、变量、参数和 C++ 实现 |
| 546 | Order 和 LaunchingOrderLayout 是不是重复了，如果重复了，系统地检查一下所有 C++ 代码 |

## The decisions, and the evidence for each
| 546 | Order and LaunchingOrderLayout are duplicates, and the module's own stores decide which is right at each disputed offset | re/g_adjudicate.py: 20 offsets to the layout, 1 to Order, and that one was a layout defect already fixed |
| 548 | the human authorised continuous work with a report every thirty rounds or on a block | round 548, recorded in re/DECISIONS.md and as a rule in re/RULES.md |
| 548 | backups are a verified local bundle plus a tar of the inputs, never a push | re/g_backup.py produced a 7.23 MB bundle of 552 commits and a 25.03 MB tar, and a test clone from the bundle reproduced HEAD |




| round | decision | evidence |
|---|---|---|
| 526 | library code is CLASSIFIED and counted, never reimplemented | re/CATEGORIES.md, and the counting rule recorded there |
| 530 | a node's string is owned iff its pointer is not the node's own +0x30 | RE 0x9308C0 |
| 533 | a structure is found in its CONSTRUCTOR, not in the frequency of its offsets | RE 0x14620 settled a layout the frequency tools had got wrong |
| 535 | a field is NAMED only from an oracle or a setter whose name is the field's | re/LEDGER.md, two-witness rule |
| 538 | the reporting cadence is a program condition, not a note | re/g_rounds.py refuses a round at thirty |
| 540 | the module's own store decides a field's width | RE 0xD255 is movsd, so +0x010 is a double and not an integer |
| 545 | a callee's first-argument type is the caller's class when rcx carries it | re/g_types_propagate.py, 4486 functions typed by CALL |
| 546 | `Order` in model.hpp is a duplicate of `LaunchingOrderLayout` and is wrong where they disagree | re/g_adjudicate.py: the module agrees with the layout at 20 offsets and with Order at one, and that one is a width the layout then fixed |

## The open question about `Order`, recorded rather than acted on

`lcns/include/lcns/model.hpp` declares `struct Order` at line 175: 44 fields, 43 with offsets, describing the same object as
`LaunchingOrderLayout`. The two share 39 offsets and agree on only ONE of them in both name and width. The module adjudicates
the 21 width disputes at 20 to 1 in the layout's favour, and the single exception was a defect in the LAYOUT rather than a point
for `Order` -- `unnamed038` was declared eight bytes wide while RE 0xD0F8 writes one byte.

Replacing `Order` with the recovered layout is a large refactor of nester.cpp, engine.cpp and eight test files, and it is
deliberately NOT done in the round that found it. What is done is that the disagreement is measured, recorded with the addresses,
and enforced: a reader who touches either declaration now has `re/g_compare_type.py Order LaunchingOrderLayout` and
`re/g_duplicates.py` to see the whole picture in one command. The refactor is a task in the ledger, not a paragraph in a report.
