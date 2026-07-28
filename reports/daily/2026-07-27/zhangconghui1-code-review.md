# 代码审查日报

## 用户与范围

- 用户：张从辉（zhangconghui1）
- 报告日期：2026-07-27
- 时区：Asia/Hong_Kong
- 审查窗口：2026-07-27 00:00:00（含）至 2026-07-28 00:00:00（不含）
- 实际过滤条件：未指定项目、提交、分支、文件或目录过滤；未指定 date/date-range，按日报默认前一自然日窗口执行
- 统计口径：同一 SHA 出现在不同注册项目时，按“项目—提交发生项”分别审查和计数

## 注册表快照与生效项目

- 注册表路径：`project-registry.yaml`
- 版本：`1`
- 本次冻结摘要：`ccdd8b03261294a494f5a5892468ec425d40b03ec11a9ab50644d3f840bd0646`
- 条目级错误：无

| 项目 ID | 名称 | 代码目录 | 规范目录 | 默认分支 | 仓库配置键名 | 启用 |
| --- | --- | --- | --- | --- | --- | --- |
| `hisense-ids-app` | 海信 IDS 应用 | `data/code/hisense-ids-app` | `standards/projects/hisense-ids-app` | `projectDevGroup` | `PROJECT_HISENSE_IDS_APP_REPO_URL` | 是 |
| `hisense-ids-app-spec` | 海信 IDS 应用-结构化分支 | `data/code/hisense-ids-app-spec` | `standards/projects/hisense-ids-app-spec` | `projectDevGroup-specTemplate` | `PROJECT_HISENSE_IDS_APP_SPEC_REPO_URL` | 是 |
| `hisense-ids-app-need` | 海信 IDS 应用-需求全链路分支 | `data/code/hisense-ids-app-need` | `standards/projects/hisense-ids-app-need` | `features-DDCP-8746` | `PROJECT_HISENSE_IDS_APP_NEED_REPO_URL` | 是 |
| `hisense-ids-app-function` | 海信 IDS 应用-方法库 | `data/code/hisense-ids-app-function` | `standards/projects/hisense-ids-app-function` | `features-DDCP-8522` | `PROJECT_HISENSE_IDS_APP_FUNCTION_REPO_URL` | 是 |

## 项目来源与实际提交

| 项目 ID | 状态 | 本地目录 | 固定提交 SHA | 说明 |
| --- | --- | --- | --- | --- |
| `hisense-ids-app` | 成功 | `data/code/hisense-ids-app` | `05cf93a3f3cf6e0429b5cc27b9a390ac435cd04b` | 仓库已仅快进同步。 |
| `hisense-ids-app-spec` | 成功 | `data/code/hisense-ids-app-spec` | `17252597a4f6a1206ebb3801c61498b1cc0d15e3` | 仓库已仅快进同步。 |
| `hisense-ids-app-need` | 成功 | `data/code/hisense-ids-app-need` | `3d514d6a9d16fc0d566d87552a7cf4437994963b` | 仓库已是最新状态。 |
| `hisense-ids-app-function` | 成功 | `data/code/hisense-ids-app-function` | `1461b36e5583bdc50327b9099d25f853b8a776db` | 仓库已是最新状态。 |

### `hisense-ids-app`

- `bbc6b604d70e22aa79cf663836a3bebdb5b873d8`
- `5f9edbcc65b47b5f2532502b4ff2909c9aebad14`
- `3428a81bcb4fb3537d3d055e0461d225e451d9ef`
- `7818d55bda0901f0c0cb683c96c3c0892637ebf2`
- `75b7d0e83f8b375fa989e98dc2f2384e8c06c93e`
- `4e2acbac64c78887a35d485c39a7d72f7e661807`
- `c1e62f70a89d1760f11a159facec98a9b5ebf8c2`
- `fae9c408f0a4c72a449c1974a2327bd249fc5019`

### `hisense-ids-app-spec`

该用户范围内无提交。

### `hisense-ids-app-need`

该用户范围内无提交。

### `hisense-ids-app-function`

该用户范围内无提交。

## 汇总

- 本次覆盖项目：4 个；该用户有提交项目：1 个
- 项目—提交发生项：8；唯一 SHA：8
- 发现合计：4
  - 代码规范：0
  - 可读性：1
  - 健壮性：3
  - 性能：0

## 发现

### 1. 专利布局会签按项目阶段误纳入其他交付物

- 项目：`hisense-ids-app`
- 提交：`fae9c408f0a4c72a449c1974a2327bd249fc5019`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/structureddelivery/service/impl/DevPatentLayoutBizServiceImpl.java:1197-1261`
- 规则或代码证据：代码在发起 TR3/TR6 会签时只按 `projectId`、`projectStage` 查询 `layoutItemModels`（1201-1204），但流程变量使用当前请求的 `outputId`/`deliveryId`（1235-1236），随后把查询出的全部明细统一置为 `SUBMITTED`/`UNDER_REVIEW` 并写入同一个 `procInstId`（1256-1261）。违反公共健壮性要求 `ROBUST-009` 对多步骤写入需保留正确范围与可恢复状态。
- 问题说明：同一项目阶段存在多个结构化输出物时，本次提交会把其他 `outputId`/`deliveryId` 下的专利布局明细一起纳入本流程并更新审批状态。
- 影响：会导致无关交付物明细被错误提交、审批人集合被污染，后续驳回/通过监听也可能处理与当前流程不匹配的数据。
- 建议：查询和更新明细时同时限定 `outputId`（必要时 `deliveryId`/`idList`），并校验返回明细全部属于当前交付物后再发起流程和批量更新。

### 2. 高风险流程提交后才校验交付物导致部分写入

- 项目：`hisense-ids-app`
- 提交：`fae9c408f0a4c72a449c1974a2327bd249fc5019`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/risk/service/impl/DevProjectRiskServiceImpl.java:1267-1306`
- 规则或代码证据：`startNewProcessBySign` 先调用 `stateCombService.submitWorkflow`，再更新 `findingModel` 审批状态，最后才按 `outputId` 查询 `StructuredDeliveryModel` 且未判空就调用 `putLifecycleState`。违反 `ROBUST-004`/`ROBUST-009`：失败不能伪装成成功，多步骤写入发生部分失败时必须保留可恢复状态。
- 问题说明：如果流程参数中的 `outputId` 找不到结构化交付物，方法会在工作流已提交、风险排查记录已更新后触发空指针异常。
- 影响：高风险审批可能出现“流程已启动/风险排查已审批中/交付物未审批中”的不一致状态，后续重试或审批监听无法可靠恢复。
- 建议：在 `submitWorkflow` 前完成 `workFlowBusinessParam`、`startVariable`、`riskId`、`findingModel`、`StructuredDeliveryModel` 的完整校验；把流程提交与本地状态更新纳入一致的事务/补偿边界，并对缺失交付物返回业务错误。

### 3. 风险排查保存未处理输出物未关联交付物

- 项目：`hisense-ids-app`
- 提交：`fae9c408f0a4c72a449c1974a2327bd249fc5019`
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/structureddelivery/service/impl/DevPatentRiskFindingBizServiceImpl.java:289-299`
- 规则或代码证据：`save` 仅校验 `outputId` 非空，随后 `queryFirst` 查询 `StructuredDeliveryModel`，未判空就读取 `findId`/`findVersion`。违反 `ROBUST-001`：查询结果缺失值必须显式处理，不得依赖偶然空指针。
- 问题说明：请求携带非空但未关联结构化交付物的 `outputId` 时，保存接口会直接空指针，而不是返回可识别业务错误。
- 影响：用户保存失败时无法获得稳定错误语义；调用方也无法区分参数非法、关联缺失和系统异常。
- 建议：`queryFirst` 后先判空并返回“交付物不存在/输出物未关联结构化交付物”等业务错误，再读取 `deliveryId`/`version`。

### 4. 风险排查标题被项目 ID 覆盖

- 项目：`hisense-ids-app`
- 提交：`fae9c408f0a4c72a449c1974a2327bd249fc5019`
- 类别：可读性
- 严重级别：LOW
- 文件与行范围：`hisense-app/src/main/java/com/glaway/structureddelivery/model/DevPatentRiskFindingModel.java:120-122`
- 规则或代码证据：`save` 已在 `dto.title` 中组装“专利风险排查-阶段”（`DevPatentRiskFindingBizServiceImpl.java:281-283`），但 `updateFrom` 在 `projectId` 非空时执行 `existingModel.putTitle(dto.getProjectId())`。违反 `READ-001`/`STYLE-001`：名称和字段值应与行为、业务用途一致。
- 问题说明：更新已有风险排查记录时，标题字段会被项目 ID 覆盖，而不是保存业务标题。
- 影响：列表、流程业务名称或后续审查中看到的 `title` 会变成技术 ID，降低可读性并可能误导用户识别记录。
- 建议：将该分支改为检查 `dto.getTitle()` 并写入 `dto.getTitle()`；若标题不允许更新，应删除该赋值而不是写入 `projectId`。

## 规范加载与失败

- 规范加载顺序：`standards/common/`，随后加载各项目注册的 `standards_dir`。
- 规范冲突或降级：无；项目规则均为公共规则的补充。
- 注册表、同步、身份解析、规范读取和 Markdown 生成均无失败。
- `hisense-ids-app-need` 与 `hisense-ids-app-function` 在本窗口整体无提交。
- `hisense-ids-app-spec` 中该用户范围内无提交。
