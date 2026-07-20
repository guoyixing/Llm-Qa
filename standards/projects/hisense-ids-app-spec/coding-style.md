# 海信 IDS 应用-结构化分支项目编码规范

本文件由使用者明确要求基于当前代码和本地知识库配置，仅补充 `standards/common/`，不覆盖任何公共规则。规则适用于 `project-registry.yaml` 中 `project_id=hisense-ids-app-spec` 的项目，只约束可静态核验的技术质量，不判断业务规则是否正确。

### hisense-ids-app-spec-STYLE-001 集成模块保持单向依赖

- 标签：hisense-ids-app-spec-STYLE-001
- 级别：REQUIRED
- 适用范围：`hisense-interface` 模块新增或修改的接口、适配器、控制器、服务及其参数和返回类型
- 规则：`hisense-interface` 不得直接依赖或导入 `hisense-app` 的实现模型与服务类型；跨模块契约必须使用 `hisense-common` 中的共享值对象、`hisense-interface` 自有契约或稳定标识，并通过既有接口完成业务调用。本规则补充公共规则 `STYLE-004` 和 `READ-002`，不构成覆盖。
- 例外：只有在模块拓扑被正式调整，且同一变更同步更新 Maven 依赖、共享契约和架构说明时，才允许引入新的模块依赖。
- 检查重点：`hisense-interface/pom.xml` 的直接依赖、新增 import 的所属模块、接口签名是否暴露 `hisense-app` 实现类型、共享 DTO 是否放在正确模块。
- 建议：把跨模块值对象、枚举或常量下沉到 `hisense-common`，或在 `hisense-interface` 定义只包含所需字段的契约；仅需定位对象时传递 ID 或 BizId。
- 来源：`data/code/hisense-ids-app-spec/hisense-interface/pom.xml:21-34`；`data/code/hisense-ids-app-spec/hisense-interface/src/main/java/com/glaway/gsssalesmodel/service/MdgPushAdapter.java:33-40`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/实体/实体｜hisense-interface模块.md:9-23`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/实体/实体｜hisense-common模块.md:9-29`

### hisense-ids-app-spec-STYLE-002 规格书写操作收敛到对应 Handler

- 标签：hisense-ids-app-spec-STYLE-002
- 级别：REQUIRED
- 适用范围：`hisense-app` 中新增或修改的规格书创建、修改、升版和删除入口及其调用链
- 规则：规格书创建必须由 `SpecCreateHandler` 处理，修改必须由 `SpecModifyHandler` 处理，升版必须由 `SpecChangeHandler` 处理，删除必须由 `SpecDeleteHandler` 处理。Service、Controller、Adapter、流程回调、导入处理器及其他外层编排代码只能完成入参转换、权限或流程编排并委派给对应 Handler，不得绕过 Handler 直接新增、更新、复制或删除规格书主体、主数据关系、属性、生产版本清单和查询投影，也不得在外部复制对应 Handler 的持久化流程。
- 例外：无。确需调整职责边界时，必须在同一变更中迁移完整事务流程、全部调用入口和架构说明，不得保留并行写入实现。
- 检查重点：规格书写入口是否调用对应 Handler；`PersistHelper`、规格书模型写方法和查询投影刷新是否出现在对应 Handler 之外；批量导入、审批回调和定时或消息处理是否复制创建、修改、升版或删除逻辑；新增写入口是否绕过既有事务边界。
- 建议：外层入口只组装对应 Value 对象并调用 Handler 的公开方法；批量场景由批量编排器逐项或批量调用对应 Handler，通用子步骤应下沉为 Handler 内部方法或由 Handler 依赖的专用组件。
- 来源：`data/code/hisense-ids-app-spec/hisense-app/src/main/java/com/glaway/specification/service/handler/SpecCreateHandler.java:93-129`；`data/code/hisense-ids-app-spec/hisense-app/src/main/java/com/glaway/specification/service/handler/SpecModifyHandler.java:74-108`；`data/code/hisense-ids-app-spec/hisense-app/src/main/java/com/glaway/specification/service/handler/SpecChangeHandler.java:67-108`；`data/code/hisense-ids-app-spec/hisense-app/src/main/java/com/glaway/specification/service/handler/SpecDeleteHandler.java:19-79`；`data/code/hisense-ids-app-spec/hisense-app/src/main/java/com/glaway/specification/service/impl/SpecServiceImpl.java:397-512`
