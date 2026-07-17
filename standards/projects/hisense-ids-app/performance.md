# 海信 IDS 应用项目性能规范

本文件由使用者明确要求基于当前代码和本地知识库配置，仅补充 `standards/common/`，不覆盖任何公共规则。规则适用于 `project-registry.yaml` 中 `project_id=hisense-ids-app` 的项目，只约束可静态核验的技术质量，不判断业务规则是否正确。

### hisense-ids-app-PERF-001 IBA 集合查询使用项目批量能力

- 标签：hisense-ids-app-PERF-001
- 级别：REQUIRED
- 适用范围：新增或修改的 IBA 值、类型属性定义和数据字典组集合查询
- 规则：多个 BizId、InstanceId、属性编码或字典组 ID 的查询必须先去除空值并去重，再使用 `IbaValueQueryUtil`、`TypeAttrDefinitionQueryUtil` 或等价批量查询；Oracle `IN` 参数每批不得超过项目约定的 500 条。调用方必须区分 BizId 与迭代 InstanceId，不得把二者混用。本规则细化公共规则 `PERF-001`、`PERF-003` 和 `PERF-005`。
- 例外：调用点可静态证明集合最多只有一个元素时可以使用单对象查询；非 Oracle 数据源不受 500 条约束，但仍不得形成逐项查询。
- 检查重点：循环内 IBA 查询、`IN` 参数来源和批次大小、空值与重复键、BizId/InstanceId 方法选择、批次结果是否正确合并。
- 建议：优先调用现有工具的 `queryByBizIds`、`queryByInstanceIds`、`querySingleAttrByBizIds` 或 `queryByCodes`，不要在业务服务中重复实现分批 SQL。
- 来源：`data/code/hisense-ids-app/hisense-app/src/main/java/com/glaway/common/utils/IbaValueQueryUtil.java:25-46,86-198`；`data/code/hisense-ids-app/hisense-app/src/main/java/com/glaway/common/utils/TypeAttrDefinitionQueryUtil.java:25-46,94-188`

### hisense-ids-app-PERF-002 规格书多行处理先批量加载并建立索引

- 标签：hisense-ids-app-PERF-002
- 级别：REQUIRED
- 适用范围：规格书详情、矩阵、导出、对比、推送和生产版本详情中，由外部输入决定数量且会处理多个 mdRel、属性或引用值的路径
- 规则：存在数据库或远程读取时，必须先收集当前受控批次内的 mdRel、BizId、属性编码或唯一引用值，执行有界批量加载，再按 `specMdRelId + attrCode` 或对应稳定键建立索引后回填；不得在行、单元格或属性循环中逐项访问数据库、网络或文件。本规则细化公共规则 `PERF-001`、`PERF-003`、`PERF-004` 和 `PERF-005`。
- 例外：入口契约可静态证明最多处理一个对象，或循环体只有纯内存索引读取与转换时，可以不增加批量 I/O 层。
- 检查重点：输入规模是否受外部控制、I/O 是否位于单元格循环内、批量结果是否按双键索引、批次是否有界、引用值是否先去重。
- 建议：复用 `IbaValueQueryUtil`、`SpecAttrValueIndexUtil` 以及引用/字典处理器的 `ResolverBuilder`，一次 build 后完成回填。
- 来源：`data/code/hisense-ids-app/hisense-app/src/main/java/com/glaway/specification/util/SpecAttrValueIndexUtil.java:12-61`；`data/code/hisense-ids-app/hisense-app/src/main/java/com/glaway/specification/service/handler/SpecPushCreateHandler.java:1533-1567`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜规格书矩阵视图性能优化.md:9-35`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜规格书引用属性中文名称批量转换.md:9-35`
