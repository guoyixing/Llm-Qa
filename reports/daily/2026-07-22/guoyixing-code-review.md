# 2026-07-22 代码质量审查日报

## 审查身份与范围

- 用户：郭一行（guoyixing）
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
| `hisense-ids-app` | 成功；仓库已仅快进同步 | `e7ad42440139ab31590658531b52376b1734fb67` | `0922e29e2503398a24b4670225e838006d1de6c9`、`6bc7a8ec9ea39686d8b8d1e5357b26fdff64cdc2`、`03acf32aec5471a37467b4c0c83436eb3a7986e2` |
| `hisense-ids-app-spec` | 成功；仓库已是最新状态 | `48a45a5af60416637d3c8cfdd7b67a1a1f96da99` | 范围内无提交 |
| `hisense-ids-app-need` | 成功；仓库已是最新状态 | `5e5752cd346beb33d17c169bd5f4a9c6bb34bad7` | 范围内无提交 |
| `hisense-ids-app-function` | 成功；仓库已是最新状态 | `1461b36e5583bdc50327b9099d25f853b8a776db` | 范围内无提交 |

合并提交 `0922e29e2503398a24b4670225e838006d1de6c9` 的自身可见 combined diff 为空，未重复归入子提交的问题。

## 规范加载与失败

- 本报告中的 3 个提交均通过受信身份接口唯一映射到规范用户 `guoyixing`，已校验姓名映射一致。
- 已按顺序加载 `standards/common/` 下四类公共规则，以及 `standards/projects/hisense-ids-app/` 下项目规则；未发现无法决断的规则冲突。
- `hisense-ids-app` 的提交 `34458b5b986863331e6f84c78a35cdac5092a628` 身份无法唯一解析，已按未归属提交处理，未纳入任何个人审查、报告或投递。

## 汇总

- 实际审查项目数：1
- 实际审查提交数：3
- 代码规范发现：0
- 可读性发现：0
- 健壮性发现：1
- 性能发现：1
- 严重级别计数：`MEDIUM` 2 条

## 发现

### 1. 里程碑时间区间校验不完整

- 项目：`hisense-ids-app`
- 提交：`03acf32aec5471a37467b4c0c83436eb3a7986e2`
- 类别：健壮性
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/project/service/impl/ProjectReviewDCPServiceImpl.java:162-168,199-225`
- 规则或代码证据：公共规则 `ROBUST-002` 要求时间区间覆盖边界并保持端点关系一致。代码只检查开始时间是否早于父计划开始时间、结束时间是否晚于父计划结束时间，没有检查 `planStartTime` 是否晚于 `planEndTime`；同时调用处说明顶层计划应收敛于项目时间，但没有父计划 ID 的计划在第 207 至 210 行被直接跳过。
- 问题说明：开始时间晚于结束时间的倒置区间，只要两个端点分别落在父计划范围内就能通过；顶层计划也不会按调用处说明与项目时间比较。
- 影响：无效里程碑时间或越过项目时间边界的顶层计划可能通过启动流程前校验，使后续排期数据失去一致性。
- 建议：先显式校验 `planStartTime <= planEndTime`；对子计划按父计划边界校验，对顶层计划改用项目开始、结束时间校验，不要把无父计划直接视为无需校验。

### 2. 在里程碑循环内逐项查询计划和父计划

- 项目：`hisense-ids-app`
- 提交：`03acf32aec5471a37467b4c0c83436eb3a7986e2`
- 类别：性能
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/project/service/impl/ProjectReviewDCPServiceImpl.java:199-229`
- 规则或代码证据：公共规则 `PERF-001` 禁止在随输入集合增长的循环内逐项执行数据库查询。循环每次在第 207 行查询当前计划，并可能在第 213 行再次查询父计划。
- 问题说明：对包含 N 个里程碑的变更数据，当前实现最多发起约 2N 次计划查询。
- 影响：里程碑数量增大时，启动流程前校验的数据库往返次数线性增长，增加响应延迟和数据库压力。
- 建议：先收集并去重全部计划 ID，批量加载计划；再收集父计划 ID 批量加载并建立索引，循环内只做内存查找和时间比较。

## 失败与降级

- 注册表、4 个所选项目同步、适用规范读取及本报告生成均无已知失败。
- 本次运行存在 1 个未归属提交：`hisense-ids-app` 的 `34458b5b986863331e6f84c78a35cdac5092a628`；该失败不影响本报告中 3 个已唯一归属提交的审查事实。
