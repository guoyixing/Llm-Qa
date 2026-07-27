# 代码审查日报

## 用户与范围

- 用户：邹宇宸（zouyuchen）
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

- `c1113bf97ecb985bc3b1b65b91fbfd6a2366f13c`
- `e982d32d96b458dfe97b12bf9f6b328686df69a1`
- `8df8951119ef14e3b508f83229586b1d7b1f6fff`
- `eaff2ddb6a86e97d69a2c126cc4e770df2da8372`
- `2f8ebd0c948ec26500e7a3628bd5a1741c0d605e`
- `251f083393621222ddece0310e36035e845e68a3`
- `3baeb424991759000bba632ad2a7dae79290b4c3`
- `e9e0d824ff548a12c068f5b8298414942b361d46`
- `8682b4931e90596ea1854f44c27b28bae6417ea7`
- `82154ffe7f231afaef2984c43502f1a950e2dd59`
- `f59e37bb18acb42c73ecafb7d80efbaf17306cd6`
- `f0433f8aeaad9f69cbf35c53dd13c0f37c3f54ea`
- `c3b90876ec9460f005ebf9ec5a0cca6fbab2f986`

### `hisense-ids-app-spec`

- `c1113bf97ecb985bc3b1b65b91fbfd6a2366f13c`
- `e982d32d96b458dfe97b12bf9f6b328686df69a1`
- `8df8951119ef14e3b508f83229586b1d7b1f6fff`
- `eaff2ddb6a86e97d69a2c126cc4e770df2da8372`
- `2f8ebd0c948ec26500e7a3628bd5a1741c0d605e`
- `251f083393621222ddece0310e36035e845e68a3`
- `3baeb424991759000bba632ad2a7dae79290b4c3`
- `e9e0d824ff548a12c068f5b8298414942b361d46`
- `8682b4931e90596ea1854f44c27b28bae6417ea7`
- `82154ffe7f231afaef2984c43502f1a950e2dd59`
- `f59e37bb18acb42c73ecafb7d80efbaf17306cd6`

### `hisense-ids-app-need`

该用户范围内无提交。

### `hisense-ids-app-function`

范围内无提交。

## 汇总

- 本次覆盖项目：4 个；该用户有提交项目：2 个
- 项目—提交发生项：24；唯一 SHA：13
- 发现合计：6
  - 代码规范：1
  - 可读性：0
  - 健壮性：3
  - 性能：2

## 发现

### 1. 客户端团队 ID 未与服务端可信范围求交集

- 项目：`hisense-ids-app`
- 提交：`82154ffe7f231afaef2984c43502f1a950e2dd59`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementAssistServiceImpl.java:274-288`
- 规则或代码证据：直接代码证据。当 `selectedTeamIds` 非空时，代码直接拆分并作为查询过滤值，未与 `planTeamConfigService.getTeamListId(currentUserId)` 或服务端生成的可见团队集合求交集。
- 问题说明：用户请求可达的团队范围由客户端值直接决定，服务端既有当前用户范围未参与收敛。
- 影响：知道其他团队 ID 的调用方可能读取其无权查看的需求池数据。
- 建议：从当前用户上下文取得允许团队集合，对请求 ID 规范化、去重后求交集；存在范围外 ID 时明确拒绝。

### 2. 挂起提交筛选了与接口契约相反的状态

- 项目：`hisense-ids-app`
- 提交：`82154ffe7f231afaef2984c43502f1a950e2dd59`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/requirement/service/impl/SuspendApplyServiceImpl.java:102-107,410-423`；`hisense-app/src/main/java/com/glaway/requirement/model/value/SuspendApplyItemValue.java:20-22`
- 规则或代码证据：公共规则 `ROBUST-002`。DTO 明确定义 `yes=挂起、no=取消挂起`，参数校验也按 `FLAG_YES` 判断挂起项，但提交实现只收集 `FLAG_NO` 项。
- 问题说明：校验和实际处理对同一状态采用相反语义。
- 影响：正常 `yes` 请求会得到空 ID 集合并失败，混合请求还可能把表示取消的项目送入挂起流程。
- 建议：提交和重提路径统一只选择 `FLAG_YES`，并对状态值做显式枚举校验。

### 3. 定时任务在双层循环中逐项发送邮件

- 项目：`hisense-ids-app`
- 提交：`82154ffe7f231afaef2984c43502f1a950e2dd59`
- 类别：性能
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/requirement/job/PlanReqPoolNotifyJob.java:118-166`
- 规则或代码证据：公共规则 `PERF-002`、`PERF-006`。每条分发记录内再次遍历负责人和管理员，并同步调用 `EmailUtil.sendEmail`；调用次数随“分发记录数 × 每团队通知人数”增长。
- 问题说明：网络邮件调用在外部数据驱动的双层循环中完全串行执行。
- 影响：数据和通知人数增长时，任务时长与邮件压力线性放大，单次慢调用也会阻塞后续全部通知。
- 建议：先按收件人或团队聚合，优先使用批量能力；必须逐项发送时使用有界并发、总超时和完整失败汇总。

### 4. 结构化分支中的挂起状态筛选相反

- 项目：`hisense-ids-app-spec`
- 提交：`82154ffe7f231afaef2984c43502f1a950e2dd59`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/requirement/service/impl/SuspendApplyServiceImpl.java:102-109`
- 规则或代码证据：公共规则 `ROBUST-002`。DTO 和校验以 `FLAG_YES` 表示挂起，实际 `submitSuspendApply` 使用 `FLAG_NO` 构造 `suspendIds`。
- 问题说明：合法挂起请求与实际处理条件相反。
- 影响：正常挂起请求无法发起，混合请求可能处理错误的分发路径。
- 建议：改为筛选 `FLAG_YES`，让提交与重新提交共用同一状态筛选函数，并拒绝未知状态。

### 5. 审批中申请被无界全量读取

- 项目：`hisense-ids-app-spec`
- 提交：`82154ffe7f231afaef2984c43502f1a950e2dd59`
- 类别：性能
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/requirement/service/impl/SuspendApplyServiceImpl.java:475-497`
- 规则或代码证据：公共规则 `PERF-005`。代码只按 `APPROVING` 和未删除过滤后直接 `.query()`，再把所有记录中的逗号分隔 ID 展开到内存；读取未按本次 `distributionPathIds` 收敛，也没有分页或条数上限。
- 问题说明：每次提交都会加载系统中全部审批中申请。
- 影响：查询量和内存占用随全局待审批数量持续增长，并发提交时进一步放大数据库和应用资源消耗。
- 建议：将关系规范化并按 ID 批量查询；至少增加数据库侧交集条件、索引和有界分页。

### 6. 新增代码直接书写全限定类名

- 项目：`hisense-ids-app-spec`
- 提交：`82154ffe7f231afaef2984c43502f1a950e2dd59`
- 类别：代码规范
- 严重级别：LOW
- 文件与行范围：`hisense-app/src/main/java/com/glaway/requirement/controller/InitialRequirementController.java:45-64`；`hisense-app/src/main/java/com/glaway/requirement/service/impl/PlanTeamConfigServiceImpl.java:375-552`；`hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementServiceImpl.java:152-159`
- 规则或代码证据：公共规则 `STYLE-005`。新增字段、局部变量和表达式直接使用 `com.glaway...`、`java.util...`、`cn.hutool...` 等全限定类型，未见简单类名冲突例外。
- 问题说明：类型引用没有集中到 import 区域。
- 影响：代码噪声增加，依赖难以集中识别，并违反强制编码规范。
- 建议：添加对应 import 并使用简单类名，仅在真实同名冲突处保留全限定名称。

## 规范加载与失败

- 规范加载顺序：`standards/common/`，随后加载各项目注册的 `standards_dir`
- 规范冲突或降级：无；项目规则均为公共规则的补充
- 注册表、同步、身份解析和规范读取均无失败。
- `hisense-ids-app-need` 中该用户范围内无提交；`hisense-ids-app-function` 整体范围内无提交。
- 除上述发现外，未生成证据不足的推测性结论。
