# 每日代码审查报告

## 用户与范围

- 用户：陶甫（taofu）
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
- 审查提交数：1
- `hisense-ids-app`：`330d0c039f286f9ab67e17855bfe6049f44a6517`
- `hisense-ids-app-spec`：本用户在窗口内无归属提交

## 汇总

| 类别 | 发现数 |
| --- | ---: |
| 代码规范 | 0 |
| 可读性 | 1 |
| 健壮性 | 1 |
| 性能 | 1 |
| 合计 | 3 |

## 发现

### 1. SAP 失败和异常数值被折叠为正常零值

- 项目：`hisense-ids-app`
- 提交：`330d0c039f286f9ab67e17855bfe6049f44a6517`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostServiceImpl.java:563-617,646-704,740-749`
- 规则或代码证据：项目规则 `hisense-ids-app-ROBUST-001` 与公共规则 `ROBUST-004`，来源 `standards/projects/hisense-ids-app/robustness.md`、`standards/common/robustness.md`。SAP 响应为空、失败或载荷为空时返回空集合或三个零值；`toBd` 捕获 `NumberFormatException` 后同样返回零。
- 问题说明：外部服务失败、缺失关键数据和格式异常均与真实零工时、零加工费不可区分，调用方继续记录“数据更新完成”。
- 影响：SAP 超时、失败响应或异常数值会被伪装成有效计算结果，旧值可能保留或加工费缺失，且调用方无法识别本次计算不完整。
- 建议：分层校验响应包装、成功状态、载荷和数值字段；失败时抛出带稳定错误码与脱敏上下文的领域异常，仅对契约明确允许的缺失值执行可识别降级。

### 2. 单价配置每次无界加载并构建完整映射

- 项目：`hisense-ids-app`
- 提交：`330d0c039f286f9ab67e17855bfe6049f44a6517`
- 类别：性能
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostServiceImpl.java:707-737`
- 规则或代码证据：公共规则 `PERF-005`，来源 `standards/common/performance.md`。每次计算按公司查询全部 `UnitPricePerHourModel`，没有分页、条数或所需工作中心限制，随后构建完整 `HashMap`。
- 问题说明：查询结果和内存映射没有可定位的数据上限。
- 影响：公司单价配置记录增长时，每次成本计算的数据库读取、对象分配和映射成本线性增长。
- 建议：先从 SAP 明细收集并去重所需工厂与工作中心，再按键批量查询；设置批次和结果上限，或在版本一致性可证明时使用有界缓存。

### 3. 计算精度使用多个未命名字面值

- 项目：`hisense-ids-app`
- 提交：`330d0c039f286f9ab67e17855bfe6049f44a6517`
- 类别：可读性
- 严重级别：LOW
- 文件与行范围：`hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostServiceImpl.java:582-600,639-643,683-690`
- 规则或代码证据：公共规则 `READ-004`，来源 `standards/common/readability.md`。新增计算分别直接使用精度 `4`、`6` 和 `3` 执行 `BigDecimal.divide`，未说明这些精度的来源和用途。
- 问题说明：不同阶段的计价精度策略散落为字面值。
- 影响：调整金额或工时精度、排查累计舍入差异时，维护者无法判断哪些值应同步修改，容易造成局部规则不一致。
- 建议：提取如 `HOUR_SCALE`、`ITEM_FEE_SCALE`、`AMOUNT_SCALE` 的具名常量，并注明对应外部接口或金额精度约束。

## 失败与降级

- 注册表错误：0
- 身份解析失败：0；本用户相关提交均唯一映射
- 同步失败：0
- 规范缺失或冲突：0
- Markdown 生成失败：0
- 未执行目标项目代码、测试、构建、安装、静态分析器、语言服务器或网络补全
