# 代码审查日报

## 用户与范围

- 用户：蒋伟（jiangwei5）
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

- `808fbae03ca5626fc57ae12c7f2f5be33d885cf6`
- `a68856bb789ca0f9ae583c8ba4ace02629b32650`

### `hisense-ids-app-spec`

该用户范围内无提交。

### `hisense-ids-app-need`

该用户范围内无提交。

### `hisense-ids-app-function`

该用户范围内无提交。

## 汇总

- 本次覆盖项目：4 个；该用户有提交项目：1 个
- 项目—提交发生项：2；唯一 SHA：2
- 发现合计：1
  - 代码规范：0
  - 可读性：0
  - 健壮性：1
  - 性能：0

## 发现

### 1. 里程碑模板缺失时排序回退不稳定

- 项目：`hisense-ids-app`
- 提交：`808fbae03ca5626fc57ae12c7f2f5be33d885cf6`
- 类别：健壮性
- 严重级别：LOW
- 文件与行范围：`hisense-app/src/main/java/com/glaway/structureddelivery/service/impl/MileStonePlanBizServiceImpl.java:118-128,149-173,410-414`
- 规则或代码证据：`ROBUST-001`；代码证据：`listQuery` 查询里程碑项时未指定 `order`，随后依赖 `sortByTemplate`；`sortByTemplate` 在 `projectId` 为空、项目不存在、模板为空或异常时直接返回原列表，且模板外项仅使用 `Integer.MAX_VALUE` 无二级排序；本提交删除了 `buildValue` 中按 `createTime` 的兜底排序，当前 `buildValue` 只按输入顺序 `collect`。
- 问题说明：模板不存在、模板查询失败或存在模板未覆盖的里程碑项时，接口会直接沿用数据库查询返回顺序；由于该查询没有显式排序，里程碑列表顺序在这些边界情况下不再稳定。
- 影响：初始化或查询里程碑计划时，缺少可用模板顺序的项目可能出现展示/导出顺序漂移，用户看到的里程碑顺序可能随数据库返回顺序变化，回归了提交前的 `createTime` 兜底稳定性。
- 建议：保留模板排序的同时补充稳定兜底：模板为空或排序失败时按 `createTime` 排序；模板外或同序项使用 `createTime`/ID 作为 `thenComparing` 二级排序，并避免静默吞掉模板查询异常。

## 规范加载与失败

- 规范加载顺序：`standards/common/`，随后加载各项目注册的 `standards_dir`。
- 规范冲突或降级：无；项目规则均为公共规则的补充。
- 注册表、同步、身份解析、规范读取和 Markdown 生成均无失败。
- `hisense-ids-app-need` 与 `hisense-ids-app-function` 在本窗口整体无提交。
- `hisense-ids-app-spec` 中该用户范围内无提交。
