# 每日代码审查报告

## 用户与范围

- 用户：张从辉（zhangconghui1）
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
- 实际审查提交（2）：`12a802c71e3acb3ae4491e796a0d0da5a553115f`、`2c32447aefb98b1790191093ffc4839297db912c`

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
- 严重级别：`MEDIUM` 1 条
- 流程失败数：1 个项目规范配置降级

## 发现

### MEDIUM：分页查询不再应用名称和状态过滤条件

- 项目：`hisense-ids-app`
- 提交：`2c32447aefb98b1790191093ffc4839297db912c`
- 类别：健壮性
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/financeSector/basicData/doorPanelConfig/service/impl/DoorPanelConfigServiceImpl.java:95-121`
- 规则或代码证据：变更删除了 `queryValue.getHdrpDictName()` 对应的 `like("hdrpDictName", ...)` 和 `queryValue.getStatus()` 对应的 `equals("status", ...)`，随后直接执行 `queryPage(paging)`；新增加的返回分页对象没有在内存中补做这两个过滤。
- 问题说明：接口仍接收包含名称和状态的查询对象，但两个非空条件被静默忽略。
- 影响：用户按名称或状态检索时会收到未过滤数据，`total` 和分页内容也基于错误范围；状态筛选失效时可能展示本应排除的记录。
- 建议：在分页查询前恢复两个条件，确保过滤发生在数据库分页之前；若接口契约已正式删除这些条件，应同步移除请求字段和调用方，避免继续接受但忽略输入。

## 结论

本次对该用户的 2 个提交完成四类只读静态审查，发现 1 条 `MEDIUM` 健壮性问题。项目规范配置另有 1 项与该用户提交无关的降级。
