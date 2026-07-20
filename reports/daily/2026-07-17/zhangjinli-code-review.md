# 每日代码审查报告

## 用户与范围

- 用户：张金立（zhangjinli）
- 时区：`Asia/Hong_Kong`
- 审查窗口：`[2026-07-17 00:00:00, 2026-07-20 00:00:00)`
- 实际过滤条件：`date-range=2026-07-17,2026-07-19`；未指定项目、提交、分支、文件或目录过滤

## 注册表快照

- 路径：`project-registry.yaml`
- 版本：`1`
- 快照摘要：`dade0daa14f9c931cbc8e3ab019bdf1947229a8853edb7337ffb877657016348`
- 生效项目：`hisense-ids-app`，名称“海信 IDS 应用”，代码目录 `data/code/hisense-ids-app`，规范目录 `standards/projects/hisense-ids-app`，默认分支 `projectDevGroup`，配置键名 `PROJECT_HISENSE_IDS_APP_REPO_URL`
- 生效项目：`hisense-ids-app-spec`，名称“海信 IDS 应用-结构化分支”，代码目录 `data/code/hisense-ids-app-spec`，规范目录 `standards/projects/hisense-ids-app-spec`，默认分支 `projectDevGroup-specTemplate`，配置键名 `PROJECT_HISENSE_IDS_APP_SPEC_REPO_URL`
- 注册表条目错误：无

## 项目来源与提交

### hisense-ids-app

- 本次直接同步结果：成功，仅快进同步
- 固定来源提交：`9832cb65de32cb08115cd34844ef480ed1209c4a`
- 实际审查提交（2）：`e81b4ba9c8e573ade57f7a39b77dda6fb1a545d6`、`253e69ac301a6f16769dd4774bd31b28751956c7`

### hisense-ids-app-spec

- 本次直接同步结果：成功，仓库已是最新状态
- 固定来源提交：`7487243ec8a1fdb084ba538a685fe74f56d0a044`
- 该用户在范围内无提交

## 规范加载与失败

- 公共规范 `standards/common/` 的四类规则均已加载；`hisense-ids-app` 项目规范已加载且无覆盖冲突。
- 配置失败：`hisense-ids-app-spec` 的三个项目规范文件声明了错误的适用项目和规则标签，本次仅应用公共规则。该用户在此项目无范围内提交，因此不影响其发现判断。
- 身份解析失败：无；未归属提交：无。
- 同步失败：无；报告生成失败：无。

## 汇总

- 实际审查项目数：1
- 实际审查提交数：2
- 代码规范发现：0
- 可读性发现：0
- 健壮性发现：1
- 性能发现：0
- 严重级别：`HIGH` 1 条
- 流程失败数：1 个项目规范配置降级

## 发现

### HIGH：历史处理人被永久授予金额字段权限

- 项目：`hisense-ids-app`
- 提交：`e81b4ba9c8e573ade57f7a39b77dda6fb1a545d6`
- 类别：健壮性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/service/impl/CostBomServiceImpl.java:3409-3475`
- 规则或代码证据：金额权限函数新增历史任务兜底：查询指定用户在该流程中的全部 `HistoricTaskInstance`，只要任一历史任务键存在于 `TASK_KEY_TO_USER_VAR` 就直接返回 `true`；没有校验该任务是否为当前节点、转办后的有效受让人、已被撤回，或当前用户是否仍具备对应角色。
- 问题说明：活跃任务当前 `assignee` 分支已经覆盖“转办后的人”；额外的历史任务分支把“曾经处理过”扩大成持续有效的金额访问授权。
- 影响：被转办走、被驳回后离开当前节点或仅在早期节点处理过流程的用户，仍可能导出金额字段，造成权限范围扩大。
- 建议：把授权绑定到当前活跃任务及有效候选/受让关系；如驳回场景确需历史信息，应同时校验当前流程位置、最新一次有效转办链和角色变量，不得仅凭任意历史任务命中返回成功。

## 结论

本次对该用户的 2 个提交完成四类只读静态审查，发现 1 条 `HIGH` 健壮性问题。项目规范配置另有 1 项与该用户提交无关的降级。
