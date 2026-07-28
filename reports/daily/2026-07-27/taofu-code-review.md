# 代码审查日报

## 用户与范围

- 用户：陶甫（taofu）
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

- `93dc232a95457cb600fdb9f730069dadbb3bed1f`
- `1621f1fbfb0bce9efa250f274e11ad4e0ff8859d`
- `73630967004aad53f7bca8af11698eb49249d845`
- `e896eef27e39114a1ede4db1f28953cff529054f`
- `865b318614f44ad9874a2d47c23e1b9d0e99e7cd`
- `777f3b41721cbf2245ba7c752b5d920015ab7fca`
- `306825e28e6691e24f4e3dba9c3138e87a4b9712`
- `ceb423d568b8d2ad15db058b61c4556ce99ef72b`
- `4060bc2c1f845129660ff0b752c0ff6ac801a07b`
- `1c57ec4c4051b00d5d3d6f2602069f6607bac58a`
- `285d3d765e31eeac489dc9c6393e584c88de0368`
- `96c94441b6435174e57437543a5c511e98cd6d08`

### `hisense-ids-app-spec`

该用户范围内无提交。

### `hisense-ids-app-need`

该用户范围内无提交。

### `hisense-ids-app-function`

该用户范围内无提交。

## 汇总

- 本次覆盖项目：4 个；该用户有提交项目：1 个
- 项目—提交发生项：12；唯一 SHA：12
- 发现合计：6
  - 代码规范：1
  - 可读性：2
  - 健壮性：3
  - 性能：0

## 发现

### 1. 规划销量主表总销量重复计入合计行

- 项目：`hisense-ids-app`
- 提交：`96c94441b6435174e57437543a5c511e98cd6d08`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/financeSector/planSale/service/impl/PlanSaleServiceImpl.java:379-382,565-642,929-943`
- 规则或代码证据：新增 `batchSave` 后调用 `recalculateTotalRow`；`recalculateTotalRow` 将合计行 `totalRow.putTotal(total)` 写成所有非合计行之和；随后 `updateTotalSalesVolume` 又遍历 `queryDetailBySalesId` 返回的所有明细并把每行 `findTotal()` 全部累加，没有排除 `IsTotalEnum.YES` 合计行。
- 问题说明：保存规划销量明细后，主表总销量会把非合计行之和与合计行再相加一次，导致总销量翻倍。
- 影响：每次 `batchSave` 成功后会持久化错误的主表 `totalSalesVolume`，影响端到端成本关键数据、审批/展示或后续计算中依赖主表总销量的结果。
- 建议：`updateTotalSalesVolume` 中排除合计行，或在重算合计行后直接用非合计行汇总值更新主表，避免同一合计被重复纳入。

### 2. TR1/TR3/TR6 早返回前已发布交付项

- 项目：`hisense-ids-app`
- 提交：`306825e28e6691e24f4e3dba9c3138e87a4b9712`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/service/impl/CostWorkFlowServiceImpl.java:205-235`
- 规则或代码证据：新增交付项发布循环位于 TR1/TR3/TR6 判断之前；代码随后仍保留注释和分支：`TR1 TR3 TR6由端到端成本关闭计划和交付物状态处理` 并直接 return。
- 问题说明：TR1/TR3/TR6 本应在进入交付物发布逻辑前返回，但新增代码先把非端到端结构化交付物置为 `RELEASED`，再执行阶段判断。
- 影响：被排除阶段仍会发生交付物状态写入，可能提前发布原本应由端到端成本流程处理的交付项，造成流程状态与实际责任边界不一致。
- 建议：将 TR1/TR3/TR6 及内销项目的早返回判断前置到任何交付物状态写入之前，或把新发布逻辑明确放入允许发布的分支内。

### 3. 交付项 structuredType 缺失时终止计划关闭

- 项目：`hisense-ids-app`
- 提交：`306825e28e6691e24f4e3dba9c3138e87a4b9712`
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/service/impl/CostWorkFlowServiceImpl.java:205-219`
- 规则或代码证据：`ROBUST-001` 要求明确处理查询结果和可选字段的空值；新增代码仅按 `planId/deleteMark/lifecycleState` 查询 `StructuredDeliveryModel`，随后直接调用 `item.findStructuredType().equals(E2E_STRUCT_TYPE)`。
- 问题说明：查询结果没有约束 `structuredType` 非空，任一交付项 `structuredType` 缺失时会在 `equals` 调用处触发空指针，终止后续计划关闭流程。
- 影响：单条脏数据或历史数据即可使整个 `updateBizCurrentFinish` 失败，导致成本计划和交付物状态停留在中间态。
- 建议：改为 `E2E_STRUCT_TYPE.equals(item.findStructuredType())`，并对 `structuredType` 缺失的交付项按明确策略跳过、失败或记录可定位诊断。

### 4. 企业所得税税率硬编码为 15%

- 项目：`hisense-ids-app`
- 提交：`73630967004aad53f7bca8af11698eb49249d845`
- 类别：可读性
- 严重级别：LOW
- 文件与行范围：`hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostServiceImpl.java:255-261`
- 规则或代码证据：`READ-004` 要求影响业务判断的数字必须命名或配置；新增代码注释写明“企业所得税税率…写死15%”，并直接 `new BigDecimal("0.15")`。
- 问题说明：企业所得税税率是业务税率，直接散落硬编码，缺少具名常量、配置或来源说明。
- 影响：税率调整或不同公司税率差异时必须修改代码；同一税率含义也难以与计划侧税率保持一致。
- 建议：提取为具名常量或配置项，并复用计划/实际同一税率来源；若确有固定 15% 的业务决策，应在常量命名或配置说明中标明来源。

### 5. 总期间费用释义未同步新公式

- 项目：`hisense-ids-app`
- 提交：`93dc232a95457cb600fdb9f730069dadbb3bed1f`
- 类别：可读性
- 严重级别：LOW
- 文件与行范围：`hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostCalcServiceImpl.java:606-613；hisense-app/src/main/java/com/glaway/ecost/enums/E2eCostItemEnum.java:87-88；hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostServiceImpl.java:2097-2098,2704-2705`
- 规则或代码证据：`READ-006` 要求注释/说明与当前实现一致；提交把总费用公式改为加 `initialTotal`，但 `TOTAL_PERIOD_EXPENSE` 的定义仍是“销售费用+研发费用（含专项投入）+管理费用”，且该 definition 会写入科目树并返回给版本详情。
- 问题说明：用户可见的科目释义仍描述旧口径，与当前计算公式中的“研发费用固定公共+初始投入总计”不一致。
- 影响：维护者和前端用户看到的计算口径与实际计算不一致，排查金额差异时容易按旧公式理解。
- 建议：同步更新 `E2eCostItemEnum.TOTAL_PERIOD_EXPENSE` 的 definition，使其与当前公式完全一致；已有初始化数据如需展示新释义，也应考虑迁移或刷新来源。

### 6. 正常交付项状态处理使用 error 日志

- 项目：`hisense-ids-app`
- 提交：`306825e28e6691e24f4e3dba9c3138e87a4b9712`
- 类别：代码规范
- 严重级别：LOW
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/service/impl/CostWorkFlowServiceImpl.java:228`
- 规则或代码证据：`STYLE-002` 要求日志级别与影响相符；新增代码在正常完成交付项状态处理后使用 `log.error("completeCostDeliveryByPlan流程节点计划关闭...")`。
- 问题说明：正常流程日志被记录为 error 级别。
- 影响：会污染错误告警和日志检索结果，掩盖真正失败；高频流程下还会增加运维噪声。
- 建议：将正常状态流转日志降为 info/debug；只有异常或明确失败时使用 error，并保留稳定业务标识。

## 规范加载与失败

- 规范加载顺序：`standards/common/`，随后加载各项目注册的 `standards_dir`。
- 规范冲突或降级：无；项目规则均为公共规则的补充。
- 注册表、同步、身份解析、规范读取和 Markdown 生成均无失败。
- `hisense-ids-app-need` 与 `hisense-ids-app-function` 在本窗口整体无提交。
- `hisense-ids-app-spec` 中该用户范围内无提交。
