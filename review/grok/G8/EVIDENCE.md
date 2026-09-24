# G8 证据摘记

复核对象：PR #53 头 `85c1fb896ca32e9c256827e18b5ae165391d4e88`。基线 `96fd823e93f264280207eb34b7a97e139ace7378`。试合并 `753e818bf6e26fa82dc30ad97e206dfda7d4f7a4` 与头的树无差异。日期：2026-09-24。

## 三份输入的 SHA-256

本会话对取出的字节计算，与 `J2_CONTRACT_REPORT.md` 和测试常量相同。

| 文件 | 取自 | SHA-256 |
| --- | --- | --- |
| `review/chrome/D1-module-interface/LEFT_SLOT.md` | `origin/main` `96fd823` | `d7922f2106e388dd4a6648465b07724f59301751923405d55eba38aa5a2e55ca` |
| `hardware/module-board/PINMAP.md` | `94e393c` | `fc986a2c00b0f0f264136f228376064c790a2cc309e869f69441728322e03727` |
| `hardware/module-board/netlist.yaml` | `94e393c` | `70668e5391ebd599037322850c1e63e755cb35b44fdf27a7905d0472327179bf` |

## 检查器实跑

命令在临时目录执行，脚本字节来自 PR 头，输入是上表三份文件。PyYAML 6.0.1。

```text
FAIL: 7 处跨源不一致
- J2 封装行列 2×8 != PINMAP 4×4
- J2 封装节距/直径 2.54/1.8 mm != PINMAP 2.54/2.0 mm
- J2 pin_names 与 PINMAP 不同：缺 ['1A' … '4D']，多 ['A1' … 'B8']
- J3 必须为 2×8 @1.27 mm/Ø0.70 mm、16 位、12 个跨板网络的提案
- J3.pin_names 必须完整声明 r0.1…r1.8，且与 PINMAP §4.2 相同
- J2 网表接点集合不同：缺 ['1A' … '4D']，多 ['A1' … 'B8']
- J3 网表接点集合不同：缺 ['r0.1' … 'r1.8']，多 ['1' … '16']
```

退出码 1。上面两处名字列表在实跑中是完整的 16 个旧名和 16 个新名，此处用省略号只为缩短摘记；报告正文按完整集合理解。

`test_check_j2_contract.py`：`Ran 17 tests in 0.033s`，`OK`，退出码 0。

## 旧自检

`94e393c:hardware/module-board/check_netlist.py` 对其同目录网表：

```text
器件 41（DNP 17）；网 33；引脚 127
PASS
```

退出码 0。

## 网表端点与 J3 字段

| 项 | 值 |
| --- | --- |
| `J2.package` | `PAD-ARRAY-2x8-P2.54-D1.8` |
| `J2.pin_names` | `A1`…`A8`，`B1`…`B8` |
| `J3.package` | `CASTELLATION-1x16-P1.50-D0.70` |
| `J3.pins` | 16 |
| `J3.crossing_nets` | 14 |
| `J3.pin_names` | 无 |
| `DOCK_5V` 的 J2／J3 | `J3.1`、`J3.2`、`J2.A1`、`J2.B1` |
| `DOCK_GND` 的 J2／J3 | `J3.3`、`J3.4`、`J2.A2`、`J2.B2` |
| `DOCK_SDA` 的 J2／J3 | `J3.15`、`J2.A8` |
| `DOCK_SCL` 的 J2／J3 | `J3.16`、`J2.B8` |

J3 封装正则对上述 package 为假。`pins == 16` 为真。`crossing_nets == 12` 为假。

## 本会话额外探针

在作者的内存对齐控制上：

| 探针 | 结果 |
| --- | --- |
| `h2_contract.10 = GPIO14_WRONG` | 错误列表为空 |
| J1.13 从 `SLOT_USJ_DN` 改接到 `SLOT_KEY_UP` | `J1.13 网 ['SLOT_KEY_UP'] != SLOT_USJ_DN`；`SLOT_USJ_DN` 的 no-connect 检查失败 |
| `J3.package = BOGUS-2x8-P1.27-D0.70` | 错误列表为空 |
| PINMAP 句改为焊盘 `0.70 × 9.99 mm @1.27` | `parse_pinmap` 不报错 |
| YAML `{x: 1, x: 2}` | `ValueError`，映射键重复 |
| YAML 合并键 `<<` | `ConstructorError`，不接受覆盖 |

§4.2 与 §5.3 的 16 个 J3 位，网名和 J2 位逐格相同。

`git diff --check origin/main...85c1fb8` 退出码 0。
