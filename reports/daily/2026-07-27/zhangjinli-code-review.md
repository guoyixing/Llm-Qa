# 代码审查日报

## 用户与范围

- 用户：张金立（zhangjinli）
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

- `0af7c7799301c0c46396f055eecf3181ba36d0d5`
- `3afaa1d78c69a48f43d3ee05a9f87e1273058cdc`
- `9daea0a22b6b7c265a696e5642e49f8210cc7f60`

### `hisense-ids-app-spec`

该用户范围内无提交。

### `hisense-ids-app-need`

该用户范围内无提交。

### `hisense-ids-app-function`

该用户范围内无提交。

## 汇总

- 本次覆盖项目：4 个；该用户有提交项目：1 个
- 项目—提交发生项：3；唯一 SHA：3
- 发现合计：1
  - 代码规范：0
  - 可读性：0
  - 健壮性：1
  - 性能：0

## 发现

### 1. 请求字段 currentStage 被信任为项目实际阶段

- 项目：`hisense-ids-app`
- 提交：`0af7c7799301c0c46396f055eecf3181ba36d0d5`
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/model/dto/OtherCaliberTargetDTO.java:71-74；hisense-app/src/main/java/com/glaway/cost/controller/OtherCaliberTargetsAreMetController.java:83-85；hisense-app/src/main/java/com/glaway/cost/service/impl/OtherCaliberTargetsAreMetServiceImpl.java:641-642；hisense-app/src/main/java/com/glaway/cost/util/DataConverListMapperUtil.java:155-166`
- 规则或代码证据：公共规则 `ROBUST-001` 要求外部输入、缺失值和可选字段在首次可信边界明确处理。提交新增 `OtherCaliberTargetDTO.currentStage`，控制器直接接收 `@RequestBody OtherCaliberTargetDTO` 并传入服务；服务在日立分支调用 `filterHitachiVersionData(list, stage, otherCaliberTargetDTO.getCurrentStage(), costVersion)`，工具方法用 `stage.equals(currentStage)` 决定按当前版本过滤，否则取最大版本。
- 问题说明：`currentStage` 的注释定义为“项目实际所处阶段”，但实现把它作为外部请求字段信任并直接参与版本过滤。请求缺失该字段时当前阶段会落入“其他阶段”分支；请求传入任意阶段时也会改变当前版本/最大版本的过滤路径。
- 影响：日立其他口径目标达标列表可能因请求字段缺失或被篡改而返回错误版本、空结果或历史版本数据，导致同一项目阶段下展示结果不稳定。
- 建议：不要从 `@RequestBody` 信任 `currentStage`；在服务端根据 `baseId`/`projectId` 查询到的 `CostProductModel` 或项目主数据派生实际当前阶段和当前版本，校验缺失情况后再传给过滤方法。若字段仅为内部计算需要，应从 DTO 移除或在入口忽略客户端值。

## 规范加载与失败

- 规范加载顺序：`standards/common/`，随后加载各项目注册的 `standards_dir`。
- 规范冲突或降级：无；项目规则均为公共规则的补充。
- 注册表、同步、身份解析、规范读取和 Markdown 生成均无失败。
- `hisense-ids-app-need` 与 `hisense-ids-app-function` 在本窗口整体无提交。
- `hisense-ids-app-spec` 中该用户范围内无提交。
