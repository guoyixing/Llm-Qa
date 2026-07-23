# 2026-07-22 代码质量审查日报

## 审查身份与范围

- 用户：朱林海（zhulinhai）
- 时区：Asia/Hong_Kong
- 审查窗口：2026-07-22 00:00:00（含）至 2026-07-23 00:00:00（不含）
- 实际过滤条件：当前注册表中全部有效且已启用项目；未指定提交、分支、文件或目录过滤
- 报告日期：2026-07-22

## 注册表快照

- 注册表路径：`project-registry.yaml`
- 版本：`1`
- 冻结摘要：`ccdd8b03261294a494f5a5892468ec425d40b03ec11a9ab50644d3f840bd0646`

| project_id | 项目名称 | code_dir | standards_dir | default_branch | repository_url_config_key | enabled |
| --- | --- | --- | --- | --- | --- | --- |
| `hisense-ids-app` | 海信 IDS 应用 | `data/code/hisense-ids-app` | `standards/projects/hisense-ids-app` | `projectDevGroup` | `PROJECT_HISENSE_IDS_APP_REPO_URL` | `true` |
| `hisense-ids-app-spec` | 海信 IDS 应用-结构化分支 | `data/code/hisense-ids-app-spec` | `standards/projects/hisense-ids-app-spec` | `projectDevGroup-specTemplate` | `PROJECT_HISENSE_IDS_APP_SPEC_REPO_URL` | `true` |
| `hisense-ids-app-need` | 海信 IDS 应用-需求全链路分支 | `data/code/hisense-ids-app-need` | `standards/projects/hisense-ids-app-need` | `features-DDCP-8746` | `PROJECT_HISENSE_IDS_APP_NEED_REPO_URL` | `true` |
| `hisense-ids-app-function` | 海信 IDS 应用-方法库 | `data/code/hisense-ids-app-function` | `standards/projects/hisense-ids-app-function` | `features-DDCP-8522` | `PROJECT_HISENSE_IDS_APP_FUNCTION_REPO_URL` | `true` |

## 项目来源与实际提交

| 项目 | 本次直接同步结果 | 固定提交 SHA | 本用户实际审查提交或跳过原因 |
| --- | --- | --- | --- |
| `hisense-ids-app` | 成功；仓库已仅快进同步 | `e7ad42440139ab31590658531b52376b1734fb67` | `f42b42aef2e4639c2760dc65ba393a94bb8c0016` |
| `hisense-ids-app-spec` | 成功；仓库已是最新状态 | `48a45a5af60416637d3c8cfdd7b67a1a1f96da99` | 范围内无提交 |
| `hisense-ids-app-need` | 成功；仓库已是最新状态 | `5e5752cd346beb33d17c169bd5f4a9c6bb34bad7` | 范围内无提交 |
| `hisense-ids-app-function` | 成功；仓库已是最新状态 | `1461b36e5583bdc50327b9099d25f853b8a776db` | 范围内无提交 |

## 规范加载与失败

- 本报告中的 1 个提交通过受信身份接口唯一映射到规范用户 `zhulinhai`，已校验姓名映射一致。
- 已按顺序加载 `standards/common/` 下四类公共规则，以及 `standards/projects/hisense-ids-app/` 下项目规则；未发现无法决断的规则冲突。
- `hisense-ids-app` 的提交 `34458b5b986863331e6f84c78a35cdac5092a628` 身份无法唯一解析，已按未归属提交处理，未纳入任何个人审查、报告或投递。

## 汇总

- 实际审查项目数：1
- 实际审查提交数：1
- 代码规范发现：0
- 可读性发现：1
- 健壮性发现：2
- 性能发现：0
- 严重级别计数：`MEDIUM` 1 条、`LOW` 1 条、`ADVISORY` 1 条

## 发现

### 1. NCD 操作码的配置说明与服务契约不一致

- 项目：`hisense-ids-app`
- 提交：`f42b42aef2e4639c2760dc65ba393a94bb8c0016`
- 类别：可读性
- 严重级别：`LOW`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/ncd/config/NcdProjectConfig.java:21-33`；`hisense-app/src/main/java/com/glaway/ncd/constant/NcdProjectConstants.java:23-35`；`hisense-app/src/main/java/com/glaway/ncd/service/NcdProjectService.java:124-130`
- 规则或代码证据：公共规则 `READ-006` 要求注释与当前实现一致。配置注释列出 `start/pause/resume/complete/cancel/plan`，实际白名单和查询键为 `doStart/doPause/doRestore/doComplete/doCancel`；接口注释又称参数包含 `projectId` 和 `planIds`，实现实际要求 `projectId` 和 `operationCode`。
- 问题说明：同一入口的操作码名称和必填参数在配置说明、常量及服务契约之间不一致。
- 影响：维护者可能按注释配置错误键名，调用方也可能遗漏 `operationCode`，增加配置缺失和参数非法的排查成本。
- 建议：以操作码常量为唯一来源同步配置说明；把接口参数说明改为 `projectId` 和 `operationCode`，并明确允许值及 `plan` 的独立使用场景。

### 2. 签署表编码缺失值会继续传给下游查询

- 项目：`hisense-ids-app`
- 提交：`f42b42aef2e4639c2760dc65ba393a94bb8c0016`
- 类别：健壮性
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/ncd/service/impl/NcdProjectServiceImpl.java:1201-1204,1253-1256,1283-1290`
- 规则或代码证据：公共规则 `ROBUST-001` 要求在首次可信边界区分并处理缺失和空值。概念项目计划路径在映射为空或缺少 `plan` 时产生 `null`；操作路径只检查 `map` 和 `containsKey`，键对应 `null` 或空白字符串时仍会继续。
- 问题说明：两条新增路径都没有在调用 `getSignTableByCode` 前确认 `signCode` 为非空、非空白的有效编码。
- 影响：错误或不完整的 Nacos 配置会把无效编码继续传播到签署表服务，得到不明确的空结果或下游失败，且错误边界难以定位。
- 建议：集中封装签署表编码读取，在配置边界统一执行非空和非空白校验；失败时在下游调用前抛出稳定、可识别的配置错误。

### 3. 操作码白名单暴露为可变全局集合

- 项目：`hisense-ids-app`
- 提交：`f42b42aef2e4639c2760dc65ba393a94bb8c0016`
- 类别：健壮性
- 严重级别：`ADVISORY`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/ncd/constant/NcdProjectConstants.java:34-35`
- 规则或代码证据：代码把 `conceptProjectKeys` 声明为公开、非 `final` 的静态 `List`；该字段可被整体替换，`Arrays.asList` 的元素也可通过 `set` 修改。当前证据没有显示实际写入者，因此仅作为建议。
- 问题说明：请求参数校验依赖可被其他代码修改的共享集合，白名单缺少不可变边界。
- 影响：未来的误修改可能在全局范围改变允许的操作码，使不同请求看到意外的校验结果。
- 建议：使用私有不可变 `Set` 或不可修改集合，并通过只读方法执行校验；常量字段至少声明为 `private static final`。

## 失败与降级

- 注册表、4 个所选项目同步、适用规范读取及本报告生成均无已知失败。
- 本次运行存在 1 个未归属提交：`hisense-ids-app` 的 `34458b5b986863331e6f84c78a35cdac5092a628`；该失败不影响本报告中 1 个已唯一归属提交的审查事实。
