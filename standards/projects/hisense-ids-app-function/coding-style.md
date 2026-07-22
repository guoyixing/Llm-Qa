# 海信 IDS 应用功能分支项目编码规范

本文件仅补充 `standards/common/`，不覆盖任何公共规则，仅适用于 `project-registry.yaml` 中 `project_id=hisense-ids-app-function` 的项目，只约束可静态核验的技术质量，不判断功能生命周期、工作流、数据来源或权限等业务规则是否正确。

### hisense-ids-app-function-STYLE-001 功能领域实现必须遵守已验证的模块与包边界

- 标签：hisense-ids-app-function-STYLE-001
- 级别：REQUIRED
- 适用范围：功能库与产品功能清单相关的领域模型、持久化、服务、控制器、监听器、定时任务、外部契约、Feign 客户端和外部适配器的新增或修改
- 规则：功能库与产品功能清单的领域模型、持久化、服务、控制器、监听器和定时任务必须保留在 `hisense-app`，并分别位于 `com.glaway.functionlib` 或 `com.glaway.functionchecklist` 领域包内；面向外部系统的契约、Feign 客户端、交互控制器或适配器必须保留在 `hisense-interface`，不得把功能领域持久化实现移入该外部集成模块，也不得把外部集成实现混入上述领域包。本规则补充公共规则 `STYLE-004` 和 `READ-002`，不构成覆盖，且不降低其效力。
- 例外：只有存在可定位且已批准的项目架构决策记录，明确调整模块或包职责，并在同一变更中同步更新根 POM、相关模块 POM、启动入口或启动配置及架构说明时，才允许改变上述边界。
- 检查重点：核对新增或移动文件所属 Maven 模块及 `package` 声明，确认功能库代码位于 `hisense-app/src/main/java/com/glaway/functionlib/`、产品功能清单代码位于 `hisense-app/src/main/java/com/glaway/functionchecklist/`；检查 `hisense-interface` 是否只承载外部契约与集成入口，领域服务中的持久化是否误移至外部集成模块；如职责调整，确认批准记录和同一变更内的 POM、启动配置与架构说明完整。当前 `FunctionController`、`FunctionServiceImpl`、`FunctionWorkFlowServiceImpl`、`FunctionChecklistController`、`FunctionChecklistItemController`、`FunctionChecklistServiceImpl` 和 `FunctionChecklistItemServiceImpl` 仅作为检查入口，不要求这些类名长期不变。
- 建议：把功能库领域实现放入 `hisense-app/src/main/java/com/glaway/functionlib/`，把产品功能清单领域实现放入 `hisense-app/src/main/java/com/glaway/functionchecklist/`，把面向外部系统的契约、Feign 客户端、交互控制器或适配器放入 `hisense-interface` 对应集成包，并让持久化调用留在领域服务边界内。
- 来源：`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/实体/实体｜功能库.md:9-10`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/实体/实体｜功能库.md:22-28`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/实体/实体｜产品功能清单.md:9-10`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/实体/实体｜产品功能清单.md:26-36`；`data/code/hisense-ids-app-function/pom.xml:13-25`；`data/code/hisense-ids-app-function/hisense-app/pom.xml:13-27`；`data/code/hisense-ids-app-function/hisense-app/pom.xml:29-69`；`data/code/hisense-ids-app-function/hisense-interface/pom.xml:13-34`；`data/code/hisense-ids-app-function/hisense-interface/pom.xml:38-75`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionlib/controller/FunctionController.java:1-24`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionlib/service/impl/FunctionServiceImpl.java:1-54`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionchecklist/service/impl/FunctionChecklistServiceImpl.java:1-38`

### hisense-ids-app-function-STYLE-002 每条领域写流程必须有且仅有一个编排所有者

- 标签：hisense-ids-app-function-STYLE-002
- 级别：REQUIRED
- 适用范围：功能库与产品功能清单的新增、修改、删除、版本变更、流程发起、流程回调、状态回写、清单行项写入及其由 Controller、Job、Listener 或外部适配器触发的写调用链
- 规则：每个领域聚合或跨聚合写流程必须有且仅有一个领域服务作为写编排所有者，由其统一组织校验、模型构建、主对象与版本对象写入、关联行项写入、流程记录、状态回写和持久化顺序。Controller、Job、Listener 和外部适配器只能完成入参转换与外层委派，不得直接调用 `PersistHelper` 或等价持久化入口，也不得复制编排所有者负责的多步写流程。流程记录或行项等专用领域服务可以拥有自身聚合的写入，但调用链中必须明确由一个上层所有者组织跨聚合顺序。本规则补充公共规则 `STYLE-004`、`READ-002` 和 `READ-006`，不构成覆盖，且不降低其效力。
- 例外：无。确需调整某条写流程的编排所有者时，必须在同一变更中迁移完整写流程、全部调用入口及描述该职责的注释或文档，不得保留并行写实现。
- 检查重点：沿 Controller、Job、Listener 和外部适配器入口检查每条写调用链是否只有一个可定位的编排所有者，外层是否出现 `PersistHelper` 或等价持久化调用，是否复制模型构建、版本切换、流程记录、状态回写或行项写入顺序，专用服务之间的调用是否仍由一个上层所有者组织。当前 `FunctionController`、`FunctionServiceImpl`、`FunctionWorkFlowServiceImpl`、`FunctionChecklistServiceImpl` 和 `FunctionChecklistItemServiceImpl` 是定位所有者及协作者的检查入口，不要求这些类名长期不变；职责变化时还应按 `READ-006` 核对相关注释是否同步。
- 建议：让外层入口只构造 Value 或命令对象并调用领域服务公开写方法；把重复持久化步骤下沉为编排所有者的私有方法，或由其调用职责单一的流程记录、清单行项等专用服务，避免形成第二套写流程。
- 来源：`standards/common/coding-style.md:53-62` 中的公共规则 `STYLE-004`；`standards/common/readability.md:31-40` 中的公共规则 `READ-002`；`standards/common/readability.md:75-84` 中的公共规则 `READ-006`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionlib/controller/FunctionController.java:68-129`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionlib/service/impl/FunctionServiceImpl.java:118-247`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionlib/service/impl/FunctionServiceImpl.java:405-547`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionlib/service/impl/FunctionServiceImpl.java:549-628`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionlib/service/impl/FunctionWorkFlowServiceImpl.java:45-79`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionlib/service/impl/FunctionWorkFlowServiceImpl.java:138-231`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionchecklist/service/impl/FunctionChecklistServiceImpl.java:112-184`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionchecklist/service/impl/FunctionChecklistServiceImpl.java:233-399`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionchecklist/service/impl/FunctionChecklistItemServiceImpl.java:60-163`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionchecklist/service/impl/FunctionChecklistItemServiceImpl.java:193-315`

### hisense-ids-app-function-STYLE-003 生命周期、工作流与数据来源常量宜集中维护

- 标签：hisense-ids-app-function-STYLE-003
- 级别：ADVISORY
- 适用范围：`com.glaway.functionlib` 与 `com.glaway.functionchecklist` 中表达生命周期状态、流程状态、流程 Key、流程变量名、签署表编码和数据来源的新增或修改代码
- 规则：建议把同一领域内复用的生命周期、工作流和数据来源字面值集中在对应的常量类或枚举中，并由调用方引用同一符号；常量名称、注释和枚举映射应与当前实现一致。该要求是根据现有实现形成的工程归纳，只能作为改进建议，不能据此报告规范违规。本规则补充公共规则 `STYLE-004`、`READ-004` 和 `READ-006`，不构成覆盖，且不降低其效力。
- 例外：框架 API 明确要求且只在单个局部使用、没有跨调用方共享语义的字面值可以就地保留；由生成代码或外部依赖定义且项目不得重新声明的常量可直接引用其原始符号。
- 检查重点：检查同一生命周期状态、流程状态、流程 Key、流程变量名、签署表编码或数据来源是否在多个类中重复写成字符串，是否已有对应常量却仍使用字面值，常量与枚举映射是否重复或冲突，修改实现时注释是否按 `READ-006` 同步。当前 `FunctionLibConstant`、`FunctionLifecycleStateEnum`、`FunctionChecklistConstant` 和 `FunctionChecklistLifecycleStateEnum` 仅作为检查入口，不要求这些类名或拆分方式长期不变，也不据此判断具体业务取值是否正确。
- 建议：优先复用所属领域的现有常量或枚举；新增共享字面值时放入职责相符的常量类，命名中表达用途而非具体调用方，并同步替换重复字面值和更新相关注释。
- 来源：工程归纳，依据 `data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionlib/constant/FunctionLibConstant.java:18-114`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionlib/constant/FunctionLibConstant.java:116-253`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionlib/constant/FunctionLifecycleStateEnum.java:6-38`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionchecklist/constant/FunctionChecklistConstant.java:18-66`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionchecklist/constant/FunctionChecklistConstant.java:91-106`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionchecklist/constant/FunctionChecklistLifecycleStateEnum.java:6-32`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionlib/service/impl/FunctionServiceImpl.java:405-547`；`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionchecklist/service/impl/FunctionChecklistItemServiceImpl.java:60-120`；`standards/common/coding-style.md:53-62` 中的公共规则 `STYLE-004`；`standards/common/readability.md:53-62` 中的公共规则 `READ-004`；`standards/common/readability.md:75-84` 中的公共规则 `READ-006`
