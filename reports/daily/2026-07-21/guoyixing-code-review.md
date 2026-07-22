# 2026-07-21 代码质量日报

## 用户与范围

- 用户：郭一行（guoyixing）
- 时区：`Asia/Hong_Kong`
- 审查窗口：`2026-07-21 00:00:00+08:00`（含）至 `2026-07-22 00:00:00+08:00`（不含）
- 实际过滤条件：选择当前注册表全部有效且已启用项目；按窗口和各项目本次固定提交筛选；未指定提交、分支、文件或目录过滤条件。
- 证据边界：仅使用本次冻结快照、直接同步结果、固定提交、可见差异和必要的最少上下文；未读取未提交内容，未执行目标项目。

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

- `b23122fd0d444765f6aae4c628eb5a91da2b1f2c`
- `49faa535daf1828bbfeb2ebf2a87470328a41123`

### `hisense-ids-app-spec`

- `e935b302f741a7096fc3efdff4453155c8e373d4`
- `acfe338807c6ed16ea6917bef23f756f1448ae8a`
- `d586aa1a53819ccb75cd7778b953d8b5022f06ff`

### `hisense-ids-app-need`

范围内无提交。

## 汇总

- 本次成功处理项目数：3
- 该用户有提交的项目数：2
- 项目—提交关联数：5
- 唯一提交数：5

| 类别 | 发现数 |
| --- | ---: |
| 代码规范 | 0 |
| 可读性 | 1 |
| 健壮性 | 1 |
| 性能 | 1 |
| **合计** | **3** |

| 严重级别 | 数量 |
| --- | ---: |
| HIGH | 1 |
| MEDIUM | 1 |
| LOW | 1 |

## 发现

### 激活版本更新仍是非原子的检查后执行

- 项目：`hisense-ids-app`
- 提交：`49faa535daf1828bbfeb2ebf2a87470328a41123`
- 类别：健壮性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/masterdata/service/impl/MasterDataWorkFlowServiceImpl.java:463-464,503-551`
- 规则或代码证据：公共规则 `ROBUST-007`。代码先在内存中激活新版，再查询并逐项停用其他版本；新版直到外层后续更新才明确持久化。可见差异中没有数据库唯一约束、锁或带条件的原子更新。
- 问题说明：两个并发变更可能在对方新版写入前都读取到相同旧状态，随后分别持久化各自新版。
- 影响：同一 `masterId` 仍可能出现多个 `available=1` 的版本，或者并发流程错误停用彼此刚创建的版本。
- 建议：在数据库侧建立唯一性约束，或按 `masterId` 在同一事务中通过行锁或条件更新原子完成“停用旧版并激活新版”，并校验更新行数。

### 逐版本停用形成线性增长的数据库访问

- 项目：`hisense-ids-app`
- 提交：`49faa535daf1828bbfeb2ebf2a87470328a41123`
- 类别：性能
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/masterdata/service/impl/MasterDataWorkFlowServiceImpl.java:521-533,560-569`
- 规则或代码证据：公共规则 `PERF-001`、`PERF-003`。`otherActiveVersions.forEach(this::deactivateVersion)` 对每个版本分别更新版本、调用 `getChildLink()` 查询关联，并再次更新关联集合。
- 问题说明：数据库往返次数随其他激活版本数量线性增长。
- 影响：历史异常版本越多，流程结束耗时和数据库负载越大，同时放大并发窗口。
- 建议：一次收集版本 ID，批量停用版本、批量加载关联并批量更新 `deleteMark`；同时通过唯一性约束阻止异常集合继续增长。

### 下载地址注释与回退实现不一致

- 项目：`hisense-ids-app-spec`
- 提交：`d586aa1a53819ccb75cd7778b953d8b5022f06ff`
- 类别：可读性
- 严重级别：`LOW`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/specification/service/handler/SpecExternalPushHandler.java:777-788`
- 规则或代码证据：公共规则 `READ-006`。方法说明写明前缀未配置或 `fileId` 为空时返回 `null`，实现却在前缀为空时返回裸 `fileId`。
- 问题说明：文档与实际返回语义冲突，并把仅有标识符的字符串放入 `fileUrl`。
- 影响：维护者和调用方无法依据方法契约判断是否获得可用下载地址。
- 建议：按契约在前缀为空时返回 `null`；若外部契约确实允许裸标识符，则同步调整字段命名、注释和接口说明。

## 失败与降级

- 注册表条目错误、项目同步失败、身份失败、规范冲突：均为 0。
- 本用户 Markdown 事实报告生成前置失败：0。
- `acfe338807c6ed16ea6917bef23f756f1448ae8a` 是普通合并提交，未证明候选问题由独有冲突解决引入，因此不把第一父差异重复归给合并作者。
- 该合并提交中的未声明局部变量已由同窗口后续提交 `e935b302f741a7096fc3efdff4453155c8e373d4` 修复并进入冻结源码，不生成历史缺陷发现。
