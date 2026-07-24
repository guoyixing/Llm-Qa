# 2026-07-23 手动代码审查报告

## 用户与范围

- 用户：郭晓彤（guoxiaotong1）
- 时区：`Asia/Hong_Kong`
- 报告日期依据：显式提交范围中最早的 Git Author Date 转换为香港本地日期后为 `2026-07-23`
- 实际过滤条件：项目 `hisense-ids-app`；显式提交 `273f8b66f417bab3ea5a1e2e5cb268838bd98e64`、`df362d25c7ea6c2be6078180a02350555241753d`；未指定日期、分支、文件或目录过滤
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
  - `273f8b66f417bab3ea5a1e2e5cb268838bd98e64`
  - `df362d25c7ea6c2be6078180a02350555241753d`

## 汇总

| 指标 | 数量 |
|---|---:|
| 实际审查项目数 | 1 |
| 实际审查提交数 | 2 |
| 代码规范发现 | 0 |
| 可读性发现 | 0 |
| 健壮性发现 | 4 |
| 性能发现 | 1 |
| 发现总数 | 5 |

严重级别：`HIGH` 1 条、`MEDIUM` 4 条。

## 发现

### 端到端工时查询校验了 SAP 地址但未写入请求参数

- 项目：`hisense-ids-app`
- 提交：`273f8b66f417bab3ea5a1e2e5cb268838bd98e64`
- 类别：健壮性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/ecost/service/impl/E2eCostServiceImpl.java:675-682`；关联路由证据 `hisense-interface/src/main/java/com/glaway/cost/service/impl/CostInteractiveServiceImpl.java:103-115`
- 规则或代码证据：`E2eCostServiceImpl` 查询并校验 `sapAddress` 非空，但没有调用 `param.setSAPADDRESS(sapAddress)`；同提交的工时接口路由从 `querySapManHour.getSAPADDRESS()` 读取标识，并在未匹配三个已知值时保持 `requestCode=""`。
- 问题说明：该端到端路径创建的 `SapManHourValue` 缺少路由所需的 `SAPADDRESS`，与同提交中其他工时查询路径的赋值方式不一致。
- 影响：该路径进入工时接口后无法选择任何已配置 SAP 路由，并会以空字符串调用 `queryUrlByRequestCode`，从而不能可靠发起目标 SAP 工时查询。
- 建议：在非空校验后、调用工时接口前执行 `param.setSAPADDRESS(sapAddress)`，确保请求对象携带已经确认的路由标识。

### 未知 SAP 标识被转换为空请求编码后继续查询

- 项目：`hisense-ids-app`
- 提交：`273f8b66f417bab3ea5a1e2e5cb268838bd98e64`
- 类别：健壮性
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-interface/src/main/java/com/glaway/cost/service/impl/CostInteractiveServiceImpl.java:39-50,103-115,158-172`
- 规则或代码证据：三处接口路由均以 `String requestCode = ""` 初始化，只为 `SAP_GROUP_600`、`SAP_GROUP_700` 和 `SAP_GROUP_900` 赋值；未知非空标识不进入失败分支，而是继续调用 `queryUrlByRequestCode(Collections.singletonList(requestCode))`。该行为不符合公共规则 `ROBUST-004` 对失败显式传播的要求。
- 问题说明：配置值非空但不属于已支持标识时，代码没有拒绝该值或返回可识别错误，而是把空请求编码传给下游配置查询。
- 影响：无效配置不会在路由边界被准确定位，后续行为取决于空键查询结果，可能掩盖真实的 SAP 标识配置错误。
- 建议：将路由选择改为完整的互斥分支；未匹配支持列表时立即抛出包含稳定上下文的业务异常，禁止使用空字符串继续查询。

### 配置写入唯一键与读取条件不一致，结果取决于无排序首项

- 项目：`hisense-ids-app`
- 提交：`df362d25c7ea6c2be6078180a02350555241753d`
- 类别：健壮性
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/service/impl/CostSapFactoryConfigServiceImpl.java:107-114,187-200,224-242`
- 规则或代码证据：新增时按 `productionBaseCode`、`productCompanyCode`、`domesticExport` 组合检查重复；`getSapAddressByProductionBase` 只按 `productionBaseCode` 查询并返回 `query.get(0)`，全量映射同样对相同生产基地保留查询迭代中的第一条，且两处均没有排序或多结果错误处理。
- 问题说明：写入逻辑允许同一生产基地对应不同产品公司或内外销配置，但读取逻辑丢失这些区分字段并任意选择首条记录。
- 影响：存在多个合法组合配置时，同一生产基地可能得到与调用上下文不对应的 SAP 地址；结果还可能随数据库返回顺序变化。
- 建议：让读取接口接收并使用与写入唯一键一致的产品公司、生产基地和内外销条件；查询返回多条时显式报错，不得使用无排序首项或“首次写入 Map”的方式消解冲突。

### 分页参数未经边界校验直接传入查询

- 项目：`hisense-ids-app`
- 提交：`df362d25c7ea6c2be6078180a02350555241753d`
- 类别：健壮性
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/service/impl/CostSapFactoryConfigServiceImpl.java:53-54,82-86`
- 规则或代码证据：公共规则 `ROBUST-002` 要求分页覆盖最小值、最大值和越界输入。代码直接从请求值读取 `currentPage`、`pageSize` 并构造 `Paging`，没有验证页码至少为 1，也没有为每页条数设置最大值。
- 问题说明：请求可以覆盖值对象中的默认分页值，并将零、负数或过大的分页参数传入持久化查询层。
- 影响：非法页码的处理完全依赖下层实现；过大的 `pageSize` 会破坏分页查询的数据量边界，增加单次查询与结果映射负担。
- 建议：在构造 `Paging` 前要求 `currentPage >= 1`，并将 `pageSize` 限制在具名且可定位的正数上限内；非法值应返回明确参数错误。

### 新增控制器入口无分页返回全部 SAP 工厂配置

- 项目：`hisense-ids-app`
- 提交：`df362d25c7ea6c2be6078180a02350555241753d`
- 类别：性能
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/cost/controller/CostSapFactoryConfigController.java:35-43`；`hisense-app/src/main/java/com/glaway/cost/service/impl/CostSapFactoryConfigServiceImpl.java:41-48`
- 规则或代码证据：公共规则 `PERF-005` 禁止对持续增长的数据进行无界读取。新增控制器公开“无分页”入口，服务方法执行没有筛选、分页或条数上限的完整查询，并将全部模型映射后一次返回。
- 问题说明：该请求的数据读取、对象映射和响应规模随配置表记录数直接增长，没有可定位的固定小集合契约。
- 影响：配置量增长后，单次请求会增加数据库读取、服务内存占用、对象转换和响应序列化成本。
- 建议：将公开入口改为带硬性 `pageSize` 上限的分页查询；如内部确需遍历全部配置，应使用受控分批处理，不应通过控制器一次返回完整集合。

## 失败与降级

- 身份解析成功：2 个提交均唯一映射到郭晓彤（guoxiaotong1），未发生姓名不一致。
- 规范读取成功：已按公共规范再到 `standards/projects/hisense-ids-app` 的顺序加载，没有不可决冲突。
- 报告生成范围：仅生成本 Markdown；按照用户确认的手动审查方式，不生成 HTML、不发送邮件。
- 本报告仅陈述本次固定提交和可见差异的只读静态审查事实，不包含运行、测试、构建或远端新鲜度结论。
