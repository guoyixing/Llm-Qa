# 多项目 AI 静态代码质量审查

## 这套工具能做什么

这套工具会审查你注册的多个代码仓库，重点检查代码规范、可读性、健壮性和性能。它只读取固定提交、可见差异和审查所需的最少上下文，不运行目标项目的代码、测试或构建。

工具可以只同步仓库、审查现有本地工作区，或完成同步、审查、报告和邮件投递组成的日报流程。

## 先选择你要做的事


| 你想做什么              | 使用命令                 | 会同步仓库 | 会生成报告                   | 会发送邮件        |
| ------------------ | -------------------- | ----- | ----------------------- | ------------ |
| 只同步全部或指定项目，并查看同步汇总 | `/sync-repositories` | 是     | 否                       | 否            |
| 审查已有的受控本地工作区       | `/code-review`       | 否     | 是，仅 Markdown            | 否            |
| 执行完整日报流程           | `/daily-review`      | 是     | 是，Markdown 和通过检查后的 HTML | 是，仅符合全部门禁的用户 |


需要先把本仓库作为 OpenCode 工作区打开，再输入命令。不要把这些命令输入 PowerShell，也不要直接运行 `tools/*.py`。

## 第一次使用：按顺序完成这些步骤

1. 按“第 1 步”确认 OpenCode、Git、Python 和模型配置已经可用。
2. 编辑根目录 [`project-registry.yaml`](project-registry.yaml)，先以 `enabled: false` 注册项目。
3. 创建项目规范目录，例如 `standards/projects/example-service/`，并写入项目审查规则。
4. 请管理员通过组织批准的安全配置流程准备仓库、身份和邮件相关的受保护配置。
5. 完成占位内容、目录和受保护配置检查后，把项目改为 `enabled: true`。
6. 将本仓库作为工作区打开，在 OpenCode 对话输入框中运行所需的 Slash Command。
7. 查看命令最终中文汇总，并按报告日期进入 `reports/daily/` 检查产物。

当前 [`project-registry.yaml`](project-registry.yaml) 只包含已禁用的 `non-production-example`。在你注册并启用一个有效项目之前，不会处理任何项目。

## 第 1 步：确认运行环境

开始前请逐项确认：

- 已有可用的 OpenCode。
- 已有可用的 Git。
- Python 版本为 3.11 或更高。
- 仓库解释器 `./.venv/Scripts/python.exe` 已存在且可用。
- `OPENCODE_REVIEW_MODEL` 已配置。

## 第 2 步：在 project-registry.yaml 注册项目

可以先把根目录 `project-registry.yaml` 写成下面的结构。首次配置时保持 `enabled: false`，避免在目录和受保护配置尚未就绪时误运行。

```yaml
version: 1
projects:
  - project_id: example-service
    name: "示例服务"
    code_dir: data/code/example-service
    standards_dir: standards/projects/example-service
    default_branch: main
    repository_url_config_key: PROJECT_EXAMPLE_SERVICE_REPO_URL
    enabled: false
```


| 字段                          | 你需要填写什么                                                           |
| --------------------------- | ----------------------------------------------------------------- |
| `project_id`                | 项目的规范唯一 ID，只能使用小写 ASCII 字母、数字和内部连字符，首尾必须是字母或数字                    |
| `name`                      | 面向维护者显示的非空项目名称                                                    |
| `code_dir`                  | 项目的受控本地代码目录，必须位于 `data/code/` 下                                   |
| `standards_dir`             | 项目审查规则目录，必须位于 `standards/projects/` 下                             |
| `default_branch`            | 该项目的默认分支                                                          |
| `repository_url_config_key` | 受保护仓库 URL 的配置键名，例如 `PROJECT_EXAMPLE_SERVICE_REPO_URL`，绝不能填写实际 URL |
| `enabled`                   | 是否参与处理；首次准备时使用 `false`，全部就绪后再改为 `true`                            |


多个项目的 `code_dir` 之间不能重叠，`standards_dir` 之间也不能重叠。注册表中不能出现仓库 URL、Token、用户名或密码、SMTP 详情、身份映射或收件人数据。

安全的启用顺序是：

1. 替换示例名称、分支和其他占位内容。
2. 创建 `standards_dir` 对应的项目规范目录。
3. 请管理员准备 `repository_url_config_key` 所指向的受保护配置及其他必要配置。
4. 确认以上内容就绪后，再把 `enabled` 改为 `true`。

## 第 3 步：创建项目审查规则

为上面的项目创建目录：

```text
standards/projects/example-service/
```

然后创建一个具体规则文件，例如：

```text
standards/projects/example-service/performance.md
```

你可以从下面这条完整规则开始。它强化公共规则 `PERF-001`，不声明覆盖公共规则。

```markdown
### example-service-PERF-001 批处理路径禁止逐项数据库查询

- 标签：example-service-PERF-001
- 级别：REQUIRED
- 适用范围：example-service 中处理两个及以上条目的批量导入、批量更新和批量查询路径
- 规则：批处理路径必须使用批量数据库操作或预先合并查询，不得为每个条目单独发起数据库查询。本规则补充并强化公共规则 PERF-001，不构成覆盖。
- 例外：无
- 检查重点：检查循环、映射和逐项回调中是否发生数据库读取或写入，并确认调用次数是否随条目数量线性增长。
- 建议：改用批量查询、批量写入或一次预取后在内存中匹配结果。
- 来源：standards/common/ 中的公共规则 PERF-001
```

审查时先加载 `standards/common/`，再加载项目注册项指向的 `standards/projects/` 目录。不冲突的规则会一起生效。规范文件的组织方式和模板见 [`standards/README.md`](standards/README.md)；规则适用、冲突和覆盖语义只以 [`AGENTS.md`](AGENTS.md) 为准。

## 第 4 步：确认受保护配置已由管理员完成

公开注册表只保存配置键名，不保存受保护值。对于上面的示例，你需要修改.env文件的以下事项：

- 已为 `PROJECT_EXAMPLE_SERVICE_REPO_URL` 提供受保护的仓库 URL。
- 如果仓库需要认证，对应的可选用户名和密码必须同时配置，不能只配置其中一个。
- 要按作者生成个人报告，必须配置受信的作者邮箱到规范用户 ID 的唯一身份映射。
- 要运行日报邮件流程，还必须配置领导路由和 SMTP。

本公开仓库不说明这些受保护值的存储位置或录入入口。操作人员必须使用组织批准的安全配置流程，或联系管理员完成配置。不要把受保护值写入 README、注册表、命令参数或其他公开文件，也不要尝试从公开工作流中读取它们。

## 第 5 步：在 OpenCode 中运行命令

再次确认：先把本仓库作为 OpenCode 工作区打开，然后在 OpenCode 对话输入框中输入下面的命令。

只同步一个项目：

```text
/sync-repositories project=example-service
```

按香港时区的自然日手动审查现有本地工作区：

```text
/code-review project=example-service date=2026-07-19
```

按完整提交 SHA 手动审查：

```text
/code-review project=example-service commit=<40位小写提交SHA>
```

同步并执行指定日期的完整日报：

```text
/daily-review project=example-service date=2026-07-19
```

省略 `project` 选择时，命令会选择注册表中全部有效且已启用的项目。`/daily-review` 省略日期时，使用 `Asia/Hong_Kong` 的前一自然日。

`/code-review` 不同步仓库，必须提供 `date`、`date-range` 或 `commit`。命令支持日期范围，但当前可读文档没有提供可直接复制的 `date-range` 编码示例，因此这里不猜测其写法。参数组合、范围和流程语义以 [`AGENTS.md`](AGENTS.md) 为唯一权威；命令入口与当前参数形式可查看：

- [`/sync-repositories`](.opencode/commands/sync-repositories.md)
- [`/code-review`](.opencode/commands/code-review.md)
- [`/daily-review`](.opencode/commands/daily-review.md)

## 执行后去哪里看结果

`/sync-repositories` 只在 OpenCode 对话中给出本次同步汇总，不生成代码审查报告。

`/code-review` 只生成 Markdown 事实报告：

```text
reports/daily/<YYYY-MM-DD>/<user_id>-code-review.md
```

`/daily-review` 先写入同一路径的 Markdown。只有 Markdown 成功后，才可生成同目录同主名的忠实、安全 HTML：

```text
reports/daily/<YYYY-MM-DD>/<user_id>-code-review.html
```

HTML 通过检查且该用户的其他门禁全部满足后，日报才会按规范用户 ID 排序，逐用户严格串行调用受信邮件入口。每位符合条件的用户发送一封独立邮件，前一用户的结果返回并校验后才处理下一用户。

报告会用直接的中文说明：审查了哪些项目和提交、使用了什么时间窗口和过滤条件、每类发现有多少、每条发现位于哪个文件和行范围、证据与影响是什么、建议如何修改，以及哪些项目、提交或用户被跳过及原因。Markdown 是唯一事实报告，HTML 只能忠实呈现对应 Markdown。

## 如何判断成功或失败

始终阅读 OpenCode 最终输出的中文汇总，不要只看是否生成了文件。


| 状态        | 表示什么                      | 你应该怎么做                        |
| --------- | ------------------------- | ----------------------------- |
| 全部成功      | 本次目标范围内要求的步骤和完成门禁都已满足     | 核对实际覆盖的项目、用户、提交和报告数量          |
| 部分失败      | 至少一部分范围可信成功，但其他项目、用户或步骤失败 | 按最终汇总逐项处理失败原因，不要把整次运行当成成功     |
| 全部失败      | 没有可信成功范围，或注册表等全局前置条件失败    | 先修复最终汇总中的首个全局或项目级问题，再重新发起新的运行 |
| `PARTIAL` | 一封邮件的部分目标被接受，其他目标被拒绝      | 视为未完整投递；记录结果并按组织流程处理，不要自动重试   |
| `UNKNOWN` | 邮件投递结果无法明确确认              | 视为未完成；查看脱敏中文原因，不要声称投递成功或自动重试  |


生成文件、进程退出码为零、只有一个项目成功，或只有部分收件人接受，都不能证明完整成功。完成条件只以 [`AGENTS.md`](AGENTS.md) 和本次最终中文汇总为准。

## 常见问题


| 现象                          | 先检查什么                                                                                                            |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 没有任何项目被处理                   | 检查 `project-registry.yaml` 是否仍只有禁用的 `non-production-example`，目标项目是否有效且 `enabled: true`，以及输入的 `project_id` 是否完全匹配 |
| 项目同步失败                      | 查看最终中文汇总中的脱敏原因；检查注册表字段、目录边界、配置键名和启用状态，并请管理员确认对应受保护仓库配置已完成，不要查找或输出秘密值                                             |
| 手动审查没有生成报告                  | 确认受控本地工作区已经存在，命令提供了 `date`、`date-range` 或完整提交 SHA，并检查最终汇总是否报告身份、日期或固定提交失败                                        |
| 显示“范围内无提交”                  | 检查日期、分支、提交、文件和目录过滤条件是否确实覆盖目标提交；不要通过扩大到全部历史来掩盖范围错误                                                                |
| 一些提交没有出现在个人报告中              | 查看是否因 Author Email 格式、无匹配、非唯一匹配或身份接口失败而被列为未归属；不要根据姓名或邮箱外观猜测用户                                                    |
| Markdown 已存在，但没有 HTML 或邮件   | 查看最终中文汇总中该用户的 Markdown 完整性、HTML 忠实与安全检查、身份映射和投递前门禁；Markdown 保留并不代表后续步骤成功                                         |
| 邮件结果是 `PARTIAL` 或 `UNKNOWN` | 这不是完整成功。记录最终中文结果并按组织批准的邮件运维流程处理，不要自动重试，也不要尝试读取 SMTP 或收件人受保护配置                                                    |


## 仓库结构与权威文档

```text
.
├── AGENTS.md                         唯一权威流程契约
├── opencode.json                     OpenCode 模型与权限配置
├── project-registry.yaml             唯一项目成员与配置来源
├── .opencode/
│   ├── commands/                     Slash Command 入口定义
│   └── skills/                       日报 HTML 忠实呈现能力
├── standards/
│   ├── README.md                     规范文件组织与模板说明
│   ├── common/                       公共审查规则
│   └── projects/                     项目审查规则
├── data/code/                        注册项目的受控本地工作区
├── reports/daily/                    Markdown 和日报 HTML 输出
├── tools/                            受信内部实现，不是用户命令入口
└── tests/                            仓库自身验证，不是日常操作入口
```

维护时按下面的权威关系判断信息来源：

- [`AGENTS.md`](AGENTS.md) 是审查、报告、投递、安全和失败语义的唯一权威契约。
- [`project-registry.yaml`](project-registry.yaml) 是项目成员与项目配置的唯一来源。
- [`.opencode/commands/`](.opencode/commands/) 只定义当前 Slash Command 的调用入口与参数形式，不能改写 `AGENTS.md`。
- [`standards/README.md`](standards/README.md) 说明规则文件如何组织和编写，规则适用、冲突和覆盖语义仍以 `AGENTS.md` 为准。
- `tools/` 是受信内部实现，不应由用户直接运行。
- `tests/` 只用于验证本仓库自身，不是同步、审查或投递入口。

