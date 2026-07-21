# 海信 IDS 应用需求分支项目健壮性规范

本文件仅补充 `standards/common/`，不覆盖任何公共规则，仅适用于 `project-registry.yaml` 中 `project_id=hisense-ids-app-need` 的项目。本文件只约束可静态核验的技术质量，不判断业务规则或业务结果是否正确。

### hisense-ids-app-need-ROBUST-001 全链路关系字段必须保持模型定义的标识语义

- 标签：hisense-ids-app-need-ROBUST-001
- 级别：REQUIRED
- 适用范围：模型或 API 契约明确标识为稳定 ID 或稳定业务键的 `rawId`、`initialRequirementId`、`distributionPathId`、`projectRequirementId`、`requirementChecklistId`、`predecessorId`、`roadSignNumber`，以及这些字段在查询、持久化、传输和状态传播中的使用
- 规则：上述关系字段必须保持其模型或 API 契约明确规定的标识语义，写入、查询和返回不得把一种对象或版本的标识替换为另一种标识。只有可定位的模型或 API 契约能证明某字段是稳定 ID 或稳定业务键时，才能据此判定；审查者不得按名称外观猜测。显示名称、展示文本和可变描述不得作为关系键。本规则补充公共规则 `STYLE-001`，不构成覆盖。
- 例外：名称和展示文本可以作为只读展示字段，但不得回写或转换为关系键。
- 检查重点：核对字段定义、模型构造方法、查询连接条件和返回映射是否对同一字段保持一致语义；确认 `roadSignNumber` 等业务键有明确契约依据，并排除仅凭变量名推断标识含义的结论。
- 建议：在适配入口显式转换不同模型的标识，并以字段类型、模型方法或接口说明保留转换依据；展示字段与关系字段分开传递。
- 来源：公共规则 `STYLE-001`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/实体/实体｜需求清单模块.md:39-48`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜需求全链路状态追踪.md:24-39`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementAssistServiceImpl.java:100-170`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirementlist/service/impl/RequirementChecklistServiceImpl.java:808-856`

### hisense-ids-app-need-ROBUST-002 用户请求的数据范围必须由服务端可信上下文收敛

- 标签：hisense-ids-app-need-ROBUST-002
- 级别：REQUIRED
- 适用范围：用户请求可达的需求列表、详情、删除、挂起、分发、入池及其他携带对象 ID、公司或团队筛选条件的读写接口
- 规则：请求提供的对象 ID、公司或团队筛选条件必须与服务端可信上下文派生的允许范围取交集后再用于查询或写入；操作需要可信范围但无法取得时必须关闭失败。用户请求可达的调用不得只依赖客户端范围，也不得使用无边界的 `PermissionType.ALL` 代替服务端范围约束。本规则不定义尚未确定的角色模型。本规则补充公共规则 `ROBUST-001` 和 `ROBUST-004`，不构成覆盖。
- 例外：不接收用户目标或筛选条件、身份固定且处理范围由服务端配置明确限定的受信后台入口，可以使用其已证明的服务端范围。
- 检查重点：核对当前用户或受信任务上下文的来源、请求集合与允许集合的交集、空或缺失可信范围的失败路径，以及 Controller 可达调用链中的 `PermissionType.ALL` 和客户端筛选值。
- 建议：在服务入口集中解析服务端允许范围，先收敛对象集合再调用查询或写入；让可信范围缺失返回可区分失败。
- 来源：公共规则 `ROBUST-001`、`ROBUST-004`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜需求池管理.md:9-33`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜需求分发去重与筛选优化.md:10-20`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementAssistServiceImpl.java:270-301`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementAssistServiceImpl.java:592-642`

### hisense-ids-app-need-ROBUST-003 状态与版本写入必须校验当前有效对象

- 标签：hisense-ids-app-need-ROBUST-003
- 级别：REQUIRED
- 适用范围：原始需求、初始需求、项目需求、分发路径和需求清单的状态转换、工作流回调、撤回、删除、发布、作废及升版写入
- 规则：状态或版本写入前必须重新取得当前有效对象，并校验当前状态允许本次动作。版本号必须使用项目统一的 `VersionControlHelper` 或其他有可定位证据的统一当前版本机制生成，新版本必须记录 `predecessorId`，并在同一一致性边界内协调新旧版本可用性；失败不得留下多个当前有效版本、全部版本无效或与已完成步骤矛盾的部分写入。本规则补充公共规则 `ROBUST-004`、`ROBUST-007` 和 `ROBUST-009`，不构成覆盖。
- 例外：框架以同一原子操作完成当前对象读取、状态条件校验和写入时，可以不重复手工校验，但静态代码必须能定位该保证。
- 检查重点：核对写入前的当前对象查询、状态守卫、`VersionControlHelper` 或等价统一证据、`predecessorId`、可用标记、持久化顺序、事务或原子边界及失败后的状态一致性。
- 建议：把状态守卫和版本切换收敛到领域服务，以条件更新或受控事务完成版本生成、前驱关联和可用性切换。
- 来源：公共规则 `ROBUST-004`、`ROBUST-007`、`ROBUST-009`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/实体/实体｜需求清单模块.md:27-37`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/摘要/摘要｜需求全链路-功能清单管理-PRD.md:12-22`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementServiceImpl.java:240-275`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementServiceImpl.java:1206-1275`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirementlist/service/impl/RequirementChecklistServiceImpl.java:808-867`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirementlist/service/impl/RequirementChecklistServiceImpl.java:980-1009`

### hisense-ids-app-need-ROBUST-004 导入提交单元必须先校验后写入并如实报告结果

- 标签：hisense-ids-app-need-ROBUST-004
- 级别：REQUIRED
- 适用范围：原始需求、初始需求评审及其他需求数据的 Excel、压缩包或批量文件导入
- 规则：每个提交单元在任何写入前必须完整解析并校验该单元，同时保留源文件和源行身份。接口契约为全有或全无时，任一校验错误都不得产生写入；接口契约明确允许有界分块或部分完成时，每个分块必须原子提交，最终结果必须区分已完成、失败、未执行和状态未知，且不得报告整体成功。本规则只约束提交边界和结果真实性，不规定业务是否接受部分导入。本规则补充公共规则 `ROBUST-001`、`ROBUST-002`、`ROBUST-004` 和 `ROBUST-009`，不构成覆盖。
- 例外：具备已验证原子事务且失败时整体回滚的提交单元，可以只返回单一失败结果，但仍须保留可定位的输入错误证据。
- 检查重点：核对提交单元边界、源文件和源行号、解析与校验是否先于写入、异常是否被吞掉、全有或全无契约下是否发生部分写入，以及分块结果是否覆盖四种完成状态。
- 建议：按接口契约明确提交单元，先生成带源文件和行号的验证结果，再进入原子写入；分块时使用固定上限并汇总逐块结果。
- 来源：公共规则 `ROBUST-001`、`ROBUST-002`、`ROBUST-004`、`ROBUST-009`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/主题/主题｜需求全链路.md:59-71`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/摘要/摘要｜需求全链路-需求分类管理-PRD.md:12-22`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜功能导入导出.md:11-32`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/listener/RawImportListener.java:20-79`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/listener/InitialReviewImportListener.java:29-113`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/RawRequirementServiceImpl.java:1275-1354`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/RawRequirementServiceImpl.java:1357-1442`

### hisense-ids-app-need-ROBUST-005 未决与延期需求应保持显式隔离

- 标签：hisense-ids-app-need-ROBUST-005
- 级别：ADVISORY
- 适用范围：项目资料明确标记为待确认、延期、后续完善、非本期范围或依赖未完成的需求路径
- 规则：建议在没有更新且可定位的决策证据时，隔离未决或延期路径，不用猜测默认值、占位写入或伪成功替代业务决定；实现前应取得晚于原待决记录的新鲜决策证据。本规则不能据此生成确定性违规，也不定义最终业务结果。本规则补充公共规则 `READ-006` 和 `ROBUST-004`，不构成覆盖。
- 例外：新版本 PRD、批准的决策记录或明确接口契约已经给出结论，且代码变更能定位该证据时，可以按新结论实现。
- 检查重点：仅作为建议核对 TODO、占位分支、默认状态、空实现和成功返回是否替待决事项作出结论，并确认引用证据的时间和适用范围；不得据此推导确定性违规。
- 建议：用明确的未支持或未执行结果隔离待决路径，在实现最终行为时引用新的决策证据。
- 来源：公共规则 `READ-006`、`ROBUST-004`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/分析/分析｜需求全链路-PRD评审风险分析.md:19-46`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/摘要/摘要｜需求全链路-需求池管理-PRD.md:46-54`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementAssistServiceImpl.java:645-684`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementServiceImpl.java:1253-1275`

### hisense-ids-app-need-ROBUST-006 外部需求接口必须校验输入与处理结果边界

- 标签：hisense-ids-app-need-ROBUST-006
- 级别：REQUIRED
- 适用范围：`hisense-interface` 暴露的需求创建、状态查询及其适配器和领域服务调用链的技术输入与结果边界
- 规则：外部需求接口必须拒绝空请求和空元素；已配置或接口契约要求批量上限时，必须校验该上限；必须校验稳定外部标识的存在性和格式、批内重复及需查询的存量重复，并确认下游包装状态、返回条目和实际处理结果一致。本规则不新增详细业务字段规则或认证要求。本规则补充公共规则 `ROBUST-001`、`ROBUST-002` 和 `ROBUST-004`，不构成覆盖。
- 例外：单对象接口不适用批量数量和批内重复检查，但仍须满足空值、稳定外部标识及结果一致性要求。
- 检查重点：核对空集合、空元素、可定位的配置或契约批量上限、稳定外部标识格式和存在性、重复项、下游异常、包装状态及返回结果与副作用是否一致。
- 建议：在最外层适配器解析有界请求，以稳定外部标识去重并保留条目对应关系；用可区分结果表达下游失败和未完成项。
- 来源：公共规则 `ROBUST-001`、`ROBUST-002`、`ROBUST-004`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜统一需求创建接口.md:9-39`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/摘要/摘要｜需求全链路-需求分类管理-PRD.md:43-50`；`data/code/hisense-ids-app-need/hisense-interface/src/main/java/com/glaway/requirement/controller/RequirementController.java:28-57`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/RawRequirementServiceImpl.java:507-591`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/RawRequirementServiceImpl.java:1696-1786`

### hisense-ids-app-need-ROBUST-007 外部需求接口日志不得记录完整载荷

- 标签：hisense-ids-app-need-ROBUST-007
- 级别：REQUIRED
- 适用范围：外部需求创建、状态查询及其 Controller、Feign、适配器和服务调用链中的应用日志与异常日志
- 规则：日志只得记录定位事件所需的请求 ID、条目数和已脱敏的稳定键，不得记录完整请求、需求正文、个人数据或原始外部响应；失败日志必须在脱敏后保留可定位的根因和处理阶段。本规则补充公共规则 `STYLE-002` 和 `STYLE-003`，不构成覆盖。
- 例外：无。
- 检查重点：核对对象序列化、集合打印、需求名称和正文、人员字段、原始响应、外部标识脱敏，以及异常记录是否保留根因但未泄露载荷。
- 建议：使用结构化日志记录请求 ID、数量、处理阶段和掩码键；异常转换时保留原因链，并移除对象级序列化日志。
- 来源：公共规则 `STYLE-002`、`STYLE-003`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/摘要/摘要｜hisense-tech-ingest-projectDevGroup-110007b8e-d57ca1d42.md:10-21`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/分析/分析｜hisense-tech-ingest-projectDevGroup-110007b8e-d57ca1d42.md:43-51`；`data/code/hisense-ids-app-need/hisense-interface/src/main/java/com/glaway/requirement/controller/RequirementController.java:28-57`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/RawRequirementServiceImpl.java:560-591`

### hisense-ids-app-need-ROBUST-008 需求定时任务扫描必须有界推进

- 标签：hisense-ids-app-need-ROBUST-008
- 级别：REQUIRED
- 适用范围：需求池提醒、挂起到期处理、状态刷新及其他由受信调度入口扫描需求或分发记录的定时任务
- 规则：需求定时任务必须通过稳定排序的分页、游标或固定配置批次扫描，且每轮都必须有可验证的进度、配置上限和终止条件；任务只能由可证明的受信调度入口触发。本规则只约束扫描推进和入口边界，不包含通知或状态更新的幂等要求。本规则补充公共规则 `ROBUST-003` 和 `PERF-005`，不构成覆盖。
- 例外：数据源由可定位契约证明为固定小集合时可以单批读取，但仍须有固定上限、终止条件和受信调度入口。
- 检查重点：核对全量查询、稳定排序键、页码或游标更新、固定配置批量大小、游标停滞处理、退出条件，以及是否存在用户请求可直接触发的入口。
- 建议：按稳定 ID 或等价稳定键分页，固定批量上限，并在游标不推进或达到上限时以明确原因终止。
- 来源：公共规则 `ROBUST-003`、`PERF-005`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜需求池管理.md:21-39`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/摘要/摘要｜需求全链路-需求池管理-PRD.md:12-22`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/job/PlanReqPoolNotifyJob.java:49-113`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/ProjectReqDistributionServiceImpl.java:425-464`

### hisense-ids-app-need-ROBUST-009 需求定时任务副作用必须可安全重试

- 标签：hisense-ids-app-need-ROBUST-009
- 级别：REQUIRED
- 适用范围：需求定时任务产生的通知、状态更新及其他可重复触发的外部或持久化副作用
- 规则：通知和状态更新必须使用稳定对象、目标、任务窗口的组合，或其他有证据证明等价的幂等依据；重试必须跳过已知成功的副作用，并在任务结束时按条目汇总已完成、失败、未执行和状态未知。本规则不要求特定数据库、缓存或消息技术。本规则补充公共规则 `ROBUST-004`、`ROBUST-006` 和 `ROBUST-009`，不构成覆盖。
- 例外：副作用由下游接口或原子操作提供可定位且覆盖重试窗口的幂等保证时，可以复用该保证，但调用方仍须汇总条目结果。
- 检查重点：核对稳定对象和目标、任务窗口或等价幂等证据、重试时的成功跳过、单项异常后的控制流、状态未知处理，以及最终逐项结果摘要。
- 建议：为每个副作用记录稳定的执行身份和结果，重试前读取已知结果，并让任务摘要完整反映各条目状态。
- 来源：公共规则 `ROBUST-004`、`ROBUST-006`、`ROBUST-009`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜需求池管理.md:21-39`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/摘要/摘要｜需求全链路-需求池管理-PRD.md:12-22`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/job/PlanReqPoolNotifyJob.java:112-146`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/ProjectReqDistributionServiceImpl.java:446-464`

### hisense-ids-app-need-ROBUST-010 动态 SQL 条件必须绑定参数或使用服务端白名单

- 标签：hisense-ids-app-need-ROBUST-010
- 级别：REQUIRED
- 适用范围：需求、分发路径、需求池和需求清单查询中的动态值、集合、列名、排序项及 `SqlParameter` 构造
- 规则：请求提供的动态值和集合必须通过框架支持的绑定参数传递；动态列名和排序项只能由服务端固定枚举或白名单映射生成。不得使用 `String.join` 拼接带引号的请求集合，不得把请求值包装为 raw `SqlParameter` 片段，也不得直接拼接请求提供的列名、排序或 SQL 语法。本规则补充公共规则 `ROBUST-001` 和 `ROBUST-002`，不构成覆盖。
- 例外：完全由服务端常量组成且不含请求、配置或外部数据的固定 SQL 片段可以直接使用。
- 检查重点：核对 `String.join`、手工引号和括号、raw 参数标志、动态 `IN` 条件、列名与排序拼接、集合占位符及请求值进入 SQL 的路径。
- 建议：使用查询框架的集合绑定或逐值占位符；将允许的列和排序映射为服务端固定枚举，并拒绝白名单外输入。
- 来源：公共规则 `ROBUST-001`、`ROBUST-002`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜需求分发去重与筛选优化.md:12-25`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/分析/分析｜需求全链路-PRD评审风险分析.md:39-46`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementAssistServiceImpl.java:304-390`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementAssistServiceImpl.java:580-585`；`data/code/hisense-ids-app-need/hisense-app/src/main/resources/META-INF/sql/requirement.sql.xml:60-92`；`data/code/hisense-ids-app-need/hisense-app/src/main/resources/META-INF/sql/requirement.sql.xml:135-185`

### hisense-ids-app-need-ROBUST-011 新旧需求分发接口兼容必须收敛到显式适配边界

- 标签：hisense-ids-app-need-ROBUST-011
- 级别：REQUIRED
- 适用范围：需求分发旧 API 与新 API 并存期间的 Controller、适配器、查询、保存和响应链路
- 规则：兼容期间，旧 API 必须在显式适配边界转换为一个规范模型和一套明确的 ID 语义；边界之后的查询、保存和响应必须使用一致的标识及失败语义。临时兼容代码必须具有代码或可定位决策记录中可见的移除条件。本规则不规定删除分发谓词，也不规定旧模型到新模型的具体业务映射。本规则补充公共规则 `STYLE-001`、`READ-006`、`ROBUST-004` 和 `ROBUST-009`，不构成覆盖。
- 例外：旧 API 已完全拒绝调用且不会进入下游查询或写入时，可以不做模型转换，但拒绝响应必须明确且与实际未执行状态一致。
- 检查重点：核对旧 API 入口、适配边界、旧新字段转换、边界后的规范模型、查询与保存使用的 ID、响应与异常语义，以及临时兼容说明中的可验证移除条件；不得由资料推断具体业务映射。
- 建议：在旧入口后设置单一适配器，转换完成后只调用规范服务；以测试、版本开关或决策记录中的可见条件标记兼容代码的移除时机。
- 来源：公共规则 `STYLE-001`、`READ-006`、`ROBUST-004`、`ROBUST-009`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜需求分发接口新旧兼容.md:10-18,33-43,63-67`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/分析/分析｜需求分发变更风险分析.md:14-21,31-38`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/controller/InitialRequirementController.java:168-187`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/ProjectReqDistributionServiceImpl.java:403-419`
