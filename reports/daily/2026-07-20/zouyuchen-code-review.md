# 每日代码审查报告

## 用户与范围

- 用户：邹宇宸（zouyuchen）
- 审查窗口：2026-07-20 00:00:00（含）至 2026-07-21 00:00:00（不含）
- 时区：Asia/Hong_Kong
- 实际过滤条件：未显式指定项目、提交、分支、文件或目录；使用全部有效且已启用项目及默认前一自然日窗口

## 注册表快照与生效项目

- 注册表：`project-registry.yaml`
- 注册表版本：`1`
- 注册表摘要：`dade0daa14f9c931cbc8e3ab019bdf1947229a8853edb7337ffb877657016348`

| 项目 ID | 名称 | 代码目录 | 规范目录 | 默认分支 | 仓库配置键 | 启用 |
| --- | --- | --- | --- | --- | --- | --- |
| `hisense-ids-app` | 海信 IDS 应用 | `data/code/hisense-ids-app` | `standards/projects/hisense-ids-app` | `projectDevGroup` | `PROJECT_HISENSE_IDS_APP_REPO_URL` | 是 |
| `hisense-ids-app-spec` | 海信 IDS 应用-结构化分支 | `data/code/hisense-ids-app-spec` | `standards/projects/hisense-ids-app-spec` | `projectDevGroup-specTemplate` | `PROJECT_HISENSE_IDS_APP_SPEC_REPO_URL` | 是 |

## 项目来源与实际提交

| 项目 | 状态 | 固定提交 | 说明 |
| --- | --- | --- | --- |
| `hisense-ids-app` | 成功 | `d1ac2041e9ed9bfc19da71e9c44fe9bbf11c92a4` | 仓库已是最新状态。 |
| `hisense-ids-app-spec` | 成功 | `33a47c37709de6094d5f0cdc1eccbf987d80e4ce` | 仓库已是最新状态。 |

### 实际审查范围

- 审查项目数：1
- 审查提交数：20
- `hisense-ids-app-spec`：本用户在窗口内无归属提交
- `hisense-ids-app` 提交：
  - `9832cb65de32cb08115cd34844ef480ed1209c4a`
  - `b90d3b102371b219a582344f9f97a3fd4536dff5`
  - `3502dfba9decff1c1d8e15e615266e7259e17d56`
  - `cc3546b715c086aded307e7223f1f7e43398646a`
  - `9e46efd32d2e896bc990716947dbbe9a18f11d31`
  - `0161373440d06a93ef62588caeb1bba7d5ed18f9`
  - `7e029587914fb98f0236d0b4721dd8ae54d7cb71`
  - `f39115d84c02f82af9bccbe11e8057c91ebf3734`
  - `403ea8f5808bb10e169f4bb35aec90fb4c6aeaee`
  - `a9734441a4e5a1e61e7f71ab6d2aefa7b0a2966c`
  - `55d1743b9484c8ff8a403b9cff0bb6dbb94bed90`
  - `4440243a172812483c7fbbadd53dc18fc79d37aa`
  - `d187844ba17d052fa24128aa1199f9a169ec8471`
  - `1389979987d394becb20f72585db05faf60d59e8`
  - `2733264ff13df58a7ed67831c89dab72c953fa77`
  - `4820f088a3c1faa06ba0d4913452ccd3c0292c14`
  - `342bdd83317e57361029acf5629e9cb06e11022d`
  - `a5e4adbe6f547329f27866a9012e636a1e0deac8`
  - `5614a528b9d07981af33bd98e9fb40c85e223bdc`
  - `d1ac2041e9ed9bfc19da71e9c44fe9bbf11c92a4`

`55d1743b9484c8ff8a403b9cff0bb6dbb94bed90` 的变更在同一窗口被 `4440243a172812483c7fbbadd53dc18fc79d37aa` 完整回退，未对已回退代码重复生成发现。

## 汇总

| 类别 | 发现数 |
| --- | ---: |
| 代码规范 | 0 |
| 可读性 | 2 |
| 健壮性 | 3 |
| 性能 | 1 |
| 合计 | 6 |

## 发现

### 1. 实际费用请求固定使用另一项目编码

- 项目：`hisense-ids-app`
- 提交：`7e029587914fb98f0236d0b4721dd8ae54d7cb71`（引入），`f39115d84c02f82af9bccbe11e8057c91ebf3734`（合入）
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostServiceImpl.java:301-310`
- 规则或代码证据：公共规则 `ROBUST-001`、`ROBUST-004`，来源 `standards/common/robustness.md`。代码已从当前模型读取 `project.findProjectCode()`，但请求参数仍固定写入字符串 `BCYSCPXM2026010005`。
- 问题说明：所有项目拉取实际费用时都查询固定项目的数据，而后续处理仍以当前项目和当前版本保存结果。
- 影响：任意非该固定项目调用 `fetchActualData` 时，费用明细和汇总可能被错误项目的数据污染，属于跨项目数据错配。
- 建议：使用已校验的 `projectCode` 作为请求参数；为空时返回可识别失败并停止写入，不得使用固定项目编码兜底。

### 2. 外部管报失败被伪装为合法空结果

- 项目：`hisense-ids-app`
- 提交：`7e029587914fb98f0236d0b4721dd8ae54d7cb71`（引入），`f39115d84c02f82af9bccbe11e8057c91ebf3734`（合入）
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-interface/src/main/java/com/glaway/ecost/service/impl/E2eCostInterfaceServiceImpl.java:34-68`；`hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostServiceImpl.java:246-283,301-313`
- 规则或代码证据：公共规则 `ROBUST-004`，来源 `standards/common/robustness.md`。接口配置缺失、空响应和下游失败均返回空集合；调用方仅记录“无数据”并继续后续更新，最终返回成功数值 `0`。
- 问题说明：合法无数据与外部系统失败不可区分，部分数据未刷新时仍被视为完整成功。
- 影响：管报配置错误、服务失败或空响应时，旧实际值可能保留，其他科目仍继续更新，调用方无法识别不完整结果。
- 建议：使用领域异常或显式结果状态区分合法空结果与失败；失败时中止本次实际值更新并返回稳定、脱敏的错误。

### 3. 同一参数在筛选分支中使用了不同持久化字段

- 项目：`hisense-ids-app`
- 提交：`7e029587914fb98f0236d0b4721dd8ae54d7cb71`（引入），`f39115d84c02f82af9bccbe11e8057c91ebf3734`（合入）
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostServiceImpl.java:886-913`
- 规则或代码证据：公共规则 `ROBUST-002`，来源 `standards/common/robustness.md`。方法参数名和注释均为 `versionDataId`；无 `itemCode` 时查询 `versionDataId`，有 `itemCode` 时却查询 `versionId`。
- 问题说明：是否携带科目编码改变了同一标识的数据库字段语义。
- 影响：携带 `itemCode` 查询时通常返回空结果；若不同字段值偶然相同，还可能返回错误版本范围的数据。
- 建议：始终先按 `versionDataId` 定位明细，再追加科目条件；如确需版本 ID，应增加独立且命名明确的参数。

### 4. 详情加载形成版本与任务两层 N+1 查询

- 项目：`hisense-ids-app`
- 提交：`7e029587914fb98f0236d0b4721dd8ae54d7cb71`（引入），`f39115d84c02f82af9bccbe11e8057c91ebf3734`（合入）
- 类别：性能
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostServiceImpl.java:142-156,2548-2574,2625-2638`
- 规则或代码证据：公共规则 `PERF-001`、`PERF-003`，来源 `standards/common/performance.md`。详情遍历每个版本；每个版本单独查询任务，每个任务再查询任务行，并为每个版本单独查询 DATA。
- 问题说明：查询次数至少为 `1 + 2V + T`，其中 `V` 为版本数、`T` 为任务数。
- 影响：项目历史版本和任务数量增长时，详情接口数据库往返线性放大，增加响应延迟与数据库负载。
- 建议：按全部 `versionId` 批量加载任务和 DATA，再按全部 `taskId` 批量加载任务行，建立 `versionId`、`taskId`、`itemId` 索引后组装。

### 5. 注释保留已停用的完整请求日志代码

- 项目：`hisense-ids-app`
- 提交：`b90d3b102371b219a582344f9f97a3fd4536dff5`
- 类别：可读性
- 严重级别：LOW
- 文件与行范围：`hisense-interface/src/main/java/com/glaway/masterdata/controller/MdgController.java:36,51`
- 规则或代码证据：公共规则 `READ-005`，来源 `standards/common/readability.md`。两条原 `log.info(...)` 语句仅被改成注释，没有关闭原因、恢复边界或移除条件。
- 问题说明：死代码式注释无法说明该日志是否应恢复，并在生产入口附近保留了记录完整请求体的便捷开关。
- 影响：维护者可能在排障时直接恢复完整请求日志，重新引入大对象或敏感数据输出。
- 建议：删除已停用语句；若需要诊断，使用受控、限长、脱敏的结构化日志并说明启用条件。

### 6. 注释保留已停用的完整响应日志代码

- 项目：`hisense-ids-app`
- 提交：`403ea8f5808bb10e169f4bb35aec90fb4c6aeaee`
- 类别：可读性
- 严重级别：LOW
- 文件与行范围：`hisense-interface/src/main/java/com/glaway/financeSector/service/impl/FinanceSectorInteractiveServiceImpl.java:726`
- 规则或代码证据：公共规则 `READ-005`，来源 `standards/common/readability.md`。完整响应日志仅被改成 `//log.info(...)`，未说明保留原因或恢复限制。
- 问题说明：停用代码以注释形式长期留在外部调用路径中，意图不明确。
- 影响：后续直接恢复该语句会再次把完整响应写入日志，并可能造成日志量和数据暴露风险。
- 建议：删除注释代码；确需排障时使用受控、限长且脱敏的诊断字段。

## 失败与降级

- 注册表错误：0
- 身份解析失败：0；本用户相关提交均唯一映射
- 同步失败：0
- 规范缺失或冲突：0
- Markdown 生成失败：0
- 未执行目标项目代码、测试、构建、安装、静态分析器、语言服务器或网络补全
