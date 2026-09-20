提案 · 未冻结 · 由 Hiro 独立复核（gpt-6-astra / high）起草 · 待主控处理修改项 · 不得据以制造

# H0 设计前提变更专项复核

- 任务：H0；负责人：Hiro，独立审查。
- 平台：Codex 本地桌面会话；实际模型 ID：`gpt-6-astra`；推理档位：`high`。
- 模型核验：本会话最近的 `turn_context` 运行记录（2026-09-20T23:12:17.768Z）中 `model` 与 `collaboration_mode.settings.model` 均为上述 ID，`effort` 与对应设置均为 `high`。仅登记字段，不上传会话原文。
- 领取日期：2026-09-21 08:13 JST。
- 已执行 fetch／fast-forward；领取时 `git rev-parse origin/main`：**`3aa71469c8a207b02acedbbb217bdd5ce0dacd83`**。下文全部仓库引用限定此基线，不追随移动的 main。
- 工作分支：`hiro/h0-premise-review`。
- 接口版本：ICD-0.2-DRAFT，未冻结；审查对象为 (a) 版本证据、(b) 方向更正、(c) Chrome D1；不审 A0 电路本身。
- 状态：IN_PROGRESS。尚未给出 PASS／CHANGES_REQUIRED／BLOCKED 最终结论。
- 写入范围：本报告与 `docs/handoffs/hiro.md`；其他文件只读。

## 审查进度

已读取派发包、材料索引及主控自述七项错误。正在独立核查原始图片、PDF 与固定提交源码；不采用被审作者的置信度标签作为证据。

2026-09-21 08:20 JST 中间检查已完成：PDF 第 2–4 页与裸板图已目视；D1 的 12 份 BSP 归档按 main 原始 Git blob 校验 SHA256／blob SHA1，并与官方固定提交 tree 比对一致（Windows 工作树换行差异不算源文件损坏）。H2 的 12 GPIO 集合与源码相等，与 I²S 交集为空；EEPROM 三段为 52／8／68 字节数据加各 2 字节 CRC，共 134 字节，CRC 参考输入 `123456789` 得 `0x4B37`。

发现需修改的论证：官方内侧焊接流程不排除其他外侧接口；grep 零命中不能证明从无软件支持；方案 G 常驻不能消除连接器几何与承力依赖；派发包 A-H0-4 错写带电测电阻。另从相同 BSP 固定提交补查 `onboard/esp_mosaico.c`，确认 eFuse 1.1 与 1.2 都映射到 variant V1_2，因此 variant 不能证明 BaseBoard 与指南 1.2.1 同版。最终分项结论与修改清单正在整理，尚无 PASS。
