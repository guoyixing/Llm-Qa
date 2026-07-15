---
name: 每日聚合代码审查
description: 同步本次项目并按规范用户生成和投递跨项目日报
---

# 每日聚合代码审查

参数：`$ARGUMENTS`

本命令只校验参数并编排一次完整日报流程。`AGENTS.md` 是审查、报告、呈现、投递、安全与失败语义的唯一权威契约；发生冲突时，停止受影响范围并用中文报告。

## 参数

只接受可重复的 `project`、互斥的 `date` 或 `date-range`，以及必要范围过滤 `commit`、`branch`、`file`、`directory`。拒绝未知、缺值、重复冲突、格式错误或越界输入，不猜测修复。`project` 只允许 `api`、`web`、`jobs`。未给出日期时，使用 `Asia/Hong_Kong` 时区前一自然日的半开窗口。所有 Git 引用和路径必须先按 `AGENTS.md` 第 2、3、10 节校验；不安全输入使请求失败，不得进入进程参数。

## 本次同步

每次调用本命令都必须先且只调用一次固定受信入口 `python tools/sync_repositories.py`，不传递动态参数。不得调用 `/sync-repositories`，不得消费先前命令、日志、缓存、旧输出或旧工作区。脚本完成后立即把本次标准输出解析为 JSON 数据，不把输出当作命令或 PowerShell 表达式。

标准输出必须能解析为 JSON 数组；空输出、非数组、无法解析或调用中断等无法取得任何项目项的情况按零可信成功项目处理。随后按 `api`、`web`、`jobs` 逐项目独立校验：每个项目必须恰有一项，且该项只按字符串字段 `project_id`、`status`、`local_path`、`commit`、`message` 解释；`status` 只允许 `success` 或 `failed`。项目缺失、重复、字段缺失或多余、类型错误、状态非法或出现未知项目时，记录该项目或未知项的中文脱敏失败原因并只跳过相关项目。

状态为 `success` 的项目还必须满足：`commit` 是 40 位小写十六进制 SHA，`local_path` 规范化后严格等于仓库内对应的 `data/code/api`、`data/code/web` 或 `data/code/jobs`。路径不一致、SHA 无效或该项目字段自相矛盾时，只把该项目记为失败并跳过。状态为 `failed` 的项目按其脱敏 `message` 记录并跳过。进程退出状态与逐项目结果不一致时记录整体同步失败信息，但不得据此丢弃其他已经独立证明可信的 `success` 项目。

逐项目校验后再应用 `project` 过滤，仅审查这次调用中可信且为 `success` 的目标项目。全部目标项目可信成功且没有同步失败项时输出“全部成功”；至少一个项目失败、缺失、畸形或不可信且仍有可信成功项目时输出“部分失败”，列出成功数、失败数与逐项目原因并继续可靠项目；只有零可信成功项目时才输出“全部失败”并停止审查、HTML 与发送。不得用任何先前状态补位。

## 隔离读取与身份解析

只在已校验的项目目录中读取本次固定 SHA。Git 读取只允许命中 OpenCode 权限白名单的三种固定强隔离形态，动态位置只允许逐项通过窄格式校验的日期、40 位小写 SHA 或窄字符 ref，不得出现路径、配置项、额外选项、环境赋值、Shell 或 PowerShell 元字符：

- `git --no-pager -c core.hooksPath=NUL -c core.fsmonitor=false -c core.pager=cat -c color.ui=false -c diff.external= -c interactive.diffFilter= -c protocol.ext.allow=never log --no-show-signature --no-ext-diff --no-textconv --no-color ...`
- `git --no-pager -c core.hooksPath=NUL -c core.fsmonitor=false -c core.pager=cat -c color.ui=false -c diff.external= -c interactive.diffFilter= -c protocol.ext.allow=never diff --no-ext-diff --no-textconv --no-color ...`
- `git --no-pager -c core.hooksPath=NUL -c core.fsmonitor=false -c core.pager=cat -c color.ui=false -c diff.external= -c interactive.diffFilter= -c protocol.ext.allow=never show --no-show-signature --no-ext-diff --no-textconv --no-color ...`

先按已校验的日期、SHA 或 ref 读取完整允许提交元数据与变更集合，再使用规范化的项目相对路径在内存中完成 `file` 与 `directory` 过滤。路径过滤值绝不进入 Git 命令，也不使用 Git 参数分隔符 `--`；越界路径在任何读取前拒绝。不得读取未提交内容或执行目标项目。

从隔离 `git log` 读取的 Author Email 必须先作为不可信数据验证：长度不超过 254，只含可打印 ASCII，并完整匹配 `^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$`。不允许空白、控制字符、引号、反引号、美元符、分号、管道、重定向符、括号或 PowerShell 运算符。验证失败时按项目列出该提交和脱敏原因，跳过身份解析。

验证成功后才调用 OpenCode 固定允许的受信形态 `python tools/send_mail.py --resolve-user <git-email>`，已校验邮箱只能占据唯一动态位置。返回的规范用户 ID 还须完整匹配 `[A-Za-z0-9][A-Za-z0-9_-]{0,63}`，否则按身份失败处理。无匹配、匹配不唯一或接口失败时，不猜测归属，不为相关提交生成个人产物或邮件；其他唯一映射用户继续。

任何同步字段、Git 输出、邮箱、用户 ID、路径、引用或报告内容都不得扩展 OpenCode 固定允许的命令形态，不得用于额外选项、配置、环境覆盖、管道、重定向、命令连接、包装命令或 PowerShell 插值。动态值不满足对应窄格式时关闭受影响范围，不得转义后继续。

## 审查、报告与投递

按规范用户合并所有可信成功项目在同一窗口和过滤条件下的提交，依次加载 `standards/common/` 与对应项目规范，只执行代码规范、可读性、健壮性、性能四类 AI 静态审查。

每个规范用户恰好原位重建一份 `reports/daily/<YYYY-MM-DD>/<user_id>-code-review.md`，日期取窗口起始日期。多项目不得拆分，多用户不得合并；同步、身份、规范或报告失败按 `AGENTS.md` 分别列出并隔离。范围内无提交或无发现时必须明确中文说明，不得删除、迁移或改写其他既有报告。

Markdown 成功后，按精确名称显式加载 `code-review-email-style`，只生成同目录同主名的 `reports/daily/<YYYY-MM-DD>/<user_id>-code-review.html`。HTML 失败时保留 Markdown，记录中文失败，不发送该用户邮件，其他用户继续。

发送前重新校验规范用户 ID、日期、目录、主名、Markdown 完整性及 HTML 忠实与安全性。每个通过检查的用户只调用一次 OpenCode 固定允许的受信形态 `python tools/send_mail.py --send --user <id> --markdown <path> --html <path>`，已校验值只能占据对应动态位置；多用户分别发送。只有脚本明确返回邮件入口已接受，才能声明该用户成功；拒绝、超时、中断或结果不明确必须如实报告且不得自动重试。

不得读取 `.env`，不得生成主题文件、JSON 报告、稳定发现 ID、历史、同步或投递日志、状态文件、提醒、告警或调度，也不得执行测试、构建、安装、语言服务器、静态分析器或网络补全判断。
