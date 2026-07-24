# 2026-07-23 代码审查日报

## 用户与范围

- 用户：郭一行（guoyixing）
- 时区：`Asia/Hong_Kong`
- 审查窗口：`2026-07-23 00:00:00`（含）至 `2026-07-24 00:00:00`（不含）
- 实际过滤条件：省略项目选择，使用全部有效且已启用项目；使用默认前一自然日；未指定 `commit`、`branch`、`file` 或 `directory`
- 注册表：`project-registry.yaml`，版本 `1`
- 冻结摘要：`ccdd8b03261294a494f5a5892468ec425d40b03ec11a9ab50644d3f840bd0646`

## 注册表快照与生效项目

| 项目 | 名称 | code_dir | standards_dir | default_branch | repository_url_config_key |
|---|---|---|---|---|---|
| `hisense-ids-app` | 海信 IDS 应用 | `data/code/hisense-ids-app` | `standards/projects/hisense-ids-app` | `projectDevGroup` | `PROJECT_HISENSE_IDS_APP_REPO_URL` |
| `hisense-ids-app-spec` | 海信 IDS 应用-结构化分支 | `data/code/hisense-ids-app-spec` | `standards/projects/hisense-ids-app-spec` | `projectDevGroup-specTemplate` | `PROJECT_HISENSE_IDS_APP_SPEC_REPO_URL` |
| `hisense-ids-app-need` | 海信 IDS 应用-需求全链路分支 | `data/code/hisense-ids-app-need` | `standards/projects/hisense-ids-app-need` | `features-DDCP-8746` | `PROJECT_HISENSE_IDS_APP_NEED_REPO_URL` |
| `hisense-ids-app-function` | 海信 IDS 应用-方法库 | `data/code/hisense-ids-app-function` | `standards/projects/hisense-ids-app-function` | `features-DDCP-8522` | `PROJECT_HISENSE_IDS_APP_FUNCTION_REPO_URL` |

以上项目均为 `enabled: true`，注册表没有条目级错误。

## 项目来源与提交

| 项目 | 状态 | 固定提交 SHA | 中文说明 |
|---|---|---|---|
| `hisense-ids-app` | success | `3a8ac1f8158e985ee987809e73e26d402fe511c3` | 仓库已仅快进同步。 |
| `hisense-ids-app-spec` | success | `d0e639c311f42d8fa8e7cc87e70bcd7d2b5773ad` | 仓库已仅快进同步。 |
| `hisense-ids-app-need` | success | `1e45405191d6e4afc3b35e04162dc7936c1b7408` | 仓库已仅快进同步。 |
| `hisense-ids-app-function` | success | `1461b36e5583bdc50327b9099d25f853b8a776db` | 仓库已是最新状态。 |

四项结果均与冻结注册表绑定一致。`hisense-ids-app-function` 在窗口内无提交。

## 项目来源与实际提交

### `hisense-ids-app-spec`

`91660e4c3dd0605671402f7e9d26640c3328da40`、`c577bbd604ef548eeeb3ddb87f907a6a8800dd36`

其他项目在本窗口内没有归属于该用户的提交。

## 汇总

| 指标 | 数量 |
|---|---:|
| 实际审查项目数 | 1 |
| 实际审查提交数 | 2 |
| 代码规范发现 | 0 |
| 可读性发现 | 0 |
| 健壮性发现 | 0 |
| 性能发现 | 0 |
| 发现总数 | 0 |

## 发现

本次在四类静态质量审查范围内无发现。

## 失败与降级

- 身份解析部分失败：`hisense-ids-app` 中以下提交无法唯一映射到规范用户，已跳过个人聚合、报告和投递，不归属于本报告用户：`744b475dab0a5b2acf5d9b91d003882feb8d892f`、`e91cbc952d894c612dcb5b22309b1cca11f8400b`、`e77270d3b25ed78ebc38be262d0f5098289ed089`、`e90ca0f57b1ad3f7bad3d615dbef7df1a2326407`、`273f8b66f417bab3ea5a1e2e5cb268838bd98e64`、`df362d25c7ea6c2be6078180a02350555241753d`。
- 同步、注册表绑定和规范读取均成功；公共规范与项目规范没有不可决冲突。
- 本报告仅陈述本次固定提交和可见差异的只读静态审查事实，不包含运行、测试或构建结论。
