# 海信 IDS 应用-结构化分支项目健壮性规范

本文件由使用者明确要求基于当前代码和本地知识库配置，仅补充 `standards/common/`，不覆盖任何公共规则。规则适用于 `project-registry.yaml` 中 `project_id=hisense-ids-app-spec` 的项目，只约束可静态核验的技术质量，不判断业务规则是否正确。

### hisense-ids-app-spec-ROBUST-001 分层校验外部响应

- 标签：hisense-ids-app-spec-ROBUST-001
- 级别：REQUIRED
- 适用范围：新增或修改的 Feign、SAP、PLM、MDG、GSS、SCP、NCD 等外部调用结果解包代码，尤其是 `JsonResult<T>` 和包含嵌套集合的响应
- 规则：读取业务字段前必须依次确认响应包装非空、调用状态成功、`result` 或 `body` 非空，以及后续要访问的嵌套对象或集合满足最小结构；任一层失败都必须转换为可识别的业务错误或领域异常。下游消息只有在完成脱敏后才能进入受控诊断日志，对外只返回稳定错误码或通用文案。本规则细化公共规则 `ROBUST-001`、`ROBUST-004` 和 `STYLE-003`。
- 例外：返回类型和调用框架已经在当前边界静态保证非空与成功状态时，可以省略被证明冗余的检查，但不得只依赖未声明的运行时惯例。
- 检查重点：调用后是否立即链式执行 `getResult().getXxx()`、失败状态是否仍有非空结果、空集合首项访问、受控诊断中是否脱敏保留根因和可定位上下文。
- 建议：按“包装层、状态层、业务载荷层、嵌套字段层”顺序校验，统一抛出带外部系统名和稳定业务标识的脱敏异常。
- 来源：`data/code/hisense-ids-app-spec/hisense-interface/src/main/java/com/glaway/gsssalesmodel/service/impl/MdgPushAdapterImpl.java:96-120,142-160`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜SAP接口失败多层防护模式.md:10-38`

### hisense-ids-app-spec-ROBUST-002 GSS 适配器必须分类失败

- 标签：hisense-ids-app-spec-ROBUST-002
- 级别：REQUIRED
- 适用范围：`hisense-interface/src/main/java/com/glaway/gsssalesmodel/` 下调用 MDG、PLM 或新增下游步骤的适配器
- 规则：适配器必须把下游失败转换为 `StepInvocationException`，并明确设置 `retryable`：网络超时和可确认的服务端瞬态失败可重试；参数校验失败、业务拒绝、400/401/403 及确定无效的返回值不可重试。根因只能在受控诊断链路中保留并脱敏，不得直接进入响应；调用方必须使用该分类，不得把所有异常统一重试或统一放弃。本规则细化公共规则 `ROBUST-004` 和 `ROBUST-006`。
- 例外：下游契约明确提供更细的错误分类时，可以扩展分类表，但必须保持未知错误的处理策略可见，并同步重试执行器。
- 检查重点：`BusinessException`、超时、4xx、5xx、空响应、非法编码和未知异常的映射；异常原因链是否只在受控诊断中脱敏保留；MDG 与 PLM 适配器分类是否一致。
- 建议：集中维护分类函数和稳定错误码，让适配器只负责协议转换、响应校验与错误归一化。
- 来源：`data/code/hisense-ids-app-spec/hisense-interface/src/main/java/com/glaway/gsssalesmodel/service/MdgPushAdapter.java:13-30`；`data/code/hisense-ids-app-spec/hisense-interface/src/main/java/com/glaway/gsssalesmodel/service/impl/MdgPushAdapterImpl.java:42-50,67-120`；`data/code/hisense-ids-app-spec/hisense-interface/src/main/java/com/glaway/gsssalesmodel/service/impl/PlmPushAdapterImpl.java:38-89`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜销售型号推送适配器模式.md:9-25`

### hisense-ids-app-spec-ROBUST-003 GSS 步骤重试使用统一上限并保留中断

- 标签：hisense-ids-app-spec-ROBUST-003
- 级别：REQUIRED
- 适用范围：GSS 销售型号编排的 `StepRetryExecutor`、步骤供应者和相关重试常量
- 规则：每个步骤的尝试次数不得超过 `GssSalesModelConstants.PER_STEP_RETRY_LIMIT`，只在仍有下一次尝试时按统一退避常量等待；不可重试错误必须立即终止。捕获 `InterruptedException` 后必须恢复线程中断标志并立即结束当前步骤，不得吞掉中断或继续重试。本规则细化公共规则 `ROBUST-003` 和 `ROBUST-006`。
- 例外：调整统一上限或退避策略时，必须同步常量、执行器、步骤日志语义和可定位决策，不得在单个适配器内另设重试循环。
- 检查重点：循环上限、最后一次失败后是否仍等待、不可重试分支、`Thread.currentThread().interrupt()`、最终异常是否携带最后一次失败信息。
- 建议：继续由 `GssSalesModelConstants` 统一保存上限，由 `StepRetryExecutor` 单点实现重试，避免适配器和编排器叠加重试。
- 来源：`data/code/hisense-ids-app-spec/hisense-interface/src/main/java/com/glaway/gsssalesmodel/service/impl/StepRetryExecutorImpl.java:61-125`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/实体/实体｜步骤重试执行器.md:9-24`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜步骤重试与幂等恢复.md:9-25`

### hisense-ids-app-spec-ROBUST-004 GSS 外部副作用重试必须断点接续

- 标签：hisense-ids-app-spec-ROBUST-004
- 级别：REQUIRED
- 适用范围：`hisense-interface/src/main/java/com/glaway/gsssalesmodel/` 下的销售型号创建、MDG 推送和 PLM 推送三步编排
- 规则：流程重试前必须以稳定业务键和步骤日志判断各步骤是否已经成功；已成功且可能产生外部副作用的步骤必须复用结果并跳过，不得从头盲目重放。已有底层调用负责写入发送结果时，上层适配器不得重复写同一结果。本规则细化公共规则 `ROBUST-006` 和 `ROBUST-009`。
- 例外：无。
- 检查重点：业务键唯一性、步骤日志查询、起始步骤决策、BizId 回写与复用、成功步骤跳过、发送结果是否重复落库、部分失败状态是否可恢复。
- 建议：把每步稳定标识、结果和终态持久化，重试时只执行未完成步骤；对状态未知的下游先查询再决定是否重放。
- 来源：`data/code/hisense-ids-app-spec/hisense-interface/src/main/java/com/glaway/gsssalesmodel/service/GssSalesModelOrchestrator.java:21-38`；`data/code/hisense-ids-app-spec/hisense-interface/src/main/java/com/glaway/gsssalesmodel/service/MdgPushAdapter.java:27-30`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜步骤重试与幂等恢复.md:20-38`

### hisense-ids-app-spec-ROBUST-005 只读占位符不得离开规格书内部边界

- 标签：hisense-ids-app-spec-ROBUST-005
- 级别：REQUIRED
- 适用范围：规格书详情、矩阵、生产版本详情，以及 `SpecPushCreateHandler` 的名称装配
- 规则：`AllConstantIndex.Specification.ONLY_READ_PLACEHOLDER` 只允许作为规格书内部持久化占位；上述已验证出口读取 `demandValue` 或 `actualValue` 时，必须通过统一判断或净化能力把它转换为 `null` 或“无值”语义，不得把占位符当作真实名称或属性值。本规则细化公共规则 `ROBUST-001`。
- 例外：仅持久化层内部写入和识别该占位符时可以保留原值，且不得越过服务输出边界。
- 检查重点：详情和矩阵是否同时处理需求值与实际值、生产版本详情是否处理实际值、模板从只读改为可编辑后的历史数据、推送名称装配、是否散落硬编码占位符字符串。
- 建议：复用 `isOnlyReadPlaceholder` 和 `sanitizeOnlyReadPlaceholder`，并使用 `AllConstantIndex` 中的唯一常量。
- 来源：`data/code/hisense-ids-app-spec/hisense-common/src/main/java/com/glaway/common/constant/AllConstantIndex.java:297-300`；`data/code/hisense-ids-app-spec/hisense-app/src/main/java/com/glaway/specification/service/handler/AbstractSpecHandler.java:539-560`；`data/code/hisense-ids-app-spec/hisense-app/src/main/java/com/glaway/specification/service/handler/SpecDetailHandler.java:1170-1182`；`data/code/hisense-ids-app-spec/hisense-app/src/main/java/com/glaway/specification/service/handler/SpecMatrixHandler.java:1149-1160`；`data/code/hisense-ids-app-spec/hisense-app/src/main/java/com/glaway/specification/service/handler/SpecProductionVersionDetailHandler.java:199-213`；`data/code/hisense-ids-app-spec/hisense-app/src/main/java/com/glaway/specification/service/handler/SpecPushCreateHandler.java:1570-1603`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜只读占位符净化机制.md:10-52`

### hisense-ids-app-spec-ROBUST-006 IBA 原始值必须统一归一化

- 标签：hisense-ids-app-spec-ROBUST-006
- 级别：REQUIRED
- 适用范围：新增或修改的主数据代码中，将框架 IBA 对象的原始 `findValue()` 写入 `InstanceAttrValueParamsDTO` 的初始转换路径
- 规则：可能包含单值、多值或数据字典对象的框架 IBA 原始值必须通过 `IbaUtils.getValue` 或等价的项目统一能力归一化，不得把未经处理的 `findValue()` 直接写入 `InstanceAttrValueParamsDTO`。本规则细化公共规则 `ROBUST-001`。
- 例外：属性能力在当前代码中已证明只能是标量时可以直接使用；已经过映射的规格书推送字符串可以按 `AllConstantIndex.Separator.MASTER_DATA_MULTI_VALUE` 还原为数组，但不得硬编码分隔符。
- 检查重点：`findValue()` 是否直接进入 DTO、`getSingleValue` 是否造成多值丢失、规格书映射值是否通过具名常量还原。
- 建议：读取框架 IBA 对象时使用 `IbaUtils.getValue`；规格书映射结果需要恢复多值时复用 `AllConstantIndex.Separator`。
- 来源：`data/code/hisense-ids-app-spec/hisense-common/src/main/java/com/glaway/common/constant/AllConstantIndex.java:23-39`；`data/code/hisense-ids-app-spec/hisense-app/src/main/java/com/glaway/masterdata/service/impl/MasterDataServiceImpl.java:5675,5789,6308`；`data/code/hisense-ids-app-spec/hisense-app/src/main/java/com/glaway/specification/service/handler/SpecPushExecuteHandler.java:758-805`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜IBA多值属性值处理.md:10-41`

### hisense-ids-app-spec-ROBUST-007 规格书 CREATE 通过 BizId 接续创建

- 标签：hisense-ids-app-spec-ROBUST-007
- 级别：REQUIRED
- 适用范围：`SpecPushExecuteHandler` 的 CREATE 路径及其产品型号、销售型号、生产版本创建方法
- 规则：重试 CREATE 任务时必须先读取已经回写的产品型号、销售型号或生产版本 BizId；BizId 已存在的子步骤必须复用并跳过，只执行尚未完成的子步骤，不得重复创建已成功对象。本规则细化公共规则 `ROBUST-006` 和 `ROBUST-009`。
- 例外：无。
- 检查重点：每类对象创建前的 BizId 判断、创建与 BizId 回写是否属于同一逻辑单元、单个生产版本失败后再次触发是否只补建未完成项。
- 建议：保持 `ensureXxxCreated` 的“查询已存在、创建、回写、审计”结构，新增子步骤时提供同等接续语义。
- 来源：`data/code/hisense-ids-app-spec/hisense-app/src/main/java/com/glaway/specification/service/handler/SpecPushExecuteHandler.java:278-324,348-516`

### hisense-ids-app-spec-ROBUST-008 GSS 并行批处理必须有界完成

- 标签：hisense-ids-app-spec-ROBUST-008
- 级别：REQUIRED
- 适用范围：`GssSalesModelOrchestratorImpl` 中把销售型号集合提交到 `ThreadPoolTaskExecutor` 的并行批处理
- 规则：批次大小和提交数量必须受具名配置或线程池容量约束；主线程等待必须设置总超时，不得使用无界 `CountDownLatch.await()`。超时、拒绝提交或子任务异常时，必须区分已完成、失败、未完成和状态未知项，并执行受控取消或返回完整失败摘要，不得只返回首个失败。本规则细化公共规则 `ROBUST-003`、`ROBUST-009` 和 `PERF-006`。
- 例外：输入契约可静态证明最多只有一个元素且不创建并行任务时，不要求批次和等待控制。
- 检查重点：批次上限、线程池容量、`await` 是否带超时、提交拒绝、子任务异常、取消、全部失败项汇总和中断状态。
- 建议：使用具名且可配置的批次上限、带截止时间的等待和每项结果对象；超时后停止继续提交并返回未完成范围。
- 来源：`data/code/hisense-ids-app-spec/hisense-interface/src/main/java/com/glaway/gsssalesmodel/service/impl/GssSalesModelOrchestratorImpl.java:193-255`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜GSS销售型号并行创建.md:51-71`

### hisense-ids-app-spec-ROBUST-009 GSS 分布式锁必须校验所有权

- 标签：hisense-ids-app-spec-ROBUST-009
- 级别：REQUIRED
- 适用范围：GSS 编排入口及其他复用 `lock:gss:*` 的 Redis 分布式互斥
- 规则：锁值必须包含本次持有者的不可预测 token，释放时必须以原子 compare-and-delete 校验所有权；租约必须覆盖有界最大执行时间或支持受控续租。租约已经失效或所有权无法确认时，不得直接删除同名锁。本规则细化公共规则 `ROBUST-007` 和 `ROBUST-008`。
- 例外：使用能够证明所有权并自动续租的成熟锁实现时，可以采用该实现提供的解锁语义。
- 检查重点：锁值是否为空、固定 TTL 与最长执行时间、续租、finally 中是否无条件 delete、锁过期后旧请求是否可能删除新持有者的锁。
- 建议：使用 Redisson watchdog 或 Redis Lua 脚本实现 token 比对删除，并让等待超时、下游超时和锁租约采用一致的截止时间模型。
- 来源：`data/code/hisense-ids-app-spec/hisense-interface/src/main/java/com/glaway/gsssalesmodel/service/impl/GssSalesModelOrchestratorImpl.java:92-96,140-165`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜GSS销售型号三步编排.md:32-41`
