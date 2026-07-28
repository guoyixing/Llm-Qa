# 代码审查日报

## 用户与范围

- 用户：陶文秀（taowenxiu）
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

该用户范围内无提交。

### `hisense-ids-app-spec`

- `17252597a4f6a1206ebb3801c61498b1cc0d15e3`
- `0c2445c2a42f37715b424238e93731cce25354a8`
- `0035904f497d64fa9c182448be35a27960b31fe7`

### `hisense-ids-app-need`

该用户范围内无提交。

### `hisense-ids-app-function`

该用户范围内无提交。

## 汇总

- 本次覆盖项目：4 个；该用户有提交项目：1 个
- 项目—提交发生项：3；唯一 SHA：3
- 发现合计：3
  - 代码规范：0
  - 可读性：0
  - 健壮性：2
  - 性能：1

## 发现

### 1. 项目类型判断未处理项目不存在

- 项目：`hisense-ids-app-spec`
- 提交：`0035904f497d64fa9c182448be35a27960b31fe7`
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/specification/service/impl/ProjectSpecLinkServiceImpl.java:993-999`
- 规则或代码证据：`ROBUST-001`：查询结果、可选字段必须明确处理空值和缺失值。代码仅校验 `dto` 和 `productModelList` 后，直接对 `SearchRequestUtil.queryById(dto.getProjectId(), ...)` 的返回值执行 `projectModel.findTypeCode()`；同类方法 `queryProductModelsByProject` 在同文件 543-546 行对 `projectModel == null` 做了处理，说明该查询结果可为空。
- 问题说明：新增项目类型判断没有校验 `projectId` 为空或项目不存在的情况，可能在 `findTypeCode()` 处触发空指针，而不是返回可识别的业务错误。
- 影响：外部传入缺失、失效或已删除的 `projectId` 时，小类查询会以未受控异常失败，调用方无法区分参数错误、项目不存在和系统异常。
- 建议：在调用 `queryById` 前校验 `dto.getProjectId()`；查询不到 `ProjectModel` 时抛出明确 `BusinessException` 或按既有契约返回空结果，再读取 `findTypeCode()`。

### 2. Charter 产品型号循环内重复查库

- 项目：`hisense-ids-app-spec`
- 提交：`0035904f497d64fa9c182448be35a27960b31fe7`
- 类别：性能
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/specification/service/impl/ProjectSpecLinkServiceImpl.java:1003-1013,1056-1063,1150-1164,1458-1466,1797-1804`
- 规则或代码证据：`hisense-ids-app-spec-PERF-002` 要求规格书多行处理存在数据库读取时，应先收集受控批次内的 mdRel、BizId、属性编码或引用值，执行有界批量加载并建立索引；不得在行或属性循环中逐项访问数据库。公共 `PERF-001`/`PERF-004` 也禁止循环内数据库调用和重复计算不变量。代码在 `productModelList` 循环内每项调用 `findLatestCharterApplyId()`，该方法执行 `SearchRequestWrapper.query()`；同一循环内还逐项执行 `getCharterCategoryHierarchyByModelId` SQL。Charter 整机场景随后每项最多两次 `buildInOutUnit()`，其中 `queryCategoryHierarchyByModelBizId()` 和 `queryProductionVersionByBizId()` 均逐项执行 SQL。
- 问题说明：新增 Charter 路径把与 `dto.getProjectId()` 相关且在整个请求内不变的 applyId 查询放入产品型号循环，并对内/外机 BizId 和生产版本 BizId 逐项查库，形成随外部 `productModelList` 数量线性增长的多轮数据库访问。
- 影响：当一次导入或查询包含多个产品型号/内外机时，请求数据库调用次数按 N 或 2N 放大，容易造成慢查询、连接占用和接口响应抖动；重复查询同一 applyId 还浪费数据库资源。
- 建议：在循环前查询一次 applyId；收集所有 `modelId`、`modelBizId`、`productionVersionBizId` 后去空去重，使用批量 SQL/既有批量工具一次加载并按稳定键建 Map，再在循环内只做内存回填。

### 3. 编码前缀数据脚本保留未完成大类

- 项目：`hisense-ids-app-spec`
- 提交：`17252597a4f6a1206ebb3801c61498b1cc0d15e3`
- 类别：健壮性
- 严重级别：LOW
- 文件与行范围：`项目资料/sql/欧研产品分类树增加大类补充编码生成前缀新增数据.sql:3-4`
- 规则或代码证据：代码证据：新增 SQL 脚本中存在 `-- todo 电力设备:待补充id`，下一行对应 INSERT 被注释掉且 `LARGE_CATEGORY` 为空字符串。
- 问题说明：提交目标是为新增产品大类补充编码生成前缀，但脚本内保留了一个已知未完成的大类占位，且该 INSERT 不会执行。
- 影响：执行该脚本后，电力设备对应的编码前缀记录不会写入 `HISENSE_MD_SERIAL`；后续若该大类进入编码生成流程，将缺少前缀配置并产生不完整数据或运行时失败。
- 建议：补齐电力设备的大类 ID 并提交可执行 INSERT；若暂不纳入本次变更，应移除该 TODO 占位或拆成单独明确的后续变更，避免部署脚本携带已知未完成项。

## 规范加载与失败

- 规范加载顺序：`standards/common/`，随后加载各项目注册的 `standards_dir`。
- 规范冲突或降级：无；项目规则均为公共规则的补充。
- 注册表、同步、身份解析、规范读取和 Markdown 生成均无失败。
- `hisense-ids-app-need` 与 `hisense-ids-app-function` 在本窗口整体无提交。
