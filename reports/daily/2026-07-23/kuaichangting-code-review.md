# 2026-07-23 手动代码审查报告

## 用户与范围

- 用户：蒯长汀（kuaichangting）
- 时区：`Asia/Hong_Kong`
- 报告日期依据：显式提交范围中最早的 Git Author Date 转换为香港本地日期后为 `2026-07-23`
- 实际过滤条件：项目 `hisense-ids-app`；显式提交 `744b475dab0a5b2acf5d9b91d003882feb8d892f`、`e91cbc952d894c612dcb5b22309b1cca11f8400b`、`e77270d3b25ed78ebc38be262d0f5098289ed089`、`e90ca0f57b1ad3f7bad3d615dbef7df1a2326407`；未指定日期、分支、文件或目录过滤
- 注册表：`project-registry.yaml`
- 注册表版本：`1`
- 冻结摘要：`ccdd8b03261294a494f5a5892468ec425d40b03ec11a9ab50644d3f840bd0646`

## 注册表快照与生效项目

| 项目 | 名称 | code_dir | standards_dir | default_branch | repository_url_config_key |
|---|---|---|---|---|---|
| `hisense-ids-app` | 海信 IDS 应用 | `data/code/hisense-ids-app` | `standards/projects/hisense-ids-app` | `projectDevGroup` | `PROJECT_HISENSE_IDS_APP_REPO_URL` |

该项目在当前快照中有效且 `enabled: true`，注册表没有条目级错误。

## 项目来源与实际提交

- 来源类型：当前注册表登记的受控本地工作区
- 本地路径：`data/code/hisense-ids-app`
- 来源说明：手动审查未调用同步脚本，不声明本地工作区已同步或为远端最新
- 已固定实际提交：
  - `744b475dab0a5b2acf5d9b91d003882feb8d892f`
  - `e91cbc952d894c612dcb5b22309b1cca11f8400b`
  - `e77270d3b25ed78ebc38be262d0f5098289ed089`
  - `e90ca0f57b1ad3f7bad3d615dbef7df1a2326407`
- `e91cbc952d894c612dcb5b22309b1cca11f8400b` 为无可见补丁的合并提交，已审查且未据其父提交或工作树推测新增问题。

## 汇总

| 指标 | 数量 |
|---|---:|
| 实际审查项目数 | 1 |
| 实际审查提交数 | 4 |
| 代码规范发现 | 0 |
| 可读性发现 | 0 |
| 健壮性发现 | 0 |
| 性能发现 | 1 |
| 发现总数 | 1 |

严重级别：`LOW` 1 条。

## 发现

### 团队项目可见性查询和 `IN` 条件没有数据量边界

- 项目：`hisense-ids-app`
- 提交：`744b475dab0a5b2acf5d9b91d003882feb8d892f`
- 类别：性能
- 严重级别：`LOW`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/project/service/impl/ProjectExtendServiceImpl.java:1458-1465,1470-1472`
- 规则或代码证据：公共规则 `PERF-005` 要求数据库读取和内存集合设置分页、条数或其他明确上限。新增代码按当前用户查询全部 `ContextTeamPrincipal`，收集全部 `containerId`，再将完整集合传入项目 ID 的 `IN` 条件；补丁中没有分页、条数上限或分批处理。
- 问题说明：用户参与项目数量增加时，团队关系查询结果、内存中的项目 ID 集合以及后续 `IN` 参数会同步增长。
- 影响：大规模团队关系可能增加查询结果传输、内存占用和项目列表条件构造成本，并使后续数据库查询承担过大的 `IN` 参数集合。
- 建议：优先使用数据库关联或子查询表达团队成员可见性；如果现有查询能力只能使用 `IN`，应设置明确上限并按受控批次查询和合并结果。

## 失败与降级

- 身份解析成功：4 个提交均唯一映射到蒯长汀（kuaichangting），未发生姓名不一致。
- 规范读取成功：已按公共规范再到 `standards/projects/hisense-ids-app` 的顺序加载，没有不可决冲突。
- 报告生成范围：仅生成本 Markdown；按照用户确认的手动审查方式，不生成 HTML、不发送邮件。
- 本报告仅陈述本次固定提交和可见差异的只读静态审查事实，不包含运行、测试、构建或远端新鲜度结论。
