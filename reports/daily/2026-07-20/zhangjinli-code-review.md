# 每日代码审查报告

## 用户与范围

- 用户：张金立（zhangjinli）
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
- 审查提交数：3
- `hisense-ids-app` 提交：
  - `52d093f9584b2e3325646cb28732d832ef8b39a5`
  - `6b634cb7a4c4a4f66384fd2d8e8d0cd2d024d5e0`
  - `37a0ea5d1510fcf52d5d11e42d77beffbcbf2407`
- `hisense-ids-app-spec`：本用户在窗口内无归属提交

## 汇总

| 类别 | 发现数 |
| --- | ---: |
| 代码规范 | 0 |
| 可读性 | 0 |
| 健壮性 | 3 |
| 性能 | 0 |
| 合计 | 3 |

## 发现

### 1. 工作流启动后直接解引用可能缺失的成本模型

- 项目：`hisense-ids-app`
- 提交：`37a0ea5d1510fcf52d5d11e42d77beffbcbf2407`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/plan/service/impl/PlanExtendServiceImpl.java:8796-8810`
- 规则或代码证据：公共规则 `ROBUST-001`、`ROBUST-009`，来源 `standards/common/robustness.md`。代码先启动工作流，再通过 `findOrNullById` 查询成本基础模型，并在未判空时调用 `model.putProcInstId(...)`。
- 问题说明：`baseId` 不存在或记录不可见时会在流程已经启动后抛出空指针异常。
- 影响：流程实例可能已创建，但成本记录和流程变量未完成更新；重试还可能重复启动流程，形成部分失败和不可恢复状态。
- 建议：在启动工作流前校验 `baseId` 并确认模型存在；把流程启动、模型更新和变量设置纳入可恢复的事务或补偿边界，失败时返回明确状态。

### 2. 新增写入口未校验成本工程师的空白和长度

- 项目：`hisense-ids-app`
- 提交：`37a0ea5d1510fcf52d5d11e42d77beffbcbf2407`
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/controller/CostBaseController.java:460-476`；约束证据 `hisense-app/src/main/java/com/glaway/cost/model/entity/CostBaseEntity.java:90-91`
- 规则或代码证据：公共规则 `ROBUST-002`，来源 `standards/common/robustness.md`。入口只校验 `baseId`，直接持久化外部 `costUser`；实体和数据库列长度均为 100。
- 问题说明：空白值和超过 100 字符的值未在可信边界拒绝。
- 影响：空白值可能覆盖有效负责人；超长值会把数据库约束异常推迟到持久化阶段，产生不稳定错误响应。
- 建议：在控制器边界使用 Bean Validation 或等价校验，拒绝空白值和超过 100 字符的值，并返回稳定参数错误。

### 3. 原始异常消息直接返回给接口调用方

- 项目：`hisense-ids-app`
- 提交：`37a0ea5d1510fcf52d5d11e42d77beffbcbf2407`
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/controller/CostBaseController.java:470-476`
- 规则或代码证据：项目规则 `hisense-ids-app-ROBUST-001` 与公共规则 `STYLE-003`、`ROBUST-004`，来源 `standards/projects/hisense-ids-app/robustness.md`、`standards/common/coding-style.md`、`standards/common/robustness.md`。捕获任意异常后执行 `jr.setMessage(e.getMessage())`。
- 问题说明：持久化、框架或下游异常的原始消息未经归一化直接进入响应。
- 影响：调用方可能看到内部表名、字段、约束或实现细节；不同异常还会产生不稳定的客户端错误契约。
- 建议：对外仅返回稳定错误码和通用文案；根因与 `baseId` 仅在受控日志中脱敏保留，并按异常类型进行领域化转换。

## 失败与降级

- 注册表错误：0
- 身份解析失败：0；本用户相关提交均唯一映射
- 同步失败：0
- 规范缺失或冲突：0
- Markdown 生成失败：0
- 未执行目标项目代码、测试、构建、安装、静态分析器、语言服务器或网络补全
