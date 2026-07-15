#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

# ─── 运行方法 ───
# python tools/send_mail.py --list-users
# python tools/send_mail.py --validate-user <id>
# python tools/send_mail.py --resolve-user <git-email>
# python tools/send_mail.py --send --user <id> \
#   --markdown reports/daily/<日期>/<id>-code-review.md \
#   --html reports/daily/<日期>/<id>-code-review.html
# ──────────────────

from __future__ import annotations

import json, re, smtplib, ssl, sys
from collections.abc import Mapping, Sequence
from datetime import date
from email.message import EmailMessage
from email.utils import parseaddr
from html.parser import HTMLParser
from pathlib import Path
from typing import Final, Literal, NamedTuple, NewType, final
from urllib.parse import unquote, urlsplit

UserId = NewType("UserId", str)
EmailAddress = NewType("EmailAddress", str)
DeliveryStatus = Literal["ACCEPTED", "REJECTED", "UNKNOWN"]
ROOT: Final = Path(__file__).resolve().parent.parent
DAILY_DIR: Final = ROOT / "reports" / "daily"
USER_PATTERN: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
USER_KEY: Final = re.compile(r"USER_(\d+)_ID")
CSS_REMOTE: Final = re.compile(r"(?:url|src|image|image-set|cross-fade|-webkit-image-set)\s*\(|@import\b|@namespace\b", re.IGNORECASE)
BANNED_TAGS: Final = frozenset({"audio", "base", "embed", "form", "iframe", "image", "img", "link", "math", "meta", "object", "picture", "script", "source", "style", "svg", "track", "use", "video"})
REMOTE_ATTRIBUTES: Final = frozenset({"action", "background", "codebase", "data", "formaction", "manifest", "ping", "poster", "src", "srcset"})
OUTCOMES: Final[dict[DeliveryStatus, tuple[str, str, int]]] = {"ACCEPTED": ("邮件投递已被服务器接受", "已接受", 0), "REJECTED": ("邮件投递被明确拒绝", "明确拒绝", 4), "UNKNOWN": ("投递结果不明确，禁止声称成功", "结果不明确", 4)}


@final
class MailError(Exception):
    def __init__(self, code: str, message: str, exit_code: int = 2) -> None:
        super().__init__(message)
        self.code, self.message, self.exit_code = code, message, exit_code


class User(NamedTuple):
    user_id: UserId
    git_email: EmailAddress
    manager: EmailAddress | None


class Smtp(NamedTuple):
    host: str
    port: int
    timeout: float
    username: str
    password: str
    sender: EmailAddress
    use_ssl: bool


class Report(NamedTuple):
    user_id: UserId
    report_date: str
    subject: str
    html: str


Args = tuple[Literal["list", "validate", "resolve", "send"], str | None, Path | None, Path | None]


@final
class SafeHtmlParser:
    def __init__(self) -> None:
        self.parser = HTMLParser(convert_charrefs=True)
        self.seen_structure, self.open_structure = set[str](), set[str]()
        setattr(self.parser, "handle_starttag", self.handle_starttag)
        setattr(self.parser, "handle_endtag", self.handle_endtag)
        for name in ("handle_comment", "handle_decl", "handle_pi", "unknown_decl"):
            setattr(self.parser, name, self.reject_markup)

    def reject_markup(self, _data: str) -> None:
        raise MailError("HTML内容不安全", "HTML 包含注释、声明或处理指令", 3)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.casefold()
        if lowered in BANNED_TAGS or ":" in lowered: raise MailError("HTML内容不安全", "HTML 包含禁止的活动内容或远程资源", 3)
        if lowered in {"html", "body"}:
            if lowered in self.seen_structure or (lowered == "body" and "html" not in self.open_structure): raise MailError("HTML结构错误", "HTML 的 html 或 body 结构无效", 3)
            self.seen_structure.add(lowered)
            self.open_structure.add(lowered)
        for name, value in attrs:
            attribute = name.casefold()
            if attribute.startswith("on") or attribute.endswith(":href") or attribute in REMOTE_ATTRIBUTES: raise MailError("HTML内容不安全", "HTML 包含事件处理器或远程资源", 3)
            if attribute == "href" and (lowered != "a" or not safe_href(value)): raise MailError("HTML链接不安全", "HTML 包含不安全链接", 3)
            if attribute == "style" and value is not None and (any(marker in value for marker in ("\\", "/*", "*/")) or not value.isprintable() or CSS_REMOTE.search(value)): raise MailError("HTML样式不安全", "HTML 内联样式包含远程资源表达", 3)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.casefold()
        if lowered not in {"html", "body"}: return
        if lowered not in self.open_structure or (lowered == "html" and "body" in self.open_structure): raise MailError("HTML结构错误", "HTML 的 html 或 body 未正确配对", 3)
        self.open_structure.remove(lowered)

    def feed(self, text: str) -> None: self.parser.feed(text)

    def close(self) -> None: self.parser.close()


def safe_href(value: str | None) -> bool:
    if value is None or value != value.strip(): return False
    decoded = unquote(value)
    if "\\" in decoded or not decoded.isprintable() or any(char.isspace() for char in decoded): return False
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError: return False
    return value.startswith("https://") and parsed.scheme == "https" and parsed.hostname is not None and parsed.username is None and parsed.password is None and "%" not in parsed.netloc


def emit(output: Mapping[str, str | list[str]]) -> None: print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))


def respond(output: Mapping[str, str | list[str]], code: int) -> int:
    emit(output)
    return code


def env() -> dict[str, str]:
    try:
        lines = (ROOT / ".env").read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error: raise MailError("配置不可读", "无法读取邮件配置") from error
    values: dict[str, str] = {}
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"): continue
        key, separator, value = line.partition("=")
        if not separator or not key.strip(): raise MailError("配置格式错误", f"邮件配置第 {number} 行格式无效")
        normalized = value.strip()
        if len(normalized) >= 2 and normalized[:1] == normalized[-1:] and normalized[:1] in {"'", '"'}: normalized = normalized[1:-1]
        values[key.strip()] = normalized
    return values


def email(raw: str) -> EmailAddress:
    value = raw.strip()
    display, address = parseaddr(value)
    if not address or display or address != value or "@" not in address or any(char in value for char in "\r\n"): raise MailError("邮箱配置错误", "邮件地址配置无效")
    return EmailAddress(address)


def users(values: Mapping[str, str]) -> tuple[User, ...]:
    indexes = sorted(match.group(1) for key in values if (match := USER_KEY.fullmatch(key)))
    result: list[User] = []
    seen: set[UserId] = set()
    for index in indexes:
        raw_id = values.get(f"USER_{index}_ID", "").strip()
        user_id = UserId(raw_id)
        if USER_PATTERN.fullmatch(raw_id) is None or user_id in seen: raise MailError("用户配置错误", "规范用户标识无效或重复")
        manager = values.get(f"USER_{index}_LEADER_EMAIL", "").strip()
        result.append(User(user_id, email(values.get(f"USER_{index}_GIT_EMAIL", "")), email(manager) if manager else None))
        seen.add(user_id)
    if not result: raise MailError("用户配置错误", "未配置任何用户")
    return tuple(result)


def find_user(raw: str, configured: tuple[User, ...]) -> User:
    matches = tuple(user for user in configured if user.user_id == UserId(raw))
    if USER_PATTERN.fullmatch(raw) is None or len(matches) != 1: raise MailError("用户不存在", "未找到唯一规范用户", 3)
    return matches[0]


def require(values: Mapping[str, str], key: str) -> str:
    if not (value := values.get(key, "").strip()): raise MailError("配置缺失", "邮件配置不完整")
    return value


def smtp(values: Mapping[str, str]) -> Smtp:
    try:
        port, timeout = int(require(values, "SMTP_PORT")), float(require(values, "SMTP_TIMEOUT_SECONDS"))
    except ValueError as error: raise MailError("SMTP配置错误", "SMTP 数字配置无效") from error
    tls, ssl_value = require(values, "SMTP_USE_TLS").casefold(), require(values, "SMTP_USE_SSL").casefold()
    if tls not in {"true", "false"} or ssl_value not in {"true", "false"}: raise MailError("SMTP配置错误", "TLS 或 SSL 开关配置无效")
    use_tls, use_ssl = tls == "true", ssl_value == "true"
    username, password = values.get("SMTP_USERNAME", "").strip(), values.get("SMTP_PASSWORD", "")
    if not 1 <= port <= 65535 or not 0 < timeout <= 120 or use_tls == use_ssl: raise MailError("SMTP配置错误", "SMTP 端口、超时或加密模式无效")
    if bool(username) != bool(password): raise MailError("SMTP配置错误", "SMTP 认证配置不完整")
    return Smtp(require(values, "SMTP_HOST"), port, timeout, username, password, email(require(values, "SMTP_FROM")), use_ssl)


def controlled(raw: Path, maximum: int) -> Path:
    if ".." in raw.parts: raise MailError("产物路径错误", "日报产物路径不得包含目录遍历", 3)
    candidate = raw if raw.is_absolute() else ROOT / raw
    try:
        relative = candidate.relative_to(DAILY_DIR)
    except ValueError as error: raise MailError("产物路径错误", "日报产物原始路径越界", 3) from error
    chain = [DAILY_DIR.parent, DAILY_DIR, *(DAILY_DIR.joinpath(*relative.parts[:end]) for end in range(1, len(relative.parts) + 1))]
    if any(path.is_symlink() for path in chain): raise MailError("产物路径错误", "日报产物路径不得包含符号链接", 3)
    invalid_type = any(path.exists() and (not path.is_file() if path == candidate else not path.is_dir()) for path in chain)
    if invalid_type: raise MailError("产物路径错误", "日报产物路径段类型无效", 3)
    try:
        resolved = candidate.resolve(strict=True)
        size = resolved.stat().st_size
    except OSError as error: raise MailError("产物缺失", "指定的日报产物不存在", 3) from error
    if not resolved.is_file() or not resolved.is_relative_to(DAILY_DIR) or not 0 < size <= maximum: raise MailError("产物文件错误", "日报产物路径或大小无效", 3)
    return resolved


def report(raw_user: str, markdown_raw: Path, html_raw: Path) -> Report:
    if USER_PATTERN.fullmatch(raw_user) is None: raise MailError("用户无效", "CLI 用户标识无效", 3)
    user_id = UserId(raw_user)
    markdown, html = controlled(markdown_raw, 5 * 1024 * 1024), controlled(html_raw, 5 * 1024 * 1024)
    relative = markdown.parent.relative_to(DAILY_DIR)
    day = relative.parts[0] if len(relative.parts) == 1 else ""
    try:
        parsed_day = date.fromisoformat(day)
    except ValueError as error: raise MailError("产物日期错误", "日报产物目录日期无效", 3) from error
    stem = f"{user_id}-code-review"
    if parsed_day.isoformat() != day or markdown.parent != html.parent: raise MailError("产物归属错误", "Markdown 与 HTML 日期目录不匹配", 3)
    if markdown.name != f"{stem}.md" or html.name != f"{stem}.html": raise MailError("产物归属错误", "Markdown 与 HTML 用户或主名不匹配", 3)
    try:
        markdown_text, html_text = markdown.read_text(encoding="utf-8"), html.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error: raise MailError("产物不可读", "无法读取 Markdown 或 HTML 日报", 3) from error
    if not markdown_text.strip() or not any(line.startswith("# ") for line in markdown_text.splitlines()): raise MailError("Markdown不完整", "Markdown 日报为空或缺少主标题", 3)
    parser = SafeHtmlParser()
    parser.feed(html_text)
    parser.close()
    if parser.seen_structure != {"html", "body"} or parser.open_structure: raise MailError("HTML不完整", "HTML 日报缺少配对的 html 或 body 结构", 3)
    return Report(user_id, day, f"{day} {user_id} 代码质量审查日报", html_text)


def recipient(user: User, values: Mapping[str, str]) -> EmailAddress:
    if user.manager is not None: return user.manager
    fallback = values.get("DEFAULT_LEADER_EMAIL", "").strip()
    if not fallback: raise MailError("无收件人", "未配置可用的领导收件人", 3)
    return email(fallback)


def deliver(config: Smtp, target: EmailAddress, item: Report) -> DeliveryStatus:
    message = EmailMessage()
    message["Subject"], message["From"], message["To"] = item.subject, config.sender, target
    message.set_content(item.html, subtype="html", charset="utf-8")
    context = ssl.create_default_context()
    if config.use_ssl:
        with smtplib.SMTP_SSL(config.host, config.port, timeout=config.timeout, context=context) as client:
            if config.username: _ = client.login(config.username, config.password)
            refused = client.send_message(message)
    else:
        with smtplib.SMTP(config.host, config.port, timeout=config.timeout) as client:
            _ = client.ehlo()
            _ = client.starttls(context=context)
            _ = client.ehlo()
            if config.username: _ = client.login(config.username, config.password)
            refused = client.send_message(message)
    if refused: return "REJECTED" if all(500 <= code < 600 for code, _ in refused.values()) else "UNKNOWN"
    return "ACCEPTED"


def parse_args(raw: Sequence[str]) -> Args:
    if list(raw) == ["--list-users"]: return "list", None, None, None
    if len(raw) == 2 and raw[0] == "--validate-user": return "validate", raw[1], None, None
    if len(raw) == 2 and raw[0] == "--resolve-user": return "resolve", raw[1], None, None
    if len(raw) == 7 and (raw[0], raw[1], raw[3], raw[5]) == ("--send", "--user", "--markdown", "--html"):
        return "send", raw[2], Path(raw[4]), Path(raw[6])
    raise MailError("参数错误", "命令行参数无效")


def send_mode(args: Args) -> int:
    _, raw_user, markdown, html = args
    if raw_user is None or markdown is None or html is None: raise MailError("参数缺失", "发送模式缺少用户、Markdown 或 HTML 路径", 3)
    try:
        item = report(raw_user, markdown, html)
        values = env()
        user = find_user(str(item.user_id), users(values))
        target = recipient(user, values)
        config = smtp(values)
    except MailError as error:
        return respond({"status": f"投递前失败：{error.message}", "error_code": error.code}, error.exit_code)
    try:
        status = deliver(config, target, item)
    except smtplib.SMTPRecipientsRefused as error: status = "REJECTED" if error.recipients and all(500 <= code < 600 for code, _ in error.recipients.values()) else "UNKNOWN"
    except smtplib.SMTPResponseException as error: status = "REJECTED" if 500 <= error.smtp_code < 600 else "UNKNOWN"
    except (smtplib.SMTPException, OSError): status = "UNKNOWN"
    message, reason, exit_code = OUTCOMES[status]
    return respond({"status": message, "error_code": reason, "user_id": str(item.user_id), "report_date": item.report_date, "delivery_status": status}, exit_code)


def run() -> int:
    args = parse_args(sys.argv[1:])
    mode, raw_user, _, _ = args
    if mode == "send": return send_mode(args)
    try:
        configured = users(env())
    except MailError as error:
        status = "身份解析失败" if mode == "resolve" else "身份校验失败" if mode == "validate" else error.message
        return respond({"status": status, "error_code": "身份解析失败" if mode == "resolve" else error.code}, error.exit_code)
    if mode == "list": return respond({"user_ids": sorted(str(user.user_id) for user in configured)}, 0)
    if mode == "validate":
        try:
            _ = find_user(raw_user or "", configured)
        except MailError: return respond({"status": "INVALID", "error_code": "用户不存在"}, 3)
        return respond({"status": "VALID"}, 0)
    try:
        target = email(raw_user or "")
        matches = tuple(user for user in configured if user.git_email.casefold() == target.casefold())
    except MailError: matches = ()
    if len(matches) != 1: return respond({"status": "身份解析失败", "error_code": "身份无法唯一解析"}, 3)
    return respond({"user_id": str(matches[0].user_id)}, 0)


def main() -> int:
    try:
        return run()
    except MailError as error: return respond({"status": error.message, "error_code": error.code}, error.exit_code)
    except KeyboardInterrupt: return respond({"status": "操作中断，投递结果不明确", "error_code": "操作中断", "delivery_status": "UNKNOWN"}, 4)


if __name__ == "__main__":
    raise SystemExit(main())
