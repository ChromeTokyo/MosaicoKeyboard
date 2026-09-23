# G4 证据笔记

行号指 `82df4c6534c3aa534e5ec67381e4a7767708c749` 上的文件，除另行注明的 `96fd823` 基线。

## 冻结点

```
origin/main                         96fd823e93f264280207eb34b7a97e139ace7378
origin/chrome/t14-v12-record        82df4c6534c3aa534e5ec67381e4a7767708c749
merge-base                          96fd823e93f264280207eb34b7a97e139ace7378
git diff --stat                     4 files, +140 / −27
git diff --check                    exit 0
gh pr view 55 .mergeCommit          null
gh pr view 55 .isDraft              true
```

`14186ea98e686e061f13291c85443e4ce64d0373`：

```
committer   GitHub
date        2026-09-23T00:08:09Z
parents     96fd823e93f264280207eb34b7a97e139ace7378
            82df4c6534c3aa534e5ec67381e4a7767708c749
tree        79ec0809bb27a6cf4830e13f9d6b91004a3448cb
head tree   79ec0809bb27a6cf4830e13f9d6b91004a3448cb
branches-where-head   （空）
```

本地 `git rev-parse --verify 14186ea98e686e061f13291c85443e4ce64d0373^{commit}` 在仅 fetch 了相关分支后失败。对象能从 GitHub commit API 读到，不能从 `origin/main` 或 `origin/chrome/t14-v12-record` 走到。头提交时间 2026-09-23T00:07:55Z，该预览提交晚 14 秒，提交者是 GitHub。

## 字段是否都有空栏

在头上的规程与记录表中检索，下列标识均为两侧都出现，记录表单元格无数字：

`P00a` `P00b` `P00c` `P00d` `P00e` `P00f` `Q01` `Q01a` `Q02` `Q03` `Q04` `Q05` `Q06` `Q07` `Q08` `Q09` `Q10` `Q11` `QRX` `QRY` `M0B1` `M0B2`

记录表末行仍是「G1 冻结：未完成」。左槽回填表五行的状态列都是「未测」。AS-02／03／04 在规程第 134 行和记录表第 143 行写明保持 OPEN。

## 链接

规程与记录表在该头上的仓库内相对链接均 `git cat-file -e` 通过，包括：

- `references/official-v12/README.md`
- `review/chrome/T14/video-20260920/README.md`
- `review/chrome/T14/MEASUREMENT_RECORD.md`
- `docs/INTERFACE_CONTROL.md`
- `review/claude/3mf-analysis.md`
- `review/claude/official-evidence/README.md`
- `docs/TEAM_PLAN.md`
- 记录表回指 `docs/MEASUREMENT_PROTOCOL.md`

`docs/handoffs/chrome.md` 中 `review/chrome/T02/REPORT.md` 的相对链接在基线 `96fd823` 已存在。本 PR 没有改那一行。该路径在 `96fd823` 的树里仍然不存在；这不是 T14 这次引入的断链。

## 左槽句子（正视与侧视）

规程第 133 行把标尺放置和「拍侧视说明刻线与可见孔口是否齐平」写在同一句。同段要求三张后缀 `_正视`、`_斜视`、`_定位`，没有写 `_正视` 必须含已标定刻线。第 119 行对七焊盘 `Q01` 要求两方向参照同镜入画。左槽正视没有对应句子。这是 G4-01 的文本依据。

第 102 行（第 4A 节，仅 V1.0 四触点）有「同一测量边对准两根刻线的同侧边缘」。第 119 行 QRX／QRY 没有复述。这是 G4-05 的文本依据。

## 假设表对照用的原句

均在 `96fd823:hardware/ASSUMPTIONS.md`，状态列均为 OPEN：

- AS-02 第 18 行：卡尺量相邻针中心距；pin 1 到 pin 19「应≈ 9 × 2.54 = 22.86 mm」
- AS-03 第 19 行：量母座开口相对外壳面的凹／凸深度
- AS-04 第 20 行：量 pin 1、pin 20 到 −Y 面和 +Z 面
- AS-05 第 21 行：回形针试吸；绝缘塑料探针轻试插入深度
- AS-17 第 33 行：万用表二极管档／通断档探 pin 20、pin 19

ICD 第 50–71 行（同一 SHA）：基准姿态为屏幕朝用户、原生 USB-C 朝下；左槽在 −X；「屏朝用户、USB-C 朝下、左槽在左」。
