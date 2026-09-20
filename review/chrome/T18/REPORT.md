# T18 提案机制复核：CHANGES_REQUIRED

- 日期：2026-09-20；复核角色：Chrome（GPT-6 Astra／ultra）。本次是 Claude 提案的非作者机制复核，不是 Hiro 的独立硬件复核。
- 输入 main：`edb530106911997c894e3a2b7011a42153b0efef`；历史候选：`56030b99d3cc347e9f4b9d1ca2dd39f19c608198`。
- **结论：CHANGES_REQUIRED。** 六项机制／确定性预期得到复现，同时复现两项采纳前必须修复的问题。没有采纳 T18、关闭 F03 或批准硬件。

## 交付来源与复现边界

领取时远端 `claude/t18-reproducible-baseline` 停在 `94b30d5f09690a3c75d43d4a5e694d4e1e30147b`，仅有 D-012～D-014 与 T18／T19 领取声明，没有实现。真正实现曾随 `56030b9`／PR #10 误入 main，后由 `fd64da1`／PR #11 撤回。main 保留 Claude 的报告与对照产物；报告中“代码只存在于提案分支”的说法与该远端快照不符。

本次从 `56030b9` 原字节恢复生成器、policy、lock 到 [candidate/](candidate/)，以 [RECOVERY.json](RECOVERY.json) 记录来源、长度与 SHA-256。恢复件仅供复核，不是权威设计源，也未覆盖 `design/` 或 `references/`。

**不能在当前 main 直接执行 Claude 报告中的 `python3 design/build_design.py --out-dir …` 命令。** main 的旧生成器不解析这些参数，会写入自身仓库的 `design/`。也不要直接运行 `candidate/build_design.py`：其相对目录假设要求安装到隔离副本的 `design/` 下。

安全复现入口（从仓库根目录执行；结果打印到标准输出）：

```sh
python3 review/chrome/T18/check_proposal.py
```

[check_proposal.py](check_proposal.py) 从指定 main 导出 `design/`、`references/` 到临时目录，装入三份历史候选，再执行故障注入；退出前比较权威目录所有文件哈希。[check-results.json](check-results.json) 保存 Python 3.9.6 下的退出码、输出、哈希和逐位号结果。候选与历史原字节一致，权威目录运行前后未变。检查脚本退出成功仅表示这些观测得到复现。

## 已复现的机制

| 观测 | 结果及边界 |
| --- | --- |
| 无参数运行 | 退出 2，拒绝覆盖隔离副本的基线目录；输入未变 |
| 正常生成但 R26／C23239 未裁决 | 退出 1，明确报 R26，不产生输出 |
| 明确 `--allow-missing` 的研究输出 | 两次普通运行与一次 `python3 -O` 的五份文件逐字相同；与 Claude 已提交的 `regenerated/` 五份对照产物一致 |
| 删除已登记的 C45783 缓存 | 即使给 `--allow-missing` 仍因锁状态变化退出 1，不产生输出 |
| C25804 缓存追加一个换行 | 因 SHA-256 变化退出 1，不产生输出 |
| policy 删除 U3 条目 | 即使给 `--allow-missing` 仍退出 1，不产生输出 |

可保留的方向包括：缺失／无效缓存分开报告、按位号绑定 policy 与编码、缓存状态和哈希校验、显式输出目录与覆盖开关、统一行尾、优化运行不移除关键检查。读码确认编码不符、非法 policy，以及 `allow_placeholder` 仍引用不可用编码均有不可降级错误；这些额外路径本轮未另做故障注入。

上表的研究输出仅放行 R26，仍是草案。五份文件“与 Claude 对照产物一致”不等于“与 main 的五份设计产物一致”，也不证明 EDA 解析、电气连接或封装正确。

## R01：重新登记会清空人工审核字段（T18 新增行为）

位置：[candidate/build_design.py](candidate/build_design.py) 第 498–518、535–543 行。

触发：在 R28 的 policy 条目填写 `reason`、`placeholder_geometry`、`review_state` 三个哨兵值，然后运行 `--write-policy`。命令退出 0，前两项变成空串，审核状态变回“未审查”；没有保留原裁决。生成器重新推导整个骨架，未读取并合并已有清单。这是 T18 新增登记命令的行为；Claude 报告已承认该限制，本轮独立复现。

采纳前要求：默认保留已有条目的人工字段及 policy，仅补新位号；删除、编码变化、重置已有裁决必须显式处理。补充“已有人工裁决再次登记不丢失”的回归检查，然后才能开始逐行填写正式清单。

## R02：缺少必需焊盘的缓存仍可登记为可用（继承旧脚本不足）

位置：[candidate/build_design.py](candidate/build_design.py) 第 147–152、648–669 行；main 旧脚本第 209–220 行也只有单向 PAD 检查。

触发：只在临时副本中删除 C25804 封装内脚号 `2` 的一个 PAD，其余结构保留；运行 `--write-lock` 如实登记修改后的缓存，再运行 `--out-dir out --allow-missing`。两步均退出 0。生成的 R1～R17 共 **17 个电阻**都只有脚号 `1`，而各自设计引脚集合仍是 `1、2`；全部继续标为 `Supplier library geometry; final manufacturer audit pending`。

此例没有绕过缓存哈希检查：锁登记的是受损缓存的真实哈希。**`--allow-missing` 只放行 R26，受损 C25804 没有被识别为问题或降级放行**，17 个电阻的 BOM 状态也没有 `UNRESOLVED` 标记。问题在于解析只要求 `packageDetail` 非空，后续只验证“已有 PAD 的脚号属于设计”，未验证“全部应有物理引脚均有 PAD”。

该缺口继承自旧脚本，不能称作 T18 新引入的电路回归；但 T18 要建立“无效缓存硬失败”的可复现基线，锁定字节不足以证明结构有效，采纳前应补齐这个检查。

采纳前要求：按明确的物理引脚集合检查 PAD 覆盖，遗漏、额外脚号均阻断；同一脚号对应多个焊盘应允许。NC 电气脚仍需物理焊盘，纯机械焊盘例外必须显式声明。增加“已重新登记哈希的缺 PAD 缓存仍失败”的回归检查，不替代原厂封装核对。

## 后续决策与交接

1. 候选作者先修 R01、R02，再提交到可追踪的提案分支；本轮没有接管或改写 Claude 持有的权威生成器。
2. Chrome 后续裁决 R26／C23239、六份缓存冻结点、C5／C7／C8 及其余变更几何、U8 封装名，再填写 policy。当前缺失缓存不能靠 `--allow-missing` 变成已解决。
3. 生成器／policy 自身哈希变化目前仅提示；`reason`、`placeholder_geometry`、`review_state` 不作为生成闸门。这些是待 Chrome 明确的机制取舍，本轮不将草案生成等同于越过人工审核。应在采纳时明确草案生成与基线登记所需条件。
4. 本轮未实施 T19／F01 修复，未解决 F02，未做 ERC、DRC、EDA 导入、原厂封装或实物验证。规定的 Hiro 复核与放行链继续有效。
