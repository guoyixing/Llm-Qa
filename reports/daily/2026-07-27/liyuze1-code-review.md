# 代码审查日报

## 用户与范围

- 用户：李玉泽（liyuze1）
- 报告日期：2026-07-27
- 时区：Asia/Hong_Kong
- 审查窗口：2026-07-27 00:00:00（含）至 2026-07-28 00:00:00（不含）
- 实际过滤条件：未指定项目、提交、分支、文件或目录过滤；未指定 date/date-range，按日报默认前一自然日窗口执行
- 统计口径：同一 SHA 出现在不同注册项目时，按“项目—提交发生项”分别审查和计数

## 注册表快照与生效项目

- 注册表路径：`project-registry.yaml`
- 版本：`1`
- 本次冻结摘要：`ccdd8b03261294a494f5a5892468ec425d40b03ec11a9ab50644d3f840bd0646`
- 条目级错误：无

| 项目 ID | 名称 | 代码目录 | 规范目录 | 默认分支 | 仓库配置键名 | 启用 |
| --- | --- | --- | --- | --- | --- | --- |
| `hisense-ids-app` | 海信 IDS 应用 | `data/code/hisense-ids-app` | `standards/projects/hisense-ids-app` | `projectDevGroup` | `PROJECT_HISENSE_IDS_APP_REPO_URL` | 是 |
| `hisense-ids-app-spec` | 海信 IDS 应用-结构化分支 | `data/code/hisense-ids-app-spec` | `standards/projects/hisense-ids-app-spec` | `projectDevGroup-specTemplate` | `PROJECT_HISENSE_IDS_APP_SPEC_REPO_URL` | 是 |
| `hisense-ids-app-need` | 海信 IDS 应用-需求全链路分支 | `data/code/hisense-ids-app-need` | `standards/projects/hisense-ids-app-need` | `features-DDCP-8746` | `PROJECT_HISENSE_IDS_APP_NEED_REPO_URL` | 是 |
| `hisense-ids-app-function` | 海信 IDS 应用-方法库 | `data/code/hisense-ids-app-function` | `standards/projects/hisense-ids-app-function` | `features-DDCP-8522` | `PROJECT_HISENSE_IDS_APP_FUNCTION_REPO_URL` | 是 |

## 项目来源与实际提交

| 项目 ID | 状态 | 本地目录 | 固定提交 SHA | 说明 |
| --- | --- | --- | --- | --- |
| `hisense-ids-app` | 成功 | `data/code/hisense-ids-app` | `05cf93a3f3cf6e0429b5cc27b9a390ac435cd04b` | 仓库已仅快进同步。 |
| `hisense-ids-app-spec` | 成功 | `data/code/hisense-ids-app-spec` | `17252597a4f6a1206ebb3801c61498b1cc0d15e3` | 仓库已仅快进同步。 |
| `hisense-ids-app-need` | 成功 | `data/code/hisense-ids-app-need` | `3d514d6a9d16fc0d566d87552a7cf4437994963b` | 仓库已是最新状态。 |
| `hisense-ids-app-function` | 成功 | `data/code/hisense-ids-app-function` | `1461b36e5583bdc50327b9099d25f853b8a776db` | 仓库已是最新状态。 |

### `hisense-ids-app`

- `d9a8cbb0025c52ae4ea39fc683e3d66fdaf9c9af`

### `hisense-ids-app-spec`

该用户范围内无提交。

### `hisense-ids-app-need`

该用户范围内无提交。

### `hisense-ids-app-function`

该用户范围内无提交。

## 汇总

- 本次覆盖项目：4 个；该用户有提交项目：1 个
- 项目—提交发生项：1；唯一 SHA：1
- 发现合计：4
  - 代码规范：0
  - 可读性：0
  - 健壮性：3
  - 性能：1

## 发现

### 1. 配置型号状态同步失败被吞掉

- 项目：`hisense-ids-app`
- 提交：`d9a8cbb0025c52ae4ea39fc683e3d66fdaf9c9af`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/project/service/impl/DevProjectAssistServiceImp.java:923-1032；调用点：同文件:121-126,666-680`
- 规则或代码证据：公共规范 `ROBUST-004` / `STYLE-003` 要求失败必须通过异常、错误结果或明确部分失败状态传递，不能只记录日志后继续产生误导结果。新增 `syncConfigProductModelStatus` 在整个配置型号同步逻辑外层 `catch Exception` 后仅 `log.error` 并 `return Collections.emptyList()`；两个调用点只在返回非空时追加更新 ID，空返回会继续后续流程。
- 问题说明：配置产品型号状态同步失败被吞掉，并被伪装成“没有配置型号需要更新”。
- 影响：主产品型号已经完成开发/上市/作废等状态更新后，配置产品型号及其销售型号、生产版本可能未同步；外层事务和调用方无法感知部分失败，仍会继续推送已更新数据，形成生命周期状态不一致。
- 建议：不要在 `syncConfigProductModelStatus` 内吞异常；将失败转换为业务异常或明确的部分失败结果并由调用方决定回滚/中止/返回失败摘要。只有确认为无关联数据时才返回空集合。

### 2. 退市校验缺少名称行时空指针

- 项目：`hisense-ids-app`
- 提交：`d9a8cbb0025c52ae4ea39fc683e3d66fdaf9c9af`
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/masterdata/service/impl/DelistedFormServiceImpl.java:681-691`
- 规则或代码证据：公共规范 `ROBUST-001` 要求明确处理空值和缺失值。该处注释掉原有 `mapMDdata.get(key) == null || ... get("VALUE") == null` 防护后，下一行直接执行 `mapMDdata.get(key).get("VALUE").toString()`。
- 问题说明：退市校验中某个主数据缺少名称行或未出现在 `getAllMDNameByBizId` 结果里时，会直接触发空指针异常。
- 影响：原逻辑“没有名称不做后续校验”的受控分支被破坏，用户提交退市校验可能因单条异常数据整体失败，且异常信息不可定位到具体主数据。
- 建议：恢复按单项处理的空值分支；缺少名称时应跳过当前项或返回可识别的业务错误，并避免对 `mapMDdata.get(key)` 重复无保护解引用。

### 3. 配置整机反查读取软删除 IBA 属性

- 项目：`hisense-ids-app`
- 提交：`d9a8cbb0025c52ae4ea39fc683e3d66fdaf9c9af`
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/resources/META-INF/sql/master_data.sql.xml:2558-2564；使用点：DelistedFormServiceImpl.java:2320-2345,2765-2777`
- 规则或代码证据：公共规范 `ROBUST-001` 要求区分有效状态与缺失/无效状态。新增 SQL `getConfigProductModelByStandardMachine` 用 HX00287、HX00290、PG00061 等 IBA 值判定配置整机关系，但连接 `T_IBA_STRING_VALUE` 时未限制 `deleteFlag = 0`；同提交的 `getConfigModelsByStandardMachineIds` 在相同类型字段上显式过滤 `v1/v2/v3/v_name.deleteFlag = 0`。
- 问题说明：配置整机反查可能读到已软删除的标机型号、产品类别或名称属性。
- 影响：退市自动带出、导入冲突校验会基于过期 IBA 关系误带出配置整机/内外机或误报“不能同时导入”，导致当前有效数据被旧属性污染。
- 建议：为 `v_std`、`v_type` 以及用于展示或判断的 `v_name/v_cpxl/v_nwx` 增加与项目既有 SQL 一致的 `deleteFlag = 0` 过滤；必要时对同一属性多有效值做去重或唯一性处理。

### 4. 配置机型 baseId 传播循环内查库

- 项目：`hisense-ids-app`
- 提交：`d9a8cbb0025c52ae4ea39fc683e3d66fdaf9c9af`
- 类别：性能
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/masterdata/service/impl/DelistedFormServiceImpl.java:567-583`
- 规则或代码证据：公共规范 `PERF-001` 禁止在随输入集合增长的循环内逐项执行数据库查询。`propagateBaseId` 从 `listMap` 收集多个配置机型后，在 `for (Map.Entry...)` 内每个配置机型单独 `SqlCommandRepository.getSqlCommand("getIndoorOutdoorByConfigModelIds")` 并 `executeQueryForList`。
- 问题说明：配置机型 baseId 传播存在按配置机型数量线性增长的循环内数据库查询。
- 影响：退市列表中配置机型越多，数据库查询次数越多；该方法在组装退市数据和详情补充路径中调用，会放大页面/接口响应时间和数据库压力。
- 建议：一次性把 `configIdToBaseIdMap.keySet()` 组装为批量 IN 参数查询所有关联内外机，再在内存中按配置机型 ID 建索引回填 baseId。

## 规范加载与失败

- 规范加载顺序：`standards/common/`，随后加载各项目注册的 `standards_dir`。
- 规范冲突或降级：无；项目规则均为公共规则的补充。
- 注册表、同步、身份解析、规范读取和 Markdown 生成均无失败。
- `hisense-ids-app-need` 与 `hisense-ids-app-function` 在本窗口整体无提交。
- `hisense-ids-app-spec` 中该用户范围内无提交。
