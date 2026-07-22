# 2026-07-21 代码质量日报

## 用户与范围

- 用户：陶甫（taofu）
- 时区：`Asia/Hong_Kong`
- 审查窗口：`2026-07-21 00:00:00+08:00`（含）至 `2026-07-22 00:00:00+08:00`（不含）
- 实际过滤条件：选择当前注册表全部有效且已启用项目；按窗口和各项目本次固定提交筛选；未指定提交、分支、文件或目录过滤条件。
- 证据边界：仅使用本次冻结快照、直接同步结果、固定提交元数据、可见差异和必要的最少上下文；未读取未提交内容，未执行目标项目。

## 注册表快照与生效项目

- 注册表：`project-registry.yaml`
- 版本：`1`
- 本次冻结摘要：`8d7df2ddd33403fd0c669001a44851718324cc93e429dc213dd3e496cf524230`

| 项目 | 名称 | 代码目录 | 规范目录 | 注册分支 | 仓库配置键名 |
| --- | --- | --- | --- | --- | --- |
| `hisense-ids-app` | 海信 IDS 应用 | `data/code/hisense-ids-app` | `standards/projects/hisense-ids-app` | `projectDevGroup` | `PROJECT_HISENSE_IDS_APP_REPO_URL` |
| `hisense-ids-app-spec` | 海信 IDS 应用-结构化分支 | `data/code/hisense-ids-app-spec` | `standards/projects/hisense-ids-app-spec` | `projectDevGroup-specTemplate` | `PROJECT_HISENSE_IDS_APP_SPEC_REPO_URL` |
| `hisense-ids-app-need` | 海信 IDS 应用-需求全链路分支 | `data/code/hisense-ids-app-need` | `standards/projects/hisense-ids-app-need` | `features-DDCP-8746` | `PROJECT_HISENSE_IDS_APP_NEED_REPO_URL` |

## 项目来源与实际提交

| 项目 | 本次来源结果 |
| --- | --- |
| `hisense-ids-app` | 成功；固定 SHA `7bab46dc8ccd9d7a514ebe70064d5d36f3457522`；仓库已是最新状态。 |
| `hisense-ids-app-spec` | 成功；固定 SHA `48a45a5af60416637d3c8cfdd7b67a1a1f96da99`；仓库已是最新状态。 |
| `hisense-ids-app-need` | 成功；固定 SHA `5e5752cd346beb33d17c169bd5f4a9c6bb34bad7`；仓库已是最新状态。 |

### `hisense-ids-app`

- `abf3e7f0c323803f47a9b1d35c61688c174f4acc`
- `8e55fff1b1472c3b204887fcf853869b7762bd25`
- `135529d4ec1634ec0724573668121fbe4b2ecfc5`
- `35e06ef51071060995beab33c6792abf31a3c0f7`
- `a04488272d75fcf9af91348e99d3b9635b9620c1`

### 其他项目

- `hisense-ids-app-spec`：该用户范围内无提交。
- `hisense-ids-app-need`：范围内无提交。

## 汇总

- 本次成功处理项目数：3
- 该用户有提交的项目数：1
- 项目—提交关联数：5
- 唯一提交数：5

| 类别 | 发现数 |
| --- | ---: |
| 代码规范 | 0 |
| 可读性 | 0 |
| 健壮性 | 4 |
| 性能 | 0 |
| **合计** | **4** |

| 严重级别 | 数量 |
| --- | ---: |
| HIGH | 2 |
| MEDIUM | 1 |
| ADVISORY | 1 |

## 发现

### 人员工时被万元换算放大后写入科目值

- 项目：`hisense-ids-app`
- 提交：`135529d4ec1634ec0724573668121fbe4b2ecfc5`
- 类别：健壮性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostCalcServiceImpl.java:191-207`
- 规则或代码证据：公共规则 `ROBUST-002` 要求数值和单位边界一致。代码先对所有科目执行 `amount.multiply(WAN_YUAN)`；新增分支虽然禁止 `KMDL001` 进入总费用，仍把换算后的值合并到一级、二级科目。后续同窗口提交又把该科目的显示单位明确为“人天”。
- 问题说明：直接人员工时不是金额，却仍执行万元到元的 10000 倍换算。
- 影响：`KMDL001` 及其下级科目可能保存为原始工时的 10000 倍，导致计划值展示和后续计算失真。
- 建议：在单位换算前识别人员工时科目；工时保留原值，仅金额科目乘以 `WAN_YUAN`，并让一级、二级汇总复用同一单位判断。

### 两个流程入口均未校验项目查询结果即解引用

- 项目：`hisense-ids-app`
- 提交：`a04488272d75fcf9af91348e99d3b9635b9620c1`
- 类别：健壮性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/service/impl/CostWorkFlowServiceImpl.java:201-209`；`hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostServiceImpl.java:1406-1414`
- 规则或代码证据：公共规则 `ROBUST-001` 要求显式处理查询结果缺失。两处代码都在 `queryFirst()` 后直接调用 `developGroupProjectModel.findDomesticInternationalSales()`，没有验证查询结果非空。
- 问题说明：当 `baseProjectId` 没有匹配的项目记录时，流程依赖空指针异常表达失败。
- 影响：计划关闭或端到端成本流程启动会异常中断，调用方无法获得可区分的缺失数据错误。
- 建议：在首次可信边界统一校验查询结果；缺失时抛出带稳定项目标识的领域异常或返回明确失败结果。

### 空销售分类绕过“仅内销”准入条件

- 项目：`hisense-ids-app`
- 提交：`a04488272d75fcf9af91348e99d3b9635b9620c1`
- 类别：健壮性
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostServiceImpl.java:1411-1415`
- 规则或代码证据：公共规则 `ROBUST-001` 要求区分缺失值与合法值。新增条件只在分类“非空且不等于 `DOMESTIC`”时返回，因此 `null` 会继续启动流程，与代码声明的“仅内销”条件不一致。
- 问题说明：未分类项目没有被证明为内销，却被当作允许处理。
- 影响：销售分类缺失的数据可能错误进入仅面向内销的端到端成本流程。
- 建议：改用正向门禁，仅当分类明确等于 `DOMESTIC` 时继续；空值和其他值进入可识别的拒绝或数据修复路径。

### 财务代表缺失只记录日志并正常返回

- 项目：`hisense-ids-app`
- 提交：`35e06ef51071060995beab33c6792abf31a3c0f7`
- 类别：健壮性
- 严重级别：`ADVISORY`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostServiceImpl.java:1429-1435`
- 规则或代码证据：公共规则 `ROBUST-004` 要求失败状态可区分。`financeStaff` 为空时仅执行 `log.error(...)` 后 `return`，没有异常或错误结果传递。可见差异无法证明该场景在业务契约中必须中止，因此按建议级别报告。
- 问题说明：审批人缺失导致流程未启动，但调用方无法从返回语义区分“已完成”和“未启动”。
- 影响：若上层把正常返回视为触发完成，可能形成静默漏处理；当前静态证据不足以证明实际业务损失。
- 建议：明确方法契约；需要失败时返回可区分结果或领域异常，允许跳过时也应返回明确的未执行状态和定位上下文。

## 失败与降级

- 注册表条目错误：0；项目同步失败：0；身份解析失败或未归属提交：0。
- 规范缺失或冲突：0。
- 本用户 Markdown 事实报告生成前置失败：0。
- 财务代表缺失条目因缺少必须中止的接口契约证据，降为 `ADVISORY`。
