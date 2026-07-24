# 海信 IDS 应用需求分支项目编码规范

本文件仅补充 `standards/common/`，不覆盖任何公共规则，仅适用于 `project-registry.yaml` 中 `project_id=hisense-ids-app-need` 的项目，只约束可静态核验的技术质量，不判断业务规则是否正确。

### hisense-ids-app-need-STYLE-001 需求实现不得写入仅部署的 hisense-requirement

- 标签：hisense-ids-app-need-STYLE-001
- 级别：REQUIRED
- 适用范围：需求管理相关模块新增或修改的领域模型、持久化、服务、控制器、监听器、SQL、外部契约、Feign 客户端和适配器
- 规则：需求领域模型、持久化、服务和控制器必须保留在 `hisense-app` 的 `requirement` 或 `requirementlist` 包，外部契约、Feign 客户端和适配器必须保留在 `hisense-interface`；仅用于部署的 `hisense-requirement` 不得新增业务模型、服务、控制器、监听器或 SQL。本规则补充公共规则 `STYLE-004` 和 `READ-002`，不构成覆盖。
- 例外：只有存在可定位且已批准的项目架构决策记录，明确批准改变 `hisense-requirement` 的部署模块职责，并在同一变更中同步更新根 POM 与相关模块 POM、启动入口或启动配置以及架构说明时，才允许把上述业务实现写入该模块。
- 检查重点：核对新增文件的模块及包路径、`hisense-requirement` 是否出现业务模型、服务、控制器、监听器或 SQL、外部契约与 Feign 或适配器是否误入 `hisense-app`；如调整职责，确认项目架构决策记录可定位且已批准，并确认同一变更已更新根 POM 与相关模块 POM、启动入口或启动配置以及架构说明。
- 建议：把需求领域实现放入 `hisense-app/src/main/java/com/glaway/requirement/` 或 `hisense-app/src/main/java/com/glaway/requirementlist/`，把外部契约、Feign 客户端和适配器放入 `hisense-interface`，让 `hisense-requirement` 只保留启动与部署配置。
- 来源：`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/实体/实体｜hisense-requirement模块.md:9-39`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/实体/实体｜需求清单模块.md:11-20`；`data/code/hisense-ids-app-need/pom.xml:13-25`；`data/code/hisense-ids-app-need/hisense-requirement/pom.xml:12-31`；`data/code/hisense-ids-app-need/hisense-requirement/pom.xml:33-83`；`data/code/hisense-ids-app-need/hisense-requirement/src/main/resources/application.yml:1-20`；`data/code/hisense-ids-app-need/hisense-interface/pom.xml:13-34`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/RawRequirementServiceImpl.java:103-151`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementServiceImpl.java:122-170`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementAssistServiceImpl.java:71-86`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirementlist/service/impl/RequirementChecklistServiceImpl.java:86-117`

### hisense-ids-app-need-STYLE-002 需求写操作必须收敛到领域服务入口

- 标签：hisense-ids-app-need-STYLE-002
- 级别：REQUIRED
- 适用范围：需求与需求清单的新增、修改、删除、状态流转、版本变更、分发及其由 Controller、Job、Listener、Adapter 或工作流回调触发的写调用链
- 规则：每个需求聚合或跨聚合写工作流必须有且仅有一个领域写编排所有者，由其统一组织模型构建、关联对象写入、状态更新、版本处理和持久化顺序。Controller、Job、Listener、Adapter 和工作流回调只能完成入参转换与外层编排，并把写操作委派给该所有者；不得在外层直接调用 `PersistHelper` 或等价持久化入口，也不得复制该所有者负责的写流程。本规则补充公共规则 `STYLE-004` 和 `READ-002`，不构成覆盖。
- 例外：无。确需调整领域写编排所有者时，必须在同一变更中迁移完整写流程及全部调用入口，不得保留并行的写实现。
- 检查重点：检查每个需求聚合或跨聚合写工作流是否只有一个可定位的领域写编排所有者，Controller、Job、Listener、Adapter 和工作流回调中是否直接出现 `PersistHelper` 或等价持久化调用，是否复制多步写入顺序，以及事务边界内的关联写入是否仍由同一所有者组织。当前代码中的 `RawRequirementService`、`InitialRequirementService`、`InitialRequirementAssistService` 和 `RequirementChecklistService` 是定位相应所有者的实现证据与检查示例，不要求实现类名称长期不变。
- 建议：外层入口只组装领域写编排所有者所需的 Value 或命令对象并调用其公开写方法；重复的持久化子步骤下沉为所有者的私有方法或由其依赖的专用组件，避免形成第二套写流程。
- 来源：`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/实体/实体｜hisense-requirement模块.md:23-39`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/实体/实体｜需求清单模块.md:27-37`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/RawRequirementServiceImpl.java:140-227`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/RawRequirementServiceImpl.java:281-337`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementServiceImpl.java:167-234`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementServiceImpl.java:236-310`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementAssistServiceImpl.java:588-643`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementAssistServiceImpl.java:645-685`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirementlist/service/impl/RequirementChecklistServiceImpl.java:281-335`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirementlist/service/impl/RequirementChecklistServiceImpl.java:592-704`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirementlist/service/impl/RequirementChecklistServiceImpl.java:706-800`

### hisense-ids-app-need-STYLE-003 禁止 zhangjingli 修改 guoyixing 署名类中的代码

- 标签：hisense-ids-app-need-STYLE-003
- 级别：REQUIRED
- 适用范围：`hisense-ids-app-need` 项目内的 Java 源码；本次固定提交的 Git Author Email 经受信身份接口唯一解析为规范用户 ID `zhangjingli`，且目标 `class` 具有与该类声明明确关联的类级 Javadoc，其中至少一个 `@author` 标签的完整值去除首尾空白后恰好为 `guoyixing`，变更行位于该类声明范围内。
- 规则：满足上述全部条件时，`zhangjingli` 不得在该类声明范围内新增、修改或删除代码。新增行按变更后版本判断，删除行按变更前版本判断，修改同时核对变更前后版本，任一侧满足适用条件即纳入。本规则补充 `standards/common/`，不构成覆盖。只有身份、类级 Javadoc 归属、`@author` 精确值和变更行所属类范围均有充分静态证据时，才构成确定性违规；已证明的违规必须报告为 `HIGH`，证据不足时不得生成确定性违规发现。
- 例外：无。证据不足不属于例外，不得据此生成确定性违规发现。
- 检查重点：确认固定提交的 Git Author Email 已通过受信身份接口唯一解析为规范用户 ID `zhangjingli`，不得根据姓名、邮箱外观、Javadoc 或代码内容推断身份；确认 Javadoc 确实关联目标 `class`，且至少一个 `@author` 标签的完整值去除首尾空白后与 `guoyixing` 完全相等，不做大小写折叠、别名或部分匹配；新增使用变更后版本，删除使用变更前版本，修改同时使用两侧；若变更处于任一明确匹配的封闭类声明范围内则纳入，无法确认身份、Javadoc 归属或类范围时不生成本规则的确定性发现。
- 建议：撤销 `zhangjingli` 对该类的代码变更；如类归属约定确已改变，应先依据可定位的正式项目决定更新项目规则与类级 Javadoc，不得通过改写 Git Author Email、代提交、删除或改写 `@author` 规避检查。
- 来源：用户于 2026-07-24 提出的规则配置请求：“添加一个规则，禁止在类注释中author为guoyixing的类中出现zhangjingli提交的代码，等级为高，添加到hisense的所有项目中”；`AGENTS.md` 第 4、5、10 节；`standards/README.md` 的项目规则模板与级别说明。
