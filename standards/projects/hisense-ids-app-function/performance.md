# 海信 IDS 应用功能分支项目性能规范

本文件仅补充 `standards/common/`，不覆盖任何公共规则。规则仅适用于 `project-registry.yaml` 中 `project_id=hisense-ids-app-function` 的项目，只约束可静态核验的技术质量，不判断业务规则是否正确。

### hisense-ids-app-function-PERF-001 集合驱动路径必须消除增长型重复 I/O

- 标签：hisense-ids-app-function-PERF-001
- 级别：REQUIRED
- 适用范围：功能库、功能清单、列表与列表详情、版本查询与变更、导入、导出、附件、用户与字典补全、定时任务及外部集成路径中，可静态证明数据库、网络或文件 I/O 的调用次数、读取量、并发量或资源占用随功能、功能清单、清单条目、版本、附件、用户、字典项、导入导出记录或作业数据集合大小增长的处理。
- 规则：必须消除直接位于循环、映射、递归或逐项处理中的重复 I/O，以及隐藏在逐项服务、回调、属性访问、序列化、延迟加载或集成调用链中的 N+1 数据库、网络或文件 I/O。应按数据源和协议采用有界批量查询或写入、连接查询、预取并建立索引、数据加载器、合并文件读写、分页或流式处理；协议无法批量处理远程工作时，才可使用与下游容量相匹配的有界并发，并保留明确的超时、取消、部分失败汇总和资源释放语义。处理的数据、页、批次、流、队列、缓存和并发必须具有可定位的资源边界；列表和列表详情使用分页时，排序键必须确定且能稳定区分边界记录，避免跨页重复或遗漏。本规则补充并强化公共规则 `PERF-001`、`PERF-002`、`PERF-003` 和 `PERF-005`，不构成覆盖。
- 例外：纯内存循环不在本规则范围内。调用次数、读取量和资源占用不随外部集合增长，且不存在 N+1、无界读取、无界缓存或无界并发的路径，不按本规则判定违规；公共性能规则仍独立适用。
- 检查重点：核对功能与功能清单的列表、列表详情、版本、导入导出、附件、用户与字典补全、定时任务和外部集成所处理集合的来源；沿 `PersistHelper`、查询包装器、远程服务、文件帮助类及逐项方法、回调、流操作、属性访问和序列化调用链检查直接或间接 I/O，确认同类调用次数是否随集合大小增长。检查关联数据是否批量加载或预取后复用，写入与文件操作是否合并或分为有界批次，分页是否使用确定且稳定的排序边界，流、队列、缓存与中间集合是否有界；协议不可批量时，确认并发受控，并且远程工作保留超时、取消、部分失败汇总和资源释放语义。
- 建议：先汇总并去重功能 ID、功能清单 ID、清单条目 ID、版本 ID、附件 ID、用户 ID、字典键和外部对象标识，再使用批量接口、连接查询、预取、数据加载器或合并读写；需要内存匹配时建立 `Map`、`Set` 或其他合适的索引。大集合采用有界分页、分批或流式处理，并使用稳定排序键；协议无法批量处理时使用有界工作队列或有界并发，同时显式传播超时、取消与失败结果，不得以吞掉异常或无限重试掩盖部分失败。
- 来源：公共规范 `standards/common/performance.md:28-59,72-81`；本地知识 `D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜慢接口SQL优化方法.md:10-41`、`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜功能生命周期管理.md:9-35`、`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜功能清单生命周期管理.md:9-34`、`D:/Workspace/Code/OpenSource/LlmWiki/data/wiki/概念/概念｜退市批量推送分批容错机制.md:10-38`；本地源码 `data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionlib/service/impl/FunctionServiceImpl.java`、`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionchecklist/service/impl/FunctionChecklistServiceImpl.java`、`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionlib/listener/FunctionImportListener.java`、`data/code/hisense-ids-app-function/hisense-app/src/main/java/com/glaway/functionlib/schedule/FunctionNumberSyncJob.java`
