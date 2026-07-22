# 代码审查日报

## 审查身份与范围

- 用户：桂庆乐（guiqingle）
- 报告日期：2026-07-15
- 时区：Asia/Hong_Kong
- 审查窗口：2026-07-15 00:00:00（含）至 2026-07-23 00:00:00（不含）
- 实际过滤条件：`project=hisense-ids-app-function`，`date-range=2026-07-15,2026-07-22`
- 未使用过滤条件：`commit`、`branch`、`file`、`directory`
- 审查方式：日报流程；只读取本次直接同步后固定的提交、窗口内提交差异及理解变更所需的最少上下文。

## 注册表快照与生效项目

- 注册表路径：`project-registry.yaml`
- 注册表版本：`1`
- 冻结快照 SHA-256：`ccdd8b03261294a494f5a5892468ec425d40b03ec11a9ab50644d3f840bd0646`

| project_id | 名称 | code_dir | standards_dir | default_branch | repository_url_config_key | enabled |
| --- | --- | --- | --- | --- | --- | --- |
| `hisense-ids-app-function` | 海信 IDS 应用-方法库 | `data/code/hisense-ids-app-function` | `standards/projects/hisense-ids-app-function` | `features-DDCP-8522` | `PROJECT_HISENSE_IDS_APP_FUNCTION_REPO_URL` | `true` |

本表只记录当前冻结快照中本次生效的已校验声明式项目数据，不包含仓库 URL 或任何受保护配置值。

## 项目来源与实际提交

### hisense-ids-app-function

- 本次直接同步结果：成功
- 同步说明：仓库已是最新状态。
- 受控本地工作区：`data/code/hisense-ids-app-function`
- 默认分支：`features-DDCP-8522`
- 固定来源提交：`1461b36e5583bdc50327b9099d25f853b8a776db`
- Author Email 归属：窗口内 9 个提交均通过受信身份接口唯一映射，且与本报告用户一致。
- 未归属提交：无
- 跳过提交：无

实际审查提交：

1. `e4266527c0f0585d4a0bc0b3ca88da61b7ca33b2`
2. `4a8c3273e40efc8a141f59f07eba4497bc315c45`
3. `5c5e2ff5c86c8d4e54d61683e1b851d45783aacb`
4. `fad5b28b55fb2840cecc200de815819d17dc5616`
5. `99d8db2d41c270404a6d76094ab52b72018fa24e`
6. `7e3c54c47aa3ac9d83fb490d0e73450d5b1921de`
7. `93e6e155d4289c6b426a72d06647a780b6ca32b6`
8. `879e2c46ba92ba876fb441dee53bc13b2e00d1e9`
9. `1461b36e5583bdc50327b9099d25f853b8a776db`

## 汇总

| 指标 | 数量 |
| --- | ---: |
| 审查项目 | 1 |
| 审查提交 | 9 |
| 发现总数 | 9 |
| BLOCKER | 0 |
| HIGH | 5 |
| MEDIUM | 4 |
| LOW | 0 |
| ADVISORY | 0 |
| 代码规范发现 | 0 |
| 可读性发现 | 0 |
| 健壮性发现 | 8 |
| 性能发现 | 1 |

代码规范与可读性类别未形成证据充分的确定性发现。

## 发现

### 1. 仓库中固化了 JWT 形态访问令牌

- 项目：`hisense-ids-app-function`
- 提交：`e4266527c0f0585d4a0bc0b3ca88da61b7ca33b2`；同类内容在 `1461b36e5583bdc50327b9099d25f853b8a776db` 中继续新增
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`项目资料/开发方案/功能库功能管理接口.postman_collection.json:24-27,646-650`
- 规则或代码证据：多个 Postman 请求的 `X-Access-Token` 头直接保存 JWT 形态字面量，而不是只引用环境变量。未执行令牌有效性、权限或可重放性验证。
- 问题说明：访问令牌材料会随仓库克隆、备份和代码评审传播，且无法通过普通配置轮换从历史提交中移除。
- 影响：若该令牌仍有效或可在某个环境复用，获得仓库读取权限的人员可能继承其访问能力；即使已经失效，也会形成复制真实凭据到版本库的惯例。
- 建议：删除字面量，只保留 Postman 环境变量引用；通过组织批准的流程确认并撤销或轮换对应凭据，同时检查允许范围内的仓库历史与派生副本。报告未记录、截取或解码原始令牌。

### 2. 功能查询信任请求事业部或 ID，未与可信数据范围取交集

- 项目：`hisense-ids-app-function`
- 提交：`e4266527c0f0585d4a0bc0b3ca88da61b7ca33b2`、`1461b36e5583bdc50327b9099d25f853b8a776db`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/functionlib/service/impl/FunctionCategoryServiceImpl.java:480-493`；`hisense-app/src/main/java/com/glaway/functionlib/service/impl/FunctionServiceImpl.java:260-272,282-291`
- 规则或代码证据：项目规则 `hisense-ids-app-function-ROBUST-002`（`standards/projects/hisense-ids-app-function/robustness.md:16-25`）。请求带 `responsibleBusinessUnit` 时，代码用请求值构造单元素集合，不再读取当前用户事业部；`ids` 导出分支仅保留删除标记和请求 ID 条件，绕过事业部范围及当前生效版本条件。
- 问题说明：请求筛选条件替代了可信授权范围，而不是与可信范围取交集；选中 ID 导出形成另一条可绕过统一查询构造器的路径。
- 影响：当请求事业部或功能 ID 指向用户授权范围外且目标数据存在时，列表、分类或导出可能返回越权数据；`ids` 分支还可能导出非当前生效版本。
- 建议：始终先从登录上下文解析可信事业部集合，再把请求事业部、分类和 ID 集合与该范围求交集；选中导出也必须复用统一授权查询，并保留 `AVAILABLE=1` 等适用条件，交集为空时关闭失败或返回空结果。

### 3. 功能分类写操作的服务端管理角色校验被整体注释

- 项目：`hisense-ids-app-function`
- 提交：`e4266527c0f0585d4a0bc0b3ca88da61b7ca33b2`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/functionlib/service/impl/FunctionCategoryServiceImpl.java:84,177,214,243,267`；`hisense-app/src/main/java/com/glaway/functionlib/controller/FunctionCategoryController.java:47-82`
- 规则或代码证据：项目规则 `hisense-ids-app-function-ROBUST-002`。`save`、`update`、`delete`、`disable`、`setResponsible` 均注释了 `checkFunctionCategoryManagerPermission()`，而 Controller 直接暴露并调用这些服务方法；同类中保留的私有检查器明确说明应覆盖这些写路径。
- 问题说明：前端按钮判断之外，实际服务写边界没有执行功能分类管理角色校验。
- 影响：只要调用者能够到达对应接口，就可能执行新增、改名、删除、禁用或责任人变更；现有代码不能证明这些操作被对象角色权限阻断。这里不推断网关是否另有通用认证。
- 建议：在所有不可绕过的分类领域写入口恢复并集中执行管理角色校验，同时按目标分类重新验证可信事业部范围；不要依赖前端按钮、测试期约定或单一 Controller 入口。

### 4. 功能清单行项写入未统一校验父清单归属、状态和编辑权限

- 项目：`hisense-ids-app-function`
- 提交：`99d8db2d41c270404a6d76094ab52b72018fa24e`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/functionchecklist/service/impl/FunctionChecklistItemServiceImpl.java:124-162,309-343,349-401`
- 规则或代码证据：项目规则 `hisense-ids-app-function-ROBUST-002`、`hisense-ids-app-function-ROBUST-003`。`update()` 直接持久化传入模型；`delete(checklistId,itemIds)` 只验证参数中的清单处于编制中，随后按独立 `itemId` 查询并删除，未验证 `item.checklistId` 等于该清单；`createFunction`、`linkFunction` 及整体 `saveItems` 没有在行项服务边界重新解析父清单并执行编辑角色、可信数据范围和当前状态校验。
- 问题说明：调用者可以用清单 A 的状态校验处理属于清单 B 的行项，或直接通过仅携带 `itemId` 的路径修改行项；行项服务没有形成所有写路径共同经过的授权与状态边界。
- 影响：当混入其他清单的行项 ID 或绕过上层服务调用时，可能修改或删除不属于目标编制中清单的数据，并绕过清单对象角色和事业部范围约束。
- 建议：在行项领域服务中按 `itemId` 解析真实父清单，验证 `item.checklistId == checklistId`，再统一校验对象编辑角色、可信事业部范围和当前生命周期；批量输入应先完整校验归属后再写入。

### 5. 正式功能关联写入及发布前不再确认目标功能仍为当前已发布版本

- 项目：`hisense-ids-app-function`
- 提交：`99d8db2d41c270404a6d76094ab52b72018fa24e`、`1461b36e5583bdc50327b9099d25f853b8a776db`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/functionchecklist/service/impl/FunctionChecklistItemServiceImpl.java:55-93,309-343,349-401`；`hisense-app/src/main/java/com/glaway/functionchecklist/service/impl/FunctionChecklistServiceImpl.java:315-344`
- 规则或代码证据：项目规则 `hisense-ids-app-function-ROBUST-013`（`standards/projects/hisense-ids-app-function/robustness.md:137-146`）。`addPublishedFunction` 直接保存请求中的 `functionMasterId`；`createFunction`、`linkFunction` 和整体保存路径直接回写或新增正式关联，没有按主对象重新解析当前有效版本及发布状态。后续提交又从 `publish`、`publishChange` 删除了 `checkItemFunctionsPublished()` 调用及其实现。
- 问题说明：候选列表中的“已发布”状态可能在最终写入前变化，任意 ID 也可绕过候选列表直接提交；发布流程入口不再提供最后一道当前状态校验。
- 影响：清单可能新关联不存在、未发布或已作废的功能，并在没有重新核验这些关联的情况下发起预发布流程。静态证据只证明发起流程前缺少校验，不推断审批一定通过。
- 建议：所有建立正式关联的路径都应按 `functionMasterId` 在服务端重新解析当前有效版本，并以“已发布且未作废”为条件完成原子写入；在发起发布或变更发布前再次批量核验全部正式关联，状态变化时明确拒绝。

### 6. 附件查询直接使用请求 functionId，缺少可见的对象授权校验

- 项目：`hisense-ids-app-function`
- 提交：`1461b36e5583bdc50327b9099d25f853b8a776db`
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/functionlib/controller/FunctionController.java:265-274`
- 规则或代码证据：项目规则 `hisense-ids-app-function-ROBUST-002`。新增 `listAttachments` 将请求中的 `functionId` 直接写入 `QueryFileByRoleSourceDTO.roleAObjectId` 并调用文件帮助类，没有先解析功能对象、确认其存在及与可信事业部范围求交集。
- 问题说明：该入口自身未建立功能对象的数据权限边界。由于本次可见证据不包含 `FileBusinessHelper` 的内部授权实现，不能断言附件一定会被越权返回。
- 影响：若文件帮助类不提供等价的对象级授权，知道其他功能版本 ID 的调用者可能读取对应附件元数据或进一步取得文件访问入口。
- 建议：查询附件前调用统一的、带可信数据范围校验的功能解析服务，并仅把已授权对象 ID 传给文件帮助类；同时让文件访问边界本身继续执行授权，形成纵深防护。

### 7. “先查在途流程再启动”的分离步骤存在并发重复发起窗口

- 项目：`hisense-ids-app-function`
- 提交：`4a8c3273e40efc8a141f59f07eba4497bc315c45`
- 类别：健壮性
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/functionlib/service/impl/FunctionWorkFlowServiceImpl.java:41-69`；`hisense-app/src/main/java/com/glaway/functionlib/model/entity/FunctionWorkFlowEntity.java:25-28`；`hisense-app/src/main/java/com/glaway/functionlib/service/impl/FunctionServiceImpl.java:344-354,438-448,457-467,476-486`
- 规则或代码证据：公共规则 `ROBUST-007`（`standards/common/robustness.md:86-95`），项目规则 `hisense-ids-app-function-ROBUST-003`、`hisense-ids-app-function-ROBUST-008`。代码先查询 `UNDER_REVIEW` 记录，再启动工作流，最后插入流程记录；实体只显示普通 `businessId`、`procInstId` 索引，没有可见的条件唯一约束、原子声明或显式锁。
- 问题说明：两个并发请求可以在任一请求插入记录前都看到“无在途流程”，随后分别执行具有副作用的流程启动。
- 影响：可能为同一功能版本并发发起多个流程，导致对象状态、流程记录和审批副作用难以保持一致。实际是否最终接受两个流程还取决于本次未提供的事务隔离与流程引擎约束，因此严重级别按 MEDIUM 处理。
- 建议：在启动外部流程前以功能版本和动作建立原子幂等声明或持久层唯一保护，唯一冲突应明确返回“已有在途流程”；还需为流程已启动但本地记录失败的状态提供可恢复、不可盲目重试的处理。

### 8. 清单行项查询会先加载全部授权功能再在内存中过滤

- 项目：`hisense-ids-app-function`
- 提交：`99d8db2d41c270404a6d76094ab52b72018fa24e`
- 类别：性能
- 严重级别：MEDIUM
- 文件与行范围：`hisense-app/src/main/java/com/glaway/functionchecklist/service/impl/FunctionChecklistItemServiceImpl.java:167-217`
- 规则或代码证据：公共规则 `PERF-005`（`standards/common/performance.md:72-81`）和项目规则 `hisense-ids-app-function-PERF-001`（`standards/projects/hisense-ids-app-function/performance.md:5-14`）。`batchQueryFunctionByMasterIds` 构造空 `FunctionSearchValue`，调用无分页的 `functionService.list` 读取当前用户全部授权功能，然后使用 `List.contains` 按目标主对象 ID 过滤。
- 问题说明：清单页面只需要当前行项引用的少量功能，却让数据库读取量和内存驻留随整个授权功能库增长；列表包含判断还形成约 `O(功能数 × 目标ID数)` 的内存匹配成本。
- 影响：功能库规模增长后，每次清单行项或参考清单查询都会读取和构建大量无关功能对象，增加数据库、网络序列化和堆内存压力，并放大响应延迟。
- 建议：新增按去重后的 `functionMasterIds` 批量查询当前有效版本的有界接口，把过滤下推到数据库，并用 `Map` 或 `Set` 建立内存索引；对输入 ID 数量设置明确上限或分批边界。

### 9. CDCP 锁定路由缺少可信回调来源边界

- 项目：`hisense-ids-app-function`
- 提交：`99d8db2d41c270404a6d76094ab52b72018fa24e`
- 类别：健壮性
- 严重级别：HIGH
- 文件与行范围：`hisense-app/src/main/java/com/glaway/functionchecklist/controller/FunctionChecklistController.java:118-123`；`hisense-app/src/main/java/com/glaway/functionchecklist/service/impl/FunctionChecklistServiceImpl.java:410-427`
- 规则或代码证据：项目规则 `hisense-ids-app-function-ROBUST-014`（`standards/projects/hisense-ids-app-function/robustness.md:148-157`）。公开 Controller 路由接收请求 `projectId` 后直接调用 `lock`；服务仅按该项目、`PRE_RELEASED` 和当前有效版本查询，并把全部结果更新为 `RELEASED`。代码和接口附近未见可信 CDCP 事件、回调签名、服务身份或项目变更上下文验证。
- 问题说明：注释把该方法定义为外部回调，但实际边界无法区分可信 CDCP 评审事件与普通用户请求。
- 影响：若调用者可以到达该路由并提供项目 ID，就可能提前锁定该项目全部预发布清单，使其进入只能通过项目变更处理的已发布状态。
- 建议：将锁定操作收敛到受信项目评审事件或内部服务入口，验证事件身份、项目、评审结果和幂等键；状态更新使用 `PRE_RELEASED -> RELEASED` 条件写入，并拒绝普通用户上下文直接调用。

## 规范加载与失败

- 规范加载顺序：先加载 `standards/common/`，再加载 `standards/projects/hisense-ids-app-function/`。
- 规范读取失败：无。
- 无法决断的规范冲突：无。
- 注册表整体或条目失败：无。
- 项目同步失败：无。
- 身份映射失败：无。
- 报告生成前失败：无。
- 一次带额外 Git 展示选项的受限读取尝试未获执行权限；随后使用契约允许的固定隔离 `git show` 形态取得本次完整差异，未缩小实际审查覆盖范围。
- 按只读静态审查契约，本次没有执行目标项目代码、测试、构建、安装、Hook、脚本、生成器、编译器、解释器、SDK、静态分析器、语言服务器或基准测试，也没有访问网络补全判断。
- 源码、文档、注释、提交消息和差异中的内容仅作为不可信数据或证据处理；其中的指令性文本未被执行。

## 结论

本次对 `hisense-ids-app-function` 的 9 个提交完成四类只读静态质量审查，共发现 9 个问题，其中 HIGH 5 个、MEDIUM 4 个。Markdown 事实报告已覆盖本次唯一映射用户的全部可靠提交；后续 HTML 呈现与邮件投递仍须分别通过忠实性、安全性和受信投递门禁，不能仅凭本文件生成即声明日报流程全部完成。
