# 2026-07-21 代码质量日报

## 用户与范围

- 用户：李玉泽（liyuze1）
- 时区：`Asia/Hong_Kong`
- 审查窗口：`2026-07-21 00:00:00+08:00`（含）至 `2026-07-22 00:00:00+08:00`（不含）
- 实际过滤条件：选择当前注册表全部有效且已启用项目；按窗口和固定提交筛选；未指定提交、分支、文件或目录过滤条件。
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

- `6171ea9a63b63c02ee52e03d94e9c72a23ad5a32`
- `e277c875e8a511a003f0641df52d00fd43474ac2`
- `713f0332b61cb16aa5c02854bda2cc28fd3e337c`

### `hisense-ids-app-spec`

- `6171ea9a63b63c02ee52e03d94e9c72a23ad5a32`
- `e277c875e8a511a003f0641df52d00fd43474ac2`
- `713f0332b61cb16aa5c02854bda2cc28fd3e337c`

### `hisense-ids-app-need`

范围内无提交。

## 汇总

- 本次成功处理项目数：3
- 该用户有提交的项目数：2
- 项目—提交关联数：6
- 唯一提交数：3

| 类别 | 发现数 |
| --- | ---: |
| 代码规范 | 0 |
| 可读性 | 4 |
| 健壮性 | 4 |
| 性能 | 0 |
| **合计** | **8** |

| 严重级别 | 数量 |
| --- | ---: |
| HIGH | 4 |
| MEDIUM | 2 |
| LOW | 2 |

## 发现

以下相同 SHA 分别属于两个注册项目的实际范围，因此按项目独立报告，不跨项目去重。

### `hisense-ids-app`：批量推送上限使用未命名字面量

- 项目：`hisense-ids-app`
- 提交：`6171ea9a63b63c02ee52e03d94e9c72a23ad5a32`
- 类别：可读性
- 严重级别：`LOW`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/masterdata/service/impl/DelistedFormJobServiceImpl.java:1032`
- 规则或代码证据：公共规则 `READ-004`。新增 `CollUtil.split(mdIds, 10)` 直接使用控制推送容量的字面值 `10`。
- 问题说明：批量上限的单位、用途和来源没有通过名称或配置表达。
- 影响：后续调整批量策略时难以判断该值是下游限制还是临时调优值，容易遗漏相关约束。
- 建议：提取为具名常量或受控配置，例如 `OTHER_PUSH_BATCH_SIZE`，并记录容量来源。

### `hisense-ids-app`：LEFT JOIN 可空字段被直接解引用

- 项目：`hisense-ids-app`
- 提交：`713f0332b61cb16aa5c02854bda2cc28fd3e337c`
- 类别：健壮性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/masterdata/service/impl/DelistedFormServiceImpl.java:442-443,3287-3288`；`hisense-app/src/main/resources/META-INF/sql/master_data.sql.xml:501-506,2428-2433`
- 规则或代码证据：公共规则 `ROBUST-001`。SQL 通过 `LEFT JOIN` 取得 `CPLX` 和 `NWX`，字段允许为 `null`；Java 新增行却直接执行 `mapMDdata.get(key).get("CPLX").toString()` 和 `get("NWX").toString()`。
- 问题说明：可空查询列在解包时没有缺失值分支。
- 影响：缺少产品小类或内外销属性的记录会触发空指针异常，中断退市校验流程。
- 建议：在首次读取处显式处理缺失值，并按契约选择跳过、可识别错误或有依据的默认值。

### `hisense-ids-app`：产品类别属性编码被同时写成属性值

- 项目：`hisense-ids-app`
- 提交：`713f0332b61cb16aa5c02854bda2cc28fd3e337c`
- 类别：可读性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/project/service/impl/ProductRoadmapServiceImpl.java:4850-4856`；`hisense-app/src/main/java/com/glaway/projectapply/service/impl/CombinationApplyServiceImpl.java:418-424`；配置证据 `hisense-common/src/main/java/com/glaway/config/MdCodeConfig.java:533-536`
- 规则或代码证据：公共规则 `READ-006`。注释和新增 `baseType` 配置表明默认值应为“基型产品”，两个入口却都把 `mdCodeConfig.getProductType()` 同时作为属性编码和属性值。
- 问题说明：实现写入属性编码，而不是注释和配置声明的“基型产品”值。
- 影响：两个产品型号创建入口都可能持久化错误的产品类别值。
- 建议：保留 `productTypeCode` 作为属性编码，使用经校验的 `mdCodeConfig.getBaseType()` 作为属性值，并复用同一转换逻辑。

### `hisense-ids-app`：可空配置值作为 `equals` 接收者

- 项目：`hisense-ids-app`
- 提交：`713f0332b61cb16aa5c02854bda2cc28fd3e337c`
- 类别：健壮性
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/masterdata/service/impl/MasterDataServiceImpl.java:3788-3794`
- 规则或代码证据：公共规则 `ROBUST-001`。新增条件直接调用 `mdCodeConfig.getStandardMachineModel().equals(dto.getCode())`，可见差异没有提供配置非空保证。
- 问题说明：缺失配置会在条件判断处被直接解引用。
- 影响：主数据创建过程可能因空指针异常中止。
- 建议：在配置加载边界明确必填或可选语义，并使用空值安全比较；允许缺失时显式跳过映射。

### `hisense-ids-app-spec`：批量推送上限使用未命名字面量

- 项目：`hisense-ids-app-spec`
- 提交：`6171ea9a63b63c02ee52e03d94e9c72a23ad5a32`
- 类别：可读性
- 严重级别：`LOW`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/masterdata/service/impl/DelistedFormJobServiceImpl.java:1032`
- 规则或代码证据：公共规则 `READ-004`；新增 `CollUtil.split(mdIds, 10)` 以未命名的 `10` 控制推送容量。
- 问题说明：容量策略没有表达单位、用途和来源。
- 影响：策略调整和约束追踪困难。
- 建议：提取为具名常量或受控配置，并记录下游容量依据。

### `hisense-ids-app-spec`：LEFT JOIN 可空字段被直接解引用

- 项目：`hisense-ids-app-spec`
- 提交：`713f0332b61cb16aa5c02854bda2cc28fd3e337c`
- 类别：健壮性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/masterdata/service/impl/DelistedFormServiceImpl.java:442-443,3287-3288`；`hisense-app/src/main/resources/META-INF/sql/master_data.sql.xml:501-506,2428-2433`
- 规则或代码证据：公共规则 `ROBUST-001`。`LEFT JOIN` 产生可空 `CPLX`、`NWX`，Java 代码直接调用其 `toString()`。
- 问题说明：可空列没有缺失值处理。
- 影响：属性缺失的记录会以空指针异常中断退市校验。
- 建议：在读取边界显式区分缺失值，并返回可识别错误或采用有依据的默认语义。

### `hisense-ids-app-spec`：产品类别属性编码被同时写成属性值

- 项目：`hisense-ids-app-spec`
- 提交：`713f0332b61cb16aa5c02854bda2cc28fd3e337c`
- 类别：可读性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/project/service/impl/ProductRoadmapServiceImpl.java:4850-4856`；`hisense-app/src/main/java/com/glaway/projectapply/service/impl/CombinationApplyServiceImpl.java:418-424`；配置证据 `hisense-common/src/main/java/com/glaway/config/MdCodeConfig.java:533-536`
- 规则或代码证据：公共规则 `READ-006`。注释和 `baseType` 配置声明默认值语义，代码却把 `productType` 同时作为编码和值。
- 问题说明：写入值与配置和注释表达的用途不一致。
- 影响：两个产品型号创建入口可能持久化错误的产品类别值。
- 建议：编码使用 `productType`，值使用经校验的 `baseType`，并统一转换实现。

### `hisense-ids-app-spec`：可空配置值作为 `equals` 接收者

- 项目：`hisense-ids-app-spec`
- 提交：`713f0332b61cb16aa5c02854bda2cc28fd3e337c`
- 类别：健壮性
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/masterdata/service/impl/MasterDataServiceImpl.java:3788-3794`
- 规则或代码证据：公共规则 `ROBUST-001`。代码直接调用 `mdCodeConfig.getStandardMachineModel().equals(...)`，没有静态非空保证。
- 问题说明：配置缺失时会直接解引用空值。
- 影响：主数据创建可能异常中止。
- 建议：在配置边界校验必填性，使用空值安全比较，并为可选配置建立明确分支。

## 失败与降级

- 注册表条目错误、项目同步失败、身份失败、规范冲突：均为 0。
- 本用户 Markdown 事实报告生成前置失败：0。
- `e277c875e8a511a003f0641df52d00fd43474ac2` 在两个项目中均无证据充分的发现。
