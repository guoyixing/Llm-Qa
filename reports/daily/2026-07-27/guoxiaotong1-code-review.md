# 代码审查日报

## 用户与范围

- 用户：郭晓彤（guoxiaotong1）
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

- `ac7ad92a0a9d7c591ee7c01033916c66c12aa694`
- `f4f79d1314dacd04f9aaf1a26fb15fa64af606d4`
- `50c0b229e433af9b8b645efa6f222d8b791f87d8`
- `4c709221b790b4553b4eaaefa0f9a80158de6110`
- `a62f8bf7d53d8beeb1c2ad8cf9032c6a2e57a4cf`

### `hisense-ids-app-spec`

该用户范围内无提交。

### `hisense-ids-app-need`

该用户范围内无提交。

### `hisense-ids-app-function`

该用户范围内无提交。

## 汇总

- 本次覆盖项目：4 个；该用户有提交项目：1 个
- 项目—提交发生项：5；唯一 SHA：5
- 发现合计：4
  - 代码规范：0
  - 可读性：1
  - 健壮性：3
  - 性能：0

## 发现

### 1. SAP 地址缺失时直接调用 isEmpty 触发空指针

- 项目：`hisense-ids-app`
- 提交：`4c709221b790b4553b4eaaefa0f9a80158de6110`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-interface/src/main/java/com/glaway/cost/service/impl/CostInteractiveServiceImpl.java:39-41,109-111,174-176`
- 规则或代码证据：公共规范 `ROBUST-001` 要求明确处理空值和缺失值；合并提交将 SAP 地址校验写为 `if(sap.isEmpty())`。同一审查范围内上游多处在 SAP 地址缺失时仍 `setSAPADDRESS(sapAddress)`，因此 `sap` 可为 null。
- 问题说明：接口层在读取 `getSAPADDRESS()` 后直接调用实例方法 `isEmpty()`，没有先处理 null。缺失 SAP 地址时不会进入预期的 `BusinessException`，而是先发生空指针异常。
- 影响：BOM、标准工时、物料信息三类 SAP 路由在工厂未维护或上游传空地址时返回不可识别的系统异常，调用方无法得到稳定业务错误，问题定位也会被 NPE 掩盖。
- 建议：恢复使用 `StringUtil.isEmpty(sap)` 或显式 `sap == null || sap.isEmpty()`，并在进入路由前统一转换为带工厂信息的业务异常。

### 2. 物料信息接口未校验 INTAB 首项

- 项目：`hisense-ids-app`
- 提交：`4c709221b790b4553b4eaaefa0f9a80158de6110`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-interface/src/main/java/com/glaway/cost/service/impl/CostInteractiveServiceImpl.java:169-176`
- 规则或代码证据：公共规范 `ROBUST-001` 要求集合访问前明确处理空集合和缺失值；合并冲突差异中另一侧已有 `CollectionUtil.isEmpty(intab)` 校验，但最终代码直接执行 `querySapMatnrInfo.getINTAB().get(0)`。
- 问题说明：物料信息接口在访问 INTAB 首项前没有校验 `querySapMatnrInfo`、`INTAB` 是否为空或至少有一个元素。
- 影响：当调用方传入空 INTAB 或反序列化缺失该字段时，会发生 `NullPointerException`/`IndexOutOfBoundsException`，而不是返回“物料信息查询入参INTAB不能为空”的稳定业务错误。
- 建议：恢复先取局部变量并用 `CollectionUtil.isEmpty(intab)` 校验的结构；同时校验包装对象非空，再访问首项及其 SAP 地址。

### 3. 缺失 SAP 地址被记录后继续调用下游

- 项目：`hisense-ids-app`
- 提交：`a62f8bf7d53d8beeb1c2ad8cf9032c6a2e57a4cf`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/service/impl/CostBomServiceImpl.java:521-525,981-985,2868-2872；hisense-app/src/main/java/com/glaway/cost/service/impl/CostMachineNewBrandServiceImpl.java:379-386,1693-1697；hisense-app/src/main/java/com/glaway/cost/service/impl/CostMachineOldBrandServiceImpl.java:362-370；hisense-app/src/main/java/com/glaway/cost/service/impl/CostProcessDetailServiceImpl.java:244-259,917-930；hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostServiceImpl.java:581-586,739-748`
- 规则或代码证据：公共规范 `ROBUST-004` 要求失败必须通过异常或错误结果传递，不能只记录日志后继续产生误导结果；该提交把多处 `throw new BusinessException(...)` 改成 `log.error(...)`，随后仍把空 `sapAddress` 写入查询对象并继续调用 SAP/Feign 接口。
- 问题说明：代码已经确认“根据工厂查询不到 SAP 地址”这一非法状态，却只记录日志并继续构造请求。部分路径继续远程调用，端到端成本路径还会在接口失败时走 `result == null || !result.isSuccess()` 返回零值。
- 影响：缺失配置不再在源头中断，可能变成下游 NPE、错误路由、空结果，或在成本计算中被折算为 0，导致用户看到的错误位置和实际原因不一致，甚至产生错误成本数据。
- 建议：对缺失 SAP 地址恢复 fail-fast 的 `BusinessException`；若确需延后校验，也应在同一方法调用外部接口前返回明确失败，不得把空 SAP 地址继续传给下游或用零值掩盖失败。

### 4. 人工时路由重复空判断且错误文案不可达

- 项目：`hisense-ids-app`
- 提交：`4c709221b790b4553b4eaaefa0f9a80158de6110`
- 类别：可读性
- 严重级别：LOW
- 文件与行范围：`hisense-interface/src/main/java/com/glaway/cost/service/impl/CostInteractiveServiceImpl.java:124-130`
- 规则或代码证据：公共规范 `READ-003` 要求控制流直接表达主路径；当前代码连续两次判断 `requestCode.isEmpty()`，第一段抛“无法路由BOM接口”，第二段“无法路由人工时接口”永远不可达。
- 问题说明：人工时接口的空路由分支存在重复且前一个错误文案属于 BOM 接口。
- 影响：SAP 地址标识不支持时，人工时调用会返回错误领域的提示，误导排查方向；重复不可达分支也降低维护者对合并结果的可信度。
- 建议：删除重复分支，只保留一次人工时语义的错误处理：`无法路由人工时接口`。

## 规范加载与失败

- 规范加载顺序：`standards/common/`，随后加载各项目注册的 `standards_dir`。
- 规范冲突或降级：无；项目规则均为公共规则的补充。
- 注册表、同步、身份解析、规范读取和 Markdown 生成均无失败。
- `hisense-ids-app-need` 与 `hisense-ids-app-function` 在本窗口整体无提交。
- `hisense-ids-app-spec` 中该用户范围内无提交。
