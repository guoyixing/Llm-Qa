# 代码审查日报

## 用户与范围

- 用户：蒯长汀（kuaichangting）
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

- `47ab47a52247adb360606b123345debc4eadde90`
- `0536abdd1ae16a609c0717e229624d7a89a2c8b4`
- `31f4ec2a28e6dce439e7c4e9db61d84d66be75be`
- `f72c70281670ec15e75aefb73d0251247e05ee4b`
- `cbe4a7ef6c78a13eaab77432e4433190c608da5b`

### `hisense-ids-app-spec`

该用户范围内无提交。

### `hisense-ids-app-need`

该用户范围内无提交。

### `hisense-ids-app-function`

该用户范围内无提交。

## 汇总

- 本次覆盖项目：4 个；该用户有提交项目：1 个
- 项目—提交发生项：5；唯一 SHA：5
- 发现合计：1
  - 代码规范：1
  - 可读性：0
  - 健壮性：0
  - 性能：0

## 发现

### 1. 临时权限标签日志输出未脱敏

- 项目：`hisense-ids-app`
- 提交：`cbe4a7ef6c78a13eaab77432e4433190c608da5b`
- 类别：代码规范
- 严重级别：LOW
- 文件与行范围：`hisense-app/src/main/java/com/glaway/project/service/impl/ProjectExtendServiceImpl.java:1451`
- 规则或代码证据：公共规则 `STYLE-002` 要求日志不得记录未经脱敏的个人数据且需包含定位上下文。提交在 `queryConfByUserLabel` 中新增 `log.info("条件查询值不在人员标签中，confValue={}, personLabelList={}", confValue, personLabelList);`；`personLabelList` 来自当前用户人员标签值。
- 问题说明：权限过滤路径的临时 INFO 日志直接输出查询条件值和当前用户人员标签列表，未做脱敏或缩减，也缺少稳定请求/项目标识；该信息属于权限/人员标签上下文，不应以 INFO 全量进入应用日志。
- 影响：在项目查询等高频路径触发时，日志会扩大人员标签和权限配置相关数据的可见范围，并增加噪声；若日志被更广泛采集或检索，会增加权限属性泄露风险。该临时日志已在同窗口后续提交 `31f4ec2a28e6dce439e7c4e9db61d84d66be75be` 删除，最终版本不再保留此问题。
- 建议：不要输出完整 `personLabelList`；如确需排查，改为受控 DEBUG 日志，只记录脱敏后的稳定标识、标签数量或命中/未命中状态，并补充请求/项目上下文。

## 规范加载与失败

- 规范加载顺序：`standards/common/`，随后加载各项目注册的 `standards_dir`。
- 规范冲突或降级：无；项目规则均为公共规则的补充。
- 注册表、同步、身份解析、规范读取和 Markdown 生成均无失败。
- `hisense-ids-app-need` 与 `hisense-ids-app-function` 在本窗口整体无提交。
- `hisense-ids-app-spec` 中该用户范围内无提交。
