# 海信 IDS 应用需求分支项目性能规范

本文件仅补充 `standards/common/`，不覆盖任何公共规则。规则仅适用于 `project-registry.yaml` 中 `project_id=hisense-ids-app-need` 的项目，只约束可静态核验的技术质量，不判断业务规则是否正确。

### hisense-ids-app-need-PERF-001 外部集合驱动路径必须消除增长型重复 I/O

- 标签：hisense-ids-app-need-PERF-001
- 级别：REQUIRED
- 适用范围：需求列表、需求清单详情、发布或取消（含删除、作废）联动、状态聚合、导入和定时任务等列表、清单、导入或作业循环中，可静态证明数据库、用户、组织、标签、网络或文件 I/O 的调用次数随外部可控的 RR、IR、项目需求、需求清单条目、用户、组织、标签或路标集合大小增长的路径。
- 规则：必须消除 N+1 或随集合大小线性增长的同类重复 I/O，并根据数据源和协议采用有界批量查询或写入、连接查询、预取并索引、数据加载器、框架支持的流式处理，或在协议无法批量处理时采用有界并发；处理的数据、批次、流或并发必须有明确资源边界。本规则补充公共规则 `PERF-001`、`PERF-002`、`PERF-003` 和 `PERF-005`，不构成覆盖。
- 例外：纯内存循环不在本规则范围内。严格有界的小集合且处于非热路径的重复 I/O，只有具备有效、明确的项目决策，并按公共规则要求显式覆盖适用的 `PERF-001`、`PERF-002` 或 `PERF-003` 后才能例外；本规则不声明任何覆盖。
- 检查重点：核对列表与清单详情、发布或取消（含删除、作废）联动、状态聚合、导入和定时任务的外部集合来源，以及数据库、用户、组织、标签、网络或文件调用是否隐藏在逐项方法、回调或流操作中；确认同类 I/O 调用次数是否随集合大小增长，N+1 是否由联查、批量加载、预取索引或数据加载器消除，写入是否合并或分为有界批次，流式处理和协议不可批量时的并发是否有界。
- 建议：可先汇总并去重 RR 编号、IR 编号、项目需求 ID、清单 ID、用户 ID、组织 ID、标签 ID 或路标编号，再选用批量接口、连接查询、预取、数据加载器或框架流式处理；需要内存匹配时可使用 `Map`、`Set` 或其他合适的索引结构，协议无法批量处理时使用有界工作队列或有界并发，并保留超时、失败和资源上限语义。
- 来源：公共规范 `standards/common/performance.md:28-59,72-81`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/实体/实体｜需求清单模块.md:13-37`；`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜需求全链路状态追踪.md:11-39`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirementlist/service/impl/RequirementChecklistServiceImpl.java:117-211,595-699,874-1035`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/service/impl/InitialRequirementAssistServiceImpl.java:87-180,432-509`；`data/code/hisense-ids-app-need/hisense-app/src/main/java/com/glaway/requirement/job/PlanReqPoolNotifyJob.java:86-145`
