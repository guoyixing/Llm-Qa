# 2026-07-23 代码审查日报

## 用户与范围

- 用户：陶文秀（taowenxiu）
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

### `hisense-ids-app`

`f58a20ac6025da1e194c15b2e78fe39eaa56a973`、`8afe90e774fec2dffc54c47b02868236e0a6b765`、`ac26f965e4a922c1fa5ad0a9d7a59d4d15d4e854`

### `hisense-ids-app-spec`

`d0e639c311f42d8fa8e7cc87e70bcd7d2b5773ad`

## 汇总

| 指标 | 数量 |
|---|---:|
| 实际审查项目数 | 2 |
| 实际审查提交数 | 4 |
| 代码规范发现 | 0 |
| 可读性发现 | 2 |
| 健壮性发现 | 1 |
| 性能发现 | 0 |
| 发现总数 | 3 |

严重级别：`HIGH` 1 条、`MEDIUM` 1 条、`ADVISORY` 1 条。

## 发现

### 6.1 检查方法隐藏持久化副作用

- 项目：`hisense-ids-app`
- 提交：`f58a20ac6025da1e194c15b2e78fe39eaa56a973`
- 类别：可读性
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/plan/service/impl/PlanExtendServiceImpl.java:6555-6559`
- 规则或代码证据：公共规则 `READ-001` 要求名称与行为一致；`checkPlanPublish` 新增分支会修改动态属性并调用 `PersistHelper.service().update(projectModel)`。
- 问题说明：方法名称表达发布检查，但实现同时持久化清理流程 ID，调用者无法从名称识别写副作用。
- 影响：增加调用顺序、事务边界和维护理解成本，纯校验调用也可能改变项目状态。
- 建议：把清理操作提取为名称明确的写方法，由编排入口显式调用；或重命名当前方法，使名称准确表达检查与修复职责。

### 6.2 联调常量无条件覆盖真实 PLM 请求参数

- 项目：`hisense-ids-app`
- 提交：`ac26f965e4a922c1fa5ad0a9d7a59d4d15d4e854`
- 类别：健壮性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/output/struct/trialproductapply/service/impl/TrialProductApplyServiceImpl.java:1846,1850`
- 规则或代码证据：补丁先写入真实项目编号和试制基地编码，随后新增有效语句用固定联调值覆盖同一字段；相邻注释明确标注为开发环境联调数据，DTO 随后直接传给 `getPlmAssemblyList`。
- 问题说明：每次调用都会忽略当前项目计算出的真实参数，改用固定联调参数。
- 影响：PLM 请求对象与当前项目输入不一致，可能查询或处理错误项目的数据。
- 建议：删除两条覆盖语句；如必须保留联调能力，应通过默认关闭的受控环境配置选择测试参数，不能无条件覆盖真实值。

### 6.3 A 版例外未体现在校验错误信息中

- 项目：`hisense-ids-app-spec`
- 提交：`d0e639c311f42d8fa8e7cc87e70bcd7d2b5773ad`
- 类别：可读性
- 严重级别：`ADVISORY`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/specification/service/handler/SpecChangeHandler.java:248,261`，错误信息证据位于 `262`
- 规则或代码证据：修改后的条件允许生命周期为 `RELEASED` 或 BizVersion 为 `A`，但失败信息仍只说明“仅已发布状态的规格书可发起变更”。本项依据代码与错误信息的可见矛盾形成建议，不认定为规范违规。
- 问题说明：错误信息遗漏了新增的 A 版合法例外。
- 影响：调用方与排障人员可能误解完整准入条件。
- 建议：将信息同步为“A 版或已发布状态的规格书可发起变更”，并保留当前状态或版本等定位信息。

## 失败与降级

- 身份解析部分失败：`hisense-ids-app` 中以下提交无法唯一映射到规范用户，已跳过个人聚合、报告和投递：`744b475dab0a5b2acf5d9b91d003882feb8d892f`、`e91cbc952d894c612dcb5b22309b1cca11f8400b`、`e77270d3b25ed78ebc38be262d0f5098289ed089`、`e90ca0f57b1ad3f7bad3d615dbef7df1a2326407`、`273f8b66f417bab3ea5a1e2e5cb268838bd98e64`、`df362d25c7ea6c2be6078180a02350555241753d`。
- 同步、注册表绑定和规范读取均成功；公共规范与项目规范没有不可决冲突。
- 本报告仅陈述本次固定提交和可见差异的只读静态审查事实，不包含运行、测试或构建结论。
