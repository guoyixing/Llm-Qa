# 代码审查日报

## 用户与范围

- 用户：陶甫（taofu）
- 报告日期：2026-07-24
- 时区：Asia/Hong_Kong
- 审查窗口：2026-07-24 00:00:00（含）至 2026-07-27 00:00:00（不含）
- 实际过滤条件：`date-range=2026-07-24,2026-07-26`；未指定项目、提交、分支、文件或目录过滤
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
| `hisense-ids-app` | 成功 | `data/code/hisense-ids-app` | `c3b90876ec9460f005ebf9ec5a0cca6fbab2f986` | 仓库已仅快进同步。 |
| `hisense-ids-app-spec` | 成功 | `data/code/hisense-ids-app-spec` | `5517ca5e0b2b9903b124ad1710327d1d5f0ab943` | 仓库已仅快进同步。 |
| `hisense-ids-app-need` | 成功 | `data/code/hisense-ids-app-need` | `3d514d6a9d16fc0d566d87552a7cf4437994963b` | 仓库已仅快进同步。 |
| `hisense-ids-app-function` | 成功 | `data/code/hisense-ids-app-function` | `1461b36e5583bdc50327b9099d25f853b8a776db` | 仓库已是最新状态。 |

### `hisense-ids-app`

- `013bf2495c55db005a4c3e926d8b25d3f447a9b2`
- `db1c041d5b17e1e655fc52b73c65bb7205ff63f2`
- `ecc49b4aa327d1628e0fb16a4fb12c429cf12c48`
- `4c2ebb53e75746d459b734370e61764e30ffbfa5`
- `04ec95510262a072851f8b081a3da35e41ec6c64`
- `0d5c37aee5bd17cb6abe5468c8372bed7ccfee02`
- `c111032074b86259c280a54c58cfa2c747deea04`
- `21b54697877b4d0a83c30fbc5a1ecff306d26c95`
- `cd8c904bd037ce8f2cebcd2bdb078f71be8d92c4`

### `hisense-ids-app-spec`

- `013bf2495c55db005a4c3e926d8b25d3f447a9b2`
- `db1c041d5b17e1e655fc52b73c65bb7205ff63f2`
- `ecc49b4aa327d1628e0fb16a4fb12c429cf12c48`
- `4c2ebb53e75746d459b734370e61764e30ffbfa5`
- `04ec95510262a072851f8b081a3da35e41ec6c64`
- `0d5c37aee5bd17cb6abe5468c8372bed7ccfee02`
- `c111032074b86259c280a54c58cfa2c747deea04`

### `hisense-ids-app-need`

该用户范围内无提交。

### `hisense-ids-app-function`

范围内无提交。

## 汇总

- 本次覆盖项目：4 个；该用户有提交项目：2 个
- 项目—提交发生项：16；唯一 SHA：9
- 发现合计：1
  - 代码规范：0
  - 可读性：0
  - 健壮性：1
  - 性能：0

## 发现

### 1. 流程 business key 与监听器查询键不一致

- 项目：`hisense-ids-app`
- 提交：`21b54697877b4d0a83c30fbc5a1ecff306d26c95`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/financeSector/planSale/service/impl/PlanSaleServiceImpl.java:236`；`hisense-app/src/main/java/com/glaway/financeSector/planSale/listener/PlanSaleSubmitListener.java:18-29`；`hisense-app/src/main/java/com/glaway/financeSector/planSale/listener/PlanSalePublishEndListener.java:22-31`；`hisense-app/src/main/java/com/glaway/financeSector/planSale/listener/PlanSaleRejectListener.java:18-27`
- 规则或代码证据：公共规则 `ROBUST-001`、`ROBUST-004`。该提交把流程 business key 从 `model.findId()` 改为 `model.findProjectId()`，同窗口监听器仍使用 `equals("id", businessKey).queryFirst()` 查询 `PlanSaleModel`。
- 问题说明：流程传递项目 ID，监听器却把它当作规划销量模型 ID 查询。
- 影响：监听器通常无法取得目标模型，提交、通过或驳回后的生命周期状态更新会被跳过，流程状态和业务记录状态可能不一致。
- 建议：统一 business key 语义；若必须传项目 ID，监听器应按 `projectId` 查询并处理版本唯一性，否则继续使用规划销量模型 ID。

## 规范加载与失败

- 规范加载顺序：`standards/common/`，随后加载各项目注册的 `standards_dir`
- 规范冲突或降级：无；项目规则均为公共规则的补充
- 注册表、同步、身份解析和规范读取均无失败。
- `hisense-ids-app-need` 中该用户范围内无提交；`hisense-ids-app-function` 整体范围内无提交。
- `hisense-ids-app-spec` 中未发现该用户具有充分证据的问题。
