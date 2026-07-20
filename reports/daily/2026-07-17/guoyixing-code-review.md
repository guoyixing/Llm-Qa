# 每日代码审查报告

## 用户与范围

- 用户：郭一行（guoyixing）
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
- 实际审查提交（1）：`592f8ea61e8b3267e381366db2d64ca018575ed0`

### hisense-ids-app-spec

- 本次直接同步结果：成功，仓库已是最新状态
- 固定来源提交：`7487243ec8a1fdb084ba538a685fe74f56d0a044`
- 实际审查提交（3）：`f99b89066919ecfdde317344f26616f5098a22f1`、`7186a8b6d07a1f8e23dcbc58ffc2d5888929ffee`、`ffe257501a73d9496c3ad95d6dafe6a0362d8f65`

## 规范加载与失败

- 公共规范 `standards/common/` 的代码规范、可读性、健壮性和性能规则均已加载。
- `hisense-ids-app` 项目规范已加载，未发现覆盖冲突。
- 配置失败：`hisense-ids-app-spec` 的三个项目规范文件均声明适用于 `project_id=hisense-ids-app`，规则标签也使用 `hisense-ids-app-*`，与当前注册项目不一致；对该项目三个提交仅应用公共规则，项目规则确定性判断已停止。
- 身份解析失败：无；未归属提交：无。
- 同步失败：无；报告生成失败：无。

## 汇总

- 实际审查项目数：2
- 实际审查提交数：4
- 代码规范发现：0
- 可读性发现：0
- 健壮性发现：2
- 性能发现：1
- 严重级别：`HIGH` 2 条，`MEDIUM` 1 条
- 流程失败数：1 个项目规范配置降级

## 发现

### HIGH：异步提交失败后任务永久停留待处理状态

- 项目：`hisense-ids-app-spec`
- 提交：`7186a8b6d07a1f8e23dcbc58ffc2d5888929ffee`
- 类别：健壮性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/specification/listener/SpecExternalPushTaskCreatedListener.java:143-154`
- 规则或代码证据：公共规则 `ROBUST-004`、`ROBUST-009`。任务已在主事务中以 `PENDING` 落库；`AFTER_COMMIT` 监听器调用 `executeAsync` 时若线程池拒绝或代理提交异常，只记录错误并返回，没有把任务置为失败、保留未执行状态摘要或建立可靠补偿入口。
- 问题说明：提交线程池失败发生在事务提交之后，任务不会回滚，也不会由当前代码再次触发。
- 影响：调用方已获得批次号，但该批次会永久显示待推送且实际从未调用外部系统，形成不可恢复的假等待状态。
- 建议：异步提交失败时以独立事务把任务更新为明确的 `FAILED` 或“未执行”状态并记录脱敏原因；若业务要求最终投递，改用可持久消费的队列或受控补偿扫描，而不是仅依赖进程内事件。

### HIGH：外部返回不完整仍把推送任务标记成功

- 项目：`hisense-ids-app-spec`
- 提交：`7186a8b6d07a1f8e23dcbc58ffc2d5888929ffee`
- 类别：健壮性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/specification/service/handler/SpecExternalPushHandler.java:1328-1390`
- 规则或代码证据：公共规则 `ROBUST-004`、`ROBUST-009`。外部结果只要 `success=true`，代码就调用 `writeBackGssCode` 后无条件标记 `SUCCESS`；而回写函数对空结果、缺少生产版本 ID、缺少 GSS 编号和找不到本地生产版本的条目全部选择跳过。任务中已有 `pvCount`，但没有与有效回写数核对。
- 问题说明：外部整体成功与每个生产版本的可恢复结果没有建立一致性检查，部分失败被折叠为整体成功。
- 影响：部分或全部生产版本可能没有回写 `GSS_CODE`，任务却进入成功终态；后续不能区分已完成、失败和未知项，也无法安全补偿。
- 建议：以请求中的生产版本 ID 集合为基准校验响应完整性、唯一性和 GSS 编号非空；只在全部预期项成功回写后标记 `SUCCESS`，否则记录逐项结果并进入明确的部分失败或失败状态。

### MEDIUM：按项目循环执行多次数据库查询

- 项目：`hisense-ids-app`
- 提交：`592f8ea61e8b3267e381366db2d64ca018575ed0`
- 类别：性能
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/project/service/impl/DevProjectAssistServiceImp.java:353-370,407-487`
- 规则或代码证据：公共规则 `PERF-001`、`PERF-003`。`collectStatusBizIds` 对外部规模的 `devProjectList` 逐项调用 `queryApplyMasterDataBizIds` 或 `queryRootProjectMasterDataBizIds`；每次至少查询项目关联，非日立路径还继续查询主数据模型和子链接。
- 问题说明：数据库调用次数随项目数量线性增长，并且相同立项书可能被多个项目重复查询。
- 影响：批量生命周期更新时产生 N+1 数据访问，项目数增加会直接拉长事务和连接占用时间。
- 建议：先按公司和立项书分组，批量收集 `applyId`、`projectId` 和产品型号标识，一次查询关联与子链接后建立内存索引，再按项目回填；对重复立项书只查询一次。

## 结论

本次对该用户的 4 个提交完成四类只读静态审查，发现 2 条 `HIGH` 健壮性问题和 1 条 `MEDIUM` 性能问题。`hisense-ids-app-spec` 的项目规则因配置标识不一致而降级。
