# 2026-07-23 代码审查日报

## 用户与范围

- 用户：桂庆乐（guiqingle）
- 时区：`Asia/Hong_Kong`
- 审查窗口：`2026-07-23 00:00:00`（含）至 `2026-07-24 00:00:00`（不含）
- 实际过滤条件：省略项目选择，使用全部有效且已启用项目；使用默认前一自然日；未指定 `commit`、`branch`、`file` 或 `directory`
- 注册表：`project-registry.yaml`，版本 `1`
- 冻结摘要：`ccdd8b03261294a494f5a5892468ec425d40b03ec11a9ab50644d3f840bd0646`

## 注册表快照与生效项目

| 项目 | 名称 | code_dir | standards_dir | default_branch | repository_url_config_key |
|---|---|---|---|---|---|
| `hisense-ids-app` | 海信 IDS 应用 | `data/code/hisense-ids-app` | `standards/projects/hisense-ids-app` | `projectDevGroup` | `PROJECT_HISENSE_IDS_APP_REPO_URL` |
| `hisense-ids-app-spec` | 海信 IDS 应用-结构化分支 | `data/code/hisense-ids-app-spec` | `standards/projects/hisense-ids-app-spec` | `projectDevGroup-specTemplate` | `PROJECT_HISENSE_IDS_APP_SPEC_REPO_URL` |
| `hisense-ids-app-need` | 海信 IDS 应用-需求全链路分支 | `data/code/hisense-ids-app-need` | `standards/projects/hisense-ids-app-need` | `features-DDCP-8746` | `PROJECT_HISENSE_IDS_APP_NEED_REPO_URL` |
| `hisense-ids-app-function` | 海信 IDS 应用-方法库 | `data/code/hisense-ids-app-function` | `standards/projects/hisense-ids-app-function` | `features-DDCP-8522` | `PROJECT_HISENSE_IDS_APP_FUNCTION_REPO_URL` |

以上项目均为 `enabled: true`，注册表没有条目级错误。

## 项目来源与提交

| 项目 | 状态 | 固定提交 SHA | 中文说明 |
|---|---|---|---|
| `hisense-ids-app` | success | `3a8ac1f8158e985ee987809e73e26d402fe511c3` | 仓库已仅快进同步。 |
| `hisense-ids-app-spec` | success | `d0e639c311f42d8fa8e7cc87e70bcd7d2b5773ad` | 仓库已仅快进同步。 |
| `hisense-ids-app-need` | success | `1e45405191d6e4afc3b35e04162dc7936c1b7408` | 仓库已仅快进同步。 |
| `hisense-ids-app-function` | success | `1461b36e5583bdc50327b9099d25f853b8a776db` | 仓库已是最新状态。 |

四项结果均与冻结注册表绑定一致。`hisense-ids-app-function` 在窗口内无提交。

## 项目来源与实际提交

### `hisense-ids-app-need`

`1e45405191d6e4afc3b35e04162dc7936c1b7408`、`88f5e4c2910da4796739ea4ba2b988efab106239`

其他项目在本窗口内没有归属于该用户的提交。

## 汇总

| 指标 | 数量 |
|---|---:|
| 实际审查项目数 | 1 |
| 实际审查提交数 | 2 |
| 代码规范发现 | 1 |
| 可读性发现 | 0 |
| 健壮性发现 | 3 |
| 性能发现 | 1 |
| 发现总数 | 5 |

严重级别：`HIGH` 2 条、`MEDIUM` 2 条、`LOW` 1 条。

## 发现

### 6.1 全限定类名绕过 import

- 项目：`hisense-ids-app-need`
- 提交：`1e45405191d6e4afc3b35e04162dc7936c1b7408`
- 类别：代码规范
- 严重级别：`LOW`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/requirement/service/impl/PlanTeamConfigServiceImpl.java:524-531`；`hisense-app/src/main/java/com/glaway/requirement/service/impl/PoolApplyServiceImpl.java:71`；`hisense-app/src/main/java/com/glaway/requirement/service/impl/SuspendApplyServiceImpl.java:57,71`
- 规则或代码证据：公共规则 `STYLE-005` 要求无名称冲突时通过 import 使用简单类名；新增代码直接书写多个全限定类名，补丁未显示简单类名冲突。
- 问题说明：类型引用绕过 import 区域，形成不一致的引用风格。
- 影响：方法签名和实现冗长，降低类型引用与依赖管理的一致性。
- 建议：导入对应类型并在使用位置改为简单类名，仅在确有同名冲突时保留全限定名。

### 6.2 客户端 ID 未经可信范围收敛

- 项目：`hisense-ids-app-need`
- 提交：`88f5e4c2910da4796739ea4ba2b988efab106239`
- 类别：健壮性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/requirement/service/impl/SuspendApplyServiceImpl.java:72-77,350-356`
- 规则或代码证据：项目规则 `hisense-ids-app-need-ROBUST-002` 要求用户请求中的对象 ID 与服务端可信范围取交集，禁止用无边界 `PermissionType.ALL` 代替范围约束；请求 ID 被直接用于禁用权限检查的查询。
- 问题说明：服务端只验证对象存在和状态，没有将调用者提交的 ID 收敛到可信允许范围。
- 影响：持有其他范围对象 ID 的调用者可能使其进入挂起申请流程。
- 建议：在服务入口从可信用户上下文取得允许范围，与请求 ID 求交；可信范围缺失或任一 ID 越界时关闭失败，再执行查询与写入。

### 6.3 重新提交值未更新持久化申请

- 项目：`hisense-ids-app-need`
- 提交：`88f5e4c2910da4796739ea4ba2b988efab106239`
- 类别：健壮性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/requirement/service/impl/SuspendApplyServiceImpl.java:146-170,194-200,281-284`
- 规则或代码证据：重新提交把新的分发路径、截止时间和原因写入流程变量，但详情查询和审批回调仍从原持久化申请模型读取这些字段；可见重提路径没有更新该模型。
- 问题说明：重提输入与详情及最终回调使用两个不同的事实来源。
- 影响：接口报告重提成功后，详情展示和最终挂起写入仍可能使用首次申请的旧值。
- 建议：重提时重新加载并校验申请，在同一受控写入边界更新持久化字段，后续详情和回调统一读取该持久化事实。

### 6.4 审批通过回调缺少当前状态守卫

- 项目：`hisense-ids-app-need`
- 提交：`88f5e4c2910da4796739ea4ba2b988efab106239`
- 类别：健壮性
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/requirement/service/impl/SuspendApplyServiceImpl.java:269-320`
- 规则或代码证据：项目规则 `hisense-ids-app-need-ROBUST-003` 要求工作流回调在状态写入前重新取得当前有效对象并校验当前状态允许动作；回调查询申请后只判空，未校验当前状态便更新分发记录并标记为已通过。
- 问题说明：回调没有明确的合法源状态守卫。
- 影响：重复、迟到或与撤回、驳回竞争的回调可能再次执行写入或覆盖终态。
- 建议：写入前校验当前申请状态，使用“申请 ID + 预期当前状态”的条件更新或等价原子状态转换；重复回调返回可区分的已处理结果。

### 6.5 外部 ID 集合缺少数量上限

- 项目：`hisense-ids-app-need`
- 提交：`88f5e4c2910da4796739ea4ba2b988efab106239`
- 类别：性能
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/requirement/service/impl/SuspendApplyServiceImpl.java:72-77,337-356`
- 规则或代码证据：公共规则 `PERF-005` 和项目规则 `hisense-ids-app-need-PERF-001` 要求外部集合具有条数或批次边界；输入集合只校验非空，随后整体进入 `IN` 查询和后续处理。
- 问题说明：任意规模的 `distributionPathIds` 可一次进入查询、内存、持久化和流程处理。
- 影响：集合增大时会放大 SQL 参数、内存集合、持久化字符串和单次处理时间。
- 建议：在入口设置明确且可配置的硬上限；超限时拒绝，或按固定批次处理并保留批次结果与失败语义。

## 失败与降级

- 身份解析部分失败：`hisense-ids-app` 中以下提交无法唯一映射到规范用户，已跳过个人聚合、报告和投递：`744b475dab0a5b2acf5d9b91d003882feb8d892f`、`e91cbc952d894c612dcb5b22309b1cca11f8400b`、`e77270d3b25ed78ebc38be262d0f5098289ed089`、`e90ca0f57b1ad3f7bad3d615dbef7df1a2326407`、`273f8b66f417bab3ea5a1e2e5cb268838bd98e64`、`df362d25c7ea6c2be6078180a02350555241753d`。
- 同步、注册表绑定和规范读取均成功；公共规范与项目规范没有不可决冲突。
- 本报告仅陈述本次固定提交和可见差异的只读静态审查事实，不包含运行、测试或构建结论。
