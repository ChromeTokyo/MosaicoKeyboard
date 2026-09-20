# 参考资料

仓库保留 A0 生成脚本使用的器件库 JSON，以及官方资料入口。下载的 PDF、网页、抽取文本和渲染图片留在本地，不纳入 Git；后续可从来源重新获取。

## ESP-Mosaico

- [官方用户指南](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s31/esp-mosaico/user_guide.html)
- [CoreBoard V1.0 原理图，2026-08-18](https://dl.espressif.com/AE/SCH_SCH_ESP-Mosaico_CoreBoard_V1_0_2026-08-18.pdf)
- [BaseBoard 背面图片](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s31/_images/esp-mosaico-baseboard-back.png)

精确机械尺寸尚未冻结，详见 `docs/DESIGN_STATUS.md`。

## 候选器件原厂资料入口

| 器件 | 原厂入口 |
| --- | --- |
| BQ24074 | https://www.ti.com/product/BQ24074 |
| TPS61023 | https://www.ti.com/product/TPS61023 |
| TPS2553 | https://www.ti.com/product/TPS2553 |
| LM66100 | https://www.ti.com/product/LM66100 |
| TLV755P | https://www.ti.com/product/TLV755P |
| TCA9535 | https://www.ti.com/product/TCA9535 |
| TCA9517 | https://www.ti.com/product/TCA9517 |
| MAX17048 | https://www.analog.com/en/products/max17048.html |

后续审核应登记实际使用的数据表版本、页码及计算。上述候选器件尚未全部通过设计审核。

## EDA 与器件库缓存

- [EasyEDA 文档格式](https://docs.easyeda.com/en/DocumentFormat/EasyEDA-Document-Format/index.html)
- 器件库 JSON 来自公开接口，示例：`https://easyeda.com/api/products/C130204/components?version=6.4.19.5`。
- `C*.json` 中包含研究过程的候选、未采用及可能查询失败的记录。实际采用范围以审核后的 BOM 为准。
- JSON 缓存用于复现草案，不代表器件封装已核对或国内工厂可以采购、贴装。
