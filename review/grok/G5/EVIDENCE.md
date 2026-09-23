# G5 核验记录

对象：`b15a0487f49010c3efdf75fe27ee62050fb59f48` 相对 `96fd823e93f264280207eb34b7a97e139ace7378`。

## 命令结果

- `gh pr view 56`：`state=OPEN`，`isDraft=true`，`baseRefOid=96fd823e93f264280207eb34b7a97e139ace7378`，`headRefOid=b15a0487f49010c3efdf75fe27ee62050fb59f48`，`mergeCommit=null`，additions 36，deletions 15，files 4。
- `git rev-parse --verify 3c6b25cc^{commit}` 与 `3c6b25c^{commit}`：退出码 128，`fatal: Needed a single revision`。
- `git merge-base 96fd823 b15a048` = `96fd823e93f264280207eb34b7a97e139ace7378`。
- `git diff --shortstat 96fd823...b15a048` = `4 files changed, 36 insertions(+), 15 deletions(-)`。
- `git diff --numstat`：`TASK_BOARD.md` 6/0，`handoffs/chrome.md` 11/0，`ASSUMPTIONS.md` 9/7，`ICD-0.2-DRAFT.md` 10/8。
- `git diff --check 96fd823...b15a048`：退出码 0，无输出。

提交（新到旧）：

```
b15a0487f49010c3efdf75fe27ee62050fb59f48 ae8116e docs: hand off arrival validation safety errata
ae8116e10fe4b4110d235cd982e3238d2aabed2f e239e5e T14: align ICD arrival checks with safe evidence path
e239e5e8717784f0efcb090d0d040f0aec0ac241 9e5d9a0 T14: make assumption verification first-round safe
9e5d9a0f18a2faa660a3e7f6d44d34f70228ecbf 96fd823 docs: claim arrival validation safety errata
```

## 假设表

解析规则：只取 `| AS-` 开头的行，按 `|` 拆列。结果 30 行，每行 8 列，编号 AS-01…AS-30，状态列全部 `OPEN`。

相对基线有列差异的行：

| 编号 | 改动列 | 状态 |
| --- | --- | --- |
| AS-02 | 到货验证步骤、器材、负责人 | OPEN |
| AS-03 | 到货验证步骤、器材、负责人 | OPEN |
| AS-04 | 到货验证步骤、器材、负责人 | OPEN |
| AS-05 | 到货验证步骤、器材、负责人 | OPEN |
| AS-06 | 到货验证步骤、器材 | OPEN |
| AS-17 | 到货验证步骤、器材、负责人 | OPEN |
| AS-24 | 到货验证步骤、器材 | OPEN |

其余 23 行八列与基线相同，状态 OPEN。

## ME-D

第 5 节表头 `| ID | 约束 | 假设编号 | 到货验证 |`。数据 11 行，每行 4 列。验证列有差异的是 ME-D-01、02、03、04、05、06、08。约束列与假设编号列无差异。

## 用词

在头版本两文件中：`曲别针` 无匹配。`回形针` 仅 AS-05、ME-D-05 的禁止句。`探针` 出现在新的禁止/边界句（假设表前言、AS-05、ICD 前言、ME-D-05），不出现在「请插入」类肯定句。`通断` 出现在边界说明、AS-17 的后续专项步骤，以及未改的 EL-D-05「G6-A6 通断」。
