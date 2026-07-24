# 2026-07-23 代码审查日报

## 用户与范围

- 用户：张金立（zhangjinli）
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

### `hisense-ids-app`

`6e9ddce0823f28b4608906d16e2a05e638e85166`

### `hisense-ids-app-spec`

`8f0ce94267b925e4f6f4ffdd5e893bc7be9d26eb`

## 汇总

| 指标 | 数量 |
|---|---:|
| 实际审查项目数 | 2 |
| 实际审查提交数 | 2 |
| 代码规范发现 | 3 |
| 可读性发现 | 2 |
| 健壮性发现 | 5 |
| 性能发现 | 2 |
| 发现总数 | 12 |

严重级别：`HIGH` 1 条、`MEDIUM` 7 条、`LOW` 4 条。

## 发现

### 6.1 类型名称未表达具体职责

- 项目：`hisense-ids-app`
- 提交：`6e9ddce0823f28b4608906d16e2a05e638e85166`
- 类别：代码规范
- 严重级别：`LOW`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/service/PositiveDecompositionServiceTwo.java:7`；`hisense-app/src/main/java/com/glaway/cost/service/impl/PositiveDecompositionServiceTwoImpl.java:28`
- 规则或代码证据：公共规则 `STYLE-001` 要求类型名称表达业务用途或技术职责；新增服务及实现仅用数字后缀 `Two` 区分已有服务。
- 问题说明：数字后缀没有表达按项目、阶段获取最新版本正向分解的职责边界。
- 影响：调用方难以根据类型名称选择正确服务，后续扩展容易继续形成无语义编号。
- 建议：按真实职责命名，例如 `ProjectLatestPositiveDecompositionService`，并同步实现类与注入字段名称。

### 6.2 捕获全部异常后未保留可诊断原因链

- 项目：`hisense-ids-app`
- 提交：`6e9ddce0823f28b4608906d16e2a05e638e85166`
- 类别：代码规范
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/controller/PositiveDecompositionController.java:96-97`
- 规则或代码证据：公共规则 `STYLE-003` 要求缩小捕获范围并在异常转换时保留根因；代码捕获宽泛 `Exception` 后只把 `e.getMessage()` 拼入错误响应。
- 问题说明：异常类型、堆栈和原因链在该边界丢失，不同故障被压缩为同一种不稳定文本响应。
- 影响：服务端难以定位根因，调用方也不能稳定区分失败类型。
- 建议：让未知异常进入统一异常处理器；只转换可预期异常，并在受控诊断链路保留完整原因和稳定上下文。

### 6.3 实现注释仅复述紧随其后的操作

- 项目：`hisense-ids-app`
- 提交：`6e9ddce0823f28b4608906d16e2a05e638e85166`
- 类别：可读性
- 严重级别：`LOW`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/service/impl/PositiveDecompositionServiceTwoImpl.java:43,56`
- 规则或代码证据：公共规则 `READ-005` 要求注释解释原因、约束或权衡；两条注释分别复述随后可直接读出的过滤排序查询和 DTO 组装。
- 问题说明：删除注释不会丢失任何不可从代码得知的信息。
- 影响：增加维护噪声，并产生注释与实现不同步的风险。
- 建议：删除复述性注释；如需保留说明，应解释版本选择或字段映射背后的约束。

### 6.4 HTTP 请求字段未在输入边界处理缺失与空值

- 项目：`hisense-ids-app`
- 提交：`6e9ddce0823f28b4608906d16e2a05e638e85166`
- 类别：健壮性
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/controller/PositiveDecompositionController.java:91-94`
- 规则或代码证据：公共规则 `ROBUST-001` 要求外部输入在首次可信边界区分缺失、空值和空字符串；代码直接解引用请求体并把 `projectId`、`stage` 传入查询。
- 问题说明：请求体或必要字段缺失、为空时没有明确参数错误路径。
- 影响：无效输入会进入查询层或产生非预期异常，调用方无法稳定识别参数错误。
- 建议：在请求边界校验请求体、`projectId` 与 `stage` 的非空及非空字符串约束，并返回稳定参数错误。

### 6.5 项目关联循环重复解析并推送同一规格书

- 项目：`hisense-ids-app-spec`
- 提交：`8f0ce94267b925e4f6f4ffdd5e893bc7be9d26eb`
- 类别：健壮性
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/specification/service/impl/GssIrTimePushServiceImpl.java:96-104`，辅助证据 `418-425`
- 规则或代码证据：`linkModels` 按同一 `projectId` 查询；循环中未使用当前关联对象的规格书标识，而是反复调用 `getSpecIdByProject(link.findProjectId())`。
- 问题说明：循环项没有决定实际处理的规格书，多关联时会反复解析同一项目级结果。
- 影响：可能重复推送同一规格书并遗漏其他关联规格书，重复产生外部副作用。
- 建议：从每个关联对象取得规格书标识，去重后每个规格书只推送一次。

### 6.6 生产版本循环内逐项串行调用外部接口

- 项目：`hisense-ids-app-spec`
- 提交：`8f0ce94267b925e4f6f4ffdd5e893bc7be9d26eb`
- 类别：性能
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/specification/service/impl/GssIrTimePushServiceImpl.java:199-222`
- 规则或代码证据：公共规则 `PERF-002` 和项目规则 `hisense-ids-app-spec-PERF-002`；无静态数量上限的有效生产版本在循环内逐项调用 `feignInterfaceService.pushGssPlanIrTime`。
- 问题说明：网络调用次数和总等待时间随生产版本数量线性增长并完全串行。
- 影响：扩大整体延迟、下游请求压力和部分失败概率，单项慢请求会阻塞后续项。
- 建议：优先使用批量接口；下游不支持批量时，设置明确数量上限、超时和受控并发，并汇总逐项结果。

### 6.7 未校验外部原始响应却向调用方返回成功

- 项目：`hisense-ids-app-spec`
- 提交：`8f0ce94267b925e4f6f4ffdd5e893bc7be9d26eb`
- 类别：健壮性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-interface/src/main/java/com/glaway/specification/service/impl/GssIrTimeInterfaceServiceImpl.java:60-75`；`hisense-interface/src/main/java/com/glaway/specification/controller/GssIrTimeController.java:53-56,71-74`
- 规则或代码证据：公共规则 `ROBUST-004` 和项目规则 `hisense-ids-app-spec-ROBUST-001`；`responseStr` 只被记录，未解析或校验业务状态与载荷，服务不抛异常时控制器直接返回成功。
- 问题说明：下游通过正文表达的空响应、业务失败或非法结构没有被转换为失败。
- 影响：真实外部失败可能被伪装成成功，调用方无法识别未完成状态。
- 建议：分层解析并校验响应包装、业务状态和必要载荷；失败时抛出可识别的脱敏领域异常，校验通过后才返回成功。

### 6.8 Controller 将异常原始消息直接返回外部

- 项目：`hisense-ids-app-spec`
- 提交：`8f0ce94267b925e4f6f4ffdd5e893bc7be9d26eb`
- 类别：健壮性
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-interface/src/main/java/com/glaway/specification/controller/GssIrTimeController.java:57-59,75-77`
- 规则或代码证据：项目规则 `hisense-ids-app-spec-ROBUST-001` 要求对外只返回稳定错误码或通用文案；两个异常分支都拼接并返回 `e.getMessage()`。
- 问题说明：错误响应依赖未经分类、未经脱敏的内部异常文本。
- 影响：下游或内部实现细节可能泄露，且形成不稳定的错误契约。
- 建议：内部日志脱敏保留根因；外部响应仅使用稳定错误码和通用文案。

### 6.9 空 `padDate` 仍进入实际 IR 时间请求

- 项目：`hisense-ids-app-spec`
- 提交：`8f0ce94267b925e4f6f4ffdd5e893bc7be9d26eb`
- 类别：健壮性
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/specification/service/impl/GssIrTimePushServiceImpl.java:114-117,159-164`，辅助证据 `474-479`
- 规则或代码证据：公共规则 `ROBUST-001`；入口只校验 `specId`，`formatDate(null)` 返回 `null`，随后仍调用 `pushGssActualIrTime`。
- 问题说明：缺失的实际完成时间没有在首次可信边界被拒绝或显式跳过。
- 影响：会发送包含空日期的外部请求，失败被推迟到下游且语义不明确。
- 建议：在外部副作用前显式拒绝或跳过空 `padDate`，并记录稳定的失败或跳过原因。

### 6.10 配置规格书查询未限制 `IN` 参数和结果规模

- 项目：`hisense-ids-app-spec`
- 提交：`8f0ce94267b925e4f6f4ffdd5e893bc7be9d26eb`
- 类别：性能
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/specification/service/impl/ConfigSpecBaseModelServiceImpl.java:528-539`
- 规则或代码证据：公共规则 `PERF-005` 和项目规则 `hisense-ids-app-spec-PERF-002`；全部 `configSpecIds` 一次进入单个 `IN`，并一次读取全部有效生产版本，未见分批、分页或硬上限。
- 问题说明：SQL 参数和返回集合规模随关联规格书及生产版本数量增长。
- 影响：数量较大时可能超过数据库参数限制，并增加大结果集读取与内存占用。
- 建议：去空、去重后按受控批次查询，逐批提取并合并结果，同时设置总条数或分页边界。

### 6.11 可执行语句使用无必要的全限定类名

- 项目：`hisense-ids-app-spec`
- 提交：`8f0ce94267b925e4f6f4ffdd5e893bc7be9d26eb`
- 类别：代码规范
- 严重级别：`LOW`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/specification/service/handler/SpecExternalPushHandler.java:429`
- 规则或代码证据：公共规则 `STYLE-005`；可执行语句直接使用 `com.glaway.infinite.container.holder.InfiniteContainerHolder`，补丁未显示简单类名冲突。
- 问题说明：无必要地绕过 import 区域使用全限定类名。
- 影响：破坏统一导入风格并增加语句噪声。
- 建议：导入 `InfiniteContainerHolder`，调用位置使用简单类名。

### 6.12 `productCode` 文档与实际取值来源不一致

- 项目：`hisense-ids-app-spec`
- 提交：`8f0ce94267b925e4f6f4ffdd5e893bc7be9d26eb`
- 类别：可读性
- 严重级别：`LOW`
- 文件与行范围：`hisense-common/src/main/java/com/glaway/value/specification/GssPlanIrTimeRequestValue.java:29-32`；`hisense-app/src/main/java/com/glaway/specification/service/impl/GssIrTimePushServiceImpl.java:205-212`
- 规则或代码证据：公共规则 `READ-006`；字段文档声明来源为 `productionVersionBizId`，实现实际使用 `findProductionVersionName()`。
- 问题说明：文档字符串声明的数据来源与装配代码不一致。
- 影响：维护者和接口使用方无法从代码确定字段的真实契约，后续修改可能采用错误来源。
- 建议：确认既定接口契约后，使字段文档与取值实现保持一致；本发现不判断哪一来源符合业务。

## 失败与降级

- 身份解析部分失败：`hisense-ids-app` 中以下提交无法唯一映射到规范用户，已跳过个人聚合、报告和投递：`744b475dab0a5b2acf5d9b91d003882feb8d892f`、`e91cbc952d894c612dcb5b22309b1cca11f8400b`、`e77270d3b25ed78ebc38be262d0f5098289ed089`、`e90ca0f57b1ad3f7bad3d615dbef7df1a2326407`、`273f8b66f417bab3ea5a1e2e5cb268838bd98e64`、`df362d25c7ea6c2be6078180a02350555241753d`。
- 同步、注册表绑定和规范读取均成功；公共规范与项目规范没有不可决冲突。
- 本报告仅陈述本次固定提交和可见差异的只读静态审查事实，不包含运行、测试或构建结论。
