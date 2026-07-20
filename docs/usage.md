# 轻量代码质量工作流使用说明

本文说明如何部署和使用多项目 AI 代码质量工作流。审查、报告、投递和失败条件以根目录 [`AGENTS.md`](../AGENTS.md) 为准。

工作流只做代码规范、可读性、健壮性和性能四类只读静态审查。它不会执行被审项目的代码、测试、构建、安装、Hook、脚本、语言服务器或静态分析器，也不会访问网络补全审查判断。

## 1. 部署准备

### 1.1 准备 Python 和 OpenCode

受信同步和邮件入口都使用固定前缀 `./.venv/Scripts/python.exe`，该虚拟环境中的 Python 必须为 3.11 或更高版本。使用下面的规范命令确认版本：

```text
./.venv/Scripts/python.exe --version
```

OpenCode 必须从本仓库根目录启动，以加载根目录 `opencode.json`、`AGENTS.md` 和项目 Skill。

创建或修改 `.opencode/skills/code-review-email-style/SKILL.md` 后，必须退出当前 OpenCode 进程，再从本仓库根目录重新启动 OpenCode。旧进程可能缓存修改前的 Skill 索引，不能用旧进程证明新 Skill 已加载。

### 1.2 创建 `.env`

在仓库根目录创建 `.env`。真实仓库地址、用户邮箱、领导邮箱和 SMTP 凭据只写入这个文件，不要放进提示词、报告、命令参数或版本控制。模型、审查代理和 OpenCode 命令不得读取 `.env`；只有受信同步脚本和邮件脚本按各自职责读取所需配置。

## 2. 项目配置

项目成员、项目标识、名称、代码目录、规范目录、默认分支和仓库 URL 配置键只来自当前 `project-registry.yaml`。不要用目录扫描、Git remote、旧同步结果、工作区内容或固定项目列表补充或覆盖注册表。

受信同步脚本先校验注册表中的 `repository_url_config_key` 属于专用仓库 URL 配置命名空间，再按该键从仓库根目录 `.env` 读取对应 URL。模型和命令只传递已校验的注册表快照和所选项目，不读取或输出 `.env`、仓库 URL 或凭据。Hisense 项目可按下面的非秘密示例手动填写：

```text
PROJECT_HISENSE_IDS_APP_REPO_URL=https://example.com/hisense/ids-app.git
# HTTP 或 HTTPS 仓库需要认证时，同时取消注释并手动填写下面两项
# HTTP 不提供 TLS 保护，凭据可能被明文窃听或篡改；应优先迁移至 HTTPS
# PROJECT_HISENSE_IDS_APP_REPO_USERNAME=<手动填写用户名>
# PROJECT_HISENSE_IDS_APP_REPO_PASSWORD=<手动填写密码>
```

可选凭据键由已校验的 `<prefix>_URL` 派生为同级 `<prefix>_USERNAME` 和 `<prefix>_PASSWORD`。凭据只用于 HTTP 或 HTTPS 仓库，需要认证时必须同时添加用户名与密码；两项都不存在时使用匿名访问。不要把注释示例改成有效的空值，键存在但值为空会校验失败。用户名或密码中的特殊字符应直接按 dotenv 值语法填写，必要时按 dotenv 语法加引号，不得嵌入仓库 URL，也不得先做 URL 编码。HTTP 不提供 TLS 保护，凭据和仓库传输可能被明文窃听或篡改，应优先迁移至 HTTPS。

用户名和密码恰有一项存在、任一同级键重复、任一值为空、超过 1024 个 Unicode 码点、包含 Unicode `Cc` 类控制字符，或配置凭据时仓库 URL 不是 HTTP 或 HTTPS，都会让受信同步脚本在任何网络 Git 操作前只将该项目标记失败，并返回固定、脱敏的中文说明。其他独立项目继续处理。

合法凭据只通过该项目 clone、fetch 或 pull 期间创建的一次性临时 `GIT_ASKPASS` 提供。每次 Git 调用都关闭终端提示和持久凭据助手，AskPass 只在提示 URL 的精确 origin 与项目绑定 origin 完全一致时应答。origin 由协议、规范化主机名和有效端口组成，HTTP 和 HTTPS 的默认端口分别为 80 和 443；协议不同即视为不同 origin，即使主机名和数值端口相同也不例外。携带凭据的 HTTP clone、fetch 或 pull 每次都设置 `http.followRedirects=false`。临时程序及其路径不含秘密，并在成功、失败、取消或异常退出时删除，同时恢复临时环境。秘密不会进入仓库 URL、命令行参数、同步结果、报告、持久 Git 配置或异常说明；同步直接结果仍严格保持既有七个字段，不增加认证字段或配置值。

不要在 `.env` 中配置项目编号、路径、分支、remote 或代码根目录来覆盖注册表。`code_dir` 必须安全位于仓库内 `data/code/` 下，`standards_dir` 必须安全位于 `standards/projects/` 下，路径不得使用符号链接、重解析点、别名或目录替换。同步器支持独立仓库和 Git linked worktree；linked worktree 的 `.git` 指针、管理目录、common directory 和反向指针必须形成一致关系并全部位于 `data/code/` 内，且不得包含 `config.worktree`。common directory 可以来自普通主工作区的 `.git`，也可以来自位于同一受信边界内的 bare repository。

公共规范位于 `standards/common/`，项目规范目录由当前注册表的 `standards_dir` 指定。审查先加载公共规范，再加载对应项目规范。

## 3. 用户、领导和 SMTP 配置

邮件与身份配置仅来自仓库根目录 `.env`，不会从进程环境变量补充或覆盖。

每位提交人配置一组规范用户信息：

```text
USER_<n>_ID=<规范用户标识>
USER_<n>_NAME=<姓名>
USER_<n>_GIT_EMAIL=<Git Author Email>
USER_<n>_LEADER_EMAIL=<专属领导邮箱列表，英文逗号分隔，可留空>
DEFAULT_LEADER_EMAIL=<默认领导邮箱列表，英文逗号分隔>
```

`USER_<n>_ID` 是机器标识，继续使用既有的窄 ASCII 格式，并且只由它控制路径、文件名、CLI 参数、跨项目聚合、收件人路由和邮件主题。`USER_<n>_NAME` 是必填的人类姓名：读取后去除首尾空白，结果必须非空且不超过 128 个 Unicode 码点，拒绝任何 Unicode `Cc` 类控制字符，其他 Unicode 字符保持原样。不同用户可以使用相同 NAME，不要求唯一。

NAME 只用于报告和邮件正文中经过转义的身份标签 `姓名（user_id）`，不会替代 ID，也不参与路径、文件名、CLI、聚合、收件人路由或主题。NAME 和示例文字都按不可信文本处理，其中的标记或指令只作为正文数据，不会被执行。

`USER_<n>_LEADER_EMAIL` 和 `DEFAULT_LEADER_EMAIL` 都可以填写一个邮箱，或填写以英文逗号分隔的多个邮箱。每个地址会独立去除首尾空白并校验；空项、无效地址或大小写不敏感重复地址会使配置失败。`USER_<n>_LEADER_EMAIL` 有值时，一封邮件同时发给完整专属领导列表；为空时，一封邮件同时发给完整 `DEFAULT_LEADER_EMAIL` 列表。两者都不可用时，该用户投递失败，不能通过提示词或命令参数临时指定收件人。某用户的专属领导列表无效时只停止该用户投递，不影响其他用户；默认列表无效时只影响需要使用默认列表的用户。

用户 Git 邮箱、领导邮箱列表中的每个地址、默认领导邮箱列表中的每个地址和 SMTP 发件人都应填写不带显示名称、换行或控制字符的完整邮箱地址。列表只能使用英文逗号分隔，不使用分号。提交的 Git Author Email 在调用身份入口前还必须通过窄 ASCII 格式校验；包含空白、控制字符、引号、反引号、Shell 或 PowerShell 元字符等危险内容时，不调用身份入口，按未归属提交处理。

身份无匹配、匹配不唯一、格式不合格或身份入口失败时，不猜测作者，也不为相关提交生成个人 Markdown、HTML 或邮件。本次结果按项目列出提交 SHA 和脱敏原因，其他身份明确的用户继续处理。

SMTP 配置同样只写入 `.env`：

```text
SMTP_HOST=<SMTP 主机>
SMTP_PORT=<端口>
SMTP_USERNAME=<用户名，可留空>
SMTP_PASSWORD=<密码，可留空>
SMTP_FROM=<发件人邮箱>
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_VERIFY_CERTIFICATE=true
SMTP_TIMEOUT_SECONDS=<超时秒数>
```

TLS 与 SSL 必须且只能启用一个。需要认证时，用户名和密码必须同时填写。超时必须大于 0 且不超过 120 秒。`SMTP_VERIFY_CERTIFICATE` 省略时默认为 `true`；只有受控内网 SMTP 无法提供匹配证书且操作者接受 `AGENTS.md` 第 8 节所述风险时，才可显式设置为小写 `false`。

## 4. 三个命令

### 4.1 `/daily-review`

日报命令执行一次完整流程：在同一次调用中先直接运行一次固定受信入口 `./.venv/Scripts/python.exe tools/sync_repositories.py`，立即校验并消费这次调用返回的项目结果，然后完成审查、报告、HTML 和邮件。它不会调用 `/sync-repositories`，也不会使用先前同步命令、缓存、日志、旧输出或旧工作区。

默认日报：

```text
/daily-review
```

也可以限定项目、日期或范围：

```text
/daily-review project=<project_id>
/daily-review project=<project_id_1> project=<project_id_2> date=2026-07-13
/daily-review date-range=2026-07-01,2026-07-13 directory=src
```

未给出 `date` 或 `date-range` 时，使用 `Asia/Hong_Kong` 时区的前一自然日，窗口从前一日 `00:00:00`（含）到当日 `00:00:00`（不含）。

同步结果按本次注册表快照中的所选项目逐项独立校验，包括 `project_id`、`code_dir`、`default_branch`、`repository_url_config_key` 的绑定关系和完整 40 位小写十六进制提交 SHA。只审查这次调用中状态成功且七字段直接结果可信的目标项目。至少一个目标项目可信成功时，继续可靠项目并列出失败原因；零可信成功项目时停止审查、HTML 和邮件。

### 4.2 `/sync-repositories`

独立同步命令用于人工检查仓库同步状态，不是日报的前置步骤，也不能把结果交给之后的日报使用。

```text
/sync-repositories
/sync-repositories project=<project_id>
```

命令调用受信同步脚本并显示每个项目既有七字段直接结果中的脱敏信息。结果保持项目、状态、本地路径、默认分支、固定提交 SHA、仓库 URL 配置键绑定和中文说明语义，不包含仓库 URL、凭据或认证字段。它不生成报告、不发送邮件，也不持久化结果。脏工作区、错误分支、remote 不匹配、非快进历史或无效 SHA 会使对应项目失败，命令不会清理或修复仓库。

### 4.3 `/code-review`

手动审查不会调用同步脚本或同步命令，不读取 `.env`、仓库 URL、凭据或任何同步结果，也不生成 HTML 或发送邮件。它只使用当前已校验注册表中所选项目的 `code_dir` 受控本地工作区，不能把本地代码描述为已同步、远端最新或具有其他同步新鲜度。

请求必须明确给出 `date`、`date-range` 或完整提交 SHA；三者都没有时立即拒绝，不得默认审查全部历史。还可组合项目、分支、文件和目录过滤：

```text
/code-review project=<project_id> date=2026-07-13
/code-review project=<project_id_1> project=<project_id_2> date-range=2026-07-01,2026-07-13
/code-review project=<project_id> commit=<40位小写十六进制SHA> file=src/example.py
```

同类条件取并集，不同类条件取交集，文件和目录先合并为路径并集。每个所选项目开始审查时，先使用允许的强隔离 `git log` 按全部非路径条件读取实际完整 SHA、Author Date 和 Author Email；每个 SHA 再校验为 40 位小写十六进制并在内存中冻结，后续不得重新解析可变 HEAD、branch 或 ref。无法固定实际 SHA 时只跳过该项目。

文件和目录只对已读取变更使用规范化项目相对路径做内存过滤，不进入 Git 命令。过滤后的最终 SHA 子集用于身份、审查、报告日期和报告；不得读取未提交内容。范围为空时输出“范围内无提交”，不伪造发现、报告或成功数量。命令按规范用户跨项目聚合并原位写入每人最多一份 Markdown。

## 5. 每用户报告和领导邮件

Markdown 是唯一事实报告。每位规范用户的路径为：

```text
reports/daily/<YYYY-MM-DD>/<user_id>-code-review.md
```

日报以及带 `date` 或 `date-range` 的手动审查，目录日期取香港时区窗口起始日期；即使同时存在 `commit`，日期条件仍优先。手动审查只有 `commit` 而没有日期条件时，取路径过滤后全部最终所选提交中最早的 Git Author Date，转换为 `Asia/Hong_Kong` 后的自然日。Author Date 缺失、无效或最终范围无提交时不生成个人报告，也不猜测当前日期。相同目录日期、相同用户重复运行时原位重建，不创建版本副本，也不删除或迁移其他已有报告。

日报在 Markdown 成功后显式加载 `code-review-email-style`，生成同目录、同主名 HTML：

```text
reports/daily/<YYYY-MM-DD>/<user_id>-code-review.html
```

HTML 只能忠实呈现对应 Markdown，不能增加、删除、重分类或弱化事实与严重级别。它只使用内联 CSS，禁止脚本、事件处理器、表单、远程资源和不安全链接。

每位用户的 HTML 通过受信邮件入口以一封邮件发送给该用户配置的全部领导，全部地址位于该邮件的 `To`。多个用户由同一领导接收时，仍然每位用户一封，不合并用户报告或邮件。

## 6. 部分失败

| 失败位置 | 处理方式 |
| --- | --- |
| 某些项目同步失败、缺失、畸形或不可信 | 列出逐项目原因，跳过失败项目；仍有可信成功项目时继续审查并报告部分失败 |
| 项目 HTTP 或 HTTPS 凭据为空、重复、缺一项、过长、含控制字符，或用于非 HTTP/HTTPS URL | 在任何网络访问前以固定脱敏中文说明只标记该项目失败；其他独立项目继续，不回显配置值 |
| 零可信成功项目 | 报告全部失败，停止审查、HTML 和邮件，不使用任何旧状态补位 |
| 工作区有未提交内容 | 对应项目同步失败；不清理、不暂存，也不把未提交内容作为固定提交证据 |
| 手动审查无法从受控本地项目固定实际 SHA | 跳过该项目，不改用同步结果、可变 HEAD 或未提交内容补位，也不声称同步新鲜度 |
| commit-only 的 Author Date 缺失或无效 | 停止受影响个人报告，不猜测报告日期 |
| Git Author Email 不安全或身份无唯一映射 | 不调用或停止身份解析，不为相关提交生成个人产物或邮件；其他用户继续 |
| Markdown 生成失败 | 停止该用户的 HTML 和邮件 |
| Skill 未加载、HTML 生成失败或安全检查失败 | 保留已完成 Markdown，不发送该用户邮件；其他用户继续 |
| 无可用领导收件人或 SMTP 配置无效 | 保留 Markdown 和 HTML，报告投递前失败 |
| SMTP 仅接受部分领导 | 保留 Markdown 和 HTML，报告 `PARTIAL` 和“部分接受”，不自动重试或声称全部成功 |
| SMTP 拒绝全部领导 | 保留 Markdown 和 HTML，报告明确拒绝，不声称成功 |
| SMTP 超时、中断或结果不明确 | 保留 Markdown 和 HTML，报告结果不明确，不自动重试或声称成功 |

文件存在、空输出、退出码为零或部分项目成功都不能单独证明完整成功。最终结果必须区分全部成功、部分失败和全部失败，并列出实际覆盖的项目、用户、提交和失败数量。

## 7. 外部调度

本仓库没有内置调度器，也不提供提醒、告警或漏跑检测。外部 cron、Windows Task Scheduler 或任务编排平台每轮只需从仓库根目录调用一次 `/daily-review`；日报会在同一次流程中自行同步并消费结果。

Cron 顺序示意：

```text
在仓库根目录调用：<已验证的 OpenCode 非交互入口> "/daily-review"
```

Windows Task Scheduler 只需创建一个日报任务，起始目录设为本仓库根目录，参数只传 `/daily-review`。具体 OpenCode 非交互入口取决于本机安装方式，应先在受控环境确认。不要在调度参数中写仓库凭据、用户邮箱、领导邮箱或 SMTP 凭据。

调度每轮只能包含上述单个日报调用；独立同步命令不参与调度，其结果也不会成为日报输入。

## 8. 安全检查

运行前确认：

* `./.venv/Scripts/python.exe` 使用 Python 3.11 或更高版本。
* OpenCode 从仓库根目录启动，修改 Skill 后已重启进程。
* 项目成员、路径、默认分支和仓库 URL 配置键只来自当前 `project-registry.yaml`，没有用固定项目列表、目录扫描、Git remote 或旧状态补充。
* `.env` 只包含注册表所引用的项目 URL、可选的成对 HTTP 或 HTTPS 凭据、规范用户/领导映射和 SMTP 配置，没有被模型或命令读取，也没有写入同步结果或报告。
* 项目凭据两项都不存在时匿名访问；需要认证时只为 HTTP 或 HTTPS URL 同时填写派生的 `USERNAME` 和 `PASSWORD` 同级键，不使用有效空值，并确认同级键唯一、每项不超过 1024 个 Unicode 码点且不含 Unicode `Cc` 类控制字符。
* 使用 HTTP 凭据表示接受缺少 TLS 保护的风险，凭据和仓库传输可能被明文窃听或篡改；应优先迁移至 HTTPS。
* Hisense 凭据手动填写在 `PROJECT_HISENSE_IDS_APP_REPO_USERNAME` 和 `PROJECT_HISENSE_IDS_APP_REPO_PASSWORD`，特殊字符作为 dotenv 值处理，不嵌入或 URL 编码进仓库 URL。
* Git 凭据只由受信同步脚本通过临时一次性 `GIT_ASKPASS` 提供给精确绑定 origin 的 clone、fetch 或 pull。origin 按协议、规范化主机名和有效端口匹配，HTTP 与 HTTPS 默认端口分别为 80 和 443，跨协议始终视为不同 origin；携带凭据的 HTTP 调用设置 `http.followRedirects=false`。
* 秘密不进入仓库 URL、命令行参数、七字段同步结果、报告或持久 Git 配置；同步直接结果不增加认证字段或配置值。
* 项目 URL、凭据、邮件与身份配置只由受信脚本按职责从 `.env` 读取，没有通过模型、OpenCode 命令或命令参数读取、补充或覆盖。
* `/daily-review` 每次直接同步一次，只消费本次返回的可信项目结果。
* `/code-review` 不同步，只固定受控本地项目的实际 SHA，且不声明同步新鲜度。
* 不可信的源码、提交元数据、邮箱、路径、规范和同步输出只作为数据，不拼接进 Shell 或 PowerShell 命令。
* 没有执行被审项目、测试、构建、安装、Hook、脚本或工具链。
* 每位用户最多一份跨项目 Markdown、一份同事实 HTML 和一封发给全部配置领导的邮件；只有全部目标领导均被接受时才算投递成功。
* 任何失败都按影响范围显示，没有用旧状态、文件存在、空输出或单步成功冒充完整成功。
