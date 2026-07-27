# 代码审查日报

## 用户与范围

- 用户：桂庆乐（guiqingle）
- 报告日期：2026-07-24
- 时区：Asia/Hong_Kong
- 审查窗口：2026-07-24 00:00:00（含）至 2026-07-27 00:00:00（不含）
- 实际过滤条件：`date-range=2026-07-24,2026-07-26`；未指定项目、提交、分支、文件或目录过滤
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
| `hisense-ids-app` | 成功 | `data/code/hisense-ids-app` | `c3b90876ec9460f005ebf9ec5a0cca6fbab2f986` | 仓库已仅快进同步。 |
| `hisense-ids-app-spec` | 成功 | `data/code/hisense-ids-app-spec` | `5517ca5e0b2b9903b124ad1710327d1d5f0ab943` | 仓库已仅快进同步。 |
| `hisense-ids-app-need` | 成功 | `data/code/hisense-ids-app-need` | `3d514d6a9d16fc0d566d87552a7cf4437994963b` | 仓库已仅快进同步。 |
| `hisense-ids-app-function` | 成功 | `data/code/hisense-ids-app-function` | `1461b36e5583bdc50327b9099d25f853b8a776db` | 仓库已是最新状态。 |

### `hisense-ids-app`

- `f14efb058ef072577ef5258c84fc179d4cb79b8e`

### `hisense-ids-app-spec`

该用户范围内无提交。

### `hisense-ids-app-need`

- `2c09d99cf01c78b59067f8af8f14d0dfd01f02e3`
- `3d514d6a9d16fc0d566d87552a7cf4437994963b`

### `hisense-ids-app-function`

范围内无提交。

## 汇总

- 本次覆盖项目：4 个；该用户有提交项目：2 个
- 项目—提交发生项：3；唯一 SHA：3
- 发现合计：5
  - 代码规范：0
  - 可读性：1
  - 健壮性：4
  - 性能：0

## 发现

### 1. 顶层计划在修复前被过滤

- 项目：`hisense-ids-app`
- 提交：`f14efb058ef072577ef5258c84fc179d4cb79b8e`
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/plan/service/impl/PlanDeveloperTemplateImportExtendServiceImpl.java:367-379`
- 规则或代码证据：公共规则 `ROBUST-001`。修复服务允许以空串或 `null` 表示顶层分组并进行归一化，但调用方构造 `affectedParentIds` 时先执行 `filter(StringUtil::isNotBlank)`，顶层计划因此不会进入 `repairParents`。
- 问题说明：局部导入产生的顶层计划被排除在链路修复集合之外。
- 影响：顶层计划可能继续保留多个链头或断裂的 `prePlanId`、`nextPlanId`，使本次修复在顶层场景失效。
- 建议：保留空父 ID 并交由 `repairParents` 统一归一化，或使用明确的根分组标识，同时覆盖顶层与嵌套父计划两类输入。

### 2. 挂起提交筛选了与接口契约相反的状态

- 项目：`hisense-ids-app-need`
- 提交：`2c09d99cf01c78b59067f8af8f14d0dfd01f02e3`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/requirement/service/impl/SuspendApplyServiceImpl.java:102-112,409-424`
- 规则或代码证据：公共规则 `ROBUST-001`、`ROBUST-004`。前置校验以 `FLAG_YES` 识别挂起项，实际收集待挂起 ID 却筛选 `FLAG_NO`；同一提交中的 DTO 契约明确 `yes=挂起、no=取消挂起`。
- 问题说明：参数校验和实际处理对同一状态采用相反语义。
- 影响：仅包含正常 `yes` 项的请求会通过前置校验，但随后得到空 ID 集合并失败；混合请求还可能把 `no` 项送入挂起流程。
- 建议：提交、校验和重新提交统一按 `FLAG_YES` 收集待挂起项，并显式拒绝 `yes/no` 之外的值。

### 3. 更新入口绕过可信数据范围

- 项目：`hisense-ids-app-need`
- 提交：`3d514d6a9d16fc0d566d87552a7cf4437994963b`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/requirement/controller/PoolApplyController.java:67-77`；`hisense-app/src/main/java/com/glaway/requirement/service/impl/PoolApplyServiceImpl.java:267-301`；`hisense-app/src/main/java/com/glaway/requirement/controller/SuspendApplyController.java:65-74`；`hisense-app/src/main/java/com/glaway/requirement/service/impl/SuspendApplyServiceImpl.java:565-599`
- 规则或代码证据：项目规则 `hisense-ids-app-need-ROBUST-002`。两个用户请求可达的 `/update` 入口直接使用请求体中的 `procInstId`，查询显式使用 `PermissionType.ALL`，随后执行持久化更新；可见调用链未把目标与当前用户、申请人或服务端可信团队范围取交集。
- 问题说明：客户端流程实例 ID 被直接作为越过权限检查的写入定位条件。
- 影响：掌握其他申请流程实例 ID 的请求者可能修改不属于其可信范围的入池或挂起申请信息。
- 建议：在领域服务入口从当前用户和服务端团队上下文计算允许范围，并与 `procInstId` 同时作为查询约束；可信范围缺失时关闭失败。

### 4. “最新入池申请状态”缺少确定性排序

- 项目：`hisense-ids-app-need`
- 提交：`3d514d6a9d16fc0d566d87552a7cf4437994963b`
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementServiceImpl.java:672-680,836-916`
- 规则或代码证据：直接代码证据。实现对可能包含多条申请的两个查询均未按申请时间、创建时间、版本或稳定键排序；聚合时仅优先覆盖 `APPROVING`，多个其他状态则保留未定义遍历顺序中的首条。
- 问题说明：方法声明返回“最新”状态，但没有定义哪条记录代表最新。
- 影响：当同一需求存在多条非审批中申请时，结果依赖数据库未保证的返回顺序，可能展示非最新状态。
- 建议：明确稳定的时间与次级排序键，在数据库侧按需求分组选取最新记录，或在内存聚合前进行确定性排序。

### 5. Javadoc 与方法职责不一致

- 项目：`hisense-ids-app-need`
- 提交：`3d514d6a9d16fc0d566d87552a7cf4437994963b`
- 类别：可读性
- 严重级别：LOW
- 文件与行范围：`hisense-app/src/main/java/com/glaway/requirement/service/impl/PlanTeamConfigServiceImpl.java:497-569`
- 规则或代码证据：公共规则 `READ-006`。`getRequirementPoolList` 返回当前用户团队对应的需求池列表，但其 Javadoc 仍说明“获取团队类型的显示名称”，返回说明也与实际类型不符。
- 问题说明：新增方法继承了另一个方法的说明，注释与当前实现冲突。
- 影响：维护者和生成的接口说明会误解方法职责及返回内容。
- 建议：把原说明放回对应方法，并为 `getRequirementPoolList` 编写与需求池列表和返回类型一致的 Javadoc。

## 规范加载与失败

- 规范加载顺序：`standards/common/`，随后加载各项目注册的 `standards_dir`
- 规范冲突或降级：无；项目规则均为公共规则的补充
- 注册表、同步、身份解析和规范读取均无失败。
- `hisense-ids-app-spec` 中该用户范围内无提交；`hisense-ids-app-function` 整体范围内无提交。
- 除上述发现外，未生成证据不足的推测性结论。
