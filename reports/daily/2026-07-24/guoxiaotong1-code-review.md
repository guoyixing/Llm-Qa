# 代码审查日报

## 用户与范围

- 用户：郭晓彤（guoxiaotong1）
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

- `d11a492809b2f848a3a3b68dc299eb8ffbb1936b`
- `5ed21de990f6b9acfb5b30c1c5860b5451ab4828`
- `2a3984e3684e16ff62748222729650ef6e8aeecd`
- `d1f092b89b6abf5dfe842350cb924a4ed4382a7d`

### `hisense-ids-app-spec`

- `d11a492809b2f848a3a3b68dc299eb8ffbb1936b`
- `5ed21de990f6b9acfb5b30c1c5860b5451ab4828`
- `2a3984e3684e16ff62748222729650ef6e8aeecd`
- `d1f092b89b6abf5dfe842350cb924a4ed4382a7d`

### `hisense-ids-app-need`

该用户范围内无提交。

### `hisense-ids-app-function`

范围内无提交。

## 汇总

- 本次覆盖项目：4 个；该用户有提交项目：2 个
- 项目—提交发生项：8；唯一 SHA：4
- 发现合计：4
  - 代码规范：0
  - 可读性：0
  - 健壮性：2
  - 性能：2

## 发现

### 1. 回退提交移除了外部输入和路由校验

- 项目：`hisense-ids-app`
- 提交：`d1f092b89b6abf5dfe842350cb924a4ed4382a7d`
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-interface/src/main/java/com/glaway/cost/service/impl/CostInteractiveServiceImpl.java:47-55,112-120,155-170`
- 规则或代码证据：公共规则 `ROBUST-001`、`ROBUST-002`。该提交删除 `INTAB` 空集合校验和三处空 `requestCode` 校验，并恢复为直接访问 `querySapMatnrInfo.getINTAB().get(0)`。
- 问题说明：空集合和未知 SAP 标识不再在边界转换为明确失败。
- 影响：外部异常输入会产生非预期空指针或越界错误，或携带空路由编码继续处理，根因难以定位。
- 建议：恢复分层输入检查和未知 SAP 标识的明确业务异常。窗口内后续提交 `2a3984e3684e16ff62748222729650ef6e8aeecd` 已恢复这些保护，但不改变本提交引入问题的事实。

### 2. 回退提交恢复了无界配置表查询

- 项目：`hisense-ids-app`
- 提交：`d1f092b89b6abf5dfe842350cb924a4ed4382a7d`
- 类别：性能
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/service/impl/CostSapFactoryConfigServiceImpl.java:219-230`
- 规则或代码证据：公共规则 `PERF-005`。该提交删除 `Paging(1, 1000)` 上限，改为 `.operate().query()` 后把全部结果装入 `HashMap`。
- 问题说明：持续增长的配置表被一次性无界读取。
- 影响：配置数据异常增长时，数据库返回量和应用内存驻留均无硬上限。
- 建议：保留有界分页并明确截断策略，或按实际所需生产基地编码批量查询。窗口内后续提交 `2a3984e3684e16ff62748222729650ef6e8aeecd` 已恢复 1000 条上限。

### 3. 回退提交移除了外部输入和路由校验

- 项目：`hisense-ids-app-spec`
- 提交：`d1f092b89b6abf5dfe842350cb924a4ed4382a7d`
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-interface/src/main/java/com/glaway/cost/service/impl/CostInteractiveServiceImpl.java:47-55,112-120,155-170`
- 规则或代码证据：公共规则 `ROBUST-001`、`ROBUST-002`。该提交删除 `INTAB` 空集合校验和三处空 `requestCode` 校验，并恢复为直接访问 `querySapMatnrInfo.getINTAB().get(0)`。
- 问题说明：空集合和未知 SAP 标识不再在边界转换为明确失败。
- 影响：外部异常输入会产生非预期空指针或越界错误，或携带空路由编码继续处理，根因难以定位。
- 建议：恢复分层输入检查和未知 SAP 标识的明确业务异常。窗口内后续提交 `2a3984e3684e16ff62748222729650ef6e8aeecd` 已恢复这些保护，但不改变本项目—提交发生项的审查结论。

### 4. 回退提交恢复了无界配置表查询

- 项目：`hisense-ids-app-spec`
- 提交：`d1f092b89b6abf5dfe842350cb924a4ed4382a7d`
- 类别：性能
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/service/impl/CostSapFactoryConfigServiceImpl.java:219-230`
- 规则或代码证据：公共规则 `PERF-005`。该提交删除 `Paging(1, 1000)` 上限，改为 `.operate().query()` 后把全部结果装入 `HashMap`。
- 问题说明：持续增长的配置表被一次性无界读取。
- 影响：配置数据异常增长时，数据库返回量和应用内存驻留均无硬上限。
- 建议：保留有界分页并明确截断策略，或按实际所需生产基地编码批量查询。窗口内后续提交 `2a3984e3684e16ff62748222729650ef6e8aeecd` 已恢复 1000 条上限。

## 规范加载与失败

- 规范加载顺序：`standards/common/`，随后加载各项目注册的 `standards_dir`
- 规范冲突或降级：无；项目规则均为公共规则的补充
- 注册表、同步、身份解析和规范读取均无失败。
- `hisense-ids-app-need` 中该用户范围内无提交；`hisense-ids-app-function` 整体范围内无提交。
- 两个项目中的问题均已在同一窗口后续提交恢复；本报告仍按引入提交保留事实，不追踪跨日状态。
